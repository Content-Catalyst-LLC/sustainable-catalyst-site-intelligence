from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.evidence_presentation_v43519 import classify_evidence, readiness as evidence_readiness, source_priority
from app.main import app
from app.production_soak_v43519 import (
    circuit_opening,
    circuit_recovery,
    explicit_stale_fallback,
    missing_credential_degradation,
    provider_flapping_24_cycles,
    rate_limit_retry_after,
    readiness as soak_readiness,
    run_soak_suite,
    service_unavailable_recovery,
    steady_success,
)
from app.release_health_v43519 import deployment_verification
from app.workspace_evidence_unification_v4358 import canonicalize_country_indicator

ROOT = Path(__file__).resolve().parents[2]


def test_steady_success_scenario():
    assert steady_success()["passed"] is True


def test_429_retry_after_scenario():
    row = rate_limit_retry_after()
    assert row["passed"] is True and row["retry_after_honored"] == 1


def test_503_recovery_scenario():
    row = service_unavailable_recovery()
    assert row["passed"] is True and row["attempts"] == 3


def test_explicit_stale_fallback_scenario():
    row = explicit_stale_fallback()
    assert row["passed"] is True and row["cache_status"] == "stale-error" and row["stale"] is True


def test_circuit_opening_scenario():
    row = circuit_opening()
    assert row["passed"] is True and row["circuit_state"] == "open"


def test_circuit_recovery_scenario():
    row = circuit_recovery()
    assert row["passed"] is True and row["circuit_state"] == "closed"


def test_24_cycle_provider_flapping_scenario():
    row = provider_flapping_24_cycles()
    assert row["passed"] is True and row["cycles"] == 24 and row["successes"] == 12 and row["degraded_cycles"] == 12


def test_missing_credentials_degrade_without_blocking_release():
    row = missing_credential_degradation()
    assert row["passed"] is True and row["release_blocking"] is False and row["missing_profiles"] == row["profile_count"]


def test_soak_suite_is_exactly_eight_and_network_free():
    data = run_soak_suite(Settings(_env_file=None))
    assert data["ok"] is True
    assert data["scenario_count"] == 8 and data["passed_scenario_count"] == 8
    assert data["network_calls_performed"] is False
    assert data["upstream_health_release_blocking"] is False
    assert soak_readiness()["ok"] is True


def test_world_bank_annual_retrieval_is_not_live_operational_truth():
    data = classify_evidence(
        jurisdiction="PSE", indicator_id="EG.ELC.ACCS.ZS", source="World Bank Open Data",
        observation_year=2024, data_state="live", value_available=True, now="2026-08-12",
    )
    assert data["transport_state"] == "live"
    assert data["evidence_class"] == "harmonized-benchmark"
    assert data["evidence_label"] == "HARMONIZED BENCHMARK"
    assert data["current_condition_claim_allowed"] is False


def test_palestine_pcbs_precedence_is_exposed_without_erasing_world_bank_comparison():
    priorities = source_priority("PSE", "electricity_structural_access")
    assert priorities[0]["source_id"] == "pcbs-pxweb-sdgs" and priorities[0]["connected"] is True
    assert any(row["source_id"] == "world_bank" and row["role"] == "harmonized-fallback" for row in priorities)
    assert evidence_readiness()["ok"] is True


def test_canonical_observation_separates_transport_and_presentation_state():
    country = {"code":"PSE","iso2":"PS","name":"Palestine"}
    indicator = {
        "id":"EG.ELC.ACCS.ZS","key":"electricity_access","label":"Access to electricity","domain":"Infrastructure",
        "unit":"% of population","format":"percent","latest":{"year":2024,"value":100.0,"unit":"% of population"},
        "series":[],"source_id":"EG.ELC.ACCS.ZS","source":"World Bank Open Data","source_url":"https://data.worldbank.org/indicator/EG.ELC.ACCS.ZS?locations=PS",
        "data_state":"live","cache_state":"live","retrieved_at":"2026-08-12T00:00:00+00:00","stale":False,"lineage":{},
    }
    obs = canonicalize_country_indicator(country, indicator)
    assert obs["transport_state"] == "live"
    assert obs["presentation_state"] == "harmonized-benchmark"
    assert obs["presentation_label"] == "HARMONIZED BENCHMARK"
    assert "does not represent current electricity availability" in obs["evidence_presentation"]["warning"]


def test_release_gate_requires_soak_semantics_browser_resilience_and_canonical_truth():
    data = deployment_verification(Settings(_env_file=None))
    assert data["ok"] is True
    assert data["checks"]["production_soak_control_plane_ready"] is True
    assert data["checks"]["all_eight_deterministic_soak_scenarios_pass"] is True
    assert data["checks"]["semantic_truth_guard_ready"] is True
    assert data["checks"]["canonical_workspace_evidence_truth_ready"] is True
    assert data["checks"]["live_provider_operator_soak_non_blocking"] is True
    assert len(data["required_routes"]) == 12


def test_public_endpoints_and_sources_workspace_surface_soak_and_semantic_truth():
    client = TestClient(app)
    for path in ("/public/production-soak", "/public/production-soak/readiness", "/public/evidence-presentation/readiness", "/public/deployment-verification"):
        response = client.get(path)
        assert response.status_code == 200, path
        assert response.json()["ok"] is True, path
    classified = client.get("/public/evidence-presentation/classify", params={"jurisdiction":"PSE","indicator_id":"EG.ELC.ACCS.ZS","source":"World Bank Open Data","observation_year":2024,"data_state":"live"})
    assert classified.status_code == 200 and classified.json()["evidence_class"] == "harmonized-benchmark"
    html = (ROOT / "backend/public_app/index.html").read_text(encoding="utf-8")
    js = (ROOT / "backend/public_app/assets/app.js").read_text(encoding="utf-8")
    assert "LIVE-OPERATION STRESS LAYER · v4.39.1" in html
    assert "productionSoakScenarioMetric" in html
    assert 'apiWithRetry("/public/production-soak"' in js
    assert "item.evidence_label||item.data_state" in js
