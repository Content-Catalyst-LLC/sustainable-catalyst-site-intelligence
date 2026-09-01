from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .version import APP_VERSION

RELEASE_VERSION = APP_VERSION
CONTRACT = "unified-public-intelligence-platform"
BACKEND_ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = BACKEND_ROOT / "data/unified_public_intelligence_policy_v4000.json"


def _policy() -> dict[str, Any]:
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def _digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _route_directory() -> list[dict[str, Any]]:
    policy = _policy()
    rows: list[dict[str, Any]] = []
    for area_index, area in enumerate(policy["primary_areas"], start=1):
        for route_index, route in enumerate(area["routes"], start=1):
            rows.append({
                "route_id": route,
                "primary_area_id": area["id"],
                "primary_area_label": area["label"],
                "primary_area_order": area_index,
                "route_order": route_index,
                "preserved": True,
            })
    return rows


def public_unified_platform() -> dict[str, Any]:
    policy = _policy()
    routes = _route_directory()
    payload = {
        "ok": True,
        "version": RELEASE_VERSION,
        "contract": CONTRACT,
        "release_name": "Unified Public Intelligence Platform",
        "orbital_earth_extension": "/public/orbital-earth",
        "primary_area_count": len(policy["primary_areas"]),
        "route_count": len(routes),
        "primary_areas": policy["primary_areas"],
        "canonical_contract_count": len(policy["canonical_contracts"]),
        "compatibility": policy["compatibility"],
        "boundaries": policy["boundaries"],
    }
    payload["platform_sha256"] = _digest(payload)
    return payload


def public_unified_navigation() -> dict[str, Any]:
    policy = _policy()
    routes = _route_directory()
    return {
        "ok": True,
        "version": RELEASE_VERSION,
        "primary_area_count": len(policy["primary_areas"]),
        "route_count": len(routes),
        "areas": policy["primary_areas"],
        "routes": routes,
        "all_routes_unique": len({row["route_id"] for row in routes}) == len(routes),
    }


def public_unified_contracts() -> dict[str, Any]:
    policy = _policy()
    contracts = policy["canonical_contracts"]
    return {
        "ok": True,
        "version": RELEASE_VERSION,
        "contract_count": len(contracts),
        "contracts": contracts,
        "single_truth_contract": True,
        "single_route_state_contract": True,
        "single_publication_export_contract": True,
        "human_review_preserved": True,
        "contracts_sha256": _digest(contracts),
    }


CORE_REQUIRED_ROUTES = ("economics", "law", "science", "resources")
CORE_ENHANCED_ROUTES = ("platform", "global", "humanitarian", "dossiers", "alerts", "scenarios")
WORKSPACE_FLAG_MAP = {
    "economics": "economics_sustainability_enabled",
    "law": "international_law_observatory_enabled",
    "science": "scientific_earth_systems_enabled",
    "humanitarian": "humanitarian_conflict_displacement_enabled",
    "resources": "trade_energy_resource_security_enabled",
    "dossiers": "unified_dossiers_enabled",
    "alerts": "alerts_monitoring_enabled",
    "scenarios": "comparative_scenario_studio_enabled",
    "research": "research_workflows_enabled",
    "integration": "public_data_api_enabled",
    "experience": "offline_experience_enabled",
    "spatial": "spatial_evidence_enabled",
    "harmonization": "statistical_harmonization_enabled",
    "models": "model_governance_enabled",
    "evidence": "evidence_synthesis_enabled",
    "graph": "knowledge_graph_enabled",
    "publishing": "intelligence_publishing_enabled",
    "monitoring": "scheduled_monitoring_enabled",
    "workspaces": "institutional_workspaces_enabled",
    "workflows": "cross_platform_workflows_enabled",
    "federation": "federation_exchange_enabled",
    "governance": "production_governance_enabled",
    "platform": "connected_platform_enabled",
}


def _runtime_configuration(settings: Any = None) -> dict[str, Any]:
    def value(name: str, default: Any = None) -> Any:
        return getattr(settings, name, default) if settings is not None else default

    workspace_flags = {route: bool(value(attribute, True)) for route, attribute in WORKSPACE_FLAG_MAP.items()}
    disabled_routes = sorted(route for route, enabled in workspace_flags.items() if not enabled)
    core_enabled = bool(value("platform_core_enabled", False))
    core_base_url_configured = bool(str(value("platform_core_url", "") or "").strip())
    public_key_configured = bool(str(value("platform_core_public_api_key", "") or "").strip())
    write_key_configured = bool(str(value("platform_core_write_api_key", "") or "").strip())
    core_read_configured = core_enabled and core_base_url_configured
    unavailable_core_routes = [
        route for route in CORE_REQUIRED_ROUTES
        if workspace_flags.get(route, True) and not core_read_configured
    ]
    return {
        "runtime_ready": not disabled_routes and not unavailable_core_routes,
        "configuration_required": bool(disabled_routes or unavailable_core_routes),
        "workspace_flags": workspace_flags,
        "disabled_routes": disabled_routes,
        "platform_core": {
            "enabled": core_enabled,
            "base_url_configured": core_base_url_configured,
            "public_api_key_configured": public_key_configured,
            "public_read_configured": core_read_configured,
            "write_lineage_configured": core_read_configured and write_key_configured,
            "public_api_key_optional": True,
        },
        "core_required_routes": list(CORE_REQUIRED_ROUTES),
        "core_required_routes_unavailable": unavailable_core_routes,
        "core_enhanced_routes": list(CORE_ENHANCED_ROUTES),
        "required_environment": [
            "SC_SI_PLATFORM_CORE_ENABLED=true",
            "SC_SI_PLATFORM_CORE_URL=<deployed Platform Core backend URL>",
        ],
        "optional_environment": [
            "SC_SI_PLATFORM_CORE_PUBLIC_API_KEY=<only if public reads require authentication>",
            "SC_SI_PLATFORM_CORE_WRITE_API_KEY=<only for backend lineage/write integration>",
        ],
    }


def public_v4_configuration_readiness(settings: Any = None) -> dict[str, Any]:
    runtime = _runtime_configuration(settings)
    payload = {
        "ok": True,
        "version": RELEASE_VERSION,
        "contract": "site-intelligence-runtime-configuration",
        **runtime,
    }
    payload["configuration_sha256"] = _digest({
        "workspace_flags": runtime["workspace_flags"],
        "platform_core": runtime["platform_core"],
        "core_required_routes_unavailable": runtime["core_required_routes_unavailable"],
    })
    return payload


def public_v4_readiness(settings: Any = None) -> dict[str, Any]:
    policy = _policy()
    routes = _route_directory()
    route_ids = [row["route_id"] for row in routes]
    checks = {
        "six_primary_areas": len(policy["primary_areas"]) == 6,
        "all_35_routes_preserved": len(route_ids) == 35 and len(set(route_ids)) == 35,
        "canonical_contracts_present": len(policy["canonical_contracts"]) == 6,
        "legacy_routes_preserved": policy["compatibility"].get("legacy_routes_preserved") is True,
        "deep_links_preserved": policy["compatibility"].get("deep_links_preserved") is True,
        "automatic_migrations_disabled": policy["compatibility"].get("automatic_migrations") is False,
    }
    runtime = _runtime_configuration(settings)
    return {
        "ok": all(checks.values()),
        "runtime_ready": runtime["runtime_ready"],
        "configuration_required": runtime["configuration_required"],
        "version": RELEASE_VERSION,
        "release_name": "Unified Public Intelligence Platform",
        "orbital_earth_extension": "/public/orbital-earth",
        "checks": checks,
        "runtime_configuration": runtime,
        "summary": {
            "primary_areas": len(policy["primary_areas"]),
            "preserved_routes": len(route_ids),
            "canonical_contracts": len(policy["canonical_contracts"]),
        },
        "readiness_sha256": _digest({"checks": checks, "runtime_configuration": runtime}),
    }
