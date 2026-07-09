from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_public_dashboard_navigation_uses_platform_paths():
    response = client.get('/public/navigation?current=climate-energy')
    assert response.status_code == 200
    data = response.json()
    assert data['ok'] is True
    items = data['items']
    assert any(item['slug'] == 'climate-energy' and item['active'] for item in items)
    assert all(item['path'].startswith('/platform/site-intelligence/') for item in items)
    assert data['recommended_shortcode'] == '[sc_public_dashboard_navigation]'


def test_public_topic_page_templates_include_metadata_and_shortcodes():
    response = client.get('/public/page-templates')
    assert response.status_code == 200
    data = response.json()
    slugs = {item['slug'] for item in data['templates']}
    assert {'climate-energy', 'environmental-monitoring', 'biodiversity-land-use', 'knowledge-system', 'search-discovery', 'source-methodology', 'dashboards'} <= slugs
    climate = next(item for item in data['templates'] if item['slug'] == 'climate-energy')
    assert climate['canonical_path'] == '/platform/site-intelligence/climate-energy/'
    assert climate['shortcode'] == '[sc_public_climate_energy_dashboard]'
    assert climate['meta_description']


def test_public_topic_page_template_can_filter_by_slug():
    response = client.get('/public/page-templates?slug=source-methodology')
    assert response.status_code == 200
    data = response.json()
    assert len(data['templates']) == 1
    assert data['templates'][0]['slug'] == 'source-methodology'
    assert data['templates'][0]['shortcode'] == '[sc_public_source_methodology]'


def test_public_topic_page_visual_qa():
    response = client.get('/public/topic-page-visual-qa')
    assert response.status_code == 200
    data = response.json()
    assert data['ok'] is True
    ids = {check['id'] for check in data['checks']}
    assert {'canonical_paths', 'navigation', 'shortcodes', 'active_state', 'copy_boundaries'} <= ids
    assert data['score'] >= 90
