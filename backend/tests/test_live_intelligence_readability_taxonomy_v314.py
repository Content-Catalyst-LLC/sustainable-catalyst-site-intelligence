from pathlib import Path

from app.config import get_settings
import app.live_intelligence_v314 as live

ROOT = Path(__file__).resolve().parents[2]


def _settings(**updates):
    settings = get_settings()
    return settings.model_copy(update=updates) if hasattr(settings, "model_copy") else settings


def test_v314_taxonomy_and_readability_contract():
    payload = live.build_live_intelligence(
        _settings(external_live=False),
        feeds="platform_status",
        limit=4,
    )
    assert payload["version"] == "3.9.0"
    assert payload["schema"] == "sc-site-intelligence-live-intelligence/1.4"
    assert payload["display"]["readability_controls_supported"] is True
    assert payload["display"]["category_labels"]["economy_resources"] == "Economy, Energy & Resources"
    assert payload["display"]["default_desktop_cycle_seconds"] == 30
    assert payload["display"]["default_mobile_cycle_seconds"] == 36
    assert payload["signals"][0]["source_short_name"] == "Sustainable Catalyst"


def test_source_short_names_are_attached_to_signals():
    signal = live._signal(
        signal_id="weather.test",
        category="earth_systems",
        label="WEATHER ALERT",
        value="A verified weather alert",
        source="NOAA / National Weather Service",
        status="current",
        destination="https://example.org/",
        source_url="https://example.org/",
        updated_at="2026-07-20T12:00:00+00:00",
    )
    assert signal["source_short_name"] == "NOAA/NWS"


def test_wordpress_readability_and_taxonomy_controls():
    php = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text()
    js = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js").read_text()
    css = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.css").read_text()
    for marker in [
        "live_intelligence_speed_preset",
        "live_intelligence_mobile_speed",
        "live_intelligence_spacing",
        "live_intelligence_text_limit",
        "live_intelligence_compact_sources",
        "Economy, Energy & Resources",
        "Restore readability defaults",
        "scsi-live-admin-preview",
        "data-category-labels",
        "data-text-limit",
        "data-compact-sources",
    ]:
        assert marker in php
    assert "source_short_name" in js
    assert "categoryLabels" in js
    assert "shorten(fullValue, textLimit)" in js
    assert "--scsi-live-mobile-duration" in css
    assert "scsi-live-intelligence--spacing-compact" in css
    assert "text-overflow:ellipsis" in css


def test_theme_surfaces_remain_unmodified():
    php = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text()
    css = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.css").read_text()
    assert "[live_intelligence_parchment_navigation]" not in php
    assert "scsi-live-intelligence-parchment-navigation" not in css
    assert "theme navigation surfaces remain untouched" in css
