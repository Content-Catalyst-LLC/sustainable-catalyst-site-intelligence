from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app
from app.research_evidence_integration_v3270 import ResearchEvidenceIntegrationCenter

CLIENT = TestClient(app)


def sample():
    return {
        "title": "Brazil energy investigation",
        "question": "What does the selected evidence establish about Brazil energy conditions?",
        "route": "research",
        "countries": ["BRA"],
        "records": [
            {
                "id": "wb-energy-bra-2023",
                "title": "Energy use",
                "record_type": "indicator",
                "evidence_class": "official-statistic",
                "country": "BRA",
                "indicator_id": "energy-use",
                "value": 10.5,
                "unit": "GJ/person",
                "publisher": "World Bank",
                "source_id": "world-bank",
                "source_url": "https://api.worldbank.org/",
                "observed_at": "2023",
                "retrieved_at": "2026-08-06T00:00:00Z",
                "truth_state": "historical_only",
                "limitations": ["Historical observation"],
            },
            {
                "id": "event-bra-1",
                "title": "Public event record",
                "record_type": "event",
                "evidence_class": "event-record",
                "country": "BRA",
                "source_id": "usgs-earthquakes",
                "source_url": "https://earthquake.usgs.gov/",
                "retrieved_at": "2026-08-06T00:00:00Z",
                "truth_state": "available",
            },
        ],
        "evidence_gaps": ["No verified subnational series in this packet"],
    }


def test_schema_requires_human_confirmation_and_no_automatic_delivery():
    payload = CLIENT.get("/public/research-integration").json()
    assert payload["version"] == "3.31.0"
    assert payload["contract"] == "research-evidence-and-knowledge-integration"
    assert payload["human_confirmation_required"] is True
    assert payload["automatic_delivery"] is False
    assert payload["automatic_publication"] is False
    assert set(payload["targets"]) == {"research-librarian", "knowledge-library", "workbench", "decision-studio"}


def test_context_retains_source_snapshots_and_record_fingerprints():
    payload = CLIENT.post("/public/research-integration/context", json=sample()).json()
    context = payload["context"]
    assert context["countries"] == ["BRA"]
    assert len(context["records"]) == 2
    assert len(context["records"][0]["fingerprint"]) == 64
    snapshot = context["records"][0]["source_snapshot"]
    assert snapshot["publisher"] == "World Bank"
    assert snapshot["observed_at"] == "2023"
    assert snapshot["retrieved_at"].startswith("2026-08-06")


def test_manifest_exports_record_level_provenance_without_imputation():
    payload = CLIENT.post("/public/research-integration/evidence-manifest", json=sample()).json()
    assert payload["record_count"] == 2
    assert len(payload["manifest"]["fingerprint"]) == 64
    assert payload["manifest"]["records"][0]["truth_state"] == "historical_only"


def test_citation_export_deduplicates_source_records_safely():
    source = sample()
    duplicate = dict(source["records"][0]); duplicate["id"] = "duplicate"
    source["records"].append(duplicate)
    payload = CLIENT.post("/public/research-integration/citations", json=source).json()
    assert len(payload["citations"]) == 2
    assert payload["citations"][0]["source_url"].startswith("https://")
    assert len(payload["fingerprint"]) == 64


def test_claim_map_preserves_support_and_contradiction_without_auto_resolution():
    source = sample()
    source["claims"] = [{"id": "c1", "text": "Selected energy conditions changed."}]
    source["relationships"] = [
        {"claim_id": "c1", "record_id": "wb-energy-bra-2023", "relation": "supports"},
        {"claim_id": "c1", "record_id": "event-bra-1", "relation": "contradicts"},
    ]
    payload = CLIENT.post("/public/research-integration/claim-map", json=source).json()
    assert {row["relation"] for row in payload["relationships"]} == {"supports", "contradicts"}
    assert payload["automatic_resolution"] is False
    assert payload["human_review_required"] is True


def test_knowledge_library_discovery_is_query_plan_not_claimed_search_result():
    payload = CLIENT.post("/public/research-integration/knowledge-library/discovery", json=sample()).json()
    assert payload["plan"]["target"] == "knowledge-library"
    assert payload["plan"]["verified_matches"] == []
    assert payload["plan"]["match_state"] == "not-executed"
    assert payload["plan"]["requires_library_index"] is True


def test_research_librarian_handoff_preview_is_not_remote_delivery():
    payload = CLIENT.post("/public/research-integration/handoff/research-librarian/preview", json=sample()).json()
    packet = payload["packet"]
    assert packet["packet_type"] == "research_question"
    assert packet["preview_only"] is True
    assert packet["delivery_attempted"] is False
    assert packet["delivery_verified"] is False
    assert packet["human_confirmation_required"] is True


def test_workbench_handoff_contains_only_quantitative_records():
    payload = CLIENT.post("/public/research-integration/handoff/workbench/preview", json=sample()).json()
    datasets = payload["packet"]["payload"]["datasets"]
    assert len(datasets) == 1
    assert datasets[0]["indicator_id"] == "energy-use"
    assert datasets[0]["country"] == "BRA"


def test_decision_studio_preview_keeps_evidence_and_uncertainty_separate():
    source = sample()
    source["scenarios"] = [{"id": "base", "label": "Base case"}]
    source["uncertainties"] = ["Event coverage incomplete"]
    payload = CLIENT.post("/public/research-integration/handoff/decision-studio/preview", json=source).json()
    packet = payload["packet"]
    assert packet["packet_type"] == "scenario_decision_packet"
    assert packet["payload"]["evidence_ids"]
    assert packet["payload"]["uncertainties"] == ["Event coverage incomplete"]
    assert packet["publication_allowed"] is False


def test_sensitive_fields_are_rejected():
    payload = sample(); payload["api_token"] = "do-not-accept"
    response = CLIENT.post("/public/research-integration/context", json=payload)
    assert response.status_code == 400


def test_non_http_source_urls_are_removed():
    source = sample(); source["records"][0]["source_url"] = "javascript:alert(1)"
    payload = ResearchEvidenceIntegrationCenter(Settings()).context(source)
    assert payload["context"]["records"][0]["source_snapshot"]["source_url"] == ""
