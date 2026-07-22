from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def test_v3130_release_contract():
    requirements={
        "backend/app/version.py": ['APP_VERSION = "3.20.0"'],
        "backend/app/live_intelligence_release_operations_v3130.py": [
            "class LiveIntelligenceReleaseOperationsCenter", "def register_deployment(",
            "def verify_deployment(", "def report_issue(", "def propose_correction(",
            "def prepare_rollback(", "def approve_rollback(", "destination_write_performed",
        ],
        "backend/app/main.py": [
            "/public/live-intelligence/release-operations/policy",
            "/public/live-intelligence/release-operations/status",
            "/public/live-intelligence/release-operations/corrections",
            "/admin/live-intelligence/release-operations/deployments",
        ],
        "backend/app/config.py": [
            "live_intelligence_release_operations_enabled",
            "live_intelligence_release_deployments_path",
            "live_intelligence_release_operations_require_separation_of_duties",
        ],
        "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php": [
            "Version: 3.20.0", "sc_live_intelligence_release_operations",
            "rest_live_intelligence_release_operations_status",
        ],
        "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js": [
            "setupLiveIntelligenceReleaseOperations", "Verified deployments", "No deployment or rollback write",
        ],
        "README.md": ["v3.20.0 — Release Monitoring, Rollback, and Post-Publication Governance"],
        "RELEASE_NOTES_SITE_INTELLIGENCE_V3130.md": ["Release Monitoring", "Human verification", "rollback"],
        "docs/RELEASE_MANIFEST_V3130.json": ['"version": "3.20.0"','"destination_write_performed": false'],
        "docs/live-intelligence-release-operations-v3130.schema.json": ["Live Intelligence Release Operations",'"additionalProperties": false'],
    }
    for relative,needles in requirements.items():
        text=(ROOT/relative).read_text(encoding="utf-8")
        for needle in needles:
            assert needle in text, f"{needle!r} missing from {relative}"
