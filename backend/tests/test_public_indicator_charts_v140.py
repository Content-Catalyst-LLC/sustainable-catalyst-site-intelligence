from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app
from app.public_indicator_charts import (
    public_indicator_chart_gallery,
    public_indicator_chart_visual_qa,
    public_indicator_dashboard,
    public_indicator_dashboard_directory,
)

client = TestClient(app)


def test_indicator_dashboard_directory_has_chart_ready_pages():
    data = public_indicator_dashboard_directory(Settings(version="2.9.0"))
    assert data["ok"] is True
    assert data["version_scope"] == "v2.9.0"
    assert data["recommended_shortcode"] == "[sc_public_indicator_dashboard_directory]"
    assert len(data["dashboards"]) >= 5
    assert all(item["chart_count"] >= 1 for item in data["dashboards"])


def test_sustainability_dashboard_has_chart_specs_without_private_payloads():
    data = public_indicator_dashboard("sustainability", Settings(version="2.9.0"))
    assert data["ok"] is True
    assert data["recommended_shortcode"] == "[sc_public_sustainability_indicator_dashboard]"
    assert data["chart_count"] >= 2
    assert all("chartType" in spec for spec in data["chart_specs"])
    assert "API keys" in data["hidden"]
    assert "raw upstream" not in str(data).lower()


def test_indicator_chart_gallery_and_visual_qa():
    settings = Settings(version="2.9.0")
    gallery = public_indicator_chart_gallery(settings)
    qa = public_indicator_chart_visual_qa(settings)
    assert gallery["recommended_shortcode"] == "[sc_public_indicator_chart_gallery]"
    assert gallery["chart_count"] >= 7
    assert qa["score"] == 100
    assert any(check["id"] == "wordpress_fallback" for check in qa["checks"])


def test_public_indicator_chart_endpoints():
    endpoints = [
        "/public/indicator-dashboards",
        "/public/indicator-dashboards/sustainability",
        "/public/indicator-dashboards/development",
        "/public/indicator-dashboards/source-health",
        "/public/indicator-dashboards/research",
        "/public/indicator-dashboards/repository",
        "/public/indicator-dashboards/charts",
        "/public/indicator-dashboards/visual-qa",
    ]
    for endpoint in endpoints:
        response = client.get(endpoint)
        assert response.status_code == 200, endpoint
        assert response.json()["ok"] is True
