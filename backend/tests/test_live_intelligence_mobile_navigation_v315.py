from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]


def test_mobile_navigation_contract():
    php = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text()
    js = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js").read_text()
    css = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.css").read_text()
    for marker in ["live_intelligence_mobile_mode", "live_intelligence_mobile_interval", "scsi-live-intelligence__previous", "scsi-live-intelligence__next", "scsi-live-intelligence__position"]:
        assert marker in php
    for marker in ["showMobileSignal", "startRotation", "touchstart", "touchend", "finePointer", "reducedMotion"]:
        assert marker in js
    for marker in ["is-mobile-rotator", "data-mobile-mode=\"hidden\"", "scsi-live-intelligence__mobile-controls"]:
        assert marker in css


def test_mobile_policy_is_explicit():
    policy = json.loads((ROOT / "docs/RELEASE_MANIFEST_V315.json").read_text())
    assert policy["default_mobile_mode"] == "rotator"
    assert policy["previous_next_controls"] is True
    assert policy["swipe_navigation"] is True
    assert policy["reduced_motion_disables_auto_advance"] is True
    assert policy["touch_hover_pause_prevented"] is True


def test_touch_hover_is_gated_to_fine_pointers():
    css = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.css").read_text()
    js = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js").read_text()
    assert "@media(hover:hover) and (pointer:fine)" in css
    assert "if (finePointer.matches)" in js


def test_theme_surfaces_remain_untouched():
    css = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.css").read_text()
    assert "scsi-live-intelligence-parchment-navigation" not in css
    assert "ast-breadcrumbs-wrapper" not in css
