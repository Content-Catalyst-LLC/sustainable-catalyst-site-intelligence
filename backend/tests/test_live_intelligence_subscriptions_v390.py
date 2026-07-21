from datetime import datetime, timezone
import json

import pytest
from fastapi.testclient import TestClient

from app import main
from app.config import Settings
from app.live_intelligence_subscriptions_v390 import (
    ALERT_SCHEMA_VERSION,
    LiveIntelligenceSubscriptionCenter,
    POLICY_SCHEMA_VERSION,
    preference_manifest,
    signal_matches_rule,
    subscription_policy,
)


def settings_for(tmp_path):
    return Settings(
        environment="development",
        live_intelligence_watchlists_path=str(tmp_path / "watchlists.jsonl"),
        live_intelligence_subscription_evaluations_path=str(tmp_path / "evaluations.jsonl"),
        live_intelligence_subscription_alerts_path=str(tmp_path / "alerts.jsonl"),
        live_intelligence_subscription_digests_path=str(tmp_path / "digests.jsonl"),
        live_intelligence_subscription_handoffs_path=str(tmp_path / "handoffs.jsonl"),
        live_intelligence_rotation_state_path=str(tmp_path / "rotation.json"),
        live_intelligence_analytics_state_path=str(tmp_path / "analytics.json"),
        live_intelligence_last_known_good_path=str(tmp_path / "lkg.json"),
        live_source_operations_state_path=str(tmp_path / "source-state.json"),
        live_source_operations_history_path=str(tmp_path / "source-history.jsonl"),
    )


def signal(signal_id="event:climate:1", value="12.5", family="climate_earth_systems"):
    now = datetime.now(timezone.utc).isoformat()
    return {
        "signal_id": signal_id,
        "label": "Climate observation",
        "short_label": "Climate observation",
        "value": value,
        "formatted_value": value,
        "numeric_value": float(value),
        "signal_family": family,
        "feed_id": "noaa_nws",
        "source_name": "NOAA",
        "source_url": "https://example.org/source",
        "freshness_state": "live",
        "observed_at": now,
        "updated_at": now,
        "geography": {"scope": "country", "label": "United States", "country_code": "USA"},
        "primary_destination": {"type": "signal_context", "label": "Open context", "url": "/signal/context"},
        "context_view_url": "/signal/context",
        "evidence_url": "/signal/evidence",
    }


def public_watchlist_request():
    return {
        "title": "Climate threshold watch",
        "summary": "Human-reviewed public watch for selected climate signals.",
        "visibility": "public",
        "human_approved": True,
        "approved_by": "Editorial reviewer",
        "approval_reason": "The scope and wording are suitable for public monitoring.",
        "surface": "homepage",
        "channel": "global",
        "cadence": "daily",
        "match_mode": "all",
        "delivery_modes": ["public_feed", "digest_export", "communications_handoff"],
        "rules": [
            {"rule_id": "family", "type": "signal_family", "value": "climate_earth_systems"},
            {"rule_id": "threshold", "type": "numeric_above", "value": 10},
        ],
    }


def test_subscription_policy_discloses_no_profile_no_delivery_boundaries():
    policy = subscription_policy()
    assert policy["schema"] == POLICY_SCHEMA_VERSION
    assert policy["boundaries"]["subscriber_profiles_stored"] is False
    assert policy["boundaries"]["email_sent_by_site_intelligence"] is False
    assert policy["boundaries"]["webhooks_called_by_site_intelligence"] is False
    assert policy["boundaries"]["human_review_required_for_public_alerts"] is True
    assert preference_manifest()["subscriber_profiles_stored"] is False


def test_rule_matching_supports_family_threshold_and_geography():
    item = signal()
    assert signal_matches_rule(item, {"type": "signal_family", "value": "climate_earth_systems"})
    assert signal_matches_rule(item, {"type": "numeric_above", "value": 10})
    assert not signal_matches_rule(item, {"type": "numeric_below", "value": 10})
    assert signal_matches_rule(item, {"type": "geography_code", "value": "USA"})


def test_public_watchlist_requires_explicit_human_approval(tmp_path):
    center = LiveIntelligenceSubscriptionCenter(settings_for(tmp_path))
    request = public_watchlist_request()
    request.pop("approved_by")
    with pytest.raises(ValueError, match="Public watchlists require"):
        center.save_watchlist(request)


def test_subscription_requests_reject_recipient_and_profile_fields(tmp_path):
    center = LiveIntelligenceSubscriptionCenter(settings_for(tmp_path))
    request = public_watchlist_request()
    request["subscriber_email"] = "person@example.com"
    with pytest.raises(ValueError, match="subscriber identities"):
        center.save_watchlist(request)
    with pytest.raises(ValueError, match="subscriber identities"):
        center.create_handoff("digest:missing", {"recipients": ["person@example.com"]})


def test_evaluation_creates_pending_alert_and_deduplicates(tmp_path):
    center = LiveIntelligenceSubscriptionCenter(settings_for(tmp_path))
    watchlist = center.save_watchlist(public_watchlist_request())["watchlist"]
    first = center.evaluate_watchlist(watchlist["watchlist_id"], {"signals": [signal()]})
    second = center.evaluate_watchlist(watchlist["watchlist_id"], {"signals": [signal()]})
    assert first["evaluation"]["created_alert_count"] == 1
    assert first["alerts"][0]["status"] == "pending_review"
    assert first["alerts"][0]["published"] is False
    assert second["evaluation"]["created_alert_count"] == 0
    assert second["evaluation"]["duplicate_count"] == 1


def test_review_digest_and_provider_neutral_handoff(tmp_path):
    center = LiveIntelligenceSubscriptionCenter(settings_for(tmp_path))
    watchlist = center.save_watchlist(public_watchlist_request())["watchlist"]
    created = center.evaluate_watchlist(watchlist["watchlist_id"], {"signals": [signal()]})["alerts"][0]
    approved = center.review_alert(created["alert_id"], {
        "decision": "approve", "reviewed_by": "Editor", "reason": "Source, time, and wording checked.",
    })["alert"]
    assert approved["published"] is True
    assert center.alerts(public=True)[0]["schema"] == ALERT_SCHEMA_VERSION

    digest = center.generate_digest({
        "title": "Climate intelligence digest", "summary": "Reviewed climate matches.",
        "visibility": "public", "watchlist_ids": [watchlist["watchlist_id"]],
    })["digest"]
    reviewed = center.review_digest(digest["digest_id"], {
        "decision": "approve", "reviewed_by": "Editor", "reason": "Digest reviewed for public release.",
    })["digest"]
    assert reviewed["published"] is True
    handoff = center.create_handoff(digest["digest_id"], {"adapter": "catalyst_communications"})["handoff"]
    assert handoff["provider_neutral"] is True
    assert handoff["recipient_data_included"] is False
    assert handoff["delivery_performed"] is False



def test_public_digest_excludes_private_alerts(tmp_path):
    center = LiveIntelligenceSubscriptionCenter(settings_for(tmp_path))
    public_watch = center.save_watchlist(public_watchlist_request())["watchlist"]
    private_request = public_watchlist_request()
    private_request.update({
        "title": "Private internal watch",
        "visibility": "private",
        "human_approved": False,
        "watchlist_id": "watchlist:private-internal",
    })
    private_request.pop("approved_by", None)
    private_request.pop("approval_reason", None)
    private_watch = center.save_watchlist(private_request)["watchlist"]
    public_alert = center.evaluate_watchlist(public_watch["watchlist_id"], {"signals": [signal("event:climate:public")]})["alerts"][0]
    private_alert = center.evaluate_watchlist(private_watch["watchlist_id"], {"signals": [signal("event:climate:private")]})["alerts"][0]
    for alert in (public_alert, private_alert):
        center.review_alert(alert["alert_id"], {
            "decision": "approve", "reviewed_by": "Editor", "reason": "Reviewed for intended visibility.",
        })
    digest = center.generate_digest({
        "title": "Public-only digest", "visibility": "public",
        "alert_ids": [public_alert["alert_id"], private_alert["alert_id"]],
    })["digest"]
    assert digest["alert_count"] == 1
    assert digest["alerts"][0]["alert_id"] == public_alert["alert_id"]

def test_public_watchlist_feeds_support_json_rss_and_atom(tmp_path):
    center = LiveIntelligenceSubscriptionCenter(settings_for(tmp_path))
    watchlist = center.save_watchlist(public_watchlist_request())["watchlist"]
    alert = center.evaluate_watchlist(watchlist["watchlist_id"], {"signals": [signal()]})["alerts"][0]
    center.review_alert(alert["alert_id"], {"decision": "approve", "reviewed_by": "Editor", "reason": "Reviewed."})
    media, body = center.feed_payload(watchlist["watchlist_id"], "json")
    assert media == "application/json"
    assert json.loads(body)["count"] == 1
    media, body = center.feed_payload(watchlist["watchlist_id"], "rss")
    assert media == "application/rss+xml" and "<rss" in body
    media, body = center.feed_payload(watchlist["watchlist_id"], "atom")
    assert media == "application/atom+xml" and "<feed" in body


def test_public_and_admin_subscription_endpoints(tmp_path):
    settings = settings_for(tmp_path)
    center = LiveIntelligenceSubscriptionCenter(settings)
    watchlist = center.save_watchlist(public_watchlist_request())["watchlist"]
    main.app.dependency_overrides[main.get_settings] = lambda: settings
    try:
        client = TestClient(main.app)
        policy = client.get("/public/live-intelligence/subscriptions/policy")
        preferences = client.get("/public/live-intelligence/subscriptions/preferences")
        catalog = client.get("/public/live-intelligence/subscriptions/catalog")
        status = client.get("/public/live-intelligence/subscriptions/status")
        detail = client.get(f"/public/live-intelligence/subscriptions/catalog/{watchlist['watchlist_id']}")
        control = client.get("/admin/live-intelligence/subscriptions")
    finally:
        main.app.dependency_overrides.pop(main.get_settings, None)
    assert policy.status_code == 200
    assert preferences.status_code == 200
    assert catalog.status_code == 200 and catalog.json()["count"] == 1
    assert status.status_code == 200 and status.json()["public_watchlist_count"] == 1
    assert detail.status_code == 200
    assert control.status_code == 200
