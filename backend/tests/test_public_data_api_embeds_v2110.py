from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient
import pytest

from app.main import app
from app import public_data_api_embeds_v2110 as module

client = TestClient(app)


def settings(**kwargs):
    base = {
        "public_data_api_enabled": True,
        "public_data_api_max_limit": 200,
        "public_embeds_enabled": True,
        "public_embed_allowed_origins": "https://example.edu,https://partner.org",
        "institution_name": "Sustainable Catalyst",
        "institution_website": "https://sustainablecatalyst.com",
        "institution_logo_url": "",
        "institution_contact": "",
        "institution_accent": "#8b1e3f",
    }
    base.update(kwargs)
    return SimpleNamespace(**base)


def test_catalog_and_workspace_manifests_are_versioned_and_read_only():
    catalog = module.build_catalog(settings())
    assert catalog["version"] == "3.19.0"
    assert catalog["api_version"] == "v1"
    assert catalog["count"] == 12
    manifest = module.build_workspace_manifest("economics", settings())
    assert manifest["record_endpoint"].endswith("/economics/records")
    assert manifest["credential_exposed"] is False
    assert manifest["authentication"] == "none for public read endpoints"


def test_embed_manifest_is_bounded_portable_and_credential_free():
    out = module.build_embed_manifest("science", theme="dark", chrome="none", height=9999, institution="Example University", settings=settings())
    assert out["height"] == 2200
    assert "embed=1" in out["url"] and "view=science" in out["url"]
    assert "<iframe" in out["iframe"]
    assert out["credential_exposed"] is False
    assert out["allowed_origins"] == ["https://example.edu", "https://partner.org"]


def test_institutional_branding_is_presentation_only_and_color_validated():
    out = module.build_institution_profile(settings(institution_name="Example Institute", institution_accent="red"))
    assert out["name"] == "Example Institute"
    assert out["accent"] == "#8b1e3f"
    assert "unchanged" in out["branding_scope"]
    assert out["attribution_required"] is True


def test_record_wrapper_sanitizes_sensitive_fields(monkeypatch):
    monkeypatch.setattr(module, "_dispatch_records", lambda *_args, **_kwargs: {"records": [{"title": "Public", "api_key": "do-not-expose", "nested": {"token": "x", "source": "official"}}]})
    out = module.build_workspace_records("economics", settings(), limit=5)
    row = out["payload"]["records"][0]
    assert "api_key" not in row
    assert "token" not in row["nested"]
    assert row["nested"]["source"] == "official"
    assert out["credential_exposed"] is False


def test_invalid_workspace_and_specialized_records_fail_closed():
    with pytest.raises(ValueError):
        module.build_workspace_manifest("missing", settings())
    with pytest.raises(ValueError):
        module.build_workspace_records("research", settings())
    with pytest.raises(ValueError):
        module.build_embed_manifest("unknown", settings=settings())


def test_public_routes_frontend_and_wordpress_contract():
    assert client.get("/api/public/v1").status_code == 200
    assert client.get("/api/public/v1/catalog").status_code == 200
    assert client.get("/api/public/v1/workspaces/economics").status_code == 200
    assert client.get("/api/public/v1/embed?view=economics&theme=light&chrome=compact").status_code == 200
    assert client.get("/api/public/v1/institution").status_code == 200
    csv_response = client.get("/api/public/v1/workspaces/economics/records.csv?limit=2")
    assert csv_response.status_code == 200 and "text/csv" in csv_response.headers["content-type"]
    assert client.get("/api/public/v1/openapi-summary").status_code == 200
    assert client.get("/api/public/v1/diagnostics").status_code == 200
    root = Path(__file__).resolve().parents[2]
    html = (root / "backend/public_app/index.html").read_text()
    js = (root / "backend/public_app/assets/integration-v2110.js").read_text()
    css = (root / "backend/public_app/assets/integration-v2110.css").read_text()
    appjs = (root / "backend/public_app/assets/app.js").read_text()
    php = (root / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text()
    assert 'data-route="integration"' in html and 'id="publicDataIntegrationStudio"' in html
    assert "SCIntegrationV2110" in js and ".public-data-integration-studio" in css
    assert 'const APP_VERSION="3.19.0"' in appjs
    assert "Version: 3.19.0" in php and "sc_site_intelligence_embed" in php and "sc_public_data_api_integration" in php
