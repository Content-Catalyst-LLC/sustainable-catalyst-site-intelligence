#!/usr/bin/env python3
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
requirements = {
    "backend/app/version.py": ['APP_VERSION = "3.22.0"'],
    "backend/app/live_intelligence_registry_publications_v3220.py": ["class LiveIntelligenceRegistryPublicationCenter", "def create_brief(", "def citation_bundle(", "def record_handoff(", "automatic_publication_performed"],
    "backend/app/main.py": ["/public/live-intelligence/registry-publications/policy", "/admin/live-intelligence/registry-publications/briefs/{brief_id}/approve"],
    "backend/app/config.py": ["live_intelligence_registry_publications_enabled", "live_intelligence_registry_publications_briefs_path"],
    "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php": ["Version: 3.22.0", "sc_live_intelligence_registry_publications"],
    "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js": ["setupLiveIntelligenceRegistryPublications", "Source-linked citation bundle"],
    "README.md": ["v3.22.0 — Collection Publication, Citation Exports, and Research Brief Packages"],
    "RELEASE_NOTES_SITE_INTELLIGENCE_V3220.md": ["Collection Publication", "Citation exports", "No automatic publication"],
    "docs/RELEASE_MANIFEST_V3220.json": ['"version": "3.22.0"', '"automatic_publication_performed": false'],
    "docs/live-intelligence-registry-publications-v3220.schema.json": ["Live Intelligence Registry Research Brief", '"additionalProperties": false'],
}
for relative, needles in requirements.items():
    path = ROOT / relative
    if not path.exists(): raise SystemExit(f"Missing required release file: {relative}")
    text = path.read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text: raise SystemExit(f"Missing {needle!r} in {relative}")
print("Site Intelligence v3.22.0 release contract passed.")
