from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
requirements={
    "backend/app/version.py": ['APP_VERSION = "3.21.0"'],
    "backend/app/live_intelligence_release_operations_v3130.py": [
        "POLICY_SCHEMA_VERSION", "DEPLOYMENT_SCHEMA_VERSION", "ISSUE_SCHEMA_VERSION",
        "CORRECTION_SCHEMA_VERSION", "ROLLBACK_SCHEMA_VERSION",
        "class LiveIntelligenceReleaseOperationsCenter", "def register_deployment(",
        "def verify_deployment(", "def report_issue(", "def propose_correction(",
        "def approve_correction(", "def prepare_rollback(", "def approve_rollback(",
        "def create_handoff(", "network_fetch_performed", "destination_write_performed",
    ],
    "backend/app/main.py": [
        "/public/live-intelligence/release-operations/policy",
        "/public/live-intelligence/release-operations/status",
        "/public/live-intelligence/release-operations/corrections",
        "/admin/live-intelligence/release-operations/deployments",
        "/verify", "/issues", "/corrections", "/rollbacks", "/handoffs", "/history",
    ],
    "backend/app/config.py": [
        "live_intelligence_release_operations_enabled",
        "live_intelligence_release_deployments_path",
        "live_intelligence_release_operation_events_path",
        "live_intelligence_release_issues_path",
        "live_intelligence_release_corrections_path",
        "live_intelligence_release_rollbacks_path",
        "live_intelligence_release_operation_handoffs_path",
        "live_intelligence_release_operations_require_separation_of_duties",
    ],
    "backend/.env.example": [
        "SC_SI_LIVE_INTELLIGENCE_RELEASE_OPERATIONS_ENABLED",
        "SC_SI_LIVE_INTELLIGENCE_RELEASE_DEPLOYMENTS_PATH",
        "SC_SI_LIVE_INTELLIGENCE_RELEASE_OPERATIONS_REQUIRE_SEPARATION_OF_DUTIES",
    ],
    "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php": [
        "Version: 3.21.0", "sc_live_intelligence_release_operations",
        "rest_live_intelligence_release_operations_policy",
        "rest_live_intelligence_release_operations_status",
        "performs no deployment, rollback, deletion, network verification, or destination write",
    ],
    "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js": [
        "setupLiveIntelligenceReleaseOperations", "Deployment receipts", "Verified deployments",
        "No deployment or rollback write",
    ],
    "README.md": ["v3.21.0 — Release Monitoring, Rollback, and Post-Publication Governance"],
    "RELEASE_NOTES_SITE_INTELLIGENCE_V3130.md": ["Release Monitoring", "rollback manifests", "Private corrections"],
    "SITE_INTELLIGENCE_V3130_BUILD_VALIDATION.txt": ["RESULT: PASS", "729 tests passed", "21 tests passed", "No network verification"],
    "SITE_INTELLIGENCE_V3130_INSTALL_AND_TEST.md": ["SC_SI_FULL_TESTS=1", "sc_live_intelligence_release_operations"],
    "docs/RELEASE_MANIFEST_V3130.json": [
        '"version": "3.21.0"', '"network_fetch_performed": false',
        '"deployment_performed": false', '"rollback_performed": false',
        '"destination_write_performed": false',
    ],
    "docs/live-intelligence-release-operations-v3130.schema.json": [
        "Live Intelligence Release Operations", "release_sha256", '"additionalProperties": false',
    ],
}
for relative,needles in requirements.items():
    path=ROOT/relative
    if not path.exists(): raise SystemExit(f"Missing required release file: {relative}")
    text=path.read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text: raise SystemExit(f"Missing {needle!r} in {relative}")
print("Site Intelligence v3.21.0 release contract passed.")
