from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def test_v3120_release_contract():
    requirements={
        "backend/app/version.py": ['APP_VERSION = "3.17.0"'],
        "backend/app/live_intelligence_publication_releases_v3120.py": ["POLICY_SCHEMA_VERSION","RELEASE_SCHEMA_VERSION","PACKAGE_SCHEMA_VERSION","HANDOFF_SCHEMA_VERSION","class LiveIntelligencePublicationReleaseCenter","def prepare(","def validate(","def approve(","def create_handoff(","package_sha256","automatic_wordpress_write","destination_write_performed"],
        "backend/app/main.py": ["/public/live-intelligence/publication-releases/policy","/public/live-intelligence/publication-releases/adapters","/public/live-intelligence/publication-releases/status","/admin/live-intelligence/publication-releases/prepare","/validate","/approve","/handoffs","/package","/history"],
        "backend/app/config.py": ["live_intelligence_publication_releases_enabled","live_intelligence_publication_releases_path","live_intelligence_publication_release_events_path","live_intelligence_publication_handoffs_path","live_intelligence_publication_require_separation_of_duties"],
        "backend/.env.example": ["SC_SI_LIVE_INTELLIGENCE_PUBLICATION_RELEASES_ENABLED","SC_SI_LIVE_INTELLIGENCE_PUBLICATION_REQUIRE_SEPARATION_OF_DUTIES"],
        "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php": ["Version: 3.17.0","sc_live_intelligence_publication_releases","rest_live_intelligence_publication_release_policy","rest_live_intelligence_publication_release_status","manual destination handoff"],
        "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js": ["setupLiveIntelligencePublicationReleases","Release packages","No destination write","Separate release approval"],
        "README.md": ["v3.17.0 — Publication Adapters, Institutional Handoffs, and Release Governance"],
        "RELEASE_NOTES_SITE_INTELLIGENCE_V3120.md": ["Publication Adapters","package checksums","manual handoff receipts","separation of duties"],
        "docs/RELEASE_MANIFEST_V3120.json": ['"version": "3.12.0"','"automatic_wordpress_write": false','"institutional_write_performed": false','"package_checksums_required": true'],
        "docs/live-intelligence-publication-release-v3120.schema.json": ["Live Intelligence Publication Release","payload_sha256",'"additionalProperties": false'],
    }
    for relative,needles in requirements.items():
        text=(ROOT/relative).read_text(encoding="utf-8")
        for needle in needles:
            assert needle in text, f"{needle!r} missing from {relative}"
