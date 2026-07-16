from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root_reports_v1182():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["version"] == "2.24.0"

def test_wordpress_loader_cleanup_present():
    base = Path(__file__).resolve().parents[2] / "wordpress-plugin" / "sustainable-catalyst-site-intelligence"
    js = (base / "assets" / "sc-site-intelligence.js").read_text()
    css = (base / "assets" / "sc-site-intelligence.css").read_text()
    assert "function setPublicConnectorLoading" in js
    assert ".finally(function () { finishPublicConnectorLoading(root); });" in js
    assert "loadingShell.remove();" in js
    assert ".scsi-loading-shell[hidden]" in css
    assert "No validated public value is currently available." in js
