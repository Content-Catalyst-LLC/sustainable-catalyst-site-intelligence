import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app import main
from app.live_intelligence_federated_registry_v3180 import LiveIntelligenceFederatedPreservationRegistry
from app.live_intelligence_registry_governance_v3190 import LiveIntelligenceRegistryGovernanceCenter
from app.live_intelligence_registry_discovery_v3200 import (
    LiveIntelligenceRegistryDiscovery,
    POLICY_SCHEMA_VERSION,
    registry_discovery_policy,
)


class ExchangeStub:
    def __init__(self):
        self.rows = {
            "preservation-exchange:alpha": {
                "exchange_id": "preservation-exchange:alpha",
                "status": "approved",
                "package_sha256": "a" * 64,
                "exchange_sha256": "b" * 64,
                "profile": "bagit_manifest_1_0",
                "institution_reference": "Public exchange register",
                "record_count": 4,
                "approved_at": "2026-07-01T12:00:00Z",
                "public_visible": True,
                "standards_alignment_only": True,
                "created_by": "Internal Exchange Preparer",
                "approved_by": "Internal Exchange Approver",
            },
            "preservation-exchange:private": {
                "exchange_id": "preservation-exchange:private",
                "status": "approved",
                "package_sha256": "c" * 64,
                "exchange_sha256": "d" * 64,
                "profile": "ro_crate_1_1",
                "institution_reference": "Private exchange register",
                "record_count": 2,
                "public_visible": False,
            },
        }

    def exchange(self, exchange_id, public=False):
        row = self.rows.get(exchange_id)
        if not row or (public and row.get("public_visible") is not True):
            raise KeyError(exchange_id)
        return dict(row)

    def exchanges(self, public=False, limit=1000):
        rows = list(self.rows.values())
        if public:
            rows = [row for row in rows if row.get("public_visible") is True]
        return [dict(row) for row in rows[:limit]]


def settings_for(tmp_path):
    return Settings(
        environment="development",
        live_intelligence_preservation_registry_institutions_path=str(tmp_path / "institutions.jsonl"),
        live_intelligence_preservation_registry_attestations_path=str(tmp_path / "attestations.jsonl"),
        live_intelligence_preservation_registry_events_path=str(tmp_path / "registry-events.jsonl"),
        live_intelligence_registry_governance_challenges_path=str(tmp_path / "challenges.jsonl"),
        live_intelligence_registry_governance_appeals_path=str(tmp_path / "appeals.jsonl"),
        live_intelligence_registry_governance_events_path=str(tmp_path / "governance-events.jsonl"),
        live_intelligence_preservation_registry_consensus_threshold=2,
    )


def centers(tmp_path):
    settings = settings_for(tmp_path)
    exchange = ExchangeStub()
    registry = LiveIntelligenceFederatedPreservationRegistry(settings, exchange_center=exchange)
    governance = LiveIntelligenceRegistryGovernanceCenter(settings, registry_center=registry)
    discovery = LiveIntelligenceRegistryDiscovery(
        registry_center=registry, governance_center=governance, exchange_center=exchange,
    )
    return exchange, registry, governance, discovery


def approved_institution(registry, suffix="alpha", public_visible=True, jurisdiction="US-IL", institution_type="university_repository"):
    institution = registry.create_institution({
        "actor": f"Internal Preparer {suffix}",
        "institution_id": f"preservation-institution:{suffix}",
        "institution_name": f"Repository {suffix.title()}",
        "jurisdiction": jurisdiction,
        "institution_type": institution_type,
        "repository_reference": f"https://example.org/repositories/{suffix}",
        "public_policy_reference": f"https://example.org/policies/{suffix}",
        "trust_profile": "policy_reviewed",
        "trust_basis_note": "Public preservation policy and checksum verification evidence reviewed.",
        "supported_profiles": ["bagit_manifest_1_0"],
        "verification_methods": ["manual_checksum"],
    })["institution"]
    institution = registry.verify_institution(institution["institution_id"], {
        "actor": f"Internal Verifier {suffix}",
        "reason": "Internal review details must not be public.",
        "evidence_reference": f"https://example.org/evidence/{suffix}",
    })["institution"]
    return registry.approve_institution(institution["institution_id"], {
        "approved_by": f"Internal Governor {suffix}",
        "reason": "Internal approval details must not be public.",
        "public_visible": public_visible,
    })["institution"]


def attestation(registry, institution_id="preservation-institution:alpha", public_visible=True):
    return registry.record_attestation("preservation-exchange:alpha", {
        "actor": "Internal Attestation Officer",
        "institution_id": institution_id,
        "method": "manual_checksum",
        "result": "verified",
        "reported_package_sha256": "a" * 64,
        "evidence_reference": "https://example.org/attestations/alpha",
        "attestation_note": "Independent repository checksum review.",
        "public_visible": public_visible,
    })["attestation"]


def public_challenge(governance):
    challenge = governance.create_challenge({
        "actor": "Internal Challenge Preparer",
        "institution_id": "preservation-institution:alpha",
        "challenge_type": "status_accuracy",
        "summary": "Trust profile clarification",
        "rationale": "The public record should clarify the scope of policy review.",
        "evidence_reference": "https://example.org/challenges/alpha",
        "public_visible": True,
    })["challenge"]
    challenge = governance.review_challenge(challenge["challenge_id"], {
        "actor": "Internal Challenge Reviewer",
        "reason": "Internal review details.",
        "evidence_reference": "https://example.org/challenge-reviews/alpha",
        "recommended_action": "no_action",
    })["challenge"]
    return governance.approve_challenge(challenge["challenge_id"], {
        "approved_by": "Internal Challenge Governor",
        "reason": "Public record remains accurate.",
        "action": "no_action",
        "public_visible": True,
    })["challenge"]


def test_policy_declares_read_only_public_search_boundaries():
    policy = registry_discovery_policy()
    assert policy["schema"] == POLICY_SCHEMA_VERSION
    assert "institution" in policy["record_types"]
    assert policy["boundaries"]["search_queries_stored"] is False
    assert policy["boundaries"]["staff_identities_exposed"] is False
    assert policy["boundaries"]["source_records_mutated"] is False


def test_discovery_indexes_only_public_records(tmp_path):
    _, registry, _, discovery = centers(tmp_path)
    approved_institution(registry, "alpha", True)
    approved_institution(registry, "hidden", False)
    attestation(registry)
    rows = discovery.records()
    ids = {row["record_id"] for row in rows}
    assert "preservation-institution:alpha" in ids
    assert "preservation-institution:hidden" not in ids
    assert "preservation-exchange:private" not in ids


def test_search_matches_name_policy_and_evidence_text(tmp_path):
    _, registry, _, discovery = centers(tmp_path)
    approved_institution(registry)
    result = discovery.search(query="checksum policy")
    assert result["total"] == 1
    assert result["results"][0]["record_type"] == "institution"
    assert result["results"][0]["relevance_score"] > 0


def test_search_supports_facets_and_filters(tmp_path):
    _, registry, _, discovery = centers(tmp_path)
    approved_institution(registry, "alpha", True, "US-IL", "university_repository")
    approved_institution(registry, "beta", True, "IE-D", "national_archive")
    result = discovery.search(record_type="institution", institution_type="national_archive", jurisdiction="IE")
    assert result["total"] == 1
    assert result["results"][0]["institution_id"] == "preservation-institution:beta"
    facets = discovery.facets()
    assert {row["value"] for row in facets["institution_types"]} == {"university_repository", "national_archive"}


def test_search_rejects_unsupported_record_type_and_sort(tmp_path):
    _, _, _, discovery = centers(tmp_path)
    with pytest.raises(ValueError, match="record type"):
        discovery.search(record_type="staff_record")
    with pytest.raises(ValueError, match="sort mode"):
        discovery.search(sort="popularity")


def test_public_results_strip_staff_identity_and_internal_reason_fields(tmp_path):
    _, registry, governance, discovery = centers(tmp_path)
    approved_institution(registry)
    attestation(registry)
    public_challenge(governance)
    text = repr(discovery.search(query="Repository")["results"])
    assert "Internal Preparer" not in text
    assert "Internal Governor" not in text
    assert "created_by" not in text
    assert "approved_by" not in text
    assert "approval_reason" not in text


def test_institution_profile_links_public_evidence_and_consensus(tmp_path):
    _, registry, governance, discovery = centers(tmp_path)
    approved_institution(registry)
    attestation(registry)
    public_challenge(governance)
    profile = discovery.institution_profile("preservation-institution:alpha")
    assert profile["institution"]["institution_name"] == "Repository Alpha"
    assert len(profile["attestations"]) == 1
    assert len(profile["exchanges"]) == 1
    assert profile["exchanges"][0]["consensus"]["consensus_status"] == "partial_consensus"
    assert any(link["label"] == "Preservation policy" for link in profile["evidence_links"])
    assert profile["staff_identities_exposed"] is False


def test_profile_does_not_expose_private_challenges(tmp_path):
    _, registry, governance, discovery = centers(tmp_path)
    approved_institution(registry)
    challenge = governance.create_challenge({
        "actor": "Internal Preparer",
        "institution_id": "preservation-institution:alpha",
        "challenge_type": "evidence_gap",
        "summary": "Private issue",
        "rationale": "Private governance record.",
        "evidence_reference": "Private evidence",
        "public_visible": False,
    })["challenge"]
    assert challenge["public_visible"] is False
    assert discovery.institution_profile("preservation-institution:alpha")["challenges"] == []


def test_status_reports_record_counts_without_query_telemetry(tmp_path):
    _, registry, _, discovery = centers(tmp_path)
    approved_institution(registry)
    status = discovery.status()
    assert status["record_type_counts"]["institution"] == 1
    assert status["search_queries_stored"] is False
    assert status["visitor_profiles_created"] is False


def test_search_pagination_and_deterministic_name_sort(tmp_path):
    _, registry, _, discovery = centers(tmp_path)
    approved_institution(registry, "charlie")
    approved_institution(registry, "alpha")
    approved_institution(registry, "bravo")
    page = discovery.search(record_type="institution", sort="name", offset=1, limit=1)
    assert page["total"] == 3
    assert page["results"][0]["institution_name"] == "Repository Bravo"


def test_main_public_discovery_routes(monkeypatch, tmp_path):
    _, registry, governance, discovery = centers(tmp_path)
    approved_institution(registry)
    monkeypatch.setattr(main, "_live_intelligence_registry_discovery", lambda settings: discovery)
    client = TestClient(main.app)
    assert client.get("/public/live-intelligence/registry-discovery/policy").status_code == 200
    response = client.get("/public/live-intelligence/registry-discovery/search", params={"q": "Repository"})
    assert response.status_code == 200
    assert response.json()["total"] == 1
    profile = client.get("/public/live-intelligence/registry-discovery/institutions/preservation-institution:alpha")
    assert profile.status_code == 200
    assert profile.json()["institution"]["institution_name"] == "Repository Alpha"


def test_main_profile_route_returns_404_for_nonpublic_record(monkeypatch, tmp_path):
    _, _, _, discovery = centers(tmp_path)
    monkeypatch.setattr(main, "_live_intelligence_registry_discovery", lambda settings: discovery)
    client = TestClient(main.app)
    response = client.get("/public/live-intelligence/registry-discovery/institutions/preservation-institution:missing")
    assert response.status_code == 404
