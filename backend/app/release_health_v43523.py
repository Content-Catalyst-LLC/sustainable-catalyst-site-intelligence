from __future__ import annotations

from .release_health_v43522 import deployment_verification as prior_deployment, source_health_policy as prior_source_health
from .country_identity_v43523 import readiness as country_identity_readiness
from .version import APP_VERSION

VERSION = APP_VERSION
CONTRACT = "deployment-verification-country-identity-selector-routing-v43523"
IDENTITY_ROUTE = "/public/country-identity/readiness"


def deployment_verification(settings):
    payload = prior_deployment(settings)
    identity = country_identity_readiness()
    payload["version"] = VERSION
    payload["contract"] = CONTRACT
    checks = payload["checks"]
    checks["canonical_country_identity_ready"] = identity["ok"]
    checks["country_identity_network_free"] = identity["network_calls_performed"] is False
    checks["country_identity_upstream_non_blocking"] = identity["upstream_health_release_blocking"] is False
    checks["israel_identity_binding_isolated"] = identity["checks"]["israel_iso3_bound_to_israel"]
    checks["palestine_identity_binding_isolated"] = identity["checks"]["palestine_iso3_bound_to_palestine"]
    checks["canonical_country_identity_first_party"] = identity["checks"]["country_identity_is_first_party"]
    routes = list(payload.get("required_routes") or [])
    if IDENTITY_ROUTE not in routes:
        routes.append(IDENTITY_ROUTE)
    payload["required_routes"] = routes
    checks["required_route_contract_declared"] = len(routes) == 17
    payload["country_identity"] = {
        "ready": identity["ok"],
        "country_count": identity["country_count"],
        "selector_identity_source": "first-party-canonical-registry",
        "israel": {"iso3": "ISR", "iso2": "IL", "display_name": "Israel"},
        "palestine": {"iso3": "PSE", "iso2": "PS", "display_name": "Palestine"},
        "cross_identity_rendering": "blocked",
        "external_catalog_role": "metadata-enrichment-only",
        "network_calls_performed": False,
        "upstream_health_release_blocking": False,
    }
    payload["ok"] = all(checks.values())
    return payload


def source_health_policy(settings):
    payload = prior_source_health(settings)
    identity = country_identity_readiness()
    payload["version"] = VERSION
    payload["contract"] = CONTRACT
    payload["country_identity_policy"] = {
        "canonical_identity_source": "first-party-canonical-registry",
        "selector_map_backend_contract": "one canonical ISO3 identity plane",
        "external_catalog_policy": "World Bank or other upstream catalogs may enrich metadata but cannot define selector identity or remove a canonical country",
        "cross_identity_policy": "a response whose ISO3 code does not match the requested country is rejected and must not render",
        "selection_commit_policy": "selected ISO3 route state is committed before optional indicator retrieval",
        "israel_binding": "ISR -> IL -> Israel",
        "palestine_binding": "PSE -> PS -> Palestine",
        "ready": identity["ok"],
        "network_calls_performed": False,
        "upstream_health_release_blocking": False,
    }
    return payload
