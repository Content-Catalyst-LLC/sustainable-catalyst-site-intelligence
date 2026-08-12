#!/usr/bin/env python3
from pathlib import Path
import sys
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.config import Settings
from app.main import app
from app.version import APP_VERSION
from app.release_health_v43524 import deployment_verification, source_health_policy
from app.country_identity_v43523 import readiness as identity_readiness, canonical_country
from app.country_navigation_integrity_v43524 import readiness as navigation_readiness
from app.country_evidence_reconciliation_v43522 import readiness as reconciliation_readiness
from app.country_linked_records_v43520 import readiness as linked_record_readiness
from app.palestine_data_federation_v43521 import readiness as palestine_federation_readiness
from app.wikimedia_knowledge_context_v43521 import readiness as wikimedia_readiness
from app.production_soak_v43519 import readiness as soak_readiness
from app.evidence_presentation_v43519 import readiness as evidence_presentation_readiness
from app.workspace_browser_audit_v43518 import workspace_browser_readiness
from app.external_resilience_v43517 import resilience_readiness
from app.workspace_evidence_unification_v4358 import readiness as workspace_evidence_readiness

assert APP_VERSION == "4.35.24"
settings = Settings(_env_file=None)

identity = identity_readiness()
assert identity["ok"] is True
assert identity["country_count"] >= 170
assert identity["network_calls_performed"] is False
assert identity["upstream_health_release_blocking"] is False
assert identity["checks"]["israel_iso3_bound_to_israel"] is True
assert identity["checks"]["palestine_iso3_bound_to_palestine"] is True
assert identity["checks"]["country_identity_is_first_party"] is True
assert canonical_country("ISR")[0] == "ISR"
assert canonical_country("IL")[0] == "ISR"
assert canonical_country("Israel")[0] == "ISR"
assert canonical_country("PSE")[0] == "PSE"
assert canonical_country("PS")[0] == "PSE"
assert canonical_country("Palestine")[0] == "PSE"

for ready in (
    navigation_readiness(), reconciliation_readiness(), linked_record_readiness(), palestine_federation_readiness(), wikimedia_readiness(),
    soak_readiness(settings), evidence_presentation_readiness(), workspace_browser_readiness(),
    resilience_readiness(settings), workspace_evidence_readiness(),
):
    assert ready["ok"] is True

verification = deployment_verification(settings)
assert verification["ok"] is True
assert len(verification["required_routes"]) == 18
assert "/public/country-identity/readiness" in verification["required_routes"]
assert "/public/country-navigation-integrity/readiness" in verification["required_routes"]
for check in (
    "canonical_country_identity_ready", "country_identity_network_free",
    "country_identity_upstream_non_blocking", "israel_identity_binding_isolated",
    "palestine_identity_binding_isolated", "canonical_country_identity_first_party",
    "country_navigation_integrity_ready", "palestine_external_override_blocked",
    "israel_external_override_blocked", "external_country_metadata_enrichment_only",
    "country_navigation_network_free", "country_navigation_upstream_non_blocking",
    "country_evidence_reconciliation_ready", "palestine_data_federation_ready",
    "wikimedia_knowledge_context_ready", "country_linked_record_recovery_ready",
    "production_soak_control_plane_ready", "semantic_truth_guard_ready",
    "workspace_browser_control_plane_ready",
):
    assert verification["checks"][check] is True, check

policy = source_health_policy(settings)["country_identity_policy"]
assert policy["upstream_health_release_blocking"] is False
assert policy["canonical_identity_source"] == "first-party-canonical-registry"
assert policy["israel_binding"] == "ISR -> IL -> Israel"
assert policy["palestine_binding"] == "PSE -> PS -> Palestine"
assert "rejected" in policy["cross_identity_policy"]


nav = navigation_readiness()
assert nav["ok"] is True
assert nav["network_calls_performed"] is False
assert nav["upstream_health_release_blocking"] is False
assert nav["checks"]["palestine_identity_survives_external_override"] is True
assert nav["checks"]["israel_identity_survives_external_override"] is True
assert nav["checks"]["external_metadata_is_enrichment_only"] is True
assert nav["checks"]["palestine_and_israel_remain_distinct"] is True

nav_policy = source_health_policy(settings)["country_navigation_integrity_policy"]
assert nav_policy["selector_identity"] == "first-party canonical registry"
assert nav_policy["cross_identity_response"] == "blocked"
assert nav_policy["palestine_binding"] == "PSE -> PS -> Palestine"
assert nav_policy["israel_binding"] == "ISR -> IL -> Israel"

client = TestClient(app)
for route in (
    "/public/country-identity/readiness",
    "/public/country-navigation-integrity/readiness",
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
assert response.json()["checks"]["canonical_country_identity_ready"] is True

assert response.json()["checks"]["country_navigation_integrity_ready"] is True
assert response.json()["checks"]["palestine_external_override_blocked"] is True
assert response.json()["checks"]["israel_external_override_blocked"] is True

print("PASS: v4.35.24 Palestine-first country navigation integrity release contract")
