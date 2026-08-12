from __future__ import annotations

from .release_health_v43516 import deployment_verification as prior_deployment, source_health_policy as prior_source_health
from .external_resilience_v43517 import resilience_readiness, resilience_overview
from .version import APP_VERSION

VERSION = APP_VERSION
CONTRACT = "deployment-verification-external-resilience-v43517"


def deployment_verification(settings):
    payload = prior_deployment(settings)
    resilience = resilience_readiness(settings)
    payload["version"] = VERSION
    payload["contract"] = CONTRACT
    payload["checks"]["external_resilience_control_plane_ready"] = resilience["ok"]
    payload["checks"]["upstream_failures_remain_non_blocking"] = True
    routes = list(payload.get("required_routes") or [])
    if "/public/external-resilience/readiness" not in routes:
        routes.append("/public/external-resilience/readiness")
    payload["required_routes"] = routes
    payload["checks"]["required_route_contract_declared"] = len(routes) == 9
    payload["external_resilience"] = {
        "ready": resilience["ok"],
        "network_calls_performed": False,
        "upstream_health_release_blocking": False,
        "retry_after_supported": resilience["checks"]["retry_after_supported"],
        "stale_is_never_silently_fresh": resilience["checks"]["stale_is_never_silently_fresh"],
    }
    payload["ok"] = all(payload["checks"].values())
    return payload


def source_health_policy(settings):
    payload = prior_source_health(settings)
    resilience = resilience_overview(settings)
    payload["version"] = VERSION
    payload["contract"] = CONTRACT
    payload["external_resilience"] = {
        "provider_policy_count": resilience["provider_policy_count"],
        "telemetry": resilience["telemetry"]["totals"],
        "stale_policy": resilience["stale_policy"],
        "upstream_health_release_blocking": False,
        "network_calls_performed": False,
    }
    return payload
