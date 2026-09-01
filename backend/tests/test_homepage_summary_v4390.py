from pathlib import Path

from fastapi.testclient import TestClient

from app.homepage_summary_v4390 import SCHEMA_VERSION, build_homepage_summary
from app.main import app


ROOT = Path(__file__).resolve().parents[2]
CLIENT = TestClient(app)


def _live_payload():
    return {
        "generated_at": "2026-09-01T12:00:00+00:00",
        "gateway": {"represented_source_count": 1},
        "signals": [{
            "signal_id": "usgs:test",
            "family_label": "Earth Systems",
            "short_label": "Example public signal",
            "formatted_value": "M 4.2",
            "source_name": "U.S. Geological Survey",
            "freshness_state": "fresh",
            "primary_destination": {"url": "/public/live-intelligence/signals/usgs:test/view"},
        }],
    }


def test_homepage_summary_uses_registry_counts_and_bounded_live_highlights():
    payload = build_homepage_summary(_live_payload())
    metrics = {metric["id"]: metric for metric in payload["metrics"]}
    assert payload["ok"] is True and payload["schema"] == SCHEMA_VERSION
    assert metrics["country_profiles"]["value"] == 172
    assert metrics["registered_sources"]["value"] == 8
    assert metrics["current_signals"]["value"] == 1
    assert payload["highlights"][0]["source"] == "U.S. Geological Survey"


def test_homepage_summary_empty_state_does_not_invent_live_signals():
    payload = build_homepage_summary({"signals": [], "generated_at": "2026-09-01T12:00:00+00:00"})
    assert payload["status"]["state"] == "online"
    assert payload["status"]["delivery_state"] == "available"
    assert payload["highlights"] == []
    assert next(metric for metric in payload["metrics"] if metric["id"] == "current_signals")["value"] == 0


def test_homepage_summary_exposes_three_valid_application_entry_points():
    payload = build_homepage_summary(_live_payload())
    assert [entry["id"] for entry in payload["entry_points"]] == ["world", "earth", "ocean_space"]
    assert all(entry["href"].startswith("/app/?view=") for entry in payload["entry_points"])


def test_homepage_summary_routes_are_public_and_alias_the_v1_contract():
    paths = {route.path for route in app.routes}
    assert "/public/site-intelligence/summary" in paths
    assert "/v1/public/site-intelligence/summary" in paths


def test_wordpress_shortcode_is_lightweight_and_does_not_embed_an_iframe():
    plugin = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text()
    js = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js").read_text()
    css = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.css").read_text()
    assert "add_shortcode('sc_site_intelligence_home'" in plugin
    method = plugin.split("public function site_intelligence_home_shortcode", 1)[1].split("public function", 1)[0]
    assert "<iframe" not in method
    assert "data-scsi-home-summary" in method
    assert "setupSiteIntelligenceHomeSummary" in js
    assert ".scsi-home-summary__metrics" in css
