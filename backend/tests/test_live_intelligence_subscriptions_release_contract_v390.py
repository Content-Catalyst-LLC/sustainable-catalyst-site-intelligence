from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_v390_release_contract():
    requirements = {
        "backend/app/version.py": ['APP_VERSION = "3.9.0"'],
        "backend/app/live_intelligence_subscriptions_v390.py": [
            "POLICY_SCHEMA_VERSION", "WATCHLIST_SCHEMA_VERSION", "ALERT_SCHEMA_VERSION",
            "class LiveIntelligenceSubscriptionCenter", "def subscription_policy(",
            "def evaluate_watchlist(", "def create_handoff(", "subscriber_profiles_stored",
            "email_sent_by_site_intelligence", "human_review_required_for_public_alerts",
        ],
        "backend/app/main.py": [
            "/public/live-intelligence/subscriptions/policy",
            "/public/live-intelligence/subscriptions/catalog",
            "/public/live-intelligence/subscriptions/watchlists/{watchlist_id}/feed",
            "/admin/live-intelligence/subscriptions/watchlists/{watchlist_id}/evaluate",
            "/admin/live-intelligence/subscriptions/digests/{digest_id}/handoff",
        ],
        "backend/app/config.py": [
            "live_intelligence_subscriptions_enabled", "live_intelligence_watchlists_path",
            "live_intelligence_subscription_handoffs_path", "live_intelligence_subscriptions_dedupe_hours",
        ],
        "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php": [
            "Version: 3.9.0", "sc_live_intelligence_watchlists", "sc_live_intelligence_alerts",
            "sc_live_intelligence_digests", "rest_live_intelligence_subscription_policy",
        ],
        "README.md": ["v3.9.0 — Signal Subscriptions, Alerts, and Scheduled Intelligence"],
        "RELEASE_NOTES_SITE_INTELLIGENCE_V390.md": [
            "Signal Subscriptions, Alerts, and Scheduled Intelligence", "subscriber profiles",
            "provider-neutral",
        ],
        "docs/RELEASE_MANIFEST_V390.json": [
            '"version": "3.9.0"', '"subscriber_profiles_stored": false',
            '"automatic_publication": false', '"direct_email_delivery": false',
        ],
    }
    for relative, needles in requirements.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        for needle in needles:
            assert needle in text, f"{needle!r} missing from {relative}"
