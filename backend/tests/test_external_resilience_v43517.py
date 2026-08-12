from __future__ import annotations

from email.message import Message
from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError, URLError

import pytest
from fastapi.testclient import TestClient

from app.external_resilience_v43517 import (
    CircuitOpenError,
    ResilientTransport,
    policy_for_url,
    resilience_readiness,
    resilience_overview,
)
from app.main import app

ROOT = Path(__file__).resolve().parents[2]
client = TestClient(app)


class FakeClock:
    def __init__(self):
        self.value = 1000.0
        self.sleeps: list[float] = []

    def now(self) -> float:
        return self.value

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(float(seconds))
        self.value += float(seconds)

    def advance(self, seconds: float) -> None:
        self.value += float(seconds)


class FakeResponse:
    def __init__(self, body: bytes = b'{"ok":true}', status: int = 200, content_type: str = "application/json"):
        self._body = body
        self.status = status
        self.headers = Message()
        self.headers["Content-Type"] = content_type

    def read(self, _size: int = -1) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


def sequence_opener(*items):
    queue = list(items)
    calls = []

    def opener(req, timeout=0):
        calls.append((req.full_url, timeout, req.method))
        if not queue:
            raise AssertionError("unexpected upstream call")
        item = queue.pop(0)
        if isinstance(item, BaseException):
            raise item
        return item

    opener.calls = calls
    return opener


def http_error(code: int, retry_after: str | None = None) -> HTTPError:
    headers = Message()
    if retry_after is not None:
        headers["Retry-After"] = retry_after
    return HTTPError("https://example.test/data", code, "test", headers, BytesIO(b""))


def transport() -> tuple[ResilientTransport, FakeClock]:
    clock = FakeClock()
    return ResilientTransport(clock=clock.now, sleeper=clock.sleep), clock


def test_readiness_is_network_free_secret_safe_and_non_blocking():
    payload = resilience_readiness()
    assert payload["ok"] is True
    assert payload["network_calls_performed"] is False
    assert payload["secret_material_exposed"] is False
    assert payload["checks"]["upstream_health_non_blocking"] is True
    assert payload["checks"]["stale_is_never_silently_fresh"] is True


def test_provider_profiles_are_client_policies_not_quota_claims():
    payload = resilience_overview()
    assert payload["provider_policy_count"] >= 10
    assert "not a provider quota" in payload["rate_limit_policy"].lower()
    assert policy_for_url("https://www.airnowapi.org/aq/observation").id == "airnow"
    assert policy_for_url("https://api.eia.gov/v2/electricity/data").id == "eia"
    assert policy_for_url("https://example.test/data").id == "default"


def test_get_retries_retryable_failure_then_succeeds():
    t, clock = transport()
    opener = sequence_opener(http_error(503), FakeResponse())
    result = t.request("GET", "https://example.test/data", opener=opener)
    assert result.attempts == 2
    assert result.retry_count == 1
    assert len(opener.calls) == 2
    assert clock.sleeps and clock.sleeps[-1] > 0


def test_retry_after_is_honored_for_rate_limit_response():
    t, clock = transport()
    opener = sequence_opener(http_error(429, "2"), FakeResponse())
    result = t.request("GET", "https://example.test/rate", opener=opener)
    assert result.retry_count == 1
    assert any(delay >= 2 for delay in clock.sleeps)
    snapshot = t.snapshot()
    assert snapshot["providers"][0]["retry_after_honored"] == 1


def test_fresh_cache_hit_avoids_second_upstream_call():
    t, _clock = transport()
    opener = sequence_opener(FakeResponse(b'{"value":7}'))
    first = t.request("GET", "https://example.test/cache", opener=opener)
    second = t.request("GET", "https://example.test/cache", opener=opener)
    assert first.cache_status == "miss"
    assert second.cache_status == "hit"
    assert second.attempts == 0
    assert len(opener.calls) == 1


def test_stale_if_error_is_opt_in_and_explicitly_labeled():
    t, clock = transport()
    good = sequence_opener(FakeResponse(b'{"value":11}'))
    t.request("GET", "https://example.test/stale", opener=good)
    clock.advance(121)
    failing = sequence_opener(URLError("down"), URLError("down"), URLError("down"))
    result = t.request("GET", "https://example.test/stale", opener=failing, stale_if_error=True)
    assert result.stale is True
    assert result.cache_status == "stale-error"
    assert result.body == b'{"value":11}'


def test_stale_payload_is_not_silently_returned_when_opt_out():
    t, clock = transport()
    t.request("GET", "https://example.test/no-stale", opener=sequence_opener(FakeResponse()))
    clock.advance(121)
    with pytest.raises(RuntimeError):
        t.request("GET", "https://example.test/no-stale", opener=sequence_opener(URLError("down"), URLError("down"), URLError("down")), stale_if_error=False)


def test_circuit_opens_after_bounded_consecutive_failures():
    t, _clock = transport()
    for _ in range(3):
        with pytest.raises(RuntimeError):
            t.request("GET", "https://example.test/circuit", opener=sequence_opener(URLError("down")), retry_safe=False, cache=False)
    with pytest.raises(CircuitOpenError):
        t.request("GET", "https://example.test/circuit", opener=sequence_opener(FakeResponse()), retry_safe=False, cache=False)
    state = t.snapshot()["providers"][0]
    assert state["circuit_state"] == "open"
    assert state["circuit_open_rejections"] == 1


def test_nonretryable_auth_failure_does_not_trip_provider_circuit():
    t, _clock = transport()
    for _ in range(4):
        with pytest.raises(RuntimeError):
            t.request("GET", "https://example.test/auth", opener=sequence_opener(http_error(401)), cache=False)
    state = t.snapshot()["providers"][0]
    assert state["circuit_state"] == "closed"
    assert state["consecutive_failures"] == 0


def test_post_is_not_retried_unless_explicitly_marked_read_safe():
    t, _clock = transport()
    with pytest.raises(RuntimeError):
        t.request("POST", "https://example.test/query", data=b"{}", opener=sequence_opener(URLError("down")), cache=False)
    assert t.snapshot()["totals"]["upstream_calls"] == 1

    t2, _clock2 = transport()
    opener = sequence_opener(URLError("down"), FakeResponse())
    result = t2.request("POST", "https://example.test/query", data=b"{}", opener=opener, cache=False, retry_safe=True)
    assert result.attempts == 2


def test_transport_rejects_non_https_authoritative_requests():
    t, _clock = transport()
    with pytest.raises(ValueError, match="HTTPS"):
        t.request("GET", "http://example.test/data", opener=sequence_opener(FakeResponse()))


def test_public_telemetry_does_not_expose_request_urls_or_secret_material():
    t, _clock = transport()
    t.request("GET", "https://example.test/data?api_key=super-secret-value", opener=sequence_opener(FakeResponse()))
    text = str(t.snapshot())
    assert "super-secret-value" not in text
    assert "api_key" not in text
    assert "example.test/data" not in text


def test_public_resilience_endpoints_are_deterministic_and_network_free():
    overview = client.get("/public/external-resilience")
    readiness = client.get("/public/external-resilience/readiness")
    providers = client.get("/public/external-resilience/providers")
    deployment = client.get("/public/deployment-verification")
    source_policy = client.get("/public/source-health-policy")
    assert overview.status_code == readiness.status_code == providers.status_code == deployment.status_code == source_policy.status_code == 200
    assert overview.json()["network_calls_performed"] is False
    assert readiness.json()["ok"] is True
    assert providers.json()["secret_material_exposed"] is False
    assert deployment.json()["checks"]["external_resilience_control_plane_ready"] is True
    assert "/public/external-resilience/readiness" in deployment.json()["required_routes"]
    assert source_policy.json()["external_resilience"]["upstream_health_release_blocking"] is False


def test_authoritative_connector_helpers_route_through_shared_resilience_layer():
    for relative in (
        "backend/app/authoritative_connectors_v4353.py",
        "backend/app/authoritative_connectors_v4354.py",
        "backend/app/authoritative_connectors_v4355.py",
        "backend/app/authoritative_connectors_v43511.py",
        "backend/app/unified_live_events.py",
        "backend/app/connectors/advanced_external.py",
        "backend/app/connectors/external_data.py",
    ):
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert "external_resilience_v43517" in text
