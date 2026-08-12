from __future__ import annotations

from .release_health_v43518 import deployment_verification as prior_deployment, source_health_policy as prior_source_health
from .production_soak_v43519 import readiness as production_soak_readiness, run_soak_suite
from .evidence_presentation_v43519 import readiness as evidence_presentation_readiness
from .workspace_evidence_unification_v4358 import readiness as workspace_evidence_readiness
from .version import APP_VERSION

VERSION = APP_VERSION
CONTRACT = "deployment-verification-production-soak-semantic-truth-v43519"


def deployment_verification(settings):
    payload = prior_deployment(settings)
    soak = production_soak_readiness(settings)
    semantics = evidence_presentation_readiness()
    canonical = workspace_evidence_readiness()
    payload["version"] = VERSION
    payload["contract"] = CONTRACT
    payload["checks"]["production_soak_control_plane_ready"] = soak["ok"]
    payload["checks"]["all_eight_deterministic_soak_scenarios_pass"] = soak["scenario_count"] == 8 and soak["passed_scenario_count"] == 8
    payload["checks"]["semantic_truth_guard_ready"] = semantics["ok"]
    payload["checks"]["canonical_workspace_evidence_truth_ready"] = canonical["ok"]
    payload["checks"]["soak_network_free"] = soak["network_calls_performed"] is False
    payload["checks"]["live_provider_operator_soak_non_blocking"] = soak["upstream_health_release_blocking"] is False
    routes = list(payload.get("required_routes") or [])
    for route in ("/public/production-soak/readiness", "/public/evidence-presentation/readiness"):
        if route not in routes:
            routes.append(route)
    payload["required_routes"] = routes
    payload["checks"]["required_route_contract_declared"] = len(routes) == 12
    payload["production_soak"] = {
        "ready": soak["ok"],
        "scenario_count": soak["scenario_count"],
        "passed_scenario_count": soak["passed_scenario_count"],
        "network_calls_performed": False,
        "upstream_health_release_blocking": False,
    }
    payload["evidence_presentation"] = {
        "ready": semantics["ok"],
        "transport_state_is_not_evidence_class": semantics["checks"]["transport_state_separate_from_evidence_class"],
        "world_bank_annual_is_harmonized_benchmark": semantics["checks"]["world_bank_annual_is_harmonized_benchmark"],
        "palestine_pcbs_precedence_present": semantics["checks"]["palestine_pcbs_precedence_present"],
        "network_calls_performed": False,
    }
    payload["ok"] = all(payload["checks"].values())
    return payload


def source_health_policy(settings):
    payload = prior_source_health(settings)
    soak = run_soak_suite(settings)
    semantics = evidence_presentation_readiness()
    payload["version"] = VERSION
    payload["contract"] = CONTRACT
    payload["production_soak"] = {
        "scenario_count": soak["scenario_count"],
        "passed_scenario_count": soak["passed_scenario_count"],
        "deterministic_fault_injection_release_blocking": True,
        "live_provider_operator_soak_release_blocking": False,
        "network_calls_performed": False,
        "upstream_health_release_blocking": False,
    }
    payload["evidence_presentation_semantics"] = {
        "ready": semantics["ok"],
        "transport_freshness_can_imply_operational_current": False,
        "world_bank_role": "harmonized-benchmark/fallback for country cards unless exact-concept higher-precedence evidence is selected",
        "palestine_national_statistics_precedence": "PCBS first when exact-concept connected evidence is available",
        "network_calls_performed": False,
    }
    return payload
