from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]


def test_v330_release_contract_files_and_markers():
    checks = {
        "backend/app/live_intelligence_clustering_v330.py": [
            "cluster_event_records", "select_ranked_signals", "selection_reasons",
            "corroboration", "Scores rank display relevance",
        ],
        "backend/app/live_intelligence_v314.py": [
            "event_clustering_supported", "transparent_ranking_supported",
            "policy_url", "cluster_source_count",
        ],
        "backend/app/main.py": ["/public/live-intelligence/ranking-policy"],
        "backend/app/config.py": [
            "live_intelligence_clustering_enabled", "live_intelligence_ranking_enabled",
            "live_intelligence_cluster_time_window_hours",
        ],
        "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js": [
            "cluster_source_count", "selection_reasons", "Selected because:",
        ],
        "README.md": ["v3.3.0 — Event Clustering and Intelligence Ranking"],
        "RELEASE_NOTES_SITE_INTELLIGENCE_V330.md": [
            "canonical event", "selection reasons", "display relevance",
        ],
    }
    for relative, markers in checks.items():
        text = (ROOT / relative).read_text()
        for marker in markers:
            assert marker in text, f"{relative} missing {marker}"


def test_v330_policy_preserves_safety_and_existing_ticker_boundaries():
    policy = json.loads((ROOT / "docs/RELEASE_MANIFEST_V330.json").read_text())
    for key in [
        "event_clustering", "cross_source_duplicate_suppression", "canonical_event_records",
        "transparent_ranking", "selection_reason_explanations", "category_diversity",
        "source_caps_preserved", "feed_controls_preserved", "mobile_rotator_preserved",
        "placement_reliability_preserved", "theme_navigation_styles_untouched",
        "breadcrumb_styles_untouched",
    ]:
        assert policy[key] is True
    for key in [
        "truth_scoring", "danger_scoring", "automatic_accuracy_certification",
        "causal_inference", "browser_api_keys_exposed",
    ]:
        assert policy[key] is False
