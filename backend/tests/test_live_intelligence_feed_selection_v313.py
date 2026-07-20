from pathlib import Path

from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app
import app.live_intelligence_v313 as live

ROOT = Path(__file__).resolve().parents[2]


def _settings(**updates):
    settings = get_settings()
    return settings.model_copy(update=updates) if hasattr(settings, "model_copy") else settings


def _sig(signal_id, category, source, priority=50):
    return live._signal(
        signal_id=signal_id,
        category=category,
        label=signal_id.upper(),
        value=f"VALUE {signal_id}",
        source=source,
        status="current",
        destination="https://example.org/",
        source_url="https://example.org/",
        updated_at="2026-07-20T12:00:00+00:00",
        priority=priority,
    )


def _patch_collectors(monkeypatch):
    monkeypatch.setattr(live, "_event_signals", lambda settings: ([
        _sig("events.earthquakes-14d", "earth_systems", "USGS Earthquake Hazards Program", 10),
        _sig("events.natural-open", "earth_systems", "NASA EONET", 20),
        _sig("events.humanitarian-14d", "human_systems", "ReliefWeb", 30),
    ], {"data_state": "test"}))
    monkeypatch.setattr(live, "_weather_signals", lambda settings: ([
        _sig("weather.active-alerts", "earth_systems", "NOAA / National Weather Service", 5),
        _sig("weather.forecast-temperature", "earth_systems", "NOAA / National Weather Service", 6),
    ], {"data_state": "test"}))
    monkeypatch.setattr(live, "_nasa_power_signals", lambda settings: ([
        _sig("nasa-power.t2m", "earth_systems", "NASA POWER", 40),
    ], {"data_state": "test"}))
    monkeypatch.setattr(live, "_openalex_signals", lambda settings: ([
        _sig("research.openalex.latest", "research", "OpenAlex", 50),
        _sig("research.openalex.count", "research", "OpenAlex", 51),
    ], {"data_state": "test"}))
    monkeypatch.setattr(live, "_world_bank_signals", lambda settings: ([
        _sig("world-bank.sp.pop.grow", "economy_resources", "World Bank", 60),
    ], {"data_state": "test"}))


def test_named_feed_selection_and_exclusion(monkeypatch):
    _patch_collectors(monkeypatch)
    payload = live.build_live_intelligence(
        _settings(external_live=True),
        feeds="usgs,openalex,platform_status",
        exclude="platform",
        limit=16,
    )
    assert payload["schema"] == "sc-site-intelligence-live-intelligence/1.3"
    assert {item["feed_id"] for item in payload["signals"]} == {"usgs_earthquakes", "openalex"}
    assert payload["feed_state"]["active_feeds"] == ["usgs_earthquakes", "openalex"]
    assert payload["feed_state"]["excluded_feeds"] == ["platform_status"]


def test_per_source_limit_is_configurable(monkeypatch):
    _patch_collectors(monkeypatch)
    payload = live.build_live_intelligence(
        _settings(external_live=True),
        feeds="noaa_nws,openalex",
        limit=16,
        max_per_source=1,
    )
    assert payload["count"] == 2
    assert max(payload["feed_state"]["source_counts"].values()) == 1
    assert payload["feed_state"]["maximum_signals_per_source"] == 1


def test_public_endpoint_accepts_feed_filters():
    client = TestClient(app)
    response = client.get("/public/live-intelligence?feeds=platform_status&limit=4&max_per_source=1")
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 1
    assert payload["signals"][0]["feed_id"] == "platform_status"
    assert payload["feeds"]


def test_wordpress_controls_and_placement_fallback_contract():
    php = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text()
    js = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js").read_text()
    css = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.css").read_text()
    for marker in [
        "live_intelligence_feeds", "live_intelligence_max_per_source",
        "live_intelligence_shortcode_overrides", "Displayed feeds",
        "inject_live_intelligence_content_fallback", "$this->live_intelligence_rendered",
        "data-feeds", "data-exclude", "data-max-per-source",
    ]:
        assert marker in php
    assert "max_per_source" in js and "URLSearchParams" in js
    assert "scsi-live-intelligence-parchment-navigation" not in css
    assert "Navigation surface" not in php
