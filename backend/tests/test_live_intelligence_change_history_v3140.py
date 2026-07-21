from datetime import datetime, timezone
import json

import pytest
from fastapi.testclient import TestClient

from app import main
from app.config import Settings
from app.live_intelligence_briefings_v3100 import LiveIntelligenceBriefingCenter
from app.live_intelligence_editorial_workspace_v3110 import LiveIntelligenceEditorialWorkspace
from app.live_intelligence_publication_releases_v3120 import LiveIntelligencePublicationReleaseCenter
from app.live_intelligence_release_operations_v3130 import LiveIntelligenceReleaseOperationsCenter
from app.live_intelligence_change_history_v3140 import (
    LiveIntelligenceChangeHistoryCenter,
    POLICY_SCHEMA_VERSION,
    change_history_policy,
)


def settings_for(tmp_path):
    return Settings(
        environment="development",
        live_intelligence_briefings_path=str(tmp_path / "briefings.jsonl"),
        live_intelligence_briefing_packages_path=str(tmp_path / "briefing-packages.jsonl"),
        live_intelligence_briefing_handoffs_path=str(tmp_path / "briefing-handoffs.jsonl"),
        live_intelligence_editorial_workspaces_path=str(tmp_path / "editorial-workspaces.jsonl"),
        live_intelligence_editorial_events_path=str(tmp_path / "editorial-events.jsonl"),
        live_intelligence_editorial_orchestration_path=str(tmp_path / "editorial-orchestration.jsonl"),
        live_intelligence_publication_releases_path=str(tmp_path / "publication-releases.jsonl"),
        live_intelligence_publication_release_events_path=str(tmp_path / "publication-events.jsonl"),
        live_intelligence_publication_handoffs_path=str(tmp_path / "publication-handoffs.jsonl"),
        live_intelligence_release_deployments_path=str(tmp_path / "deployments.jsonl"),
        live_intelligence_release_operation_events_path=str(tmp_path / "release-operation-events.jsonl"),
        live_intelligence_release_issues_path=str(tmp_path / "issues.jsonl"),
        live_intelligence_release_corrections_path=str(tmp_path / "corrections.jsonl"),
        live_intelligence_release_rollbacks_path=str(tmp_path / "rollbacks.jsonl"),
        live_intelligence_release_operation_handoffs_path=str(tmp_path / "release-operation-handoffs.jsonl"),
        live_intelligence_change_history_notices_path=str(tmp_path / "change-notices.jsonl"),
        live_intelligence_change_history_events_path=str(tmp_path / "change-events.jsonl"),
        live_intelligence_change_history_handoffs_path=str(tmp_path / "change-handoffs.jsonl"),
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


def signal(name="Climate observation"):
    now = datetime.now(timezone.utc).isoformat()
    return {
        "signal_id": f"event:climate:{name.lower().replace(' ', '-')}",
        "label": name,
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


def approved_release(settings, suffix="current"):
    briefings = LiveIntelligenceBriefingCenter(settings)
    briefing = briefings.create_draft({
        "title": f"Climate release {suffix}",
        "briefing_type": "signal",
        "visibility": "public",
        "signals": [signal(suffix)],
    })["briefing"]
    editorial = LiveIntelligenceEditorialWorkspace(settings, briefing_center=briefings)
    workspace = editorial.create_workspace({
        "briefing_id": briefing["briefing_id"],
        "created_by": f"Author {suffix}",
        "assigned_to": f"Editor {suffix}",
        "assigned_role": "editor",
    })["workspace"]
    editorial.submit_for_review(workspace["workspace_id"], {"actor": f"Author {suffix}", "reason": "Ready."})
    workspace = editorial.review(workspace["workspace_id"], {
        "decision": "approve", "reviewed_by": f"Publisher {suffix}", "reason": "Evidence verified."
    })["workspace"]
    releases = LiveIntelligencePublicationReleaseCenter(settings, editorial_center=editorial, briefing_center=briefings)
    release = releases.prepare({
        "workspace_id": workspace["workspace_id"],
        "actor": f"Release manager {suffix}",
        "adapters": ["publications", "wordpress_package", "download"],
        "visibility": "public",
        "target_slug": f"climate-release-{suffix}",
    })["release"]
    releases.validate(release["release_id"], {"actor": f"Validator {suffix}", "reason": "Checksums verified."})
    release = releases.approve(release["release_id"], {
        "approved_by": f"Approver {suffix}", "reason": "Approved for manual delivery."
    })["release"]
    return releases, release


def centers(tmp_path):
    settings = settings_for(tmp_path)
    releases, current = approved_release(settings, "current")
    _, replacement = approved_release(settings, "replacement")
    operations = LiveIntelligenceReleaseOperationsCenter(settings, publication_center=releases)
    history = LiveIntelligenceChangeHistoryCenter(
        settings, release_operations_center=operations, publication_center=releases,
    )
    return settings, releases, operations, history, current, replacement


def approved_correction(operations, current, *, correction_type="correction_notice", replacement=None, public=True):
    issue = operations.report_issue({
        "release_id": current["release_id"],
        "severity": "major",
        "title": "Published record requires review",
        "description": "A source-linked public change record is required.",
        "actor": "Issue Reviewer A",
    })["issue"]
    request = {
        "correction_type": correction_type,
        "summary": "The public record has been corrected and its prior state remains available.",
        "rationale": "The change history must preserve evidence lineage and explain the update.",
        "actor": "Correction Author B",
    }
    if replacement is not None:
        request["replacement_release_id"] = replacement["release_id"]
    correction = operations.propose_correction(issue["issue_id"], request)["correction"]
    return operations.approve_correction(correction["correction_id"], {
        "approved_by": "Correction Approver C",
        "reason": "Correction and source lineage verified.",
        "public_visible": public,
    })["correction"]


def test_policy_declares_append_only_no_delete_boundary():
    policy = change_history_policy()
    assert policy["schema"] == POLICY_SCHEMA_VERSION
    assert policy["boundaries"]["original_release_retained"] is True
    assert policy["boundaries"]["append_only_public_history"] is True
    assert policy["boundaries"]["destination_content_deleted"] is False
    assert policy["boundaries"]["evidence_rewritten"] is False


def test_prepare_requires_approved_public_correction(tmp_path):
    _, _, operations, history, current, _ = centers(tmp_path)
    private = approved_correction(operations, current, public=False)
    with pytest.raises(ValueError, match="approved public correction"):
        history.prepare_notice({"correction_id": private["correction_id"], "actor": "Notice Author D"})


def test_notice_approval_requires_separation_and_is_public_append_only(tmp_path):
    _, _, operations, history, current, _ = centers(tmp_path)
    correction = approved_correction(operations, current)
    notice = history.prepare_notice({
        "correction_id": correction["correction_id"],
        "notice_type": "clarification",
        "scope": "source_link",
        "title": "Source-link clarification",
        "actor": "Notice Author D",
    })["notice"]
    with pytest.raises(ValueError, match="separation of duties"):
        history.approve_notice(notice["notice_id"], {"approved_by": "Notice Author D", "reason": "Self approval."})
    approved = history.approve_notice(notice["notice_id"], {
        "approved_by": "Notice Approver E", "reason": "Public wording and evidence links verified."
    })["notice"]
    assert approved["status"] == "approved"
    assert approved["original_release_retained"] is True
    assert approved["deletion_performed"] is False
    assert history.public_history()[0]["notice_id"] == approved["notice_id"]


def test_retraction_requires_retention_acknowledgement_and_never_deletes(tmp_path):
    _, _, operations, history, current, _ = centers(tmp_path)
    correction = approved_correction(operations, current, correction_type="withdrawal")
    notice = history.prepare_notice({"correction_id": correction["correction_id"], "actor": "Retraction Author D"})["notice"]
    assert notice["notice_type"] == "retraction"
    with pytest.raises(ValueError, match="acknowledge"):
        history.approve_notice(notice["notice_id"], {"approved_by": "Retraction Approver E", "reason": "Reviewed."})
    approved = history.approve_notice(notice["notice_id"], {
        "approved_by": "Retraction Approver E",
        "reason": "Retraction basis and preserved original record verified.",
        "original_record_retained_acknowledged": True,
    })["notice"]
    lineage = history.release_lineage(current["release_id"])
    assert approved["deletion_performed"] is False
    assert lineage["release"]["change_state"] == "retracted"
    assert lineage["release"]["original_record_retained"] is True


def test_replacement_notice_links_both_immutable_releases(tmp_path):
    _, _, operations, history, current, replacement = centers(tmp_path)
    correction = approved_correction(operations, current, correction_type="replacement", replacement=replacement)
    notice = history.prepare_notice({"correction_id": correction["correction_id"], "actor": "Replacement Author D"})["notice"]
    notice = history.approve_notice(notice["notice_id"], {
        "approved_by": "Replacement Approver E", "reason": "Both release checksums verified."
    })["notice"]
    original_lineage = history.release_lineage(current["release_id"])
    replacement_lineage = history.release_lineage(replacement["release_id"])
    assert notice["replacement_release_sha256"] == replacement["release_sha256"]
    assert original_lineage["release"]["change_state"] == "superseded"
    assert replacement_lineage["incoming_changes"][0]["affected_release_id"] == current["release_id"]


def test_draft_and_private_records_do_not_enter_public_history(tmp_path):
    _, _, operations, history, current, _ = centers(tmp_path)
    correction = approved_correction(operations, current)
    history.prepare_notice({"correction_id": correction["correction_id"], "actor": "Notice Author D"})
    assert history.public_history() == []


def test_change_package_supports_json_and_markdown(tmp_path):
    _, _, operations, history, current, _ = centers(tmp_path)
    correction = approved_correction(operations, current)
    notice = history.prepare_notice({"correction_id": correction["correction_id"], "actor": "Notice Author D"})["notice"]
    notice = history.approve_notice(notice["notice_id"], {
        "approved_by": "Notice Approver E", "reason": "Approved."
    })["notice"]
    media, body = history.package_payload(notice["notice_id"], "json")
    package = json.loads(body)
    assert media == "application/json"
    assert package["notice"]["notice_sha256"] == notice["notice_sha256"]
    assert package["deletion_performed"] is False
    media, body = history.package_payload(notice["notice_id"], "markdown")
    assert media == "text/markdown"
    assert "Original release retained: Yes" in body


def test_handoff_is_manual_and_contains_no_identity_or_credentials(tmp_path):
    _, _, operations, history, current, _ = centers(tmp_path)
    correction = approved_correction(operations, current)
    notice = history.prepare_notice({"correction_id": correction["correction_id"], "actor": "Notice Author D"})["notice"]
    notice = history.approve_notice(notice["notice_id"], {
        "approved_by": "Notice Approver E", "reason": "Approved."
    })["notice"]
    handoff = history.create_handoff(notice["notice_id"], {
        "actor": "Manual Publisher F", "adapters": ["wordpress_package", "download"]
    })["handoff"]
    assert handoff["destination_write_performed"] is False
    assert handoff["deletion_performed"] is False
    assert handoff["credentials_included"] is False
    with pytest.raises(ValueError, match="outside release operations"):
        history.create_handoff(notice["notice_id"], {"actor": "Publisher F", "api_key": "secret"})


def test_status_history_and_public_routes_are_read_only(tmp_path):
    settings, _, operations, history, current, _ = centers(tmp_path)
    correction = approved_correction(operations, current)
    notice = history.prepare_notice({"correction_id": correction["correction_id"], "actor": "Notice Author D"})["notice"]
    history.approve_notice(notice["notice_id"], {"approved_by": "Notice Approver E", "reason": "Approved."})
    assert history.status()["public_notice_count"] == 1
    assert history.history(notice["notice_id"])[0]["event_type"] == "notice_prepared"

    settings.environment = "production"
    main.app.dependency_overrides[main.get_settings] = lambda: settings
    try:
        client = TestClient(main.app)
        assert client.get("/public/live-intelligence/change-history/policy").status_code == 200
        assert client.get("/public/live-intelligence/change-history/status").status_code == 200
        public = client.get("/public/live-intelligence/change-history")
        assert public.status_code == 200
        assert public.json()["history"][0]["deletion_performed"] is False
        lineage = client.get(f"/public/live-intelligence/change-history/releases/{current['release_id']}")
        assert lineage.status_code == 200
        assert client.get("/admin/live-intelligence/change-history").status_code == 401
        assert client.get("/admin/live-intelligence/change-history", headers={"X-SC-Intelligence-Token": settings.api_token}).status_code == 200
    finally:
        main.app.dependency_overrides.clear()
