from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.unified_public_intelligence_v4000 import public_unified_navigation

CLIENT = TestClient(app)
ROOT = Path(__file__).resolve().parents[2]

EXPECTED_AREAS = {
    "live-overview": ["overview", "global", "events", "alerts"],
    "places-systems": ["country", "dossiers", "economics", "law", "science", "humanitarian", "resources", "thematic"],
    "analysis": ["compare", "spatial", "earth", "harmonization", "models", "scenarios"],
    "evidence-research": ["platform", "observatory", "research", "evidence", "graph", "sources", "saved"],
    "publishing-monitoring": ["briefing", "publishing", "monitoring", "workspaces"],
    "methods-operations": ["integration", "workflows", "federation", "governance", "experience", "launch"],
}


def test_v4_platform_contract_consolidates_without_removing_routes():
    payload = CLIENT.get("/public/v4").json()
    assert payload["ok"] is True
    assert payload["version"] == "4.12.0"
    assert payload["release_name"] == "Unified Public Intelligence Platform"
    assert payload["primary_area_count"] == 6
    assert payload["route_count"] == 35
    assert payload["canonical_contract_count"] == 6
    assert payload["compatibility"]["legacy_routes_preserved"] is True
    assert payload["compatibility"]["deep_links_preserved"] is True
    assert payload["compatibility"]["automatic_migrations"] is False
    assert len(payload["platform_sha256"]) == 64


def test_v4_navigation_has_six_complete_non_overlapping_areas():
    payload = public_unified_navigation()
    assert payload["primary_area_count"] == 6
    assert payload["route_count"] == 35
    assert payload["all_routes_unique"] is True
    areas = {row["id"]: row["routes"] for row in payload["areas"]}
    assert areas == EXPECTED_AREAS
    assert len({row["route_id"] for row in payload["routes"]}) == 35


def test_v4_contract_registry_is_explicit_and_review_bounded():
    payload = CLIENT.get("/public/v4/contracts").json()
    assert payload["contract_count"] == 6
    assert payload["single_truth_contract"] is True
    assert payload["single_route_state_contract"] is True
    assert payload["single_publication_export_contract"] is True
    assert payload["human_review_preserved"] is True
    assert len(payload["contracts_sha256"]) == 64


def test_v4_readiness_requires_six_areas_and_all_legacy_routes():
    payload = CLIENT.get("/public/v4/readiness").json()
    assert payload["ok"] is True
    assert all(payload["checks"].values())
    assert payload["summary"] == {"primary_areas": 6, "preserved_routes": 35, "canonical_contracts": 6}
    assert len(payload["readiness_sha256"]) == 64


def test_v4_browser_assets_and_service_worker_are_shipped_to_both_surfaces():
    html = (ROOT / "backend/public_app/index.html").read_text()
    sw = (ROOT / "backend/public_app/service-worker.js").read_text()
    js = (ROOT / "backend/public_app/assets/unified-platform-v4000.js").read_text()
    css = (ROOT / "backend/public_app/assets/unified-platform-v4000.css").read_text()
    assert 'data-scsi-platform-contract="unified-v4"' in html
    assert 'unified-platform-v4000.css?v=4.12.0' in html
    assert 'unified-platform-v4000.js?v=4.12.0' in html
    assert 'unified-platform-v4000.js' in sw and 'unified-platform-v4000.css' in sw
    assert 'SCSIUnifiedPlatformV4000' in js and 'GROUPS=[' in js
    assert '.v4000-nav-group' in css
    assert js == (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/unified-platform-v4000.js").read_text()
    assert css == (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/unified-platform-v4000.css").read_text()
