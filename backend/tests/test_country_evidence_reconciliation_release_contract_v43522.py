from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app
from app.version import APP_VERSION
from app.country_evidence_reconciliation_v43522 import readiness
from app.release_health_v43522 import deployment_verification, source_health_policy


def test_v43522_release_contract_is_network_free_and_scope_guarded():
    assert APP_VERSION == "4.38.0"
    ready = readiness()
    assert ready["ok"] is True
    assert ready["network_calls_performed"] is False
    assert ready["upstream_health_release_blocking"] is False
    assert ready["checks"]["exact_concept_before_authority"] is True
    assert ready["checks"]["national_geography_before_precedence"] is True
    assert ready["checks"]["palestine_subnational_scope_guard"] is True
    assert ready["checks"]["automatic_blending_prohibited"] is True

    settings = Settings(_env_file=None)
    verification = deployment_verification(settings)
    assert verification["ok"] is True
    assert len(verification["required_routes"]) == 16
    assert verification["checks"]["country_evidence_reconciliation_ready"] is True
    assert verification["checks"]["palestine_geographic_scope_guard"] is True
    assert verification["checks"]["automatic_cross_source_blending_prohibited"] is True
    assert "/public/country-evidence-reconciliation/readiness" in verification["required_routes"]

    health = source_health_policy(settings)
    policy = health["country_evidence_reconciliation_policy"]
    assert policy["discrepancy_policy"].startswith("retain and disclose")
    assert "Gaza and West Bank" in policy["palestine_scope_policy"]
    assert policy["upstream_health_release_blocking"] is False

    client = TestClient(app)
    response = client.get("/public/country-evidence-reconciliation/readiness")
    assert response.status_code == 200 and response.json()["ok"] is True
    response = client.post("/public/country-evidence-reconciliation/reconcile", json={
        "jurisdiction": "PSE",
        "concept_id": "population_total",
        "candidates": [
            {"source_id": "pcbs-pxweb", "concept_id": "population_total", "authority_class": "national-statistical-authority", "value": 5557096, "unit": "people", "observation_year": 2025, "geography_code": "PSE", "status": "final"},
            {"source_id": "world_bank", "indicator_id": "SP.POP.TOTL", "authority_class": "international-harmonized", "value": 5414000, "unit": "people", "observation_year": 2025, "geography_code": "PSE", "status": "final"},
        ],
    })
    assert response.status_code == 200
    data = response.json()
    assert data["selected"]["source_id"] == "pcbs-pxweb"
    assert data["comparisons"][0]["automatic_blending_allowed"] is False
