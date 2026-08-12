from __future__ import annotations

from .release_health_v43519 import deployment_verification as prior_deployment, source_health_policy as prior_source_health
from .country_linked_records_v43520 import readiness as linked_record_readiness
from .version import APP_VERSION

VERSION = APP_VERSION
CONTRACT = "deployment-verification-country-linked-record-recovery-v43520"


def deployment_verification(settings):
    payload = prior_deployment(settings)
    linked = linked_record_readiness()
    payload["version"] = VERSION
    payload["contract"] = CONTRACT
    payload["checks"]["country_linked_record_recovery_ready"] = linked["ok"]
    payload["checks"]["country_linked_record_readiness_network_free"] = linked["network_calls_performed"] is False
    payload["checks"]["country_linked_upstream_health_non_blocking"] = linked["upstream_health_release_blocking"] is False
    routes = list(payload.get("required_routes") or [])
    route = "/public/country-linked-records/readiness"
    if route not in routes:
        routes.append(route)
    payload["required_routes"] = routes
    payload["checks"]["required_route_contract_declared"] = len(routes) == 13
    payload["country_linked_records"] = {
        "ready": linked["ok"],
        "network_calls_performed": False,
        "upstream_health_release_blocking": False,
        "reliefweb_country_query_is_source_bounded": linked["checks"]["reliefweb_country_query_is_source_bounded"],
        "hdx_public_discovery_lane_present": linked["checks"]["hdx_public_discovery_lane_present"],
        "discovery_metadata_not_promoted_to_observation": linked["checks"]["discovery_metadata_not_promoted_to_observation"],
    }
    payload["ok"] = all(payload["checks"].values())
    return payload


def source_health_policy(settings):
    payload = prior_source_health(settings)
    linked = linked_record_readiness()
    payload["version"] = VERSION
    payload["contract"] = CONTRACT
    payload["country_linked_record_policy"] = {
        "ready": linked["ok"],
        "reliefweb_country_filtering": "country.iso3 is applied at the upstream request when a country workspace requests linked records",
        "credential_free_fallback": "HDX CKAN public metadata discovery",
        "discovery_metadata_is_current_condition": False,
        "zero_linked_records_means_zero_incidence": False,
        "network_calls_performed": False,
        "upstream_health_release_blocking": False,
    }
    return payload
