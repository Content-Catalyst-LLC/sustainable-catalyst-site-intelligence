from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
requirements = {
    "backend/app/version.py": ['APP_VERSION = "3.15.0"'],
    "backend/app/live_intelligence_public_archive_v3150.py": [
        "POLICY_SCHEMA_VERSION", "RECORD_SCHEMA_VERSION", "PACKAGE_SCHEMA_VERSION",
        "class LiveIntelligencePublicArchive", "def create_record(", "def verify_record(",
        "def approve_record(", "def verify_public_record(", "def public_lineage(",
        "def package_payload(", "def create_handoff(", "append_only_ledger",
        "source_record_mutated", "archive_record_deleted", "destination_write_performed",
    ],
    "backend/app/main.py": [
        "/public/live-intelligence/archive/policy", "/public/live-intelligence/archive/status",
        "/public/live-intelligence/archive/sources/{source_id:path}",
        "/admin/live-intelligence/archive/records", "/verify", "/approve", "/package", "/handoffs",
    ],
    "backend/app/config.py": [
        "live_intelligence_public_archive_enabled", "live_intelligence_public_archive_records_path",
        "live_intelligence_public_archive_events_path", "live_intelligence_public_archive_handoffs_path",
        "live_intelligence_public_archive_require_separation_of_duties",
    ],
    "backend/.env.example": [
        "SC_SI_LIVE_INTELLIGENCE_PUBLIC_ARCHIVE_ENABLED",
        "SC_SI_LIVE_INTELLIGENCE_PUBLIC_ARCHIVE_RECORDS_PATH",
        "SC_SI_LIVE_INTELLIGENCE_PUBLIC_ARCHIVE_REQUIRE_SEPARATION_OF_DUTIES",
    ],
    "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php": [
        "Version: 3.15.0", "sc_live_intelligence_public_archive",
        "rest_live_intelligence_public_archive_policy", "rest_live_intelligence_public_archive_status",
        "append-only provenance ledger",
    ],
    "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js": [
        "setupLiveIntelligencePublicArchive", "Append-only ledger", "No remote deposit",
    ],
    "README.md": ["v3.15.0 — Public Record Archive, Provenance Ledger, and Long-Term Preservation"],
    "RELEASE_NOTES_SITE_INTELLIGENCE_V3150.md": ["Public Record Archive", "append-only", "preservation"],
    "docs/RELEASE_MANIFEST_V3150.json": [
        '"version": "3.15.0"', '"append_only_ledger": true',
        '"archive_record_deleted": false', '"remote_deposit_performed": false',
    ],
    "docs/live-intelligence-public-archive-v3150.schema.json": [
        "Live Intelligence Public Archive Record", "source_sha256", '"additionalProperties": false',
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
print("Site Intelligence v3.15.0 release contract passed.")
