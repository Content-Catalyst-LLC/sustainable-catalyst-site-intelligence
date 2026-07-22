from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]


def test_v350_release_markers_and_wordpress_channel_controls():
    checks = {
        "backend/app/version.py": ['APP_VERSION = "3.18.0"'],
        "backend/app/live_intelligence_channels_v350.py": [
            "CHANNEL_REGISTRY", "channel_directory", "filter_channel_signals",
            "silent_global_fallback", "country_parameter_supported",
        ],
        "backend/app/main.py": [
            "/public/live-intelligence/channels", "/public/live-intelligence/channel-policy",
            "public_live_intelligence_channel_feed_endpoint",
        ],
        "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php": [
            "Version: 3.18.0", "live_intelligence_channel", "live_intelligence_region",
            "live_intelligence_country", "rest_live_intelligence_channels",
        ],
        "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js": [
            "root.dataset.channel", "params.set('region'", "params.set('country'",
        ],
        "README.md": ["v3.18.0 — Topic and Regional Channels"],
        "RELEASE_NOTES_SITE_INTELLIGENCE_V350.md": ["Topic channels", "Regional channels", "empty"],
    }
    for relative, markers in checks.items():
        text = (ROOT / relative).read_text()
        for marker in markers:
            assert marker in text, f"{relative} missing {marker}"


def test_v350_policy_preserves_existing_features_and_theme_boundaries():
    policy = json.loads((ROOT / "docs/RELEASE_MANIFEST_V350.json").read_text())
    for key in [
        "topic_channels", "regional_channels", "country_filters", "channel_directory",
        "shortcode_channel_overrides", "empty_result_honesty", "feed_controls_preserved",
        "source_operations_preserved", "event_clustering_preserved", "transparent_ranking_preserved",
        "signal_context_preserved", "mobile_rotator_preserved", "placement_reliability_preserved",
        "theme_navigation_styles_untouched", "breadcrumb_styles_untouched",
    ]:
        assert policy[key] is True
    for key in [
        "silent_global_fallback", "coordinate_only_country_inference", "geopolitical_judgment",
        "truth_certification", "browser_api_keys_exposed",
    ]:
        assert policy[key] is False


def test_theme_color_boundaries_remain_untouched():
    css = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.css").read_text()
    assert "ast-breadcrumbs-wrapper" not in css
    assert "scsi-live-intelligence-parchment-navigation" not in css
