from __future__ import annotations

"""Deterministic production-soak/fault-injection control plane for v4.35.22.

Every scenario runs entirely in process with a fake clock and fake upstream. It
exercises the same ResilientTransport implementation used by authoritative
connectors without making a provider network call.
"""

from dataclasses import dataclass, field
from email.message import Message
from io import BytesIO
from typing import Any, Callable
from urllib.error import HTTPError

from .credential_configuration_v43516 import credential_registry
from .evidence_presentation_v43519 import readiness as evidence_semantics_readiness
from .external_resilience_v43517 import CircuitOpenError, ResilientTransport
from .version import APP_VERSION

VERSION = APP_VERSION
CONTRACT = "live-operation-deterministic-soak-fault-injection-v43519"
SCENARIO_COUNT = 8
FLAP_CYCLES = 24


@dataclass
class FakeClock:
    now: float = 1000.0
    sleeps: list[float] = field(default_factory=list)
    def __call__(self) -> float:
        return self.now
    def sleep(self, seconds: float) -> None:
        value = max(0.0, float(seconds))
        self.sleeps.append(value)
        self.now += value
    def advance(self, seconds: float) -> None:
        self.now += float(seconds)


class FakeResponse:
    def __init__(self, body: bytes = b'{"ok":true}', status: int = 200, content_type: str = "application/json"):
        self._body = body
        self.status = status
        self.headers = Message()
        self.headers["Content-Type"] = content_type
    def read(self, _limit: int = -1) -> bytes:
        return self._body
    def __enter__(self):
        return self
    def __exit__(self, *_args):
        return False


def _http_error(code: int, *, retry_after: str | None = None) -> HTTPError:
    headers = Message()
    if retry_after is not None:
        headers["Retry-After"] = retry_after
    return HTTPError("https://example.test/data", code, f"HTTP {code}", headers, BytesIO(b""))


def _sequence_opener(events: list[Any]) -> Callable[..., Any]:
    queue = list(events)
    def opener(_request, timeout=8):
        if not queue:
            raise AssertionError("fault-injection opener exhausted")
        event = queue.pop(0)
        if isinstance(event, Exception):
            raise event
        return event
    return opener


def _scenario(name: str, passed: bool, **details: Any) -> dict[str, Any]:
    return {"id": name, "passed": bool(passed), **details}


def steady_success() -> dict[str, Any]:
    clock = FakeClock(); transport = ResilientTransport(clock=clock, sleeper=clock.sleep)
    result = transport.request("GET", "https://example.test/steady", opener=_sequence_opener([FakeResponse()]), cache=False)
    return _scenario("steady-success", result.attempts == 1 and not result.stale, attempts=result.attempts, stale=result.stale)


def rate_limit_retry_after() -> dict[str, Any]:
    clock = FakeClock(); transport = ResilientTransport(clock=clock, sleeper=clock.sleep)
    result = transport.request("GET", "https://example.test/429", opener=_sequence_opener([_http_error(429, retry_after="2"), FakeResponse()]), cache=False)
    state = transport.snapshot()["providers"][0]
    passed = result.attempts == 2 and result.retry_count == 1 and state["retry_after_honored"] == 1 and any(delay >= 2 for delay in clock.sleeps)
    return _scenario("429-retry-after", passed, attempts=result.attempts, retry_count=result.retry_count, retry_after_honored=state["retry_after_honored"])


def service_unavailable_recovery() -> dict[str, Any]:
    clock = FakeClock(); transport = ResilientTransport(clock=clock, sleeper=clock.sleep)
    result = transport.request("GET", "https://example.test/503", opener=_sequence_opener([_http_error(503), _http_error(503), FakeResponse()]), cache=False)
    return _scenario("503-recovery", result.attempts == 3 and result.retry_count == 2 and result.circuit_state == "closed", attempts=result.attempts, retry_count=result.retry_count)


def explicit_stale_fallback() -> dict[str, Any]:
    clock = FakeClock(); transport = ResilientTransport(clock=clock, sleeper=clock.sleep)
    url = "https://example.test/stale"
    transport.request("GET", url, opener=_sequence_opener([FakeResponse(b'{"value":1}')]), cache=True)
    clock.advance(121)
    result = transport.request("GET", url, opener=_sequence_opener([_http_error(503), _http_error(503), _http_error(503)]), cache=True, stale_if_error=True)
    return _scenario("explicit-stale-fallback", result.stale is True and result.cache_status == "stale-error", cache_status=result.cache_status, stale=result.stale)


def circuit_opening() -> dict[str, Any]:
    clock = FakeClock(); transport = ResilientTransport(clock=clock, sleeper=clock.sleep)
    for _ in range(3):
        try:
            transport.request("GET", "https://example.test/circuit", opener=_sequence_opener([_http_error(503)]), cache=False, retry_safe=False)
        except RuntimeError:
            pass
    rejected = False
    try:
        transport.request("GET", "https://example.test/circuit", opener=_sequence_opener([FakeResponse()]), cache=False, retry_safe=False)
    except CircuitOpenError:
        rejected = True
    state = transport.snapshot()["providers"][0]
    return _scenario("circuit-opening", rejected and state["circuit_state"] == "open" and state["circuit_open_rejections"] == 1, circuit_state=state["circuit_state"])


def circuit_recovery() -> dict[str, Any]:
    clock = FakeClock(); transport = ResilientTransport(clock=clock, sleeper=clock.sleep)
    url = "https://example.test/recovery"
    for _ in range(3):
        try:
            transport.request("GET", url, opener=_sequence_opener([_http_error(503)]), cache=False, retry_safe=False)
        except RuntimeError:
            pass
    clock.advance(61)
    result = transport.request("GET", url, opener=_sequence_opener([FakeResponse()]), cache=False, retry_safe=False)
    state = transport.snapshot()["providers"][0]
    return _scenario("circuit-recovery", result.circuit_state == "closed" and state["consecutive_failures"] == 0, circuit_state=state["circuit_state"])


def provider_flapping_24_cycles() -> dict[str, Any]:
    clock = FakeClock(); transport = ResilientTransport(clock=clock, sleeper=clock.sleep)
    successes = failures = 0
    for cycle in range(FLAP_CYCLES):
        event = FakeResponse() if cycle % 2 == 0 else _http_error(503)
        try:
            transport.request("GET", "https://example.test/flap", opener=_sequence_opener([event]), cache=False, retry_safe=False)
            successes += 1
        except RuntimeError:
            failures += 1
    state = transport.snapshot()["providers"][0]
    passed = successes == 12 and failures == 12 and state["circuit_state"] == "closed" and state["consecutive_failures"] == 1
    return _scenario("24-cycle-provider-flapping", passed, cycles=FLAP_CYCLES, successes=successes, degraded_cycles=failures, final_circuit_state=state["circuit_state"])


def missing_credential_degradation() -> dict[str, Any]:
    registry = credential_registry(object())
    missing = registry["states"]["missing"]
    passed = registry["ok"] is True and registry["configuration_complete"] is False and missing == registry["profile_count"] and registry["network_calls_performed"] is False
    return _scenario("missing-credential-degradation", passed, missing_profiles=missing, profile_count=registry["profile_count"], release_blocking=False)


SCENARIOS = (
    steady_success,
    rate_limit_retry_after,
    service_unavailable_recovery,
    explicit_stale_fallback,
    circuit_opening,
    circuit_recovery,
    provider_flapping_24_cycles,
    missing_credential_degradation,
)


def run_soak_suite(settings: Any = None) -> dict[str, Any]:
    rows = [func() for func in SCENARIOS]
    semantics = evidence_semantics_readiness()
    checks = {
        "eight_deterministic_scenarios": len(rows) == SCENARIO_COUNT,
        "all_scenarios_pass": all(row["passed"] for row in rows),
        "twenty_four_cycle_flapping_exercised": next(row for row in rows if row["id"] == "24-cycle-provider-flapping")["cycles"] == FLAP_CYCLES,
        "semantic_truth_guard_ready": semantics["ok"] is True,
        "network_calls_avoided": True,
        "live_provider_operator_soak_non_blocking": True,
        "upstream_health_release_blocking_false": True,
    }
    flapping = next(row for row in rows if row["id"] == "24-cycle-provider-flapping")
    return {
        "ok": all(checks.values()), "version": VERSION, "contract": CONTRACT,
        "scenario_count": len(rows), "passed_scenario_count": sum(row["passed"] for row in rows),
        "scenarios": rows, "flapping": dict(flapping), "checks": checks, "evidence_semantics": semantics,
        "network_calls_performed": False, "upstream_health_release_blocking": False,
        "operator_live_soak": {"required_for_release": False, "network_calls_performed": False, "purpose": "Post-deployment operator verification of real-provider flapping without making third-party health a release gate."},
    }


def readiness(settings: Any = None) -> dict[str, Any]:
    result = run_soak_suite(settings)
    return {
        "ok": result["ok"], "version": VERSION, "contract": CONTRACT,
        "scenario_count": result["scenario_count"], "passed_scenario_count": result["passed_scenario_count"],
        "checks": result["checks"], "scenario_ids": [row["id"] for row in result["scenarios"]],
        "network_calls_performed": False, "upstream_health_release_blocking": False,
    }
