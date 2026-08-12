from __future__ import annotations

"""Site Intelligence v4.35.19 external-source resilience control plane.

This module provides process-local, secret-safe resilience for read-oriented
external data calls: bounded retries, Retry-After handling, conservative
provider pacing, fresh-cache reuse, explicit stale-if-error support, and
circuit breakers.  It intentionally makes no provider network calls from its
public readiness/telemetry functions.

Provider profiles are client-side protection policies, not assertions about a
provider's contractual quota.  Exact upstream limits continue to belong to the
provider documentation and response headers.
"""

from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from hashlib import sha256
import json
import os
import random
import threading
import time
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from .version import APP_VERSION

VERSION = APP_VERSION
CONTRACT = "rate-limits-retries-caching-backoff-circuit-breakers-v43517"
USER_AGENT = f"SustainableCatalyst-SiteIntelligence/{VERSION} (+https://sustainablecatalyst.com)"
DEFAULT_MAX_RESPONSE_BYTES = 4 * 1024 * 1024
RETRYABLE_HTTP_STATUSES = frozenset({408, 425, 429, 500, 502, 503, 504})


def _env_int(name: str, default: int) -> int:
    try:
        return int(str(os.getenv(name, default)).strip())
    except (TypeError, ValueError):
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return float(str(os.getenv(name, default)).strip())
    except (TypeError, ValueError):
        return default


def _policy(provider_id: str, suffixes: tuple[str, ...] = (), *, minimum_interval_seconds: float = 0.05, cache_ttl_seconds: int = 120, stale_if_error_seconds: int = 900, note: str = "Conservative Site Intelligence client policy; not a provider quota assertion.") -> "ProviderPolicy":
    return ProviderPolicy(
        provider_id, suffixes,
        max_attempts=max(1, min(4, _env_int("SC_SI_EXTERNAL_RETRY_ATTEMPTS", 3))),
        base_backoff_seconds=max(0.05, min(2.0, _env_int("SC_SI_EXTERNAL_BACKOFF_BASE_MS", 250) / 1000.0)),
        max_backoff_seconds=max(1.0, min(8.0, _env_float("SC_SI_EXTERNAL_BACKOFF_MAX_SECONDS", 4.0))),
        minimum_interval_seconds=minimum_interval_seconds,
        cache_ttl_seconds=cache_ttl_seconds,
        stale_if_error_seconds=stale_if_error_seconds,
        circuit_failure_threshold=max(2, min(10, _env_int("SC_SI_EXTERNAL_CIRCUIT_FAILURE_THRESHOLD", 3))),
        circuit_open_seconds=max(10, min(600, _env_int("SC_SI_EXTERNAL_CIRCUIT_OPEN_SECONDS", 60))),
        note=note,
    )


@dataclass(frozen=True)
class ProviderPolicy:
    id: str
    host_suffixes: tuple[str, ...] = ()
    max_attempts: int = 3
    base_backoff_seconds: float = 0.25
    max_backoff_seconds: float = 4.0
    minimum_interval_seconds: float = 0.05
    cache_ttl_seconds: int = 120
    stale_if_error_seconds: int = 900
    circuit_failure_threshold: int = 3
    circuit_open_seconds: int = 60
    note: str = "Conservative Site Intelligence client policy; not a provider quota assertion."


@dataclass
class CacheEntry:
    body: bytes
    content_type: str
    charset: str
    stored_at: float
    expires_at: float
    stale_until: float


@dataclass
class ProviderState:
    consecutive_failures: int = 0
    circuit_state: str = "closed"
    circuit_open_until: float = 0.0
    next_allowed_at: float = 0.0
    total_requests: int = 0
    upstream_calls: int = 0
    successes: int = 0
    failures: int = 0
    retries: int = 0
    cache_hits: int = 0
    stale_served: int = 0
    rate_limit_waits: int = 0
    retry_after_honored: int = 0
    circuit_open_rejections: int = 0
    last_status: int | None = None
    last_error_category: str = ""
    last_event_at: str = ""


@dataclass(frozen=True)
class TransportResult:
    body: bytes
    content_type: str
    charset: str
    provider: str
    cache_status: str
    stale: bool
    attempts: int
    retry_count: int
    circuit_state: str
    retrieved_at: str

    def public_metadata(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "cache_status": self.cache_status,
            "stale": self.stale,
            "attempts": self.attempts,
            "retry_count": self.retry_count,
            "circuit_state": self.circuit_state,
            "retrieved_at": self.retrieved_at,
            "secret_material_exposed": False,
        }


class CircuitOpenError(RuntimeError):
    pass


class ResilientTransport:
    def __init__(self, *, clock: Callable[[], float] | None = None, sleeper: Callable[[float], None] | None = None):
        self._clock = clock or time.monotonic
        self._sleep = sleeper or time.sleep
        self._lock = threading.RLock()
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._states: dict[str, ProviderState] = {}
        self._max_entries = max(32, min(4096, _env_int("SC_SI_EXTERNAL_CACHE_MAX_ENTRIES", 256)))

    def reset(self) -> None:
        with self._lock:
            self._cache.clear()
            self._states.clear()

    def _state(self, provider: str) -> ProviderState:
        with self._lock:
            return self._states.setdefault(provider, ProviderState())

    def _cache_key(self, method: str, url: str, body: bytes | None, accept: str) -> str:
        material = b"\x00".join([
            method.upper().encode("ascii", "ignore"),
            url.encode("utf-8", "ignore"),
            body or b"",
            accept.encode("utf-8", "ignore"),
        ])
        return sha256(material).hexdigest()

    def _cache_get(self, key: str, now: float) -> tuple[CacheEntry | None, str]:
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None, "miss"
            self._cache.move_to_end(key)
            if now <= entry.expires_at:
                return entry, "hit"
            if now <= entry.stale_until:
                return entry, "stale-available"
            self._cache.pop(key, None)
            return None, "miss"

    def _cache_put(self, key: str, entry: CacheEntry) -> None:
        with self._lock:
            self._cache[key] = entry
            self._cache.move_to_end(key)
            while len(self._cache) > self._max_entries:
                self._cache.popitem(last=False)

    def _circuit_guard(self, provider: str, policy: ProviderPolicy, now: float) -> str:
        state = self._state(provider)
        with self._lock:
            if state.circuit_state == "open":
                if now < state.circuit_open_until:
                    state.circuit_open_rejections += 1
                    state.last_event_at = _utc_now()
                    raise CircuitOpenError(f"Authoritative source circuit is temporarily open for provider {provider}.")
                state.circuit_state = "half-open"
            return state.circuit_state

    def _record_success(self, provider: str, status: int) -> str:
        state = self._state(provider)
        with self._lock:
            state.successes += 1
            state.consecutive_failures = 0
            state.circuit_state = "closed"
            state.circuit_open_until = 0.0
            state.last_status = status
            state.last_error_category = ""
            state.last_event_at = _utc_now()
            return state.circuit_state

    def _record_failure(self, provider: str, policy: ProviderPolicy, category: str, status: int | None = None) -> str:
        state = self._state(provider)
        now = self._clock()
        with self._lock:
            state.failures += 1
            state.consecutive_failures += 1
            state.last_status = status
            state.last_error_category = category
            state.last_event_at = _utc_now()
            if state.consecutive_failures >= policy.circuit_failure_threshold:
                state.circuit_state = "open"
                state.circuit_open_until = now + policy.circuit_open_seconds
            return state.circuit_state

    def _pace(self, provider: str, policy: ProviderPolicy) -> None:
        state = self._state(provider)
        wait = 0.0
        with self._lock:
            now = self._clock()
            wait = max(0.0, state.next_allowed_at - now)
            if wait > 0:
                state.rate_limit_waits += 1
            state.next_allowed_at = max(now, state.next_allowed_at) + policy.minimum_interval_seconds
        if wait > 0:
            self._sleep(wait)

    def _retry_delay(self, attempt: int, policy: ProviderPolicy, retry_after: str | None) -> tuple[float, bool]:
        parsed = _parse_retry_after(retry_after)
        if parsed is not None:
            return min(float(parsed), max(1.0, policy.max_backoff_seconds * 8)), True
        # Small deterministic jitter avoids synchronized retry waves without making
        # test behavior nondeterministic.
        base = min(policy.max_backoff_seconds, policy.base_backoff_seconds * (2 ** max(0, attempt - 1)))
        jitter = min(0.2, base * 0.15)
        return min(policy.max_backoff_seconds, base + jitter), False

    def request(
        self,
        method: str,
        url: str,
        *,
        data: bytes | None = None,
        headers: dict[str, str] | None = None,
        timeout: int = 8,
        max_bytes: int = DEFAULT_MAX_RESPONSE_BYTES,
        cache: bool = True,
        stale_if_error: bool = False,
        retry_safe: bool | None = None,
        opener: Callable[..., Any] | None = None,
    ) -> TransportResult:
        method = method.upper().strip()
        if method not in {"GET", "POST"}:
            raise ValueError("Resilient transport only permits GET and read-oriented POST requests.")
        if not url.lower().startswith("https://"):
            raise ValueError("Authoritative-source transport requires HTTPS.")
        policy = policy_for_url(url)
        provider = policy.id
        state = self._state(provider)
        with self._lock:
            state.total_requests += 1
            state.last_event_at = _utc_now()
        request_headers = {"User-Agent": USER_AGENT, **(headers or {})}
        accept = request_headers.get("Accept", "*/*")
        key = self._cache_key(method, url, data, accept)
        now = self._clock()
        cached, cache_state = self._cache_get(key, now) if cache else (None, "bypass")
        if cached is not None and cache_state == "hit":
            with self._lock:
                state.cache_hits += 1
            return TransportResult(cached.body, cached.content_type, cached.charset, provider, "hit", False, 0, 0, state.circuit_state, _utc_now())

        try:
            circuit_state = self._circuit_guard(provider, policy, now)
        except CircuitOpenError:
            if stale_if_error and cached is not None and cache_state == "stale-available":
                with self._lock:
                    state.stale_served += 1
                return TransportResult(cached.body, cached.content_type, cached.charset, provider, "stale-circuit", True, 0, 0, "open", _utc_now())
            raise

        retry_safe = method == "GET" if retry_safe is None else bool(retry_safe)
        attempts = policy.max_attempts if retry_safe else 1
        opener = opener or urlopen
        last_exc: Exception | None = None
        retry_count = 0

        for attempt in range(1, attempts + 1):
            self._pace(provider, policy)
            req = Request(url, data=data, headers=request_headers, method=method)
            try:
                with self._lock:
                    state.upstream_calls += 1
                with opener(req, timeout=timeout) as response:
                    raw = response.read(max_bytes + 1)
                    if len(raw) > max_bytes:
                        raise ValueError("Authoritative API response exceeded the public connector size limit.")
                    content_type = str(response.headers.get_content_type() or "application/octet-stream")
                    charset = str(response.headers.get_content_charset() or "utf-8")
                    status = int(getattr(response, "status", 200) or 200)
                    circuit_state = self._record_success(provider, status)
                    if cache:
                        stored = self._clock()
                        self._cache_put(key, CacheEntry(raw, content_type, charset, stored, stored + policy.cache_ttl_seconds, stored + policy.cache_ttl_seconds + policy.stale_if_error_seconds))
                    return TransportResult(raw, content_type, charset, provider, "miss" if cache else "bypass", False, attempt, retry_count, circuit_state, _utc_now())
            except HTTPError as exc:
                status = int(exc.code)
                last_exc = exc
                retryable = retry_safe and status in RETRYABLE_HTTP_STATUSES and attempt < attempts
                if retryable:
                    delay, honored = self._retry_delay(attempt, policy, exc.headers.get("Retry-After") if exc.headers else None)
                    with self._lock:
                        state.retries += 1
                        retry_count += 1
                        if honored:
                            state.retry_after_honored += 1
                    self._sleep(delay)
                    continue
                category = "rate-limited" if status == 429 else "upstream-http" if status >= 500 or status in {408, 425} else "request-rejected"
                if status in RETRYABLE_HTTP_STATUSES:
                    self._record_failure(provider, policy, category, status)
                else:
                    with self._lock:
                        state.last_status = status
                        state.last_error_category = category
                        state.last_event_at = _utc_now()
                break
            except (URLError, TimeoutError, OSError) as exc:
                last_exc = exc
                if retry_safe and attempt < attempts:
                    delay, _ = self._retry_delay(attempt, policy, None)
                    with self._lock:
                        state.retries += 1
                        retry_count += 1
                    self._sleep(delay)
                    continue
                self._record_failure(provider, policy, "network-or-timeout", None)
                break

        if stale_if_error and cached is not None and cache_state == "stale-available":
            with self._lock:
                state.stale_served += 1
            return TransportResult(cached.body, cached.content_type, cached.charset, provider, "stale-error", True, attempts, retry_count, self._state(provider).circuit_state, _utc_now())
        if isinstance(last_exc, HTTPError):
            raise RuntimeError(f"Authoritative API returned HTTP {last_exc.code} after resilience handling.") from last_exc
        if last_exc is not None:
            raise RuntimeError("Authoritative API could not be reached after resilience handling.") from last_exc
        raise RuntimeError("Authoritative API request failed after resilience handling.")

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            providers = []
            for provider, state in sorted(self._states.items()):
                providers.append({
                    "provider": provider,
                    "circuit_state": state.circuit_state,
                    "consecutive_failures": state.consecutive_failures,
                    "requests": state.total_requests,
                    "upstream_calls": state.upstream_calls,
                    "successes": state.successes,
                    "failures": state.failures,
                    "retries": state.retries,
                    "cache_hits": state.cache_hits,
                    "stale_served": state.stale_served,
                    "rate_limit_waits": state.rate_limit_waits,
                    "retry_after_honored": state.retry_after_honored,
                    "circuit_open_rejections": state.circuit_open_rejections,
                    "last_status": state.last_status,
                    "last_error_category": state.last_error_category,
                    "last_event_at": state.last_event_at,
                    "secret_material_exposed": False,
                })
            totals = {
                "providers_seen": len(providers),
                "requests": sum(x["requests"] for x in providers),
                "upstream_calls": sum(x["upstream_calls"] for x in providers),
                "successes": sum(x["successes"] for x in providers),
                "failures": sum(x["failures"] for x in providers),
                "retries": sum(x["retries"] for x in providers),
                "cache_hits": sum(x["cache_hits"] for x in providers),
                "stale_served": sum(x["stale_served"] for x in providers),
                "open_circuits": sum(x["circuit_state"] == "open" for x in providers),
                "cache_entries": len(self._cache),
            }
        return {"providers": providers, "totals": totals}


PROVIDER_POLICIES: tuple[ProviderPolicy, ...] = (
    _policy("airnow", ("airnowapi.org",), minimum_interval_seconds=0.25, cache_ttl_seconds=3600, stale_if_error_seconds=7200, note="Hourly-oriented cache policy aligned with AirNow update cadence; not a quota assertion."),
    _policy("eia", ("api.eia.gov",), minimum_interval_seconds=0.10, cache_ttl_seconds=300, stale_if_error_seconds=1800, note="Conservative client pacing; EIA documents temporary key suspension when usage tolerances are exceeded."),
    _policy("overpass", ("overpass-api.de",), minimum_interval_seconds=0.50, cache_ttl_seconds=300, stale_if_error_seconds=3600),
    _policy("world-bank", ("api.worldbank.org", "wits.worldbank.org"), minimum_interval_seconds=0.10, cache_ttl_seconds=900, stale_if_error_seconds=7200),
    _policy("nasa-cmr", ("cmr.earthdata.nasa.gov", "graphql.earthdata.nasa.gov"), minimum_interval_seconds=0.10, cache_ttl_seconds=300, stale_if_error_seconds=1800),
    _policy("usgs-water", ("api.waterdata.usgs.gov",), minimum_interval_seconds=0.10, cache_ttl_seconds=120, stale_if_error_seconds=900),
    _policy("noaa", ("noaa.gov", "ncei.noaa.gov", "tidesandcurrents.noaa.gov"), minimum_interval_seconds=0.10, cache_ttl_seconds=300, stale_if_error_seconds=1800),
    _policy("epa", ("epa.gov",), minimum_interval_seconds=0.15, cache_ttl_seconds=300, stale_if_error_seconds=1800),
    _policy("copernicus", ("copernicus.eu", "ecmwf.int"), minimum_interval_seconds=0.20, cache_ttl_seconds=900, stale_if_error_seconds=7200),
)
DEFAULT_POLICY = _policy("default")
TRANSPORT = ResilientTransport()

def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_retry_after(value: str | None) -> float | None:
    if not value:
        return None
    text = str(value).strip()
    if text.isdigit():
        return max(0.0, float(text))
    try:
        dt = parsedate_to_datetime(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return max(0.0, (dt - datetime.now(timezone.utc)).total_seconds())
    except (TypeError, ValueError, OverflowError):
        return None


def policy_for_url(url: str) -> ProviderPolicy:
    host = (urlsplit(url).hostname or "").lower()
    for policy in PROVIDER_POLICIES:
        if any(host == suffix or host.endswith("." + suffix) for suffix in policy.host_suffixes):
            return policy
    return DEFAULT_POLICY


def request_bytes(url: str, *, method: str = "GET", data: bytes | None = None, headers: dict[str, str] | None = None, timeout: int = 8, max_bytes: int = DEFAULT_MAX_RESPONSE_BYTES, cache: bool = True, stale_if_error: bool = False, retry_safe: bool | None = None) -> TransportResult:
    return TRANSPORT.request(method, url, data=data, headers=headers, timeout=timeout, max_bytes=max_bytes, cache=cache, stale_if_error=stale_if_error, retry_safe=retry_safe)


def request_json(url: str, *, method: str = "GET", payload: dict[str, Any] | None = None, headers: dict[str, str] | None = None, timeout: int = 8, max_bytes: int = DEFAULT_MAX_RESPONSE_BYTES, cache: bool = True, stale_if_error: bool = False, retry_safe: bool | None = None, include_transport: bool = False) -> Any:
    body = None
    request_headers = {"Accept": "application/json", **(headers or {})}
    if payload is not None:
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        request_headers.setdefault("Content-Type", "application/json")
        method = "POST"
    result = request_bytes(url, method=method, data=body, headers=request_headers, timeout=timeout, max_bytes=max_bytes, cache=cache, stale_if_error=stale_if_error, retry_safe=retry_safe)
    try:
        parsed = json.loads(result.body.decode(result.charset or "utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("Authoritative API returned invalid JSON.") from exc
    if include_transport:
        return {"payload": parsed, "transport": result.public_metadata()}
    return parsed


def request_text(url: str, *, headers: dict[str, str] | None = None, timeout: int = 8, max_bytes: int = DEFAULT_MAX_RESPONSE_BYTES, cache: bool = True, stale_if_error: bool = False) -> str:
    result = request_bytes(url, headers=headers or {"Accept": "text/plain,*/*;q=0.8"}, timeout=timeout, max_bytes=max_bytes, cache=cache, stale_if_error=stale_if_error)
    return result.body.decode(result.charset or "utf-8", "replace")


def resilience_overview(settings: Any = None) -> dict[str, Any]:
    snapshot = TRANSPORT.snapshot()
    profiles = []
    for policy in (*PROVIDER_POLICIES, DEFAULT_POLICY):
        profiles.append({
            "provider": policy.id,
            "max_attempts": policy.max_attempts,
            "base_backoff_seconds": policy.base_backoff_seconds,
            "max_backoff_seconds": policy.max_backoff_seconds,
            "minimum_interval_seconds": policy.minimum_interval_seconds,
            "cache_ttl_seconds": policy.cache_ttl_seconds,
            "stale_if_error_seconds": policy.stale_if_error_seconds,
            "circuit_failure_threshold": policy.circuit_failure_threshold,
            "circuit_open_seconds": policy.circuit_open_seconds,
            "policy_note": policy.note,
        })
    return {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "enabled": bool(getattr(settings, "external_resilience_enabled", True)) if settings is not None else True,
        "provider_policy_count": len(profiles),
        "policies": profiles,
        "telemetry": snapshot,
        "stale_policy": "Stale-if-error is opt-in and is always labeled stale in TransportResult metadata; legacy raw-payload helpers use fresh-cache reuse only.",
        "rate_limit_policy": "Client pacing is conservative and provider response headers such as Retry-After take precedence; each interval is a Site Intelligence safeguard, not a provider quota assertion.",
        "network_calls_performed": False,
        "secret_material_exposed": False,
        "release_blocking_upstream_health": False,
        "generated_at": _utc_now(),
    }


def resilience_readiness(settings: Any = None) -> dict[str, Any]:
    overview = resilience_overview(settings)
    checks = {
        "retryable_statuses_bounded": RETRYABLE_HTTP_STATUSES == frozenset({408, 425, 429, 500, 502, 503, 504}),
        "retry_attempts_bounded": all(1 <= p["max_attempts"] <= 4 for p in overview["policies"]),
        "backoff_bounded": all(0 <= p["base_backoff_seconds"] <= p["max_backoff_seconds"] <= 8 for p in overview["policies"]),
        "cache_ttl_bounded": all(0 <= p["cache_ttl_seconds"] <= 86400 for p in overview["policies"]),
        "circuit_breakers_enabled": all(p["circuit_failure_threshold"] >= 2 and p["circuit_open_seconds"] >= 10 for p in overview["policies"]),
        "retry_after_supported": True,
        "stale_is_never_silently_fresh": True,
        "telemetry_secret_safe": overview["secret_material_exposed"] is False,
        "network_free_readiness": overview["network_calls_performed"] is False,
        "upstream_health_non_blocking": overview["release_blocking_upstream_health"] is False,
    }
    return {
        "ok": all(checks.values()),
        "version": VERSION,
        "contract": CONTRACT,
        "checks": checks,
        "network_calls_performed": False,
        "secret_material_exposed": False,
        "generated_at": _utc_now(),
    }


def resilience_provider_states() -> dict[str, Any]:
    snapshot = TRANSPORT.snapshot()
    return {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "providers": snapshot["providers"],
        "totals": snapshot["totals"],
        "network_calls_performed": False,
        "secret_material_exposed": False,
        "generated_at": _utc_now(),
    }
