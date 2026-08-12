from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

ROOT = Path(__file__).resolve().parents[2]
client = TestClient(app)


def test_runtime_recovery_contract_is_public_safe_and_grouped():
    response = client.get("/public/runtime-recovery")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["version"] == "4.35.23"
    assert data["scope"] == "public-client-recovery-contract"
    assert data["live_upstream_checks_performed"] is False
    assert data["policy"]["maximum_attempts"] == 3
    assert data["policy"]["circuit_failure_threshold"] == 3
    assert {item["id"] for item in data["service_groups"]} >= {"core", "geospatial", "country", "indicators", "research", "operations"}


def test_service_recovery_loads_before_diagnostics_and_application_modules():
    html = (ROOT / "backend/public_app/index.html").read_text(encoding="utf-8")
    fallback = html.index("/app/assets/vector-cartography-v3230.js")
    recovery = html.index("/app/assets/service-recovery-v3224.js")
    runtime = html.index("/app/assets/runtime-v3230.js")
    application = html.index('src="/app/assets/app.js?v=4.35.23" defer')
    assert fallback < recovery < runtime < application


def test_client_recovery_has_bounded_retry_circuit_and_last_known_good_controls():
    js = (ROOT / "backend/public_app/assets/service-recovery-v3224.js").read_text(encoding="utf-8")
    assert "const MAX_ATTEMPTS = 2" in js
    assert "const FAILURE_THRESHOLD = 3" in js
    assert "scsi:service-circuit-open" in js
    assert "scsi:service-fallback" in js
    assert "last-known-good" in js
    assert 'parts.method !== "GET"' in js
    assert 'parts.url.origin !== window.location.origin' in js
    assert "X-SCSI-Runtime-Diagnostic" in js
    assert "window.fetch = reliableFetch" in js


def test_service_worker_marks_recovered_public_json_and_caches_recovery_runtime():
    worker = (ROOT / "backend/public_app/service-worker.js").read_text(encoding="utf-8")
    assert 'const RELEASE="4.35.23"' in worker
    assert "service-recovery-v3224.js" in worker
    assert 'headers.set("X-SCSI-Recovery",reason||"service-worker-cache")' in worker
    assert 'return recovered(cached,"service-worker-cache")' in worker


def test_map_runtime_reports_each_surface_and_schedules_tile_recovery():
    js = (ROOT / "backend/public_app/assets/vector-cartography-v3230.js").read_text(encoding="utf-8")
    assert "const managedMaps = new Map()" in js
    assert "Local boundaries and labels" in js
    assert "scsi:map-recovered" in js
    assert "recoveryScheduled" in js
    assert "surfaces }" in js or "surfaces," in js
    assert "retry: function (id)" in js


def test_runtime_console_exposes_service_and_map_by_map_health():
    js = (ROOT / "backend/public_app/assets/runtime-v3230.js").read_text(encoding="utf-8")
    assert "/public/runtime-recovery" in js
    assert "data-runtime-recover" in js
    assert "function serviceRows()" in js
    assert "Map-by-map health" in js
    assert "scsi:service-circuit-open" in js
    assert "scsi:map-recovered" in js


def test_active_workspace_refreshes_once_after_service_recovery():
    js = (ROOT / "backend/public_app/assets/app.js").read_text(encoding="utf-8")
    assert 'window.addEventListener("scsi:service-recovered"' in js
    assert "await navigateToRoute(state.route)" in js
    assert "recoveryRefreshTimer" in js


def test_wordpress_proxy_uses_retry_cache_and_current_map_runtime():
    php = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text(encoding="utf-8")
    js = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js").read_text(encoding="utf-8")
    assert "Version: 4.35.23" in php
    assert "vector-cartography-v3230.js" in php
    assert "vector-cartography-v3230.css" in php
    assert "recoveryCachePrefix" in js
    assert "attempt < 3" in js
    assert "readRecoveredJson" in js
