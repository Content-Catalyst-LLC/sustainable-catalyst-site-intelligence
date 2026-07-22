from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_v3200_release_contract():
    requirements = {
        "backend/app/version.py": ['APP_VERSION = "3.20.0"'],
        "backend/app/live_intelligence_registry_discovery_v3200.py": [
            "class LiveIntelligenceRegistryDiscovery", "def search(", "def facets(",
            "def institution_profile(", "search_queries_stored", "visitor_profiles_created",
            "staff_identities_exposed", "source_records_mutated", "certification_claimed",
        ],
        "backend/app/main.py": [
            "/public/live-intelligence/registry-discovery/policy",
            "/public/live-intelligence/registry-discovery/status",
            "/public/live-intelligence/registry-discovery/facets",
            "/public/live-intelligence/registry-discovery/search",
            "/public/live-intelligence/registry-discovery/institutions/{institution_id}",
        ],
        "backend/app/config.py": [
            "live_intelligence_registry_discovery_enabled",
            "live_intelligence_registry_discovery_default_limit",
            "live_intelligence_registry_discovery_max_limit",
        ],
        "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php": [
            "Version: 3.20.0", "sc_live_intelligence_registry_discovery",
            "rest_live_intelligence_registry_discovery_search",
        ],
        "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js": [
            "setupLiveIntelligenceRegistryDiscovery", "Evidence-linked profiles",
            "Queries are not stored", "No staff identities",
        ],
        "README.md": ["v3.20.0 — Public Registry Discovery, Evidence Search, and Institutional Profiles"],
        "RELEASE_NOTES_SITE_INTELLIGENCE_V3200.md": [
            "Registry Discovery", "institutional profiles", "search queries", "staff identities",
        ],
        "docs/RELEASE_MANIFEST_V3200.json": ['"version": "3.20.0"', '"search_queries_stored": false'],
        "docs/live-intelligence-registry-discovery-v3200.schema.json": [
            "Live Intelligence Registry Discovery", '"additionalProperties": false',
        ],
    }
    for relative, needles in requirements.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        for needle in needles:
            assert needle in text, f"{needle!r} missing from {relative}"
