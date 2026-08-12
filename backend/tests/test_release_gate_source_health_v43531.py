from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app
from app.release_health_v43531 import deployment_verification, source_health_policy
from app.version import APP_VERSION

ROOT = Path(__file__).resolve().parents[2]


def settings(**updates):
    return Settings(_env_file=None, **updates)


def test_release_version_is_v43531():
    assert APP_VERSION == "4.35.22"


def test_deployment_verification_is_network_free_and_first_party_only():
    data = deployment_verification(settings())
    assert data["ok"] is True
    assert data["version"] == "4.35.22"
    assert data["network_calls_performed"] is False
    assert data["source_health_blocks_release"] is False
    assert all(data["checks"].values())
    assert "/public/source-health-policy" in data["required_routes"]


def test_source_health_policy_never_blocks_release():
    data = source_health_policy(settings())
    assert data["ok"] is True
    assert data["network_calls_performed"] is False
    assert data["summary"]["release_blocking_sources"] == 0
    assert all(row["release_blocking"] is False for row in data["sources"])


def test_reliefweb_configuration_is_reported_not_release_blocking():
    missing = source_health_policy(settings(reliefweb_appname=""))
    configured = source_health_policy(settings(reliefweb_appname="approved-app"))
    m = next(row for row in missing["sources"] if row["id"] == "reliefweb-v2")
    c = next(row for row in configured["sources"] if row["id"] == "reliefweb-v2")
    assert m["state"] == "configuration-required"
    assert c["state"] == "configured"
    assert m["release_blocking"] is False and c["release_blocking"] is False


def test_public_verification_endpoints_are_available():
    client = TestClient(app)
    deployment = client.get("/public/deployment-verification")
    policy = client.get("/public/source-health-policy")
    assert deployment.status_code == 200
    assert policy.status_code == 200
    assert deployment.json()["version"] == "4.35.22"
    assert policy.json()["summary"]["release_blocking_sources"] == 0


def test_runtime_health_explicitly_does_not_contact_upstream():
    client = TestClient(app)
    data = client.get("/public/runtime-health").json()
    assert data["ok"] is True
    assert data["live_upstream_checks_performed"] is False
    assert any("does not contact third-party APIs" in item for item in data["limitations"])


def test_v4_readiness_keeps_structural_readiness_separate_from_configuration():
    client = TestClient(app)
    data = client.get("/public/v4/readiness").json()
    assert data["ok"] is True
    assert data["summary"]["preserved_routes"] == 35
    assert "runtime_ready" in data
    assert "configuration_required" in data


def test_promotion_script_uses_hardened_verification_not_deep_domain_gate():
    text = (ROOT / "promote_site_intelligence_v4_35_3_1_to_github_and_render_macos.sh").read_text()
    assert "/public/deployment-verification" in text
    assert "/public/source-health-policy" in text
    assert "External source availability is intentionally excluded" in text
    assert "Deep gate:" not in text
    assert "all external" not in text.lower()


def test_promotion_script_does_not_probe_domain_state_endpoints():
    text = (ROOT / "promote_site_intelligence_v4_35_3_1_to_github_and_render_macos.sh").read_text()
    forbidden = (
        "/public/climate/state",
        "/public/biodiversity/state",
        "/public/mining-critical-materials/state",
        "/public/water-sanitation-infrastructure/state",
        "/public/exoplanet-habitability/state",
    )
    assert not any(token in text for token in forbidden)


def test_release_verification_requires_identity_runtime_routes_and_app_shell():
    text = (ROOT / "promote_site_intelligence_v4_35_3_1_to_github_and_render_macos.sh").read_text()
    for token in (
        "/public/release-gate",
        "/health",
        "/public/runtime-health",
        "/public/v4/readiness",
        "/public/authoritative-connectors/readiness",
        "/app/assets/app.js",
        "/app/assets/app.css",
    ):
        assert token in text


def test_source_policy_states_are_explicit():
    data = source_health_policy(settings())
    assert set(data["states"]) == {"configured", "configuration-required", "healthy", "degraded", "unavailable", "unknown"}


def test_first_five_authoritative_connectors_remain_nonblocking():
    data = source_health_policy(settings())
    ids = {row["id"] for row in data["sources"]}
    assert {
        "usgs-water-ogc-v0",
        "noaa-coastwatch-erddap",
        "nasa-exoplanet-tap",
        "unhcr-refugee-statistics-v1",
        "nasa-cmr-search",
    } <= ids
    assert all(row["release_blocking"] is False for row in data["sources"])
