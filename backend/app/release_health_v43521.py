from __future__ import annotations

from .release_health_v43520 import deployment_verification as prior_deployment, source_health_policy as prior_source_health
from .palestine_data_federation_v43521 import readiness as palestine_federation_readiness
from .wikimedia_knowledge_context_v43521 import readiness as wikimedia_readiness
from .authoritative_connectors_v43521 import connector_readiness
from .version import APP_VERSION

VERSION = APP_VERSION
CONTRACT = "deployment-verification-palestine-federation-wikimedia-context-v43521"


def deployment_verification(settings):
    payload = prior_deployment(settings)
    palestine = palestine_federation_readiness()
    wikimedia = wikimedia_readiness()
    connectors = connector_readiness(settings)
    payload["version"] = VERSION
    payload["contract"] = CONTRACT
    payload["checks"]["palestine_data_federation_ready"] = palestine["ok"]
    payload["checks"]["palestine_federation_network_free"] = palestine["network_calls_performed"] is False
    payload["checks"]["palestine_upstream_health_non_blocking"] = palestine["upstream_health_release_blocking"] is False
    payload["checks"]["wikimedia_knowledge_context_ready"] = wikimedia["ok"]
    payload["checks"]["wikimedia_context_network_free"] = wikimedia["network_calls_performed"] is False
    payload["checks"]["wikimedia_upstream_health_non_blocking"] = wikimedia["upstream_health_release_blocking"] is False
    payload["checks"]["wikimedia_excluded_from_truth_precedence"] = wikimedia["checks"]["wikimedia_excluded_from_truth_precedence"]
    payload["checks"]["palestine_open_data_connector_registered"] = connectors["checks"]["palestine_open_data_present"]
    routes = list(payload.get("required_routes") or [])
    for route in ("/public/country-data-federation/readiness", "/public/knowledge-context/readiness"):
        if route not in routes:
            routes.append(route)
    payload["required_routes"] = routes
    payload["checks"]["required_route_contract_declared"] = len(routes) == 15
    payload["palestine_data_federation"] = {
        "ready": palestine["ok"],
        "pcbs_primary": palestine["checks"]["pcbs_primary_statistical_authority_preserved"],
        "palestine_open_data_registered": palestine["checks"]["palestine_open_data_official_discovery_registered"],
        "hdx_hapi_preserved": palestine["checks"]["hdx_hapi_indicator_lane_preserved"],
        "world_bank_comparison_only": palestine["checks"]["world_bank_comparison_only"],
        "network_calls_performed": False,
        "upstream_health_release_blocking": False,
    }
    payload["wikimedia_knowledge_context"] = {
        "ready": wikimedia["ok"],
        "wikidata_entity_spine": wikimedia["checks"]["wikidata_entity_spine_registered"],
        "wikipedia_context": wikimedia["checks"]["wikipedia_context_registered"],
        "commons_visual_context": wikimedia["checks"]["commons_visual_context_registered"],
        "pageviews_attention_signal": wikimedia["checks"]["pageviews_attention_signal_registered"],
        "truth_precedence": "excluded",
        "network_calls_performed": False,
        "upstream_health_release_blocking": False,
    }
    payload["ok"] = all(payload["checks"].values())
    return payload


def source_health_policy(settings):
    payload = prior_source_health(settings)
    palestine = palestine_federation_readiness()
    wikimedia = wikimedia_readiness()
    payload["version"] = VERSION
    payload["contract"] = CONTRACT
    payload["palestine_data_federation_policy"] = {
        "pcbs_role": "primary official statistical authority for exact supported concepts",
        "palestine_open_data_role": "official/public-institution dataset discovery",
        "hdx_hapi_role": "standardized humanitarian indicators retaining source/reference-period semantics",
        "hdx_ckan_role": "humanitarian dataset discovery",
        "world_bank_role": "harmonized international comparison/fallback",
        "ready": palestine["ok"],
        "network_calls_performed": False,
        "upstream_health_release_blocking": False,
    }
    payload["wikimedia_knowledge_context_policy"] = {
        "wikidata_role": "linked entity resolution and identifiers",
        "wikipedia_role": "community-curated background context",
        "commons_role": "visual context with per-file provenance/licensing",
        "pageviews_role": "public attention signal only",
        "truth_precedence": "excluded",
        "ready": wikimedia["ok"],
        "network_calls_performed": False,
        "upstream_health_release_blocking": False,
    }
    return payload
