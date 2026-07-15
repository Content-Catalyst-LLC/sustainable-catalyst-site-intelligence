from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.live_country_intelligence import country_indicators, country_profile

client = TestClient(app)

def fake_series(iso2, indicator_id, per_page=30):
    return [
        {"year": 2021, "value": 10.0, "unit": "", "source_note": indicator_id},
        {"year": 2022, "value": 12.0, "unit": "", "source_note": indicator_id},
        {"year": 2023, "value": 14.0, "unit": "", "source_note": indicator_id},
    ]

def test_root_reports_v1150():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["version"] == "2.3.0"

@patch("app.live_country_intelligence._world_bank_series", side_effect=fake_series)
def test_country_indicators_live(mocked):
    from app.live_country_intelligence import _live_indicator_bundle
    _live_indicator_bundle.cache_clear()
    result = country_indicators("KEN")
    assert result["ok"] is True
    assert result["data_state"] in {"live", "cached"}
    assert result["available_indicator_count"] == 8
    assert result["indicators"][0]["latest"]["year"] == 2023

@patch("app.live_country_intelligence._world_bank_series", side_effect=fake_series)
def test_country_profile_has_highlights(mocked):
    from app.live_country_intelligence import _live_indicator_bundle
    _live_indicator_bundle.cache_clear()
    result = country_profile("GHA")
    assert result["country"]["name"] == "Ghana"
    assert len(result["highlights"]) == 6
    assert result["trends_endpoint"].endswith("/trends")

def test_unsupported_country_returns_404():
    response = client.get("/public/country/ZZZ")
    assert response.status_code == 404

def test_country_app_assets_present():
    from pathlib import Path
    base = Path(__file__).resolve().parents[1] / "public_app"
    assert "countryIndicatorGrid" in (base / "index.html").read_text()
    assert "loadLiveCountry" in (base / "assets" / "app.js").read_text()
    assert "country-indicator-grid" in (base / "assets" / "app.css").read_text()
