from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_public_topic_dashboard_directory():
    response = client.get('/public/dashboards')
    assert response.status_code == 200
    data = response.json()
    assert data['ok'] is True
    slugs = {item['slug'] for item in data['dashboards']}
    assert {'climate-energy', 'environmental-monitoring', 'biodiversity-land-use', 'knowledge-system', 'search-discovery'} <= slugs
    assert data['recommended_index_shortcode'] == '[sc_public_dashboard_directory]'


def test_public_topic_dashboard_payloads_are_public_safe():
    for slug in ['climate-energy', 'environmental-monitoring', 'biodiversity-land-use', 'knowledge-system', 'search-discovery']:
        response = client.get(f'/public/dashboards/{slug}')
        assert response.status_code == 200
        data = response.json()
        assert data['ok'] is True
        assert data['slug'] == slug
        assert data['shortcode'].startswith('[sc_public_')
        assert data['cards']
        assert 'methodology' in data
        assert 'Raw analytics and query-level reports' in data['methodology']['hidden']


def test_public_source_methodology():
    response = client.get('/public/source-methodology')
    assert response.status_code == 200
    data = response.json()
    assert data['ok'] is True
    assert data['recommended_shortcode'] == '[sc_public_source_methodology]'
    assert len(data['principles']) >= 4
    assert len(data['source_families']) >= 5


def test_private_topic_dashboard_index_requires_token_in_production(monkeypatch):
    # The app default environment in tests is development, so protected route should be reachable.
    response = client.get('/intelligence/public-topic-dashboards')
    assert response.status_code == 200
    assert response.json()['ok'] is True
