from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root_reports_v1160():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["version"] == "3.16.0"

def test_earth_observation_overview():
    response = client.get("/public/earth-observation")
    assert response.status_code == 200
    payload = response.json()
    assert payload["title"] == "Earth Observation Studio"
    assert payload["layer_count"] >= 8

def test_earth_layers_have_metadata():
    response = client.get("/public/earth-observation/layers")
    assert response.status_code == 200
    layers = response.json()["layers"]
    assert len(layers) >= 8
    assert all("source" in item for item in layers)
    assert all("temporal_resolution" in item for item in layers)
    assert all("limits" in item for item in layers)

def test_comparison_resolves_dates_and_tiles():
    response = client.get("/public/earth-observation/compare?layer=true-color&date_a=2026-06-01&date_b=2026-06-08")
    assert response.status_code == 200
    payload = response.json()
    assert payload["left"]["date"] == "2026-06-01"
    assert payload["right"]["date"] == "2026-06-08"
    assert "{time}" not in payload["left"]["tile_url"]

def test_timeline_has_frames():
    response = client.get("/public/earth-observation/timeline?layer=true-color&days=7")
    assert response.status_code == 200
    assert response.json()["frame_count"] == 7

def test_earth_app_assets_present():
    base = Path(__file__).resolve().parents[1] / "public_app"
    html = (base / "index.html").read_text()
    css = (base / "assets" / "app.css").read_text()
    js = (base / "assets" / "app.js").read_text()
    assert "earthStudio" in html
    assert "earth-compare-stage" in css
    assert "openEarthStudio" in js
    assert "exportEarthPNG" in js
