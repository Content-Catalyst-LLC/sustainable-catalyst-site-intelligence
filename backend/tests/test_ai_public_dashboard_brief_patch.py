from fastapi.testclient import TestClient

from app.main import app


def test_ai_public_dashboard_brief_uses_public_safe_snapshot():
    client = TestClient(app)
    response = client.get('/ai/briefs/public-dashboard?use_ai=false')
    assert response.status_code == 200
    data = response.json()
    assert data['ok'] is True
    assert data['brief_id'] == 'public-dashboard-ai-brief'
    assert data['source_report']['source']['dashboard'] == 'public-safe-snapshot'
    assert data['source_report']['source']['live_analytics'] is False
    assert '<!DOCTYPE' not in data['executive_summary']
