#!/usr/bin/env python3
from pathlib import Path
import sys
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.config import Settings
from app.main import app
from app.version import APP_VERSION
from app.release_health_v43521 import deployment_verification, source_health_policy
from app.country_linked_records_v43520 import readiness as linked_record_readiness
from app.palestine_data_federation_v43521 import readiness as palestine_federation_readiness
from app.wikimedia_knowledge_context_v43521 import readiness as wikimedia_readiness
from app.authoritative_connectors_v43521 import connector_readiness as v43521_connector_readiness
from app.production_soak_v43519 import readiness as soak_readiness
from app.evidence_presentation_v43519 import readiness as evidence_presentation_readiness
from app.workspace_browser_audit_v43518 import workspace_browser_readiness
from app.external_resilience_v43517 import resilience_readiness
from app.workspace_evidence_unification_v4358 import readiness as workspace_evidence_readiness

assert APP_VERSION == "4.35.23"
settings = Settings(_env_file=None)

linked = linked_record_readiness()
assert linked["ok"] is True
assert linked["network_calls_performed"] is False
assert linked["upstream_health_release_blocking"] is False
assert linked["checks"]["reliefweb_country_query_is_source_bounded"] is True
assert linked["checks"]["hdx_public_discovery_lane_present"] is True
assert linked["checks"]["palestine_official_open_data_lane_present"] is True
assert linked["checks"]["discovery_metadata_not_promoted_to_observation"] is True
assert linked["checks"]["zero_records_not_interpreted_as_zero_incidence"] is True

palestine = palestine_federation_readiness()
assert palestine["ok"] is True
assert palestine["network_calls_performed"] is False
assert palestine["upstream_health_release_blocking"] is False
assert palestine["checks"]["pcbs_primary_statistical_authority_preserved"] is True
assert palestine["checks"]["palestine_open_data_official_discovery_registered"] is True
assert palestine["checks"]["hdx_hapi_indicator_lane_preserved"] is True
assert palestine["checks"]["world_bank_comparison_only"] is True
assert palestine["checks"]["wikimedia_excluded_from_truth_precedence"] is True

wikimedia = wikimedia_readiness()
assert wikimedia["ok"] is True
assert wikimedia["network_calls_performed"] is False
assert wikimedia["upstream_health_release_blocking"] is False
for check in (
    "wikidata_entity_spine_registered", "wikipedia_context_registered", "commons_visual_context_registered",
    "pageviews_attention_signal_registered", "wikimedia_excluded_from_truth_precedence",
    "commons_license_metadata_preserved", "pageviews_not_severity",
):
    assert wikimedia["checks"][check] is True, check

connector = v43521_connector_readiness(settings)
assert connector["ok"] is True
assert connector["checks"]["palestine_open_data_present"] is True
assert connector["network_calls_performed"] is False

assert soak_readiness(settings)["ok"] is True
assert evidence_presentation_readiness()["ok"] is True
assert workspace_browser_readiness()["ok"] is True
assert resilience_readiness(settings)["ok"] is True
assert workspace_evidence_readiness()["ok"] is True

verification = deployment_verification(settings)
assert verification["ok"] is True
assert len(verification["required_routes"]) == 15
for route in (
    "/public/country-linked-records/readiness",
    "/public/country-data-federation/readiness",
    "/public/knowledge-context/readiness",
):
    assert route in verification["required_routes"]
for check in (
    "country_linked_record_recovery_ready",
    "palestine_data_federation_ready",
    "palestine_open_data_connector_registered",
    "wikimedia_knowledge_context_ready",
    "wikimedia_excluded_from_truth_precedence",
    "production_soak_control_plane_ready",
    "semantic_truth_guard_ready",
    "workspace_browser_control_plane_ready",
):
    assert verification["checks"][check] is True, check

health = source_health_policy(settings)
assert health["country_linked_record_policy"]["discovery_metadata_is_current_condition"] is False
assert health["palestine_data_federation_policy"]["world_bank_role"] == "harmonized international comparison/fallback"
assert health["wikimedia_knowledge_context_policy"]["truth_precedence"] == "excluded"
assert health["wikimedia_knowledge_context_policy"]["upstream_health_release_blocking"] is False

client = TestClient(app)
for route in (
    "/public/country-linked-records/readiness",
    "/public/country-data-federation/readiness",
    "/public/knowledge-context/readiness",
):
    response = client.get(route)
    assert response.status_code == 200 and response.json()["ok"] is True, route
response = client.get("/public/deployment-verification")
assert response.status_code == 200
assert response.json()["checks"]["wikimedia_knowledge_context_ready"] is True
assert response.json()["checks"]["palestine_data_federation_ready"] is True

main = (ROOT / "backend/app/main.py").read_text()
linked_module = (ROOT / "backend/app/country_linked_records_v43520.py").read_text()
app_js = (ROOT / "backend/public_app/assets/app.js").read_text()
for marker in (
    '@app.get("/public/country/{country_code}/linked-records")',
    '@app.get("/public/country/{country_code}/data-federation")',
    '@app.get("/public/country/{country_code}/knowledge-context")',
    '@app.get("/public/palestine-open-data/search")',
    '@app.get("/public/knowledge-context/wikidata/search")',
    '@app.get("/public/knowledge-context/commons/search")',
    '@app.get("/public/knowledge-context/pageviews")',
    '@app.get("/public/knowledge-context/readiness")',
    "release_health_v43521",
):
    assert marker in main, marker
for marker in (
    "palestine_open_data_search",
    '"record_class": "official-dataset-discovery"',
    '"evidence_class": "official-discovery-metadata"',
):
    assert marker in linked_module, marker
for marker in (
    "/knowledge-context?language=en&media_limit=4&pageview_days=30",
    "Wikimedia-linked context",
    "PUBLIC ATTENTION SIGNAL",
    "PALESTINE DATA FEDERATION",
    "Wikimedia remains outside this evidence-precedence chain",
):
    assert marker in app_js, marker

print("PASS: v4.35.23 Palestine Data Federation + Wikimedia Knowledge Context release contract")
