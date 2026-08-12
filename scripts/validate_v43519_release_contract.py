#!/usr/bin/env python3
from pathlib import Path
import sys
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.config import Settings
from app.main import app
from app.version import APP_VERSION
from app.authoritative_api_production_audit_v43516 import production_audit
from app.authoritative_connectors_v43515 import connector_catalog
from app.credential_configuration_v43516 import credential_readiness
from app.external_resilience_v43517 import resilience_readiness
from app.release_health_v43519 import deployment_verification, source_health_policy
from app.workspace_browser_audit_v43518 import workspace_browser_audit, workspace_browser_readiness
from app.production_soak_v43519 import run_soak_suite, readiness as soak_readiness
from app.evidence_presentation_v43519 import readiness as evidence_presentation_readiness, classify_evidence, source_priority
from app.workspace_evidence_unification_v4358 import readiness as workspace_evidence_readiness

assert APP_VERSION == "4.35.22"
settings = Settings(_env_file=None)

# 35-route first-party browser control plane remains deterministic and provider-independent.
audit = workspace_browser_audit()
ready = workspace_browser_readiness()
assert audit["ok"] is True and audit["route_count"] == 35 and audit["primary_area_count"] == 6
assert len(audit["routes"]) == 35 and all(audit["checks"].values())
assert ready["ok"] is True
assert ready["network_calls_performed"] is False
assert ready["upstream_health_release_blocking"] is False

# Connector coverage is intentionally unchanged by the stress/semantic release.
prod = production_audit(settings)["machine_readable_summary"]
assert prod["registrations"] == 112
assert prod["counts"]["LIVE"] == 51
assert prod["counts"]["DISCOVERY"] == 15
assert prod["counts"]["AUTH_REQUIRED"] == 17
assert prod["registered_not_retrieved"] == 27
assert prod["counts"]["BULK"] == 2 and prod["counts"]["STALE"] == 0
catalog = connector_catalog(settings)
assert catalog["connector_count"] == 50
assert catalog["live_connector_count"] == 31
assert catalog["discovery_connector_count"] == 11
assert catalog["auth_required_connector_count"] == 8
assert credential_readiness(settings)["ok"] is True
assert resilience_readiness(settings)["ok"] is True
assert workspace_evidence_readiness()["ok"] is True

# Eight deterministic live-operation failure/recovery scenarios are release blocking.
soak = run_soak_suite(settings)
assert soak["ok"] is True
assert soak["scenario_count"] == 8 and soak["passed_scenario_count"] == 8
assert soak["flapping"]["cycles"] == 24
assert soak["network_calls_performed"] is False
assert soak["upstream_health_release_blocking"] is False
assert soak_readiness(settings)["ok"] is True

# Retrieval freshness cannot be presented as observation/current-condition truth.
semantics = evidence_presentation_readiness()
assert semantics["ok"] is True and semantics["network_calls_performed"] is False
assert all(semantics["checks"].values())
wb = classify_evidence(
    jurisdiction="PSE", indicator_id="EG.ELC.ACCS.ZS", source="World Bank Open Data",
    observation_year=2024, data_state="live", value_available=True, now="2026-08-12",
)
assert wb["transport_state"] == "live"
assert wb["evidence_class"] == "harmonized-benchmark"
assert wb["current_condition_claim_allowed"] is False
assert "does not represent current electricity availability" in wb["warning"]
priorities = source_priority("PSE", "electricity_structural_access")
assert priorities[0]["source_id"] == "pcbs-pxweb-sdgs"
assert any(row["source_id"] == "world_bank" and row["role"] == "harmonized-fallback" for row in priorities)

verification = deployment_verification(settings)
assert verification["ok"] is True
for check in (
    "workspace_browser_control_plane_ready",
    "all_35_registered_routes_audited",
    "registered_routes_have_recovery_surface",
    "browser_provider_health_non_blocking",
    "production_soak_control_plane_ready",
    "all_eight_deterministic_soak_scenarios_pass",
    "semantic_truth_guard_ready",
    "canonical_workspace_evidence_truth_ready",
    "soak_network_free",
    "live_provider_operator_soak_non_blocking",
):
    assert verification["checks"][check] is True, check
assert "/public/production-soak/readiness" in verification["required_routes"]
assert "/public/evidence-presentation/readiness" in verification["required_routes"]
assert len(verification["required_routes"]) == 12
health = source_health_policy(settings)
assert health["production_soak"]["deterministic_fault_injection_release_blocking"] is True
assert health["production_soak"]["live_provider_operator_soak_release_blocking"] is False
assert health["evidence_presentation_semantics"]["transport_freshness_can_imply_operational_current"] is False

client = TestClient(app)
for endpoint in (
    "/public/workspace-browser-audit/readiness",
    "/public/deployment-verification",
    "/public/source-health-policy",
    "/public/external-resilience/readiness",
    "/public/production-soak",
    "/public/production-soak/readiness",
    "/public/evidence-presentation/readiness",
):
    response = client.get(endpoint)
    assert response.status_code == 200, endpoint
    assert response.json().get("ok") is True, endpoint
classified = client.get("/public/evidence-presentation/classify", params={
    "jurisdiction":"PSE", "indicator_id":"EG.ELC.ACCS.ZS", "source":"World Bank Open Data",
    "observation_year":2024, "data_state":"live",
})
assert classified.status_code == 200 and classified.json()["evidence_class"] == "harmonized-benchmark"

main=(ROOT/"backend/app/main.py").read_text()
for marker in ("release_health_v43519", "production_soak_v43519", "evidence_presentation_v43519", "/public/production-soak/readiness", "/public/evidence-presentation/readiness"):
    assert marker in main, marker
app_js=(ROOT/"backend/public_app/assets/app.js").read_text()
index=(ROOT/"backend/public_app/index.html").read_text()
for marker in ("LIVE-OPERATION STRESS LAYER · v4.35.22", "productionSoakScenarioMetric"):
    assert marker in index, marker
for marker in ('apiWithRetry("/public/production-soak"', "item.evidence_label||item.data_state", "overview.evidence_summary"):
    assert marker in app_js, marker

promotion=(ROOT/"promote_site_intelligence_v4_35_19_to_github_and_render_macos.sh").read_text()
assert "Deep gate:" not in promotion
assert "/public/production-soak/readiness" in promotion
assert "/public/evidence-presentation/readiness" in promotion
assert "production_soak_ready" in promotion and "evidence_presentation_ready" in promotion
print("PASS: v4.35.22 Live-Operation Stress, Semantic Truth & Recovery Integrity release contract")
