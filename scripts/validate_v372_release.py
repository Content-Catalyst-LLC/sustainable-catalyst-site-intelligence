#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    "backend/app/version.py": ['APP_VERSION = "3.7.2"'],
    "backend/app/config.py": ["live_intelligence_analytics_enabled", "live_intelligence_analytics_state_path", "live_intelligence_analytics_retention_days"],
    "backend/app/live_intelligence_analytics_v372.py": [
        "ANALYTICS_SCHEMA_VERSION", "class LiveIntelligenceAnalyticsStore", "def sanitize_analytics_event(",
        "def analytics_policy(", "raw_events_stored", "individual_user_tracking", "page_paths_stored",
    ],
    "backend/app/main.py": [
        "/public/live-intelligence/analytics/events", "/public/live-intelligence/analytics-policy",
        "/public/live-intelligence/analytics/summary", "/public/live-intelligence/analytics/source-reliability",
        "/admin/live-intelligence/analytics",
    ],
    "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php": [
        "Version: 3.7.2", "rest_live_intelligence_analytics_events", "rest_live_intelligence_analytics_summary",
    ],
    "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js": [
        "sendLiveAnalytics", "signal_impression", "feed_load_failure", "reduced_motion_use",
    ],
    "README.md": ["v3.7.2 — Analytics and Public-Value Measurement"],
    "RELEASE_NOTES_SITE_INTELLIGENCE_V372.md": ["Analytics and Public-Value Measurement", "Raw events are never stored"],
    "docs/RELEASE_MANIFEST_V372.json": ['"version": "3.7.2"', '"raw_events_stored": false', '"individual_user_tracking": false'],
}
for relative, needles in REQUIRED.items():
    path = ROOT / relative
    if not path.exists():
        raise SystemExit(f"Missing required release file: {relative}")
    text = path.read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"Missing {needle!r} in {relative}")
print("Site Intelligence v3.7.2 release contract passed.")
