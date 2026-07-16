from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app import live_country_intelligence as countries

client = TestClient(app)

FAKE_CATALOG = {
    "KEN": {"name": "Kenya", "iso2": "KE", "region": "Sub-Saharan Africa", "capital": "Nairobi", "latitude": 0.0, "longitude": 37.0},
    "GHA": {"name": "Ghana", "iso2": "GH", "region": "Sub-Saharan Africa", "capital": "Accra", "latitude": 7.9, "longitude": -1.0},
    "FRA": {"name": "France", "iso2": "FR", "region": "Europe & Central Asia", "capital": "Paris", "latitude": 46.2, "longitude": 2.2},
}

def test_root_reports_v1180():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["version"] == "2.12.1"

@patch("app.live_country_intelligence._catalog_from_world_bank", return_value=FAKE_CATALOG)
def test_country_catalog_is_searchable(mock_catalog):
    countries._COUNTRY_CATALOG_CACHE = None
    payload = countries.country_catalog(force_refresh=True)
    assert payload["country_count"] >= 3
    search = countries.search_countries("fra")
    assert any(item["code"] == "FRA" for item in search["countries"])

@patch("app.live_country_intelligence._catalog_from_world_bank", return_value=FAKE_CATALOG)
def test_regions_are_grouped(mock_catalog):
    countries._COUNTRY_CATALOG_CACHE = None
    payload = countries.country_regions()
    assert any(item["name"] == "Sub-Saharan Africa" for item in payload["regions"])

def test_country_catalog_endpoints():
    response = client.get("/public/countries/search?q=Kenya")
    assert response.status_code == 200
    assert "countries" in response.json()

    regions = client.get("/public/countries/regions")
    assert regions.status_code == 200
    assert "regions" in regions.json()

def test_global_country_assets_present():
    base = Path(__file__).resolve().parents[1] / "public_app"
    html = (base / "index.html").read_text()
    css = (base / "assets" / "app.css").read_text()
    js = (base / "assets" / "app.js").read_text()
    assert "globalCountryExplorer" in html
    assert "global-country-explorer" in css
    assert "openGlobalCountryExplorer" in js
    assert "searchGlobalCountries" in js
