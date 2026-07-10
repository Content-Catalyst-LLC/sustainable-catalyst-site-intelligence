from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app
from app.public_source_briefs_exports import (
    public_dashboard_export,
    public_dashboard_export_manifest,
    public_dashboard_export_visual_qa,
    public_source_aware_brief,
    public_source_aware_brief_directory,
)

client = TestClient(app)


def test_source_aware_brief_directory_is_public_safe():
    data = public_source_aware_brief_directory(Settings(version="1.15.0"))
    assert data["ok"] is True
    assert data["version_scope"] == "v1.15.0"
    assert data["recommended_shortcode"] == "[sc_public_source_aware_brief_directory]"
    assert len(data["briefs"]) == 3
    assert "upstream response bodies" in data["hidden"]


def test_source_aware_brief_has_citations_and_boundaries():
    data = public_source_aware_brief("indicator", Settings(version="1.15.0"))
    assert data["ok"] is True
    assert data["recommended_shortcode"] == "[sc_public_indicator_source_brief]"
    assert data["source_citations"]
    assert "professional advice" in data["boundary_note"]
    assert "secret" not in str(data).lower()


def test_dashboard_export_manifest_and_bundle_payloads():
    settings = Settings(version="1.15.0")
    manifest = public_dashboard_export_manifest(settings)
    export = public_dashboard_export("source-health", settings)
    assert manifest["recommended_shortcode"] == "[sc_public_dashboard_export_manifest]"
    assert len(manifest["exports"]) == 3
    assert export["recommended_shortcode"] == "[sc_public_source_health_export]"
    assert "markdown" in export["export_bundle"]
    assert export["export_bundle"]["csv_preview"]
    assert "raw upstream" not in str(export).lower()


def test_dashboard_export_visual_qa():
    data = public_dashboard_export_visual_qa(Settings(version="1.15.0"))
    assert data["ok"] is True
    assert data["score"] == 100
    assert data["recommended_shortcode"] == "[sc_public_dashboard_export_visual_qa]"
    assert any(check["id"] == "source_citations_present" for check in data["checks"])


def test_public_source_aware_and_export_endpoints():
    endpoints = [
        "/public/source-aware-briefs",
        "/public/source-aware-briefs/site-intelligence",
        "/public/source-aware-briefs/indicator",
        "/public/source-aware-briefs/source-health",
        "/public/dashboard-exports",
        "/public/dashboard-exports/manifest",
        "/public/dashboard-exports/site-intelligence",
        "/public/dashboard-exports/indicator",
        "/public/dashboard-exports/source-health",
        "/public/dashboard-exports/visual-qa",
    ]
    for endpoint in endpoints:
        response = client.get(endpoint)
        assert response.status_code == 200, endpoint
        assert response.json()["ok"] is True
