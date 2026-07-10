from fastapi.testclient import TestClient

from app.main import app
from app.human_development_intelligence import DOMAINS, SOURCES, SCHEMA

client = TestClient(app)


def test_human_development_overview():
    response = client.get('/public/human-development')
    assert response.status_code == 200
    payload = response.json()
    assert payload['schema'] == SCHEMA
    assert len(payload['domains']) == 7
    assert len(payload['sources']) >= 9


def test_human_development_sources():
    payload = client.get('/public/human-development/sources').json()
    assert payload['counts']['sources'] == len(SOURCES)
    assert payload['counts']['no_key_required'] == len(SOURCES)


def test_human_development_domain_detail():
    response = client.get('/public/human-development/domains/education')
    assert response.status_code == 200
    payload = response.json()
    assert payload['domain']['domain_id'] == 'education'
    assert any(source['source_id'] == 'unesco-uis' for source in payload['sources'])


def test_human_development_missing_domain():
    assert client.get('/public/human-development/domains/not-real').status_code == 404


def test_human_development_country_profile_and_methodology():
    profile = client.get('/public/human-development/country-profile?country=KEN').json()
    assert profile['country_code'] == 'KEN'
    assert len(profile['sections']) == len(DOMAINS)
    methodology = client.get('/public/human-development/methodology').json()
    assert methodology['normalized_observation_schema']['schema'] == SCHEMA


def test_human_development_export():
    payload = client.get('/public/human-development/export').json()
    assert 'json' in payload['formats']
    assert len(payload['records']['domains']) == 7
