from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

ROOT = Path(__file__).resolve().parents[2]
client = TestClient(app)


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_global_conditions_is_a_permanent_sidebar_route():
    html = read("backend/public_app/index.html")
    app_js = read("backend/public_app/assets/app.js")
    global_js = read("backend/public_app/assets/global-conditions-v210.js")
    assert html.count('data-route="global"') == 1
    assert 'Global conditions</span><small>Conditions and live map' in html
    assert '#primaryNavigation")?.addEventListener("click"' in app_js
    assert 'event.target.closest?.(".nav-item[data-route]")' in app_js
    assert "createElement(\"button\")" not in global_js
    assert "window.SCSIRouterV3228" in app_js


def test_map_startup_is_entirely_first_party():
    html = read("backend/public_app/index.html")
    runtime = read("backend/public_app/assets/vector-cartography-v3230.js")
    assert "unpkg.com/leaflet" not in html
    assert "leaflet@1.9.4/dist/leaflet.js" not in html
    assert html.index("vector-cartography-v3230.js") < html.index('src="/app/assets/app.js?v=4.35.21"')
    assert '__scsiFirstParty: true' in runtime
    assert 'mode: "vector-cartography-engine"' in runtime
    assert 'data-map-zoom-in' in runtime
    assert 'pointerdown' in runtime and 'wheel' in runtime and 'keydown' in runtime


def test_map_health_only_counts_visible_degraded_surfaces():
    runtime = read("backend/public_app/assets/runtime-v3230.js")
    assert "visibleSurfaces" in runtime
    assert 'surface.visible !== false' in runtime
    assert 'mode.indexOf("fallback")' not in runtime
    assert "self-hosted map engine remains healthy on its local world-boundary basemap" in runtime


def test_runtime_contract_reports_first_party_map_bootstrap():
    response = client.get("/public/runtime-health")
    assert response.status_code == 200
    data = response.json()
    checks = {item["id"]: item for item in data["checks"]}
    assert data["status"] == "healthy"
    assert checks["first-party-map-runtime"]["status"] == "pass"
    assert data["recovery_policy"]["map_engine"] == "Use the vector cartography engine with local Natural Earth country boundaries and labels."


def test_wordpress_uses_the_same_first_party_runtime_before_map_features():
    php = read("wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php")
    js = read("wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js")
    map_js = read("wordpress-plugin/sustainable-catalyst-site-intelligence/assets/vector-cartography-v3230.js")
    assert "wp_enqueue_script('scsi-map-engine'" in php
    assert "['scsi-map-engine']" in php
    assert "return loadSelfHostedMapEngine();" in js
    assert "unpkg.com/leaflet" not in js
    assert "__scsiFirstParty" in map_js


def test_release_and_offline_shell_are_aligned():
    worker = read("backend/public_app/service-worker.js")
    html = read("backend/public_app/index.html")
    assert 'const RELEASE="4.35.21"' in worker
    assert 'data-scsi-release="4.35.21"' in html
    assert "vector-cartography-v3230.js" in worker
    assert "global-conditions-v210.js" in worker
