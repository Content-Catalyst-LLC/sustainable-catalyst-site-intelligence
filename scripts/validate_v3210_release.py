#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
requirements = {
    "backend/app/version.py": ['APP_VERSION = "3.21.0"'],
    "backend/app/live_intelligence_registry_collections_v3210.py": [
        "class LiveIntelligenceRegistryCollectionsCenter", "def create_view(", "def create_collection(",
        "def pathway(", "visitor_queries_stored", "approved_snapshots_overwritten", "remote_write_performed",
    ],
    "backend/app/main.py": [
        "/public/live-intelligence/registry-collections/policy",
        "/public/live-intelligence/registry-collections/status",
        "/public/live-intelligence/registry-collections/views",
        "/public/live-intelligence/registry-collections/{collection_id}/pathway",
    ],
    "backend/app/config.py": ["live_intelligence_registry_collections_enabled", "live_intelligence_registry_collections_views_path"],
    "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php": [
        "Version: 3.21.0", "sc_live_intelligence_registry_collections", "rest_live_intelligence_registry_collection_pathway",
    ],
    "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js": [
        "setupLiveIntelligenceRegistryCollections", "Checksum-bound evidence pathway", "Visitor queries are not stored",
    ],
    "README.md": ["v3.21.0 — Saved Discovery Views, Public Research Collections, and Evidence Pathways"],
    "RELEASE_NOTES_SITE_INTELLIGENCE_V3210.md": ["Saved Discovery Views", "public research collections", "Visitor queries are not stored"],
    "docs/RELEASE_MANIFEST_V3210.json": ['"version": "3.21.0"', '"visitor_queries_stored": false'],
    "docs/live-intelligence-registry-collections-v3210.schema.json": ["Live Intelligence Registry Research Collection", '"additionalProperties": false'],
}
for relative, needles in requirements.items():
    path = ROOT / relative
    if not path.exists():
        raise SystemExit(f"Missing required release file: {relative}")
    text = path.read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"Missing {needle!r} in {relative}")
print("Site Intelligence v3.21.0 release contract passed.")
