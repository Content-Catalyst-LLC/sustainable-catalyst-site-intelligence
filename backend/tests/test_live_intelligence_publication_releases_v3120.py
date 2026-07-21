from datetime import datetime, timezone

import json
import pytest
from fastapi.testclient import TestClient

from app import main
from app.config import Settings
from app.live_intelligence_briefings_v3100 import LiveIntelligenceBriefingCenter
from app.live_intelligence_editorial_workspace_v3110 import LiveIntelligenceEditorialWorkspace
from app.live_intelligence_publication_releases_v3120 import (
    LiveIntelligencePublicationReleaseCenter, POLICY_SCHEMA_VERSION,
    adapter_catalog, publication_release_policy,
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
    now=datetime.now(timezone.utc).isoformat()
    return {"signal_id":"event:climate:release","label":"Climate observation","formatted_value":"12.5 °C","signal_family":"climate_earth_systems","source_name":"NOAA","source_url":"https://example.org/source","context_url":"/signal/context","freshness_state":"live","observed_at":now,"updated_at":now,"geography":{"scope":"country","label":"United States","country_code":"USA"}}


def centers(tmp_path):
    settings=settings_for(tmp_path)
    briefings=LiveIntelligenceBriefingCenter(settings)
    briefing=briefings.create_draft({"title":"Climate release briefing","briefing_type":"signal","visibility":"public","signals":[signal()]})["briefing"]
    editorial=LiveIntelligenceEditorialWorkspace(settings,briefing_center=briefings)
    workspace=editorial.create_workspace({"briefing_id":briefing["briefing_id"],"created_by":"Author A","assigned_to":"Editor B","assigned_role":"editor"})["workspace"]
    editorial.submit_for_review(workspace["workspace_id"],{"actor":"Author A","reason":"Ready for release review."})
    workspace=editorial.review(workspace["workspace_id"],{"decision":"approve","reviewed_by":"Publisher D","reason":"Claims, evidence, and limitations verified."})["workspace"]
    releases=LiveIntelligencePublicationReleaseCenter(settings,editorial_center=editorial,briefing_center=briefings)
    return settings,briefings,editorial,releases,workspace


def prepared(releases,workspace):
    return releases.prepare({"workspace_id":workspace["workspace_id"],"actor":"Release Manager E","adapters":["publications","knowledge_library","wordpress_package","download"],"visibility":"public","target_slug":"climate-release"})["release"]


def test_policy_and_adapter_catalog_disclose_no_write_boundary():
    policy=publication_release_policy()
    assert policy["schema"]==POLICY_SCHEMA_VERSION
    assert policy["boundaries"]["automatic_wordpress_write"] is False
    assert policy["boundaries"]["package_checksums_required"] is True
    assert all(item["destination_write_performed"] is False for item in adapter_catalog()["adapters"])


def test_prepare_requires_approved_workspace(tmp_path):
    settings=settings_for(tmp_path)
    briefings=LiveIntelligenceBriefingCenter(settings)
    briefing=briefings.create_draft({"title":"Draft","briefing_type":"signal","visibility":"public","signals":[signal()]})["briefing"]
    editorial=LiveIntelligenceEditorialWorkspace(settings,briefing_center=briefings)
    workspace=editorial.create_workspace({"briefing_id":briefing["briefing_id"],"created_by":"Author A"})["workspace"]
    releases=LiveIntelligencePublicationReleaseCenter(settings,editorial_center=editorial,briefing_center=briefings)
    with pytest.raises(ValueError,match="human-approved"):
        releases.prepare({"workspace_id":workspace["workspace_id"],"actor":"Release Manager E"})


def test_prepare_builds_immutable_adapter_packages(tmp_path):
    _,_,_,releases,workspace=centers(tmp_path)
    release=prepared(releases,workspace)
    assert release["status"]=="prepared"
    assert release["payload_sha256"]
    assert len(release["packages"])==4
    assert all(item["package_sha256"] for item in release["packages"])
    assert release["automatic_wordpress_write"] is False


def test_identity_credentials_and_webhooks_are_rejected(tmp_path):
    _,_,_,releases,workspace=centers(tmp_path)
    with pytest.raises(ValueError,match="outside release packages"):
        releases.prepare({"workspace_id":workspace["workspace_id"],"actor":"Release Manager E","webhook_url":"https://example.org/hook"})
    with pytest.raises(ValueError,match="not contact information"):
        releases.prepare({"workspace_id":workspace["workspace_id"],"actor":"person@example.com"})


def test_validation_detects_unchanged_evidence_and_packages(tmp_path):
    _,_,_,releases,workspace=centers(tmp_path)
    release=prepared(releases,workspace)
    result=releases.validate(release["release_id"],{"actor":"Validator F","reason":"Checksums and evidence lineage verified."})
    assert result["validation"]["passed"] is True
    assert all(result["validation"]["checks"].values())
    assert result["release"]["status"]=="validated"


def test_release_approval_requires_separation_of_duties(tmp_path):
    _,_,_,releases,workspace=centers(tmp_path)
    release=prepared(releases,workspace)
    releases.validate(release["release_id"],{"actor":"Validator F","reason":"Validated."})
    with pytest.raises(ValueError,match="separation of duties"):
        releases.approve(release["release_id"],{"approved_by":"Validator F","reason":"Self approval."})
    approved=releases.approve(release["release_id"],{"approved_by":"Release Approver G","reason":"Approved for controlled manual delivery."})["release"]
    assert approved["status"]=="approved"


def test_handoff_receipts_perform_no_destination_write(tmp_path):
    _,_,_,releases,workspace=centers(tmp_path)
    release=prepared(releases,workspace)
    releases.validate(release["release_id"],{"actor":"Validator F","reason":"Validated."})
    releases.approve(release["release_id"],{"approved_by":"Release Approver G","reason":"Approved."})
    handoff=releases.create_handoff(release["release_id"],{"actor":"Publisher H","adapters":["publications","download"]})["handoff"]
    assert handoff["destination_write_performed"] is False
    assert handoff["credentials_included"] is False
    assert all(row["destination_write_performed"] is False for row in handoff["receipts"])


def test_approved_package_exports_json_and_markdown(tmp_path):
    _,_,_,releases,workspace=centers(tmp_path)
    release=prepared(releases,workspace)
    releases.validate(release["release_id"],{"actor":"Validator F","reason":"Validated."})
    releases.approve(release["release_id"],{"approved_by":"Release Approver G","reason":"Approved."})
    media,body=releases.package_payload(release["release_id"],"json")
    assert media=="application/json" and json.loads(body)["destination_write_performed"] is False
    media,body=releases.package_payload(release["release_id"],"markdown")
    assert media=="text/markdown" and "Destination write performed: no" in body


def test_status_and_history_are_aggregate_and_auditable(tmp_path):
    _,_,_,releases,workspace=centers(tmp_path)
    release=prepared(releases,workspace)
    releases.validate(release["release_id"],{"actor":"Validator F","reason":"Validated."})
    history=releases.history(release["release_id"])
    assert [row["event_type"] for row in history]==["release_prepared","release_validated"]
    status=releases.status()
    assert status["release_count"]==1
    assert status["institutional_write_performed"] is False


def test_public_policy_status_catalog_and_protected_admin_route(tmp_path):
    settings,_,_,releases,workspace=centers(tmp_path)
    prepared(releases,workspace)
    settings.environment="production"
    main.app.dependency_overrides[main.get_settings]=lambda:settings
    try:
        client=TestClient(main.app)
        policy=client.get("/public/live-intelligence/publication-releases/policy")
        adapters=client.get("/public/live-intelligence/publication-releases/adapters")
        status=client.get("/public/live-intelligence/publication-releases/status")
        unauthorized=client.get("/admin/live-intelligence/publication-releases")
        authorized=client.get("/admin/live-intelligence/publication-releases",headers={"X-SC-Intelligence-Token":settings.api_token})
    finally:
        main.app.dependency_overrides.pop(main.get_settings,None)
    assert policy.status_code==200
    assert adapters.status_code==200 and adapters.json()["adapters"]
    assert status.status_code==200 and status.json()["release_count"]==1
    assert unauthorized.status_code in {401,403}
    assert authorized.status_code==200
