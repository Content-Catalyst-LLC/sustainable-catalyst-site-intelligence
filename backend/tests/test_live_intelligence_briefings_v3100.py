from datetime import datetime, timezone
import json

import pytest
from fastapi.testclient import TestClient

from app import main
from app.config import Settings
from app.live_intelligence_briefings_v3100 import (
    BRIEFING_SCHEMA_VERSION,
    LiveIntelligenceBriefingCenter,
    POLICY_SCHEMA_VERSION,
    briefing_policy,
    briefing_templates,
)


def settings_for(tmp_path):
    return Settings(
        environment="development",
        live_intelligence_briefings_path=str(tmp_path / "briefings.jsonl"),
        live_intelligence_briefing_packages_path=str(tmp_path / "packages.jsonl"),
        live_intelligence_briefing_handoffs_path=str(tmp_path / "briefing-handoffs.jsonl"),
        live_intelligence_watchlists_path=str(tmp_path / "watchlists.jsonl"),
        live_intelligence_subscription_evaluations_path=str(tmp_path / "evaluations.jsonl"),
        live_intelligence_subscription_alerts_path=str(tmp_path / "alerts.jsonl"),
        live_intelligence_subscription_digests_path=str(tmp_path / "digests.jsonl"),
        live_intelligence_subscription_handoffs_path=str(tmp_path / "subscription-handoffs.jsonl"),
        live_intelligence_rotation_state_path=str(tmp_path / "rotation.json"),
        live_intelligence_analytics_state_path=str(tmp_path / "analytics.json"),
        live_intelligence_last_known_good_path=str(tmp_path / "lkg.json"),
        live_source_operations_state_path=str(tmp_path / "source-state.json"),
        live_source_operations_history_path=str(tmp_path / "source-history.jsonl"),
    )


def signal(signal_id="event:climate:1"):
    now = datetime.now(timezone.utc).isoformat()
    return {
        "signal_id": signal_id,
        "label": "Climate observation",
        "short_label": "Climate observation",
        "value": "12.5",
        "formatted_value": "12.5 °C",
        "numeric_value": 12.5,
        "signal_family": "climate_earth_systems",
        "feed_id": "noaa_nws",
        "source_name": "NOAA",
        "source_url": "https://example.org/source",
        "freshness_state": "live",
        "observed_at": now,
        "updated_at": now,
        "geography": {"scope": "country", "label": "United States", "country_code": "USA"},
        "primary_destination": {"type": "signal_context", "label": "Open context", "url": "/signal/context"},
        "context_url": "/signal/context",
    }


def public_request():
    return {
        "title": "Climate signal briefing",
        "briefing_type": "signal",
        "visibility": "public",
        "signals": [signal()],
    }


def test_briefing_policy_discloses_editorial_boundaries():
    policy = briefing_policy()
    assert policy["schema"] == POLICY_SCHEMA_VERSION
    assert policy["boundaries"]["automatic_publication"] is False
    assert policy["boundaries"]["automatic_wordpress_write"] is False
    assert policy["boundaries"]["human_review_required"] is True
    assert policy["boundaries"]["unsupported_claims_allowed"] is False
    assert len(briefing_templates()["templates"]) == 5


def test_draft_is_source_bound_and_not_published(tmp_path):
    center = LiveIntelligenceBriefingCenter(settings_for(tmp_path))
    draft = center.create_draft(public_request())["briefing"]
    assert draft["schema"] == BRIEFING_SCHEMA_VERSION
    assert draft["status"] == "draft"
    assert draft["published"] is False
    assert draft["source_count"] == 1
    assert draft["claim_count"] == 1
    assert draft["claims"][0]["source_refs"]
    assert draft["claims"][0]["causal_inference"] is False
    assert draft["narrative_method"] == "deterministic_source_bound_template"


def test_draft_requires_canonical_evidence(tmp_path):
    center = LiveIntelligenceBriefingCenter(settings_for(tmp_path))
    with pytest.raises(ValueError, match="At least one canonical signal"):
        center.create_draft({"title": "Empty briefing", "visibility": "private"})


def test_payload_rejects_recipient_identity_fields(tmp_path):
    center = LiveIntelligenceBriefingCenter(settings_for(tmp_path))
    request = public_request()
    request["recipients"] = ["person@example.com"]
    with pytest.raises(ValueError, match="recipient identities"):
        center.create_draft(request)


def test_human_review_controls_publication(tmp_path):
    center = LiveIntelligenceBriefingCenter(settings_for(tmp_path))
    draft = center.create_draft(public_request())["briefing"]
    assert center.briefings(public=True) == []
    approved = center.review_briefing(draft["briefing_id"], {
        "decision": "approve", "reviewed_by": "Editor", "reason": "Sources, dates, and language verified.",
    })["briefing"]
    assert approved["published"] is True
    assert approved["claims"][0]["human_verified"] is True
    public = center.briefings(public=True)
    assert len(public) == 1 and public[0]["human_reviewed"] is True


def test_rejected_briefing_stays_private(tmp_path):
    center = LiveIntelligenceBriefingCenter(settings_for(tmp_path))
    draft = center.create_draft(public_request())["briefing"]
    rejected = center.review_briefing(draft["briefing_id"], {
        "decision": "reject", "reviewed_by": "Editor", "reason": "Needs stronger geographic context.",
    })["briefing"]
    assert rejected["status"] == "rejected"
    assert rejected["published"] is False
    assert center.briefings(public=True) == []


def test_approved_briefing_exports_json_and_markdown(tmp_path):
    center = LiveIntelligenceBriefingCenter(settings_for(tmp_path))
    draft = center.create_draft(public_request())["briefing"]
    center.review_briefing(draft["briefing_id"], {
        "decision": "approve", "reviewed_by": "Editor", "reason": "Reviewed.",
    })
    media, body = center.package_payload(draft["briefing_id"], "json", public=True)
    assert media == "application/json"
    assert json.loads(body)["wordpress_write_performed"] is False
    media, body = center.package_payload(draft["briefing_id"], "markdown", public=True)
    assert media == "text/markdown"
    assert "# Climate signal briefing" in body
    assert "## Sources" in body


def test_handoff_is_provider_neutral_and_performs_no_write(tmp_path):
    center = LiveIntelligenceBriefingCenter(settings_for(tmp_path))
    draft = center.create_draft(public_request())["briefing"]
    center.review_briefing(draft["briefing_id"], {
        "decision": "approve", "reviewed_by": "Editor", "reason": "Reviewed.",
    })
    handoff = center.create_handoff(draft["briefing_id"], {"adapter": "knowledge_library"})["handoff"]
    assert handoff["provider_neutral"] is True
    assert handoff["publication_performed"] is False
    assert handoff["wordpress_write_performed"] is False
    assert handoff["recipient_data_included"] is False


def test_public_briefing_endpoints(tmp_path):
    settings = settings_for(tmp_path)
    center = LiveIntelligenceBriefingCenter(settings)
    draft = center.create_draft(public_request())["briefing"]
    center.review_briefing(draft["briefing_id"], {
        "decision": "approve", "reviewed_by": "Editor", "reason": "Reviewed for public release.",
    })
    main.app.dependency_overrides[main.get_settings] = lambda: settings
    try:
        client = TestClient(main.app)
        policy = client.get("/public/live-intelligence/briefings/policy")
        templates = client.get("/public/live-intelligence/briefings/templates")
        listing = client.get("/public/live-intelligence/briefings")
        detail = client.get(f"/public/live-intelligence/briefings/{draft['briefing_id']}")
        export = client.get(f"/public/live-intelligence/briefings/{draft['briefing_id']}/export?format=markdown")
    finally:
        main.app.dependency_overrides.pop(main.get_settings, None)
    assert policy.status_code == 200
    assert templates.status_code == 200
    assert listing.status_code == 200 and listing.json()["count"] == 1
    assert detail.status_code == 200
    assert export.status_code == 200 and "## Sources" in export.text
