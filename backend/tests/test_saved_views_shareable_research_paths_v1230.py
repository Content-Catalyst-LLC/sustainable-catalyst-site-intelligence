from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.saved_views import (
    ALLOWED_VIEWS,
    SCHEMA_VERSION,
    STORAGE_KEY,
    diagnostics,
    migrations_manifest,
    schema_manifest,
    validate_manifest,
)

client = TestClient(app)


def valid_manifest(**overrides):
    manifest = {
        "schema": SCHEMA_VERSION,
        "application_version": "3.20.0",
        "id": "sv-test-123456",
        "name": "Kenya climate investigation",
        "view": "thematic",
        "state": {
            "dashboard": "climate-environment",
            "country": "KEN",
            "thematicDays": "30",
            "thematicLayer": "true-color",
        },
        "created_at": "2026-07-11T00:00:00Z",
    }
    manifest.update(overrides)
    return manifest


def test_schema_manifest_is_browser_local_and_public_only():
    payload = schema_manifest()
    assert payload["schema"] == SCHEMA_VERSION
    assert payload["storage_key"] == STORAGE_KEY
    assert payload["storage"] == "browser-localStorage"
    assert payload["privacy"]["server_persistence"] is False
    assert payload["privacy"]["shared_urls_contain_public_state_only"] is True
    assert {item["id"] for item in payload["allowed_views"]} == set(ALLOWED_VIEWS)


def test_valid_thematic_manifest_is_normalized_without_persistence():
    result = validate_manifest(valid_manifest())
    assert result["valid"] is True
    assert result["persisted"] is False
    assert result["manifest"]["state"]["country"] == "KEN"
    assert result["manifest"]["state"]["dashboard"] == "climate-environment"


def test_unknown_state_fields_are_removed_with_warning():
    manifest = valid_manifest(state={"dashboard": "climate-environment", "country": "KEN", "privateNote": "do not retain"})
    result = validate_manifest(manifest)
    assert result["valid"] is True
    assert "privateNote" not in result["manifest"]["state"]
    assert any("privateNote" in warning for warning in result["warnings"])


def test_sensitive_fields_are_rejected_recursively():
    manifest = valid_manifest(state={"dashboard": "climate-environment", "country": "KEN", "api_key": "abc"})
    result = validate_manifest(manifest)
    assert result["valid"] is False
    assert "Sensitive field" in result["errors"][0]


def test_invalid_country_code_is_rejected():
    manifest = valid_manifest(state={"dashboard": "climate-environment", "country": "KENYA"})
    result = validate_manifest(manifest)
    assert result["valid"] is False
    assert "three-letter" in result["errors"][0]


def test_duplicate_comparison_country_is_rejected():
    manifest = valid_manifest(
        view="compare",
        state={"country": "KEN", "compare": "KEN", "compareView": "table"},
    )
    result = validate_manifest(manifest)
    assert result["valid"] is False
    assert "must be different" in result["errors"][0]


def test_legacy_manifest_migrates_to_current_schema():
    legacy = {
        "schema": "sc-saved-view/0.9",
        "application_version": "3.20.0",
        "id": "sv-legacy-123456",
        "title": "Legacy source research",
        "route": "sources",
        "params": {"source": "world-bank", "state": "live"},
        "saved_at": "2026-07-10T12:00:00Z",
    }
    result = validate_manifest(legacy)
    assert result["valid"] is True
    assert result["migrated_from"] == "sc-saved-view/0.9"
    assert result["manifest"]["schema"] == SCHEMA_VERSION
    assert result["manifest"]["view"] == "sources"
    assert result["manifest"]["name"] == "Legacy source research"


def test_unsupported_schema_and_view_are_rejected():
    unsupported_schema = validate_manifest({**valid_manifest(), "schema": "sc-saved-view/8.0"})
    unsupported_view = validate_manifest({**valid_manifest(), "view": "admin"})
    assert unsupported_schema["valid"] is False
    assert unsupported_view["valid"] is False


def test_manifest_size_limit_rejects_oversized_import():
    manifest = valid_manifest(name="x" * 70000)
    result = validate_manifest(manifest)
    assert result["valid"] is False
    assert "byte limit" in result["errors"][0]


def test_migrations_and_diagnostics_are_public_safe():
    migrations = migrations_manifest()
    report = diagnostics()
    assert migrations["current_schema"] == SCHEMA_VERSION
    assert migrations["persistence"] == "none"
    assert report["ok"] is True
    assert report["checks"]["server_persistence_disabled"] is True
    assert "secret" not in str(report).lower()


def test_saved_view_public_endpoints():
    schema_response = client.get("/public/saved-views/schema")
    migrations_response = client.get("/public/saved-views/migrations")
    diagnostics_response = client.get("/public/saved-views/diagnostics")
    validation_response = client.post("/public/saved-views/validate", json=valid_manifest())
    assert schema_response.status_code == 200
    assert migrations_response.status_code == 200
    assert diagnostics_response.status_code == 200
    assert validation_response.status_code == 200
    assert validation_response.json()["valid"] is True


def test_validate_endpoint_does_not_persist_or_echo_unknown_fields():
    manifest = valid_manifest()
    manifest["unknown_top_level"] = "removed"
    response = client.post("/public/saved-views/validate", json=manifest)
    payload = response.json()
    assert payload["persisted"] is False
    assert "unknown_top_level" not in payload["manifest"]


def test_public_app_exposes_saved_views_workspace_and_dialog():
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    html = (root / "backend/public_app/index.html").read_text(encoding="utf-8")
    assert 'data-route="saved"' in html
    assert 'id="savedViewsStudio"' in html
    assert 'id="saveViewDialog"' in html
    assert 'id="savedImportFile"' in html


def test_frontend_uses_local_storage_and_public_validation_only():
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    js = (root / "backend/public_app/assets/app.js").read_text(encoding="utf-8")
    assert 'sc_site_intelligence_saved_views_v1' in js
    assert 'localStorage.setItem' in js
    assert '/public/saved-views/validate' in js
    assert 'sc-saved-view-collection/1.0' in js
    assert 'savedViewUrl' in js
    assert 'No unvalidated file was stored.' in js


def test_wordpress_saved_views_shortcode_contract():
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    php = (root / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text(encoding="utf-8")
    assert "Version: 3.20.0" in php
    assert "const VERSION = '3.20.0';" in php
    assert "add_shortcode('sc_saved_research_views'" in php
    assert "public function saved_research_views_shortcode" in php
    assert "/app/?view=saved" in php


def test_invalid_earth_layer_and_reversed_dates_are_rejected():
    bad_layer = validate_manifest(
        valid_manifest(
            view="earth",
            state={"earthLayer": "private-layer", "dateA": "2026-07-01", "dateB": "2026-07-10"},
        )
    )
    bad_dates = validate_manifest(
        valid_manifest(
            view="earth",
            state={"earthLayer": "true-color", "dateA": "2026-07-10", "dateB": "2026-07-01"},
        )
    )
    assert bad_layer["valid"] is False
    assert bad_dates["valid"] is False


def test_briefing_fractional_opacity_is_valid():
    result = validate_manifest(
        valid_manifest(
            view="briefing",
            state={
                "type": "earth",
                "briefType": "earth",
                "layer_id": "true-color",
                "date_a": "2026-07-01",
                "date_b": "2026-07-10",
                "latitude": "12",
                "longitude": "20",
                "zoom": "2",
                "opacity": "0.72",
            },
        )
    )
    assert result["valid"] is True
    assert result["manifest"]["state"]["opacity"] == "0.72"


def test_frontend_saved_view_cards_include_rename_workflow():
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    js = (root / "backend/public_app/assets/app.js").read_text(encoding="utf-8")
    assert 'data-saved-action="rename"' in js
    assert 'prompt("Rename saved view"' in js
    assert 'toast("Saved view renamed")' in js
