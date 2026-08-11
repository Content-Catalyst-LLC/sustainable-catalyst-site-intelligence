from fastapi.testclient import TestClient
from app.main import app

CLIENT = TestClient(app)


def package_payload():
    return {
        "title": "Brazil public intelligence briefing",
        "summary": "A reviewable public briefing.",
        "publication_type": "intelligence-brief",
        "geographies": ["BRA"],
        "methodology": ["Preserve source identity and observation dates."],
        "limitations": ["The record set is incomplete and does not establish causation."],
        "frozen_at": "2026-08-07T00:00:00Z",
        "sources": [{"source_id": "world-bank", "publisher": "World Bank", "title": "World Development Indicators", "source_url": "https://data.worldbank.org", "retrieved_at": "2026-08-07T00:00:00Z", "truth_state": "historical_only"}],
        "evidence": [{"evidence_id": "bra-pop", "title": "Brazil population", "source_id": "world-bank", "country": "BRA", "indicator_id": "SP.POP.TOTL", "value": 216422446, "unit": "people", "observed_at": "2023", "truth_state": "historical_only"}],
        "blocks": [
            {"block_type": "narrative", "title": "Summary", "text": "Public evidence remains reviewable."},
            {"block_type": "map", "title": "Brazil", "text": "Selected geography.", "source_ids": ["world-bank"], "evidence_ids": ["bra-pop"], "alt_text": "Map showing Brazil as the selected geography."},
        ],
    }


def test_publication_studio_contract_is_review_gated():
    payload = CLIENT.get("/public/publication-studio").json()
    assert payload["version"] == "4.35.6"
    assert payload["contract"] == "briefing-story-map-publication-studio"
    assert payload["human_editorial_review_required"] is True
    assert payload["human_publish_confirmation_required"] is True
    assert payload["automatic_publication"] is False
    assert payload["public_write_performed"] is False


def test_frozen_manifest_is_stable_for_same_supplied_records():
    first = CLIENT.post("/public/publication-studio/frozen-manifest", json=package_payload()).json()["manifest"]
    second = CLIENT.post("/public/publication-studio/frozen-manifest", json=package_payload()).json()["manifest"]
    assert first["manifest_sha256"] == second["manifest_sha256"]
    assert first["source_count"] == 1 and first["evidence_count"] == 1
    assert first["proof_of_accuracy"] is False and first["change_detection_only"] is True


def test_briefing_preview_keeps_methodology_limitations_and_draft_state():
    brief = CLIENT.post("/public/publication-studio/briefing/preview", json=package_payload()).json()["brief"]
    assert brief["editorial_state"] == "draft"
    assert brief["human_review_required"] is True
    assert brief["automatic_publication"] is False and brief["write_performed"] is False
    assert brief["methodology"] and brief["limitations"]
    assert len(brief["brief_sha256"]) == 64


def test_story_map_requires_accessible_visual_description_for_pass():
    good = CLIENT.post("/public/publication-studio/story-map/preview", json=package_payload()).json()["story_map"]
    assert good["accessibility"]["status"] == "pass"
    bad_payload = package_payload()
    bad_payload["blocks"][1]["alt_text"] = ""
    bad = CLIENT.post("/public/publication-studio/story-map/preview", json=bad_payload).json()["story_map"]
    assert bad["accessibility"]["status"] == "needs-review"
    assert bad["interpretation_boundary"].endswith("do not establish causation.")


def test_publication_readiness_is_not_publish_authorization():
    ready = CLIENT.post("/public/publication-studio/readiness", json=package_payload()).json()
    assert ready["status"] == "ready-for-human-review"
    assert all(ready["checks"].values())
    assert ready["human_review_still_required"] is True
    assert ready["publish_allowed"] is False


def test_incomplete_brief_does_not_pass_readiness():
    payload = package_payload(); payload["methodology"] = []; payload["limitations"] = []
    ready = CLIENT.post("/public/publication-studio/readiness", json=payload).json()
    assert ready["status"] == "incomplete"
    assert ready["checks"]["methodology"] is False and ready["checks"]["limitations"] is False


def test_correction_preview_preserves_prior_public_version():
    response = CLIENT.post("/public/publication-studio/correction/preview", json={"publication_id": "brief:bra", "version_id": "brief:bra:v1", "action": "correction", "note": "Correct the observation period."})
    assert response.status_code == 200
    correction = response.json()["correction"]
    assert correction["preserves_prior_version"] is True
    assert correction["human_review_required"] is True
    assert correction["automatic_change"] is False and correction["write_performed"] is False


def test_publication_package_contains_accessible_print_source_and_evidence_csv():
    result = CLIENT.post("/public/publication-studio/package", json=package_payload()).json()
    packet = result["packet"]
    assert packet["print_html_ready"] is True and packet["accessible_pdf_source_ready"] is True
    assert packet["pdf_binary_generated"] is False
    assert packet["human_review_required"] is True and packet["automatic_publication"] is False
    assert "<!doctype html>" in result["print_html"].lower()
    assert "evidence_id,title,source_id" in result["csv_evidence"]
    assert len(packet["package_sha256"]) == 64


def test_public_preview_rejects_secret_fields_and_unsafe_source_urls():
    secret = package_payload(); secret["api_key"] = "should-not-be-here"
    assert CLIENT.post("/public/publication-studio/briefing/preview", json=secret).status_code == 400
    unsafe = package_payload(); unsafe["sources"][0]["source_url"] = "javascript:alert(1)"
    manifest = CLIENT.post("/public/publication-studio/frozen-manifest", json=unsafe).json()["manifest"]
    assert manifest["sources"][0]["source_url"] == ""
