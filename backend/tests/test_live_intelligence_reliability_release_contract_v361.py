from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]


def test_v361_release_contract_files_and_markers():
    checks = {
        "backend/app/live_intelligence_reliability_v361.py": ["RELIABILITY_SCHEMA_VERSION", "LiveIntelligenceReliabilityStore", "classify_signal_freshness"],
        "backend/app/main.py": ["/public/live-intelligence/status"],
        "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php": ["Version: 3.8.0", "live_intelligence_show_freshness"],
        "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js": ["data-scsi-live-delivery", "refreshSeconds"],
        "docs/V361_LIVE_INTELLIGENCE_RELIABILITY.md": ["same channel", "Freshness describes time, not truth"],
    }
    for relative, markers in checks.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        for marker in markers:
            assert marker in text, f"{relative} is missing {marker}"


def test_v361_policy_preserves_public_interest_and_theme_boundaries():
    policy = json.loads((ROOT / "docs/RELEASE_MANIFEST_V361.json").read_text(encoding="utf-8"))
    assert policy["same_query_last_known_good"] is True
    assert policy["honest_empty_geographic_results"] is True
    assert policy["fabricated_replacement_values"] is False
    assert policy["cross_query_cache_reuse"] is False
    css = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.css").read_text(encoding="utf-8")
    assert "ast-breadcrumbs-wrapper" not in css
    assert "scsi-live-intelligence-parchment-navigation" not in css
