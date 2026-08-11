from __future__ import annotations

from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.testclient import TestClient

from app.authoritative_api_audit_v4353 import (
    ACCESS_CLASSES,
    COMPLETED_CONNECTOR_TARGETS,
    PRIORITY_CONNECTOR_TARGETS,
    VERIFIED_MACHINE_INTERFACES,
    audit_overview,
    audit_readiness,
    source_inventory,
    workspace_matrix,
)
from app.config import Settings
from app.main import app
from app import unified_live_events
from app.version import APP_VERSION

ROOT = Path(__file__).resolve().parents[2]


def test_release_version_and_taxonomy():
    assert APP_VERSION == "4.35.4"
    assert ACCESS_CLASSES == (
        "LIVE",
        "DISCOVERY",
        "REGISTERED",
        "AUTH_REQUIRED",
        "BULK",
        "STALE",
        "UNAVAILABLE",
    )


def test_audit_inventory_is_broad_and_does_not_equate_registration_with_live(monkeypatch):
    monkeypatch.delenv("SC_SI_RELIEFWEB_APPNAME", raising=False)
    data = audit_overview(Settings(_env_file=None))
    summary = data["summary"]
    assert data["contract"] == "authoritative-api-workspace-integrity-audit"
    assert summary["source_registrations"] >= 175
    assert summary["unique_source_endpoints_or_records"] >= 100
    assert summary["workspaces_with_source_registries"] >= 35
    assert summary["machine_readable_registrations"] >= 80
    assert summary["registered_but_not_retrieved"] > 0
    assert summary["counts"]["LIVE"] < summary["source_registrations"]


def test_reliefweb_is_configuration_gated_until_approved_appname_exists(monkeypatch):
    monkeypatch.delenv("SC_SI_RELIEFWEB_APPNAME", raising=False)
    rows = source_inventory(Settings(_env_file=None))
    reliefweb = [row for row in rows if row.get("host") == "api.reliefweb.int"]
    assert reliefweb
    assert {row["access_class"] for row in reliefweb} == {"AUTH_REQUIRED"}
    assert {row["configuration_state"] for row in reliefweb} == {"configuration-required"}
    assert {row["configuration_key"] for row in reliefweb} == {"SC_SI_RELIEFWEB_APPNAME"}


def test_reliefweb_becomes_live_when_appname_is_configured(monkeypatch):
    monkeypatch.setenv("SC_SI_RELIEFWEB_APPNAME", "sustainable-catalyst-site-intelligence-test")
    rows = source_inventory(Settings(_env_file=None))
    reliefweb = [row for row in rows if row.get("host") == "api.reliefweb.int"]
    assert reliefweb
    assert {row["access_class"] for row in reliefweb} == {"LIVE"}
    assert {row["configuration_state"] for row in reliefweb} == {"configured"}


def test_verified_machine_interfaces_and_completed_targets_are_explicit():
    verified = {row["id"] for row in VERIFIED_MACHINE_INTERFACES}
    assert {
        "reliefweb-v2",
        "usgs-water-ogc-v0",
        "noaa-coastwatch-erddap",
        "nasa-cmr-search",
        "nasa-cmr-graphql",
        "nasa-exoplanet-tap",
        "unhcr-refugee-statistics-v1",
    } <= verified
    completed = {row["id"] for row in COMPLETED_CONNECTOR_TARGETS}
    assert {
        "usgs-water-ogc-v0",
        "noaa-coastwatch-erddap",
        "nasa-exoplanet-tap",
        "unhcr-refugee-statistics-v1",
        "nasa-cmr-search",
    } == completed
    assert PRIORITY_CONNECTOR_TARGETS


def test_workspace_matrix_exposes_registration_and_gap_counts(monkeypatch):
    monkeypatch.delenv("SC_SI_RELIEFWEB_APPNAME", raising=False)
    data = workspace_matrix(Settings(_env_file=None))
    assert data["ok"] is True
    assert data["workspaces"]
    hydrology = next(row for row in data["workspaces"] if row["workspace"] == "Hydrology, Rivers, Flood & Drought")
    assert hydrology["source_registrations"] > 0
    assert "REGISTERED" in hydrology["counts"]
    assert hydrology["machine_readable_registrations"] >= 1


def test_readiness_reports_integrity_checks_without_network_calls(monkeypatch):
    monkeypatch.delenv("SC_SI_RELIEFWEB_APPNAME", raising=False)
    data = audit_readiness(Settings(_env_file=None))
    assert data["ok"] is True
    assert data["version"] == "4.35.4"
    assert data["network_calls_performed"] is False
    assert all(data["checks"].values())


def test_reliefweb_registry_uses_v2_only():
    source = (ROOT / "backend/app/unified_live_events.py").read_text(encoding="utf-8")
    assert '"api_version": "v2"' in source
    assert "https://api.reliefweb.int/v2/reports" in source
    assert "api.reliefweb.int/v1/reports" not in source


def test_reliefweb_v2_requires_appname_before_network_call(monkeypatch):
    monkeypatch.delenv("SC_SI_RELIEFWEB_APPNAME", raising=False)
    monkeypatch.setattr(unified_live_events, "_request_json", lambda *_args, **_kwargs: pytest.fail("network call should not occur"))
    with pytest.raises(RuntimeError, match="reliefweb_v2_appname_not_configured"):
        unified_live_events._reliefweb_reports()


def test_reliefweb_v2_request_carries_appname_and_current_path(monkeypatch):
    captured = {}

    def fake_request(url, timeout=10):
        captured["url"] = url
        captured["timeout"] = timeout
        return {"data": []}

    monkeypatch.setenv("SC_SI_RELIEFWEB_APPNAME", "sustainable-catalyst-test-app")
    monkeypatch.setattr(unified_live_events, "_request_json", fake_request)
    assert unified_live_events._reliefweb_reports(days=7, limit=10) == []
    parsed = urlparse(captured["url"])
    params = parse_qs(parsed.query)
    assert parsed.scheme == "https"
    assert parsed.netloc == "api.reliefweb.int"
    assert parsed.path == "/v2/reports"
    assert params["appname"] == ["sustainable-catalyst-test-app"]
    assert params["limit"] == ["10"]


def test_public_authoritative_api_endpoints(monkeypatch):
    monkeypatch.delenv("SC_SI_RELIEFWEB_APPNAME", raising=False)
    client = TestClient(app)
    overview = client.get("/public/authoritative-apis")
    assert overview.status_code == 200
    assert overview.json()["version"] == "4.35.4"
    catalog = client.get("/public/authoritative-apis/catalog", params={"workspace": "Hydrology"})
    assert catalog.status_code == 200
    assert catalog.json()["sources"]
    matrix = client.get("/public/authoritative-apis/workspaces")
    assert matrix.status_code == 200 and matrix.json()["workspaces"]
    readiness = client.get("/public/authoritative-apis/readiness")
    assert readiness.status_code == 200 and readiness.json()["ok"] is True
    invalid = client.get("/public/authoritative-apis/catalog", params={"access_class": "NOT_A_CLASS"})
    assert invalid.status_code == 400


def test_sources_workspace_surfaces_authoritative_coverage():
    html = (ROOT / "backend/public_app/index.html").read_text(encoding="utf-8")
    js = (ROOT / "backend/public_app/assets/app.js").read_text(encoding="utf-8")
    for token in (
        "AUTHORITATIVE API COVERAGE",
        "authoritativeRegistrationMetric",
        "authoritativeLiveMetric",
        "authoritativeGapMetric",
        "authoritativeAuthMetric",
        "authoritativePriorityTargets",
    ):
        assert token in html
    assert "/public/authoritative-apis" in js
    assert "renderAuthoritativeApiAudit" in js
