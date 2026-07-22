from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_v3110_release_contract():
    requirements = {
        "backend/app/version.py": ['APP_VERSION = "3.17.0"'],
        "backend/app/live_intelligence_editorial_workspace_v3110.py": [
            "POLICY_SCHEMA_VERSION", "WORKSPACE_SCHEMA_VERSION", "REVISION_SCHEMA_VERSION",
            "ORCHESTRATION_SCHEMA_VERSION", "class LiveIntelligenceEditorialWorkspace",
            "def create_workspace(", "def add_revision(", "def submit_for_review(",
            "def review(", "def orchestrate(", "separation_of_duties",
            "automatic_wordpress_write", "evidence_mutation_allowed",
        ],
        "backend/app/main.py": [
            "/public/live-intelligence/editorial/policy", "/public/live-intelligence/editorial/status",
            "/admin/live-intelligence/editorial/workspaces", "/assign", "/revisions",
            "/submit", "/review", "/orchestrate", "/history",
        ],
        "backend/app/config.py": [
            "live_intelligence_editorial_workspaces_path", "live_intelligence_editorial_events_path",
            "live_intelligence_editorial_orchestration_path", "live_intelligence_editorial_require_separation_of_duties",
        ],
        "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php": [
            "Version: 3.17.0", "sc_live_intelligence_editorial_workspace",
            "rest_live_intelligence_editorial_policy", "rest_live_intelligence_editorial_status",
        ],
        "README.md": ["v3.17.0 — Editorial Workspace, Review Queues, and Publication Orchestration"],
        "RELEASE_NOTES_SITE_INTELLIGENCE_V3110.md": [
            "Editorial Workspace", "separation of duties", "revision history", "provider-neutral",
        ],
        "docs/RELEASE_MANIFEST_V3110.json": [
            '"version": "3.17.0"', '"automatic_publication": false',
            '"automatic_wordpress_write": false', '"evidence_mutation_allowed": false',
        ],
    }
    for relative, needles in requirements.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        for needle in needles:
            assert needle in text, f"{needle!r} missing from {relative}"
