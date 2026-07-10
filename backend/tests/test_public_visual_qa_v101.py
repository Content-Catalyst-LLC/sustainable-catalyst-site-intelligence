from fastapi.testclient import TestClient

from app.main import app
from app.admin_control import module_manager, shortcode_catalog
from app.config import Settings
from app.public_page_builder import public_dashboard_visual_qa, public_page_builder


def test_v101_public_visual_qa_endpoint():
    client = TestClient(app)
    response = client.get('/public/page-builder/visual-qa')
    assert response.status_code == 200
    data = response.json()
    assert data['ok'] is True
    assert data['version'] == '1.10.0'
    assert data['status'] == 'release_candidate'
    assert data['recommended_public_shortcode'] == '[sc_site_intelligence_public_flagship]'
    assert '[sc_public_dashboard_visual_qa]' == data['review_shortcode']
    assert data['score'] >= 90


def test_v101_page_builder_includes_copy_polish_status():
    data = public_page_builder(Settings(version='1.10.0'))
    assert data['version'] == '1.10.0'
    assert data['visual_qa_status'] == 'release_candidate'
    assert data['copy_polish_status'] == 'polished'
    assert 'Read the full page aloud' in ' '.join(data['release_checklist'])


def test_v101_visual_qa_payload_has_public_page_copy():
    data = public_dashboard_visual_qa(Settings(version='1.10.0'))
    copy = data['public_page_copy']
    assert copy['suggested_title'] == 'Sustainable Catalyst Site Intelligence'
    assert 'public-safe dashboard' in copy['suggested_excerpt']
    assert any('non-advice' in item.lower() for item in data['copy_guidelines'])


def test_v101_admin_catalog_includes_visual_qa_shortcode():
    catalog = shortcode_catalog()
    values = {row['shortcode'] for row in catalog['shortcodes']}
    assert '[sc_public_dashboard_visual_qa]' in values


def test_v101_module_catalog_includes_public_release_qa_module():
    modules = module_manager(Settings(version='1.10.0'))['modules']
    qa = [module for module in modules if module['id'] == 'public-release-qa'][0]
    assert qa['visibility'] == 'private-review'
    assert '[sc_public_dashboard_visual_qa]' in qa['shortcodes']
    assert '/public/page-builder/visual-qa' in qa['endpoints']
