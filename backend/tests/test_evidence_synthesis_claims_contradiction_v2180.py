from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.evidence_synthesis_v2180 import EvidenceSynthesisCenter, SCHEMA_VERSION
from app.main import app


def settings(tmp_path: Path) -> Settings:
    return Settings(
        api_token="dev-token-change-me",
        evidence_synthesis_root_path=str(tmp_path / "evidence"),
        evidence_synthesis_claims_path=str(tmp_path / "claims.jsonl"),
        evidence_synthesis_evidence_path=str(tmp_path / "evidence.jsonl"),
        evidence_synthesis_reviews_path=str(tmp_path / "reviews.jsonl"),
        evidence_synthesis_syntheses_path=str(tmp_path / "syntheses.jsonl"),
        evidence_synthesis_uncertainty_path=str(tmp_path / "uncertainty.jsonl"),
        evidence_synthesis_policy_path="backend/data/evidence_synthesis_policy_v2180.json",
    )


def claim(**overrides):
    value = {
        "claim_id": "heat-mortality",
        "title": "Extreme heat increases mortality risk",
        "statement": "Periods of extreme heat are associated with increased mortality risk in exposed populations.",
        "claim_type": "interpretive",
        "scope": "Public-health evidence review",
        "visibility": "public",
        "status": "draft",
    }
    value.update(overrides)
    return value


def evidence(evidence_id: str, relationship: str, **overrides):
    value = {
        "evidence_id": evidence_id,
        "claim_id": "heat-mortality",
        "relationship": relationship,
        "source_id": f"source-{evidence_id}",
        "source_title": f"Evidence source {evidence_id}",
        "source_url": "https://example.org/source",
        "source_type": "research-paper",
        "excerpt": "A source-bounded excerpt used only for evidence review.",
        "locator": "p. 4",
        "visibility": "public",
    }
    value.update(overrides)
    return value


def test_claim_registration_requires_human_confirmation_for_direct_approval(tmp_path):
    center = EvidenceSynthesisCenter(settings(tmp_path))
    try:
        center.register_claim(claim(status="approved"))
        assert False, "approval should require human confirmation"
    except ValueError as exc:
        assert "human_review_confirmed" in str(exc)
    result = center.register_claim(claim())
    assert result["claim"]["human_review_required"] is True
    assert result["claim"]["claim_sha256"]


def test_evidence_relationships_and_redaction_are_preserved(tmp_path):
    center = EvidenceSynthesisCenter(settings(tmp_path))
    center.register_claim(claim())
    result = center.add_evidence(evidence("support-1", "supports", metadata={"api_key": "secret", "dataset": "heat"}))
    record = result["evidence"]
    assert record["relationship"] == "supports"
    assert record["redacted_metadata"]["api_key"] == "[redacted]"
    assert record["evidence_not_conclusion"] is True


def test_contradiction_review_keeps_support_and_conflict_visible(tmp_path):
    center = EvidenceSynthesisCenter(settings(tmp_path))
    center.register_claim(claim())
    center.add_evidence(evidence("support-1", "supports"))
    center.add_evidence(evidence("conflict-1", "conflicts"))
    review = center.contradiction_review("heat-mortality")
    assert review["contradiction_status"] == "review_required"
    assert review["human_resolution_required"] is True
    assert review["causation_not_inferred"] is True


def test_uncertainty_and_deterministic_synthesis_are_grounded(tmp_path):
    center = EvidenceSynthesisCenter(settings(tmp_path))
    center.register_claim(claim())
    center.add_evidence(evidence("support-1", "supports"))
    center.add_evidence(evidence("qualify-1", "qualifies"))
    center.record_uncertainty({"claim_id": "heat-mortality", "category": "coverage", "severity": "material", "description": "Rural coverage is limited.", "visibility": "public"})
    result = center.synthesize({"claim_id": "heat-mortality", "ai_assist": True})
    synthesis = result["synthesis"]
    assert synthesis["conclusion"] == "supported_with_qualifications"
    assert synthesis["grounded_only"] is True
    assert synthesis["ai_assistance"]["external_model_invoked"] is False
    assert synthesis["citations"][0]["evidence_id"]


def test_review_updates_claim_and_public_boundary(tmp_path):
    center = EvidenceSynthesisCenter(settings(tmp_path))
    center.register_claim(claim())
    center.add_evidence(evidence("support-1", "supports"))
    review = center.review_claim({"claim_id": "heat-mortality", "decision": "approve", "reviewer_role": "Senior evidence reviewer", "rationale": "The evidence and limitations have been reviewed."})
    assert review["claim"]["status"] == "approved"
    assert center.claims(public=True)["count"] == 1


def test_public_synthesis_requires_approved_claim_and_approval_flag(tmp_path):
    center = EvidenceSynthesisCenter(settings(tmp_path))
    center.register_claim(claim())
    center.add_evidence(evidence("support-1", "supports"))
    try:
        center.synthesize({"claim_id": "heat-mortality", "visibility": "public", "human_review_confirmed": True})
        assert False
    except ValueError as exc:
        assert "approved claim" in str(exc)
    center.review_claim({"claim_id": "heat-mortality", "decision": "approve", "reviewer_role": "Reviewer", "rationale": "Approved with documented limits."})
    result = center.synthesize({"claim_id": "heat-mortality", "visibility": "public", "human_review_confirmed": True})
    assert result["synthesis"]["approval_status"] == "approved"


def test_export_and_handoffs_preserve_relationships_and_read_only_boundary(tmp_path):
    center = EvidenceSynthesisCenter(settings(tmp_path))
    center.register_claim(claim())
    center.add_evidence(evidence("support-1", "supports"))
    center.review_claim({"claim_id": "heat-mortality", "decision": "approve", "reviewer_role": "Reviewer", "rationale": "Approved."})
    export = center.export_packet("heat-mortality", public=True)
    assert export["read_only"] is True
    assert export["packet"]["packet_sha256"]
    assert "evidence_id,relationship" in export["csv"]
    handoff = center.handoff("heat-mortality", "knowledge-library", public=True)
    assert handoff["destination"] == "knowledge-library"
    assert handoff["read_only"] is True


def test_public_and_admin_routes(tmp_path):
    cfg = settings(tmp_path)
    app.dependency_overrides[get_settings] = lambda: cfg
    try:
        client = TestClient(app)
        for path in ["/public/evidence-synthesis", "/public/evidence-synthesis/methodology", "/public/evidence-synthesis/diagnostics", "/public/claims", "/admin/evidence-synthesis/control-center"]:
            response = client.get(path)
            assert response.status_code == 200, (path, response.text)
        registered = client.post("/admin/evidence-synthesis/claims/register", json=claim())
        assert registered.status_code == 200
        added = client.post("/admin/evidence-synthesis/evidence/add", json=evidence("support-1", "supports"))
        assert added.status_code == 200
        reviewed = client.post("/admin/evidence-synthesis/claims/review", json={"claim_id": "heat-mortality", "decision": "approve", "reviewer_role": "Reviewer", "rationale": "Approved."})
        assert reviewed.status_code == 200
        synthesis = client.post("/admin/evidence-synthesis/synthesize", json={"claim_id": "heat-mortality", "visibility": "public", "human_review_confirmed": True})
        assert synthesis.status_code == 200
        public = client.get("/public/claims")
        assert public.json()["count"] == 1
        detail = client.get("/public/claims/heat-mortality")
        assert detail.status_code == 200
    finally:
        app.dependency_overrides.clear()


def test_public_summary_exposes_safety_and_schema(tmp_path):
    summary = EvidenceSynthesisCenter(settings(tmp_path)).public_summary()
    assert summary["schema"] == SCHEMA_VERSION
    assert summary["human_review_required"] is True
    assert summary["external_ai_enabled"] is False
    assert any("fabricated evidence" in item.lower() for item in summary["boundaries"])
