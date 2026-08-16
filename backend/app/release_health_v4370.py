from __future__ import annotations

from .release_health_v43525 import deployment_verification as prior_deployment, source_health_policy as prior_source_health
from .live_underwater_media_v4370 import readiness as underwater_media_readiness, provider_catalog as underwater_media_providers
from .version import APP_VERSION

VERSION = APP_VERSION
CONTRACT = "deployment-verification-live-underwater-media-v4370"
REQUIRED = (
    "/public/underwater-media/providers",
    "/public/underwater-media/readiness",
)


def deployment_verification(settings):
    payload = prior_deployment(settings)
    underwater = underwater_media_readiness(settings)
    payload["version"] = VERSION
    payload["contract"] = CONTRACT
    checks = payload["checks"]
    live = underwater.get("checks", {})
    checks["live_underwater_media_ready"] = underwater.get("ok") is True
    checks["fathomnet_underwater_lane_ready"] = live.get("fathomnet_public_lane_ready") is True
    checks["noaa_underwater_lane_ready"] = live.get("noaa_public_lane_ready") is True
    checks["onc_underwater_credential_non_blocking"] = live.get("onc_missing_credential_non_blocking") is True
    checks["underwater_media_network_free_readiness"] = underwater.get("network_calls_performed") is False
    routes = list(payload.get("required_routes") or [])
    for route in REQUIRED:
        if route not in routes:
            routes.append(route)
    payload["required_routes"] = routes
    checks["required_route_contract_declared"] = len(routes) == 21
    payload["live_underwater_media"] = underwater
    payload["ok"] = all(checks.values())
    return payload


def source_health_policy(settings):
    payload = prior_source_health(settings)
    providers = underwater_media_providers(settings)
    payload["version"] = VERSION
    payload["contract"] = CONTRACT
    payload["underwater_media"] = {
        "provider_count": providers.get("provider_count"),
        "default_provider": providers.get("default_provider"),
        "providers": [
            {
                "id": row.get("id"),
                "configured": row.get("configured"),
                "configuration_required": row.get("configuration_required"),
                "release_blocking": False,
            }
            for row in providers.get("providers", [])
        ],
        "onc_missing_credential_blocks_release": False,
        "network_calls_performed": False,
    }
    return payload
