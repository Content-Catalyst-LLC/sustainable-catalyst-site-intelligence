from copy import deepcopy
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app import main
from app.live_intelligence_registry_collections_v3210 import (
    LiveIntelligenceRegistryCollectionsCenter,
    POLICY_SCHEMA_VERSION,
    registry_collections_policy,
)


class FakeDiscovery:
    def __init__(self):
        self.rows = [
            {
                "record_type": "institution",
                "record_id": "preservation-institution:alpha",
                "institution_id": "preservation-institution:alpha",
                "institution_name": "Repository Alpha",
                "title": "Repository Alpha",
                "summary": "Approved university repository with checksum policy.",
                "institution_type": "university_repository",
                "jurisdiction": "US-IL",
                "trust_profile": "policy_reviewed",
                "repository_reference": "https://example.org/repository/alpha",
                "public_policy_reference": "https://example.org/policy/alpha",
                "institution_sha256": "a" * 64,
                "published_at": "2026-07-20T10:00:00Z",
            },
            {
                "record_type": "exchange",
                "record_id": "preservation-exchange:alpha",
                "exchange_id": "preservation-exchange:alpha",
                "title": "Preservation exchange alpha",
                "summary": "BagIt-style public exchange.",
                "profile": "bagit_style",
                "package_sha256": "b" * 64,
                "exchange_sha256": "c" * 64,
                "status": "approved",
                "published_at": "2026-07-21T10:00:00Z",
            },
            {
                "record_type": "attestation",
                "record_id": "preservation-attestation:alpha",
                "institution_id": "preservation-institution:alpha",
                "exchange_id": "preservation-exchange:alpha",
                "institution_name": "Repository Alpha",
                "title": "Repository Alpha attestation",
                "summary": "Independent checksum attestation.",
                "method": "manual_checksum",
                "result": "verified",
                "evidence_reference": "https://example.org/attestation/alpha",
                "attestation_sha256": "d" * 64,
                "published_at": "2026-07-21T11:00:00Z",
            },
        ]

    def records(self):
        return deepcopy(self.rows)

    def search(self, **kwargs):
        rows = deepcopy(self.rows)
        q = str(kwargs.get("query") or "").lower()
        record_type = str(kwargs.get("record_type") or "").lower()
        jurisdiction = str(kwargs.get("jurisdiction") or "").lower()
        if q:
            rows = [row for row in rows if q in (str(row.get("title")) + " " + str(row.get("summary"))).lower()]
        if record_type:
            rows = [row for row in rows if row.get("record_type") == record_type]
        if jurisdiction:
            rows = [row for row in rows if jurisdiction in str(row.get("jurisdiction") or "").lower()]
        rows.sort(key=lambda row: str(row.get("title") or "").lower())
        limit = int(kwargs.get("limit") or 25)
        return {"ok": True, "total": len(rows), "results": rows[:limit]}


def center(tmp_path: Path):
    settings = Settings(
        live_intelligence_registry_collections_views_path=str(tmp_path / "views.jsonl"),
        live_intelligence_registry_collections_path=str(tmp_path / "collections.jsonl"),
        live_intelligence_registry_collections_events_path=str(tmp_path / "events.jsonl"),
        live_intelligence_registry_collections_snapshot_limit=100,
    )
    discovery = FakeDiscovery()
    return discovery, LiveIntelligenceRegistryCollectionsCenter(settings, discovery=discovery)


def approved_view(c):
    row = c.create_view({
        "actor": "Collection Preparer",
        "title": "Illinois preservation institutions",
        "description": "A reproducible registry discovery view.",
        "filter_state": {"record_type": "institution", "jurisdiction": "US-IL", "sort": "name"},
        "public_visible": True,
    })["view"]
    row = c.review_view(row["view_id"], {
        "actor": "Collection Reviewer",
        "note": "Filters and result set reviewed.",
        "evidence_reference": "https://example.org/reviews/view-alpha",
    })["view"]
    return c.approve_view(row["view_id"], {
        "approved_by": "Collection Governor",
        "note": "Approved for public reuse.",
        "public_visible": True,
    })["view"]


def approved_collection(c, view_id):
    row = c.create_collection({
        "actor": "Pathway Preparer",
        "title": "Illinois preservation evidence pathway",
        "purpose": "Connect the approved institution record to its public preservation evidence.",
        "summary": "A public, checksum-bound collection assembled from an approved saved view.",
        "source_view_ids": [view_id],
        "record_ids": ["preservation-exchange:alpha", "preservation-attestation:alpha"],
        "pathway_steps": [
            {"record_id": "preservation-institution:alpha", "rationale": "Start with the approved institution profile."},
            {"record_id": "preservation-exchange:alpha", "rationale": "Follow the preservation exchange package."},
            {"record_id": "preservation-attestation:alpha", "rationale": "Conclude with independent checksum evidence."},
        ],
        "public_visible": True,
    })["collection"]
    row = c.review_collection(row["collection_id"], {
        "actor": "Pathway Reviewer",
        "note": "Record order and evidence rationale reviewed.",
        "evidence_reference": "https://example.org/reviews/collection-alpha",
    })["collection"]
    return c.approve_collection(row["collection_id"], {
        "approved_by": "Pathway Governor",
        "note": "Approved as a public research collection.",
        "public_visible": True,
    })["collection"]


def test_policy_declares_privacy_and_append_only_boundaries():
    policy = registry_collections_policy()
    assert policy["schema"] == POLICY_SCHEMA_VERSION
    assert policy["boundaries"]["visitor_queries_stored"] is False
    assert policy["boundaries"]["visitor_profiles_created"] is False
    assert policy["boundaries"]["approved_snapshots_overwritten"] is False


def test_saved_view_canonicalizes_filters_and_snapshots_results(tmp_path):
    _, c = center(tmp_path)
    view = c.create_view({
        "actor": "View Preparer",
        "title": "Illinois institutions",
        "description": "Public institutions in Illinois.",
        "filter_state": {"jurisdiction": "US-IL", "record_type": "institution", "sort": "name"},
    })["view"]
    assert view["filter_state"] == {"jurisdiction": "us-il", "record_type": "institution", "sort": "name"}
    assert view["snapshot_record_ids"] == ["preservation-institution:alpha"]
    assert len(view["filter_state_sha256"]) == 64


def test_saved_view_requires_separate_reviewer_and_approver(tmp_path):
    _, c = center(tmp_path)
    view = c.create_view({"actor": "Same Role", "title": "A view", "description": "Description", "filter_state": {}})["view"]
    with pytest.raises(ValueError, match="separation"):
        c.review_view(view["view_id"], {"actor": "Same Role", "note": "Review", "evidence_reference": "Evidence"})
    reviewed = c.review_view(view["view_id"], {"actor": "Reviewer", "note": "Review", "evidence_reference": "Evidence"})["view"]
    with pytest.raises(ValueError, match="separate approver"):
        c.approve_view(reviewed["view_id"], {"approved_by": "Reviewer", "note": "Approval"})


def test_public_views_require_explicit_approval_and_visibility(tmp_path):
    _, c = center(tmp_path)
    draft = c.create_view({"actor": "Preparer", "title": "Draft", "description": "Not public", "filter_state": {}})["view"]
    assert draft["status"] == "draft"
    assert c.views(public=True) == []
    public = approved_view(c)
    assert c.views(public=True)[0]["view_id"] == public["view_id"]
    assert "approved_by" not in repr(c.views(public=True))


def test_collection_accepts_approved_views_and_public_records_only(tmp_path):
    _, c = center(tmp_path)
    view = approved_view(c)
    collection = c.create_collection({
        "actor": "Pathway Preparer",
        "title": "Collection",
        "purpose": "Research purpose",
        "summary": "Research summary",
        "source_view_ids": [view["view_id"]],
        "record_ids": ["preservation-exchange:alpha"],
    })["collection"]
    assert collection["record_count"] == 2
    assert collection["record_ids"] == ["preservation-institution:alpha", "preservation-exchange:alpha"]
    with pytest.raises(ValueError, match="approved public"):
        c.create_collection({
            "actor": "Pathway Preparer", "title": "Bad", "purpose": "Purpose", "summary": "Summary",
            "record_ids": ["private-record:missing"],
        })


def test_evidence_pathway_preserves_order_and_rationale(tmp_path):
    _, c = center(tmp_path)
    view = approved_view(c)
    collection = approved_collection(c, view["view_id"])
    pathway = c.pathway(collection["collection_id"], public=True)
    assert [step["sequence"] for step in pathway["pathway"]] == [1, 2, 3]
    assert pathway["pathway"][0]["rationale"].startswith("Start with")
    assert pathway["visitor_profiles_created"] is False


def test_collection_drift_requires_explicit_acknowledgment(tmp_path):
    discovery, c = center(tmp_path)
    view = approved_view(c)
    draft = c.create_collection({
        "actor": "Pathway Preparer", "title": "Drift collection", "purpose": "Purpose", "summary": "Summary",
        "source_view_ids": [view["view_id"]],
    })["collection"]
    discovery.rows[0]["summary"] = "Public record changed after collection preparation."
    reviewed = c.review_collection(draft["collection_id"], {
        "actor": "Pathway Reviewer", "note": "Drift reviewed", "evidence_reference": "Evidence",
    })["collection"]
    assert reviewed["review_drift"]["drift_detected"] is True
    with pytest.raises(ValueError, match="acknowledged"):
        c.approve_collection(reviewed["collection_id"], {"approved_by": "Pathway Governor", "note": "Approval"})
    approved = c.approve_collection(reviewed["collection_id"], {
        "approved_by": "Pathway Governor", "note": "Approved with retained snapshot", "acknowledge_drift": True,
    })["collection"]
    assert approved["drift_acknowledged"] is True


def test_identity_and_credential_fields_are_rejected(tmp_path):
    _, c = center(tmp_path)
    with pytest.raises(ValueError, match="identities and credentials"):
        c.create_view({
            "actor": "Preparer", "title": "View", "description": "Description", "filter_state": {},
            "visitor_id": "person-123",
        })
    with pytest.raises(ValueError, match="identities, credentials"):
        c.create_collection({
            "actor": "Preparer", "title": "Collection", "purpose": "Purpose", "summary": "Summary",
            "record_ids": ["preservation-institution:alpha"], "access_token": "secret",
        })


def test_public_projection_strips_governance_actor_fields(tmp_path):
    _, c = center(tmp_path)
    view = approved_view(c)
    collection = approved_collection(c, view["view_id"])
    text = repr(c.collection(collection["collection_id"], public=True))
    assert "Pathway Preparer" not in text
    assert "Pathway Reviewer" not in text
    assert "Pathway Governor" not in text
    assert "approved_by" not in text


def test_json_and_markdown_packages_are_checksum_bound(tmp_path):
    _, c = center(tmp_path)
    view = approved_view(c)
    collection = approved_collection(c, view["view_id"])
    media_type, payload = c.package_payload(collection["collection_id"], "json")
    assert media_type == "application/json"
    assert collection["collection_sha256"] in payload
    media_type, markdown = c.package_payload(collection["collection_id"], "markdown")
    assert media_type == "text/markdown"
    assert "## Evidence pathway" in markdown
    assert "No visitor query storage" in markdown


def test_status_and_history_are_aggregate_and_append_only(tmp_path):
    _, c = center(tmp_path)
    view = approved_view(c)
    collection = approved_collection(c, view["view_id"])
    status = c.status()
    assert status["approved_public_view_count"] == 1
    assert status["approved_public_collection_count"] == 1
    assert status["visitor_queries_stored"] is False
    history = c.history(collection["collection_id"])
    assert [row["event_type"] for row in history] == [
        "research_collection_approved", "research_collection_reviewed", "research_collection_created"
    ]


def test_main_public_collection_routes(monkeypatch, tmp_path):
    _, c = center(tmp_path)
    view = approved_view(c)
    collection = approved_collection(c, view["view_id"])
    monkeypatch.setattr(main, "_live_intelligence_registry_collections", lambda settings: c)
    client = TestClient(main.app)
    assert client.get("/public/live-intelligence/registry-collections/policy").status_code == 200
    assert client.get("/public/live-intelligence/registry-collections/views").json()["count"] == 1
    assert client.get("/public/live-intelligence/registry-collections").json()["count"] == 1
    response = client.get(f"/public/live-intelligence/registry-collections/{collection['collection_id']}/pathway")
    assert response.status_code == 200
    assert response.json()["record_count"] == 3


def test_main_public_route_returns_404_for_private_or_missing_collection(monkeypatch, tmp_path):
    _, c = center(tmp_path)
    monkeypatch.setattr(main, "_live_intelligence_registry_collections", lambda settings: c)
    client = TestClient(main.app)
    response = client.get("/public/live-intelligence/registry-collections/registry-collection:missing")
    assert response.status_code == 404
