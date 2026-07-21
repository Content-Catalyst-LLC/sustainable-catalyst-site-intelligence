from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_v370_release_contract():
    requirements = {
        "backend/app/version.py": ['APP_VERSION = "3.7.0"'],
        "backend/app/live_intelligence_gateway_v370.py": [
            "GATEWAY_SCHEMA_VERSION", "SIGNAL_FAMILY_REGISTRY", "DESTINATION_HIERARCHY",
            "def enrich_gateway_signal(", "def apply_gateway_policy(", "def homepage_gateway_policy(",
        ],
        "backend/app/main.py": [
            "/public/live-intelligence/homepage", "/public/live-intelligence/gateway-policy",
            "public_live_intelligence_homepage_endpoint", "public_live_intelligence_gateway_policy_endpoint",
        ],
        "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php": [
            "Version: 3.7.0", "rest_live_intelligence_homepage", "rest_live_intelligence_gateway_policy",
            "data-surface", "surface' => 'homepage'", "max_visible' => '8'",
        ],
        "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js": [
            "signal.primary_destination", "signal.family_label", "data-signal-family", "data-destination-type",
            "'/live-intelligence/homepage'",
        ],
        "README.md": ["v3.7.0 — Homepage Intelligence Gateway"],
        "docs/RELEASE_MANIFEST_V370.json": ["\"version\": \"3.7.0\"", "\"automatic_emergency_publication\": false", "\"full_application_boot_required\": false"],
    }
    for relative, needles in requirements.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        for needle in needles:
            assert needle in text, f"{needle!r} missing from {relative}"
