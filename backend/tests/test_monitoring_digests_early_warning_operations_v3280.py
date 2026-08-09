from fastapi.testclient import TestClient

from app.main import app
from app.monitoring_early_warning_v3280 import MonitoringEarlyWarningCenter

CLIENT = TestClient(app)


def watchlist():
    return {
        "title": "Brazil energy watch",
        "cadence": "daily",
        "countries": ["BRA"],
        "areas": [{"id": "bra", "label": "Brazil", "country": "BRA", "resolution": "country"}],
        "source_ids": ["world-bank"],
        "rules": [{"id": "energy-threshold", "name": "Energy threshold", "indicator_id": "energy-use", "country": "BRA", "source_id": "world-bank", "operator": ">=", "threshold": 10, "unit": "GJ/person"}],
    }


def current_signal(value=10.5, freshness="historical_only", withdrawn=False):
    return {"id": "bra-energy-2023", "title": "Energy use", "indicator_id": "energy-use", "country": "BRA", "source_id": "world-bank", "value": value, "unit": "GJ/person", "observed_at": "2023", "retrieved_at": "2026-08-06T00:00:00Z", "freshness": freshness, "withdrawn": withdrawn, "limitations": ["Historical observation"]}


def test_schema_is_review_gated_and_not_emergency_dispatch():
    payload = CLIENT.get("/public/monitoring-operations").json()
    assert payload["version"] == "3.31.0"
    assert payload["contract"] == "monitoring-digests-and-early-warning-operations"
    assert payload["alert_states"] == ["new", "continuing", "changed", "resolved", "withdrawn"]
    assert payload["human_review_required"] is True
    assert payload["automatic_publication"] is False
    assert payload["automatic_emergency_dispatch"] is False
    assert payload["individual_tracking"] is False
    assert payload["hidden_risk_score"] is False


def test_watchlist_preserves_country_area_sources_and_thresholds_without_server_write():
    payload = CLIENT.post("/public/monitoring-operations/watchlist/preview", json=watchlist()).json()
    w = payload["watchlist"]
    assert w["countries"] == ["BRA"]
    assert w["areas"][0]["country"] == "BRA"
    assert w["source_ids"] == ["world-bank"]
    assert w["rules"][0]["threshold"] == 10
    assert w["server_write_performed"] is False
    assert len(w["fingerprint"]) == 64


def test_threshold_match_is_new_and_explains_trigger_and_limitations():
    payload = CLIENT.post("/public/monitoring-operations/evaluate", json={"watchlist": watchlist(), "signals": [current_signal()]}).json()
    assert payload["alert_count"] == 1
    alert = payload["alerts"][0]
    assert alert["state"] == "new"
    assert "energy-use >= 10" in alert["trigger"]
    assert "Energy threshold" in alert["explanation"]
    assert alert["freshness"] == "historical_only"
    assert alert["limitations"] == ["Historical observation"]
    assert alert["operational_emergency_alert"] is False


def test_previous_signal_supports_continuing_changed_and_resolved_states():
    base = {"watchlist": watchlist(), "previous_signals": [current_signal(10.5)]}
    continuing = CLIENT.post("/public/monitoring-operations/evaluate", json={**base, "signals": [current_signal(10.5)]}).json()
    changed = CLIENT.post("/public/monitoring-operations/evaluate", json={**base, "signals": [current_signal(11.5)]}).json()
    resolved = CLIENT.post("/public/monitoring-operations/evaluate", json={**base, "signals": []}).json()
    assert continuing["alerts"][0]["state"] == "continuing"
    assert changed["alerts"][0]["state"] == "changed"
    assert resolved["alerts"][0]["state"] == "resolved"
    assert "does not prove" in resolved["alerts"][0]["explanation"]


def test_withdrawn_signal_remains_explicitly_withdrawn():
    payload = CLIENT.post("/public/monitoring-operations/evaluate", json={"watchlist": watchlist(), "signals": [current_signal(10.5, withdrawn=True)]}).json()
    assert payload["alerts"][0]["state"] == "withdrawn"


def test_source_change_monitoring_does_not_claim_publisher_wide_outage():
    payload = CLIENT.post("/public/monitoring-operations/source-changes", json={
        "previous": [{"source_id": "world-bank", "schema_fingerprint": "a", "status": "operational", "freshness": "current", "coverage_fingerprint": "1"}],
        "current": [{"source_id": "world-bank", "schema_fingerprint": "b", "status": "degraded", "freshness": "stale", "coverage_fingerprint": "1"}],
    }).json()
    row = payload["changes"][0]
    assert row["state"] == "changed"
    assert set(row["changed_fields"]) == {"schema_fingerprint", "status", "freshness"}
    assert row["publisher_outage_verified"] is False
    assert payload["publisher_wide_outage_claimed"] is False


def test_modeled_warning_is_distinct_from_source_alert_and_has_no_automatic_action():
    payload = CLIENT.post("/public/monitoring-operations/modeled-warning/preview", json={"model_id": "early-warning-demo", "model_output": 0.8, "threshold": 0.7}).json()
    w = payload["warning"]
    assert w["state"] == "active"
    assert w["modeled_warning"] is True
    assert w["source_alert"] is False
    assert w["operational_emergency_alert"] is False
    assert w["automatic_action"] is False
    assert w["probability_claimed"] is False


def test_digest_stays_draft_until_human_review():
    evaluation = CLIENT.post("/public/monitoring-operations/evaluate", json={"watchlist": watchlist(), "signals": [current_signal()]}).json()
    payload = CLIENT.post("/public/monitoring-operations/digest/preview", json={"title": "Brazil daily monitoring", "alerts": evaluation["alerts"]}).json()
    d = payload["digest"]
    assert d["status"] == "draft"
    assert d["human_review_required"] is True
    assert d["publication_allowed"] is False
    assert d["automatic_publication"] is False
    assert d["state_counts"]["new"] == 1
    assert len(d["fingerprint"]) == 64


def test_public_feed_contract_requires_approved_items_without_profiles_or_tracking():
    payload = CLIENT.get("/public/monitoring-operations/feed-contract").json()
    assert payload["formats"] == ["json", "atom", "rss"]
    assert payload["published_items_must_be_human_approved"] is True
    assert payload["subscriber_profile_required"] is False
    assert payload["tracking_required"] is False


def test_sensitive_identity_or_credential_fields_are_rejected():
    payload = watchlist(); payload["user_id"] = "not-allowed"
    response = CLIENT.post("/public/monitoring-operations/watchlist/preview", json=payload)
    assert response.status_code == 400


def test_release_assets_and_policy_are_wired():
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    html = (root / "backend/public_app/index.html").read_text()
    worker = (root / "backend/public_app/service-worker.js").read_text()
    js = (root / "backend/public_app/assets/monitoring-operations-v3280.js").read_text()
    policy = (root / "backend/data/monitoring_early_warning_policy_v3280.json").read_text()
    assert "monitoring-operations-v3280.css?v=3.31.0" in html
    assert "monitoring-operations-v3280.js?v=3.31.0" in html
    assert "monitoring-operations-v3280.js" in worker
    assert "SCSIMonitoringOperationsV3280" in js
    assert '"version": "3.31.0"' in policy
