from app.main import app
from fastapi.testclient import TestClient


def test_public_landing_page_endpoint_returns_public_model():
    client = TestClient(app)
    response = client.get('/public/landing-page')
    assert response.status_code == 200
    payload = response.json()
    assert payload['ok'] is True
    assert payload['status']['raw_analytics_exposed'] is False
    assert payload['cards']
    assert payload['sections']


def test_public_climate_summary_defaults_to_fast_snapshot():
    client = TestClient(app)
    response = client.get('/public/climate-energy-summary')
    assert response.status_code == 200
    payload = response.json()
    assert payload['ok'] is True
    assert payload['source'] == 'public-stable-snapshot'
    assert payload['stability']['public_status'] == 'public_ready'
    assert payload['indicators']
