from pathlib import Path

from fastapi.testclient import TestClient

from app import main as main_module
from app.main import app

ROOT = Path(__file__).resolve().parents[2]
client = TestClient(app)


def test_first_party_map_runtime_loads_before_application_without_blocking_cdn():
    html = (ROOT / "backend/public_app/index.html").read_text(encoding="utf-8")
    runtime = html.index("/app/assets/vector-cartography-v3230.js")
    application = html.index('src="/app/assets/app.js?v=4.35.18" defer')
    assert runtime < application
    assert "unpkg.com/leaflet" not in html
    assert "cdn.jsdelivr.net/npm/leaflet" not in html
    assert "/app/assets/vector-cartography-v3230.css" in html


def test_map_runtime_assets_are_first_party_and_offline_cached():
    js_response = client.get("/app/assets/vector-cartography-v3230.js")
    css_response = client.get("/app/assets/vector-cartography-v3230.css")
    worker = (ROOT / "backend/public_app/service-worker.js").read_text(encoding="utf-8")
    assert js_response.status_code == css_response.status_code == 200
    assert "SCSIMapReliability" in js_response.text
    assert "vector-cartography-engine" in js_response.text
    assert "__scsiFirstParty" in js_response.text
    assert "vector-cartography-v3230.js" in worker
    assert "vector-cartography-v3230.css" in worker


def test_spatial_evidence_has_a_real_map_surface_and_geometry_renderer():
    html = (ROOT / "backend/public_app/index.html").read_text(encoding="utf-8")
    js = (ROOT / "backend/public_app/assets/spatial-v2150.js").read_text(encoding="utf-8")
    css = (ROOT / "backend/public_app/assets/spatial-v2150.css").read_text(encoding="utf-8")
    assert 'id="spatialEvidenceMap"' in html
    assert "L.geoJSON" in js
    assert "renderEvidence" in js
    assert "/public/geospatial/events" in js
    assert ".spatial-map" in css


def test_embeddable_app_uses_csp_without_conflicting_frame_header(monkeypatch):
    monkeypatch.setattr(main_module.settings, "public_embeds_enabled", True)
    monkeypatch.setattr(main_module.settings, "public_embed_allowed_origins", "https://partner.example")
    response = client.get("/app/")
    assert response.status_code == 200
    assert "x-frame-options" not in response.headers
    assert "frame-ancestors 'self'" in response.headers["content-security-policy"]
    assert "https://partner.example" in response.headers["content-security-policy"]


def test_non_embeddable_app_keeps_same_origin_frame_protection(monkeypatch):
    monkeypatch.setattr(main_module.settings, "public_embeds_enabled", False)
    response = client.get("/app/")
    assert response.status_code == 200
    assert response.headers["x-frame-options"] == "SAMEORIGIN"
    assert response.headers["content-security-policy"] == "frame-ancestors 'self'"


def test_wordpress_map_loader_is_first_party_and_dependency_ordered():
    php = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text(encoding="utf-8")
    js = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js").read_text(encoding="utf-8")
    assert "mapEngineUrl" in php and "vector-cartography-v3230.js" in php
    assert "function loadSelfHostedMapEngine" in js
    assert "return loadSelfHostedMapEngine();" in js
    assert "unpkg.com/leaflet" not in js
    assert "wp_enqueue_script('scsi-map-engine'" in php
    assert "['scsi-map-engine']" in php
