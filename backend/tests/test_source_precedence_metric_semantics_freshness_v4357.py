from __future__ import annotations
from fastapi.testclient import TestClient
import pytest

from app.evidence_intelligence_v4357 import (
    concept_for_indicator, freshness_assessment, indicator_semantics, metric_catalog,
    overview, precedence_catalog, readiness, select_evidence,
)
from app.config import Settings
from app.main import app
from app.record_provenance_v4357 import public_indicator_record_truth
from app.version import APP_VERSION


def settings(**updates):
    return Settings(_env_file=None, **updates)


def test_release_version_and_readiness():
    assert APP_VERSION == "4.35.25"
    assert overview()["critical_boundary"].startswith("Electricity access")
    assert readiness()["ok"] is True
    assert readiness()["network_calls_performed"] is False


def test_metric_catalog_separates_structural_access_from_operational_supply():
    data = metric_catalog()
    concepts = {row["concept_id"]: row for row in data["concepts"]}
    assert concepts["electricity_structural_access"]["kind"] == "structural_access_statistic"
    assert concepts["electricity_operational_availability"]["kind"] == "operational_condition"
    assert "current electricity availability" in concepts["electricity_structural_access"]["forbidden_substitutions"]


def test_world_bank_electricity_indicator_maps_only_to_structural_access():
    assert concept_for_indicator("EG.ELC.ACCS.ZS") == "electricity_structural_access"
    semantics = indicator_semantics("EG.ELC.ACCS.ZS", jurisdiction="PSE")
    assert semantics["concept_id"] == "electricity_structural_access"
    assert semantics["precedence_rules"][0]["preferred_sources"][0] == "pcbs-pxweb-sdgs"


def test_palestine_operational_precedence_excludes_world_bank():
    rules = precedence_catalog(jurisdiction="PSE", concept_id="electricity_operational_availability")["rules"]
    assert rules
    assert "world_bank" not in rules[0]["preferred_sources"]
    assert "ocha-opt" in rules[0]["preferred_sources"]


def test_freshness_is_cadence_aware():
    annual = freshness_assessment(observed_at="2025-12-31", cadence="annual", now="2026-08-11")
    near = freshness_assessment(observed_at="2025-12-31", cadence="near_real_time", now="2026-08-11")
    assert annual["status"] in {"current", "recent"}
    assert near["status"] == "stale"
    assert freshness_assessment(observed_at=None, cadence="annual", now="2026-08-11")["status"] == "unknown"


def test_semantic_mismatch_can_never_win_on_freshness():
    data = select_evidence(
        concept_id="electricity_structural_access", jurisdiction="PSE", now="2026-08-11",
        candidates=[
            {"source_id":"world_bank","indicator_id":"EG.ELC.ACCS.ZS","authority_class":"international-harmonized","value":100.0,"unit":"% of population","observation_year":2024,"status":"final"},
            {"source_id":"ocha-opt","concept_id":"electricity_operational_availability","authority_class":"official-sector-authority","value":"severely constrained","unit":"operational status","observed_at":"2026-08-10","status":"final"},
        ],
    )
    assert data["selected"]["source_id"] == "world_bank"
    assert data["selected"]["concept_id"] == "electricity_structural_access"
    assert next(row for row in data["candidates"] if row["source_id"] == "ocha-opt")["exact_semantics"] is False


def test_pcbs_outranks_world_bank_for_same_palestine_structural_access_concept():
    data = select_evidence(
        concept_id="electricity_structural_access", jurisdiction="PSE", now="2026-08-11",
        candidates=[
            {"source_id":"world_bank","concept_id":"electricity_structural_access","authority_class":"international-harmonized","value":100.0,"unit":"% of population","observation_year":2024,"status":"final"},
            {"source_id":"pcbs-pxweb-sdgs","concept_id":"electricity_structural_access","authority_class":"national-statistical-authority","value":99.9,"unit":"% of population","observation_year":2020,"status":"final"},
        ],
    )
    assert data["selected"]["source_id"] == "pcbs-pxweb-sdgs"
    assert data["selected"]["freshness"]["status"] == "stale"
    assert data["candidates"][0]["score"] != data["candidates"][1]["score"]


def test_conflicting_exact_concept_observations_are_disclosed_not_blended():
    data = select_evidence(
        concept_id="electricity_structural_access", jurisdiction="PSE", now="2026-08-11",
        candidates=[
            {"source_id":"a","concept_id":"electricity_structural_access","authority_class":"national-statistical-authority","value":98.0,"unit":"% of population","observed_at":"2024-12-31"},
            {"source_id":"b","concept_id":"electricity_structural_access","authority_class":"international-harmonized","value":100.0,"unit":"% of population","observed_at":"2024-12-31"},
        ],
    )
    assert len(data["conflicts"]) == 1
    assert data["conflicts"][0]["resolution"] == "disclose-both-no-automatic-blending"
    assert data["selected"]["value"] in {98.0, 100.0}


def test_no_semantically_eligible_evidence_returns_no_selection():
    data = select_evidence(
        concept_id="electricity_operational_availability", jurisdiction="PSE",
        candidates=[{"source_id":"world_bank","indicator_id":"EG.ELC.ACCS.ZS","authority_class":"international-harmonized","value":100.0,"unit":"% of population","observation_year":2024}],
    )
    assert data["selected"] is None
    assert data["selection_state"] == "no-semantically-eligible-evidence"


def test_record_truth_enrichment_prevents_electricity_access_overclaim(monkeypatch):
    from app import record_provenance_v3238 as prior
    fake = {
        "ok":True,"dates":{"observation_year":2024,"observation_at":"2024-12-31T00:00:00+00:00"},
        "source":{"indicator_id":"EG.ELC.ACCS.ZS"},"limitations":[],"assertion":"old assertion",
    }
    monkeypatch.setattr(prior, "public_indicator_record_truth", lambda *_a, **_k: dict(fake))
    data = public_indicator_record_truth(settings(), "PSE", "EG.ELC.ACCS.ZS")
    assert data["semantics"]["concept_id"] == "electricity_structural_access"
    assert "current electricity availability" in data["semantics"]["forbidden_substitutions"]
    assert "not a statement about current electricity supply" in data["assertion"]


def test_selection_input_bounds():
    with pytest.raises(ValueError):
        select_evidence(concept_id="not-real", jurisdiction="PSE", candidates=[{"value":1}])
    with pytest.raises(ValueError):
        select_evidence(concept_id="population_total", jurisdiction="", candidates=[{"value":1}])
    with pytest.raises(ValueError):
        select_evidence(concept_id="population_total", jurisdiction="PSE", candidates=[])


def test_public_evidence_intelligence_routes():
    client = TestClient(app)
    assert client.get("/public/evidence-intelligence").status_code == 200
    assert client.get("/public/evidence-intelligence/metrics").json()["concept_count"] >= 9
    assert client.get("/public/evidence-intelligence/precedence", params={"jurisdiction":"PSE","concept_id":"electricity_structural_access"}).status_code == 200
    assert client.get("/public/evidence-intelligence/freshness", params={"observed_at":"2024-12-31","cadence":"annual","now":"2026-08-11"}).status_code == 200
    assert client.get("/public/evidence-intelligence/readiness").json()["ok"] is True
    response = client.post("/public/evidence-intelligence/select", json={"concept_id":"electricity_operational_availability","jurisdiction":"PSE","candidates":[{"source_id":"world_bank","indicator_id":"EG.ELC.ACCS.ZS","value":100.0,"unit":"% of population"}]})
    assert response.status_code == 200 and response.json()["selected"] is None
