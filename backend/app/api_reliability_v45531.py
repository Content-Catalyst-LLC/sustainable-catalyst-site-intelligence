"""Site Intelligence v4.55.3.1 API reliability and contract-truth layer.

This module does not add domain capability. It makes runtime state explicit so a
client can distinguish process liveness, dependency readiness, a valid empty
result, a degraded partial result, and an unavailable dependency.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Mapping

from .global_conditions_observatory import _core_json, core_read_config
from .version import APP_VERSION

CONTRACT_SCHEMA = "sc-site-intelligence-api-contract-truth/1.0"
HEALTH_SCHEMA = "sc-site-intelligence-capability-health/1.0"
RELIABLE_RESPONSE_SCHEMA = "sc-site-intelligence-reliable-response/1.0"
GOOD_STATES = {"connected", "live", "partial-live", "cached", "reference-snapshot", "available", "ready"}
PARTIAL_STATES = {"degraded", "partial", "delayed", "stale"}
BAD_STATES = {"disabled", "core-unconfigured", "unavailable", "error", "failed", "offline"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def api_contract_truth_manifest() -> dict[str, Any]:
    return {
        "ok": True,
        "schema": CONTRACT_SCHEMA,
        "version": APP_VERSION,
        "release": "API Reliability & Contract Truth Repair",
        "semantics": {
            "health": "Process liveness only. A 200 response does not assert provider or domain-data readiness.",
            "ready": "Required data dependency readiness. Returns HTTP 503 when Platform Core is unconfigured or unreachable.",
            "capability_health": "Explicit per-domain configuration and optional live-probe state.",
            "reliable_domain_routes": "Return HTTP 503 with ok=false when the requested domain dependency is unavailable, HTTP 206 for usable degraded results, and HTTP 200 for connected results including a legitimate no-records result.",
        },
        "truth_rules": [
            "HTTP 200 is not sufficient evidence that a domain dependency is healthy.",
            "An empty connected query is reported as no-records, not dependency-unavailable.",
            "A dependency failure is never converted to ok=true by the reliable API surface.",
            "Legacy routes remain available for compatibility and may preserve historical payload shapes.",
            "Capability maturity is explicit; legacy main.py ownership is not evidence of production maturity.",
        ],
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
        payload = _core_json(config, "/health", cache_key="v45531:core-health")
    except RuntimeError as exc:
        return {"ok": False, "state": "unavailable", "configured": True, "detail": str(exc)}
    upstream_ok = not isinstance(payload, Mapping) or payload.get("ok", True) is not False
    return {
        "ok": bool(upstream_ok),
        "state": "connected" if upstream_ok else "degraded",
        "configured": True,
        "detail": "Platform Core health probe succeeded." if upstream_ok else "Platform Core health endpoint reported not-ok.",
    }


def build_readiness(settings: Any = None) -> dict[str, Any]:
    core = _core_probe(settings)
    ready = core["state"] == "connected"
    return {
        "ok": ready,
        "ready": ready,
        "schema": "sc-site-intelligence-readiness/1.0",
        "version": APP_VERSION,
        "generated_at": _now(),
        "state": "ready" if ready else "not-ready",
        "required_dependencies": {"platform_core": core},
        "liveness_is_not_readiness": True,
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
    """Translate historical domain payloads into truthful transport semantics."""
    source = dict(payload)
    state, detail = _integration_state(source)
    count = _result_count(source)
    legacy_ok = source.get("ok")

    if state in GOOD_STATES:
        status = 200
        ok = True
        data_state = "records" if count > 0 else "no-records"
    elif state in PARTIAL_STATES and count > 0:
        status = 206
        ok = True
        data_state = "partial-records"
    else:
        status = 503
        ok = False
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
        if not is_enabled:
            state = "disabled"
        elif capability == "dossiers":
            state = "configured-unverified" if core.configured else "core-unconfigured"
        else:
            state = "configured-unverified" if core.configured else "core-unconfigured"
        rows.append({"capability": capability, "enabled": is_enabled, "state": state, "live_probe": False})
    return rows


def _live_domain_payloads(settings: Any = None) -> list[tuple[str, Mapping[str, Any]]]:
    from .economics_markets_sustainability import build_economic_records
    from .humanitarian_conflict_displacement_observatory import build_records as build_humanitarian_records
    from .international_law_observatory import build_law_records
    from .scientific_earth_systems_observatory import build_science_records
    from .trade_energy_resource_security_observatory import build_records as build_resource_records

    return [
        ("economics", build_economic_records(settings, limit=1)),
        ("law", build_law_records(settings, limit=1)),
        ("science", build_science_records(settings, limit=1)),
        ("humanitarian", build_humanitarian_records(settings, limit=1, days=1)),
        ("resources", build_resource_records(settings, limit=1)),
    ]


def build_capability_health(settings: Any = None, *, probe: bool = False) -> dict[str, Any]:
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
            "capabilities": capabilities,
            "note": "Set probe=true to exercise the live domain bridges. Configuration alone is not production evidence.",
        }

    rows: list[dict[str, Any]] = []
    for capability, payload in _live_domain_payloads(settings):
        normalized, http_status = normalize_reliable_payload(payload, capability=capability)
        rows.append({
            "capability": capability,
            "state": normalized["dependency_state"],
            "data_state": normalized["data_state"],
            "record_count": normalized["record_count"],
            "ok": normalized["ok"],
            "http_status_if_requested": http_status,
            "live_probe": True,
            "detail": normalized.get("truth_detail") or "",
        })
    usable = sum(1 for row in rows if row["ok"])
    bad = sum(1 for row in rows if not row["ok"])
    if bad == 0:
        overall = "ready"
    elif usable:
        overall = "degraded"
    else:
        overall = "not-ready"
    return {
        "ok": bad == 0,
        "schema": HEALTH_SCHEMA,
        "version": APP_VERSION,
        "generated_at": _now(),
        "probe": True,
        "overall_state": overall,
        "usable_capabilities": usable,
        "unavailable_capabilities": bad,
        "capabilities": rows,
    }
