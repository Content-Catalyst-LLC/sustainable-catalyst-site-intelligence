from fastapi.testclient import TestClient

from app.main import app
from app.admin_control import shortcode_catalog


def test_admin_overview_endpoint_available_in_dev():
    client = TestClient(app)
    response = client.get('/intelligence/admin')
    assert response.status_code == 200
    data = response.json()
    assert data['ok'] is True
    assert data['version'] == '3.7.1'
    assert data['totals']['modules'] >= 1
    assert data['totals']['shortcodes'] >= 1


def test_admin_registry_and_coverage_endpoints():
    client = TestClient(app)
    registry = client.get('/admin/registry')
    coverage = client.get('/admin/registry/coverage')
    assert registry.status_code == 200
    assert coverage.status_code == 200
    assert registry.json()['ok'] is True
    assert 'counts' in registry.json()
    assert 'coverage' in coverage.json()


def test_admin_modules_sources_shortcodes_diagnostics():
    client = TestClient(app)
    for path in ['/admin/modules', '/admin/sources', '/admin/shortcodes', '/admin/diagnostics', '/admin/visibility', '/admin/source-control']:
        response = client.get(path)
        assert response.status_code == 200
        assert response.json()['ok'] is True


def test_shortcode_catalog_includes_v090_admin_shortcodes():
    data = shortcode_catalog()
    values = {item['shortcode'] for item in data['shortcodes']}
    assert '[sc_site_intelligence_admin_overview]' in values
    assert '[sc_site_intelligence_shortcode_catalog]' in values
    assert '[sc_site_intelligence_module_status]' in values
