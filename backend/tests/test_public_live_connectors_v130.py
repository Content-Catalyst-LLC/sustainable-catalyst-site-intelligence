from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app
from app.public_live_connectors import (
    admin_connector_diagnostics,
    public_cache_status,
    public_connector_detail,
    public_connector_status,
    public_source_freshness,
)


def test_public_connector_status_payload():
    data = public_connector_status(Settings(version="3.9.0"))
    assert data["ok"] is True
    assert data["version_scope"] == "v3.9.0"
    assert data["counts"]["live_ready"] >= 4
    assert any(item["slug"] == "world-bank" for item in data["connectors"])
    assert "[sc_public_connector_status]" == data["recommended_shortcode"]


def test_public_cache_and_freshness_payloads_are_public_safe():
    settings = Settings(version="3.9.0")
    cache = public_cache_status(settings)
    freshness = public_source_freshness(settings)
    assert cache["cache_enabled"] is True
    assert len(cache["policies"]) >= 5
    assert len(freshness["freshness"]) >= 5
    assert all("next_refresh_after" in item for item in cache["policies"])
    assert all("public_note" in item for item in freshness["freshness"])


def test_public_connector_details_include_methodology_and_no_secrets():
    detail = public_connector_detail("github", Settings(version="3.9.0"))
    assert detail["ok"] is True
    assert detail["connector"]["slug"] == "github"
    assert detail["connector"]["requires_credentials"] is False
    assert "methodology" in detail
    environmental = public_connector_detail("environmental", Settings(version="3.9.0"))
    assert len(environmental["subconnectors"]) >= 6


def test_admin_connector_diagnostics_hides_values():
    settings = Settings(version="3.9.0", eia_api_key="super_private_value", epa_aqs_email="a@example.com", epa_aqs_key="super_private_value")
    data = admin_connector_diagnostics(settings)
    assert data["optional_credentials"]["eia_api_key_configured"] is True
    assert data["optional_credentials"]["epa_aqs_credentials_configured"] is True
    assert "super_private_value" not in str(data)
    assert "raw upstream payloads" in data["hidden"]


def test_public_connector_endpoints():
    client = TestClient(app)
    for path in [
        "/public/connectors/status",
        "/public/connectors/cache",
        "/public/connectors/freshness",
        "/public/connectors/world-bank",
        "/public/connectors/openalex",
        "/public/connectors/crossref",
        "/public/connectors/github",
        "/public/connectors/environmental",
    ]:
        response = client.get(path)
        assert response.status_code == 200, path
        assert response.json()["ok"] is True
