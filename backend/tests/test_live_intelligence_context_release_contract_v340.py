from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]


def test_v340_release_markers_and_wordpress_context_routes():
    checks = {
        "backend/app/version.py": ['APP_VERSION = "3.7.0"'],
        "backend/app/live_intelligence_context_v340.py": [
            "build_signal_context", "build_signal_evidence", "render_signal_context_html",
            "canonical_digest", "term overlap", "independent verification",
        ],
        "backend/app/main.py": [
            "/public/live-intelligence/context-policy", "/public/live-intelligence/signals/{signal_id}",
            "public_live_intelligence_signal_context_view_endpoint",
        ],
        "backend/app/live_intelligence_v314.py": [
            "signal_context_supported", "signal_evidence_download_supported", "enrich_signal_links",
        ],
        "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php": [
            "Version: 3.7.0", "scsi_live_signal", "render_live_intelligence_signal_page",
            "live_intelligence_detail_links", "Send to Decision Studio",
        ],
        "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js": [
            "data-scsi-signal-id", "contextBase", "sc_live_intelligence_context_open",
        ],
        "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.css": [
            "scsi-live-signal-context", "scsi-live-signal-button",
        ],
        "README.md": ["v3.7.0 — Signal Context and Drill-Down"],
        "RELEASE_NOTES_SITE_INTELLIGENCE_V340.md": ["Source lineage", "SHA-256", "Decision Studio"],
    }
    for relative, markers in checks.items():
        text = (ROOT / relative).read_text()
        for marker in markers:
            assert marker in text, f"{relative} missing {marker}"


def test_v340_policy_preserves_existing_live_intelligence_and_theme_boundaries():
    policy = json.loads((ROOT / "docs/RELEASE_MANIFEST_V340.json").read_text())
    for key in [
        "public_signal_context", "source_lineage", "signal_timeline",
        "map_context_when_coordinates_exist", "downloadable_evidence_records",
        "canonical_sha256_digest", "wordpress_signal_detail_routes",
        "site_intelligence_handoff", "decision_studio_handoff",
        "feed_controls_preserved", "source_operations_preserved",
        "event_clustering_preserved", "transparent_ranking_preserved",
        "mobile_rotator_preserved", "placement_reliability_preserved",
        "theme_navigation_styles_untouched", "breadcrumb_styles_untouched",
    ]:
        assert policy[key] is True
    for key in [
        "independent_verification_claimed", "causal_inference", "geographic_precision_inflation",
        "automatic_publication", "truth_certification", "browser_api_keys_exposed",
    ]:
        assert policy[key] is False


def test_no_navigation_or_breadcrumb_color_override_reintroduced():
    css = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.css").read_text()
    assert "ast-breadcrumbs-wrapper" not in css
    assert "scsi-live-intelligence-parchment-navigation" not in css
