from __future__ import annotations

import json
from pathlib import Path

from app.main import app
from app.route_registry_v4430 import capability_manifest
from app.runtime_context_repair_v455321 import (
    classify_runtime_health,
    manifest,
    normalize_domain_context,
)
from app.version import APP_VERSION, RELEASE_NAME

ROOT = Path(__file__).resolve().parents[2]


def test_release_identity_and_route_inventory_remain_stable():
    assert APP_VERSION == "4.55.3.2.2"
    assert RELEASE_NAME == "Browser API Transport & CORS Repair"
    inventory = capability_manifest(app.routes)
    assert inventory["registry_version"] == "2.6.2"
    assert inventory["route_count"] == 1518
    assert inventory["modularized_route_count"] == 209
    assert inventory["capability_count"] == 31
    assert inventory["unclassified_route_count"] == 0


def test_release_registry_declares_strict_offline_semantics():
    data = manifest()
    assert data["version"] == APP_VERSION
    assert data["runtime_health"]["primary_health_path"] == "/health"
    assert data["runtime_health"]["optional_endpoint_failure_state"] == "degraded"
    assert data["economics_empty_state"]["fabricated_records"] is False


def test_runtime_health_requires_network_or_primary_health_failure_for_offline():
    healthy_primary = [
        {"label": "Service", "path": "/health", "ok": True},
        {"label": "Runtime", "path": "/public/runtime-health", "ok": False},
        {"label": "Geospatial", "path": "/public/geospatial/diagnostics", "ok": False},
        {"label": "Spatial", "path": "/public/spatial", "ok": False},
    ]
    assert classify_runtime_health(online=True, endpoints=healthy_primary) == "degraded"
    assert classify_runtime_health(online=False, endpoints=healthy_primary) == "offline"
    broken_primary = [{"label": "Service", "path": "/health", "ok": False}]
    assert classify_runtime_health(online=True, endpoints=broken_primary) == "offline"


def test_domain_context_normalizes_country_into_domain_specific_keys():
    econ = normalize_domain_context("economics", "ken")
    assert econ["country"] == "KEN"
    assert econ["geography_code"] == "KEN"
    resources = normalize_domain_context("resources", "irl")
    assert resources["geography_code"] == "IRL"
    law = normalize_domain_context("law", "ken")
    assert law["country"] == "KEN"
    assert "geography_code" not in law


def test_standalone_bridge_propagates_deep_link_country_context():
    bridge = (ROOT / "web/app/assets/standalone-api-bridge-v45532.js").read_text()
    assert 'const RELEASE="4.55.3.2.2"' in bridge
    assert '["economics","science","resources"].includes(view)' in bridge
    assert 'q.set("geography_code",resolved)' in bridge
    assert "SCSIStandaloneBridgeV455321" in bridge


def test_runtime_health_browser_code_no_longer_counts_optional_failures_as_offline():
    for rel in [
        "web/app/assets/runtime-v3230.js",
        "backend/public_app/assets/runtime-v3230.js",
    ]:
        text = (ROOT / rel).read_text()
        assert 'failed >= 3' not in text
        assert 'primaryService && !primaryService.ok' in text
        assert 'return "degraded"' in text


def test_economics_reads_global_country_and_has_truthful_zero_record_state():
    for rel in [
        "web/app/assets/economics-v220.js",
        "backend/public_app/assets/economics-v220.js",
    ]:
        text = (ROOT / rel).read_text()
        assert 'params.get("country") || qs("#countrySelect")?.value' in text
        assert 'no official economics records matched ${domainCountryLabel()}' in text
        assert 'No matching official economics records for ${domainCountryLabel()}' in text
        assert 'records are available through the Site Intelligence public bridge' not in text


def test_current_web_release_and_service_worker_are_cache_busted():
    assert 'release: "4.55.3.2.2"' in (ROOT / "web/config.js").read_text()
    html = (ROOT / "web/index.html").read_text()
    assert 'data-scsi-release="4.55.3.2.2"' in html
    assert 'runtime-v3230.js?v=4.55.3.2.2' in html
    assert 'economics-v220.js?v=2.2.0' in html  # controller identity remains domain v2.2; patched code is cache-busted by service worker/release shell.
    worker = (ROOT / "web/service-worker.js").read_text()
    assert "4.55.3.2.2" in worker


def test_all_release_bound_registries_are_aligned():
    deploy = (ROOT / "deploy/contabo/upgrade_site_intelligence_backend_v4_55_3_2_2_contabo.sh").read_text()
    block = deploy.split("RELEASE_BOUND_POLICIES=(", 1)[1].split("\n)", 1)[0]
    names = [line.strip() for line in block.splitlines() if line.strip() and not line.strip().startswith("#")]
    assert len(names) == 45
    for name in names:
        payload = json.loads((ROOT / "backend/data" / name).read_text())
        assert payload["version"] == APP_VERSION, name
