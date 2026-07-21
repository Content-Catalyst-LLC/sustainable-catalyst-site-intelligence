from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app import main
from app.live_intelligence_gateway_v370 import (
    DEFAULT_HOMEPAGE_SIGNAL_LIMIT,
    GATEWAY_SCHEMA_VERSION,
    apply_gateway_policy,
    enrich_gateway_signal,
    homepage_gateway_policy,
)


def sample_signal(**overrides):
    signal = {
        "signal_id": "event.test-gateway",
        "category": "earth_systems",
        "feed_id": "usgs_earthquakes",
        "label": "EARTHQUAKE ACTIVITY",
        "value": "M5.2 public event",
        "unit": "",
        "status": "current",
        "source_name": "USGS Earthquake Hazards Program",
        "source_url": "https://earthquake.usgs.gov/",
        "destination_url": "/platform/site-intelligence/?view=earth",
        "context_view_url": "/public/live-intelligence/signals/event.test-gateway/view",
        "evidence_url": "/public/live-intelligence/signals/event.test-gateway/evidence",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "coordinates": [-122.3, 37.8],
        "country": "United States",
        "country_code": "US",
        "validation_state": "valid",
        "selection_score": 210,
    }
    signal.update(overrides)
    return signal


def test_gateway_signal_contract_and_destination_hierarchy():
    item = enrich_gateway_signal(sample_signal())
    assert item["signal_family"] == "climate_earth_systems"
    assert item["family_label"] == "Climate & Earth Systems"
    assert item["geography"]["scope"] == "country"
    assert item["geography"]["map_url"].startswith("https://www.openstreetmap.org/")
    assert item["primary_destination"]["type"] == "signal_context"
    types = [entry["type"] for entry in item["secondary_destinations"]]
    assert types[:3] == ["site_intelligence_workspace", "evidence_record", "map_context"]
    assert "decision_studio" in types and "primary_source" in types
    assert item["homepage_eligible"] is True
    assert item["formatted_value"] == "M5.2 public event"


def test_gateway_payload_summarizes_families_geography_and_destinations():
    payload = apply_gateway_policy({
        "ok": True,
        "signals": [sample_signal(), sample_signal(signal_id="platform.status", category="platform", feed_id="platform_status", coordinates=[])],
        "display": {},
        "boundaries": [],
    }, surface="homepage")
    assert payload["gateway_schema"] == GATEWAY_SCHEMA_VERSION
    assert payload["gateway"]["surface"] == "homepage"
    assert payload["gateway"]["family_counts"]["climate_earth_systems"] == 1
    assert payload["gateway"]["family_counts"]["platform_operations"] == 1
    assert payload["display"]["recommended_homepage_position"] == "directly_below_hero"
    assert payload["display"]["full_application_boot_required"] is False


def test_gateway_policy_is_public_and_bounded():
    policy = homepage_gateway_policy()
    assert policy["version"] == "3.13.0"
    assert policy["default_signal_limit"] == DEFAULT_HOMEPAGE_SIGNAL_LIMIT == 8
    assert policy["maximum_signal_limit"] == 12
    assert policy["sticky"] is False
    assert len(policy["signal_families"]) == 8
    assert policy["destination_hierarchy"][0]["type"] == "signal_context"


def test_gateway_policy_endpoint():
    response = TestClient(main.app).get("/public/live-intelligence/gateway-policy")
    assert response.status_code == 200
    payload = response.json()
    assert payload["schema"] == GATEWAY_SCHEMA_VERSION
    assert payload["version"] == "3.13.0"


def test_homepage_endpoint_uses_gateway_surface(monkeypatch):
    monkeypatch.setattr(main, "build_live_intelligence", lambda *args, **kwargs: {
        "ok": True,
        "version": "3.13.0",
        "signals": [sample_signal()],
        "display": {},
        "boundaries": [],
    })
    response = TestClient(main.app).get("/public/live-intelligence/homepage")
    assert response.status_code == 200
    payload = response.json()
    assert payload["gateway"]["surface"] == "homepage"
    assert payload["count"] == 1
    assert payload["signals"][0]["primary_destination"]["type"] == "signal_context"
