from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
requirements = {
    "backend/app/version.py": ['APP_VERSION = "3.19.0"'],
    "backend/app/live_intelligence_change_history_v3140.py": [
        "POLICY_SCHEMA_VERSION", "NOTICE_SCHEMA_VERSION", "HANDOFF_SCHEMA_VERSION",
        "class LiveIntelligenceChangeHistoryCenter", "def prepare_notice(",
        "def approve_notice(", "def public_history(", "def release_lineage(",
        "def package_payload(", "def create_handoff(", "original_release_retained",
        "append_only_history", "destination_write_performed", "deletion_performed",
    ],
    "backend/app/main.py": [
        "/public/live-intelligence/change-history/policy",
        "/public/live-intelligence/change-history/status",
        "/public/live-intelligence/change-history/releases/{release_id}",
        "/admin/live-intelligence/change-history/notices",
        "/approve", "/package", "/handoffs", "/history",
    ],
    "backend/app/config.py": [
        "live_intelligence_change_history_enabled",
        "live_intelligence_change_history_notices_path",
        "live_intelligence_change_history_events_path",
        "live_intelligence_change_history_handoffs_path",
        "live_intelligence_change_history_require_separation_of_duties",
    ],
    "backend/.env.example": [
        "SC_SI_LIVE_INTELLIGENCE_CHANGE_HISTORY_ENABLED",
        "SC_SI_LIVE_INTELLIGENCE_CHANGE_HISTORY_NOTICES_PATH",
        "SC_SI_LIVE_INTELLIGENCE_CHANGE_HISTORY_REQUIRE_SEPARATION_OF_DUTIES",
    ],
    "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php": [
        "Version: 3.19.0", "sc_live_intelligence_change_history",
        "rest_live_intelligence_change_history_policy",
        "rest_live_intelligence_change_history_status",
        "preserves the original record",
    ],
    "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js": [
        "setupLiveIntelligenceChangeHistory", "Original release retained", "No destination deletion",
    ],
    "README.md": ["v3.19.0 — Corrections, Retractions, and Public Change History"],
    "RELEASE_NOTES_SITE_INTELLIGENCE_V3140.md": ["Corrections, Retractions", "append-only", "original release"],
    "docs/RELEASE_MANIFEST_V3140.json": [
        '"version": "3.19.0"', '"original_release_retained": true',
        '"append_only_history": true', '"deletion_performed": false',
    ],
    "docs/live-intelligence-change-history-v3140.schema.json": [
        "Live Intelligence Public Change History", "affected_release_sha256", '"additionalProperties": false',
    ],
}
for relative, needles in requirements.items():
    path = ROOT / relative
    if not path.exists():
        raise SystemExit(f"Missing required release file: {relative}")
    text = path.read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"Missing {needle!r} in {relative}")
print("Site Intelligence v3.19.0 release contract passed.")
