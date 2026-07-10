from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_dashboard_directory_and_manifest():
    response = client.get('/public/dashboard-studio')
    assert response.status_code == 200
    body = response.json()
    assert body['version'] == '1.14.1'
    assert len(body['dashboards']) >= 4
    assert client.get('/public/dashboard-studio/manifest').status_code == 200


def test_dashboard_detail_data_sources_brief_export():
    dashboard_id = 'climate-human-vulnerability'
    assert client.get(f'/public/dashboard-studio/{dashboard_id}').status_code == 200
    data = client.get(f'/public/dashboard-studio/{dashboard_id}/data?country=KEN').json()
    assert data['filters']['geography']['country'] == 'KEN'
    assert client.get(f'/public/dashboard-studio/{dashboard_id}/sources').status_code == 200
    assert client.get(f'/public/dashboard-studio/{dashboard_id}/brief?country=KEN').status_code == 200
    assert client.get(f'/public/dashboard-studio/{dashboard_id}/export?country=KEN').status_code == 200


def test_country_and_comparison_views():
    profile = client.get('/public/country-intelligence/KEN')
    assert profile.status_code == 200
    assert len(profile.json()['domains']) == 6
    comparison = client.get('/public/cross-domain-comparison?country=KEN&compare=GHA').json()
    assert comparison['ok'] is True
