from __future__ import annotations

from .release_health_v43521 import deployment_verification as prior_deployment, source_health_policy as prior_source_health
from .country_evidence_reconciliation_v43522 import readiness as reconciliation_readiness
from .version import APP_VERSION

VERSION = APP_VERSION
CONTRACT = "deployment-verification-country-evidence-reconciliation-v43522"


def deployment_verification(settings):
    payload = prior_deployment(settings)
    reconciliation = reconciliation_readiness()
    payload["version"] = VERSION
    payload["contract"] = CONTRACT
    payload["checks"]["country_evidence_reconciliation_ready"] = reconciliation["ok"]
    payload["checks"]["country_reconciliation_network_free"] = reconciliation["network_calls_performed"] is False
    payload["checks"]["country_reconciliation_upstream_non_blocking"] = reconciliation["upstream_health_release_blocking"] is False
    payload["checks"]["palestine_geographic_scope_guard"] = reconciliation["checks"]["palestine_subnational_scope_guard"]
    payload["checks"]["automatic_cross_source_blending_prohibited"] = reconciliation["checks"]["automatic_blending_prohibited"]
    routes = list(payload.get("required_routes") or [])
    route = "/public/country-evidence-reconciliation/readiness"
    if route not in routes:
        routes.append(route)
    payload["required_routes"] = routes
    payload["checks"]["required_route_contract_declared"] = len(routes) == 16
    payload["country_evidence_reconciliation"] = {
        "ready": reconciliation["ok"],
        "exact_concept_before_authority": reconciliation["checks"]["exact_concept_before_authority"],
        "national_geography_before_precedence": reconciliation["checks"]["national_geography_before_precedence"],
        "palestine_subnational_scope_guard": reconciliation["checks"]["palestine_subnational_scope_guard"],
        "automatic_blending": "prohibited",
        "network_calls_performed": False,
        "upstream_health_release_blocking": False,
    }
    payload["ok"] = all(payload["checks"].values())
    return payload


def source_health_policy(settings):
    payload = prior_source_health(settings)
    reconciliation = reconciliation_readiness()
    payload["version"] = VERSION
    payload["contract"] = CONTRACT
    payload["country_evidence_reconciliation_policy"] = {
        "selection_order": ["exact concept", "compatible units", "national geographic scope", "declared source precedence", "authority", "cadence-aware freshness", "status"],
        "discrepancy_policy": "retain and disclose; never average into a synthetic country statistic",
        "palestine_scope_policy": "Gaza and West Bank observations remain subnational context unless an upstream source explicitly provides a Palestine-wide national observation",
        "preferred_source_absence_policy": "report missing from the current candidate set; do not infer zero incidence or source unavailability",
        "ready": reconciliation["ok"],
        "network_calls_performed": False,
        "upstream_health_release_blocking": False,
    }
    return payload
