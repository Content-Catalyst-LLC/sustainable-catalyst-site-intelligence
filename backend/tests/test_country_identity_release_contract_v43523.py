from __future__ import annotations

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app
from app.release_health_v43523 import deployment_verification, source_health_policy
from app.country_identity_v43523 import readiness


def test_country_identity_readiness_is_first_party_network_free_and_isolated():
    payload = readiness()
    assert payload["ok"] is True
    assert payload["country_count"] >= 170
    assert payload["network_calls_performed"] is False
    assert payload["upstream_health_release_blocking"] is False
    assert payload["checks"]["israel_iso3_bound_to_israel"] is True
    assert payload["checks"]["palestine_iso3_bound_to_palestine"] is True
    assert payload["checks"]["country_identity_is_first_party"] is True


def test_deployment_gate_requires_country_identity_without_upstream_health():
    settings = Settings(_env_file=None)
    verification = deployment_verification(settings)
    assert verification["ok"] is True
    assert "/public/country-identity/readiness" in verification["required_routes"]
    assert len(verification["required_routes"]) == 17
    for key in (
        "canonical_country_identity_ready",
        "country_identity_network_free",
        "country_identity_upstream_non_blocking",
        "israel_identity_binding_isolated",
        "palestine_identity_binding_isolated",
        "canonical_country_identity_first_party",
    ):
        assert verification["checks"][key] is True, key
    policy = source_health_policy(settings)["country_identity_policy"]
    assert policy["network_calls_performed"] is False
    assert policy["upstream_health_release_blocking"] is False
    assert policy["israel_binding"] == "ISR -> IL -> Israel"
    assert policy["palestine_binding"] == "PSE -> PS -> Palestine"
    client = TestClient(app)
    response = client.get("/public/country-identity/readiness")
    assert response.status_code == 200
    assert response.json()["checks"]["israel_iso3_bound_to_israel"] is True
    deployment = client.get("/public/deployment-verification")
    assert deployment.status_code == 200
    assert deployment.json()["checks"]["palestine_identity_binding_isolated"] is True
