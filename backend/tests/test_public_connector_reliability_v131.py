from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app
from app.public_live_connectors import (
    admin_connector_diagnostics,
    public_connector_reliability,
    public_connector_status,
    public_connector_status_polish,
)


def test_connector_reliability_payload_is_public_safe():
    data = public_connector_reliability(Settings(version="2.19.0"))
    assert data["ok"] is True
    assert data["version_scope"] == "v2.19.0"
    assert data["recommended_shortcode"] == "[sc_public_connector_reliability]"
    assert data["score"] >= 70
    assert data["reliability_counts"]["healthy"] >= 4
    assert all("recovery_action" in item for item in data["status_cards"])
    assert "raw upstream payload" not in str(data).lower()


def test_connector_status_now_includes_reliability_counts():
    data = public_connector_status(Settings(version="2.19.0"))
    assert data["version_scope"] == "v2.19.0"
    assert "reliability_score" in data
    assert "reliability_counts" in data
    assert any(item["reliability_level"] == "healthy" for item in data["status_cards"])


def test_status_polish_payload_contains_display_guidance_and_hidden_fields():
    data = public_connector_status_polish(Settings(version="2.19.0"))
    assert data["ok"] is True
    assert data["recommended_shortcode"] == "[sc_public_connector_status_polish]"
    assert any("[sc_public_connector_status]" in item for item in data["display_guidance"])
    assert "API key values" in data["hidden"]


def test_admin_diagnostics_includes_recovery_queue_without_secrets():
    settings = Settings(version="2.19.0", eia_api_key="secret-value", epa_aqs_key="secret-value", epa_aqs_email="ops@example.com")
    data = admin_connector_diagnostics(settings)
    assert data["version_scope"] == "v2.19.0"
    assert "recovery_queue" in data
    assert "secret-value" not in str(data)


def test_public_connector_reliability_endpoints():
    client = TestClient(app)
    for path in [
        "/public/connectors/reliability",
        "/public/connectors/status-polish",
    ]:
        response = client.get(path)
        assert response.status_code == 200, path
        assert response.json()["ok"] is True
