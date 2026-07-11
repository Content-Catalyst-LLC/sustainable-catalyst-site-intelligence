from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root_reports_v1161():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["version"] == "1.18.3"

def test_earth_diagnostics():
    response = client.get("/public/earth-observation/diagnostics")
    assert response.status_code == 200
    payload = response.json()
    assert payload["version"] == "1.18.3"
    assert payload["interaction_checks"]["broken_tile_state"] == "ready"
    assert payload["layer_count"] >= 8

def test_reliability_assets_present():
    base = Path(__file__).resolve().parents[1] / "public_app"
    assert "earthUnavailable" in (base / "index.html").read_text()
    assert "earth-status" in (base / "assets" / "app.css").read_text()
    js = (base / "assets" / "app.js").read_text()
    assert "bindTileReliability" in js
    assert "stopEarthPlayback" in js
    assert "validateEarthDates" in js
