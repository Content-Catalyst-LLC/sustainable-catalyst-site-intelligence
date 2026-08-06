from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

ROOT = Path(__file__).resolve().parents[2]
client = TestClient(app)


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_release_identity_and_workspace_assets_are_current():
    assert 'APP_VERSION = "3.24.0"' in read("backend/app/version.py")
    html = read("backend/public_app/index.html")
    assert 'data-scsi-release="3.24.0"' in html
    assert "/app/assets/cartographic-workspace-v3230.css?v=3.24.0" in html
    assert "/app/assets/cartographic-workspace-v3230.js?v=3.24.0" in html
    assert html.index("vector-cartography-v3230.js") < html.index("runtime-v3230.js") < html.index("app.js") < html.index("cartographic-workspace-v3230.js")


def test_workspace_css_creates_bounded_map_first_application():
    css = read("backend/public_app/assets/cartographic-workspace-v3230.css")
    for token in (
        "[hidden]{display:none!important}",
        "body{background:",
        "overflow:hidden",
        ".overview-layout{display:grid",
        ".overview-evidence-rail",
        "#map{height:clamp(520px",
        "body:not([data-active-route=\"overview\"])",
        "min-height:440px!important",
    ):
        assert token in css
    assert ".orbital-glow,.map-vignette{display:none!important}" in css


def test_workspace_runtime_routes_drawer_focus_and_visible_health():
    js = read("backend/public_app/assets/cartographic-workspace-v3230.js")
    for token in (
        "buildOverviewWorkspace",
        "overviewEvidenceRail",
        "setRailOpen(!evidenceRail.classList.contains('is-open'))",
        "document.body.dataset.activeRoute=route",
        "focusSelectedCountry",
        "map.flyTo",
        "evaluateVisibleMaps",
        "scsiPresentationHealth",
        "scsi:visible-map-health",
        "rect.width>=300&&rect.height>=300",
        "paths>0||tiles>0",
    ):
        assert token in js


def test_runtime_health_requires_workspace_and_map_assets():
    response = client.get("/public/runtime-health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["status"] == "healthy"
    paths = {item["path"] for item in payload["assets"]}
    for path in (
        "/app/assets/vector-cartography-v3230.js",
        "/app/assets/world-cartography-v3230.geojson",
        "/app/assets/runtime-v3230.js",
        "/app/assets/cartographic-workspace-v3230.css",
        "/app/assets/cartographic-workspace-v3230.js",
    ):
        assert path in paths


def test_country_selection_reframes_the_primary_map():
    app_js = read("backend/public_app/assets/app.js")
    workspace_js = read("backend/public_app/assets/cartographic-workspace-v3230.js")
    assert 'apiWithRetry(`/public/country/${code}/overview`' in app_js
    assert "state.map?.flyTo?." in app_js
    assert "country.latitude" in workspace_js
    assert "country.longitude" in workspace_js
    assert "Number(country.default_zoom||5)" in workspace_js


def test_wordpress_packages_workspace_runtime_and_release_identity():
    php = read("wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php")
    assert "Version: 3.24.0" in php
    assert "cartographic-workspace-v3230.css" in php
    assert "vector-cartography-v3230.js" in php
    assert "wp_enqueue_style('scsi-cartographic-workspace'" not in php
    assert "wp_enqueue_script('scsi-cartographic-workspace-script'" not in php
    for name in (
        "cartographic-workspace-v3230.css",
        "cartographic-workspace-v3230.js",
        "vector-cartography-v3230.js",
        "world-cartography-v3230.geojson",
    ):
        assert (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/assets" / name).is_file()


def test_service_worker_caches_current_presentation_assets():
    worker = read("backend/public_app/service-worker.js")
    assert 'const RELEASE="3.24.0"' in worker
    for name in (
        "cartographic-workspace-v3230.js",
        "cartographic-workspace-v3230.css",
        "vector-cartography-v3230.js",
        "world-cartography-v3230.geojson",
    ):
        assert name in worker


def test_current_promotion_gate_and_browser_smoke_are_declared():
    promote = read("promote_site_intelligence_v3_22_9_to_github_and_render_macos.sh")
    assert 'RELEASE="3.24.0"' in promote
    assert "vector-cartography-v3230.js" in promote
    assert "world-cartography-v3230.geojson" in promote
    assert "/public/runtime-health" in promote
    smoke = read("scripts/browser_smoke_v3230.py")
    assert "cartographic-workspace-v3230.js" in smoke
    assert "overviewLayout" in smoke
    assert "presentationHealth" in smoke
    assert "routeHidden" in smoke
