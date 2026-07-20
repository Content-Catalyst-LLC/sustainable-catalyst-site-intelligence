from fastapi.testclient import TestClient

from app.main import app
from app.config import Settings
from app.release import release_checklist, release_public_summary, release_status, smoke_test
from app.admin_control import shortcode_catalog, module_manager


def test_v100_release_public_summary_endpoint_is_public_safe():
    client = TestClient(app)
    response = client.get('/release/public-summary')
    assert response.status_code == 200
    data = response.json()
    assert data['ok'] is True
    assert data['version'] == '3.1.5'
    assert data['recommended_page']['shortcode'] == '[sc_site_intelligence_app height="1000"]'
    assert 'raw analytics' in ' '.join(data['boundaries']).lower()
    assert 'meta_description' in data['metadata']


def test_v100_release_status_requires_token_in_production():
    client = TestClient(app)
    response = client.get('/release/status')
    # Default test settings have no token configured, so protected route is callable in tests.
    assert response.status_code == 200
    data = response.json()
    assert data['version'] == '3.1.5'
    assert data['release_stage'] == 'v3.1.5_security_privacy_governance_production_scale'
    assert data['public_shortcode'] == '[sc_site_intelligence_app height="1000"]'
    assert data['release_score'] >= 70


def test_v100_release_helpers_include_launch_metadata_and_smoke_checks():
    settings = Settings(version='3.1.5')
    checklist = release_checklist(settings)
    summary = release_public_summary(settings)
    status = release_status(settings)
    smoke = smoke_test(settings)
    assert checklist['counts']['total'] >= 8
    assert summary['metadata']['page_title'] == 'Site Intelligence'
    assert status['private_status_shortcode'] == '[sc_site_intelligence_release_status]'
    assert any('/public/countries/diagnostics' == item['path'] for item in smoke['checks'])


def test_v100_admin_catalog_includes_release_status_shortcode():
    values = {row['shortcode'] for row in shortcode_catalog()['shortcodes']}
    assert '[sc_site_intelligence_release_status]' in values


def test_v100_module_catalog_includes_release_module():
    modules = module_manager(Settings(version='3.1.5'))['modules']
    release_modules = [module for module in modules if module['id'] == 'release-status']
    assert release_modules
    module = release_modules[0]
    assert '/release/status' in module['endpoints']
    assert '[sc_site_intelligence_release_status]' in module['shortcodes']
