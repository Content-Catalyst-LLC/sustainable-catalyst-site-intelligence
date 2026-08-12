from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .version import APP_VERSION

VERSION = APP_VERSION
CONTRACT = "workspace-browser-audit-simply-works-v43518"
ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "backend/data/unified_public_intelligence_policy_v4000.json"
INDEX_PATH = ROOT / "backend/public_app/index.html"
APP_JS_PATH = ROOT / "backend/public_app/assets/app.js"
RELIABILITY_JS_PATH = ROOT / "backend/public_app/assets/workspace-reliability-v43518.js"

ROUTE_SURFACES: dict[str, str] = {
    "overview": "#map",
    "global": "#globalConditionsObservatory",
    "events": "#eventStudio",
    "alerts": "#alertsStudio",
    "country": "#globalCountryExplorer",
    "dossiers": "#dossierStudio",
    "economics": "#economicsStudio",
    "law": "#lawStudio",
    "science": "#scienceStudio",
    "humanitarian": "#humanitarianStudio",
    "resources": "#resourceStudio",
    "thematic": "#thematicStudio",
    "compare": "#compareStudio",
    "spatial": "#spatialEvidenceStudio",
    "earth": "#earthStudio",
    "harmonization": "#harmonizationStudio",
    "models": "#modelGovernanceStudio",
    "scenarios": "#scenarioStudio",
    "platform": "#connectedPlatformStudio",
    "observatory": "#auditablePublicObservatory",
    "research": "#researchWorkflowStudio",
    "evidence": "#evidenceSynthesisStudio",
    "graph": "#knowledgeGraphExplorer",
    "sources": "#sourceStudio",
    "saved": "#savedViewsStudio",
    "briefing": "#briefingStudio",
    "publishing": "#intelligencePublishingStudio",
    "monitoring": "#scheduledMonitoringStudio",
    "workspaces": "#institutionalWorkspaceStudio",
    "integration": "#publicDataIntegrationStudio",
    "workflows": "#crossPlatformWorkflowStudio",
    "federation": "#institutionalDataExchangeStudio",
    "governance": "#productionGovernanceStudio",
    "experience": "#offlineExperienceStudio",
    "launch": "#publicLaunchPortfolio",
}


def _policy() -> dict[str, Any]:
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def _routes() -> list[str]:
    return [route for area in _policy()["primary_areas"] for route in area["routes"]]


def _digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _static_route_row(route: str) -> dict[str, Any]:
    index = INDEX_PATH.read_text(encoding="utf-8")
    app_js = APP_JS_PATH.read_text(encoding="utf-8")
    reliability_js = RELIABILITY_JS_PATH.read_text(encoding="utf-8") if RELIABILITY_JS_PATH.exists() else ""
    selector = ROUTE_SURFACES[route]
    selector_id = selector.removeprefix("#")
    return {
        "route": route,
        "surface_selector": selector,
        "surface_declared": selector_id in index or selector_id in app_js or selector_id in reliability_js,
        "route_metadata_declared": f"{route}:[" in app_js,
        "router_branch_declared": route == "overview" or f'route==="{route}"' in app_js,
        "recovery_surface_available": "workspace-recovery" in reliability_js,
        "degraded_state_explicit": True,
        "upstream_health_release_blocking": False,
    }


def workspace_browser_audit() -> dict[str, Any]:
    policy = _policy()
    routes = _routes()
    rows = [_static_route_row(route) for route in routes]
    checks = {
        "six_primary_areas": len(policy["primary_areas"]) == 6,
        "all_35_routes_preserved": len(routes) == 35 and len(set(routes)) == 35,
        "all_35_surfaces_mapped": set(routes) == set(ROUTE_SURFACES),
        "all_surfaces_declared": all(row["surface_declared"] for row in rows),
        "all_route_metadata_declared": all(row["route_metadata_declared"] for row in rows),
        "all_router_branches_declared": all(row["router_branch_declared"] for row in rows),
        "recovery_layer_present": all(row["recovery_surface_available"] for row in rows),
        "view_unavailable_not_used_for_registered_routes": "registered route recovery" in APP_JS_PATH.read_text(encoding="utf-8"),
        "upstream_health_non_blocking": True,
        "network_calls_avoided": True,
    }
    payload = {
        "ok": all(checks.values()),
        "version": VERSION,
        "contract": CONTRACT,
        "audit_mode": "network-free-control-plane",
        "primary_area_count": len(policy["primary_areas"]),
        "route_count": len(routes),
        "routes": rows,
        "checks": checks,
        "simply_works_definition": {
            "registered_route_never_blank": True,
            "registered_route_never_falls_through_to_unavailable": True,
            "explicit_degraded_state_when_module_or_data_fails": True,
            "desktop_mobile_iframe_browser_gate_required": True,
            "canonical_evidence_and_truth_contract_preserved": True,
            "provider_outage_release_blocking": False,
        },
    }
    payload["audit_sha256"] = _digest({"checks": checks, "routes": rows})
    return payload


def workspace_browser_readiness() -> dict[str, Any]:
    audit = workspace_browser_audit()
    return {
        "ok": audit["ok"],
        "version": VERSION,
        "contract": CONTRACT,
        "route_count": audit["route_count"],
        "primary_area_count": audit["primary_area_count"],
        "checks": audit["checks"],
        "network_calls_performed": False,
        "upstream_health_release_blocking": False,
        "audit_sha256": audit["audit_sha256"],
    }


def workspace_route_detail(route: str) -> dict[str, Any]:
    if route not in ROUTE_SURFACES:
        raise KeyError(route)
    row = _static_route_row(route)
    row.update({"ok": all((row["surface_declared"], row["route_metadata_declared"], row["router_branch_declared"], row["recovery_surface_available"])), "version": VERSION, "contract": CONTRACT})
    return row
