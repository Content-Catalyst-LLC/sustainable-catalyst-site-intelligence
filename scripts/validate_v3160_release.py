from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
requirements = {
    "backend/app/version.py": ['APP_VERSION = "3.18.0"'],
    "backend/app/live_intelligence_archive_audits_v3160.py": [
        "POLICY_SCHEMA_VERSION", "AUDIT_SCHEMA_VERSION", "CUSTODY_SCHEMA_VERSION",
        "class LiveIntelligenceArchiveAuditCenter", "def create_audit(", "def run_audit(",
        "def approve_audit(", "def prepare_custody_transfer(", "def verify_custody_transfer(",
        "def approve_custody_transfer(", "def record_custody_receipt(", "def report_payload(",
        "append_only_audit_ledger", "automatic_scheduler_claimed", "remote_deposit_performed",
    ],
    "backend/app/main.py": [
        "/public/live-intelligence/archive-audits/policy", "/public/live-intelligence/archive-audits/status",
        "/public/live-intelligence/archive-audits/custody", "/admin/live-intelligence/archive-audits",
        "/run", "/approve", "/package", "/receipts",
    ],
    "backend/app/config.py": [
        "live_intelligence_archive_audits_enabled", "live_intelligence_archive_audits_path",
        "live_intelligence_archive_audit_events_path", "live_intelligence_archive_custody_path",
        "live_intelligence_archive_audit_require_separation_of_duties",
    ],
    "backend/.env.example": [
        "SC_SI_LIVE_INTELLIGENCE_ARCHIVE_AUDITS_ENABLED",
        "SC_SI_LIVE_INTELLIGENCE_ARCHIVE_AUDITS_PATH",
        "SC_SI_LIVE_INTELLIGENCE_ARCHIVE_AUDIT_REQUIRE_SEPARATION_OF_DUTIES",
    ],
    "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php": [
        "Version: 3.18.0", "sc_live_intelligence_archive_audits",
        "rest_live_intelligence_archive_audit_policy", "rest_live_intelligence_archive_audit_status",
        "no automatic scheduling, remote deposit, archive mutation, or destination write",
    ],
    "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js": [
        "setupLiveIntelligenceArchiveAudits", "Checksum audits", "Manual custody", "No remote deposit",
    ],
    "README.md": ["v3.18.0 — Archive Verification, Preservation Audits, and Institutional Custody"],
    "RELEASE_NOTES_SITE_INTELLIGENCE_V3160.md": ["Archive Verification", "custody", "checksum"],
    "docs/RELEASE_MANIFEST_V3160.json": [
        '"version": "3.18.0"', '"append_only_audit_ledger": true',
        '"automatic_scheduler_claimed": false', '"remote_deposit_performed": false',
    ],
    "docs/live-intelligence-archive-audit-v3160.schema.json": [
        "Live Intelligence Archive Audit", "audit_sha256", '"additionalProperties": false',
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
print("Site Intelligence v3.18.0 release contract passed.")
