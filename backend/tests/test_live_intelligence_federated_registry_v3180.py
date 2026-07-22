import json

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app import main
from app.live_intelligence_federated_registry_v3180 import (
    LiveIntelligenceFederatedPreservationRegistry,
    POLICY_SCHEMA_VERSION,
    federated_registry_policy,
)


class ExchangeStub:
    def __init__(self):
        self.row = {
            "exchange_id": "preservation-exchange:alpha",
            "status": "approved",
            "package_sha256": "a" * 64,
            "exchange_sha256": "b" * 64,
            "profile": "bagit_manifest_1_0",
            "public_visible": True,
        }

    def exchange(self, exchange_id, public=False):
        if exchange_id != self.row["exchange_id"]:
            raise KeyError(exchange_id)
        if public and not self.row.get("public_visible"):
            raise KeyError(exchange_id)
        return dict(self.row)


def settings_for(tmp_path, threshold=2):
    return Settings(
        environment="development",
        live_intelligence_preservation_registry_institutions_path=str(tmp_path / "institutions.jsonl"),
        live_intelligence_preservation_registry_attestations_path=str(tmp_path / "attestations.jsonl"),
        live_intelligence_preservation_registry_events_path=str(tmp_path / "events.jsonl"),
        live_intelligence_preservation_registry_consensus_threshold=threshold,
    )


def center(tmp_path, exchange=None, threshold=2):
    return LiveIntelligenceFederatedPreservationRegistry(
        settings_for(tmp_path, threshold), exchange_center=exchange or ExchangeStub()
    )


def approved_institution(registry, suffix="alpha", public_visible=True, methods=None):
    institution = registry.create_institution({
        "actor": f"Registry Preparer {suffix}",
        "institution_id": f"preservation-institution:{suffix}",
        "institution_name": f"Repository {suffix.title()}",
        "jurisdiction": "US-IL",
        "institution_type": "university_repository",
        "repository_reference": f"Public repository record {suffix}",
        "public_policy_reference": f"Preservation policy {suffix}",
        "trust_profile": "policy_reviewed",
        "supported_profiles": ["bagit_manifest_1_0"],
        "verification_methods": methods or ["manual_checksum", "independent_repository_review"],
    })["institution"]
    institution = registry.verify_institution(institution["institution_id"], {
        "actor": f"Registry Verifier {suffix}",
        "reason": "Public preservation policy reviewed.",
        "evidence_reference": f"Evidence register {suffix}",
    })["institution"]
    return registry.approve_institution(institution["institution_id"], {
        "approved_by": f"Registry Governor {suffix}",
        "reason": "Public-safe institutional registry entry approved.",
        "public_visible": public_visible,
    })["institution"]


def attestation(registry, institution_id, *, public_visible=True, result="verified", checksum="a" * 64):
    return registry.record_attestation("preservation-exchange:alpha", {
        "actor": "Institutional Attestation Officer",
        "institution_id": institution_id,
        "method": "manual_checksum",
        "result": result,
        "reported_package_sha256": checksum,
        "evidence_reference": f"Attestation report for {institution_id}",
        "public_visible": public_visible,
    })["attestation"]


def test_policy_declares_registry_without_certification_or_remote_write():
    policy = federated_registry_policy()
    assert policy["schema"] == POLICY_SCHEMA_VERSION
    assert "policy_reviewed" in policy["trust_profiles"]
    assert policy["boundaries"]["multi_party_consensus_unique_institutions"] is True
    assert policy["boundaries"]["certification_claimed"] is False
    assert policy["boundaries"]["network_verification_performed"] is False


def test_institution_requires_public_references_and_builds_checksums(tmp_path):
    registry = center(tmp_path)
    with pytest.raises(ValueError, match="Institution name"):
        registry.create_institution({"actor": "A"})
    institution = registry.create_institution({
        "actor": "A", "institution_name": "Public Archive", "jurisdiction": "US",
        "repository_reference": "Repository directory", "public_policy_reference": "Policy page",
    })["institution"]
    assert institution["status"] == "prepared"
    assert len(institution["package_sha256"]) == 64
    assert len(institution["institution_sha256"]) == 64
    assert institution["certification_claimed"] is False


def test_unsupported_profiles_and_methods_are_rejected(tmp_path):
    registry = center(tmp_path)
    base = {
        "actor": "A", "institution_name": "Public Archive", "jurisdiction": "US",
        "repository_reference": "Repository directory", "public_policy_reference": "Policy page",
    }
    with pytest.raises(ValueError, match="exchange profile"):
        registry.create_institution({**base, "supported_profiles": ["unknown_profile"]})
    with pytest.raises(ValueError, match="verification method"):
        registry.create_institution({**base, "verification_methods": ["automatic_network_probe"]})


def test_institution_verification_and_approval_require_separation(tmp_path):
    registry = center(tmp_path)
    institution = registry.create_institution({
        "actor": "Preparer", "institution_name": "Public Archive", "jurisdiction": "US",
        "repository_reference": "Repository directory", "public_policy_reference": "Policy page",
    })["institution"]
    institution = registry.verify_institution(institution["institution_id"], {
        "actor": "Verifier", "reason": "Reviewed.", "evidence_reference": "Review file",
    })["institution"]
    with pytest.raises(ValueError, match="separation of duties"):
        registry.approve_institution(institution["institution_id"], {
            "approved_by": "Verifier", "reason": "Self approval.",
        })


def test_attestation_requires_approved_exchange_and_institution(tmp_path):
    exchange = ExchangeStub(); exchange.row["status"] = "verified"
    registry = center(tmp_path, exchange)
    institution = approved_institution(registry)
    with pytest.raises(ValueError, match="approved preservation exchanges"):
        attestation(registry, institution["institution_id"])

    exchange.row["status"] = "approved"
    draft = registry.create_institution({
        "actor": "A", "institution_name": "Draft Archive", "jurisdiction": "US",
        "repository_reference": "Repository directory", "public_policy_reference": "Policy page",
    })["institution"]
    with pytest.raises(ValueError, match="approved preservation institutions"):
        attestation(registry, draft["institution_id"])


def test_verified_attestation_is_checksum_bound(tmp_path):
    registry = center(tmp_path)
    institution = approved_institution(registry)
    with pytest.raises(ValueError, match="approved exchange package checksum"):
        attestation(registry, institution["institution_id"], checksum="0" * 64)
    row = attestation(registry, institution["institution_id"])
    assert row["checksum_matches"] is True
    assert row["external_attestation_human_reported"] is True
    assert row["network_verification_performed"] is False


def test_consensus_counts_unique_institutions_only(tmp_path):
    registry = center(tmp_path, threshold=2)
    alpha = approved_institution(registry, "alpha")
    attestation(registry, alpha["institution_id"])
    attestation(registry, alpha["institution_id"])
    consensus = registry.consensus("preservation-exchange:alpha")
    assert consensus["verified_institution_count"] == 1
    assert consensus["consensus_status"] == "partial_consensus"


def test_consensus_reaches_threshold_across_two_approved_institutions(tmp_path):
    registry = center(tmp_path, threshold=2)
    alpha = approved_institution(registry, "alpha")
    beta = approved_institution(registry, "beta")
    attestation(registry, alpha["institution_id"])
    attestation(registry, beta["institution_id"])
    consensus = registry.consensus("preservation-exchange:alpha", public=True)
    assert consensus["verified_institution_count"] == 2
    assert consensus["consensus_status"] == "verified_consensus"
    assert len(consensus["consensus_sha256"]) == 64


def test_private_institution_and_attestation_are_not_public(tmp_path):
    registry = center(tmp_path)
    institution = approved_institution(registry, public_visible=False)
    row = attestation(registry, institution["institution_id"], public_visible=True)
    assert row["public_visible"] is False
    assert registry.institutions(public=True) == []
    assert registry.attestations(public=True) == []


def test_identity_and_credentials_are_rejected(tmp_path):
    registry = center(tmp_path)
    base = {
        "actor": "A", "institution_name": "Public Archive", "jurisdiction": "US",
        "repository_reference": "Repository directory", "public_policy_reference": "Policy page",
    }
    with pytest.raises(ValueError):
        registry.create_institution({**base, "contact_email": "person@example.org"})
    with pytest.raises(ValueError):
        registry.create_institution({**base, "api_token": "secret"})


def test_json_and_markdown_registry_packages(tmp_path):
    registry = center(tmp_path)
    alpha = approved_institution(registry, "alpha")
    beta = approved_institution(registry, "beta")
    attestation(registry, alpha["institution_id"])
    attestation(registry, beta["institution_id"])
    media, body = registry.institution_package_payload(alpha["institution_id"], "json")
    assert media == "application/json"
    assert len(json.loads(body)["package_sha256"]) == 64
    media, body = registry.consensus_package_payload("preservation-exchange:alpha", "markdown")
    assert media == "text/markdown"
    assert "not a certification" in body.lower()


def test_public_routes_are_read_only(monkeypatch, tmp_path):
    registry = center(tmp_path)
    alpha = approved_institution(registry, "alpha")
    beta = approved_institution(registry, "beta")
    attestation(registry, alpha["institution_id"])
    attestation(registry, beta["institution_id"])
    monkeypatch.setattr(main, "_live_intelligence_federated_registry", lambda settings: registry)
    client = TestClient(main.app)
    response = client.get("/public/live-intelligence/preservation-registry/institutions")
    assert response.status_code == 200
    assert len(response.json()["institutions"]) == 2
    consensus = client.get("/public/live-intelligence/preservation-registry/exchanges/preservation-exchange:alpha/consensus")
    assert consensus.status_code == 200
    assert consensus.json()["consensus"]["consensus_status"] == "verified_consensus"
