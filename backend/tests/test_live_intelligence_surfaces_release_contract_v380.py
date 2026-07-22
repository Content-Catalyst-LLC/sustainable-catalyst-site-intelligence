from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_v380_release_contract():
    requirements = {
        "backend/app/version.py": ['APP_VERSION = "3.21.0"'],
        "backend/app/live_intelligence_surfaces_v380.py": [
            "SURFACE_SCHEMA_VERSION", "SURFACE_REGISTRY", "def surface_directory(",
            "def apply_connected_surface_policy(", "def embed_manifest(",
            "separate_ingestion_per_surface", "advertising_or_affiliate_signals",
        ],
        "backend/app/main.py": [
            "/public/live-intelligence/surfaces", "/public/live-intelligence/surface-policy",
            "/public/live-intelligence/surfaces/{surface_id}/feed", "/public/live-intelligence/embed-manifest",
            "apply_connected_surface_policy(result, \"homepage\"",
        ],
        "backend/app/live_intelligence_analytics_v372.py": [
            '"static_strip"', '"publication"', '"library"', '"advisory"', '"lab"', '"external_embed"',
        ],
        "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php": [
            "Version: 3.21.0", "sc_live_intelligence_publication", "sc_live_intelligence_library",
            "sc_live_intelligence_advisory", "sc_live_intelligence_lab", "sc_live_intelligence_embed",
            "rest_live_intelligence_surface_policy", "rest_live_intelligence_surface_feed",
        ],
        "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js": [
            "allowedSurfaces", "static_strip", "external_embed", "/live-intelligence/surfaces/",
        ],
        "README.md": ["v3.21.0 — Connected Live Intelligence Surface"],
        "RELEASE_NOTES_SITE_INTELLIGENCE_V380.md": ["Connected Live Intelligence Surface", "one governed signal system"],
        "docs/RELEASE_MANIFEST_V380.json": [
            '"version": "3.8.0"', '"separate_ingestion_per_surface": false',
            '"advertising_or_affiliate_signals": false', '"freshness_rules_bypassable": false',
        ],
    }
    for relative, needles in requirements.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        for needle in needles:
            assert needle in text, f"{needle!r} missing from {relative}"
