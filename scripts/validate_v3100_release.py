#!/usr/bin/env python3
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    "backend/app/version.py": ['APP_VERSION = "3.11.0"'],
    "backend/app/live_intelligence_briefings_v3100.py": [
        "POLICY_SCHEMA_VERSION", "BRIEFING_SCHEMA_VERSION", "CLAIM_SCHEMA_VERSION",
        "PACKAGE_SCHEMA_VERSION", "HANDOFF_SCHEMA_VERSION", "class LiveIntelligenceBriefingCenter",
        "def create_draft(", "def review_briefing(", "def package_payload(", "def create_handoff(",
        "deterministic_source_bound_template", "automatic_wordpress_write", "human_review_required",
    ],
    "backend/app/main.py": [
        "/public/live-intelligence/briefings/policy", "/public/live-intelligence/briefings/templates",
        "/public/live-intelligence/briefings/{briefing_id}", "/public/live-intelligence/briefings/{briefing_id}/export",
        "/admin/live-intelligence/briefings/drafts", "/admin/live-intelligence/briefings/{briefing_id}/review",
        "/admin/live-intelligence/briefings/{briefing_id}/handoff",
    ],
    "backend/app/config.py": [
        "live_intelligence_briefings_enabled", "live_intelligence_briefings_path",
        "live_intelligence_briefing_packages_path", "live_intelligence_briefing_handoffs_path",
        "live_intelligence_briefings_max_sources",
    ],
    "backend/.env.example": [
        "SC_SI_LIVE_INTELLIGENCE_BRIEFINGS_ENABLED", "SC_SI_LIVE_INTELLIGENCE_BRIEFING_HANDOFFS_PATH",
    ],
    "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php": [
        "Version: 3.11.0", "sc_live_intelligence_briefings", "rest_live_intelligence_briefings",
        "rest_live_intelligence_briefing_policy", "automatic WordPress publication",
    ],
    "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js": [
        "briefingCard", "key_observations", "Markdown package", "Source-linked briefings approved by an editor",
    ],
    "README.md": ["v3.11.0 — Live Intelligence Briefings, Narrative Context, and Publication Workflow"],
    "RELEASE_NOTES_SITE_INTELLIGENCE_V3100.md": [
        "Live Intelligence Briefings", "source-linked", "human review", "automatic WordPress",
    ],
    "docs/RELEASE_MANIFEST_V3100.json": [
        '"version": "3.11.0"', '"automatic_publication": false',
        '"automatic_wordpress_write": false', '"unsupported_claims_allowed": false',
    ],
    "docs/live-intelligence-briefing-v3100.schema.json": [
        "Live Intelligence Briefing", "source_refs", '"causal_inference": {"const": false}',
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
print("Site Intelligence v3.11.0 release contract passed.")
