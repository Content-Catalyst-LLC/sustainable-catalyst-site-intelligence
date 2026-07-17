from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root_reports_v1152():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["version"] == "3.0.0"

def test_public_launch_status():
    response = client.get("/public/launch-status")
    assert response.status_code == 200
    payload = response.json()
    assert payload["release_channel"] == "public-beta"
    assert payload["platform_core_required_for_public_app"] is False
    assert payload["launch_checks"]["responsive_embed"] == "ready"

def test_launch_assets_present():
    base = Path(__file__).resolve().parents[1] / "public_app"
    assert "launchScreen" in (base / "index.html").read_text()
    assert "apiWithRetry" in (base / "assets" / "app.js").read_text()
    assert "launch-screen" in (base / "assets" / "app.css").read_text()
