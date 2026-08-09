from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

ROOT = Path(__file__).resolve().parents[2]
client = TestClient(app)


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_release_identity_and_cartography_assets_are_current():
    assert 'APP_VERSION = "4.11.0"' in read("backend/app/version.py")
    html = read("backend/public_app/index.html")
    assert 'data-scsi-release="4.11.0"' in html
    assert 'data-map-runtime="vector-cartography-engine"' in html
    assert "/app/assets/vector-cartography-v3230.css?v=4.11.0" in html
    assert "/app/assets/vector-cartography-v3230.js?v=4.11.0" in html
    assert html.index("vector-cartography-v3230.js") < html.index("service-recovery-v3224.js") < html.index("runtime-v3230.js") < html.index("app.js")


def test_local_vector_geography_has_labels_ranks_and_country_identity():
    payload = json.loads(read("backend/public_app/assets/world-cartography-v3230.geojson"))
    assert payload["type"] == "FeatureCollection"
    assert payload["version"] == "4.11.0"
    assert len(payload["features"]) >= 170
    for feature in payload["features"]:
        props = feature["properties"]
        assert props.get("name")
        assert props.get("iso_a3") is not None
        assert isinstance(props.get("label_lat"), (int, float))
        assert isinstance(props.get("label_lng"), (int, float))
        assert 1 <= int(props.get("label_rank")) <= 5
        assert props.get("cartography_class")


def test_engine_renders_vector_labels_scale_coordinates_and_layer_roles():
    engine = read("backend/public_app/assets/vector-cartography-v3230.js")
    for token in (
        "class SelfHostedTileLayer",
        "scsi-country-labels",
        "scsi-country-label",
        "scsi-map-scale",
        "scsi-map-coordinate-readout",
        "visibleGeography",
        "visibleLabels",
        'this.options.role ||',
        '"vector-plus-satellite"',
        'libraryMode: "vector-cartography-engine"',
        "satelliteComposition: true",
    ):
        assert token in engine
    assert "world-cartography-v3230.geojson" in engine


def test_satellite_layers_are_composed_above_the_basemap():
    app_js = read("backend/public_app/assets/app.js")
    wordpress_js = read("wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js")
    assert 'role:"imagery",layerId:id' in app_js
    assert "state.imagery.bringToFront()" in app_js
    assert "thematicState.imagery.bringToFront()" in app_js
    assert 'role:"imagery",layerId:id' in wordpress_js
    assert "currentRaster.bringToFront()" in wordpress_js
    assert "currentRaster.bringToBack()" not in wordpress_js


def test_cartographic_css_removes_black_globe_mask_and_improves_hierarchy():
    css = read("backend/public_app/assets/vector-cartography-v3230.css")
    app_css = read("backend/public_app/assets/app.css")
    for token in (
        ".scsi-map-tile-layer--base",
        ".scsi-map-tile-layer--imagery",
        ".scsi-country-shape",
        ".scsi-country-label",
        ".scsi-map-scale",
        ".scsi-map-coordinate-readout",
    ):
        assert token in css
    assert ".orbital-glow,.map-vignette{display:none!important}" in app_css
    assert "min-height:520px" in app_css


def test_runtime_health_requires_vector_cartography_assets():
    response = client.get("/public/runtime-health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    paths = {item["path"] for item in payload["assets"]}
    assert "/app/assets/vector-cartography-v3230.js" in paths
    assert "/app/assets/vector-cartography-v3230.css" in paths
    assert "/app/assets/world-cartography-v3230.geojson" in paths
    assert "/app/assets/runtime-v3230.js" in paths


def test_wordpress_packages_the_same_cartography_runtime_and_release():
    php = read("wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php")
    assert "Version: 4.11.0" in php
    assert "vector-cartography-v3230.js" in php
    assert "vector-cartography-v3230.css" in php
    assert "world-cartography-v3230.geojson" in php
    for name in ("vector-cartography-v3230.js", "vector-cartography-v3230.css", "world-cartography-v3230.geojson"):
        assert (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/assets" / name).is_file()


def test_service_worker_and_promotion_gate_verify_live_cartography():
    worker = read("backend/public_app/service-worker.js")
    promote = read("promote_site_intelligence_v3_22_9_to_github_and_render_macos.sh")
    assert 'const RELEASE="4.11.0"' in worker
    for name in ("vector-cartography-v3230.js", "vector-cartography-v3230.css", "world-cartography-v3230.geojson", "runtime-v3230.js"):
        assert name in worker
    assert "/app/assets/vector-cartography-v3230.js" in promote
    assert "/app/assets/world-cartography-v3230.geojson" in promote
    assert "/public/runtime-health" in promote


def test_current_release_validation_and_browser_smoke_are_present():
    assert (ROOT / "verify_site_intelligence_v3_22_9_macos.sh").is_file()
    assert (ROOT / "promote_site_intelligence_v3_22_9_to_github_and_render_macos.sh").is_file()
    smoke = read("scripts/browser_smoke_v3229.py")
    assert "vector-cartography-v3230.js" in smoke
    assert "tileRoles" in smoke
    assert "unique_colors" in smoke
    assert "dark_ratio" in smoke
