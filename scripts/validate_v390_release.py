#!/usr/bin/env python3
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    "backend/app/version.py": ['APP_VERSION = "3.18.0"'],
    "backend/app/live_intelligence_subscriptions_v390.py": [
        "POLICY_SCHEMA_VERSION", "WATCHLIST_SCHEMA_VERSION", "ALERT_SCHEMA_VERSION",
        "DIGEST_SCHEMA_VERSION", "HANDOFF_SCHEMA_VERSION", "class LiveIntelligenceSubscriptionCenter",
        "def evaluate_watchlist(", "def generate_digest(", "def create_handoff(",
        "subscriber_profiles_stored", "email_sent_by_site_intelligence",
        "human_review_required_for_public_alerts", "ready_for_external_adapter",
    ],
    "backend/app/main.py": [
        "/public/live-intelligence/subscriptions/policy",
        "/public/live-intelligence/subscriptions/catalog",
        "/public/live-intelligence/subscriptions/alerts",
        "/public/live-intelligence/subscriptions/digests",
        "/public/live-intelligence/subscriptions/watchlists/{watchlist_id}/feed",
        "/admin/live-intelligence/subscriptions/run-due",
        "/admin/live-intelligence/subscriptions/alerts/{alert_id}/review",
        "/admin/live-intelligence/subscriptions/digests/{digest_id}/handoff",
    ],
    "backend/app/config.py": [
        "live_intelligence_subscriptions_enabled", "live_intelligence_watchlists_path",
        "live_intelligence_subscription_alerts_path", "live_intelligence_subscription_digests_path",
        "live_intelligence_subscription_handoffs_path", "live_intelligence_subscriptions_dedupe_hours",
    ],
    "backend/.env.example": [
        "SC_SI_LIVE_INTELLIGENCE_SUBSCRIPTIONS_ENABLED",
        "SC_SI_LIVE_INTELLIGENCE_SUBSCRIPTION_HANDOFFS_PATH",
    ],
    "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php": [
        "Version: 3.18.0", "sc_live_intelligence_watchlists", "sc_live_intelligence_alerts",
        "sc_live_intelligence_digests", "rest_live_intelligence_subscription_policy",
        "rest_live_intelligence_subscription_feed", "performs no direct email delivery",
    ],
    "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js": [
        "setupLiveIntelligenceSubscriptions", "scsi-live-subscriptions", "feed_urls",
    ],
    "README.md": ["v3.18.0 — Signal Subscriptions, Alerts, and Scheduled Intelligence"],
    "RELEASE_NOTES_SITE_INTELLIGENCE_V390.md": [
        "Signal Subscriptions, Alerts, and Scheduled Intelligence", "subscriber profiles", "provider-neutral",
    ],
    "docs/RELEASE_MANIFEST_V390.json": [
        '"version": "3.18.0"', '"subscriber_profiles_stored": false',
        '"automatic_publication": false', '"direct_email_delivery": false',
    ],
    "docs/live-intelligence-watchlist-v390.schema.json": ["Live Intelligence Watchlist", "numeric_above"],
}
for relative, needles in REQUIRED.items():
    path = ROOT / relative
    if not path.exists():
        raise SystemExit(f"Missing required release file: {relative}")
    text = path.read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"Missing {needle!r} in {relative}")
print("Site Intelligence v3.18.0 release contract passed.")
