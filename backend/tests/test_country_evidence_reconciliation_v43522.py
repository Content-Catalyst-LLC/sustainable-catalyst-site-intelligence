from pathlib import Path

from app import country_evidence_reconciliation_v43522 as reconciliation


def test_palestine_pcbs_world_bank_population_discrepancy_selects_pcbs_without_blending():
    payload = reconciliation.reconcile_evidence(
        jurisdiction="PSE",
        concept_id="population_total",
        candidates=[
            {
                "source_id": "pcbs-pxweb", "publisher": "Palestinian Central Bureau of Statistics",
                "concept_id": "population_total", "authority_class": "national-statistical-authority",
                "value": 5_557_096, "unit": "people", "observation_year": 2025,
                "status": "final", "geography_code": "PSE", "methodology_id": "pcbs-2025-revised-estimate",
            },
            {
                "source_id": "world_bank", "publisher": "World Bank Open Data",
                "indicator_id": "SP.POP.TOTL", "authority_class": "international-harmonized",
                "value": 5_414_000, "unit": "people", "observation_year": 2025,
                "status": "final", "geography_code": "PSE", "methodology_id": "world-bank-harmonized-series",
            },
        ],
        now="2026-08-12T00:00:00+00:00",
    )
    assert payload["selected"]["source_id"] == "pcbs-pxweb"
    assert payload["reconciliation_state"] == "reconciled"
    assert payload["comparisons"][0]["classification"] == "material-discrepancy-methodology-diverges"
    assert payload["comparisons"][0]["automatic_blending_allowed"] is False


def test_gaza_operational_electricity_cannot_replace_palestine_structural_access():
    payload = reconciliation.reconcile_evidence(
        jurisdiction="PSE",
        concept_id="electricity_structural_access",
        candidates=[
            {
                "source_id": "world_bank", "indicator_id": "EG.ELC.ACCS.ZS", "authority_class": "international-harmonized",
                "value": 100.0, "unit": "% of population", "observation_year": 2024, "status": "final", "geography_code": "PSE",
            },
            {
                "source_id": "ocha-opt", "concept_id": "electricity_operational_availability", "authority_class": "intergovernmental-custodian",
                "value": 0.0, "unit": "hours/day", "reference_period": "2026-08-01", "status": "provisional", "geography_label": "Gaza Strip",
            },
        ],
        now="2026-08-12T00:00:00+00:00",
    )
    assert payload["selected"]["source_id"] == "world_bank"
    excluded = payload["excluded_from_national_selection"][0]
    assert "different-concept" in excluded["reasons"]
    assert "subnational-context-only" in excluded["reasons"]


def test_west_bank_statistic_is_context_not_palestine_national_substitute():
    payload = reconciliation.reconcile_evidence(
        jurisdiction="PSE",
        concept_id="secondary_enrollment_gross",
        candidates=[
            {
                "source_id": "pcbs-pxweb", "concept_id": "secondary_enrollment_gross", "authority_class": "national-statistical-authority",
                "value": 91.0, "unit": "% gross", "observation_year": 2025, "geography_label": "West Bank", "status": "final",
            },
            {
                "source_id": "world_bank", "indicator_id": "SE.SEC.ENRR", "authority_class": "international-harmonized",
                "value": 89.1, "unit": "% gross", "observation_year": 2023, "geography_code": "PSE", "status": "final",
            },
        ],
    )
    assert payload["selected"]["source_id"] == "world_bank"
    assert payload["reconciliation_state"] == "fallback-selected-preferred-source-not-in-candidate-set"
    assert payload["excluded_from_national_selection"][0]["geography"]["canonical_code"] == "PSE-WBK"


def test_different_reference_periods_are_not_called_contradiction():
    payload = reconciliation.reconcile_evidence(
        jurisdiction="PSE", concept_id="population_total",
        candidates=[
            {"source_id": "pcbs-pxweb", "concept_id": "population_total", "authority_class": "national-statistical-authority", "value": 5_557_096, "unit": "people", "observation_year": 2025, "geography_code": "PSE", "status": "final"},
            {"source_id": "world_bank", "indicator_id": "SP.POP.TOTL", "authority_class": "international-harmonized", "value": 5_300_000, "unit": "people", "observation_year": 2024, "geography_code": "PSE", "status": "final"},
        ],
    )
    assert payload["comparisons"][0]["classification"] == "different-reference-periods"


def test_readiness_is_network_free_and_scope_safe():
    ready = reconciliation.readiness()
    assert ready["ok"] is True
    assert ready["network_calls_performed"] is False
    assert ready["upstream_health_release_blocking"] is False
    assert ready["checks"]["palestine_subnational_scope_guard"] is True
    assert ready["checks"]["automatic_blending_prohibited"] is True


def test_v43522_routes_and_country_ui_are_wired():
    root = Path(__file__).resolve().parents[2]
    main = (root / "backend/app/main.py").read_text()
    app_js = (root / "backend/public_app/assets/app.js").read_text()
    assert '@app.get("/public/country-evidence-reconciliation/readiness")' in main
    assert '@app.post("/public/country-evidence-reconciliation/reconcile")' in main
    assert '@app.get("/public/country/{country_code}/evidence-reconciliation")' in main
    assert "Evidence reconciliation" in app_js
    assert "/evidence-reconciliation" in app_js
