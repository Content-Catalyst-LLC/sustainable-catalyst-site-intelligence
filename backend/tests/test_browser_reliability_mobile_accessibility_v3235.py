from __future__ import annotations

from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app

ROOT = Path(__file__).resolve().parents[2]
CLIENT = TestClient(app)


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_browser_reliability_contract_is_public_and_bounded():
    response = CLIENT.get("/public/browser-reliability")
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["version"] == "4.27.0"
    assert payload["release_id"] == "site-intelligence-v4.27.0"
    assert payload["contract"] == "browser-reliability-mobile-accessibility"
    assert len(payload["supported_browsers"]) == 4
    assert {row["id"] for row in payload["viewport_profiles"]} == {"phone", "tablet", "desktop"}
    assert payload["accessibility"]["minimum_touch_target_px"] == 44
    assert payload["boundaries"]["user_agent_blocking"] is False


def test_accessibility_contract_covers_keyboard_motion_maps_and_focus():
    payload = CLIENT.get("/public/browser-reliability").json()
    accessibility = payload["accessibility"]
    for key in (
        "keyboard_routes",
        "route_focus_management",
        "dialog_focus_containment",
        "focus_restoration",
        "map_text_summaries",
        "reduced_motion",
        "forced_colors",
        "live_region_updates",
    ):
        assert accessibility[key] is True


def test_reliability_contract_covers_mobile_and_long_sessions():
    payload = CLIENT.get("/public/browser-reliability").json()
    reliability = payload["reliability"]
    assert reliability["resize_recovery"] is True
    assert reliability["orientation_recovery"] is True
    assert reliability["visibility_recovery"] is True
    assert reliability["low_bandwidth_mode"] is True
    assert reliability["optional_imagery_suppressed_in_low_bandwidth"] is True
    assert reliability["long_session_heartbeat_seconds"] == 30


def test_app_shell_orders_browser_reliability_inside_the_application():
    html = read("backend/public_app/index.html")
    assert "/app/assets/browser-reliability-v3235.css?v=4.27.0" in html
    assert "/app/assets/browser-reliability-v3235.js?v=4.27.0" in html
    assert html.index("analytical-workspaces-v3234.js") < html.index("browser-reliability-v3235.js") < html.index("data-truth-v32371.js")
    js = read("backend/public_app/assets/browser-reliability-v3235.js")
    for token in (
        "scsi:browser-reliability-ready",
        "scsi:viewport-recovery",
        "scsi-map-summary",
        "prefers-reduced-motion",
        "insideApp",
        "Low-bandwidth mode",
    ):
        assert token in js


def test_service_worker_runtime_health_and_wordpress_package_assets():
    worker = read("backend/public_app/service-worker.js")
    assert 'const RELEASE="4.27.0"' in worker
    assert "browser-reliability-v3235.js" in worker
    assert "browser-reliability-v3235.css" in worker
    health = CLIENT.get("/public/runtime-health").json()
    assets = {row["path"] for row in health["assets"]}
    endpoints = {row["path"] for row in health["endpoint_contracts"]}
    assert "/app/assets/browser-reliability-v3235.js" in assets
    assert "/app/assets/browser-reliability-v3235.css" in assets
    assert "/public/browser-reliability" in endpoints
    php = read("wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php")
    assert "Version: 4.27.0" in php
    assert "browserReliabilityJsUrl" in php
    assert "wp_enqueue_script('scsi-browser-reliability'" not in php
    assert (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/browser-reliability-v3235.js").is_file()


def test_css_declares_phone_touch_reduced_motion_and_forced_colors_rules():
    css = read("backend/public_app/assets/browser-reliability-v3235.css")
    for token in (
        "--scsi-touch-target:44px",
        'data-scsi-viewport="phone"',
        "prefers-reduced-motion:reduce",
        "forced-colors:active",
        'data-scsi-input="coarse"',
        'data-scsi-low-bandwidth="true"',
    ):
        assert token in css
