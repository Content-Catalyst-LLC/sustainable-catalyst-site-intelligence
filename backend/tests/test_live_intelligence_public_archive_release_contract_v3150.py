from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]


def test_v3150_release_contract():
    requirements = {
        "backend/app/version.py": ['APP_VERSION = "3.21.0"'],
        "backend/app/live_intelligence_public_archive_v3150.py": [
            "class LiveIntelligencePublicArchive", "def create_record(", "def verify_record(",
            "def approve_record(", "def verify_public_record(", "def package_payload(",
            "append_only_ledger", "archive_record_deleted", "destination_write_performed",
        ],
        "backend/app/main.py": [
            "/public/live-intelligence/archive/policy", "/public/live-intelligence/archive/status",
            "/public/live-intelligence/archive/sources/{source_id:path}",
            "/admin/live-intelligence/archive/records", "/records/{archive_id}/approve",
        ],
        "backend/app/config.py": [
            "live_intelligence_public_archive_enabled", "live_intelligence_public_archive_records_path",
            "live_intelligence_public_archive_require_separation_of_duties",
        ],
        "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php": [
            "Version: 3.21.0", "sc_live_intelligence_public_archive",
            "rest_live_intelligence_public_archive_status",
        ],
        "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js": [
            "setupLiveIntelligencePublicArchive", "Append-only ledger", "No remote deposit",
        ],
        "README.md": ["v3.21.0 — Public Record Archive, Provenance Ledger, and Long-Term Preservation"],
        "RELEASE_NOTES_SITE_INTELLIGENCE_V3150.md": ["Public Record Archive", "append-only", "preservation"],
        "docs/RELEASE_MANIFEST_V3150.json": ['"version": "3.21.0"', '"archive_record_deleted": false'],
        "docs/live-intelligence-public-archive-v3150.schema.json": ["Live Intelligence Public Archive Record", '"additionalProperties": false'],
    }
    for relative, needles in requirements.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        for needle in needles:
            assert needle in text, f"{needle!r} missing from {relative}"
