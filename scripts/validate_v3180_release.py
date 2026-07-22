from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
requirements = {
    "backend/app/version.py": ['APP_VERSION = "3.19.0"'],
    "backend/app/live_intelligence_federated_registry_v3180.py": [
        "class LiveIntelligenceFederatedPreservationRegistry", "def create_institution(",
        "def verify_institution(", "def approve_institution(", "def record_attestation(",
        "def consensus(", "multi_party_consensus_unique_institutions", "certification_claimed",
        "network_verification_performed", "destination_write_performed",
    ],
    "backend/app/main.py": [
        "/public/live-intelligence/preservation-registry/policy",
        "/public/live-intelligence/preservation-registry/institutions",
        "/public/live-intelligence/preservation-registry/attestations",
        "/public/live-intelligence/preservation-registry/exchanges/{exchange_id}/consensus",
        "/admin/live-intelligence/preservation-registry",
    ],
    "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php": [
        "Version: 3.19.0", "sc_live_intelligence_preservation_registry",
        "rest_live_intelligence_preservation_registry_status",
    ],
    "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js": [
        "setupLiveIntelligencePreservationRegistry", "Evidence-linked trust profiles",
        "Multi-party checksum consensus", "No certification claim",
    ],
    "README.md": ["v3.19.0 — Federated Preservation Registry, Trust Profiles, and Cross-Institution Verification"],
    "RELEASE_NOTES_SITE_INTELLIGENCE_V3180.md": ["Federated Preservation Registry", "multi-party", "trust profiles"],
    "docs/RELEASE_MANIFEST_V3180.json": ['"version": "3.19.0"', '"certification_claimed": false'],
    "docs/live-intelligence-federated-preservation-registry-v3180.schema.json": [
        "Live Intelligence Federated Preservation Registry", '"additionalProperties": false'
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
