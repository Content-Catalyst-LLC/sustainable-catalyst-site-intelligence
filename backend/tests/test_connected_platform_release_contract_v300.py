from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_public_app_contains_connected_platform_workspace():
    html = (ROOT / "backend/public_app/index.html").read_text(encoding="utf-8")
    assert 'data-route="platform"' in html
    assert 'id="connectedPlatformStudio"' in html
    assert '/app/assets/platform-v300.css?v=3.15.0' in html
    assert '/app/assets/platform-v300.js?v=3.15.0' in html


def test_service_worker_caches_connected_platform_assets():
    worker = (ROOT / "backend/public_app/service-worker.js").read_text(encoding="utf-8")
    assert 'const RELEASE="3.15.0"' in worker
    assert 'platform-v300.css' in worker
    assert 'platform-v300.js' in worker


def test_wordpress_plugin_exposes_connected_platform_shortcodes():
    php = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text(encoding="utf-8")
    assert "Version: 3.15.0" in php
    assert "sc_connected_public_intelligence" in php
    assert "sc_connected_intelligence_control_center" in php
    assert "admin/connected-intelligence/control-center" in php


def test_connected_platform_policy_exists_and_is_current():
    import json
    policy = json.loads((ROOT / "backend/data/connected_platform_policy_v300.json").read_text(encoding="utf-8"))
    assert policy["version"] == "3.15.0"
    assert policy["public_index"]["private_records_excluded"] is True
    assert policy["governance"]["graph_proximity_implies_causation"] is False
