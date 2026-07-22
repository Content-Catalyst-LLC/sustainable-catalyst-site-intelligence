#!/usr/bin/env python3
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    "backend/app/version.py": ['APP_VERSION = "3.22.0"'],
    "backend/app/live_intelligence_editorial_workspace_v3110.py": [
        "POLICY_SCHEMA_VERSION", "WORKSPACE_SCHEMA_VERSION", "REVISION_SCHEMA_VERSION",
        "REVIEW_SCHEMA_VERSION", "ORCHESTRATION_SCHEMA_VERSION",
        "class LiveIntelligenceEditorialWorkspace", "def create_workspace(", "def assign(",
        "def add_revision(", "def submit_for_review(", "def review(", "def orchestrate(",
        "separation_of_duties", "automatic_wordpress_write", "immutable_source_digest",
    ],
    "backend/app/main.py": [
        "/public/live-intelligence/editorial/policy", "/public/live-intelligence/editorial/status",
        "/admin/live-intelligence/editorial/workspaces", "/assign", "/revisions", "/submit",
        "/review", "/orchestrate", "/history",
    ],
    "backend/app/config.py": [
        "live_intelligence_editorial_enabled", "live_intelligence_editorial_workspaces_path",
        "live_intelligence_editorial_events_path", "live_intelligence_editorial_orchestration_path",
        "live_intelligence_editorial_require_separation_of_duties",
    ],
    "backend/.env.example": [
        "SC_SI_LIVE_INTELLIGENCE_EDITORIAL_ENABLED",
        "SC_SI_LIVE_INTELLIGENCE_EDITORIAL_REQUIRE_SEPARATION_OF_DUTIES",
    ],
    "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php": [
        "Version: 3.22.0", "sc_live_intelligence_editorial_workspace",
        "rest_live_intelligence_editorial_policy", "rest_live_intelligence_editorial_status",
        "separation of duties", "automatic WordPress write",
    ],
    "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js": [
        "setupLiveIntelligenceEditorial", "Publication ready", "Immutable evidence",
        "No automatic WordPress write",
    ],
    "README.md": ["v3.22.0 — Editorial Workspace, Review Queues, and Publication Orchestration"],
    "RELEASE_NOTES_SITE_INTELLIGENCE_V3110.md": [
        "Editorial Workspace", "separation of duties", "revision history", "provider-neutral",
    ],
    "docs/RELEASE_MANIFEST_V3110.json": [
        '"version": "3.22.0"', '"automatic_publication": false',
        '"automatic_wordpress_write": false', '"evidence_mutation_allowed": false',
    ],
    "docs/live-intelligence-editorial-workspace-v3110.schema.json": [
        "Live Intelligence Editorial Workspace", "immutable_source_digest", '"additionalProperties": false',
    ],
}
for relative, needles in REQUIRED.items():
    path = ROOT / relative
    if not path.exists():
        raise SystemExit(f"Missing required release file: {relative}")
    text = path.read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"Missing {needle!r} in {relative}")
print("Site Intelligence v3.22.0 release contract passed.")
