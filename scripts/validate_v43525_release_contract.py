#!/usr/bin/env python3
from pathlib import Path
import sys
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.config import Settings
from app.main import app
from app.version import APP_VERSION
from app.release_health_v43525 import deployment_verification, source_health_policy
from app.country_evidence_presentation_v43525 import readiness as presentation_readiness
from app.country_navigation_integrity_v43524 import readiness as navigation_readiness
from app.country_identity_v43523 import readiness as identity_readiness
from app.country_evidence_reconciliation_v43522 import readiness as reconciliation_readiness
from app.country_linked_records_v43520 import readiness as linked_record_readiness
from app.palestine_data_federation_v43521 import readiness as palestine_federation_readiness
from app.wikimedia_knowledge_context_v43521 import readiness as wikimedia_readiness
from app.production_soak_v43519 import readiness as soak_readiness
from app.evidence_presentation_v43519 import readiness as semantic_readiness
from app.workspace_browser_audit_v43518 import workspace_browser_readiness
from app.external_resilience_v43517 import resilience_readiness
from app.workspace_evidence_unification_v4358 import readiness as workspace_evidence_readiness

assert APP_VERSION == "4.35.25"
settings = Settings(_env_file=None)
for ready in (
    presentation_readiness(), navigation_readiness(), identity_readiness(), reconciliation_readiness(), linked_record_readiness(),
    palestine_federation_readiness(), wikimedia_readiness(), soak_readiness(settings), semantic_readiness(),
    workspace_browser_readiness(), resilience_readiness(settings), workspace_evidence_readiness(),
):
    assert ready["ok"] is True, ready.get("contract")

presentation = presentation_readiness()
assert presentation["network_calls_performed"] is False
assert presentation["upstream_health_release_blocking"] is False
assert presentation["checks"]["structural_electricity_not_conditions_now"] is True
assert presentation["checks"]["world_bank_electricity_is_benchmark"] is True

verification = deployment_verification(settings)
assert verification["ok"] is True
assert len(verification["required_routes"]) == 19
assert "/public/country-evidence-presentation/readiness" in verification["required_routes"]
for check in (
    "country_evidence_presentation_ready", "structural_electricity_not_operational_truth",
    "structural_electricity_warning_visible", "harmonized_benchmark_role_explicit",
    "country_presentation_network_free", "country_presentation_upstream_non_blocking",
    "country_navigation_integrity_ready", "canonical_country_identity_ready",
    "country_evidence_reconciliation_ready", "palestine_data_federation_ready",
    "wikimedia_knowledge_context_ready", "country_linked_record_recovery_ready",
    "production_soak_control_plane_ready", "semantic_truth_guard_ready",
    "workspace_browser_control_plane_ready",
):
    assert verification["checks"][check] is True, check

policy = source_health_policy(settings)["country_evidence_presentation_policy"]
assert policy["structural_statistics_are_operational_conditions"] is False
assert policy["international_benchmark_can_override_operational_reporting"] is False
assert policy["transport_state_is_evidence_authority"] is False

client = TestClient(app)
for route in (
    "/public/country-evidence-presentation/readiness",
    "/public/country-navigation-integrity/readiness",
    "/public/country-identity/readiness",
    "/public/country-evidence-reconciliation/readiness",
    "/public/country-linked-records/readiness",
    "/public/country-data-federation/readiness",
    "/public/knowledge-context/readiness",
    "/public/production-soak/readiness",
):
    response = client.get(route)
    assert response.status_code == 200 and response.json()["ok"] is True, route
print("PASS: v4.35.25 Country Intelligence Presentation & Evidence Hierarchy release contract")
