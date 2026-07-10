from fastapi.testclient import TestClient
from app.main import app
from app.international_law_governance import SOURCES, MONITORS, NORMALIZED_LEGAL_EVENT_SCHEMA

client = TestClient(app)


def test_overview_and_sources():
    response = client.get('/public/international-law')
    assert response.status_code == 200
    data = response.json()
    assert data['version_scope'] == 'v1.10.0'
    assert len(data['monitors']) == 7
    assert len(data['sources']) >= 10


def test_sanctions_monitor_is_advisory():
    data = client.get('/public/international-law/sanctions').json()
    assert data['ok'] is True
    assert 'not a substitute' in data['safety_note'].lower()
    assert 'official_reason_link' in data['fields']


def test_monitor_detail_and_not_found():
    response = client.get('/public/international-law/monitors/treaties')
    assert response.status_code == 200
    assert response.json()['monitor']['monitor_id'] == 'treaties'
    assert client.get('/public/international-law/monitors/not-real').status_code == 404


def test_event_stream_schema():
    data = client.get('/public/international-law/events?event_type=judgment&jurisdiction=global').json()
    assert data['filters']['event_type'] == 'judgment'
    assert data['record_schema']['schema'] == 'sc-international-law-governance/1.0'
    assert 'legal_status' in data['record_schema']['required']


def test_methodology_and_export():
    methodology = client.get('/public/international-law/methodology').json()
    export = client.get('/public/international-law/export').json()
    assert 'legal advice' in methodology['excluded_uses']
    assert export['schema'] == 'sc-international-law-governance/1.0'
    assert len(SOURCES) >= 10 and len(MONITORS) == 7
    assert NORMALIZED_LEGAL_EVENT_SCHEMA['required']
