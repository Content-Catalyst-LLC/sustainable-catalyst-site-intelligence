from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_v3220_release_contract():
    requirements = {
        "backend/app/version.py": ['APP_VERSION = "3.22.0"'],
        "backend/app/live_intelligence_registry_publications_v3220.py": [
            "class LiveIntelligenceRegistryPublicationCenter", "def create_brief(", "def review_brief(",
            "def approve_brief(", "def citation_bundle(", "def package_payload(", "def record_handoff(",
            "automatic_publication_performed", "recipient_identities_stored", "citation_standard_certification_claimed",
        ],
        "backend/app/main.py": [
            "/public/live-intelligence/registry-publications/policy",
            "/public/live-intelligence/registry-publications/status",
            "/public/live-intelligence/registry-publications/briefs/{brief_id}/citations",
            "/admin/live-intelligence/registry-publications/briefs/{brief_id}/approve",
            "/admin/live-intelligence/registry-publications/briefs/{brief_id}/handoffs",
        ],
        "backend/app/config.py": [
            "live_intelligence_registry_publications_enabled",
            "live_intelligence_registry_publications_briefs_path",
            "live_intelligence_registry_publications_handoffs_path",
        ],
        "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php": [
            "Version: 3.22.0", "sc_live_intelligence_registry_publications",
            "rest_live_intelligence_registry_publications_briefs",
            "rest_live_intelligence_registry_publication_citations",
        ],
        "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js": [
            "setupLiveIntelligenceRegistryPublications", "Source-linked citation bundle",
            "No automatic publication",
        ],
        "README.md": ["v3.22.0 — Collection Publication, Citation Exports, and Research Brief Packages"],
        "RELEASE_NOTES_SITE_INTELLIGENCE_V3220.md": ["Collection Publication", "Citation exports", "No automatic publication"],
        "docs/RELEASE_MANIFEST_V3220.json": ['"version": "3.22.0"', '"automatic_publication_performed": false'],
        "docs/live-intelligence-registry-publications-v3220.schema.json": ["Live Intelligence Registry Research Brief", '"additionalProperties": false'],
    }
    for relative, needles in requirements.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        for needle in needles:
            assert needle in text, f"{needle!r} missing from {relative}"
