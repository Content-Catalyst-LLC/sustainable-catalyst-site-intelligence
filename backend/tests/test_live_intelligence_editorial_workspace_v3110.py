from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app import main
from app.config import Settings
from app.live_intelligence_briefings_v3100 import LiveIntelligenceBriefingCenter
from app.live_intelligence_editorial_workspace_v3110 import (
    LiveIntelligenceEditorialWorkspace,
    POLICY_SCHEMA_VERSION,
    editorial_workspace_policy,
)


def settings_for(tmp_path):
    return Settings(
        environment="development",
        live_intelligence_briefings_path=str(tmp_path / "briefings.jsonl"),
        live_intelligence_briefing_packages_path=str(tmp_path / "packages.jsonl"),
        live_intelligence_briefing_handoffs_path=str(tmp_path / "briefing-handoffs.jsonl"),
        live_intelligence_editorial_workspaces_path=str(tmp_path / "editorial-workspaces.jsonl"),
        live_intelligence_editorial_events_path=str(tmp_path / "editorial-events.jsonl"),
        live_intelligence_editorial_orchestration_path=str(tmp_path / "editorial-orchestration.jsonl"),
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


def signal():
    now = datetime.now(timezone.utc).isoformat()
    return {
        "signal_id": "event:climate:editorial",
        "label": "Climate observation",
        "formatted_value": "12.5 °C",
        "signal_family": "climate_earth_systems",
        "source_name": "NOAA",
        "source_url": "https://example.org/source",
        "context_url": "/signal/context",
        "freshness_state": "live",
        "observed_at": now,
        "updated_at": now,
        "geography": {"scope": "country", "label": "United States", "country_code": "USA"},
    }


def centers(tmp_path):
    settings = settings_for(tmp_path)
    briefings = LiveIntelligenceBriefingCenter(settings)
    briefing = briefings.create_draft({
        "title": "Climate editorial briefing",
        "briefing_type": "signal",
        "visibility": "public",
        "signals": [signal()],
    })["briefing"]
    editorial = LiveIntelligenceEditorialWorkspace(settings, briefing_center=briefings)
    return settings, briefings, editorial, briefing


def create_workspace(editorial, briefing):
    return editorial.create_workspace({
        "briefing_id": briefing["briefing_id"],
        "created_by": "Author A",
        "assigned_to": "Editor B",
        "assigned_role": "editor",
    })["workspace"]


def test_policy_discloses_editorial_and_publication_boundaries():
    policy = editorial_workspace_policy()
    assert policy["schema"] == POLICY_SCHEMA_VERSION
    assert policy["boundaries"]["separation_of_duties"] is True
    assert policy["boundaries"]["evidence_mutation_allowed"] is False
    assert policy["boundaries"]["automatic_wordpress_write"] is False


def test_workspace_starts_with_immutable_source_digest(tmp_path):
    _, _, editorial, briefing = centers(tmp_path)
    workspace = create_workspace(editorial, briefing)
    assert workspace["status"] == "drafting"
    assert workspace["immutable_source_digest"]
    assert workspace["content"]["title"] == briefing["title"]
    assert workspace["publication_ready"] is False


def test_assignments_use_editorial_handles_not_contact_information(tmp_path):
    _, _, editorial, briefing = centers(tmp_path)
    workspace = create_workspace(editorial, briefing)
    with pytest.raises(ValueError, match="not contact information"):
        editorial.assign(workspace["workspace_id"], {"actor": "Editor B", "assigned_to": "person@example.com", "assigned_role": "editor"})
    updated = editorial.assign(workspace["workspace_id"], {"actor": "Editor B", "assigned_to": "Fact Checker C", "assigned_role": "fact_checker"})["workspace"]
    assert updated["assigned_role"] == "fact_checker"


def test_revision_changes_copy_but_cannot_rewrite_evidence(tmp_path):
    _, _, editorial, briefing = centers(tmp_path)
    workspace = create_workspace(editorial, briefing)
    revised = editorial.add_revision(workspace["workspace_id"], {
        "actor": "Author A",
        "changes": {"deck": "A verified editorial deck", "limitations": ["Review source methodology."]},
        "reason": "Clarified scope.",
    })["workspace"]
    assert revised["revision_number"] == 1
    assert revised["content"]["deck"] == "A verified editorial deck"
    assert revised["immutable_source_digest"] == workspace["immutable_source_digest"]
    with pytest.raises(ValueError, match="immutable"):
        editorial.add_revision(workspace["workspace_id"], {"actor": "Author A", "changes": {"evidence": []}})


def test_submission_and_separation_of_duties(tmp_path):
    _, _, editorial, briefing = centers(tmp_path)
    workspace = create_workspace(editorial, briefing)
    editorial.submit_for_review(workspace["workspace_id"], {"actor": "Author A", "reason": "Ready for fact and source review."})
    with pytest.raises(ValueError, match="separation of duties"):
        editorial.review(workspace["workspace_id"], {"decision": "approve", "reviewed_by": "Author A", "reason": "Self approved."})
    approved = editorial.review(workspace["workspace_id"], {"decision": "approve", "reviewed_by": "Publisher D", "reason": "Claims, sources, dates, and limitations verified."})["workspace"]
    assert approved["status"] == "approved"
    assert approved["publication_ready"] is True


def test_changes_requested_reopens_revision_flow(tmp_path):
    _, _, editorial, briefing = centers(tmp_path)
    workspace = create_workspace(editorial, briefing)
    editorial.submit_for_review(workspace["workspace_id"], {"actor": "Author A", "reason": "Review requested."})
    changed = editorial.review(workspace["workspace_id"], {"decision": "request_changes", "reviewed_by": "Editor B", "reason": "Add a clearer limitation."})["workspace"]
    assert changed["status"] == "changes_requested"
    revised = editorial.add_revision(workspace["workspace_id"], {"actor": "Author A", "changes": {"limitations": ["Geographic scope is limited."]}})["workspace"]
    assert revised["status"] == "drafting"


def test_orchestration_is_provider_neutral_and_performs_no_write(tmp_path):
    _, _, editorial, briefing = centers(tmp_path)
    workspace = create_workspace(editorial, briefing)
    editorial.submit_for_review(workspace["workspace_id"], {"actor": "Author A", "reason": "Ready."})
    editorial.review(workspace["workspace_id"], {"decision": "approve", "reviewed_by": "Publisher D", "reason": "Verified."})
    plan = editorial.orchestrate(workspace["workspace_id"], {"actor": "Publisher D", "adapters": ["publications", "knowledge_library", "download"]})["orchestration"]
    assert plan["provider_neutral"] is True
    assert plan["publication_performed"] is False
    assert plan["wordpress_write_performed"] is False
    assert all(item["write_performed"] is False for item in plan["adapters"])


def test_orchestration_requires_human_approved_workspace(tmp_path):
    _, _, editorial, briefing = centers(tmp_path)
    workspace = create_workspace(editorial, briefing)
    with pytest.raises(ValueError, match="human-approved"):
        editorial.orchestrate(workspace["workspace_id"], {"actor": "Publisher D", "adapters": ["download"]})


def test_history_and_status_are_aggregate_and_auditable(tmp_path):
    _, _, editorial, briefing = centers(tmp_path)
    workspace = create_workspace(editorial, briefing)
    editorial.assign(workspace["workspace_id"], {"actor": "Editor B", "assigned_to": "Fact Checker C", "assigned_role": "fact_checker"})
    history = editorial.history(workspace["workspace_id"])
    assert [row["event_type"] for row in history] == ["workspace_created", "assignment_changed"]
    status = editorial.status()
    assert status["workspace_count"] == 1
    assert status["automatic_publication"] is False


def test_public_policy_status_and_admin_routes(tmp_path):
    settings, _, editorial, briefing = centers(tmp_path)
    create_workspace(editorial, briefing)
    settings.environment = "production"
    main.app.dependency_overrides[main.get_settings] = lambda: settings
    try:
        client = TestClient(main.app)
        policy = client.get("/public/live-intelligence/editorial/policy")
        status = client.get("/public/live-intelligence/editorial/status")
        unauthorized = client.get("/admin/live-intelligence/editorial")
        authorized = client.get("/admin/live-intelligence/editorial", headers={"X-SC-Intelligence-Token": settings.api_token})
    finally:
        main.app.dependency_overrides.pop(main.get_settings, None)
    assert policy.status_code == 200
    assert status.status_code == 200 and status.json()["workspace_count"] == 1
    assert unauthorized.status_code in {401, 403}
    assert authorized.status_code == 200
