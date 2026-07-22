from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]


def test_v3140_release_contract():
    requirements = {
        "backend/app/version.py": ['APP_VERSION = "3.17.0"'],
        "backend/app/live_intelligence_change_history_v3140.py": [
            "class LiveIntelligenceChangeHistoryCenter", "def prepare_notice(",
            "def approve_notice(", "def release_lineage(", "def package_payload(",
            "original_release_retained", "append_only_history", "deletion_performed",
        ],
        "backend/app/main.py": [
            "/public/live-intelligence/change-history/policy",
            "/public/live-intelligence/change-history/status",
            "/public/live-intelligence/change-history/releases/{release_id}",
            "/admin/live-intelligence/change-history/notices",
        ],
        "backend/app/config.py": [
            "live_intelligence_change_history_enabled",
            "live_intelligence_change_history_notices_path",
            "live_intelligence_change_history_require_separation_of_duties",
        ],
        "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php": [
            "Version: 3.17.0", "sc_live_intelligence_change_history",
            "rest_live_intelligence_change_history_status",
        ],
        "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js": [
            "setupLiveIntelligenceChangeHistory", "Original release retained", "No destination deletion",
        ],
        "README.md": ["v3.17.0 — Corrections, Retractions, and Public Change History"],
        "RELEASE_NOTES_SITE_INTELLIGENCE_V3140.md": ["Corrections, Retractions", "append-only", "original release"],
        "docs/RELEASE_MANIFEST_V3140.json": ['"version": "3.17.0"', '"deletion_performed": false'],
        "docs/live-intelligence-change-history-v3140.schema.json": ["Live Intelligence Public Change History", '"additionalProperties": false'],
    }
    for relative, needles in requirements.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        for needle in needles:
            assert needle in text, f"{needle!r} missing from {relative}"
