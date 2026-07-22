from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_v3190_release_contract():
    requirements = {
        "backend/app/version.py": ['APP_VERSION = "3.21.0"'],
        "backend/app/live_intelligence_registry_governance_v3190.py": [
            "class LiveIntelligenceRegistryGovernanceCenter",
            "def create_challenge(", "def review_challenge(", "def approve_challenge(",
            "def create_appeal(", "def review_appeal(", "def approve_appeal(",
            "def institution_governance(", "append_only_governance_ledger",
            "prior_attestations_retained", "automatic_enforcement_performed",
            "remote_write_performed", "certification_claimed",
        ],
        "backend/app/main.py": [
            "/public/live-intelligence/registry-governance/policy",
            "/public/live-intelligence/registry-governance/challenges",
            "/public/live-intelligence/registry-governance/appeals",
            "/public/live-intelligence/registry-governance/institutions/{institution_id}",
            "/admin/live-intelligence/registry-governance",
        ],
        "backend/app/config.py": [
            "live_intelligence_registry_governance_enabled",
            "live_intelligence_registry_governance_challenges_path",
            "live_intelligence_registry_governance_appeals_path",
            "live_intelligence_registry_governance_events_path",
        ],
        "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php": [
            "Version: 3.21.0", "sc_live_intelligence_registry_governance",
            "rest_live_intelligence_registry_governance_status",
        ],
        "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js": [
            "setupLiveIntelligenceRegistryGovernance", "Append-only decisions",
            "Appeal pathway", "No record deletion",
        ],
        "README.md": ["v3.21.0 — Registry Governance, Challenges, Revocation, and Appeals"],
        "RELEASE_NOTES_SITE_INTELLIGENCE_V3190.md": [
            "Registry Governance", "revocation", "appeals", "append-only",
        ],
        "docs/RELEASE_MANIFEST_V3190.json": ['"version": "3.21.0"', '"automatic_enforcement_performed": false'],
        "docs/live-intelligence-registry-governance-v3190.schema.json": [
            "Live Intelligence Registry Governance", '"additionalProperties": false',
        ],
    }
    for relative, needles in requirements.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        for needle in needles:
            assert needle in text, f"{needle!r} missing from {relative}"
