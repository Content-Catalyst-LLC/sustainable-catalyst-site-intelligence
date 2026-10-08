from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.browser_api_transport_v455322 import (
    PUBLIC_WEB_ORIGIN,
    RUNTIME_DIAGNOSTIC_HEADER,
    classify_transport,
    manifest,
    required_cors_request_headers,
)
from app.main import app
from app.route_registry_v4430 import capability_manifest
from app.version import APP_VERSION, RELEASE_NAME

ROOT = Path(__file__).resolve().parents[2]
client = TestClient(app)


def test_release_identity_and_route_inventory_are_stable():
    assert APP_VERSION == "4.55.3.2.2"
    assert RELEASE_NAME == "Browser API Transport & CORS Repair"
    inventory = capability_manifest(app.routes)
    assert inventory["registry_version"] == "2.6.2"
    assert inventory["route_count"] == 1518
    assert inventory["modularized_route_count"] == 209
    assert inventory["capability_count"] == 31
    assert inventory["unclassified_route_count"] == 0


def test_registry_declares_preflight_and_strict_offline_contract():
    data = manifest()
    assert data["version"] == APP_VERSION
    assert data["production_preflight_gate"]["path"] == "/health"
    assert data["runtime_transport"]["ordinary_public_gets_require_custom_header"] is False
    assert RUNTIME_DIAGNOSTIC_HEADER in required_cors_request_headers()
    assert classify_transport(browser_online=True, primary_health_ok=True, optional_failures=4) == "degraded"
    assert classify_transport(browser_online=True, primary_health_ok=False, optional_failures=0) == "offline"


def test_cors_preflight_allows_public_web_runtime_diagnostic_header():
    response = client.options(
        "/health",
        headers={
            "Origin": PUBLIC_WEB_ORIGIN,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": RUNTIME_DIAGNOSTIC_HEADER,
        },
    )
    assert response.status_code == 200, response.text
    assert response.headers.get("access-control-allow-origin") == PUBLIC_WEB_ORIGIN
    allowed = response.headers.get("access-control-allow-headers", "").lower()
    assert RUNTIME_DIAGNOSTIC_HEADER.lower() in allowed
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_cross_origin_health_get_accepts_diagnostic_header():
    response = client.get(
        "/health",
        headers={"Origin": PUBLIC_WEB_ORIGIN, RUNTIME_DIAGNOSTIC_HEADER: APP_VERSION},
    )
    assert response.status_code == 200
    assert response.json()["version"] == APP_VERSION
    assert response.headers.get("access-control-allow-origin") == PUBLIC_WEB_ORIGIN


def test_runtime_public_gets_no_longer_require_custom_diagnostic_header():
    for rel in ["web/app/assets/runtime-v3230.js", "backend/public_app/assets/runtime-v3230.js"]:
        text = (ROOT / rel).read_text()
        assert 'headers: { Accept: "application/json" }' in text
        assert '"X-SCSI-Runtime-Diagnostic": VERSION' not in text
        assert 'primaryService && !primaryService.ok' in text


def test_fastapi_cors_allowlist_retains_runtime_diagnostic_header():
    text = (ROOT / "backend/app/main.py").read_text()
    assert '"X-SCSI-Runtime-Diagnostic"' in text
    assert 'https://intelligence.sustainablecatalyst.com' in (ROOT / "backend/app/config.py").read_text()


def test_release_bound_registries_are_aligned():
    deploy = (ROOT / "deploy/contabo/upgrade_site_intelligence_backend_v4_55_3_2_2_contabo.sh").read_text()
    block = deploy.split("RELEASE_BOUND_POLICIES=(", 1)[1].split("\n)", 1)[0]
    names = [line.strip() for line in block.splitlines() if line.strip() and not line.strip().startswith("#")]
    assert len(names) == 45
    assert "browser_api_transport_registry_v455322.json" in names
    for name in names:
        payload = json.loads((ROOT / "backend/data" / name).read_text())
        assert payload["version"] == APP_VERSION, name
