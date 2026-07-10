from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_overview_and_sources():
    overview = client.get('/public/human-security').json()
    assert overview['ok'] is True
    assert overview['schema'] == 'sc-conflict-displacement-human-security/1.0'
    assert len(overview['monitors']) == 6
    sources = client.get('/public/human-security/sources').json()
    assert sources['counts']['sources'] == 6
    assert any(item['source_id'] == 'acled' for item in sources['sources'])


def test_monitor_detail_and_not_found():
    response = client.get('/public/human-security/monitors/civilian-protection')
    assert response.status_code == 200
    assert response.json()['monitor']['monitor_id'] == 'civilian-protection'
    assert client.get('/public/human-security/monitors/not-real').status_code == 404


def test_event_displacement_forecast_and_export_contracts():
    events = client.get('/public/human-security/events?record_type=conflict_event&country=SDN').json()
    assert events['filters']['country'] == 'SDN'
    assert 'modeled_forecast' in events['supported_record_types']
    displacement = client.get('/public/human-security/displacement').json()
    assert 'refugees' in displacement['categories']
    forecast = client.get('/public/human-security/modeled-risk').json()
    assert 'not_observed' in forecast['labels']
    export = client.get('/public/human-security/export').json()
    assert export['formats'] == ['json', 'csv_ready']
