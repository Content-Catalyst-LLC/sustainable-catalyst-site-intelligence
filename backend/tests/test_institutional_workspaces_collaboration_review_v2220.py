from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from app.config import Settings, get_settings
from app.institutional_workspaces_v2220 import InstitutionalWorkspaceCenter, SCHEMA_VERSION
from app.main import app


def settings(tmp_path: Path) -> Settings:
    root = tmp_path / "workspaces"
    policy = Path(__file__).resolve().parents[1] / "data/institutional_workspaces_policy_v2220.json"
    return Settings(
        institutional_workspaces_root_path=str(root),
        institutional_workspaces_workspaces_path=str(root / "workspaces.jsonl"),
        institutional_workspaces_members_path=str(root / "members.jsonl"),
        institutional_workspaces_assignments_path=str(root / "assignments.jsonl"),
        institutional_workspaces_comments_path=str(root / "comments.jsonl"),
        institutional_workspaces_reviews_path=str(root / "reviews.jsonl"),
        institutional_workspaces_collections_path=str(root / "collections.jsonl"),
        institutional_workspaces_activity_path=str(root / "activity.jsonl"),
        institutional_workspaces_retention_path=str(root / "retention.jsonl"),
        institutional_workspaces_policy_path=str(policy),
        institutional_workspaces_default_retention_days=365,
    )


def center(tmp_path: Path, now: datetime | None = None) -> InstitutionalWorkspaceCenter:
    stamp = now or datetime(2026, 7, 16, 15, tzinfo=timezone.utc)
    return InstitutionalWorkspaceCenter(settings(tmp_path), now_fn=lambda: stamp)


def workspace(c: InstitutionalWorkspaceCenter):
    return c.create_workspace({
        "workspace_id": "workspace:climate-review",
        "title": "Climate evidence review",
        "summary": "Shared institutional review workspace.",
        "visibility": "private",
        "topics": ["climate", "evidence"],
        "institution": {"name": "Example Institute"},
    })


def test_workspace_roles_and_private_public_boundary(tmp_path):
    c = center(tmp_path)
    row = workspace(c)
    assert row["status"] == "draft"
    assert c.public_summary()["workspaces"] == []
    diagnostics = c.diagnostics(public=True)
    assert diagnostics["public_accounts_required"] is False
    assert diagnostics["persistent_authentication_claimed"] is False
    assert set(diagnostics["roles"]) == {"administrator", "analyst", "publisher", "reviewer"}


def test_member_role_permissions_are_explicit(tmp_path):
    c = center(tmp_path)
    workspace(c)
    member = c.add_member("workspace:climate-review", {"subject_id": "member:1", "display_label": "Analyst One", "role": "analyst"})
    assert "manage_sources" in member["permissions"]
    assert "publish" not in member["permissions"]
    with pytest.raises(PermissionError):
        c.add_member("workspace:climate-review", {"subject_id": "member:2", "role": "reviewer"}, actor_role="analyst")


def test_assignments_comments_and_activity_are_private(tmp_path):
    c = center(tmp_path)
    workspace(c)
    assignment = c.save_assignment("workspace:climate-review", {"title": "Verify source", "priority": "high"}, actor_role="analyst", actor_id="member:1")
    comment = c.add_comment("workspace:climate-review", {"body": "Check the reporting period.", "target_type": "assignment", "target_id": assignment["assignment_id"]}, actor_role="analyst", actor_id="member:1")
    assert assignment["status"] == "open"
    assert comment["public"] is False
    detail = c.workspace_detail("workspace:climate-review")
    assert detail["activity"]
    assert "comments" not in c._public_workspace(c._workspace("workspace:climate-review"))


def test_evidence_review_requires_human_rationale(tmp_path):
    c = center(tmp_path)
    workspace(c)
    with pytest.raises(ValueError, match="rationale"):
        c.review_evidence("workspace:climate-review", {"evidence_id": "evidence:1", "decision": "approved"})
    review = c.review_evidence("workspace:climate-review", {
        "evidence_id": "evidence:1", "decision": "approved", "rationale": "Source and methodology verified.", "public_eligible": True,
    }, actor_role="reviewer", actor_id="reviewer:1")
    assert review["automatic_decision"] is False
    assert review["public_eligible"] is True


def test_publication_requires_approved_evidence_and_resolved_urgent_work(tmp_path):
    c = center(tmp_path)
    workspace(c)
    with pytest.raises(ValueError, match="approved"):
        c.update_workspace("workspace:climate-review", {"status": "published", "visibility": "public"}, actor_role="publisher")
    c.review_evidence("workspace:climate-review", {"evidence_id": "evidence:1", "decision": "approved", "rationale": "Reviewed.", "public_eligible": True})
    urgent = c.save_assignment("workspace:climate-review", {"title": "Resolve contradiction", "priority": "urgent"}, actor_role="analyst")
    with pytest.raises(ValueError, match="urgent"):
        c.update_workspace("workspace:climate-review", {"status": "published", "visibility": "public"}, actor_role="administrator")
    c.save_assignment("workspace:climate-review", {"assignment_id": urgent["assignment_id"], "title": urgent["title"], "priority": "urgent", "status": "completed"}, actor_role="administrator")
    published = c.update_workspace("workspace:climate-review", {"status": "published", "visibility": "public"}, actor_role="administrator")
    assert published["published_at"]
    assert c.public_summary()["workspaces"][0]["approved_evidence_count"] == 1


def test_public_source_collection_filters_unapproved_evidence(tmp_path):
    c = center(tmp_path)
    workspace(c)
    c.review_evidence("workspace:climate-review", {"evidence_id": "evidence:approved", "decision": "approved", "rationale": "Verified.", "public_eligible": True})
    collection = c.save_collection("workspace:climate-review", {
        "title": "Public sources", "visibility": "public", "source_ids": ["source:1"], "evidence_ids": ["evidence:approved", "evidence:private"],
    })
    assert collection["public_evidence_ids"] == ["evidence:approved"]


def test_retention_is_preview_first_and_confirmed(tmp_path):
    old = datetime(2024, 1, 1, tzinfo=timezone.utc)
    c_old = center(tmp_path, old)
    workspace(c_old)
    assignment = c_old.save_assignment("workspace:climate-review", {"title": "Old task", "status": "completed"}, actor_role="administrator")
    comment = c_old.add_comment("workspace:climate-review", {"body": "Resolved note", "resolved": True})
    c_now = center(tmp_path, datetime(2026, 7, 16, tzinfo=timezone.utc))
    preview = c_now.retention_preview("workspace:climate-review", 365)
    assert preview["preview_only"] is True
    assert assignment["assignment_id"] in preview["candidates"]["assignments"]
    assert comment["comment_id"] in preview["candidates"]["comments"]
    with pytest.raises(ValueError, match="confirm=true"):
        c_now.apply_retention("workspace:climate-review", {"cutoff_days": 365})
    receipt = c_now.apply_retention("workspace:climate-review", {"cutoff_days": 365, "confirm": True})
    assert receipt["deleted"]["assignments"] == 1


def test_export_archive_has_digest_and_no_remote_write_claim(tmp_path):
    c = center(tmp_path)
    workspace(c)
    media, body = c.export_workspace("workspace:climate-review", "publisher", "json")
    assert media == "application/json"
    assert b'"sha256"' in body
    assert b"does not provision accounts" in body
    media, body = c.export_workspace("workspace:climate-review", "administrator", "zip")
    assert media == "application/zip" and body.startswith(b"PK")


def test_public_api_exposes_only_published_workspace(tmp_path):
    current = settings(tmp_path)
    app.dependency_overrides[get_settings] = lambda: current
    try:
        client = TestClient(app)
        create = client.post("/admin/institutional-workspaces", json={"workspace_id": "workspace:api", "title": "API workspace"})
        assert create.status_code == 200
        public = client.get("/public/institutional-workspaces").json()
        assert public["version"] == "3.8.0"
        assert public["workspaces"] == []
        review = client.post("/admin/institutional-workspaces/workspace:api/evidence-reviews", json={"evidence_id": "evidence:1", "decision": "approved", "rationale": "Verified.", "public_eligible": True, "actor_role": "reviewer"})
        assert review.status_code == 200
        publish = client.post("/admin/institutional-workspaces/workspace:api", json={"status": "published", "visibility": "public"})
        assert publish.status_code == 200
        public = client.get("/public/institutional-workspaces").json()
        assert len(public["workspaces"]) == 1
        assert "members" not in public["workspaces"][0]
    finally:
        app.dependency_overrides.clear()


def test_release_schema_and_control_center(tmp_path):
    c = center(tmp_path)
    workspace(c)
    data = c.control_center()
    assert data["schema"] == SCHEMA_VERSION
    assert data["authentication"]["persistent_identity_provider_included"] is False
    assert data["summary"]["workspace_count"] == 1
