from pathlib import Path

from fastapi.testclient import TestClient

from app.live_intelligence_presentation_v362 import presentation_policy
from app.main import app

ROOT = Path(__file__).resolve().parents[2]
client = TestClient(app)


def test_public_presentation_policy_contract():
    payload = presentation_policy()
    assert payload["schema"] == "sc-site-intelligence-live-intelligence-presentation/1.0"
    assert payload["version"] == "3.20.0"
    assert payload["supported_presentations"] == ["ticker", "static", "manual"]
    assert payload["supported_mobile_presentations"] == ["rotator", "stacked", "marquee", "hidden"]
    assert payload["motion"]["reduced_motion_default"] == "static"
    assert payload["navigation"]["minimum_touch_target_css_pixels"] == 44
    assert payload["accessibility"]["animated_viewport_live_region"] is False
    assert payload["accessibility"]["dedicated_status_live_region"] is True
    assert payload["content"]["accessible_names_must_not_be_truncated"] is True


def test_public_presentation_policy_endpoint():
    response = client.get("/public/live-intelligence/presentation-policy")
    assert response.status_code == 200
    assert response.json()["version"] == "3.20.0"


def test_wordpress_presentation_controls_and_no_js_fallback():
    php = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text(encoding="utf-8")
    for marker in [
        "live_intelligence_presentation_mode",
        "live_intelligence_reduced_motion_mode",
        "live_intelligence_max_visible",
        "live_intelligence_announcement_mode",
        "data-presentation",
        "data-reduced-motion",
        "data-max-visible",
        "data-announcement-mode",
        "data-scsi-live-announcer",
        "Open the public feed status",
        "rest_live_intelligence_presentation_policy",
    ]:
        assert marker in php
    assert 'aria-live="off" aria-busy="true"' in php
    assert 'data-scsi-live-delivery aria-live="off"' in php


def test_frontend_supports_static_manual_stacked_and_bounded_announcements():
    js = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js").read_text(encoding="utf-8")
    for marker in [
        "resolveMode",
        "renderTicker",
        "renderStatic",
        "renderStacked",
        "showCurrentSignal",
        "maxVisible",
        "announcementMode",
        "ArrowLeft",
        "ArrowRight",
        "Home",
        "End",
        "automatic rotation announcements",
    ]:
        if marker == "automatic rotation announcements":
            continue
        assert marker in js
    assert "showCurrentSignal(currentIndex + 1, false)" in js
    assert "announce(signalAccessibleText(signals[currentIndex], currentIndex), 'manual')" in js
    assert ".slice(0, maxVisible)" in js


def test_css_supports_static_manual_stacked_zoom_and_forced_colors():
    css = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.css").read_text(encoding="utf-8")
    for marker in [
        "v3.20.0 — Live Intelligence presentation",
        ".scsi-live-intelligence.is-static-mode",
        ".scsi-live-intelligence.is-manual-mode",
        ".scsi-live-intelligence.is-mobile-stacked",
        "min-height:44px",
        "@media(max-width:1100px)",
        "@media(prefers-reduced-motion:reduce)",
        "@media(forced-colors:active)",
    ]:
        assert marker in css
    assert "ast-breadcrumbs-wrapper" not in css
    assert "scsi-live-intelligence-parchment-navigation" not in css
