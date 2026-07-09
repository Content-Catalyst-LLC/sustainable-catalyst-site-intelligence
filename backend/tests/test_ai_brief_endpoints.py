from fastapi.testclient import TestClient

from app.main import app


def test_ai_status_endpoint_available_in_dev():
    client = TestClient(app)
    response = client.get("/ai/status")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "provider" in data


def test_ai_briefs_catalog_endpoint_available_in_dev():
    client = TestClient(app)
    response = client.get("/intelligence/ai-briefs")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert any(item["id"] == "site-intelligence" for item in data["briefs"])
