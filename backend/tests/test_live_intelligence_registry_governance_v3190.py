import json

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app import main
from app.live_intelligence_federated_registry_v3180 import LiveIntelligenceFederatedPreservationRegistry
from app.live_intelligence_registry_governance_v3190 import (
    LiveIntelligenceRegistryGovernanceCenter,
    POLICY_SCHEMA_VERSION,
    registry_governance_policy,
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


def settings_for(tmp_path):
    return Settings(
        environment="development",
        live_intelligence_preservation_registry_institutions_path=str(tmp_path / "institutions.jsonl"),
        live_intelligence_preservation_registry_attestations_path=str(tmp_path / "attestations.jsonl"),
        live_intelligence_preservation_registry_events_path=str(tmp_path / "registry-events.jsonl"),
        live_intelligence_registry_governance_challenges_path=str(tmp_path / "challenges.jsonl"),
        live_intelligence_registry_governance_appeals_path=str(tmp_path / "appeals.jsonl"),
        live_intelligence_registry_governance_events_path=str(tmp_path / "governance-events.jsonl"),
    )


def centers(tmp_path):
    settings = settings_for(tmp_path)
    registry = LiveIntelligenceFederatedPreservationRegistry(settings, exchange_center=ExchangeStub())
    governance = LiveIntelligenceRegistryGovernanceCenter(settings, registry_center=registry)
    return registry, governance


def approved_institution(registry, *, public_visible=True):
    institution = registry.create_institution({
        "actor": "Registry Preparer",
        "institution_id": "preservation-institution:alpha",
        "institution_name": "Repository Alpha",
        "jurisdiction": "US-IL",
        "institution_type": "university_repository",
        "repository_reference": "Public repository record",
        "public_policy_reference": "Preservation policy",
        "trust_profile": "policy_reviewed",
        "supported_profiles": ["bagit_manifest_1_0"],
        "verification_methods": ["manual_checksum"],
    })["institution"]
    institution = registry.verify_institution(institution["institution_id"], {
        "actor": "Registry Verifier",
        "reason": "Policy reviewed.",
        "evidence_reference": "Evidence register",
    })["institution"]
    return registry.approve_institution(institution["institution_id"], {
        "approved_by": "Registry Governor",
        "reason": "Entry approved.",
        "public_visible": public_visible,
    })["institution"]


def attest(registry):
    return registry.record_attestation("preservation-exchange:alpha", {
        "actor": "Attestation Officer",
        "institution_id": "preservation-institution:alpha",
        "method": "manual_checksum",
        "result": "verified",
        "reported_package_sha256": "a" * 64,
        "evidence_reference": "Attestation report",
        "public_visible": True,
    })["attestation"]


def submitted_challenge(governance, *, public_visible=True, challenge_type="governance_concern"):
    return governance.create_challenge({
        "actor": "Challenge Preparer",
        "institution_id": "preservation-institution:alpha",
        "challenge_type": challenge_type,
        "summary": "The registry entry requires review.",
        "rationale": "New public evidence may affect the current trust declaration.",
        "evidence_reference": "Public challenge evidence",
        "public_visible": public_visible,
    })["challenge"]


def reviewed_challenge(governance, challenge_id, action="suspend", profile=None):
    request = {
        "actor": "Challenge Reviewer",
        "reason": "Evidence reviewed against the registry policy.",
        "evidence_reference": "Challenge review record",
        "recommended_action": action,
    }
    if profile:
        request["recommended_trust_profile"] = profile
    return governance.review_challenge(challenge_id, request)["challenge"]


def resolved_challenge(governance, challenge_id, action="suspend", profile=None, public_visible=True):
    request = {
        "approved_by": "Challenge Governor",
        "reason": "Governance decision approved.",
        "action": action,
        "public_visible": public_visible,
    }
    if profile:
        request["trust_profile"] = profile
    return governance.approve_challenge(challenge_id, request)


def test_policy_declares_append_only_human_governance():
    policy = registry_governance_policy()
    assert policy["schema"] == POLICY_SCHEMA_VERSION
    assert "revoke" in policy["resolution_actions"]
    assert policy["boundaries"]["original_registry_records_retained"] is True
    assert policy["boundaries"]["automatic_revocation_performed"] is False
    assert policy["boundaries"]["certification_claimed"] is False


def test_challenge_requires_registry_institution_and_public_evidence(tmp_path):
    _, governance = centers(tmp_path)
    with pytest.raises(KeyError):
        governance.create_challenge({
            "actor": "A", "institution_id": "preservation-institution:missing",
            "challenge_type": "evidence_gap", "summary": "Missing", "rationale": "Missing", "evidence_reference": "Evidence",
        })

    registry, governance = centers(tmp_path / "second")
    approved_institution(registry)
    with pytest.raises(ValueError, match="evidence reference"):
        governance.create_challenge({
            "actor": "A", "institution_id": "preservation-institution:alpha",
            "challenge_type": "evidence_gap", "summary": "Missing", "rationale": "Missing", "evidence_reference": "",
        })


def test_challenge_review_and_approval_require_separation(tmp_path):
    registry, governance = centers(tmp_path)
    approved_institution(registry)
    challenge = submitted_challenge(governance)
    with pytest.raises(ValueError, match="separation of duties"):
        governance.review_challenge(challenge["challenge_id"], {
            "actor": "Challenge Preparer", "reason": "Review", "evidence_reference": "Evidence", "recommended_action": "suspend",
        })
    reviewed = reviewed_challenge(governance, challenge["challenge_id"])
    with pytest.raises(ValueError, match="separation of duties"):
        governance.approve_challenge(reviewed["challenge_id"], {
            "approved_by": "Challenge Reviewer", "reason": "Approve", "action": "suspend",
        })


def test_suspension_preserves_attestation_but_removes_current_consensus(tmp_path):
    registry, governance = centers(tmp_path)
    approved_institution(registry)
    attestation = attest(registry)
    assert registry.consensus("preservation-exchange:alpha", public=True)["verified_institution_count"] == 1
    challenge = submitted_challenge(governance)
    reviewed_challenge(governance, challenge["challenge_id"], "suspend")
    result = resolved_challenge(governance, challenge["challenge_id"], "suspend")
    assert result["institution"]["status"] == "suspended"
    assert registry.attestation(attestation["attestation_id"])["attestation_sha256"] == attestation["attestation_sha256"]
    assert registry.attestations(public=True) == []
    assert registry.consensus("preservation-exchange:alpha", public=True)["consensus_status"] == "unverified"


def test_trust_profile_change_appends_new_institution_state(tmp_path):
    registry, governance = centers(tmp_path)
    original = approved_institution(registry)
    challenge = submitted_challenge(governance, challenge_type="status_accuracy")
    reviewed_challenge(governance, challenge["challenge_id"], "update_trust_profile", "declared")
    result = resolved_challenge(governance, challenge["challenge_id"], "update_trust_profile", "declared")
    updated = result["institution"]
    assert updated["status"] == "approved"
    assert updated["trust_profile"] == "declared"
    assert updated["prior_institution_sha256"] == original["institution_sha256"]
    assert updated["institution_sha256"] != original["institution_sha256"]


def test_retraction_style_deletion_is_not_supported(tmp_path):
    registry, governance = centers(tmp_path)
    approved_institution(registry)
    assert "delete" not in registry_governance_policy()["resolution_actions"]
    challenge = submitted_challenge(governance)
    reviewed_challenge(governance, challenge["challenge_id"], "revoke")
    result = resolved_challenge(governance, challenge["challenge_id"], "revoke")
    assert result["institution"]["status"] == "revoked"
    assert result["challenge"]["prior_registry_records_retained"] is True
    assert result["challenge"]["prior_attestations_retained"] is True


def test_resolved_public_challenge_remains_visible_after_revocation(tmp_path):
    registry, governance = centers(tmp_path)
    approved_institution(registry)
    challenge = submitted_challenge(governance, public_visible=True)
    reviewed_challenge(governance, challenge["challenge_id"], "revoke")
    resolved_challenge(governance, challenge["challenge_id"], "revoke", public_visible=True)
    public = governance.challenges(public=True)
    assert len(public) == 1
    assert public[0]["resolution_action"] == "revoke"
    summary = governance.institution_governance("preservation-institution:alpha", public=True)
    assert summary["current_status"] == "revoked"
    assert summary["challenge_count"] == 1


def test_appeal_requires_resolved_governance_action(tmp_path):
    registry, governance = centers(tmp_path)
    approved_institution(registry)
    challenge = submitted_challenge(governance)
    with pytest.raises(ValueError, match="resolved"):
        governance.create_appeal(challenge["challenge_id"], {
            "actor": "Appeal Preparer", "rationale": "Appeal", "evidence_reference": "Evidence",
        })


def test_appeal_reinstatement_requires_separate_review_and_approval(tmp_path):
    registry, governance = centers(tmp_path)
    approved_institution(registry)
    attest(registry)
    challenge = submitted_challenge(governance)
    reviewed_challenge(governance, challenge["challenge_id"], "suspend")
    resolved = resolved_challenge(governance, challenge["challenge_id"], "suspend")["challenge"]
    appeal = governance.create_appeal(resolved["challenge_id"], {
        "actor": "Appeal Preparer", "rationale": "New evidence supports reinstatement.", "evidence_reference": "Appeal evidence", "public_visible": True,
    })["appeal"]
    with pytest.raises(ValueError, match="separation of duties"):
        governance.review_appeal(appeal["appeal_id"], {
            "actor": "Appeal Preparer", "reason": "Review", "evidence_reference": "Evidence", "recommended_outcome": "reinstate",
        })
    appeal = governance.review_appeal(appeal["appeal_id"], {
        "actor": "Appeal Reviewer", "reason": "Evidence reviewed.", "evidence_reference": "Appeal review", "recommended_outcome": "reinstate",
    })["appeal"]
    with pytest.raises(ValueError, match="separation of duties"):
        governance.approve_appeal(appeal["appeal_id"], {
            "approved_by": "Appeal Reviewer", "reason": "Approve", "outcome": "reinstate",
        })
    result = governance.approve_appeal(appeal["appeal_id"], {
        "approved_by": "Appeal Governor", "reason": "Reinstatement approved.", "outcome": "reinstate", "public_visible": True,
    })
    assert result["institution"]["status"] == "approved"
    assert registry.consensus("preservation-exchange:alpha", public=True)["verified_institution_count"] == 1


def test_private_challenges_and_appeals_do_not_enter_public_history(tmp_path):
    registry, governance = centers(tmp_path)
    approved_institution(registry)
    challenge = submitted_challenge(governance, public_visible=False)
    reviewed_challenge(governance, challenge["challenge_id"], "suspend")
    resolved = resolved_challenge(governance, challenge["challenge_id"], "suspend", public_visible=False)["challenge"]
    appeal = governance.create_appeal(resolved["challenge_id"], {
        "actor": "Appeal Preparer", "rationale": "Appeal", "evidence_reference": "Evidence", "public_visible": True,
    })["appeal"]
    appeal = governance.review_appeal(appeal["appeal_id"], {
        "actor": "Appeal Reviewer", "reason": "Review", "evidence_reference": "Evidence", "recommended_outcome": "uphold",
    })["appeal"]
    governance.approve_appeal(appeal["appeal_id"], {
        "approved_by": "Appeal Governor", "reason": "Uphold", "outcome": "uphold", "public_visible": True,
    })
    assert governance.challenges(public=True) == []
    assert governance.appeals(public=True) == []


def test_identity_and_credentials_are_rejected(tmp_path):
    registry, governance = centers(tmp_path)
    approved_institution(registry)
    base = {
        "actor": "A", "institution_id": "preservation-institution:alpha", "challenge_type": "evidence_gap",
        "summary": "Review", "rationale": "Review", "evidence_reference": "Evidence",
    }
    with pytest.raises(ValueError):
        governance.create_challenge({**base, "contact_email": "person@example.org"})
    with pytest.raises(ValueError):
        governance.create_challenge({**base, "api_token": "secret"})


def test_json_and_markdown_governance_packages(tmp_path):
    registry, governance = centers(tmp_path)
    approved_institution(registry)
    challenge = submitted_challenge(governance)
    reviewed_challenge(governance, challenge["challenge_id"], "suspend")
    resolved_challenge(governance, challenge["challenge_id"], "suspend")
    media, body = governance.package_payload("preservation-institution:alpha", "json")
    assert media == "application/json"
    assert len(json.loads(body)["package_sha256"]) == 64
    media, body = governance.package_payload("preservation-institution:alpha", "markdown")
    assert media == "text/markdown"
    assert "append-only" in body.lower()


def test_public_routes_are_read_only(monkeypatch, tmp_path):
    registry, governance = centers(tmp_path)
    approved_institution(registry)
    challenge = submitted_challenge(governance)
    reviewed_challenge(governance, challenge["challenge_id"], "suspend")
    resolved_challenge(governance, challenge["challenge_id"], "suspend")
    monkeypatch.setattr(main, "_live_intelligence_registry_governance", lambda settings: governance)
    client = TestClient(main.app)
    status = client.get("/public/live-intelligence/registry-governance/status")
    assert status.status_code == 200
    assert status.json()["public_challenge_count"] == 1
    history = client.get("/public/live-intelligence/registry-governance/institutions/preservation-institution:alpha")
    assert history.status_code == 200
    assert history.json()["governance"]["current_status"] == "suspended"
    assert client.post("/public/live-intelligence/registry-governance/challenges", json={}).status_code == 405
