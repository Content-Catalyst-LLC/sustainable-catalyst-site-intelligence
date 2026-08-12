from __future__ import annotations

from .release_health_v43523 import deployment_verification as prior_deployment, source_health_policy as prior_source_health
from .country_navigation_integrity_v43524 import readiness as navigation_readiness
from .version import APP_VERSION

VERSION = APP_VERSION
CONTRACT = "deployment-verification-palestine-first-country-navigation-integrity-v43524"
NAVIGATION_ROUTE = "/public/country-navigation-integrity/readiness"


def deployment_verification(settings):
    payload = prior_deployment(settings)
    nav = navigation_readiness()
    payload["version"] = VERSION
    payload["contract"] = CONTRACT
    checks = payload["checks"]
    checks["country_navigation_integrity_ready"] = nav["ok"]
    checks["palestine_external_override_blocked"] = nav["checks"]["palestine_identity_survives_external_override"]
    checks["israel_external_override_blocked"] = nav["checks"]["israel_identity_survives_external_override"]
    checks["external_country_metadata_enrichment_only"] = nav["checks"]["external_metadata_is_enrichment_only"]
    checks["country_navigation_network_free"] = nav["network_calls_performed"] is False
    checks["country_navigation_upstream_non_blocking"] = nav["upstream_health_release_blocking"] is False
    routes = list(payload.get("required_routes") or [])
    if NAVIGATION_ROUTE not in routes:
        routes.append(NAVIGATION_ROUTE)
    payload["required_routes"] = routes
    checks["required_route_contract_declared"] = len(routes) == 18
    payload["country_navigation_integrity"] = nav
    payload["ok"] = all(checks.values())
    return payload


def source_health_policy(settings):
    payload = prior_source_health(settings)
    nav = navigation_readiness()
    payload["version"] = VERSION
    payload["contract"] = CONTRACT
    payload["country_navigation_integrity_policy"] = nav["policy"] | {
        "ready": nav["ok"],
        "network_calls_performed": False,
        "upstream_health_release_blocking": False,
    }
    return payload
