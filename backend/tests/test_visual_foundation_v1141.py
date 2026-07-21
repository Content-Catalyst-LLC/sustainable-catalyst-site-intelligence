from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root_reports_v1141():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["version"] == "3.14.0"

def test_visual_system_assets_present():
    base = Path(__file__).resolve().parents[1] / "public_app"
    html = (base / "index.html").read_text()
    css = (base / "assets" / "app.css").read_text()
    js = (base / "assets" / "app.js").read_text()
    assert "orbital-glow" in html
    assert "cinematic-map" in html
    assert "skeleton-stack" in html
    assert "Immersive visual foundation" in css
    assert "markerPulse" in js
    assert "prefers-reduced-motion" in css
