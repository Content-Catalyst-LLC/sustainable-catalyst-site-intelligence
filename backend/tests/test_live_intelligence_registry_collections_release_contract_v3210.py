from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_v3210_release_contract():
    requirements = {
        "backend/app/version.py": ['APP_VERSION = "3.21.0"'],
        "backend/app/live_intelligence_registry_collections_v3210.py": [
            "class LiveIntelligenceRegistryCollectionsCenter", "def create_view(", "def approve_view(",
            "def create_collection(", "def approve_collection(", "def pathway(", "def package_payload(",
            "visitor_queries_stored", "visitor_profiles_created", "approved_snapshots_overwritten",
            "source_records_mutated", "remote_write_performed", "certification_claimed",
        ],
        "backend/app/main.py": [
            "/public/live-intelligence/registry-collections/policy",
            "/public/live-intelligence/registry-collections/status",
            "/public/live-intelligence/registry-collections/views",
            "/public/live-intelligence/registry-collections/{collection_id}",
            "/public/live-intelligence/registry-collections/{collection_id}/pathway",
            "/admin/live-intelligence/registry-collections/views/{view_id}/review",
            "/admin/live-intelligence/registry-collections/{collection_id}/approve",
        ],
        "backend/app/config.py": [
            "live_intelligence_registry_collections_enabled",
            "live_intelligence_registry_collections_views_path",
            "live_intelligence_registry_collections_path",
            "live_intelligence_registry_collections_events_path",
            "live_intelligence_registry_collections_snapshot_limit",
        ],
        "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php": [
            "Version: 3.21.0", "sc_live_intelligence_registry_collections",
            "rest_live_intelligence_registry_collections_views",
            "rest_live_intelligence_registry_collection_pathway",
        ],
        "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js": [
            "setupLiveIntelligenceRegistryCollections", "Checksum-bound evidence pathway",
            "Visitor queries are not stored", "Approved snapshots are not overwritten",
        ],
        "README.md": ["v3.21.0 — Saved Discovery Views, Public Research Collections, and Evidence Pathways"],
        "RELEASE_NOTES_SITE_INTELLIGENCE_V3210.md": [
            "Saved Discovery Views", "public research collections", "Evidence pathways",
            "Visitor queries are not stored",
        ],
        "docs/RELEASE_MANIFEST_V3210.json": ['"version": "3.21.0"', '"visitor_queries_stored": false'],
        "docs/live-intelligence-registry-collections-v3210.schema.json": [
            "Live Intelligence Registry Research Collection", '"additionalProperties": false',
        ],
    }
    for relative, needles in requirements.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        for needle in needles:
            assert needle in text, f"{needle!r} missing from {relative}"
