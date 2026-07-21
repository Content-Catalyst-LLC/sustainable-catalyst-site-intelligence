from pathlib import Path

from fastapi.testclient import TestClient

from app import main
from app.config import Settings

ROOT = Path(__file__).resolve().parents[2]


def test_v372_release_contract_markers():
    requirements = {
        "backend/app/version.py": ['APP_VERSION = "3.7.2"'],
        "backend/app/config.py": [
            "live_intelligence_analytics_enabled", "live_intelligence_analytics_state_path",
            "live_intelligence_analytics_retention_days", "live_intelligence_analytics_max_signal_buckets",
        ],
        "backend/app/live_intelligence_analytics_v372.py": [
            "ANALYTICS_SCHEMA_VERSION", "LiveIntelligenceAnalyticsStore", "sanitize_analytics_event",
            "aggregate_counters_only", "raw_events_stored", "individual_user_tracking",
            "page_paths_stored", "clicks alone",
        ],
        "backend/app/main.py": [
            "/public/live-intelligence/analytics/events", "/public/live-intelligence/analytics-policy",
            "/public/live-intelligence/analytics/summary", "/public/live-intelligence/analytics/source-reliability",
            "/admin/live-intelligence/analytics", '"aggregate_counters_only": True',
        ],
        "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php": [
            "Version: 3.7.2", "rest_live_intelligence_analytics_events",
            "rest_live_intelligence_analytics_summary", "rest_live_intelligence_analytics_source_reliability",
        ],
        "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js": [
            "sendLiveAnalytics", "signal_impression", "feed_load_failure", "reduced_motion_use",
            "Live Intelligence uses its own aggregate-only telemetry contract",
        ],
        "README.md": ["v3.7.2 — Analytics and Public-Value Measurement"],
        "RELEASE_NOTES_SITE_INTELLIGENCE_V372.md": [
            "Analytics and Public-Value Measurement", "Raw events are never stored",
        ],
        "docs/RELEASE_MANIFEST_V372.json": [
            '"version": "3.7.2"', '"raw_events_stored": false',
            '"individual_user_tracking": false', '"click_through_rate_only": false',
        ],
    }
    for relative, needles in requirements.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        for needle in needles:
            assert needle in text, f"{needle!r} missing from {relative}"


def test_homepage_contract_discloses_aggregate_measurement(monkeypatch, tmp_path):
    monkeypatch.setattr(main, "build_live_intelligence", lambda settings, **kwargs: {
        "ok": True, "signals": [], "display": {}, "feed_state": {}, "boundaries": [],
    })
    settings = Settings(
        live_intelligence_rotation_state_path=str(tmp_path / "rotation.json"),
        live_intelligence_analytics_state_path=str(tmp_path / "analytics.json"),
    )
    main.app.dependency_overrides[main.get_settings] = lambda: settings
    try:
        response = TestClient(main.app).get("/public/live-intelligence/homepage")
    finally:
        main.app.dependency_overrides.pop(main.get_settings, None)
    assert response.status_code == 200
    measurement = response.json()["measurement"]
    assert measurement["aggregate_counters_only"] is True
    assert measurement["individual_user_tracking"] is False
    assert measurement["click_through_rate_only"] is False
