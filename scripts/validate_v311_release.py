from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
checks = {
    "backend/app/version.py": [
        'APP_VERSION = "3.1.1"',
        'Connected Public Intelligence and Evidence Platform',
    ],
    "backend/app/live_intelligence_v311.py": [
        'SCHEMA_VERSION = "sc-site-intelligence-live-intelligence/1.1"',
        "def build_live_intelligence",
        "Demonstration fallback records and sample connector values are excluded",
        "LATEST EARTHQUAKE",
        "LATEST HUMANITARIAN REPORT",
    ],
    "backend/app/main.py": [
        "from .live_intelligence_v311 import",
        "/public/live-intelligence",
        "/public/live-intelligence/status",
    ],
    "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php": [
        "Version: 3.1.1",
        "sc_live_intelligence",
        "register_live_intelligence_placement",
        "live_intelligence_placement",
        "below_breadcrumb",
        "astra_get_option('breadcrumb-position')",
        "live_intelligence_parchment_navigation",
    ],
    "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.css": [
        "v3.1.1 — Live Intelligence content and interface repair",
        "is-hover-paused",
        "animation-play-state:paused!important",
        "scsi-live-intelligence-parchment-navigation",
    ],
    "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js": [
        "setupLiveIntelligence",
        "mouseenter",
        "mouseleave",
        "is-focus-paused",
        "is-delayed",
    ],
    "README.md": [
        "v3.1.1 — Live Intelligence Content and Interface Repair",
        "Current release:** v3.1.1 — Connected Public Intelligence and Evidence Platform",
    ],
}
for rel, markers in checks.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for marker in markers:
        if marker not in text:
            raise SystemExit(f"{rel}: missing {marker}")

policy = json.loads((ROOT / "docs/RELEASE_MANIFEST_V311.json").read_text(encoding="utf-8"))
for key in [
    "verified_public_interest_signals",
    "demonstration_records_suppressed",
    "sample_connector_values_suppressed",
    "single_platform_status_item",
    "hover_pause_repaired",
    "focus_pause_supported",
    "pause_button_supported",
    "last_verified_feed_preserved_on_refresh_failure",
    "below_breadcrumb_default",
    "below_header_fallback",
    "shortcode_only_mode",
    "parchment_navigation_option",
    "shortcode_available",
    "source_attribution_required",
    "freshness_required",
]:
    if policy.get(key) is not True:
        raise SystemExit(f"Release policy requires {key}=true")
for key in [
    "raw_upstream_payloads_exposed",
    "browser_api_keys_exposed",
    "demonstration_values_public",
    "automatic_interpretation",
    "sticky_ticker_default",
    "sitewide_default",
]:
    if policy.get(key) is not False:
        raise SystemExit(f"Release policy requires {key}=false")
print("Site Intelligence v3.1.1 release contract passed.")
