from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app import offline_mobile_accessibility_performance_v2120 as delivery

client = TestClient(app)
ROOT = Path(__file__).resolve().parents[2]


def test_v2121_reliability_profile_and_route():
    payload = delivery.build_reliability()
    assert payload["version"] == "2.24.0"
    assert payload["service_worker"]["partial_install_recovery"] is True
    assert payload["service_worker"]["bounded_public_cache"] is True
    assert payload["embeds"]["origin_checked"] is True
    response = client.get("/public/offline-experience/reliability")
    assert response.status_code == 200
    assert response.json()["release_alignment"]["backend"] == "2.24.0"


def test_service_worker_has_upgrade_cache_and_recovery_contracts():
    worker = (ROOT / "backend/public_app/service-worker.js").read_text(encoding="utf-8")
    assert 'const RELEASE="2.24.0"' in worker
    assert "Promise.allSettled" in worker
    assert "trimCache" in worker
    assert "MAX_DATA_ENTRIES=120" in worker
    assert "MAX_DATA_AGE_MS" in worker
    assert "navigationPreload" in worker
    assert "SC_SI_ACTIVATE_UPDATE" in worker
    assert "SC_SI_CLEAR_OFFLINE" in worker
    assert 'request.method!=="GET"' in worker


def test_delivery_headers_force_release_alignment_and_fresh_shell_checks():
    worker = client.get("/app/service-worker.js")
    html = client.get("/app/")
    manifest = client.get("/app/manifest.webmanifest")
    assert worker.headers["cache-control"] == "no-cache, no-store, must-revalidate"
    assert worker.headers["x-sc-cache-generation"] == "scsi-v2.24.0"
    assert html.headers["cache-control"] == "no-cache, no-store, must-revalidate"
    assert manifest.headers["cache-control"] == "no-cache, max-age=0, must-revalidate"
    for response in (worker, html, manifest):
        assert response.headers["x-sc-site-intelligence-version"] == "2.24.0"


def test_manifest_and_offline_page_are_patch_aligned():
    manifest = (ROOT / "backend/public_app/manifest.webmanifest").read_text(encoding="utf-8")
    offline = (ROOT / "backend/public_app/offline.html").read_text(encoding="utf-8")
    assert 'release=2.24.0' in manifest
    assert '"display_override"' in manifest
    assert '"shortcuts"' in manifest
    assert "RELEASE 2.24.0" in offline
    assert "Reset offline cache" in offline
    assert "key.startsWith('scsi-')" in offline


def test_application_registers_uncached_worker_and_reports_versioned_height():
    js = (ROOT / "backend/public_app/assets/app.js").read_text(encoding="utf-8")
    assert 'APP_VERSION="2.24.0"' in js
    assert 'updateViaCache:"none"' in js
    assert "SC_SI_ACTIVATE_UPDATE" in js
    assert 'type:"scsi-height"' in js
    assert "version:APP_VERSION" in js
    assert "SC_SI_REQUEST_HEIGHT" in js
    assert "window.visualViewport" in js


def test_wordpress_embed_controller_checks_origin_and_source_window():
    plugin = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text(encoding="utf-8")
    js = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js").read_text(encoding="utf-8")
    css = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.css").read_text(encoding="utf-8")
    assert "Version: 2.24.0" in plugin
    assert "data-scsi-embed-frame" in plugin
    assert "setupResponsiveEmbeds" in js
    assert "event.origin !== record.origin" in js
    assert "event.source !== record.frame.contentWindow" in js
    assert "SC_SI_REQUEST_HEIGHT" in js
    assert "min-height:760px" in css
    assert "Open Site Intelligence in a new tab" in plugin


def test_delivery_diagnostics_pass_for_packaged_release():
    payload = delivery.build_diagnostics()
    assert payload["version"] == "2.24.0"
    assert payload["ok"] is True, payload["checks"]
    assert all(payload["checks"].values())
