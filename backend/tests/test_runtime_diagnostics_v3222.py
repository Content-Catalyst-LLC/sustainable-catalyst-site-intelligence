from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

ROOT = Path(__file__).resolve().parents[2]
client = TestClient(app)


def test_public_runtime_health_is_local_public_safe_and_versioned():
    response = client.get("/public/runtime-health")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["version"] == "4.24.0"
    assert data["scope"] == "local-runtime-contract"
    assert data["live_upstream_checks_performed"] is False
    assert data["summary"]["available_assets"] == data["summary"]["required_assets"]
    assert any(item["path"] == "/public/runtime-health" for item in data["endpoint_contracts"])


def test_runtime_assets_load_between_map_reliability_and_application():
    html = (ROOT / "backend/public_app/index.html").read_text(encoding="utf-8")
    fallback = html.index("/app/assets/vector-cartography-v3230.js")
    runtime = html.index("/app/assets/runtime-v3230.js")
    application = html.index('src="/app/assets/app.js?v=4.24.0" defer')
    assert fallback < runtime < application
    assert "/app/assets/runtime-v3230.css" in html


def test_runtime_health_tray_has_rescan_copy_and_fault_capture():
    js = (ROOT / "backend/public_app/assets/runtime-v3230.js").read_text(encoding="utf-8")
    css = (ROOT / "backend/public_app/assets/runtime-v3230.css").read_text(encoding="utf-8")
    assert "window.SCSIRuntimeHealth" in js
    assert "/public/runtime-health" in js
    assert 'window.addEventListener("unhandledrejection"' in js
    assert "data-runtime-rerun" in js and "data-runtime-copy" in js
    assert ".scsi-runtime-toggle" in css and ".scsi-runtime-panel" in css


def test_map_runtime_keeps_first_party_interactive_mode_without_openstreetmap():
    js = (ROOT / "backend/public_app/assets/vector-cartography-v3230.js").read_text(encoding="utf-8")
    css = (ROOT / "backend/public_app/assets/vector-cartography-v3230.css").read_text(encoding="utf-8")
    assert 'reason: this._isBase() ? "basemap-tiles-unavailable"' in js
    assert 'container.dataset.scsiMapMode = this._map._boundaries ? "self-hosted-vector-cartography" : "self-hosted-grid"' in js
    assert 'this._root.style.display = "none"' in js
    assert ".scsi-map-imagery-limited" in css
    assert "snapshot: function" in js


def test_runtime_assets_are_offline_cached_and_release_aligned():
    worker = (ROOT / "backend/public_app/service-worker.js").read_text(encoding="utf-8")
    assert 'const RELEASE="4.24.0"' in worker
    assert "runtime-v3230.js" in worker
    assert "runtime-v3230.css" in worker
    assert "vector-cartography-v3230.js" in worker


def test_wordpress_package_uses_the_upgraded_map_runtime():
    php = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text(encoding="utf-8")
    fallback = ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/vector-cartography-v3230.js"
    assert "Version: 4.24.0" in php
    assert "vector-cartography-v3230.js" in php
    assert fallback.is_file()
    assert "basemap-tiles-unavailable" in fallback.read_text(encoding="utf-8")


def test_runtime_health_reports_known_map_surfaces_and_recovery_policy():
    data = client.get("/public/runtime-health").json()
    surfaces = {item["container_id"]: item for item in data["map_surfaces"]}
    assert surfaces["spatialEvidenceMap"]["status"] == "declared"
    assert surfaces["eventExplorerMap"]["fallback_supported"] is True
    assert "openstreetmap_tiles_unavailable" in data["recovery_policy"]
    assert data["embed_policy"]["frame_policy"] in {"configured-origin-csp", "same-origin-only"}
