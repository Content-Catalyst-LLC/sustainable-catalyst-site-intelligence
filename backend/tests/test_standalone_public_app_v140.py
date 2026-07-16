from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_standalone_app_serves():
    response = client.get("/app/")
    assert response.status_code == 200
    assert "Site Intelligence" in response.text
    assert "Climate and Human Vulnerability" in response.text

def test_standalone_assets_exist():
    base = Path(__file__).resolve().parents[1] / "public_app"
    assert (base / "index.html").exists()
    assert (base / "assets" / "app.css").exists()
    assert (base / "assets" / "app.js").exists()

def test_root_reports_v1140():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["version"] == "2.17.0"
