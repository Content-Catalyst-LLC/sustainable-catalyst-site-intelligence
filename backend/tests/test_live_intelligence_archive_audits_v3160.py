import json
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app import main
from app.live_intelligence_release_operations_v3130 import _digest
from app.live_intelligence_archive_audits_v3160 import (
    LiveIntelligenceArchiveAuditCenter,
    POLICY_SCHEMA_VERSION,
    archive_audit_policy,
)


class ArchiveStub:
    def __init__(self):
        self.rows = []
        self.source_matches = {}
        self._add("public-archive:alpha", "")
        self._add("public-archive:beta", "public-archive:alpha")

    def _add(self, archive_id, previous_id):
        source = {"source_id": archive_id, "title": archive_id, "public": True}
        previous = next((row for row in self.rows if row["archive_id"] == previous_id), None)
        record = {
            "archive_id": archive_id,
            "source_type": "publication_release",
            "source_id": f"publication-release:{archive_id.rsplit(':', 1)[-1]}",
            "source_snapshot": source,
            "source_sha256": _digest(source),
            "previous_archive_id": previous_id,
            "previous_record_sha256": previous["record_sha256"] if previous else "",
            "retention_class": "permanent",
            "review_due_at": "2030-01-01T00:00:00+00:00",
            "status": "approved",
            "public_visible": True,
            "created_at": f"2026-01-0{len(self.rows)+1}T00:00:00+00:00",
            "preservation_manifest": {
                "archive_id": archive_id,
                "files": [{"path": "source-snapshot.json", "sha256": _digest(source)}],
            },
            "archive_record_deleted": False,
            "archive_record_mutated": False,
            "destination_write_performed": False,
        }
        record["preservation_manifest_sha256"] = _digest(record["preservation_manifest"])
        record["record_sha256"] = _digest({k: v for k, v in record.items() if k != "record_sha256"})
        self.rows.append(record)
        self.source_matches[archive_id] = True

    def records(self, public=False, limit=2000):
        rows = list(self.rows)
        if public:
            rows = [row for row in rows if row["status"] == "approved" and row["public_visible"]]
        return rows[:limit]

    def verify_public_record(self, archive_id):
        return {
            "ok": self.source_matches.get(archive_id, True),
            "source_checksum_matches": self.source_matches.get(archive_id, True),
            "manifest_checksum_matches": True,
        }


def settings_for(tmp_path):
    return Settings(
        environment="development",
        live_intelligence_archive_audits_path=str(tmp_path / "audits.jsonl"),
        live_intelligence_archive_audit_events_path=str(tmp_path / "audit-events.jsonl"),
        live_intelligence_archive_custody_path=str(tmp_path / "custody.jsonl"),
    )


def center(tmp_path, archive=None):
    return LiveIntelligenceArchiveAuditCenter(settings_for(tmp_path), archive_center=archive or ArchiveStub())


def approved_audit(audit_center):
    audit = audit_center.create_audit({
        "actor": "Preservation Officer A",
        "audit_type": "full_chain",
        "cadence": "annual",
    })["audit"]
    audit = audit_center.run_audit(audit["audit_id"], {
        "actor": "Integrity Reviewer B",
        "reason": "Run annual checksum and chain verification.",
    })["audit"]
    return audit_center.approve_audit(audit["audit_id"], {
        "approved_by": "Archive Governor C",
        "reason": "Preservation audit reviewed and approved.",
        "public_visible": True,
    })["audit"]


def test_policy_declares_no_scheduler_no_write_boundaries():
    policy = archive_audit_policy()
    assert policy["schema"] == POLICY_SCHEMA_VERSION
    assert policy["boundaries"]["append_only_audit_ledger"] is True
    assert policy["boundaries"]["automatic_scheduler_claimed"] is False
    assert policy["boundaries"]["remote_deposit_performed"] is False
    assert policy["boundaries"]["archive_record_mutated"] is False


def test_clean_audit_verifies_record_manifest_source_and_chain(tmp_path):
    audit_center = center(tmp_path)
    audit = audit_center.create_audit({"actor": "Preservation Officer A", "audit_type": "full_chain"})["audit"]
    audit = audit_center.run_audit(audit["audit_id"], {"actor": "Integrity Reviewer B", "reason": "Verify."})["audit"]
    assert audit["status"] == "verified"
    assert audit["summary"]["records_examined"] == 2
    assert audit["summary"]["records_checksum_verified"] == 2
    assert audit["summary"]["finding_count"] == 0


def test_current_source_drift_is_warning_without_archive_mutation(tmp_path):
    archive = ArchiveStub()
    archive.source_matches["public-archive:beta"] = False
    audit_center = center(tmp_path, archive)
    audit = audit_center.create_audit({"actor": "Preservation Officer A"})["audit"]
    audit = audit_center.run_audit(audit["audit_id"], {"actor": "Integrity Reviewer B", "reason": "Verify."})["audit"]
    assert audit["status"] == "review_required"
    assert audit["summary"]["critical_count"] == 0
    assert audit["summary"]["warning_count"] == 1
    assert audit["archive_record_mutated"] is False


def test_checksum_tamper_creates_critical_finding_and_requires_acknowledgment(tmp_path):
    archive = ArchiveStub()
    archive.rows[1]["source_snapshot"]["title"] = "tampered"
    audit_center = center(tmp_path, archive)
    audit = audit_center.create_audit({"actor": "Preservation Officer A"})["audit"]
    audit = audit_center.run_audit(audit["audit_id"], {"actor": "Integrity Reviewer B", "reason": "Verify."})["audit"]
    assert audit["summary"]["critical_count"] >= 1
    with pytest.raises(ValueError, match="Critical findings"):
        audit_center.approve_audit(audit["audit_id"], {
            "approved_by": "Archive Governor C", "reason": "Review complete.",
        })
    approved = audit_center.approve_audit(audit["audit_id"], {
        "approved_by": "Archive Governor C", "reason": "Critical finding retained for remediation.",
        "critical_findings_acknowledged": True,
    })["audit"]
    assert approved["status"] == "approved"


def test_audit_approval_requires_separation_of_duties(tmp_path):
    audit_center = center(tmp_path)
    audit = audit_center.create_audit({"actor": "Preservation Officer A"})["audit"]
    audit = audit_center.run_audit(audit["audit_id"], {"actor": "Integrity Reviewer B", "reason": "Verify."})["audit"]
    with pytest.raises(ValueError, match="separation of duties"):
        audit_center.approve_audit(audit["audit_id"], {
            "approved_by": "Integrity Reviewer B", "reason": "Self approval.",
        })


def test_custody_transfer_is_checksum_bound_and_manual(tmp_path):
    audit_center = center(tmp_path)
    audit = approved_audit(audit_center)
    transfer = audit_center.prepare_custody_transfer({
        "audit_id": audit["audit_id"],
        "actor": "Custody Preparer D",
        "adapter": "institutional_archive",
        "institution_reference": "Partner archive accession queue",
    })["transfer"]
    assert transfer["record_count"] == 2
    assert transfer["manual_transfer_required"] is True
    transfer = audit_center.verify_custody_transfer(transfer["transfer_id"], {
        "actor": "Custody Verifier E", "reason": "Package checksums verified.",
    })["transfer"]
    transfer = audit_center.approve_custody_transfer(transfer["transfer_id"], {
        "approved_by": "Custody Governor F", "reason": "Manual institutional transfer approved.",
        "public_visible": True,
    })["transfer"]
    assert transfer["status"] == "approved"
    assert transfer["remote_deposit_performed"] is False


def test_manual_receipt_records_reference_without_claiming_remote_action(tmp_path):
    audit_center = center(tmp_path)
    audit = approved_audit(audit_center)
    transfer = audit_center.prepare_custody_transfer({"audit_id": audit["audit_id"], "actor": "Custody Preparer D"})["transfer"]
    transfer = audit_center.verify_custody_transfer(transfer["transfer_id"], {"actor": "Custody Verifier E", "reason": "Verified."})["transfer"]
    transfer = audit_center.approve_custody_transfer(transfer["transfer_id"], {"approved_by": "Custody Governor F", "reason": "Approved."})["transfer"]
    receipt = audit_center.record_custody_receipt(transfer["transfer_id"], {
        "actor": "Records Officer G", "custody_reference": "Accession batch 2026-Q3",
    })["transfer"]
    assert receipt["status"] == "manual_receipt_recorded"
    assert receipt["destination_write_performed"] is False


def test_json_and_markdown_packages(tmp_path):
    audit_center = center(tmp_path)
    audit = approved_audit(audit_center)
    media, body = audit_center.report_payload(audit["audit_id"], "json", public=True)
    payload = json.loads(body)
    assert media == "application/json"
    assert len(payload["package_sha256"]) == 64
    media, body = audit_center.report_payload(audit["audit_id"], "markdown", public=True)
    assert media == "text/markdown"
    assert "no archive mutation" in body.lower()


def test_identity_and_credentials_are_rejected(tmp_path):
    audit_center = center(tmp_path)
    with pytest.raises(ValueError):
        audit_center.create_audit({"actor": "Preservation Officer A", "recipient_email": "person@example.org"})
    with pytest.raises(ValueError):
        audit_center.create_audit({"actor": "Preservation Officer A", "api_token": "secret"})


def test_public_routes_are_read_only(monkeypatch, tmp_path):
    audit_center = center(tmp_path)
    audit = approved_audit(audit_center)
    monkeypatch.setattr(main, "_live_intelligence_archive_audits", lambda settings: audit_center)
    client = TestClient(main.app)
    response = client.get("/public/live-intelligence/archive-audits")
    assert response.status_code == 200
    assert response.json()["audits"][0]["audit_id"] == audit["audit_id"]
    detail = client.get(f"/public/live-intelligence/archive-audits/{audit['audit_id']}")
    assert detail.status_code == 200
    assert detail.json()["audit"]["status"] == "approved"
