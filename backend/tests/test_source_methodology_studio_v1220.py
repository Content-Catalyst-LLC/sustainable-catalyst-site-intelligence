from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from app.main import app
from app import source_methodology_studio as studio

client = TestClient(app)
ROOT = Path(__file__).resolve().parents[2]


def test_source_directory_contains_required_public_records_and_states():
    payload = studio.source_directory(include_health=False)

    assert payload["ok"] is True
    assert payload["version"] == "3.18.0"
    assert payload["schema_version"] == "sc-source-methodology/1.0"
    assert payload["recommended_shortcode"] == '[sc_source_methodology_studio height="1100"]'

    source_ids = {item["id"] for item in payload["sources"]}
    assert {
        "world-bank",
        "nasa-gibs",
        "usgs-earthquakes",
        "nasa-eonet",
        "reliefweb",
    } <= source_ids

    assert set(payload["states"]) == {
        "live",
        "cached",
        "stale",
        "temporarily-unavailable",
        "experimental",
        "disabled",
    }
    assert "API keys" in payload["hidden"]
    assert "secret environment variables" in payload["hidden"]


def test_source_directory_filters_domain_state_feature_and_query():
    nasa = studio.source_directory(query="NASA")
    assert {item["id"] for item in nasa["sources"]} >= {"nasa-gibs", "nasa-eonet", "nasa-power"}

    events = studio.source_directory(domain="events")
    assert {item["id"] for item in events["sources"]} == {
        "usgs-earthquakes",
        "nasa-eonet",
        "reliefweb",
    }

    live = studio.source_directory(state="live")
    assert live["sources"]
    assert all(item["state"] == "live" for item in live["sources"])

    compare = studio.source_directory(feature="compare")
    assert {"world-bank", "usgs-earthquakes", "nasa-eonet", "reliefweb"} <= {
        item["id"] for item in compare["sources"]
    }


def test_source_detail_status_and_coverage(monkeypatch):
    monkeypatch.setattr(
        studio,
        "_public_dynamic_states",
        lambda: (
            {
                "world-bank": {
                    "state": "cached",
                    "last_checked": "2026-07-11T00:00:00+00:00",
                    "last_successful_retrieval": "2026-07-10T23:00:00+00:00",
                    "status_note": "Cached diagnostic fixture.",
                }
            },
            [],
        ),
    )

    detail = studio.source_detail("world-bank", include_health=True)
    assert detail["source"]["state"] == "cached"
    assert detail["source"]["source_name"] if "source_name" in detail["source"] else detail["source"]["name"]
    assert any(item["id"] == "latest-value-selection" for item in detail["methodologies"])

    status = studio.source_status("world-bank")
    assert status["state_label"] == "Cached"
    assert status["last_successful_retrieval"] == "2026-07-10T23:00:00+00:00"

    coverage = studio.source_coverage("nasa-gibs")
    assert coverage["geographic_coverage"]
    assert coverage["temporal_coverage"]
    assert coverage["known_limits"]

    with pytest.raises(studio.SourceMethodologyError):
        studio.source_detail("not-a-source", include_health=False)


def test_methodology_registry_matches_actual_reliability_rules():
    payload = studio.methodology_directory()
    method_ids = {item["id"] for item in payload["methods"]}

    assert payload["version"] == "3.18.0"
    assert payload["total_registered"] >= 17
    assert {
        "latest-value-selection",
        "missing-values",
        "zero-vs-unavailable",
        "reporting-year-differences",
        "indicator-compatibility",
        "country-event-matching",
        "event-deduplication",
        "earth-date-validation",
        "imagery-interpretation",
        "brief-generation",
        "export-generation",
        "cache-behavior",
        "optional-source-failures",
    } <= method_ids

    compare = studio.methodology_directory(feature="compare")
    assert all("compare" in item["applies_to"] or "all-public-views" in item["applies_to"] for item in compare["methods"])

    missing = studio.methodology_directory(query="missing")
    assert any(item["id"] == "missing-values" for item in missing["methods"])


def test_methodology_detail_retains_sources_rules_and_limits():
    detail = studio.methodology_detail("indicator-compatibility")
    assert detail["methodology"]["rules"]
    assert detail["methodology"]["limitations"]
    assert {item["id"] for item in detail["sources"]} == {"world-bank"}

    with pytest.raises(studio.SourceMethodologyError):
        studio.methodology_detail("not-a-method")


def test_public_safe_diagnostics_validate_cross_references(monkeypatch):
    monkeypatch.setattr(
        studio,
        "_public_dynamic_states",
        lambda: (
            {
                "world-bank": {"state": "live", "last_checked": "2026-07-11T00:00:00+00:00"},
                "nasa-gibs": {"state": "experimental", "last_checked": "2026-07-11T00:00:00+00:00"},
                "usgs-earthquakes": {"state": "live", "last_checked": "2026-07-11T00:00:00+00:00"},
                "nasa-eonet": {"state": "live", "last_checked": "2026-07-11T00:00:00+00:00"},
                "reliefweb": {"state": "cached", "last_checked": "2026-07-11T00:00:00+00:00"},
            },
            [],
        ),
    )

    payload = studio.studio_diagnostics()
    checks = payload["checks"]
    assert checks["required_source_records_complete"] is True
    assert checks["all_sources_have_official_urls"] is True
    assert checks["all_sources_have_known_limits"] is True
    assert checks["all_method_source_references_valid"] is True
    assert checks["all_source_methodology_references_valid"] is True
    assert checks["secrets_exposed"] is False
    assert checks["platform_core_dependency"] == "optional"


def test_json_and_csv_exports_are_source_complete(monkeypatch):
    monkeypatch.setattr(studio, "_public_dynamic_states", lambda: ({}, []))

    json_body, json_type, json_name = studio.studio_export("json", include_health=True)
    assert json_type == "application/json"
    assert json_name.endswith(".json")
    assert '"schema_version": "sc-source-methodology/1.0"' in json_body
    assert '"world-bank"' in json_body
    assert '"latest-value-selection"' in json_body

    csv_body, csv_type, csv_name = studio.studio_export("csv", include_health=True)
    assert csv_type == "text/csv"
    assert csv_name.endswith(".csv")
    assert csv_body.startswith("\ufeff")
    rows = list(csv.DictReader(StringIO(csv_body.lstrip("\ufeff"))))
    assert len(rows) == len(studio.SOURCE_RECORDS)
    assert all(row["official_url"] for row in rows)
    assert all(row["known_limits"] for row in rows)

    with pytest.raises(studio.SourceMethodologyError):
        studio.studio_export("pdf")


def test_public_source_and_methodology_endpoints():
    responses = {
        "/public/sources": client.get("/public/sources"),
        "/public/sources/world-bank": client.get("/public/sources/world-bank"),
        "/public/sources/world-bank/coverage": client.get("/public/sources/world-bank/coverage"),
        "/public/methodology": client.get("/public/methodology"),
        "/public/methodology/indicator-compatibility": client.get("/public/methodology/indicator-compatibility"),
        "/public/source-methodology/export?format=json&include_health=false": client.get(
            "/public/source-methodology/export?format=json&include_health=false"
        ),
        "/public/source-methodology/export?format=csv&include_health=false": client.get(
            "/public/source-methodology/export?format=csv&include_health=false"
        ),
    }

    for endpoint, response in responses.items():
        assert response.status_code == 200, endpoint

    assert responses["/public/sources"].json()["schema_version"] == "sc-source-methodology/1.0"
    assert responses["/public/sources/world-bank"].json()["source"]["id"] == "world-bank"
    assert responses["/public/methodology/indicator-compatibility"].json()["methodology"]["id"] == "indicator-compatibility"

    json_export = responses["/public/source-methodology/export?format=json&include_health=false"]
    assert json_export.headers["cache-control"] == "no-store"
    assert json_export.headers["x-content-type-options"] == "nosniff"

    csv_export = responses["/public/source-methodology/export?format=csv&include_health=false"]
    assert "attachment" in csv_export.headers["content-disposition"]


def test_unknown_public_source_and_methodology_return_404():
    assert client.get("/public/sources/not-registered").status_code == 404
    assert client.get("/public/methodology/not-registered").status_code == 404
    assert client.get("/public/source-methodology/export?format=pdf").status_code == 422


def test_standalone_source_studio_contract_is_present():
    html = (ROOT / "backend/public_app/index.html").read_text(encoding="utf-8")
    js = (ROOT / "backend/public_app/assets/app.js").read_text(encoding="utf-8")
    css = (ROOT / "backend/public_app/assets/app.css").read_text(encoding="utf-8")

    assert 'data-route="sources"' in html
    assert 'id="sourceStudio"' in html
    assert 'id="sourceRegistryList"' in html
    assert 'id="methodologyRegistryList"' in html
    assert "/public/source-methodology/diagnostics" in js
    assert "/public/source-methodology/export" in js
    assert "const sourceStudioState" in js
    assert ".source-studio" in css
    assert ".methodology-registry-list" in css


def test_wordpress_source_methodology_shortcode_contract():
    php = (
        ROOT
        / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php"
    ).read_text(encoding="utf-8")

    assert "Version: 3.18.0" in php
    assert "const VERSION = '3.18.0';" in php
    assert "add_shortcode('sc_source_methodology_studio'" in php
    assert "public function source_methodology_studio_shortcode" in php
    assert "view' => 'sources'" in php
    assert "source-methodology-embed" in php


def test_release_docs_and_manifest_exist():
    documentation = (ROOT / "docs/SOURCE_AND_METHODOLOGY_STUDIO_V1220.md").read_text(encoding="utf-8")
    manifest = (ROOT / "docs/RELEASE_MANIFEST_V1220.json").read_text(encoding="utf-8")
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "Source and Methodology Studio" in documentation
    assert '"release": "1.22.0"' in manifest
    assert "## 1.22.0 — Source and Methodology Studio" in changelog
    assert "**Current release:** v3.18.0" in readme
