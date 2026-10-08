"""Site Intelligence v4.56.1 Platform Core cross-domain bridge recovery.

This module does not duplicate provider adapters from Platform Core. It exposes a
public-safe view of Core's source/connector catalog, reports domain coverage, and
certifies that Site Intelligence can consume Core through either the scoped
public API or the private sc-internal read surface.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Any, Mapping

from .global_conditions_observatory import _core_json, _items, core_read_config
from .version import APP_VERSION, RELEASE_NAME

SCHEMA = "sc-site-intelligence-core-domain-bridge/1.0"

DOMAIN_CONNECTOR_DOMAINS: dict[str, set[str]] = {
    "law": {"international_law"},
    "economics": {
        "economics", "finance", "labour", "company_finance", "energy",
        "agriculture", "demographics", "sustainability",
    },
    "humanitarian": {"humanitarian", "demographics", "international_law", "sustainability"},
    "science": {
        "earth_science", "atmospheric_science", "hydrology", "biomedical_science",
        "chemistry", "biodiversity", "materials_science", "astronomy",
        "high_energy_astrophysics", "infrared_astronomy", "space_science",
    },
    "resources": {"energy", "economics", "agriculture", "hydrology", "earth_science", "sustainability"},
    "dossiers": {"*"},
}

EXPECTED_SOURCE_MINIMUM = 40
EXPECTED_CONNECTOR_MINIMUM = 39


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any, limit: int = 300) -> str:
    return str(value or "").strip()[:limit]


def _safe_source(item: Mapping[str, Any]) -> dict[str, Any]:
    metadata = item.get("metadata") if isinstance(item.get("metadata"), Mapping) else {}
    return {
        "id": _safe_text(item.get("id"), 160),
        "name": _safe_text(item.get("name"), 240),
        "organization": _safe_text(item.get("organization"), 240),
        "review_status": _safe_text(item.get("review_status"), 80),
        "access_cost": _safe_text(item.get("access_cost"), 40),
        "api_key_requirement": _safe_text(item.get("api_key_requirement"), 120),
        "active": bool(item.get("active", True)),
        "domain": _safe_text(metadata.get("domain"), 100),
        "official": bool(metadata.get("official", False)),
    }


def _safe_connector(item: Mapping[str, Any]) -> dict[str, Any]:
    caps = item.get("capabilities")
    if not isinstance(caps, list):
        caps = item.get("capabilities_json")
    if not isinstance(caps, list):
        caps = []
    return {
        "id": _safe_text(item.get("id"), 180),
        "source_id": _safe_text(item.get("source_id"), 160),
        "name": _safe_text(item.get("name"), 260),
        "domain": _safe_text(item.get("domain"), 100),
        "enabled": bool(item.get("enabled", True)),
        "status": _safe_text(item.get("status"), 80),
        "capabilities": [_safe_text(value, 120) for value in caps[:40]],
        "last_health_status": _safe_text(item.get("last_health_status"), 80),
        "last_success_at": _safe_text(item.get("last_success_at"), 80),
    }


def bridge_manifest(settings: Any = None) -> dict[str, Any]:
    config = core_read_config(settings)
    return {
        "ok": True,
        "schema": SCHEMA,
        "version": APP_VERSION,
        "release_name": RELEASE_NAME,
        "generated_at": _now(),
        "core": {
            "enabled": config.enabled,
            "configured": config.configured,
            "base_url_configured": bool(config.base_url),
            "public_api_key_configured": bool(config.api_key),
            "internal_service": config.internal_service,
            "read_mode": config.read_mode,
            "credential_exposed": False,
        },
        "domain_workspaces": sorted(DOMAIN_CONNECTOR_DOMAINS),
        "catalog_targets": {
            "minimum_sources": EXPECTED_SOURCE_MINIMUM,
            "minimum_connectors": EXPECTED_CONNECTOR_MINIMUM,
        },
        "rules": [
            "Platform Core owns provider adapters and ingestion authority.",
            "Site Intelligence consumes Core records and catalogs; it does not duplicate Core connectors.",
            "Private Core reads are allowed only for explicitly recognized internal service hosts.",
            "Public Core reads use the scoped /api/v1 surface.",
            "Connector registration does not imply successful ingestion or record availability.",
            "No provider record, readiness state, or legal conclusion is fabricated.",
        ],
    }


def source_catalog(settings: Any = None) -> dict[str, Any]:
    config = core_read_config(settings)
    if not config.configured:
        return {
            "ok": False,
            "schema": SCHEMA,
            "version": APP_VERSION,
            "state": "core-unconfigured",
            "generated_at": _now(),
            "source_count": 0,
            "connector_count": 0,
            "sources": [],
            "connectors": [],
            "credential_exposed": False,
        }
    try:
        source_payload = _core_json(config, "/api/v1/live/sources", {"active": "true"}, cache_key="v4561:core-sources")
        connector_payload = _core_json(config, "/api/v1/live/connectors", {"enabled": "true"}, cache_key="v4561:core-connectors")
        sources = [_safe_source(item) for item in _items(source_payload, "sources", "items")]
        connectors = [_safe_connector(item) for item in _items(connector_payload, "connectors", "items")]
        return {
            "ok": True,
            "schema": SCHEMA,
            "version": APP_VERSION,
            "state": "connected",
            "generated_at": _now(),
            "read_mode": config.read_mode,
            "source_count": len(sources),
            "connector_count": len(connectors),
            "sources": sources,
            "connectors": connectors,
            "credential_exposed": False,
        }
    except RuntimeError as exc:
        return {
            "ok": False,
            "schema": SCHEMA,
            "version": APP_VERSION,
            "state": "degraded",
            "generated_at": _now(),
            "message": str(exc)[:500],
            "source_count": 0,
            "connector_count": 0,
            "sources": [],
            "connectors": [],
            "credential_exposed": False,
        }


def domain_coverage(settings: Any = None, *, domain: str) -> dict[str, Any]:
    key = str(domain or "").strip().lower()
    if key not in DOMAIN_CONNECTOR_DOMAINS:
        raise KeyError(key)
    catalog = source_catalog(settings)
    connectors = catalog.get("connectors", []) if catalog.get("ok") else []
    allowed = DOMAIN_CONNECTOR_DOMAINS[key]
    if "*" in allowed:
        selected = list(connectors)
    else:
        selected = [item for item in connectors if item.get("domain") in allowed]
    source_ids = {item.get("source_id") for item in selected if item.get("source_id")}
    sources = [item for item in catalog.get("sources", []) if item.get("id") in source_ids]
    by_domain = Counter(item.get("domain") or "unclassified" for item in selected)
    return {
        "ok": bool(catalog.get("ok")),
        "schema": SCHEMA,
        "version": APP_VERSION,
        "state": catalog.get("state", "unavailable"),
        "generated_at": _now(),
        "workspace": key,
        "read_mode": catalog.get("read_mode"),
        "connector_domains": sorted(allowed),
        "source_count": len(sources),
        "connector_count": len(selected),
        "connectors_by_domain": dict(sorted(by_domain.items())),
        "sources": sources,
        "connectors": selected,
        "catalog_source_count": int(catalog.get("source_count") or 0),
        "catalog_connector_count": int(catalog.get("connector_count") or 0),
        "credential_exposed": False,
    }


def diagnostics(settings: Any = None, *, probe: bool = False, country: str = "KEN") -> dict[str, Any]:
    manifest = bridge_manifest(settings)
    catalog = source_catalog(settings)
    domains = {name: domain_coverage(settings, domain=name) for name in DOMAIN_CONNECTOR_DOMAINS}
    result = {
        "ok": bool(catalog.get("ok")),
        "schema": SCHEMA,
        "version": APP_VERSION,
        "release_name": RELEASE_NAME,
        "generated_at": _now(),
        "bridge": manifest["core"],
        "catalog": {
            "state": catalog.get("state"),
            "source_count": catalog.get("source_count", 0),
            "connector_count": catalog.get("connector_count", 0),
            "minimum_source_target_met": int(catalog.get("source_count") or 0) >= EXPECTED_SOURCE_MINIMUM,
            "minimum_connector_target_met": int(catalog.get("connector_count") or 0) >= EXPECTED_CONNECTOR_MINIMUM,
        },
        "domains": {
            name: {
                "source_count": row["source_count"],
                "connector_count": row["connector_count"],
                "connectors_by_domain": row["connectors_by_domain"],
            }
            for name, row in domains.items()
        },
        "probe": bool(probe),
        "credential_exposed": False,
    }
    if probe:
        from .api_reliability_v455311 import CANONICAL_CAPABILITIES, probe_capability
        rows = []
        for capability in CANONICAL_CAPABILITIES:
            payload, status = probe_capability(capability, settings, country=country, limit=5)
            rows.append({
                "capability": capability,
                "http_status": status,
                "dependency_state": payload.get("dependency_state"),
                "data_state": payload.get("data_state"),
                "record_count": payload.get("record_count", 0),
                "ok": payload.get("ok", False),
            })
        result["capability_probes"] = rows
        result["probe_ok"] = all(row["http_status"] < 500 for row in rows)
    return result
