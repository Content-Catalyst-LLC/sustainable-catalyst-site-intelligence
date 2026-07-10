from fastapi.testclient import TestClient

from app.main import app
from app.public_api_sources import (
    public_development_indicators,
    public_indicator_overview,
    public_repository_intelligence,
    public_research_metadata,
    public_source_health,
    public_sources,
    public_sustainability_indicators,
)

client = TestClient(app)


def test_public_api_source_payload_is_public_safe():
    data = public_sources()
    assert data["ok"] is True
    assert data["version_scope"] == "v1.3.0"
    assert any("World Bank" in item["source_examples"] for item in data["source_families"])
    assert any("OpenAlex" in item["source_examples"] for item in data["source_families"])
    assert any("GitHub repositories" in item["source_examples"] for item in data["source_families"])
    exclusions = " ".join(sum([item["private_exclusions"] for item in data["source_families"]], []))
    assert "API keys" in exclusions or "tokens" in exclusions


def test_public_source_health_counts_and_hidden_fields():
    data = public_source_health()
    assert data["ok"] is True
    assert data["counts"]["cached"] >= 3
    assert data["counts"]["planned"] >= 3
    assert "API credentials and keys" in data["hidden"]


def test_development_research_repository_indicator_payloads():
    dev = public_development_indicators()
    research = public_research_metadata()
    repos = public_repository_intelligence()
    overview = public_indicator_overview()
    sustainability = public_sustainability_indicators()

    assert dev["recommended_shortcode"] == "[sc_public_development_indicators]"
    assert "World Bank" in dev["indicator_groups"][0]["sources"]
    assert "OpenAlex" in research["metadata_groups"][0]["sources"]
    assert "GitHub" in repos["repository_groups"][0]["sources"]
    assert any(item["status"] == "cached" for item in overview["indicators"])
    assert "ESG assurance" in " ".join(sustainability["methodology"])


def test_public_api_source_endpoints():
    endpoints = [
        "/public/sources",
        "/public/sources/health",
        "/public/sources/development-indicators",
        "/public/sources/research-metadata",
        "/public/sources/publications",
        "/public/sources/repositories",
        "/public/indicators/overview",
        "/public/indicators/sustainability",
    ]
    for endpoint in endpoints:
        response = client.get(endpoint)
        assert response.status_code == 200
        payload = response.json()
        assert payload["ok"] is True
        assert "generated_at" in payload
