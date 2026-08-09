from __future__ import annotations

from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

ROOT = Path(__file__).resolve().parents[2]
CLIENT = TestClient(app)


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_performance_offline_contract_is_public_release_aligned_and_bounded():
    response = CLIENT.get("/public/performance-offline")
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["version"] == "4.7.0"
    assert payload["release_id"] == "site-intelligence-v4.7.0"
    assert payload["contract"] == "performance-and-offline-recovery"
    assert payload["performance_budgets"]["first_useful_map_ms"] == 3500
    assert payload["performance_budgets"]["api_network_timeout_ms"] == 5500
    assert payload["loading"]["route_request_cancellation"] is True
    assert payload["cache_strategies"]["public_api_data"] == "network-first-timeout-cached-fallback"
    assert payload["boundaries"]["cached_response_must_be_labeled"] is True


def test_app_shell_places_performance_runtime_before_application_fetches():
    html = read("backend/public_app/index.html")
    assert '/app/assets/performance-offline-v3236.css?v=4.7.0' in html
    assert '/app/assets/performance-offline-v3236.js?v=4.7.0' in html
    assert html.index("runtime-v3230.js") < html.index("performance-offline-v3236.js") < html.index("app.js")
    js = read("backend/public_app/assets/performance-offline-v3236.js")
    for token in (
        "scsi:first-useful-map",
        "scsi:route-interactive",
        "route-changed",
        "duplicate",
        "scsi:bootstrap-state",
        "insideApp",
    ):
        assert token.lower() in js.lower()


def test_service_worker_uses_distinct_release_shell_immutable_and_data_strategies():
    worker = read("backend/public_app/service-worker.js")
    assert 'const RELEASE="4.7.0"' in worker
    assert 'const IMMUTABLE=`${VERSION}-immutable`' in worker
    assert "cacheFirstImmutable" in worker
    assert "networkFirstData" in worker
    assert "NETWORK_TIMEOUT_MS=5500" in worker
    assert 'headers.set("X-SCSI-Data-State","offline-cached")' in worker
    assert "bootstrap-v32361.js" in worker
    assert "performance-offline-v3236.js" in worker
    assert "!key.startsWith(VERSION)" in worker


def test_runtime_health_includes_performance_assets_and_endpoint():
    health = CLIENT.get("/public/runtime-health").json()
    assert health["ok"] is True
    assets = {row["path"] for row in health["assets"]}
    endpoints = {row["path"] for row in health["endpoint_contracts"]}
    assert "/app/assets/performance-offline-v3236.js" in assets
    assert "/app/assets/performance-offline-v3236.css" in assets
    assert "/public/performance-offline" in endpoints


def test_wordpress_packages_assets_without_executing_app_runtime_in_host_page():
    php = read("wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php")
    assert "Version: 4.7.0" in php
    assert "performanceOfflineCssUrl" in php
    assert "performanceOfflineJsUrl" in php
    assert "wp_enqueue_script('scsi-performance-offline'" not in php
    assets = ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/assets"
    assert (assets / "performance-offline-v3236.js").is_file()
    assert (assets / "performance-offline-v3236.css").is_file()


def test_policy_requires_honest_offline_and_update_recovery_states():
    payload = CLIENT.get("/public/performance-offline").json()
    assert "offline-cached" in payload["offline_states"]
    assert "update-ready" in payload["offline_states"]
    assert payload["recovery"]["controlled_reload_on_controller_change"] is True
    assert payload["recovery"]["single_reload_guard"] is True
    assert payload["recovery"]["remove_previous_release_caches"] is True
    assert payload["measurement"]["first_useful_map_requires_visible_geography_or_tiles"] is True
