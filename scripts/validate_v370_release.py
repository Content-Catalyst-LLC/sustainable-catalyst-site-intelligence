#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    "backend/app/version.py": ['APP_VERSION = "3.7.0"'],
    "backend/app/live_intelligence_gateway_v370.py": ["GATEWAY_SCHEMA_VERSION", "homepage_gateway_policy", "primary_destination"],
    "backend/app/main.py": ["/public/live-intelligence/homepage", "/public/live-intelligence/gateway-policy"],
    "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php": ["Version: 3.7.0", "rest_live_intelligence_homepage", "data-surface"],
    "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js": ["data-signal-family", "data-destination-type", "signal.primary_destination"],
    "README.md": ["v3.7.0 — Homepage Intelligence Gateway"],
    "RELEASE_NOTES_SITE_INTELLIGENCE_V370.md": ["Homepage Intelligence Gateway"],
    "docs/RELEASE_MANIFEST_V370.json": ["\"version\": \"3.7.0\"", "\"automatic_emergency_publication\": false"],
}
for relative, needles in REQUIRED.items():
    path = ROOT / relative
    if not path.exists():
        raise SystemExit(f"Missing required release file: {relative}")
    text = path.read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"Missing {needle!r} in {relative}")
print("Site Intelligence v3.7.0 release contract passed.")
