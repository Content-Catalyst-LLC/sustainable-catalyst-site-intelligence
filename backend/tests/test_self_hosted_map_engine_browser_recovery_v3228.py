from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

ROOT = Path(__file__).resolve().parents[2]
client = TestClient(app)


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_self_hosted_engine_replaces_false_positive_tile_stub():
    engine = read("backend/public_app/assets/vector-cartography-v3230.js")
    assert "class SelfHostedTileLayer" in engine
    assert 'document.createElement("img")' in engine
    assert "world-cartography-v3230.geojson" in engine
    assert "__scsiSelfHosted: true" in engine
    assert "self-hosted-vector-cartography" in engine
    assert "applicationHealthy: true" in engine
    assert "setTimeout(() => this._emit(\"load\"), 0)" not in engine


def test_local_world_boundary_asset_is_real_and_publicly_served():
    path = ROOT / "backend/public_app/assets/world-cartography-v3230.geojson"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["type"] == "FeatureCollection"
    assert len(payload["features"]) >= 170
    response = client.get("/app/assets/world-cartography-v3230.geojson")
    assert response.status_code == 200
    assert len(response.json()["features"]) >= 170


def test_application_loads_engine_before_all_map_modules():
    html = read("backend/public_app/index.html")
    engine = html.index("/app/assets/vector-cartography-v3230.js?v=4.35.12")
    recovery = html.index("/app/assets/service-recovery-v3224.js?v=4.35.12")
    runtime = html.index("/app/assets/runtime-v3230.js?v=4.35.12")
    application = html.index("/app/assets/app.js?v=4.35.12")
    assert engine < recovery < runtime < application
    assert 'data-map-runtime="vector-cartography-engine"' in html


def test_runtime_health_separates_optional_imagery_from_application_health():
    runtime = read("backend/public_app/assets/runtime-v3230.js")
    engine = read("backend/public_app/assets/vector-cartography-v3230.js")
    assert "activeErrorCount" in runtime
    assert "resolveErrors" in runtime
    assert 'element.dataset.scsiMapStatus === "failed"' in runtime
    assert "imageryLimitedCount" in runtime
    assert 'container.dataset.scsiMapStatus = "ready"' in engine
    assert 'container.dataset.scsiImageryMode = "limited"' in engine


def test_service_worker_uses_network_first_for_versioned_map_assets():
    worker = read("backend/public_app/service-worker.js")
    assert 'const RELEASE="4.35.12"' in worker
    assert "vector-cartography-v3230.js" in worker
    assert "world-cartography-v3230.geojson" in worker
    assert "networkFirstShell" in worker
    assert "staleWhileRevalidate" not in worker


def test_wordpress_embeds_force_release_parity_and_bundle_same_engine():
    php = read("wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php")
    js = read("wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js")
    assert "vector-cartography-v3230.js" in php
    assert "world-cartography-v3230.geojson" in php
    assert "'release' => self::VERSION" in php
    assert 'data-scsi-release="%5$s"' in php
    assert "observedVersion !== expectedVersion" in js
    assert "cache_bust" in js
    assert (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/world-cartography-v3230.geojson").is_file()


def test_runtime_contract_reports_local_vector_basemap():
    response = client.get("/public/runtime-health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    paths = {item["path"] for item in payload["assets"]}
    assert "/app/assets/vector-cartography-v3230.js" in paths
    assert "/app/assets/world-cartography-v3230.geojson" in paths
    assert payload["recovery_policy"]["map_engine"].startswith("Use the vector cartography engine")

def test_current_release_scripts_are_unambiguous():
    assert (ROOT / "verify_site_intelligence_v3_22_9_macos.sh").is_file()
    assert (ROOT / "promote_site_intelligence_v3_22_9_to_github_and_render_macos.sh").is_file()
    assert not (ROOT / "verify_site_intelligence_v3_22_7_macos.sh").exists()
    assert not (ROOT / "promote_site_intelligence_v3_22_7_to_github_and_render_macos.sh").exists()


def test_current_release_documentation_is_present():
    for name in (
        "RELEASE_NOTES_SITE_INTELLIGENCE_V3229.md",
        "SITE_INTELLIGENCE_V3229_CARTOGRAPHY_AUDIT.md",
        "SITE_INTELLIGENCE_V3229_INSTALL_AND_TEST.md",
        "SITE_INTELLIGENCE_V3229_TERMINAL_COMMANDS.txt",
        "SITE_INTELLIGENCE_V3229_BUILD_VALIDATION.txt",
    ):
        assert (ROOT / name).is_file(), name


def test_live_promotion_verifies_rendered_geography_and_runtime_health():
    script = (ROOT / "promote_site_intelligence_v3_22_9_to_github_and_render_macos.sh").read_text(encoding="utf-8")
    assert "/app/?release=${RELEASE}" in script
    assert "/app/assets/vector-cartography-v3230.js" in script
    assert "/app/assets/world-cartography-v3230.geojson" in script
    assert "len(d.get(\"features\",[]))>=170" in script
    assert "/public/runtime-health" in script
    assert "world_ready" in script


def test_world_boundary_metadata_and_geometry_contract():
    payload = json.loads((ROOT / "backend/public_app/assets/world-cartography-v3230.geojson").read_text(encoding="utf-8"))
    assert payload["type"] == "FeatureCollection"
    assert len(payload["features"]) >= 170
    geometries = {feature.get("geometry", {}).get("type") for feature in payload["features"]}
    assert geometries <= {"Polygon", "MultiPolygon"}

