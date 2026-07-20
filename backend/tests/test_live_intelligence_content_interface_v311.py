from pathlib import Path

from app.config import get_settings
import app.live_intelligence_v313 as live

ROOT = Path(__file__).resolve().parents[2]


def _settings(**updates):
    settings = get_settings()
    if hasattr(settings, "model_copy"):
        return settings.model_copy(update=updates)
    for key, value in updates.items():
        setattr(settings, key, value)
    return settings


def _events_payload():
    return {
        "generated_at": "2026-07-20T15:00:00+00:00",
        "delivery_state": "live",
        "source_states": {"usgs": "live", "nasa-eonet": "live", "reliefweb": "live"},
        "events": [
            {
                "id": "eq-1", "source": "usgs", "source_name": "USGS Earthquake Hazards Program",
                "source_url": "https://earthquake.usgs.gov/example", "category": "earthquake",
                "title": "20 km south of Example City", "summary": "Reviewed earthquake record.",
                "magnitude": 5.8, "observed_at": "2026-07-20T14:00:00+00:00",
                "updated_at": "2026-07-20T14:05:00+00:00", "data_state": "live", "metadata": {},
            },
            {
                "id": "fire-1", "source": "nasa-eonet", "source_name": "NASA EONET",
                "source_url": "https://eonet.gsfc.nasa.gov/example", "category": "wildfire",
                "title": "Wildfire activity in Example Region", "summary": "Open natural event.",
                "observed_at": "2026-07-20T13:00:00+00:00", "updated_at": "2026-07-20T13:00:00+00:00",
                "data_state": "live", "metadata": {},
            },
            {
                "id": "rw-1", "source": "reliefweb", "source_name": "ReliefWeb",
                "source_url": "https://reliefweb.int/example", "category": "humanitarian",
                "title": "Humanitarian situation report", "summary": "Published humanitarian report.",
                "observed_at": "2026-07-20T12:00:00+00:00", "updated_at": "2026-07-20T12:10:00+00:00",
                "data_state": "live", "metadata": {},
            },
            {
                "id": "demo-1", "source": "local-fallback", "source_name": "Demo",
                "category": "earthquake", "title": "Demonstration earthquake record",
                "observed_at": "2026-07-20T11:00:00+00:00", "updated_at": "2026-07-20T11:00:00+00:00",
                "data_state": "fallback", "metadata": {"fabricated_for_demo": True},
            },
        ],
    }


def _weather_payload():
    return {
        "source": "NOAA / National Weather Service",
        "live": True,
        "summary": "NOAA/NWS live forecast and alert context.",
        "cache": {"status": "miss"},
        "indicators": [
            {"label": "Active weather alerts", "value": 2, "unit": "alerts", "interpretation": "Active public alerts."},
            {"label": "Forecast temperature context", "value": 27.5, "unit": "°C", "interpretation": "Short-term temperature context."},
        ],
    }


def test_feed_prioritizes_public_interest_signals(monkeypatch):
    monkeypatch.setattr(live, "unified_events", lambda **kwargs: _events_payload())
    monkeypatch.setattr(live.AdvancedExternalDataHub, "noaa_weather_climate", lambda self: _weather_payload())
    monkeypatch.setattr(live, "_nasa_power_signals", lambda settings: ([], {"data_state": "test"}))
    monkeypatch.setattr(live, "_openalex_signals", lambda settings: ([], {"data_state": "test"}))
    monkeypatch.setattr(live, "_world_bank_signals", lambda settings: ([], {"data_state": "test"}))
    payload = live.build_live_intelligence(_settings(external_live=True), limit=8)
    labels = [item["label"] for item in payload["signals"]]
    values = " ".join(item["value"] for item in payload["signals"])
    assert "LOCAL WEATHER ALERTS" in labels
    assert "LATEST EARTHQUAKE" in labels
    assert "OPEN NATURAL EVENT" in labels
    assert "LATEST HUMANITARIAN REPORT" in labels
    assert "Demonstration" not in values
    assert payload["feed_state"]["useful_signal_count"] >= 6
    assert payload["feed_state"]["platform_signal_count"] <= 1


def test_sample_weather_values_are_suppressed(monkeypatch):
    monkeypatch.setattr(live, "unified_events", lambda **kwargs: _events_payload())
    monkeypatch.setattr(live.AdvancedExternalDataHub, "noaa_weather_climate", lambda self: {
        "source": "sample", "live": False, "cache": {"status": "fallback"},
        "indicators": [{"label": "Active weather alerts", "value": 99, "unit": "alerts"}],
    })
    monkeypatch.setattr(live, "_nasa_power_signals", lambda settings: ([], {"data_state": "test"}))
    monkeypatch.setattr(live, "_openalex_signals", lambda settings: ([], {"data_state": "test"}))
    monkeypatch.setattr(live, "_world_bank_signals", lambda settings: ([], {"data_state": "test"}))
    payload = live.build_live_intelligence(_settings(external_live=True), limit=20)
    assert all(item["signal_id"] != "weather.active-alerts" for item in payload["signals"])


def test_interface_contract_contains_hover_pause_and_breadcrumb_placement():
    css = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.css").read_text()
    js = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js").read_text()
    php = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text()
    assert "is-hover-paused" in css and "animation-play-state:paused!important" in css
    assert "mouseenter" in js and "mouseleave" in js and "focusin" in js
    assert "live_intelligence_placement" in php
    assert "below_breadcrumb" in php and "astra_get_option('breadcrumb-position')" in php
    assert "scsi-live-intelligence-parchment-navigation" not in css
    assert "Navigation surface" not in php
    assert "$classes[] = 'scsi-live-intelligence-parchment-navigation'" not in php
