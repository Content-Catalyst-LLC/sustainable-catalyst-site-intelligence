from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root_reports_v1181():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["version"] == "2.4.0"

def test_global_notice_removed():
    base = Path(__file__).resolve().parents[1] / "public_app"
    html = (base / "index.html").read_text()
    css = (base / "assets" / "app.css").read_text()
    js = (base / "assets" / "app.js").read_text()
    assert 'id="globalNotice"' not in html
    assert ".global-notice{" not in css
    assert 'qs("#dismissNotice")' not in js
