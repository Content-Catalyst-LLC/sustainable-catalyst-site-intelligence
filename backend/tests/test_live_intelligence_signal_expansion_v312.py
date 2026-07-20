from pathlib import Path

from app.config import get_settings
import app.live_intelligence_v313 as live

ROOT = Path(__file__).resolve().parents[2]


def _settings(**updates):
    settings = get_settings()
    return settings.model_copy(update=updates) if hasattr(settings, "model_copy") else settings


def _sig(signal_id, category, source, priority=50, status="current"):
    return live._signal(
        signal_id=signal_id,
        category=category,
        label=signal_id.upper(),
        value=f"VALUE {signal_id}",
        source=source,
        status=status,
        destination="https://example.org/",
        source_url="https://example.org/",
        updated_at="2026-07-20T12:00:00+00:00",
        priority=priority,
    )


def test_expanded_feed_defaults_to_sixteen_and_balances_categories(monkeypatch):
    monkeypatch.setattr(live, "_event_signals", lambda settings: ([
        _sig("eq.latest", "earth_systems", "USGS", 10),
        _sig("eq.strongest", "earth_systems", "USGS", 20),
        _sig("eq.count", "earth_systems", "USGS", 30),
        _sig("eq.extra", "earth_systems", "USGS", 40),
        _sig("human.latest", "human_systems", "ReliefWeb", 15),
        _sig("human.count", "human_systems", "ReliefWeb", 35),
    ], {"data_state": "test"}))
    monkeypatch.setattr(live, "_weather_signals", lambda settings: ([
        _sig("weather.alert", "earth_systems", "NOAA", 5, "attention"),
        _sig("weather.temp", "earth_systems", "NOAA", 45),
    ], {"data_state": "test"}))
    monkeypatch.setattr(live, "_nasa_power_signals", lambda settings: ([
        _sig("power.temp", "earth_systems", "NASA POWER", 60),
        _sig("power.rain", "earth_systems", "NASA POWER", 61),
        _sig("power.solar", "earth_systems", "NASA POWER", 62),
    ], {"data_state": "test"}))
    monkeypatch.setattr(live, "_openalex_signals", lambda settings: ([
        _sig("research.latest", "research", "OpenAlex", 25),
        _sig("research.count", "research", "OpenAlex", 55),
    ], {"data_state": "test"}))
    monkeypatch.setattr(live, "_world_bank_signals", lambda settings: ([
        _sig("development.population", "economy_resources", "World Bank", 50),
        _sig("development.renewable", "economy_resources", "World Bank", 52),
    ], {"data_state": "test"}))

    payload = live.build_live_intelligence(_settings(external_live=True))
    assert payload["schema"] == "sc-site-intelligence-live-intelligence/1.3"
    assert payload["count"] >= 13
    assert payload["feed_state"]["default_signal_limit"] == 16
    assert payload["feed_state"]["platform_signal_count"] == 1
    assert set(payload["feed_state"]["category_counts"]) >= {"earth_systems", "human_systems", "research", "economy_resources", "platform"}
    assert max(payload["feed_state"]["source_counts"].values()) <= 3
    assert "eq.extra" not in {item["signal_id"] for item in payload["signals"]}


def test_navigation_and_breadcrumb_theme_styles_are_not_overridden():
    php = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text()
    css = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.css").read_text()
    assert "Navigation surface" not in php
    assert "$classes[] = 'scsi-live-intelligence-parchment-navigation'" not in php
    assert "scsi-live-intelligence-parchment-navigation" not in css
    assert "theme navigation surfaces remain untouched" in css
    assert "live_intelligence_limit' => '16'" in php
    assert 'max="24"' in php


def test_periodic_indicator_boundary_and_theme_display_contract(monkeypatch):
    monkeypatch.setattr(live, "_event_signals", lambda settings: ([], {"data_state": "test"}))
    monkeypatch.setattr(live, "_weather_signals", lambda settings: ([], {"data_state": "test"}))
    monkeypatch.setattr(live, "_nasa_power_signals", lambda settings: ([], {"data_state": "test"}))
    monkeypatch.setattr(live, "_openalex_signals", lambda settings: ([], {"data_state": "test"}))
    monkeypatch.setattr(live, "_world_bank_signals", lambda settings: ([
        _sig("development.population", "economy_resources", "World Bank", 20),
    ], {"data_state": "test"}))
    payload = live.build_live_intelligence(_settings(external_live=True), limit=16)
    assert payload["display"]["theme_navigation_styles"] == "untouched"
    assert any("data year" in boundary.lower() for boundary in payload["boundaries"])
