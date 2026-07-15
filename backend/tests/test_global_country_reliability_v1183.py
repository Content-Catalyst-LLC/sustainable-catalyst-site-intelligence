from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app import live_country_intelligence as countries
from app.country_cache import CountryJsonCache
from app.unified_live_events import _country_match, unified_events

client = TestClient(app)

FAKE_CATALOG = {
    "EGY": {"name": "Egypt, Arab Rep.", "iso2": "EG", "region": " Middle East & North Africa  ", "capital": "Cairo", "latitude": 26.8, "longitude": 30.8},
    "KOR": {"name": "Korea, Rep.", "iso2": "KR", "region": "East Asia & Pacific", "capital": "Seoul", "latitude": 36.5, "longitude": 127.8},
    "KEN": {"name": "Kenya", "iso2": "KE", "region": "Sub-Saharan Africa", "capital": "Nairobi", "latitude": 0.0, "longitude": 37.0},
}


def test_build_info_matches_release_and_plugin_expectation():
    response = client.get("/public/build-info")
    assert response.status_code == 200
    payload = response.json()
    assert payload["backend_version"] == "2.1.0"
    assert payload["expected_wordpress_plugin_version"] == "2.1.0"
    assert payload["api_schema_version"] == "2.0"


@patch("app.live_country_intelligence._catalog_from_world_bank", return_value=FAKE_CATALOG)
def test_catalog_preserves_source_name_and_normalizes_public_display(mock_catalog):
    countries._COUNTRY_CATALOG_CACHE = None
    payload = countries.country_catalog(force_refresh=True)
    egypt = next(item for item in payload["countries"] if item["code"] == "EGY")
    korea = next(item for item in payload["countries"] if item["code"] == "KOR")
    assert egypt["name"] == "Egypt"
    assert egypt["source_name"] == "Egypt, Arab Rep."
    assert egypt["region"] == "Middle East & North Africa"
    assert "Egypt, Arab Rep." in egypt["alternate_names"]
    assert korea["name"] == "South Korea"


@patch("app.live_country_intelligence._catalog_from_world_bank", return_value=FAKE_CATALOG)
def test_country_search_uses_source_names_and_aliases(mock_catalog):
    countries._COUNTRY_CATALOG_CACHE = None
    countries.country_catalog(force_refresh=True)
    assert countries.search_countries("Arab Rep.")["countries"][0]["code"] == "EGY"
    assert countries.search_countries("Republic of Korea")["countries"][0]["code"] == "KOR"


def test_json_last_known_good_cache_distinguishes_fresh_and_stale(tmp_path):
    cache = CountryJsonCache(tmp_path / "country-cache.json")
    cache.set("test", {"value": 0})
    fresh = cache.get("test", fresh_seconds=60, stale_seconds=120)
    assert fresh is not None
    assert fresh.state == "cached"
    assert fresh.value["value"] == 0
    stale = cache.get("test", fresh_seconds=-1, stale_seconds=120)
    assert stale is not None
    assert stale.state == "stale"
    assert stale.stale is True


def test_invalid_country_diagnostics_returns_structured_fallback():
    response = client.get("/public/country/ZZZ/diagnostics")
    assert response.status_code == 404
    detail = response.json()["detail"]
    assert detail["code"] == "unsupported_country"
    assert detail["fallback_country"] == "KEN"


def test_country_match_retains_method_confidence_and_evidence():
    title = _country_match("M 5.0 - western Kenya", [36.8, 0.2])
    assert title["country_code"] == "KEN"
    assert title["country_match_method"] in {"title-country-name", "coordinate-bounding-box"}
    assert title["country_match_confidence"] > 0
    assert title["country_match_evidence"]


@patch("app.unified_live_events._usgs_events", return_value=[])
@patch("app.unified_live_events._eonet_events", return_value=[])
@patch("app.unified_live_events._reliefweb_reports", return_value=[])
def test_country_diagnostics_can_request_events_without_demo_fallback(reliefweb, eonet, usgs):
    payload = unified_events(country_code="FRA", allow_fallback=False)
    assert payload["count"] == 0
    assert payload["data_state"] == "unavailable"


def test_frontend_contains_abortable_country_requests_and_debounce():
    js = (Path(__file__).resolve().parents[1] / "public_app" / "assets" / "app.js").read_text()
    assert "AbortController" in js
    assert "requestSequence" in js
    assert "searchTimer" in js
    assert "Unsupported country code" in js
    assert "overviewMarker" in js
    assert 'if(route==="country")' in js
    assert 'await openGlobalCountryExplorer()' in js
    assert 'if(route==="events")' in js
    assert 'await openEventStudio()' in js


def test_wordpress_plugin_has_backend_compatibility_notice():
    plugin = Path(__file__).resolve().parents[2] / "wordpress-plugin" / "sustainable-catalyst-site-intelligence" / "sustainable-catalyst-site-intelligence.php"
    text = plugin.read_text()
    assert "Version: 2.1.0" in text
    assert "backend_version_notice" in text
    assert "/public/build-info" in text
