import json

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app import main
from app.live_intelligence_release_operations_v3130 import _digest
from app.live_intelligence_preservation_exchange_v3170 import (
    LiveIntelligencePreservationExchangeCenter,
    POLICY_SCHEMA_VERSION,
    preservation_exchange_policy,
)


class CustodyStub:
    def __init__(self):
        self.row = {
            "transfer_id": "custody-transfer:alpha",
            "status": "approved",
            "transfer_sha256": "a" * 64,
            "package_sha256": "b" * 64,
            "institution_reference": "Partner archive accession queue",
            "record_manifest": [
                {"archive_id": "public-archive:alpha", "record_sha256": "c" * 64, "preservation_manifest_sha256": "d" * 64},
                {"archive_id": "public-archive:beta", "record_sha256": "e" * 64, "preservation_manifest_sha256": "f" * 64},
            ],
        }

    def custody_transfer(self, transfer_id, public=False):
        if transfer_id != self.row["transfer_id"]:
            raise KeyError(transfer_id)
        return dict(self.row)


def settings_for(tmp_path):
    return Settings(
        environment="development",
        live_intelligence_preservation_exchange_path=str(tmp_path / "exchanges.jsonl"),
        live_intelligence_preservation_exchange_verifications_path=str(tmp_path / "verifications.jsonl"),
        live_intelligence_preservation_exchange_events_path=str(tmp_path / "events.jsonl"),
    )


def center(tmp_path, custody=None):
    return LiveIntelligencePreservationExchangeCenter(settings_for(tmp_path), custody_center=custody or CustodyStub())


def approved_exchange(exchange_center, public_visible=True):
    exchange = exchange_center.create_exchange({
        "actor": "Exchange Preparer A",
        "custody_transfer_id": "custody-transfer:alpha",
        "profile": "bagit_manifest_1_0",
        "institution_reference": "Partner archive queue",
    })["exchange"]
    exchange = exchange_center.verify_exchange(exchange["exchange_id"], {
        "actor": "Exchange Verifier B", "reason": "Manifest and custody checksums verified.",
    })["exchange"]
    return exchange_center.approve_exchange(exchange["exchange_id"], {
        "approved_by": "Exchange Governor C", "reason": "Manual institutional exchange approved.",
        "public_visible": public_visible,
    })["exchange"]


def test_policy_declares_interoperability_without_remote_write():
    policy = preservation_exchange_policy()
    assert policy["schema"] == POLICY_SCHEMA_VERSION
    assert "bagit_manifest_1_0" in policy["profiles"]
    assert policy["boundaries"]["external_verification_human_reported"] is True
    assert policy["boundaries"]["network_verification_performed"] is False
    assert policy["boundaries"]["remote_deposit_performed"] is False


def test_exchange_requires_approved_custody(tmp_path):
    custody = CustodyStub(); custody.row["status"] = "verified"
    with pytest.raises(ValueError, match="approved custody"):
        center(tmp_path, custody).create_exchange({"actor": "A", "custody_transfer_id": "custody-transfer:alpha"})


def test_exchange_builds_profile_and_checksum_manifest(tmp_path):
    exchange = center(tmp_path).create_exchange({
        "actor": "Exchange Preparer A", "custody_transfer_id": "custody-transfer:alpha",
        "profile": "oais_sip_profile",
    })["exchange"]
    assert exchange["profile"] == "oais_sip_profile"
    assert exchange["record_count"] == 2
    assert len(exchange["exchange_manifest_sha256"]) == 64
    assert len(exchange["package_sha256"]) == 64
    assert exchange["destination_write_performed"] is False


def test_verification_detects_custody_drift(tmp_path):
    custody = CustodyStub(); exchange_center = center(tmp_path, custody)
    exchange = exchange_center.create_exchange({"actor": "A", "custody_transfer_id": "custody-transfer:alpha"})["exchange"]
    custody.row["transfer_sha256"] = "9" * 64
    with pytest.raises(ValueError, match="changed after"):
        exchange_center.verify_exchange(exchange["exchange_id"], {"actor": "B", "reason": "Verify."})


def test_approval_requires_separation_of_duties(tmp_path):
    exchange_center = center(tmp_path)
    exchange = exchange_center.create_exchange({"actor": "A", "custody_transfer_id": "custody-transfer:alpha"})["exchange"]
    exchange = exchange_center.verify_exchange(exchange["exchange_id"], {"actor": "B", "reason": "Verify."})["exchange"]
    with pytest.raises(ValueError, match="separation of duties"):
        exchange_center.approve_exchange(exchange["exchange_id"], {"approved_by": "B", "reason": "Self approve."})


def test_external_verification_is_human_reported_and_checksum_bound(tmp_path):
    exchange_center = center(tmp_path); exchange = approved_exchange(exchange_center)
    verification = exchange_center.record_external_verification(exchange["exchange_id"], {
        "actor": "Institutional Reviewer D",
        "method": "independent_repository_review",
        "result": "verified",
        "reported_package_sha256": exchange["package_sha256"],
        "institution_reference": "Partner Repository",
        "verification_reference": "Verification report 2026-07",
        "public_visible": True,
    })["verification"]
    assert verification["checksum_matches"] is True
    assert verification["external_verification_human_reported"] is True
    assert verification["network_verification_performed"] is False


def test_verified_receipt_rejects_wrong_checksum(tmp_path):
    exchange_center = center(tmp_path); exchange = approved_exchange(exchange_center)
    with pytest.raises(ValueError, match="approved exchange package checksum"):
        exchange_center.record_external_verification(exchange["exchange_id"], {
            "actor": "D", "result": "verified", "reported_package_sha256": "0" * 64,
            "institution_reference": "Partner", "verification_reference": "Report",
        })


def test_private_verification_is_not_public(tmp_path):
    exchange_center = center(tmp_path); exchange = approved_exchange(exchange_center)
    exchange_center.record_external_verification(exchange["exchange_id"], {
        "actor": "D", "result": "verified", "reported_package_sha256": exchange["package_sha256"],
        "institution_reference": "Partner", "verification_reference": "Private report", "public_visible": False,
    })
    assert exchange_center.verifications(public=True) == []


def test_json_and_markdown_packages(tmp_path):
    exchange_center = center(tmp_path); exchange = approved_exchange(exchange_center)
    media, body = exchange_center.package_payload(exchange["exchange_id"], "json", public=True)
    assert media == "application/json"
    assert len(json.loads(body)["package_sha256"]) == 64
    media, body = exchange_center.package_payload(exchange["exchange_id"], "markdown", public=True)
    assert media == "text/markdown"
    assert "no network verification" in body.lower()


def test_identity_and_credentials_are_rejected(tmp_path):
    exchange_center = center(tmp_path)
    with pytest.raises(ValueError):
        exchange_center.create_exchange({"actor": "A", "custody_transfer_id": "custody-transfer:alpha", "recipient_email": "person@example.org"})
    with pytest.raises(ValueError):
        exchange_center.create_exchange({"actor": "A", "custody_transfer_id": "custody-transfer:alpha", "api_token": "secret"})


def test_public_routes_are_read_only(monkeypatch, tmp_path):
    exchange_center = center(tmp_path); exchange = approved_exchange(exchange_center)
    monkeypatch.setattr(main, "_live_intelligence_preservation_exchange", lambda settings: exchange_center)
    client = TestClient(main.app)
    response = client.get("/public/live-intelligence/preservation-exchange/exchanges")
    assert response.status_code == 200
    assert response.json()["exchanges"][0]["exchange_id"] == exchange["exchange_id"]
    detail = client.get(f"/public/live-intelligence/preservation-exchange/exchanges/{exchange['exchange_id']}")
    assert detail.status_code == 200
