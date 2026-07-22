from fastapi.testclient import TestClient

from app.main import app
from app.config import get_settings
from app.live_intelligence_v310 import build_live_intelligence


def _settings(**updates):
    settings = get_settings()
    if hasattr(settings, "model_copy"):
        return settings.model_copy(update=updates)
    for key, value in updates.items():
        setattr(settings, key, value)
    return settings


def test_live_intelligence_contract_without_external_calls():
    payload = build_live_intelligence(_settings(external_live=False), limit=8)
    assert payload["ok"] is True
    assert payload["version"] == "3.21.0"
    assert payload["schema"] == "sc-site-intelligence-live-intelligence/1.4"
    assert 1 <= payload["count"] <= 8
    assert payload["feed_state"]["platform_signal_count"] == 1
    for signal in payload["signals"]:
        assert signal["signal_id"]
        assert signal["label"]
        assert signal["value"]
        assert signal["source_name"]
        assert signal["updated_at"]


def test_live_intelligence_endpoint_and_platform_filter():
    client = TestClient(app)
    response = client.get("/public/live-intelligence?category=platform&limit=4")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "3.21.0"
    assert data["count"] == 1
    assert all(item["category"] == "platform" for item in data["signals"])
    status = client.get("/public/live-intelligence/status")
    assert status.status_code == 200
    assert status.json()["service"] == "available"
