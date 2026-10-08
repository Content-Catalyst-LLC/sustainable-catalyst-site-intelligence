"""Site Intelligence v4.55.3.2 live-probe consistency and failure normalization.

This release is intentionally corrective. It does not add providers or domain
features. It makes the canonical reliable routes, capability health, and
readiness use the same probe logic and the same country-context normalization.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import logging
from typing import Any, Callable, Mapping

from .country_identity_v43523 import canonical_country
from .global_conditions_observatory import _core_json, core_read_config
from .version import APP_VERSION

log = logging.getLogger(__name__)

CONTRACT_SCHEMA = "sc-site-intelligence-api-contract-truth/1.1"
HEALTH_SCHEMA = "sc-site-intelligence-capability-health/1.1"
READINESS_SCHEMA = "sc-site-intelligence-readiness/1.1"
RELIABLE_RESPONSE_SCHEMA = "sc-site-intelligence-reliable-response/1.1"

GOOD_STATES = {"connected", "live", "cached", "reference-snapshot", "available", "ready"}
PARTIAL_STATES = {"partial-live", "partial", "delayed", "stale"}
DEGRADED_STATES = {"degraded"}
BAD_STATES = {"disabled", "core-unconfigured", "unavailable", "error", "failed", "offline", "exception"}

CANONICAL_PROBE_COUNTRY = "KEN"
CANONICAL_CAPABILITIES = ("economics", "law", "science", "humanitarian", "resources", "dossiers")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def api_contract_truth_manifest() -> dict[str, Any]:
    return {
        "ok": True,
        "schema": CONTRACT_SCHEMA,
        "version": APP_VERSION,
        "release": "Live Probe Consistency & Domain Failure Normalization",
        "semantics": {
            "health": "Process liveness only. A 200 response does not assert provider or domain-data readiness.",
            "ready": "Platform Core reachability plus canonical domain-operability. Returns HTTP 503 when required domain probes fail.",
            "capability_health": "Uses the same canonical domain probe functions as the reliable public routes.",
            "reliable_domain_routes": "Return structured JSON for expected dependency/runtime failures: 503 unavailable, 206 partial, 200 connected including legitimate no-records.",
        },
        "truth_rules": [
            "HTTP 200 is not sufficient evidence that a domain dependency is healthy.",
            "Platform Core process reachability is not equivalent to domain operability.",
            "Capability health and reliable domain routes must share one probe implementation.",
            "Expected upstream/runtime failures on reliable routes are normalized to JSON and never leak an HTML/plain-text 500 response.",
            "A dependency failure is never converted to ok=true by the reliable API surface.",
            "A connected empty query is no-records, not dependency-unavailable.",
            "A partial-live capability is HTTP 206 whether or not the current query returned records.",
            "Country context is canonicalized through the first-party ISO3/ISO2/name registry before domain querying.",
        ],
        "canonical_probe_country": CANONICAL_PROBE_COUNTRY,
        "canonical_routes": {
            "liveness": "/health",
            "readiness": "/ready",
            "capability_health": "/public/capability-health",
            "economics": "/public/reliable/economics/records",
            "law": "/public/reliable/law/records",
            "science": "/public/reliable/science/records",
            "humanitarian": "/public/reliable/humanitarian/records",
            "resources": "/public/reliable/resources/records",
            "dossiers": "/public/reliable/dossiers/country",
        },
    }


def _core_probe(settings: Any = None) -> dict[str, Any]:
    config = core_read_config(settings)
    if not config.enabled:
        return {"ok": False, "state": "disabled", "configured": False, "detail": "Platform Core reading is disabled."}
    if not config.configured:
        return {"ok": False, "state": "core-unconfigured", "configured": False, "detail": "Platform Core public reading is not configured."}
    try:
        payload = _core_json(config, "/health", cache_key="v455311:core-health")
    except Exception as exc:  # reliability boundary: never make readiness itself crash
        log.warning("Platform Core readiness probe failed: %s", exc)
        return {"ok": False, "state": "unavailable", "configured": True, "detail": str(exc)[:400]}
    upstream_ok = not isinstance(payload, Mapping) or payload.get("ok", True) is not False
    return {
        "ok": bool(upstream_ok),
        "state": "connected" if upstream_ok else "degraded",
        "configured": True,
        "detail": "Platform Core health probe succeeded." if upstream_ok else "Platform Core health endpoint reported not-ok.",
    }


def _integration_state(payload: Mapping[str, Any]) -> tuple[str, str]:
    integration = payload.get("integration")
    if isinstance(integration, Mapping):
        state = str(integration.get("state") or "").strip().lower()
        detail = str(integration.get("message") or "").strip()
        if state:
            return state, detail
    state = str(payload.get("state") or "").strip().lower()
    detail = str(payload.get("message") or payload.get("detail") or "").strip()
    return state or "unknown", detail


def _result_count(payload: Mapping[str, Any]) -> int:
    for key in ("records", "items", "results", "features"):
        value = payload.get(key)
        if isinstance(value, list):
            return len(value)
    for key in ("count", "total", "record_count"):
        value = payload.get(key)
        if isinstance(value, (int, float)):
            return int(value)
    counts = payload.get("counts")
    if isinstance(counts, Mapping):
        for key in ("evidence_records", "records", "records_visible", "records_available"):
            value = counts.get(key)
            if isinstance(value, (int, float)):
                return int(value)
    return 0


def normalize_reliable_payload(payload: Mapping[str, Any], *, capability: str) -> tuple[dict[str, Any], int]:
    """Translate a domain payload into one transport truth contract."""
    source = dict(payload)
    state, detail = _integration_state(source)
    count = _result_count(source)
    legacy_ok = source.get("ok")

    if state in GOOD_STATES:
        status, ok = 200, True
        data_state = "records" if count > 0 else "no-records"
    elif state in PARTIAL_STATES:
        status, ok = 206, True
        data_state = "partial-records" if count > 0 else "partial-no-records"
    elif state in DEGRADED_STATES and count > 0:
        status, ok = 206, True
        data_state = "partial-records"
    else:
        status, ok = 503, False
        data_state = "dependency-unavailable"

    source.update({
        "ok": ok,
        "contract_schema": RELIABLE_RESPONSE_SCHEMA,
        "contract_version": APP_VERSION,
        "capability": capability,
        "dependency_state": state,
        "data_state": data_state,
        "record_count": count,
        "legacy_ok": legacy_ok,
        "truth_detail": detail,
    })
    return source, status


def _country_context(value: str) -> dict[str, Any]:
    token = str(value or CANONICAL_PROBE_COUNTRY).strip() or CANONICAL_PROBE_COUNTRY
    try:
        iso3, record = canonical_country(token)
        return {
            "requested": token,
            "iso3": iso3,
            "iso2": str(record.get("iso2") or "").upper(),
            "name": str(record.get("name") or record.get("display_name") or iso3),
            "resolved": True,
        }
    except Exception:
        upper = token.upper()
        return {"requested": token, "iso3": upper, "iso2": "", "name": token, "resolved": False}


def _exception_payload(capability: str, exc: Exception, *, context: Mapping[str, Any] | None = None) -> dict[str, Any]:
    log.exception("Reliable %s probe raised %s", capability, type(exc).__name__)
    return {
        "ok": False,
        "schema": RELIABLE_RESPONSE_SCHEMA,
        "version": APP_VERSION,
        "generated_at": _now(),
        "integration": {
            "state": "exception",
            "message": f"{capability} probe failed before a valid domain payload was produced.",
            "configured": True,
            "credential_exposed": False,
        },
        "records": [],
        "record_count": 0,
        "failure": {"type": type(exc).__name__, "normalized": True},
        "context_resolution": dict(context or {}),
    }


def _with_context(payload: Mapping[str, Any], context: Mapping[str, Any], attempted: list[str], matched: str = "") -> dict[str, Any]:
    out = dict(payload)
    out["context_resolution"] = {**dict(context), "attempted": attempted, "matched": matched or None}
    return out


def _try_aliases(
    capability: str,
    context: Mapping[str, Any],
    caller: Callable[[str], Mapping[str, Any]],
    candidates: list[str],
) -> dict[str, Any]:
    attempted: list[str] = []
    last: Mapping[str, Any] = {}
    seen: set[str] = set()
    for candidate in candidates:
        candidate = str(candidate or "").strip()
        if not candidate or candidate.casefold() in seen:
            continue
        seen.add(candidate.casefold())
        attempted.append(candidate)
        try:
            payload = caller(candidate)
        except Exception as exc:
            return _with_context(_exception_payload(capability, exc, context=context), context, attempted)
        last = payload
        normalized, status = normalize_reliable_payload(payload, capability=capability)
        if status >= 500:
            return _with_context(payload, context, attempted)
        if normalized["record_count"] > 0:
            return _with_context(payload, context, attempted, candidate)
    return _with_context(last or {"ok": True, "state": "connected", "records": []}, context, attempted)


def probe_capability(
    capability: str,
    settings: Any = None,
    *,
    country: str = CANONICAL_PROBE_COUNTRY,
    limit: int = 1,
    query: str = "",
) -> tuple[dict[str, Any], int]:
    """Execute the same canonical probe used by routes, health, and readiness."""
    from .economics_markets_sustainability import build_economic_records
    from .humanitarian_conflict_displacement_observatory import build_records as build_humanitarian_records
    from .international_law_observatory import build_law_records
    from .scientific_earth_systems_observatory import build_science_records
    from .trade_energy_resource_security_observatory import build_records as build_resource_records
    from .unified_country_regional_dossiers import build_country_dossier

    context = _country_context(country)
    iso3, iso2, name = context["iso3"], context["iso2"], context["name"]
    limit = max(1, min(int(limit), 300))

    try:
        if capability == "economics":
            payload = _try_aliases(
                capability, context,
                lambda code: build_economic_records(settings, geography_code=code, limit=limit),
                [iso3, iso2],
            )
        elif capability == "resources":
            payload = _try_aliases(
                capability, context,
                lambda code: build_resource_records(settings, geography_code=code, limit=limit),
                [iso3, iso2],
            )
        elif capability == "law":
            payload = _try_aliases(
                capability, context,
                lambda code: build_law_records(settings, country=code, limit=limit),
                [iso3, iso2, name],
            )
        elif capability == "humanitarian":
            payload = _try_aliases(
                capability, context,
                lambda code: build_humanitarian_records(settings, country=code, days=30, limit=limit),
                [iso3, iso2],
            )
        elif capability == "science":
            # The v2.5 science bridge has no geography_code parameter. The old
            # reliable route passed one anyway, which raised TypeError and leaked
            # a raw 500. Resolve country context to metadata query text instead.
            science_query = " ".join(part for part in (name, query.strip()) if part).strip()
            payload = build_science_records(settings, query=science_query, limit=limit)
            payload = _with_context(payload, {**context, "context_mode": "metadata-query"}, [science_query], science_query)
        elif capability == "dossiers":
            payload = build_country_dossier(settings, country=iso3, limit_per_domain=max(5, min(limit, 60)))
            payload = _with_context(payload, context, [iso3], iso3)
        else:
            raise ValueError(f"unsupported capability: {capability}")
    except Exception as exc:
        payload = _exception_payload(capability, exc, context=context)

    return normalize_reliable_payload(payload, capability=capability)


def _configured_capabilities(settings: Any = None) -> list[dict[str, Any]]:
    core = core_read_config(settings)
    enabled = {
        "economics": bool(getattr(settings, "economics_sustainability_enabled", True)),
        "law": bool(getattr(settings, "international_law_observatory_enabled", True)),
        "science": bool(getattr(settings, "scientific_earth_systems_enabled", True)),
        "humanitarian": bool(getattr(settings, "humanitarian_conflict_displacement_enabled", True)),
        "resources": bool(getattr(settings, "trade_energy_resource_security_enabled", True)),
        "dossiers": bool(getattr(settings, "unified_dossiers_enabled", True)),
    }
    rows = []
    for capability, is_enabled in enabled.items():
        state = "disabled" if not is_enabled else ("configured-unverified" if core.configured else "core-unconfigured")
        rows.append({"capability": capability, "enabled": is_enabled, "state": state, "live_probe": False})
    return rows


def build_capability_health(settings: Any = None, *, probe: bool = False, country: str = CANONICAL_PROBE_COUNTRY) -> dict[str, Any]:
    if not probe:
        capabilities = _configured_capabilities(settings)
        core = core_read_config(settings)
        overall = "configured-unverified" if core.configured else "not-ready"
        return {
            "ok": core.configured,
            "schema": HEALTH_SCHEMA,
            "version": APP_VERSION,
            "generated_at": _now(),
            "probe": False,
            "overall_state": overall,
            "canonical_probe_country": country,
            "capabilities": capabilities,
            "note": "Set probe=true to exercise the exact canonical probes used by reliable domain routes.",
        }

    rows: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=len(CANONICAL_CAPABILITIES)) as pool:
        futures = {pool.submit(probe_capability, capability, settings, country=country, limit=5): capability for capability in CANONICAL_CAPABILITIES}
        for future in as_completed(futures):
            capability = futures[future]
            try:
                normalized, http_status = future.result()
            except Exception as exc:
                normalized, http_status = normalize_reliable_payload(_exception_payload(capability, exc), capability=capability)
            rows.append({
                "capability": capability,
                "state": normalized["dependency_state"],
                "data_state": normalized["data_state"],
                "record_count": normalized["record_count"],
                "ok": normalized["ok"],
                "http_status_if_requested": http_status,
                "live_probe": True,
                "detail": normalized.get("truth_detail") or "",
                "context_resolution": normalized.get("context_resolution") or {},
            })
    rows.sort(key=lambda item: CANONICAL_CAPABILITIES.index(item["capability"]))
    unavailable = sum(1 for row in rows if row["http_status_if_requested"] >= 500)
    partial = sum(1 for row in rows if row["http_status_if_requested"] == 206)
    usable = sum(1 for row in rows if row["http_status_if_requested"] < 500)
    overall = "ready" if unavailable == 0 and partial == 0 else ("degraded" if usable else "not-ready")
    return {
        "ok": unavailable == 0,
        "schema": HEALTH_SCHEMA,
        "version": APP_VERSION,
        "generated_at": _now(),
        "probe": True,
        "canonical_probe_country": country,
        "overall_state": overall,
        "usable_capabilities": usable,
        "partial_capabilities": partial,
        "unavailable_capabilities": unavailable,
        "capabilities": rows,
    }


def build_readiness(settings: Any = None, *, country: str = CANONICAL_PROBE_COUNTRY) -> dict[str, Any]:
    core = _core_probe(settings)
    if not core["ok"]:
        return {
            "ok": False,
            "ready": False,
            "schema": READINESS_SCHEMA,
            "version": APP_VERSION,
            "generated_at": _now(),
            "state": "platform-unavailable",
            "platform_ready": False,
            "domain_ready": False,
            "required_dependencies": {"platform_core": core},
            "domain_health": None,
            "liveness_is_not_readiness": True,
        }

    domain_health = build_capability_health(settings, probe=True, country=country)
    domain_ready = domain_health["unavailable_capabilities"] == 0
    ready = bool(core["ok"] and domain_ready)
    state = "ready" if ready and domain_health["partial_capabilities"] == 0 else ("domain-partial" if ready else "domain-degraded")
    return {
        "ok": ready,
        "ready": ready,
        "schema": READINESS_SCHEMA,
        "version": APP_VERSION,
        "generated_at": _now(),
        "state": state,
        "platform_ready": True,
        "domain_ready": domain_ready,
        "required_dependencies": {"platform_core": core},
        "domain_health": {
            "overall_state": domain_health["overall_state"],
            "canonical_probe_country": domain_health["canonical_probe_country"],
            "usable_capabilities": domain_health["usable_capabilities"],
            "partial_capabilities": domain_health["partial_capabilities"],
            "unavailable_capabilities": domain_health["unavailable_capabilities"],
            "capabilities": domain_health["capabilities"],
        },
        "liveness_is_not_readiness": True,
    }
