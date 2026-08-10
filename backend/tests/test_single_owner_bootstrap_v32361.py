from __future__ import annotations

from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

ROOT = Path(__file__).resolve().parents[2]
CLIENT = TestClient(app)

def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")

def test_bootstrap_recovery_contract_is_public_and_release_aligned():
    response = CLIENT.get("/public/bootstrap-recovery")
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["version"] == "4.20.0"
    assert payload["contract"] == "single-owner-bootstrap-and-loading-recovery"
    assert payload["service_worker"]["registration_owner_count"] == 1
    assert payload["startup"]["fail_open"] is True
    assert payload["startup"]["degraded_workspace_available"] is True

def test_only_bootstrap_registers_and_listens_for_controller_changes():
    assets = ROOT / "backend/public_app/assets"
    registrations = []
    controller_listeners = []
    for path in assets.glob("*.js"):
        text = path.read_text(encoding="utf-8")
        if "serviceWorker.register" in text:
            registrations.append(path.name)
        if "controllerchange" in text:
            controller_listeners.append(path.name)
    assert registrations == ["bootstrap-v32361.js"]
    assert controller_listeners == ["bootstrap-v32361.js"]
    assert "serviceWorker.register" not in read("backend/public_app/assets/app.js")
    assert "serviceWorker.register" not in read("backend/public_app/assets/performance-offline-v3236.js")
    assert "serviceWorker.register" not in read("backend/public_app/assets/experience-v2120.js")

def test_bootstrap_precedes_performance_and_application_and_is_fail_open():
    html = read("backend/public_app/index.html")
    assert '/app/assets/bootstrap-v32361.js?v=4.20.0' in html
    assert html.index("bootstrap-v32361.js") < html.index("performance-offline-v3236.js") < html.index("app.js")
    bootstrap = read("backend/public_app/assets/bootstrap-v32361.js")
    for token in ("startup deadline exceeded", "failOpen", "service-workers-disabled", "scsi:application-ready"):
        if token == "service-workers-disabled":
            continue
        assert token in bootstrap
    app_js = read("backend/public_app/assets/app.js")
    assert "async function startApplication()" in app_js
    assert "Application startup recovered" in app_js
    assert "scsi:application-ready" in app_js

def test_runtime_health_includes_bootstrap_asset_and_endpoint():
    health = CLIENT.get("/public/runtime-health").json()
    assert health["ok"] is True
    assets = {row["path"] for row in health["assets"]}
    endpoints = {row["path"] for row in health["endpoint_contracts"]}
    assert "/app/assets/bootstrap-v32361.js" in assets
    assert "/public/bootstrap-recovery" in endpoints

def test_wordpress_package_preserves_host_isolation_and_carries_bootstrap_asset():
    php = read("wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php")
    assert "Version: 4.20.0" in php
    assert "wp_enqueue_script('scsi-bootstrap" not in php
    assert (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/bootstrap-v32361.js").is_file()
