#!/usr/bin/env python3
from pathlib import Path
import sys
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.config import Settings
from app.main import app
from app.version import APP_VERSION
from app.release_health_v43520 import deployment_verification, source_health_policy
from app.country_linked_records_v43520 import readiness as linked_record_readiness
from app.production_soak_v43519 import readiness as soak_readiness
from app.evidence_presentation_v43519 import readiness as evidence_presentation_readiness
from app.workspace_browser_audit_v43518 import workspace_browser_readiness
from app.external_resilience_v43517 import resilience_readiness
from app.workspace_evidence_unification_v4358 import readiness as workspace_evidence_readiness

assert APP_VERSION == "4.35.21"
settings = Settings(_env_file=None)

linked = linked_record_readiness()
assert linked["ok"] is True
assert linked["network_calls_performed"] is False
assert linked["upstream_health_release_blocking"] is False
assert linked["checks"]["reliefweb_country_query_is_source_bounded"] is True
assert linked["checks"]["hdx_public_discovery_lane_present"] is True
assert linked["checks"]["discovery_metadata_not_promoted_to_observation"] is True
assert linked["checks"]["zero_records_not_interpreted_as_zero_incidence"] is True

assert soak_readiness(settings)["ok"] is True
assert evidence_presentation_readiness()["ok"] is True
assert workspace_browser_readiness()["ok"] is True
assert resilience_readiness(settings)["ok"] is True
assert workspace_evidence_readiness()["ok"] is True

verification = deployment_verification(settings)
assert verification["ok"] is True
assert len(verification["required_routes"]) == 13
assert "/public/country-linked-records/readiness" in verification["required_routes"]
for check in (
    "country_linked_record_recovery_ready",
    "country_linked_record_readiness_network_free",
    "country_linked_upstream_health_non_blocking",
    "production_soak_control_plane_ready",
    "semantic_truth_guard_ready",
    "workspace_browser_control_plane_ready",
):
    assert verification["checks"][check] is True, check
health = source_health_policy(settings)
assert health["country_linked_record_policy"]["discovery_metadata_is_current_condition"] is False
assert health["country_linked_record_policy"]["zero_linked_records_means_zero_incidence"] is False
assert health["country_linked_record_policy"]["upstream_health_release_blocking"] is False

client = TestClient(app)
response = client.get("/public/country-linked-records/readiness")
assert response.status_code == 200 and response.json()["ok"] is True
response = client.get("/public/deployment-verification")
assert response.status_code == 200 and response.json()["checks"]["country_linked_record_recovery_ready"] is True

main = (ROOT / "backend/app/main.py").read_text()
unified = (ROOT / "backend/app/unified_live_events.py").read_text()
linked_module = (ROOT / "backend/app/country_linked_records_v43520.py").read_text()
app_js = (ROOT / "backend/public_app/assets/app.js").read_text()
index = (ROOT / "backend/public_app/index.html").read_text()
for marker in (
    '@app.get("/public/country/{country_code}/linked-records")',
    '@app.get("/public/country-linked-records/readiness")',
    "release_health_v43520",
):
    assert marker in main, marker
for marker in (
    '"filter[conditions][1][field]": "country.iso3"',
    'country_code=country_code',
    ':country:{str(country_code or \'GLOBAL\').upper()}',
):
    assert marker in unified, marker
for marker in (
    "hdx_dataset_search",
    '"record_class": "dataset-discovery"',
    '"evidence_class": "discovery-metadata"',
    "zero record count",
):
    assert marker in linked_module, marker
assert "/public/country/${encodeURIComponent(code)}/linked-records?days=90&limit=24" in app_js
assert "/public/events?country_code=" not in app_js[app_js.index("async function loadCountryEvents"):app_js.index("function setCountryLoading")]
assert "Open humanitarian view" in index

print("PASS: v4.35.21 Country-Linked Record Recovery release contract")
