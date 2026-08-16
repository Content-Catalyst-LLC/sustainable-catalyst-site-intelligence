from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.production_truth_v3231 import ROUTES

ROOT = Path(__file__).resolve().parents[2]
CLIENT = TestClient(app)


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_production_truth_directory_is_complete_and_honest():
    response = CLIENT.get("/public/workspaces/production-truth")
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["version"] == "4.38.0"
    assert payload["release_id"] == "site-intelligence-v4.38.0"
    assert payload["contract"] == "production-truth-and-workspace-completion"
    assert payload["route_count"] == 35 == len(ROUTES)
    assert payload["summary"]["operational"] == 19
    assert payload["summary"]["operational_bounded"] == 16
    assert payload["summary"]["unavailable"] == 0
    assert payload["summary"]["lazy_loaded"] == 35


def test_every_public_route_has_all_five_runtime_states():
    payload = CLIENT.get("/public/workspaces/production-truth").json()
    expected = {"initial", "ready", "empty", "degraded", "unavailable"}
    route_ids = {route["route_id"] for route in payload["routes"]}
    html = read("backend/public_app/index.html")
    nav_routes = set()
    for route_id in route_ids:
        assert f'data-route="{route_id}"' in html
        nav_routes.add(route_id)
    assert nav_routes == route_ids
    for route in payload["routes"]:
        assert set(route["state_contract"]) == expected
        assert route["empty_state"]
        assert route["degraded_state"]
        assert route["limitation"]
        assert route["publicly_navigable"] is True
        assert route["lazy_load"] is True


def test_route_detail_rejects_unknown_routes():
    assert CLIENT.get("/public/workspaces/production-truth/overview").status_code == 200
    response = CLIENT.get("/public/workspaces/production-truth/not-a-route")
    assert response.status_code == 404
    assert response.json()["detail"] == "Unknown public workspace route"


def test_frontend_enforces_route_truth_history_and_recovery():
    js = read("backend/public_app/assets/production-truth-v3231.js")
    for token in (
        'const VERSION="4.38.0"',
        'ENDPOINT="/public/workspaces/production-truth"',
        "productionTruthBar",
        "initial:\"Opening workspace\"",
        "ready:\"Workspace ready\"",
        "empty:\"No matching public records\"",
        "degraded:\"Workspace partially available\"",
        "unavailable:\"Workspace unavailable\"",
        "controllerAvailable",
        "surfaceFor",
        "classifySurface",
        "history.pushState",
        "window.addEventListener('popstate'",
        "SCSIRouterV3228?.navigate",
        "scsi:service-fallback",
        "scsi:service-recovered",
        "scsi:workspace-state",
        "active route only",
    ):
        assert token in js


def test_frontend_disables_missing_controllers_instead_of_false_success():
    js = read("backend/public_app/assets/production-truth-v3231.js")
    assert "button.disabled=!available" in js
    assert "data-production-state" in read("backend/public_app/assets/production-truth-v3231.css")
    assert "The required public controller or workspace surface is not available" in js
    assert "No public records are available for this workspace" in js


def test_app_shell_and_offline_cache_include_production_truth_assets():
    html = read("backend/public_app/index.html")
    assert 'data-scsi-release="4.38.0"' in html
    assert '/app/assets/production-truth-v3231.css?v=4.38.0' in html
    assert '/app/assets/production-truth-v3231.js?v=4.38.0' in html
    assert html.index("app.js") < html.index("cartographic-workspace-v3230.js") < html.index("production-truth-v3231.js")
    worker = read("backend/public_app/service-worker.js")
    assert 'const RELEASE="4.38.0"' in worker
    assert "production-truth-v3231.js" in worker
    assert "production-truth-v3231.css" in worker


def test_runtime_health_requires_the_production_truth_contract():
    payload = CLIENT.get("/public/runtime-health").json()
    assert payload["ok"] is True
    assert payload["status"] == "healthy"
    paths = {item["path"] for item in payload["assets"]}
    assert "/app/assets/production-truth-v3231.js" in paths
    assert "/app/assets/production-truth-v3231.css" in paths
    endpoint_paths = {item["path"] for item in payload["endpoint_contracts"]}
    assert "/public/workspaces/production-truth" in endpoint_paths


def test_wordpress_packages_production_truth_assets_without_running_them_in_the_host_document():
    php = read("wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php")
    assert "Version: 4.38.0" in php
    assert "site-intelligence-v4.38.0" in php
    assert "wp_enqueue_style('scsi-production-truth'" not in php
    assert "wp_enqueue_script('scsi-production-truth'" not in php
    for name in ("production-truth-v3231.js", "production-truth-v3231.css"):
        assert (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/assets" / name).is_file()
    js = read("wordpress-plugin/sustainable-catalyst-site-intelligence/assets/production-truth-v3231.js")
    assert "APP_ROOT=document.querySelector('#app[data-scsi-release]')" in js
    assert "if(!APP_ROOT||!document.querySelector('#primaryNavigation')||!document.querySelector('#main.workspace'))return" in js
