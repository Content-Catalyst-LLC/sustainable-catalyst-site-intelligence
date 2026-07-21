from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]


def test_v362_release_contract_files_and_markers():
    checks = {
        "backend/app/live_intelligence_presentation_v362.py": ["PRESENTATION_SCHEMA", "presentation_policy", "animated_viewport_live_region"],
        "backend/app/main.py": ["/public/live-intelligence/presentation-policy", "public_live_intelligence_presentation_policy_endpoint"],
        "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php": ["Version: 3.13.0", "live_intelligence_reduced_motion_mode", "data-scsi-live-announcer"],
        "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js": ["renderStatic", "renderStacked", "signalAccessibleText", "ArrowRight"],
        "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.css": ["v3.13.0 — Live Intelligence presentation", "is-mobile-stacked", "min-height:44px"],
        "docs/V362_LIVE_INTELLIGENCE_PRESENTATION_ACCESSIBILITY.md": ["Motion is optional", "Screen-reader announcements"],
    }
    for relative, markers in checks.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        for marker in markers:
            assert marker in text, f"{relative} is missing {marker}"


def test_v362_policy_preserves_public_interest_and_theme_boundaries():
    policy = json.loads((ROOT / "docs/RELEASE_MANIFEST_V362.json").read_text(encoding="utf-8"))
    for key in [
        "static_administrator_mode",
        "manual_previous_next_mode",
        "reduced_motion_static_or_manual",
        "mobile_stacked_mode",
        "keyboard_navigation",
        "swipe_navigation",
        "minimum_touch_target_44px",
        "bounded_assistive_announcements",
        "full_accessible_names",
        "no_javascript_fallback",
        "theme_navigation_styles_untouched",
        "breadcrumb_styles_untouched",
    ]:
        assert policy[key] is True
    for key in [
        "motion_required_for_access",
        "animated_viewport_live_region",
        "automatic_rotation_announcements",
        "browser_api_keys_exposed",
    ]:
        assert policy[key] is False
