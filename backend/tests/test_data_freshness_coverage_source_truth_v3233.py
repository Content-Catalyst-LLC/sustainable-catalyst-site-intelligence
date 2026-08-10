from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.data_truth_v3233 import DataTruthCenter
from app.main import app

ROOT = Path(__file__).resolve().parents[2]
CLIENT = TestClient(app)


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_public_data_truth_directory_discloses_non_live_states_and_boundaries():
    response = CLIENT.get("/public/data-truth")
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["version"] == "4.15.0"
    assert payload["release_id"] == "site-intelligence-v4.15.0"
    assert payload["contract"] == "data-freshness-coverage-and-source-truth"
    assert payload["source_count"] == 8
    assert payload["classification_policy"]["cached_is_live"] is False
    assert payload["classification_policy"]["stale_is_live"] is False
    assert payload["classification_policy"]["demonstration_is_live"] is False
    assert payload["summary"]["demonstration"] == 8
    assert all(not row["data_state"]["live_claim_allowed"] for row in payload["sources"])


def test_source_detail_exposes_publisher_endpoint_license_coverage_refresh_and_schema():
    payload = CLIENT.get("/public/data-truth/usgs_earthquakes").json()
    source = payload["source"]
    assert source["publisher"] == "U.S. Geological Survey"
    assert source["endpoint"]["url"].startswith("https://earthquake.usgs.gov/")
    assert source["license"]["name"]
    assert source["coverage"]["geographic"]
    assert source["coverage"]["temporal"]
    assert source["refresh_policy"]["refresh_minutes"] > 0
    assert source["schema"]["required_fields"]
    assert source["schema"]["status"] == "not_observed"
    assert source["completeness"]["complete"] is True
    assert source["resilience"]["fallback_may_claim_live"] is False


def test_unknown_source_fails_closed():
    response = CLIENT.get("/public/data-truth/not_a_source")
    assert response.status_code == 404


def test_registry_has_canonical_truth_metadata_for_every_source():
    import json
    registry = json.loads(read("backend/data/live_intelligence_source_registry_v320.json"))
    assert registry["version"] == "4.15.0"
    assert len(registry["sources"]) == 8
    for source in registry["sources"]:
        assert source["endpoint"]["url"]
        assert source["data_classification"] in {"live", "historical_snapshot", "context_only"}
        assert source["schema_contract"]["required_fields"]
        assert source["retry_policy"]["circuit_breaker_failures"] == 3
        assert source["retry_policy"]["automatic_fallback_claims_live"] is False


def test_app_shell_loads_data_truth_inside_application_before_production_truth():
    html = read("backend/public_app/index.html")
    assert '/app/assets/data-truth-v32371.css?v=4.15.0' in html
    assert '/app/assets/data-truth-v32371.js?v=4.15.0' in html
    assert html.index("cartographic-interaction-v3232.js") < html.index("data-truth-v32371.js") < html.index("production-truth-v3231.js")
    js = read("backend/public_app/assets/data-truth-v32371.js")
    for token in ("dataTruthToggle", "dataTruthPanel", "stale_marker_required", "Cached, historical, demonstration", "SCSIDataTruthV32371"):
        assert token in js


def test_runtime_health_offline_shell_and_wordpress_package_include_truth_assets_without_host_execution():
    health = CLIENT.get("/public/runtime-health").json()
    paths = {item["path"] for item in health["assets"]}
    endpoints = {item["path"] for item in health["endpoint_contracts"]}
    assert "/app/assets/data-truth-v32371.js" in paths
    assert "/app/assets/data-truth-v32371.css" in paths
    assert "/public/data-truth" in endpoints
    worker = read("backend/public_app/service-worker.js")
    assert "data-truth-v32371.js" in worker and "data-truth-v32371.css" in worker
    php = read("wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php")
    assert "Version: 4.15.0" in php
    assert "dataTruthCssUrl" in php and "dataTruthJsUrl" in php
    assert "wp_enqueue_script('scsi-data-truth'" not in php
    assert (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/data-truth-v32371.js").is_file()
    assert (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/data-truth-v32371.css").is_file()


def test_classification_marks_failed_last_known_good_as_cached_not_live():
    class Operations:
        def registry(self, public=True):
            return {"sources": [{
                "feed_id": "sample", "label": "Sample", "provider": "Publisher", "category": "test",
                "endpoint": {"url": "https://example.test/data"}, "license": {"name": "Open"},
                "coverage": {"geographic": "Global", "temporal": "Current"},
                "default_refresh_minutes": 10, "default_cache_ttl_minutes": 30, "stale_after_minutes": 60,
                "data_classification": "live", "schema_contract": {"record_type": "sample", "required_fields": ["id"]},
                "retry_policy": {"circuit_breaker_failures": 3, "maximum_attempts": 3, "automatic_fallback_claims_live": False},
                "effective": {"enabled": True, "refresh_minutes": 10, "cache_ttl_minutes": 30},
                "health": {"state": "degraded", "freshness": "fresh", "age_minutes": 5, "due": True},
                "runtime": {"last_success_at": "2026-08-05T20:00:00Z", "last_attempt_at": "2026-08-05T20:05:00Z", "last_data_state": "cached", "last_status": "error", "consecutive_failures": 1},
            }]}
    payload = DataTruthCenter(Settings(demo_mode=False), operations=Operations()).directory()
    row = payload["sources"][0]
    assert row["data_state"]["presentation"] == "recently_cached"
    assert row["data_state"]["live_claim_allowed"] is False
    assert row["data_state"]["stale_marker_required"] is True
    assert row["resilience"]["circuit_breaker_state"] == "watch"
