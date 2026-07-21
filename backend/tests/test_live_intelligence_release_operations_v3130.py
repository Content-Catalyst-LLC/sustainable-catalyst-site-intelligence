from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app import main
from app.config import Settings
from app.live_intelligence_briefings_v3100 import LiveIntelligenceBriefingCenter
from app.live_intelligence_editorial_workspace_v3110 import LiveIntelligenceEditorialWorkspace
from app.live_intelligence_publication_releases_v3120 import LiveIntelligencePublicationReleaseCenter
from app.live_intelligence_release_operations_v3130 import (
    LiveIntelligenceReleaseOperationsCenter,
    POLICY_SCHEMA_VERSION,
    release_operations_policy,
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
    editorial.submit_for_review(workspace["workspace_id"], {"actor": f"Author {suffix}", "reason": "Ready for review."})
    workspace = editorial.review(workspace["workspace_id"], {"decision": "approve", "reviewed_by": f"Publisher {suffix}", "reason": "Evidence verified."})["workspace"]
    releases = LiveIntelligencePublicationReleaseCenter(settings, editorial_center=editorial, briefing_center=briefings)
    release = releases.prepare({
        "workspace_id": workspace["workspace_id"],
        "actor": f"Release manager {suffix}",
        "adapters": ["publications", "wordpress_package", "download"],
        "visibility": "public",
        "target_slug": f"climate-release-{suffix}",
    })["release"]
    releases.validate(release["release_id"], {"actor": f"Validator {suffix}", "reason": "Checksums verified."})
    release = releases.approve(release["release_id"], {"approved_by": f"Approver {suffix}", "reason": "Approved for manual delivery."})["release"]
    return releases, release


def centers(tmp_path):
    settings = settings_for(tmp_path)
    releases, current = approved_release(settings, "current")
    _, previous = approved_release(settings, "previous")
    operations = LiveIntelligenceReleaseOperationsCenter(settings, publication_center=releases)
    return settings, releases, operations, current, previous


def deployment(operations, release):
    return operations.register_deployment({
        "release_id": release["release_id"],
        "adapter_id": "wordpress_package",
        "environment": "production",
        "destination_label": "Sustainable Catalyst WordPress",
        "destination_reference": "https://sustainablecatalyst.com/live-intelligence/climate-release",
        "actor": "Deployment Recorder A",
    })["deployment"]


def test_policy_discloses_manual_no_write_boundary():
    policy = release_operations_policy()
    assert policy["schema"] == POLICY_SCHEMA_VERSION
    assert policy["boundaries"]["deployment_performed"] is False
    assert policy["boundaries"]["rollback_performed"] is False
    assert policy["boundaries"]["destination_write_performed"] is False
    assert policy["boundaries"]["human_verification_required"] is True


def test_deployment_receipt_requires_approved_release(tmp_path):
    settings = settings_for(tmp_path)
    briefings = LiveIntelligenceBriefingCenter(settings)
    editorial = LiveIntelligenceEditorialWorkspace(settings, briefing_center=briefings)
    releases = LiveIntelligencePublicationReleaseCenter(settings, editorial_center=editorial, briefing_center=briefings)
    operations = LiveIntelligenceReleaseOperationsCenter(settings, publication_center=releases)
    with pytest.raises(KeyError):
        operations.register_deployment({
            "release_id": "publication-release:missing",
            "adapter_id": "wordpress_package",
            "destination_label": "WordPress",
            "destination_reference": "manual-receipt",
            "actor": "Recorder A",
        })


def test_register_and_verify_deployment_checks_integrity_and_public_safeguards(tmp_path):
    _, _, operations, current, _ = centers(tmp_path)
    receipt = deployment(operations, current)
    result = operations.verify_deployment(receipt["deployment_id"], {
        "actor": "Verifier B",
        "reason": "Published package and safeguards reviewed manually.",
        "observed_release_sha256": receipt["release_sha256"],
        "observed_payload_sha256": receipt["payload_sha256"],
        "observed_package_sha256": receipt["package_sha256"],
        "destination_accessible": True,
        "source_links_present": True,
        "freshness_labels_present": True,
        "correction_path_present": True,
    })
    assert result["verification"]["passed"] is True
    assert result["deployment"]["state"] == "verified"
    assert result["deployment"]["network_fetch_performed"] is False


def test_verification_failure_is_honest_and_does_not_claim_network_access(tmp_path):
    _, _, operations, current, _ = centers(tmp_path)
    receipt = deployment(operations, current)
    result = operations.verify_deployment(receipt["deployment_id"], {
        "actor": "Verifier B",
        "reason": "Package mismatch found.",
        "observed_release_sha256": receipt["release_sha256"],
        "observed_payload_sha256": receipt["payload_sha256"],
        "observed_package_sha256": "0" * 64,
        "destination_accessible": True,
        "source_links_present": True,
        "freshness_labels_present": True,
        "correction_path_present": True,
    })
    assert result["verification"]["passed"] is False
    assert result["deployment"]["state"] == "verification_failed"
    assert result["deployment"]["network_fetch_performed"] is False


def test_identity_credentials_and_webhooks_are_rejected(tmp_path):
    _, _, operations, current, _ = centers(tmp_path)
    with pytest.raises(ValueError, match="outside release operations"):
        operations.register_deployment({
            "release_id": current["release_id"],
            "adapter_id": "wordpress_package",
            "destination_label": "WordPress",
            "destination_reference": "manual",
            "actor": "Recorder A",
            "api_key": "secret",
        })
    with pytest.raises(ValueError, match="not contact information"):
        operations.register_deployment({
            "release_id": current["release_id"],
            "adapter_id": "wordpress_package",
            "destination_label": "WordPress",
            "destination_reference": "manual",
            "actor": "person@example.com",
        })


    with pytest.raises(ValueError, match="embedded credentials"):
        operations.register_deployment({
            "release_id": current["release_id"],
            "adapter_id": "wordpress_package",
            "destination_label": "WordPress",
            "destination_reference": "https://example.org/page?access_token=secret",
            "actor": "Recorder A",
        })


def test_issue_and_public_correction_require_separate_human_approval(tmp_path):
    _, _, operations, current, _ = centers(tmp_path)
    receipt = deployment(operations, current)
    issue = operations.report_issue({
        "deployment_id": receipt["deployment_id"],
        "severity": "major",
        "title": "Source link omitted",
        "description": "The published page omitted one source link.",
        "evidence_references": ["manual-review:2026-07-21"],
        "actor": "Issue Reviewer C",
    })["issue"]
    correction = operations.propose_correction(issue["issue_id"], {
        "correction_type": "correction_notice",
        "summary": "A source link was restored.",
        "rationale": "Public evidence navigation must remain complete.",
        "actor": "Correction Author D",
    })["correction"]
    with pytest.raises(ValueError, match="separation of duties"):
        operations.approve_correction(correction["correction_id"], {
            "approved_by": "Correction Author D",
            "reason": "Self approval.",
            "public_visible": True,
        })
    approved = operations.approve_correction(correction["correction_id"], {
        "approved_by": "Correction Approver E",
        "reason": "Correction text and source lineage verified.",
        "public_visible": True,
    })["correction"]
    assert approved["status"] == "approved"
    assert operations.public_corrections()[0]["summary"] == "A source link was restored."


def test_private_corrections_never_leak_to_public_feed(tmp_path):
    _, _, operations, current, _ = centers(tmp_path)
    receipt = deployment(operations, current)
    issue = operations.report_issue({
        "deployment_id": receipt["deployment_id"],
        "severity": "minor",
        "title": "Internal formatting review",
        "description": "Formatting requires internal review.",
        "actor": "Reviewer C",
    })["issue"]
    correction = operations.propose_correction(issue["issue_id"], {
        "correction_type": "correction_notice",
        "summary": "Formatting adjusted.",
        "rationale": "Internal presentation consistency.",
        "actor": "Author D",
    })["correction"]
    operations.approve_correction(correction["correction_id"], {
        "approved_by": "Approver E",
        "reason": "Approved as an internal correction record.",
        "public_visible": False,
    })
    assert operations.public_corrections() == []


def test_rollback_package_requires_approved_target_and_separate_approval(tmp_path):
    _, _, operations, current, previous = centers(tmp_path)
    receipt = deployment(operations, current)
    rollback = operations.prepare_rollback(receipt["deployment_id"], {
        "target_release_id": previous["release_id"],
        "reason": "Restore the previously verified release while correction review proceeds.",
        "actor": "Rollback Preparer F",
    })["rollback"]
    assert rollback["rollback_performed"] is False
    with pytest.raises(ValueError, match="separation of duties"):
        operations.approve_rollback(rollback["rollback_id"], {
            "approved_by": "Rollback Preparer F",
            "reason": "Self approval.",
        })
    approved = operations.approve_rollback(rollback["rollback_id"], {
        "approved_by": "Rollback Approver G",
        "reason": "Target checksums and operational need verified.",
    })["rollback"]
    assert approved["status"] == "approved"
    assert approved["destination_write_performed"] is False


def test_correction_and_rollback_handoffs_are_manual_no_write_receipts(tmp_path):
    _, _, operations, current, previous = centers(tmp_path)
    receipt = deployment(operations, current)
    rollback = operations.prepare_rollback(receipt["deployment_id"], {
        "target_release_id": previous["release_id"],
        "reason": "Controlled rollback prepared.",
        "actor": "Preparer F",
    })["rollback"]
    rollback = operations.approve_rollback(rollback["rollback_id"], {
        "approved_by": "Approver G",
        "reason": "Approved.",
    })["rollback"]
    handoff = operations.create_handoff("rollback", rollback["rollback_id"], {
        "actor": "Operations Publisher H",
        "adapters": ["wordpress_package", "download"],
    })["handoff"]
    assert handoff["rollback_performed"] is False
    assert handoff["destination_write_performed"] is False
    assert all(row["destination_write_performed"] is False for row in handoff["states"])


def test_status_history_public_routes_and_admin_protection(tmp_path):
    settings, _, operations, current, _ = centers(tmp_path)
    receipt = deployment(operations, current)
    assert operations.history(receipt["deployment_id"])[0]["event_type"] == "deployment_reported"
    settings.environment = "production"
    main.app.dependency_overrides[main.get_settings] = lambda: settings
    try:
        client = TestClient(main.app)
        policy = client.get("/public/live-intelligence/release-operations/policy")
        status = client.get("/public/live-intelligence/release-operations/status")
        corrections = client.get("/public/live-intelligence/release-operations/corrections")
        unauthorized = client.get("/admin/live-intelligence/release-operations")
        authorized = client.get("/admin/live-intelligence/release-operations", headers={"X-SC-Intelligence-Token": settings.api_token})
    finally:
        main.app.dependency_overrides.pop(main.get_settings, None)
    assert policy.status_code == 200
    assert status.status_code == 200 and status.json()["deployment_count"] == 1
    assert corrections.status_code == 200 and corrections.json()["destination_write_performed"] is False
    assert unauthorized.status_code in {401, 403}
    assert authorized.status_code == 200
