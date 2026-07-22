from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_v2150_policy_and_catalog_define_spatial_governance():
    policy = json.loads((ROOT / "backend/data/spatial_evidence_policy_v2150.json").read_text(encoding="utf-8"))
    catalog = json.loads((ROOT / "backend/data/spatial_layer_catalog_v2150.json").read_text(encoding="utf-8"))
    assert policy["schema"] == "sc-site-intelligence-spatial-evidence/1.0"
    assert policy["version"] == "3.20.0"
    assert policy["public_raw_private_dataset_access"] is False
    assert policy["paid_gis_server_required"] is False
    assert len(catalog["layers"]) >= 6
    assert any("military targeting" in item for item in policy["responsible_use"])


def test_v2150_wordpress_and_backend_publish_spatial_surfaces():
    main = (ROOT / "backend/app/main.py").read_text(encoding="utf-8")
    plugin = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text(encoding="utf-8")
    js = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js").read_text(encoding="utf-8")
    for marker in ["/public/spatial", "/admin/spatial/control-center", "/admin/spatial/analyze/intersection", "/admin/spatial/analyze/compare"]:
        assert marker in main
    assert "Version: 3.20.0" in plugin
    assert "sc_public_spatial_evidence" in plugin
    assert "sc_spatial_evidence_control_center" in plugin
    assert "public-spatial-evidence" in plugin
    assert "spatial-evidence" in js


def test_v2150_runtime_spatial_state_is_excluded_from_source_release():
    assert not (ROOT / "backend/data/spatial_evidence_v2150").exists()
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "backend/data/spatial_evidence_v2150/" in gitignore


def test_v2150_public_application_registers_spatial_workspace_and_offline_assets():
    index = (ROOT / "backend/public_app/index.html").read_text(encoding="utf-8")
    app = (ROOT / "backend/public_app/assets/app.js").read_text(encoding="utf-8")
    worker = (ROOT / "backend/public_app/service-worker.js").read_text(encoding="utf-8")
    spatial_js = (ROOT / "backend/public_app/assets/spatial-v2150.js").read_text(encoding="utf-8")
    spatial_css = (ROOT / "backend/public_app/assets/spatial-v2150.css").read_text(encoding="utf-8")
    assert 'data-route="spatial"' in index
    assert 'id="spatialEvidenceStudio"' in index
    assert '/app/assets/spatial-v2150.js?v=3.20.0' in index
    assert 'spatial:[' in app
    assert 'SCSpatialV2150' in app
    assert '/app/assets/spatial-v2150.js' in worker
    assert '/app/assets/spatial-v2150.css' in worker
    assert 'window.SCSpatialV2150' in spatial_js
    assert '.spatial-evidence-studio' in spatial_css
