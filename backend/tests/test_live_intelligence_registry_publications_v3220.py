from copy import deepcopy
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app import main
from app.live_intelligence_registry_publications_v3220 import (
    LiveIntelligenceRegistryPublicationCenter,
    POLICY_SCHEMA_VERSION,
    registry_publication_policy,
)


class FakeCollections:
    def __init__(self):
        self.row = {
            "collection_id": "registry-collection:alpha",
            "status": "approved",
            "public_visible": True,
            "collection_sha256": "a" * 64,
            "evidence_pathway_sha256": "b" * 64,
            "record_snapshots": [
                {"record_id": "preservation-institution:alpha", "record_type": "institution", "title": "Repository Alpha", "summary": "Approved repository.", "record_sha256": "c" * 64, "repository_reference": "https://example.org/repository/alpha", "published_at": "2026-07-20T10:00:00Z"},
                {"record_id": "preservation-exchange:alpha", "record_type": "exchange", "title": "Exchange Alpha", "summary": "Approved exchange.", "record_sha256": "d" * 64, "evidence_reference": "https://example.org/exchange/alpha", "published_at": "2026-07-21T10:00:00Z"},
            ],
            "evidence_pathway": [
                {"sequence": 1, "record_id": "preservation-institution:alpha", "record_type": "institution", "title": "Repository Alpha", "rationale": "Begin with the institution profile.", "record_sha256": "c" * 64},
                {"sequence": 2, "record_id": "preservation-exchange:alpha", "record_type": "exchange", "title": "Exchange Alpha", "rationale": "Follow with the approved exchange.", "record_sha256": "d" * 64},
            ],
        }

    def collection(self, collection_id, public=False):
        if collection_id != self.row["collection_id"]:
            raise KeyError(collection_id)
        if public and not self.row["public_visible"]:
            raise KeyError(collection_id)
        return deepcopy(self.row)


def center(tmp_path: Path):
    settings = Settings(
        live_intelligence_registry_publications_briefs_path=str(tmp_path / "briefs.jsonl"),
        live_intelligence_registry_publications_events_path=str(tmp_path / "events.jsonl"),
        live_intelligence_registry_publications_handoffs_path=str(tmp_path / "handoffs.jsonl"),
    )
    collections = FakeCollections()
    return collections, LiveIntelligenceRegistryPublicationCenter(settings, collections=collections)


def draft(c):
    return c.create_brief({
        "actor": "Brief Preparer",
        "collection_id": "registry-collection:alpha",
        "title": "Preservation evidence brief",
        "deck": "A source-linked public research brief.",
        "abstract": "This brief synthesizes an approved public evidence pathway.",
        "key_findings": ["The repository has an approved public profile.", "The exchange package retains checksums."],
        "methodology": "Human synthesis of the retained collection snapshot and pathway rationale.",
        "limitations": "The package records human-reviewed public evidence and performs no network verification.",
        "public_visible": True,
    })["brief"]


def approved(c):
    row = draft(c)
    row = c.review_brief(row["brief_id"], {"actor": "Brief Reviewer", "note": "Sources and limitations reviewed.", "evidence_reference": "https://example.org/review/brief"})["brief"]
    return c.approve_brief(row["brief_id"], {"approved_by": "Brief Governor", "note": "Approved for public release.", "public_visible": True})["brief"]


def test_policy_declares_manual_publication_and_privacy_boundaries():
    policy = registry_publication_policy()
    assert policy["schema"] == POLICY_SCHEMA_VERSION
    assert policy["boundaries"]["automatic_publication_performed"] is False
    assert policy["boundaries"]["recipient_identities_stored"] is False
    assert "bibtex" in policy["citation_formats"]


def test_brief_requires_approved_public_collection(tmp_path):
    collections, c = center(tmp_path)
    collections.row["public_visible"] = False
    with pytest.raises(ValueError, match="approved public collections"):
        draft(c)


def test_brief_retains_collection_checksum_pathway_and_citations(tmp_path):
    _, c = center(tmp_path)
    row = draft(c)
    assert row["source_collection_sha256"] == "a" * 64
    assert len(row["citations"]) == 2
    assert row["evidence_pathway"][0]["rationale"].startswith("Begin")
    assert len(row["citations_sha256"]) == 64


def test_review_and_approval_require_separate_roles(tmp_path):
    _, c = center(tmp_path)
    row = draft(c)
    with pytest.raises(ValueError, match="separation"):
        c.review_brief(row["brief_id"], {"actor": "Brief Preparer", "note": "Review", "evidence_reference": "Evidence"})
    row = c.review_brief(row["brief_id"], {"actor": "Reviewer", "note": "Review", "evidence_reference": "Evidence"})["brief"]
    with pytest.raises(ValueError, match="separate approver"):
        c.approve_brief(row["brief_id"], {"approved_by": "Reviewer", "note": "Approval"})


def test_source_collection_drift_requires_acknowledgment(tmp_path):
    collections, c = center(tmp_path)
    row = draft(c)
    row = c.review_brief(row["brief_id"], {"actor": "Reviewer", "note": "Review", "evidence_reference": "Evidence"})["brief"]
    collections.row["collection_sha256"] = "f" * 64
    with pytest.raises(ValueError, match="drift"):
        c.approve_brief(row["brief_id"], {"approved_by": "Governor", "note": "Approval"})
    row = c.approve_brief(row["brief_id"], {"approved_by": "Governor", "note": "Approval", "acknowledge_drift": True})["brief"]
    assert row["drift_acknowledged"] is True


def test_public_briefs_require_approval_and_visibility(tmp_path):
    _, c = center(tmp_path)
    draft(c)
    assert c.briefs(public=True) == []
    row = approved(c)
    public = c.brief(row["brief_id"], public=True)
    assert public["brief_id"] == row["brief_id"]
    assert "approved_by" not in repr(public)


def test_citation_bundle_is_checksum_bound_and_public_safe(tmp_path):
    _, c = center(tmp_path)
    row = approved(c)
    bundle = c.citation_bundle(row["brief_id"], public=True)
    assert bundle["citation_count"] == 2
    assert len(bundle["bundle_sha256"]) == 64
    assert bundle["citation_standard_certification_claimed"] is False


def test_json_markdown_bibtex_and_ris_packages(tmp_path):
    _, c = center(tmp_path)
    row = approved(c)
    media, payload = c.package_payload(row["brief_id"], "json")
    assert media == "application/json" and row["brief_sha256"] in payload
    media, payload = c.package_payload(row["brief_id"], "markdown")
    assert media == "text/markdown" and "## Key findings" in payload and "## Citations" in payload
    media, payload = c.package_payload(row["brief_id"], "bibtex")
    assert media == "application/x-bibtex" and "@misc{" in payload
    media, payload = c.package_payload(row["brief_id"], "ris")
    assert "research-info-systems" in media and "TY  - GEN" in payload


def test_handoff_receipts_are_manual_and_do_not_write(tmp_path):
    _, c = center(tmp_path)
    row = approved(c)
    receipt = c.record_handoff(row["brief_id"], {"actor": "Release Operator", "target": "knowledge_library", "format": "markdown", "note": "Package handed off manually."})["handoff"]
    assert receipt["manual_delivery_only"] is True
    assert receipt["remote_write_performed"] is False
    assert len(receipt["package_sha256"]) == 64


def test_identity_and_credentials_are_rejected(tmp_path):
    _, c = center(tmp_path)
    with pytest.raises(ValueError, match="identities and credentials"):
        c.create_brief({"actor": "Preparer", "collection_id": "registry-collection:alpha", "title": "Title", "deck": "Deck", "abstract": "Abstract", "key_findings": ["Finding"], "methodology": "Method", "limitations": "Limits", "visitor_id": "person"})


def test_status_and_history_are_append_only(tmp_path):
    _, c = center(tmp_path)
    row = approved(c)
    status = c.status()
    assert status["approved_public_brief_count"] == 1
    assert status["automatic_publication_performed"] is False
    assert [item["event_type"] for item in c.history(row["brief_id"])] == ["research_brief_approved", "research_brief_reviewed", "research_brief_created"]


def test_main_public_routes(monkeypatch, tmp_path):
    _, c = center(tmp_path)
    row = approved(c)
    monkeypatch.setattr(main, "_live_intelligence_registry_publications", lambda settings: c)
    client = TestClient(main.app)
    assert client.get("/public/live-intelligence/registry-publications/policy").status_code == 200
    assert client.get("/public/live-intelligence/registry-publications/status").json()["approved_public_brief_count"] == 1
    assert client.get("/public/live-intelligence/registry-publications/briefs").json()["count"] == 1
    assert client.get(f"/public/live-intelligence/registry-publications/briefs/{row['brief_id']}/citations").json()["citation_count"] == 2


def test_main_public_route_returns_404_for_missing_brief(monkeypatch, tmp_path):
    _, c = center(tmp_path)
    monkeypatch.setattr(main, "_live_intelligence_registry_publications", lambda settings: c)
    response = TestClient(main.app).get("/public/live-intelligence/registry-publications/briefs/registry-brief:missing")
    assert response.status_code == 404
