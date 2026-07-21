from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.live_intelligence_source_operations_v320 import (
    LiveIntelligenceSourceOperations,
    REGISTRY_SCHEMA,
    SCHEMA_VERSION,
)
from app.live_intelligence_v314 import build_live_intelligence
from app.main import app

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "backend/data/live_intelligence_source_registry_v320.json"


def _settings(tmp_path: Path, **overrides) -> Settings:
    values = {
        "version": "3.8.0",
        "external_live": False,
        "public_connector_live_checks": False,
        "live_source_operations_registry_path": str(REGISTRY),
        "live_source_operations_state_path": str(tmp_path / "source-state.json"),
        "live_source_operations_history_path": str(tmp_path / "source-history.jsonl"),
    }
    values.update(overrides)
    return Settings(**values)


def test_v320_registry_has_operational_attribution_and_coverage(tmp_path):
    center = LiveIntelligenceSourceOperations(_settings(tmp_path))
    payload = center.registry(public=True)
    assert payload["schema"] == SCHEMA_VERSION
    assert payload["version"] == "3.8.0"
    assert payload["source_count"] == 8
    assert {item["feed_id"] for item in payload["sources"]} == {
        "noaa_nws", "usgs_earthquakes", "nasa_eonet", "reliefweb",
        "nasa_power", "openalex", "world_bank", "platform_status",
    }
    assert all(item["license"]["name"] for item in payload["sources"])
    assert all(item["coverage"]["geographic"] for item in payload["sources"])
    assert all(item["quality"]["status"] for item in payload["sources"])
    assert "api_key" not in json.dumps(payload).lower()


def test_registry_file_schema_and_safe_source_terms():
    payload = json.loads(REGISTRY.read_text())
    assert payload["schema"] == REGISTRY_SCHEMA
    assert payload["version"] == "3.8.0"
    sources = {item["feed_id"]: item for item in payload["sources"]}
    assert sources["openalex"]["license"]["name"] == "CC0"
    assert "data year" in sources["world_bank"]["public_note"].lower()
    assert "emergency-warning" in sources["noaa_nws"]["quality"]["limitations"]


def test_source_configuration_updates_are_bounded_and_persisted(tmp_path):
    center = LiveIntelligenceSourceOperations(_settings(tmp_path))
    updated = center.update_source("openalex", {
        "enabled": False,
        "priority": 0,
        "refresh_minutes": 1,
        "cache_ttl_minutes": 99999,
        "ignored": "value",
    })["source"]
    assert updated["effective"] == {
        "enabled": False,
        "priority": 1,
        "refresh_minutes": 5,
        "cache_ttl_minutes": 10080,
    }
    reloaded = LiveIntelligenceSourceOperations(_settings(tmp_path)).source("openalex", public=False)["source"]
    assert reloaded["effective"] == updated["effective"]
    assert reloaded["health"]["state"] == "disabled"


def test_result_history_tracks_freshness_rate_and_failures(tmp_path):
    fixed = datetime(2026, 7, 20, 12, 0, tzinfo=timezone.utc)
    center = LiveIntelligenceSourceOperations(_settings(tmp_path), now_fn=lambda: fixed)
    center.record_result("usgs_earthquakes", ok=True, data_state="live", record_count=3, duration_ms=120)
    source = center.source("usgs_earthquakes", public=False)["source"]
    assert source["health"]["state"] == "healthy"
    assert source["runtime"]["requests_today"] == 1
    assert source["runtime"]["last_record_count"] == 3

    later = fixed + timedelta(minutes=20)
    center = LiveIntelligenceSourceOperations(_settings(tmp_path), now_fn=lambda: later)
    center.record_result("usgs_earthquakes", ok=False, data_state="unavailable", error="TimeoutError")
    source = center.source("usgs_earthquakes", public=False)["source"]
    assert source["health"]["state"] == "degraded"
    assert source["runtime"]["consecutive_failures"] == 1
    assert source["runtime"]["last_error"] == "TimeoutError"
    history = center.history(feed_id="usgs_earthquakes", limit=10)
    assert history["count"] == 2
    assert history["history"][-1]["error_class"] == "TimeoutError"


def test_manual_configuration_and_live_tests_are_explicit(tmp_path):
    center = LiveIntelligenceSourceOperations(_settings(tmp_path))
    config = center.manual_test("world_bank", live=False)
    assert config["ok"] is True
    assert config["live_request_made"] is False

    live = center.manual_test(
        "world_bank",
        live=True,
        test_runner=lambda feed_id: {
            "count": 2,
            "feed_state": {"active_feeds": [feed_id], "development": {"data_state": "cached"}},
        },
    )
    assert live["ok"] is True
    assert live["live_request_made"] is True
    assert live["data_state"] == "cached"
    assert center.source("world_bank", public=False)["source"]["runtime"]["last_test_status"] == "passed"


def test_disabled_operational_source_is_removed_from_effective_feed(tmp_path):
    settings = _settings(tmp_path)
    center = LiveIntelligenceSourceOperations(settings)
    center.update_source("platform_status", {"enabled": False})
    payload = build_live_intelligence(settings, feeds=["platform_status"], record_operations=False)
    assert payload["count"] == 0
    assert payload["feed_state"]["active_feeds"] == []
    assert payload["source_operations"]["enabled"] is True


def test_public_and_admin_source_operations_routes_are_registered():
    client = TestClient(app)
    public = client.get("/public/live-intelligence/sources")
    assert public.status_code == 200
    assert public.json()["source_count"] == 8
    detail = client.get("/public/live-intelligence/sources/usgs_earthquakes")
    assert detail.status_code == 200
    assert detail.json()["source"]["feed_id"] == "usgs_earthquakes"
    missing = client.get("/public/live-intelligence/sources/not_real")
    assert missing.status_code == 404
    admin = client.get("/admin/live-intelligence/sources/control-center")
    assert admin.status_code == 200
    assert admin.json()["capabilities"]["manual_test"] is True


def test_wordpress_source_operations_control_surface_contract():
    php = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text()
    for marker in [
        "Signal source operations", "rest_live_intelligence_sources",
        "rest_live_intelligence_source_update", "rest_live_intelligence_source_test",
        "scsi-source-operations-table", "Check config", "Live test",
    ]:
        assert marker in php
    assert "ast-breadcrumbs-wrapper" not in (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.css").read_text()
