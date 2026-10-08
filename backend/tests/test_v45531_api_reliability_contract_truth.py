from pathlib import Path

from fastapi.testclient import TestClient

from app.api_reliability_v455311 import (
    api_contract_truth_manifest,
    build_capability_health,
    normalize_reliable_payload,
)
from app.config import Settings
from app.main import app
from app.route_registry_v4430 import capability_manifest, route_inventory
from app.version import APP_VERSION, RELEASE_NAME

ROOT = Path(__file__).resolve().parents[2]
client = TestClient(app)


def test_release_identity_and_route_inventory():
    assert APP_VERSION == "4.55.3.2.1"
    assert RELEASE_NAME == "Runtime Health Truth & Domain Context Repair"
    manifest = capability_manifest(app.routes)
    assert manifest["registry_version"] == "2.6.1"
    assert manifest["route_count"] == 1518
    assert manifest["modularized_route_count"] == 209
    assert manifest["capability_count"] == 31
    assert manifest["unclassified_route_count"] == 0
    family = next(item for item in manifest["capabilities"] if item["capability_id"] == "api-reliability")
    assert family["maturity"] == "production"
    assert family["route_count"] == 9
    assert family["modularized_route_count"] == 9
    keys = [(method, row["path"]) for row in route_inventory(app.routes) for method in row["methods"]]
    assert len(keys) == len(set(keys))


def test_legacy_main_capabilities_do_not_default_to_production():
    manifest = capability_manifest(app.routes)
    legacy = [item for item in manifest["capabilities"] if item["owner"] == "backend.app.main"]
    assert legacy
    assert all(item["maturity"] == "migration" for item in legacy)


def test_health_is_explicitly_liveness_only():
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["alive"] is True
    assert payload["scope"] == "process-only"
    assert payload["dependency_readiness_asserted"] is False
    assert payload["readiness_route"] == "/ready"


def test_ready_fails_truthfully_when_core_is_unconfigured():
    response = client.get("/ready")
    assert response.status_code == 503
    payload = response.json()
    assert payload["ok"] is False
    assert payload["ready"] is False
    assert payload["required_dependencies"]["platform_core"]["state"] in {"disabled", "core-unconfigured"}


def test_contract_truth_manifest_defines_transport_semantics():
    payload = api_contract_truth_manifest()
    assert payload["version"] == "4.55.3.2.1"
    assert payload["canonical_routes"]["readiness"] == "/ready"
    text = " ".join(payload["truth_rules"])
    assert "HTTP 200" in text
    assert "no-records" in text
    assert "ok=true" in text


def test_capability_health_configuration_is_not_live_proof():
    settings = Settings(platform_core_enabled=False, platform_core_url="")
    payload = build_capability_health(settings, probe=False)
    assert payload["probe"] is False
    assert payload["ok"] is False
    assert payload["overall_state"] == "not-ready"
    assert all(item["live_probe"] is False for item in payload["capabilities"])


def test_reliable_contract_distinguishes_empty_from_dependency_failure():
    connected_empty = {
        "ok": True,
        "integration": {"state": "connected", "message": "connected"},
        "records": [],
    }
    out, status = normalize_reliable_payload(connected_empty, capability="economics")
    assert status == 200
    assert out["ok"] is True
    assert out["data_state"] == "no-records"
    assert out["record_count"] == 0

    failed = {
        "ok": True,
        "integration": {"state": "degraded", "message": "Platform Core could not be reached."},
        "records": [],
    }
    out, status = normalize_reliable_payload(failed, capability="economics")
    assert status == 503
    assert out["ok"] is False
    assert out["data_state"] == "dependency-unavailable"
    assert out["legacy_ok"] is True


def test_reliable_contract_uses_206_for_usable_partial_records():
    payload = {
        "ok": True,
        "state": "degraded",
        "records": [{"id": "one"}],
    }
    out, status = normalize_reliable_payload(payload, capability="humanitarian")
    assert status == 206
    assert out["ok"] is True
    assert out["data_state"] == "partial-records"


def test_reliable_economics_route_does_not_claim_success_when_core_missing():
    response = client.get("/public/reliable/economics/records?geography_code=KEN&limit=2")
    assert response.status_code == 503
    payload = response.json()
    assert payload["ok"] is False
    assert payload["capability"] == "economics"
    assert payload["data_state"] == "dependency-unavailable"
    assert payload["dependency_state"] in {"disabled", "core-unconfigured", "degraded", "unavailable"}


def test_reliability_registry_is_release_bound_and_truthful():
    import json
    registry = json.loads((ROOT / "backend/data/api_reliability_contract_v45531.json").read_text())
    assert registry["version"] == "4.55.3.2.1"
    assert registry["guardrails"]["http_200_equated_with_domain_readiness"] is False
    assert registry["guardrails"]["dependency_failure_reported_ok_true_on_reliable_surface"] is False
    assert registry["guardrails"]["new_provider_integrations"] is False


def test_standalone_home_surfaces_reliability_state():
    views = (ROOT / "web/assets/views.js").read_text()
    assert "/public/capability-health" in views
    assert "API data readiness" in views
    assert "configuration state" in views


def test_wordpress_remains_launch_bridge_only():
    php = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text()
    assert "Version: 4.55.3.2.1" in php
    assert "const VERSION = '4.55.3.2.1';" in php
    assert "const WORDPRESS_ROLE = 'public-site-launch-bridge';" in php
