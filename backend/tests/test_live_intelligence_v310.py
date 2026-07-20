from fastapi.testclient import TestClient

from app.main import app
from app.config import get_settings
from app.live_intelligence_v310 import build_live_intelligence


def test_live_intelligence_contract():
    payload = build_live_intelligence(get_settings(), limit=8)
    assert payload["ok"] is True
    assert payload["version"] == "3.1.0"
    assert payload["schema"] == "sc-site-intelligence-live-intelligence/1.0"
    assert 1 <= payload["count"] <= 8
    for signal in payload["signals"]:
        assert signal["signal_id"]
        assert signal["label"]
        assert signal["value"]
        assert signal["source_name"]
        assert signal["updated_at"]


def test_live_intelligence_endpoint_and_filter():
    client = TestClient(app)
    response = client.get("/public/live-intelligence?category=platform&limit=4")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "3.1.0"
    assert data["count"] <= 4
    assert all(item["category"] == "platform" for item in data["signals"])
    status = client.get("/public/live-intelligence/status")
    assert status.status_code == 200
    assert status.json()["service"] == "available"
