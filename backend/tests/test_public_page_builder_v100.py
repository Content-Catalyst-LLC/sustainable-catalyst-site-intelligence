from fastapi.testclient import TestClient

from app.main import app
from app.public_page_builder import public_shortcode_bundles
from app.admin_control import shortcode_catalog, module_manager
from app.config import Settings


def test_v100_public_page_builder_endpoints():
    client = TestClient(app)
    for path in [
        "/public/page-builder",
        "/public/page-builder/shortcodes",
        "/public/page-builder/readiness",
    ]:
        response = client.get(path)
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True


def test_v100_public_page_builder_is_public_safe():
    client = TestClient(app)
    response = client.get("/public/page-builder")
    assert response.status_code == 200
    payload = response.json()
    assert payload["version"] == "1.12.1"
    assert payload["public_defaults"]["raw_analytics_exposed"] is False
    assert payload["public_defaults"]["private_reports_exposed"] is False
    assert payload["flagship_shortcode"] == "[sc_site_intelligence_public_flagship]"
    assert "[sc_public_methodology]" in payload["canonical_stack"]


def test_v100_shortcode_bundles_include_flagship():
    data = public_shortcode_bundles()
    shortcodes = {bundle["shortcode"] for bundle in data["bundles"]}
    assert "[sc_site_intelligence_public_flagship]" in shortcodes
    assert any(bundle["visibility"] == "private" for bundle in data["bundles"])


def test_v100_admin_catalog_includes_page_builder_shortcodes():
    catalog = shortcode_catalog()
    values = {row["shortcode"] for row in catalog["shortcodes"]}
    assert "[sc_site_intelligence_public_flagship]" in values
    assert "[sc_site_intelligence_public_page_builder]" in values
    assert "[sc_public_dashboard_shortcode_bundle]" in values


def test_v100_module_catalog_includes_public_builder():
    modules = module_manager(Settings(version="1.12.1"))["modules"]
    public = [module for module in modules if module["id"] == "public-dashboard"][0]
    assert "[sc_site_intelligence_public_flagship]" in public["shortcodes"]
    assert "/public/page-builder" in public["endpoints"]
