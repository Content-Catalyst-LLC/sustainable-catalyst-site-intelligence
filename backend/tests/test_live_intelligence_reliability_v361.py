from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from app import main
from app.config import Settings
from app import live_intelligence_reliability_v361 as reliability

NOW = datetime(2026, 7, 20, 18, 0, tzinfo=timezone.utc)


def settings(tmp_path: Path, **overrides):
    values = {
        "external_live": False,
        "live_intelligence_last_known_good_path": str(tmp_path / "live-intelligence-lkg.json"),
        "live_intelligence_fresh_minutes": 30,
        "live_intelligence_delayed_hours": 6,
        "live_intelligence_stale_hours": 24,
        "live_intelligence_max_signal_age_hours": 48,
        "live_intelligence_last_known_good_retention_hours": 168,
    }
    values.update(overrides)
    return Settings(**values)


def signal(signal_id="signal.one", *, age_minutes=5, source_name="Public Source", data_state="live"):
    timestamp = NOW - timedelta(minutes=age_minutes)
    return {
        "signal_id": signal_id,
        "category": "earth_systems",
        "feed_id": "test_feed",
        "label": "TEST SIGNAL",
        "value": "Verified public observation",
        "detail": "A deterministic release-test signal.",
        "status": "current",
        "data_state": data_state,
        "observed_at": timestamp.isoformat(),
        "updated_at": timestamp.isoformat(),
        "source_name": source_name,
        "source_url": "https://example.org/source",
        "destination_url": "https://example.org/detail",
    }


def payload(signals=None, **extra):
    result = {
        "ok": True,
        "version": "3.13.0",
        "schema": "sc-site-intelligence-live-intelligence/1.4",
        "generated_at": NOW.isoformat(),
        "category": "all",
        "count": len(signals or []),
        "signals": list(signals or []),
        "feeds": [],
        "feed_state": {"useful_signal_count": len(signals or []), "platform_signal_count": 0},
        "display": {},
        "boundaries": [],
    }
    result.update(extra)
    return result


def test_freshness_states_are_explicit_and_bounded(tmp_path):
    cfg = settings(tmp_path)
    assert reliability.classify_signal_freshness(signal(age_minutes=5), cfg, now=NOW)["state"] == "live"
    assert reliability.classify_signal_freshness(signal(age_minutes=90), cfg, now=NOW)["state"] == "recently_updated"
    assert reliability.classify_signal_freshness(signal(age_minutes=8 * 60), cfg, now=NOW)["state"] == "delayed"
    assert reliability.classify_signal_freshness(signal(age_minutes=30 * 60), cfg, now=NOW)["state"] == "stale"
    historical = signal(age_minutes=60 * 24 * 365, data_state="historical")
    assert reliability.classify_signal_freshness(historical, cfg, now=NOW)["state"] == "historical"


def test_validation_isolates_malformed_duplicate_and_expired_signals(tmp_path):
    cfg = settings(tmp_path)
    malformed = signal("missing-source")
    malformed["source_name"] = ""
    result = reliability.apply_reliability_policy(
        payload([
            signal("valid"),
            signal("valid"),
            malformed,
            signal("expired", age_minutes=72 * 60),
        ]),
        cfg,
        now=NOW,
    )
    assert [item["signal_id"] for item in result["signals"]] == ["valid"]
    diagnostic = result["feed_state"]["reliability"]
    assert diagnostic["duplicate_signals_suppressed"] == 1
    assert diagnostic["expired_signals_suppressed"] == 1
    assert diagnostic["rejection_counts"]["missing_source"] == 1
    assert diagnostic["partial_feed"] is True
    assert result["delivery"]["state"] == "live"


def test_same_query_last_known_good_recovers_after_origin_failure(tmp_path, monkeypatch):
    cfg = settings(tmp_path)
    monkeypatch.setattr(reliability, "_now_dt", lambda: NOW)
    monkeypatch.setattr(reliability.base, "build_live_intelligence", lambda *args, **kwargs: payload([signal()]))
    first = reliability.build_live_intelligence(cfg, channel="global", limit=8)
    assert first["delivery"]["origin"] == "current_request"
    assert first["delivery"]["last_known_good"] is False

    def fail(*args, **kwargs):
        raise TimeoutError("upstream timeout")

    monkeypatch.setattr(reliability.base, "build_live_intelligence", fail)
    recovered = reliability.build_live_intelligence(cfg, channel="global", limit=8)
    assert recovered["count"] == 1
    assert recovered["delivery"]["origin"] == "last_known_good"
    assert recovered["delivery"]["last_known_good"] is True
    assert recovered["delivery"]["state"] == "delayed"
    assert recovered["delivery"]["origin_error"] == "TimeoutError"


def test_last_known_good_is_never_reused_for_a_different_query(tmp_path, monkeypatch):
    cfg = settings(tmp_path)
    monkeypatch.setattr(reliability, "_now_dt", lambda: NOW)
    monkeypatch.setattr(reliability.base, "build_live_intelligence", lambda *args, **kwargs: payload([signal()]))
    reliability.build_live_intelligence(cfg, channel="global", limit=8)
    monkeypatch.setattr(reliability.base, "build_live_intelligence", lambda *args, **kwargs: (_ for _ in ()).throw(ConnectionError()))
    different = reliability.build_live_intelligence(cfg, channel="global", limit=9)
    assert different["count"] == 0
    assert different["delivery"]["state"] == "unavailable"
    assert different["delivery"]["last_known_good"] is False


def test_honest_empty_geographic_result_is_not_replaced_by_global_cache(tmp_path, monkeypatch):
    cfg = settings(tmp_path)
    monkeypatch.setattr(reliability, "_now_dt", lambda: NOW)
    monkeypatch.setattr(reliability.base, "build_live_intelligence", lambda *args, **kwargs: payload([signal()]))
    reliability.build_live_intelligence(cfg, channel="global", limit=8)
    empty = payload([], channel_filter={"channel_id": "global", "country": "ZZ", "region": "", "matched_count": 0})
    monkeypatch.setattr(reliability.base, "build_live_intelligence", lambda *args, **kwargs: empty)
    result = reliability.build_live_intelligence(cfg, channel="global", country="ZZ", limit=8)
    assert result["count"] == 0
    assert result["delivery"]["state"] == "empty"
    assert result["delivery"]["origin"] == "current_request"
    assert result["delivery"]["last_known_good"] is False


def test_status_contract_exposes_health_without_cache_path(tmp_path, monkeypatch):
    cfg = settings(tmp_path)
    monkeypatch.setattr(reliability, "_now_dt", lambda: NOW)
    monkeypatch.setattr(reliability.base, "build_live_intelligence", lambda *args, **kwargs: payload([signal()]))
    status = reliability.live_intelligence_status(cfg)
    assert status["schema"] == reliability.RELIABILITY_SCHEMA_VERSION
    assert status["service"] == "available"
    assert status["freshness_counts"]["live"] == 1
    assert status["thresholds"]["fresh_minutes"] == 30
    assert "path" not in status["last_known_good"]


def test_public_status_route_uses_reliability_contract(monkeypatch):
    monkeypatch.setattr(main, "live_intelligence_status", lambda settings: {
        "ok": True,
        "version": "3.13.0",
        "schema": reliability.RELIABILITY_SCHEMA_VERSION,
        "service": "available",
        "signal_count": 3,
    })
    response = TestClient(main.app).get("/public/live-intelligence/status")
    assert response.status_code == 200
    assert response.json()["schema"] == reliability.RELIABILITY_SCHEMA_VERSION
