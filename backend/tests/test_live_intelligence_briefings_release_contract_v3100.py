from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_v3100_release_contract():
    requirements = {
        "backend/app/version.py": ['APP_VERSION = "3.14.0"'],
        "backend/app/live_intelligence_briefings_v3100.py": [
            "POLICY_SCHEMA_VERSION", "BRIEFING_SCHEMA_VERSION", "CLAIM_SCHEMA_VERSION",
            "class LiveIntelligenceBriefingCenter", "def create_draft(", "def review_briefing(",
            "def package_payload(", "def create_handoff(", "automatic_wordpress_write",
            "deterministic_source_bound_template", "human_review_required",
        ],
        "backend/app/main.py": [
            "/public/live-intelligence/briefings/policy", "/public/live-intelligence/briefings/templates",
            "/public/live-intelligence/briefings/{briefing_id}/export",
            "/admin/live-intelligence/briefings/drafts",
            "/admin/live-intelligence/briefings/{briefing_id}/review",
            "/admin/live-intelligence/briefings/{briefing_id}/handoff",
        ],
        "backend/app/config.py": [
            "live_intelligence_briefings_enabled", "live_intelligence_briefings_path",
            "live_intelligence_briefing_packages_path", "live_intelligence_briefing_handoffs_path",
        ],
        "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php": [
            "Version: 3.14.0", "sc_live_intelligence_briefings",
            "rest_live_intelligence_briefings", "automatic WordPress publication",
        ],
        "README.md": ["v3.14.0 — Live Intelligence Briefings, Narrative Context, and Publication Workflow"],
        "RELEASE_NOTES_SITE_INTELLIGENCE_V3100.md": [
            "Live Intelligence Briefings", "source-linked", "human review", "WordPress",
        ],
        "docs/RELEASE_MANIFEST_V3100.json": [
            '"version": "3.14.0"', '"automatic_publication": false',
            '"automatic_wordpress_write": false', '"unsupported_claims_allowed": false',
        ],
    }
    for relative, needles in requirements.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        for needle in needles:
            assert needle in text, f"{needle!r} missing from {relative}"
