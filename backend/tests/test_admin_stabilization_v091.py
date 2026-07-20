from fastapi.testclient import TestClient

from app.main import app
from app.admin_control import shortcode_catalog


def test_v091_admin_stabilization_endpoints():
    client = TestClient(app)
    for path in [
        "/admin/status",
        "/admin/connection-check",
        "/admin/public-readiness-check",
        "/admin/diagnostic-summary",
    ]:
        response = client.get(path)
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["version"] == "3.1.4"


def test_v091_shortcode_catalog_includes_admin_diagnostics():
    data = shortcode_catalog()
    values = {item["shortcode"] for item in data["shortcodes"]}
    assert "[sc_site_intelligence_diagnostic_summary]" in values
    assert "[sc_site_intelligence_connection_check]" in values
