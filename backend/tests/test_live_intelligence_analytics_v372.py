from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app import main
from app.config import Settings
from app.live_intelligence_analytics_v372 import (
    ANALYTICS_SCHEMA_VERSION,
    LiveIntelligenceAnalyticsStore,
    analytics_policy,
    sanitize_analytics_event,
)


def event(event_type="signal_impression", **overrides):
    payload = {
        "event_type": event_type,
        "surface": "homepage",
        "signal_id": "usgs.earthquake.1",
        "signal_family": "climate_earth_systems",
        "freshness_state": "live",
        "source_id": "usgs_earthquakes",
        "destination_type": "signal_context",
        "viewport": "desktop",
        "motion_mode": "standard",
        "delivery_state": "live",
    }
    payload.update(overrides)
    return payload


def test_sanitizer_accepts_bounded_dimensions_and_rejects_identifiers():
    clean = sanitize_analytics_event(event(count=100))
    assert clean["count"] == 25
    assert clean["signal_id"] == "usgs.earthquake.1"
    try:
        sanitize_analytics_event(event(user_id="visitor-123"))
        assert False, "visitor identifiers must be rejected"
    except ValueError as exc:
        assert "prohibited" in str(exc).lower()


def test_store_writes_aggregate_counters_only(tmp_path):
    settings = Settings(live_intelligence_analytics_state_path=str(tmp_path / "analytics.json"))
    store = LiveIntelligenceAnalyticsStore(settings)
    receipt = store.record([event(), event("source_open", destination_type="primary_source")])
    assert receipt["stored_raw_events"] is False
    state = store.read()
    text = str(state).lower()
    assert "visitor" not in text
    assert "page_path" not in text
    day = next(iter(state["days"].values()))
    assert day["events"]["signal_impression"] == 1
    assert day["sources"]["usgs_earthquakes"]["source_open"] == 1


def test_summary_reports_public_value_delivery_and_accessibility(tmp_path):
    settings = Settings(live_intelligence_analytics_state_path=str(tmp_path / "analytics.json"))
    store = LiveIntelligenceAnalyticsStore(settings)
    store.record([
        event("component_impression"),
        event("feed_load_success"),
        event("signal_impression"),
        event("evidence_record_open", destination_type="evidence_record"),
        event("reduced_motion_use", motion_mode="reduced"),
    ])
    summary = store.summary(days=30)
    assert summary["schema"] == ANALYTICS_SCHEMA_VERSION
    assert summary["engagement"]["evidence_record_opens"] == 1
    assert summary["delivery"]["load_success_rate"] == 100.0
    assert summary["accessibility"]["reduced_motion_uses"] == 1
    assert summary["privacy"]["individual_user_tracking"] is False


def test_retention_prunes_old_day_buckets(tmp_path):
    settings = Settings(
        live_intelligence_analytics_state_path=str(tmp_path / "analytics.json"),
        live_intelligence_analytics_retention_days=30,
    )
    store = LiveIntelligenceAnalyticsStore(settings)
    now = datetime.now(timezone.utc)
    store.record([event()], now=now - timedelta(days=45))
    store.record([event("component_impression")], now=now)
    state = store.read()
    assert len(state["days"]) == 1


def test_policy_discloses_no_tracking_and_no_click_only_optimization():
    policy = analytics_policy()
    assert policy["privacy"]["raw_events_stored"] is False
    assert policy["privacy"]["cross_site_tracking"] is False
    assert "not the sole" in policy["success_standard"][-1]


def test_public_event_summary_and_reliability_endpoints(tmp_path):
    settings = Settings(live_intelligence_analytics_state_path=str(tmp_path / "analytics.json"))
    main.app.dependency_overrides[main.get_settings] = lambda: settings
    client = TestClient(main.app)
    try:
        accepted = client.post("/public/live-intelligence/analytics/events", json={"events": [
            event("component_impression"),
            event("feed_load_success", source_id="usgs_earthquakes"),
            event("signal_impression", source_id="usgs_earthquakes"),
        ]})
        summary = client.get("/public/live-intelligence/analytics/summary?days=30")
        reliability = client.get("/public/live-intelligence/analytics/source-reliability?days=30")
        policy = client.get("/public/live-intelligence/analytics-policy")
    finally:
        main.app.dependency_overrides.pop(main.get_settings, None)
    assert accepted.status_code == 202
    assert accepted.json()["receipt"]["accepted_events"] == 3
    assert summary.status_code == 200
    assert summary.json()["totals"]["component_impression"] == 1
    assert reliability.status_code == 200
    assert reliability.json()["sources"][0]["source_id"] == "usgs_earthquakes"
    assert policy.status_code == 200


def test_admin_summary_is_aggregate_and_can_include_signal_counters(tmp_path):
    settings = Settings(live_intelligence_analytics_state_path=str(tmp_path / "analytics.json"))
    store = LiveIntelligenceAnalyticsStore(settings)
    store.record([event()])
    main.app.dependency_overrides[main.get_settings] = lambda: settings
    client = TestClient(main.app)
    try:
        response = client.get("/admin/live-intelligence/analytics?days=30")
    finally:
        main.app.dependency_overrides.pop(main.get_settings, None)
    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["by_signal"]["usgs.earthquake.1"]["signal_impression"] == 1
    assert payload["status"]["raw_event_storage"] is False
