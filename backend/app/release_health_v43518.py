from __future__ import annotations

from .release_health_v43517 import deployment_verification as prior_deployment, source_health_policy as prior_source_health
from .workspace_browser_audit_v43518 import workspace_browser_readiness, workspace_browser_audit
from .version import APP_VERSION

VERSION = APP_VERSION
CONTRACT = "deployment-verification-simply-works-browser-audit-v43518"


def deployment_verification(settings):
    payload = prior_deployment(settings)
    browser = workspace_browser_readiness()
    payload["version"] = VERSION
    payload["contract"] = CONTRACT
    payload["checks"]["workspace_browser_control_plane_ready"] = browser["ok"]
    payload["checks"]["all_35_registered_routes_audited"] = browser["route_count"] == 35
    payload["checks"]["registered_routes_have_recovery_surface"] = browser["checks"]["recovery_layer_present"]
    payload["checks"]["browser_provider_health_non_blocking"] = browser["upstream_health_release_blocking"] is False
    routes = list(payload.get("required_routes") or [])
    if "/public/workspace-browser-audit/readiness" not in routes:
        routes.append("/public/workspace-browser-audit/readiness")
    payload["required_routes"] = routes
    payload["checks"]["required_route_contract_declared"] = len(routes) == 10
    payload["workspace_browser_audit"] = {
        "ready": browser["ok"],
        "route_count": browser["route_count"],
        "primary_area_count": browser["primary_area_count"],
        "network_calls_performed": False,
        "upstream_health_release_blocking": False,
    }
    payload["ok"] = all(payload["checks"].values())
    return payload


def source_health_policy(settings):
    payload = prior_source_health(settings)
    browser = workspace_browser_audit()
    payload["version"] = VERSION
    payload["contract"] = CONTRACT
    payload["workspace_browser_reliability"] = {
        "route_count": browser["route_count"],
        "primary_area_count": browser["primary_area_count"],
        "blank_registered_routes_allowed": False,
        "explicit_degraded_state_required": True,
        "upstream_health_release_blocking": False,
        "network_calls_performed": False,
    }
    return payload
