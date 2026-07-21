import json

import pytest
from fastapi.testclient import TestClient

from app import main
from app.config import Settings
from app.live_intelligence_public_archive_v3150 import (
    LiveIntelligencePublicArchive,
    POLICY_SCHEMA_VERSION,
    public_archive_policy,
)


class Publications:
    def __init__(self):
        self.rows = {
            "publication-release:alpha": {
                "release_id": "publication-release:alpha",
                "status": "approved",
                "visibility": "public",
                "title": "Climate evidence release",
                "target_slug": "climate-evidence-release",
                "release_sha256": "a" * 64,
                "payload_sha256": "b" * 64,
                "sources": [{"label": "NOAA", "url": "https://example.org/noaa"}],
                "approved_by": "Internal Publisher",
            }
        }

    def release(self, release_id):
        if release_id not in self.rows:
            raise KeyError(release_id)
        return dict(self.rows[release_id])


class Changes:
    def __init__(self):
        self.rows = {
            "change-notice:alpha": {
                "notice_id": "change-notice:alpha",
                "status": "approved",
                "public_visible": True,
                "notice_type": "correction",
                "title": "Public correction",
                "affected_release_id": "publication-release:alpha",
                "affected_release_sha256": "a" * 64,
                "original_release_retained": True,
                "approved_by": "Internal Reviewer",
            }
        }

    def notice(self, notice_id):
        if notice_id not in self.rows:
            raise KeyError(notice_id)
        return dict(self.rows[notice_id])


class Briefings:
    def __init__(self):
        self.rows = {
            "briefing:alpha": {
                "briefing_id": "briefing:alpha",
                "status": "approved",
                "visibility": "public",
                "published": True,
                "title": "Climate briefing",
                "observations": [{"claim": "Observed public signal", "source_url": "https://example.org/source"}],
                "reviewed_by": "Internal Editor",
            }
        }

    def _briefing(self, briefing_id, public=False):
        row = self.rows.get(briefing_id)
        if not row or (public and not (row.get("published") and row.get("visibility") == "public")):
            raise KeyError(briefing_id)
        return dict(row)


def settings_for(tmp_path):
    return Settings(
        environment="development",
        live_intelligence_public_archive_records_path=str(tmp_path / "archive-records.jsonl"),
        live_intelligence_public_archive_events_path=str(tmp_path / "archive-events.jsonl"),
        live_intelligence_public_archive_handoffs_path=str(tmp_path / "archive-handoffs.jsonl"),
    )


def center(tmp_path):
    return LiveIntelligencePublicArchive(
        settings_for(tmp_path),
        publication_center=Publications(),
        change_history_center=Changes(),
        briefing_center=Briefings(),
    )


def approved_record(archive, source_type="publication_release", source_id="publication-release:alpha"):
    record = archive.create_record({
        "source_type": source_type,
        "source_id": source_id,
        "actor": "Archive Preparer A",
        "retention_class": "permanent",
    })["record"]
    record = archive.verify_record(record["archive_id"], {
        "actor": "Archive Verifier B",
        "reason": "Source and checksum verified.",
    })["record"]
    return archive.approve_record(record["archive_id"], {
        "approved_by": "Archive Approver C",
        "reason": "Long-term public-interest retention approved.",
    })["record"]


def test_policy_declares_append_only_no_write_boundaries():
    policy = public_archive_policy()
    assert policy["schema"] == POLICY_SCHEMA_VERSION
    assert policy["boundaries"]["append_only_ledger"] is True
    assert policy["boundaries"]["archive_record_deleted"] is False
    assert policy["boundaries"]["destination_write_performed"] is False
    assert policy["boundaries"]["remote_deposit_performed"] is False


def test_archive_requires_approved_public_source(tmp_path):
    publications = Publications()
    publications.rows["publication-release:alpha"]["visibility"] = "internal"
    archive = LiveIntelligencePublicArchive(
        settings_for(tmp_path), publication_center=publications,
        change_history_center=Changes(), briefing_center=Briefings(),
    )
    with pytest.raises(ValueError, match="approved and public"):
        archive.create_record({"source_type": "publication_release", "source_id": "publication-release:alpha", "actor": "Archive Preparer A"})


def test_record_is_checksum_bound_and_strips_operational_identity(tmp_path):
    archive = center(tmp_path)
    record = archive.create_record({
        "source_type": "publication_release",
        "source_id": "publication-release:alpha",
        "actor": "Archive Preparer A",
    })["record"]
    assert len(record["source_sha256"]) == 64
    assert len(record["record_sha256"]) == 64
    assert "approved_by" not in record["source_snapshot"]
    assert record["source_record_mutated"] is False


def test_source_drift_blocks_verification(tmp_path):
    publications = Publications()
    archive = LiveIntelligencePublicArchive(
        settings_for(tmp_path), publication_center=publications,
        change_history_center=Changes(), briefing_center=Briefings(),
    )
    record = archive.create_record({"source_type": "publication_release", "source_id": "publication-release:alpha", "actor": "Archive Preparer A"})["record"]
    publications.rows["publication-release:alpha"]["title"] = "Changed after preparation"
    with pytest.raises(ValueError, match="changed after archive preparation"):
        archive.verify_record(record["archive_id"], {"actor": "Archive Verifier B", "reason": "Verify."})


def test_approval_requires_verification_and_separation_of_duties(tmp_path):
    archive = center(tmp_path)
    record = archive.create_record({"source_type": "publication_release", "source_id": "publication-release:alpha", "actor": "Archive Preparer A"})["record"]
    with pytest.raises(ValueError, match="verified before approval"):
        archive.approve_record(record["archive_id"], {"approved_by": "Archive Approver C", "reason": "Approve."})
    record = archive.verify_record(record["archive_id"], {"actor": "Archive Verifier B", "reason": "Verified."})["record"]
    with pytest.raises(ValueError, match="separation of duties"):
        archive.approve_record(record["archive_id"], {"approved_by": "Archive Verifier B", "reason": "Self approve."})


def test_approved_record_has_preservation_manifest_and_public_verification(tmp_path):
    archive = center(tmp_path)
    record = approved_record(archive)
    assert record["status"] == "approved"
    assert len(record["preservation_manifest"]["files"]) == 4
    verification = archive.verify_public_record(record["archive_id"])
    assert verification["ok"] is True
    assert verification["source_checksum_matches"] is True
    assert verification["manifest_checksum_matches"] is True


def test_records_form_append_only_chain(tmp_path):
    archive = center(tmp_path)
    first = approved_record(archive)
    second = approved_record(archive, "public_change_notice", "change-notice:alpha")
    assert second["previous_archive_id"] == first["archive_id"]
    assert second["previous_record_sha256"] == first["record_sha256"]
    assert second["archive_record_deleted"] is False


def test_json_markdown_packages_and_manual_handoff(tmp_path):
    archive = center(tmp_path)
    record = approved_record(archive, "public_briefing", "briefing:alpha")
    media_type, body = archive.package_payload(record["archive_id"], "json", public=True)
    payload = json.loads(body)
    assert media_type == "application/json"
    assert payload["automatic_deposit"] is False
    assert len(payload["package_sha256"]) == 64
    media_type, body = archive.package_payload(record["archive_id"], "markdown", public=True)
    assert media_type == "text/markdown"
    assert "Original records remain retained" in body
    handoff = archive.create_handoff(record["archive_id"], {"actor": "Custody Officer D", "adapter": "institutional_archive"})["handoff"]
    assert handoff["status"] == "manual_custody_required"
    assert handoff["destination_write_performed"] is False


def test_identity_and_credentials_are_rejected(tmp_path):
    archive = center(tmp_path)
    with pytest.raises(ValueError):
        archive.create_record({
            "source_type": "publication_release", "source_id": "publication-release:alpha",
            "actor": "Archive Preparer A", "recipient_email": "person@example.org",
        })


def test_public_routes_expose_read_only_archive(monkeypatch, tmp_path):
    archive = center(tmp_path)
    record = approved_record(archive)
    monkeypatch.setattr(main, "_live_intelligence_public_archive", lambda settings: archive)
    client = TestClient(main.app)
    response = client.get("/public/live-intelligence/archive")
    assert response.status_code == 200
    assert response.json()["records"][0]["archive_id"] == record["archive_id"]
    detail = client.get(f"/public/live-intelligence/archive/{record['archive_id']}")
    assert detail.status_code == 200
    assert detail.json()["verification"]["ok"] is True
