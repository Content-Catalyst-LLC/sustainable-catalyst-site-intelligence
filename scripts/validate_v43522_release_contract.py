#!/usr/bin/env python3
from pathlib import Path
import sys
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.config import Settings
from app.main import app
from app.version import APP_VERSION
from app.release_health_v43522 import deployment_verification, source_health_policy
from app.country_evidence_reconciliation_v43522 import readiness as reconciliation_readiness, reconcile_evidence
from app.country_linked_records_v43520 import readiness as linked_record_readiness
from app.palestine_data_federation_v43521 import readiness as palestine_federation_readiness
from app.wikimedia_knowledge_context_v43521 import readiness as wikimedia_readiness
from app.production_soak_v43519 import readiness as soak_readiness
from app.evidence_presentation_v43519 import readiness as evidence_presentation_readiness
from app.workspace_browser_audit_v43518 import workspace_browser_readiness
from app.external_resilience_v43517 import resilience_readiness
from app.workspace_evidence_unification_v4358 import readiness as workspace_evidence_readiness

assert APP_VERSION == "4.35.23"
settings = Settings(_env_file=None)

reconciliation = reconciliation_readiness()
assert reconciliation["ok"] is True
assert reconciliation["network_calls_performed"] is False
assert reconciliation["upstream_health_release_blocking"] is False
for check in (
    "exact_concept_before_authority", "national_geography_before_precedence",
    "palestine_subnational_scope_guard", "different_reference_periods_not_automatic_conflicts",
    "methodology_difference_disclosed", "automatic_blending_prohibited",
    "preferred_source_absence_disclosed",
):
    assert reconciliation["checks"][check] is True, check

sample = reconcile_evidence(
    jurisdiction="PSE", concept_id="population_total",
    candidates=[
        {"source_id":"pcbs-pxweb","concept_id":"population_total","authority_class":"national-statistical-authority","value":5557096,"unit":"people","observation_year":2025,"geography_code":"PSE","status":"final","methodology_id":"pcbs-revised"},
        {"source_id":"world_bank","indicator_id":"SP.POP.TOTL","authority_class":"international-harmonized","value":5414000,"unit":"people","observation_year":2025,"geography_code":"PSE","status":"final","methodology_id":"wb-harmonized"},
    ],
    now="2026-08-12T00:00:00+00:00",
)
assert sample["selected"]["source_id"] == "pcbs-pxweb"
assert sample["comparisons"][0]["automatic_blending_allowed"] is False
assert sample["comparisons"][0]["classification"] == "material-discrepancy-methodology-diverges"

for ready in (
    linked_record_readiness(), palestine_federation_readiness(), wikimedia_readiness(),
    soak_readiness(settings), evidence_presentation_readiness(), workspace_browser_readiness(),
    resilience_readiness(settings), workspace_evidence_readiness(),
):
    assert ready["ok"] is True

verification = deployment_verification(settings)
assert verification["ok"] is True
assert len(verification["required_routes"]) == 16
assert "/public/country-evidence-reconciliation/readiness" in verification["required_routes"]
for check in (
    "country_evidence_reconciliation_ready", "country_reconciliation_network_free",
    "country_reconciliation_upstream_non_blocking", "palestine_geographic_scope_guard",
    "automatic_cross_source_blending_prohibited", "palestine_data_federation_ready",
    "wikimedia_knowledge_context_ready", "country_linked_record_recovery_ready",
    "production_soak_control_plane_ready", "semantic_truth_guard_ready",
    "workspace_browser_control_plane_ready",
):
    assert verification["checks"][check] is True, check

health = source_health_policy(settings)
policy = health["country_evidence_reconciliation_policy"]
assert policy["upstream_health_release_blocking"] is False
assert policy["discrepancy_policy"].startswith("retain and disclose")
assert "Gaza and West Bank" in policy["palestine_scope_policy"]

client = TestClient(app)
for route in (
    "/public/country-evidence-reconciliation/readiness",
    "/public/country-linked-records/readiness",
    "/public/country-data-federation/readiness",
    "/public/knowledge-context/readiness",
    "/public/production-soak/readiness",
):
    response = client.get(route)
    assert response.status_code == 200 and response.json()["ok"] is True, route
response = client.get("/public/deployment-verification")
assert response.status_code == 200
assert response.json()["checks"]["country_evidence_reconciliation_ready"] is True

print("PASS: v4.35.23 country evidence reconciliation & scope-integrity release contract")
