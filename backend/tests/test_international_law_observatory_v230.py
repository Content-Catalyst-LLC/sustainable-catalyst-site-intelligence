from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app import international_law_observatory as module
from app.main import app

client = TestClient(app)


def settings(**overrides):
    values = {
        "platform_core_enabled": True,
        "platform_core_url": "https://core.example.test",
        "platform_core_public_api_key": "test-public-key",
        "international_law_observatory_enabled": True,
        "international_law_observatory_timeout_seconds": 9,
        "international_law_observatory_cache_ttl_seconds": 120,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def record(**overrides):
    value = {
        "id": "law-1",
        "raw_record_id": "must-not-leak",
        "source_record_id": "S/RES/2728 (2024)",
        "source_id": "un-digital-library",
        "connector_id": "un.digital-library",
        "record_type": "security_council_resolution",
        "authority_level": "official_security_council_resolution",
        "title": "Resolution 2728 (2024)",
        "official_symbol": "S/RES/2728 (2024)",
        "issuing_body": "United Nations Security Council",
        "legal_body": "United Nations Security Council",
        "jurisdiction": "international",
        "legal_status": "adopted",
        "adoption_date": "2024-03-25T00:00:00Z",
        "publication_date": "2024-03-25T00:00:00Z",
        "entry_into_force_date": None,
        "languages": ["English", "French"],
        "countries": ["PSE", "ISR"],
        "subjects": ["Ceasefire", "Humanitarian assistance"],
        "related_instruments": [],
        "related_cases": [],
        "related_resolutions": [],
        "related_sdg_targets": ["16.1"],
        "canonical_source_url": "https://digitallibrary.un.org/record/987654?api_key=must-not-leak",
        "citation": "United Nations Security Council resolution 2728 (2024).",
        "summary": "Official resolution metadata fixture.",
        "license_name": "UN terms",
        "attribution": "United Nations",
        "content_hash": "a" * 64,
        "metadata": {"safe": "value", "token": "must-not-leak"},
        "public": True,
    }
    value.update(overrides)
    return value


def core_records(records):
    return {"data": records, "meta": {"pagination": {"total": len(records), "limit": 100, "offset": 0}}}


def taxonomy():
    return {"data": {"official_security_council_resolution": "Official Security Council resolution. Binding effect must be determined from Charter basis and legal context, not the document symbol alone.", "non_binding_recommendation": "Official non-binding recommendation."}}


def fake_core(config, path, query=None, **kwargs):
    if path.endswith("authority-taxonomy"):
        return taxonomy()
    return core_records([record()])


def test_unconfigured_core_returns_explicit_empty_state():
    payload = module.build_law_overview(settings(platform_core_enabled=False, platform_core_url=""))
    assert payload["integration"]["state"] == "core-unconfigured"
    assert payload["counts"]["records_available"] == 0
    assert payload["governance_policy"]["automatic_binding_effect_inference"] is False
    assert payload["integration"]["credential_exposed"] is False


def test_public_record_sanitizes_and_preserves_authority(monkeypatch):
    monkeypatch.setattr(module, "_core_json", fake_core)
    payload = module.build_law_records(settings(), limit=25)
    item = payload["records"][0]
    assert item["record_type"] == "security_council_resolution"
    assert item["authority_level"] == "official_security_council_resolution"
    assert item["authority_group"] == "institutional"
    assert "document symbol alone" in item["authority_explanation"]
    assert "api_key" not in item["canonical_source_url"]
    assert "token" not in item["metadata"]
    assert "raw_record_id" not in item
    assert "test-public-key" not in str(payload)


def test_timeline_sorts_official_dates(monkeypatch):
    rows = [record(id="new", publication_date="2025-01-01T00:00:00Z", title="New"), record(id="old", publication_date="2024-01-01T00:00:00Z", title="Old")]
    def handler(config, path, query=None, **kwargs):
        return taxonomy() if path.endswith("authority-taxonomy") else core_records(rows)
    monkeypatch.setattr(module, "_core_json", handler)
    payload = module.build_law_timeline(settings())
    assert [item["record_id"] for item in payload["events"]] == ["old", "new"]
    assert payload["events"][0]["authority_label"] == "Official Security Council resolution"


def test_country_profile_and_authority_matrix(monkeypatch):
    rows = [record(id="one"), record(id="two", authority_level="official_report", record_type="un_report", legal_body="United Nations General Assembly", issuing_body="United Nations General Assembly")]
    def handler(config, path, query=None, **kwargs):
        return taxonomy() if path.endswith("authority-taxonomy") else core_records(rows)
    monkeypatch.setattr(module, "_core_json", handler)
    profile = module.build_country_legal_profile(settings(), country="PSE")
    matrix = module.build_authority_matrix(settings(), country="PSE")
    assert profile["counts"]["records"] == 2
    assert profile["interpretation"].startswith("Record presence")
    assert sum(row["total"] for row in matrix["rows"]) == 2
    assert "not a score" in matrix["warning"]


def test_country_profile_requires_country():
    with pytest.raises(ValueError):
        module.build_country_legal_profile(settings(), country="")


def test_public_routes(monkeypatch):
    monkeypatch.setenv("SC_SI_PLATFORM_CORE_ENABLED", "true")
    monkeypatch.setenv("SC_SI_PLATFORM_CORE_URL", "https://core.example.test")
    monkeypatch.setenv("SC_SI_PLATFORM_CORE_PUBLIC_API_KEY", "test-public-key")
    monkeypatch.setenv("SC_SI_INTERNATIONAL_LAW_OBSERVATORY_ENABLED", "true")
    from app.config import get_settings
    get_settings.cache_clear()
    monkeypatch.setattr(module, "_core_json", fake_core)
    overview = client.get("/public/international-law-observatory")
    records = client.get("/public/international-law-observatory/records?limit=10")
    facets = client.get("/public/international-law-observatory/facets")
    timeline = client.get("/public/international-law-observatory/timeline")
    country = client.get("/public/international-law-observatory/country-profile?country=PSE")
    matrix = client.get("/public/international-law-observatory/authority-matrix?country=PSE")
    diagnostics = client.get("/public/international-law-observatory/diagnostics")
    assert all(response.status_code == 200 for response in (overview, records, facets, timeline, country, matrix, diagnostics))
    assert records.json()["records"][0]["official_symbol"] == "S/RES/2728 (2024)"
    assert diagnostics.json()["public_safety"]["legal_advice"] is False


def test_public_interface_and_wordpress_contract():
    root = Path(__file__).resolve().parents[2]
    html = (root / "backend/public_app/index.html").read_text()
    js = (root / "backend/public_app/assets/law-v230.js").read_text()
    css = (root / "backend/public_app/assets/law-v230.css").read_text()
    app_js = (root / "backend/public_app/assets/app.js").read_text()
    php = (root / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text()
    assert 'data-route="law"' in html
    assert 'id="lawStudio"' in html
    assert "SCLawV230" in js
    assert "legal advice" in html.lower()
    assert ".law-studio" in css
    assert 'const APP_VERSION="2.9.0"' in app_js
    assert "Version: 2.9.0" in php
    assert "sc_international_law_governance_observatory" in php
