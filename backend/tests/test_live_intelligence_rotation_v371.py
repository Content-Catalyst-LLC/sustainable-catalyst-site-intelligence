from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app import main
from app.config import Settings
from app.live_intelligence_rotation_v371 import (
    ROTATION_SCHEMA_VERSION,
    LiveIntelligenceRotationStore,
    apply_rotation_policy,
    rotation_policy,
    score_rotation_candidate,
    select_rotation_signals,
)


def signal(signal_id: str, family: str, source: str, *, freshness: str = "live", score: int = 80, priority: int = 40, geography: str = "global"):
    now = datetime.now(timezone.utc).isoformat()
    return {
        "signal_id": signal_id,
        "label": signal_id.upper(),
        "value": "Public observation",
        "formatted_value": "Public observation",
        "category": "earth_systems",
        "signal_family": family,
        "family_label": family.replace("_", " ").title(),
        "feed_id": source,
        "source_name": source,
        "source_url": "https://example.org/source",
        "validation_state": "valid",
        "freshness_state": freshness,
        "data_state": "current" if freshness != "stale" else "stale",
        "selection_score": score,
        "priority_score": score,
        "priority": priority,
        "observed_at": now,
        "updated_at": now,
        "homepage_eligible": True,
        "geography": {"scope": geography, "label": geography.title()},
        "primary_destination": {"type": "signal_context", "url": f"/signal/{signal_id}"},
        "secondary_destinations": [{"type": "evidence_record", "url": f"/evidence/{signal_id}"}],
        "methodology_note": "Public methodology context.",
        "responsible_use_note": "Interpret with source and limitations.",
    }


def test_rotation_score_is_transparent_and_repetition_is_penalized():
    first = score_rotation_candidate(signal("one", "climate_earth_systems", "usgs"), exposure_count=0)
    repeated = score_rotation_candidate(signal("one", "climate_earth_systems", "usgs"), exposure_count=3)
    assert first["rotation_base_score"] > repeated["rotation_base_score"]
    assert repeated["rotation_score_components"]["repetition_penalty"] == -15
    assert "freshness" in first["rotation_score_components"]
    assert first["rotation_eligible"] is True


def test_rotation_selection_balances_family_and_source_deterministically():
    signals = [
        signal("earth-a", "climate_earth_systems", "usgs", score=95),
        signal("earth-b", "climate_earth_systems", "usgs", score=94),
        signal("human-a", "humanitarian_conditions", "reliefweb", score=82),
        signal("science-a", "science_environment", "openalex", score=80),
    ]
    selected, diagnostics = select_rotation_signals(signals, limit=3)
    assert [item["signal_id"] for item in selected] == ["earth-a", "human-a", "science-a"]
    assert diagnostics["family_counts"] == {
        "climate_earth_systems": 1,
        "humanitarian_conditions": 1,
        "science_environment": 1,
    }
    assert [item["rotation_rank"] for item in selected] == [1, 2, 3]


def test_human_override_requires_approval_and_never_changes_observation(tmp_path):
    settings = Settings(live_intelligence_rotation_state_path=str(tmp_path / "rotation.json"))
    store = LiveIntelligenceRotationStore(settings)
    try:
        store.set_override("earth-a", {"mode": "pin", "reason": "Editorial priority"})
        assert False, "approval should be required"
    except ValueError as exc:
        assert "Human approval" in str(exc)
    override = store.set_override("earth-a", {
        "mode": "pin",
        "reason": "Human-reviewed public-interest context",
        "human_approved": True,
        "updated_by": "editor",
    })
    assert override["changes_observation"] is False
    assert override["automatic_emergency_publication"] is False
    assert store.active_overrides()["earth-a"]["mode"] == "pin"


def test_suppression_and_pin_are_applied_without_mutating_values():
    inputs = [
        signal("pinned", "science_environment", "openalex", score=30),
        signal("suppressed", "climate_earth_systems", "usgs", score=99),
        signal("normal", "humanitarian_conditions", "reliefweb", score=70),
    ]
    selected, diagnostics = select_rotation_signals(inputs, limit=2, overrides={
        "pinned": {"mode": "pin", "human_approved": True, "reason": "Reviewed"},
        "suppressed": {"mode": "suppress", "human_approved": True, "reason": "Duplicate framing"},
    })
    assert [item["signal_id"] for item in selected] == ["pinned", "normal"]
    assert selected[0]["value"] == "Public observation"
    assert diagnostics["suppressed_signal_ids"] == ["suppressed"]


def test_rotation_history_is_aggregate_and_expires_outside_window(tmp_path):
    settings = Settings(live_intelligence_rotation_state_path=str(tmp_path / "rotation.json"))
    store = LiveIntelligenceRotationStore(settings)
    now = datetime.now(timezone.utc)
    store.record_selection(surface="homepage", signals=[signal("earth-a", "climate_earth_systems", "usgs")], now=now)
    assert store.exposure_counts(surface="homepage", window_hours=24, now=now)["earth-a"] == 1
    state = store.read()
    assert "user" not in str(state).lower()
    state["history"][0]["selected_at"] = (now - timedelta(days=10)).isoformat()
    store.write(state)
    assert store.exposure_counts(surface="homepage", window_hours=24, now=now)["earth-a"] == 0


def test_apply_rotation_policy_returns_public_diagnostics_and_records_history(tmp_path):
    settings = Settings(
        live_intelligence_rotation_state_path=str(tmp_path / "rotation.json"),
        live_intelligence_minimum_display_seconds=15,
        live_intelligence_maximum_exposure_seconds=50,
    )
    payload = {"ok": True, "signals": [
        signal("earth-a", "climate_earth_systems", "usgs"),
        signal("human-a", "humanitarian_conditions", "reliefweb"),
    ], "display": {}, "feed_state": {}, "boundaries": []}
    result = apply_rotation_policy(payload, settings, limit=2, record_history=True)
    assert result["rotation_schema"] == ROTATION_SCHEMA_VERSION
    assert result["rotation"]["anonymous_aggregate_history_only"] is True
    assert result["display"]["human_controlled_overrides_supported"] is True
    assert all(item["minimum_display_seconds"] == 15 for item in result["signals"])
    assert LiveIntelligenceRotationStore(settings).status()["history_record_count"] == 1


def test_rotation_policy_endpoint_is_public_and_bounded():
    response = TestClient(main.app).get("/public/live-intelligence/rotation-policy")
    assert response.status_code == 200
    payload = response.json()
    assert payload["schema"] == ROTATION_SCHEMA_VERSION
    assert payload["version"] == "3.11.0"
    assert payload["governance"]["human_approval_required_for_override"] is True
    assert payload["history"]["individual_user_tracking"] is False


def test_homepage_endpoint_applies_rotation_to_larger_candidate_pool(monkeypatch, tmp_path):
    captured = {}
    def fake_build(settings, **kwargs):
        captured.update(kwargs)
        return {"ok": True, "signals": [
            signal("earth-a", "climate_earth_systems", "usgs", score=95),
            signal("earth-b", "climate_earth_systems", "usgs", score=94),
            signal("human-a", "humanitarian_conditions", "reliefweb", score=80),
        ], "display": {}, "feed_state": {}, "boundaries": []}
    monkeypatch.setattr(main, "build_live_intelligence", fake_build)
    settings = Settings(live_intelligence_rotation_state_path=str(tmp_path / "rotation.json"))
    main.app.dependency_overrides[main.get_settings] = lambda: settings
    try:
        response = TestClient(main.app).get("/public/live-intelligence/homepage?limit=2")
    finally:
        main.app.dependency_overrides.pop(main.get_settings, None)
    assert response.status_code == 200
    payload = response.json()
    assert captured["limit"] == 24
    assert payload["count"] == 2
    assert payload["rotation"]["candidate_count"] == 3
    assert payload["signals"][0]["rotation_rank"] == 1
