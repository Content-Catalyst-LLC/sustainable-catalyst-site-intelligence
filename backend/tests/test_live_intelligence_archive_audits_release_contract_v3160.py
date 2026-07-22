from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]


def test_v3160_release_contract():
    requirements = {
        "backend/app/version.py": ['APP_VERSION = "3.18.0"'],
        "backend/app/live_intelligence_archive_audits_v3160.py": [
            "class LiveIntelligenceArchiveAuditCenter", "def create_audit(", "def run_audit(",
            "def approve_audit(", "def prepare_custody_transfer(", "def verify_custody_transfer(",
            "def approve_custody_transfer(", "def record_custody_receipt(",
            "append_only_audit_ledger", "automatic_scheduler_claimed", "remote_deposit_performed",
        ],
        "backend/app/main.py": [
            "/public/live-intelligence/archive-audits/policy", "/public/live-intelligence/archive-audits/status",
            "/public/live-intelligence/archive-audits/custody", "/admin/live-intelligence/archive-audits",
            "/custody/{transfer_id}/verify", "/custody/{transfer_id}/approve",
        ],
        "backend/app/config.py": [
            "live_intelligence_archive_audits_enabled", "live_intelligence_archive_audits_path",
            "live_intelligence_archive_custody_path", "live_intelligence_archive_audit_require_separation_of_duties",
        ],
        "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php": [
            "Version: 3.18.0", "sc_live_intelligence_archive_audits",
            "rest_live_intelligence_archive_audit_status",
        ],
        "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js": [
            "setupLiveIntelligenceArchiveAudits", "Checksum audits", "Manual custody",
        ],
        "README.md": ["v3.18.0 — Archive Verification, Preservation Audits, and Institutional Custody"],
        "RELEASE_NOTES_SITE_INTELLIGENCE_V3160.md": ["Archive Verification", "custody", "checksum"],
        "docs/RELEASE_MANIFEST_V3160.json": ['"version": "3.18.0"', '"automatic_scheduler_claimed": false'],
        "docs/live-intelligence-archive-audit-v3160.schema.json": ["Live Intelligence Archive Audit", '"additionalProperties": false'],
    }
    for relative, needles in requirements.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        for needle in needles:
            assert needle in text, f"{needle!r} missing from {relative}"
