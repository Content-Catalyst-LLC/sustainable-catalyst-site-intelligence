from __future__ import annotations

from .release_health_v43524 import deployment_verification as prior_deployment, source_health_policy as prior_source_health
from .country_evidence_presentation_v43525 import readiness as presentation_readiness
from .version import APP_VERSION

VERSION = APP_VERSION
CONTRACT = "deployment-verification-country-intelligence-presentation-evidence-hierarchy-v43525"
PRESENTATION_ROUTE = "/public/country-evidence-presentation/readiness"


def deployment_verification(settings):
    payload = prior_deployment(settings)
    presentation = presentation_readiness()
    payload["version"] = VERSION
    payload["contract"] = CONTRACT
    checks = payload["checks"]
    checks["country_evidence_presentation_ready"] = presentation["ok"]
    checks["structural_electricity_not_operational_truth"] = presentation["checks"]["structural_electricity_not_conditions_now"]
    checks["structural_electricity_warning_visible"] = presentation["checks"]["structural_electricity_warning_visible"]
    checks["harmonized_benchmark_role_explicit"] = presentation["checks"]["world_bank_electricity_is_benchmark"]
    checks["country_presentation_network_free"] = presentation["network_calls_performed"] is False
    checks["country_presentation_upstream_non_blocking"] = presentation["upstream_health_release_blocking"] is False
    routes = list(payload.get("required_routes") or [])
    if PRESENTATION_ROUTE not in routes:
        routes.append(PRESENTATION_ROUTE)
    payload["required_routes"] = routes
    checks["required_route_contract_declared"] = len(routes) == 19
    payload["country_evidence_presentation"] = presentation
    payload["ok"] = all(checks.values())
    return payload


def source_health_policy(settings):
    payload = prior_source_health(settings)
    presentation = presentation_readiness()
    payload["version"] = VERSION
    payload["contract"] = CONTRACT
    payload["country_evidence_presentation_policy"] = {
        "ready": presentation["ok"],
        "structural_statistics_are_operational_conditions": False,
        "international_benchmark_can_override_operational_reporting": False,
        "transport_state_is_evidence_authority": False,
        "source_roles_visible": True,
        "network_calls_performed": False,
        "upstream_health_release_blocking": False,
    }
    return payload
