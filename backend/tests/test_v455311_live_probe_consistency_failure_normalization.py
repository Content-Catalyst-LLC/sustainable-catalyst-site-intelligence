from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.api_reliability_v455311 import (
    api_contract_truth_manifest,
    build_capability_health,
    build_readiness,
    normalize_reliable_payload,
    probe_capability,
)
from app.config import Settings
from app.main import app
from app.route_registry_v4430 import capability_manifest, route_inventory
from app.version import APP_VERSION, RELEASE_NAME

ROOT = Path(__file__).resolve().parents[2]
client = TestClient(app)


def test_release_identity_and_inventory_unchanged_except_contract_revision():
    assert APP_VERSION == "4.55.3.2"
    assert RELEASE_NAME == "Standalone Functional Parity Recovery"
    manifest = capability_manifest(app.routes)
    assert manifest["registry_version"] == "2.6.0"
    assert manifest["route_count"] == 1518
    assert manifest["modularized_route_count"] == 209
    assert manifest["capability_count"] == 31
    assert manifest["unclassified_route_count"] == 0
    family = next(x for x in manifest["capabilities"] if x["capability_id"] == "api-reliability")
    assert family["route_count"] == 9
    assert family["modularized_route_count"] == 9
    assert family["maturity"] == "production"
    keys = [(method, row["path"]) for row in route_inventory(app.routes) for method in row["methods"]]
    assert len(keys) == len(set(keys))


def test_partial_live_is_transport_206_even_when_current_query_is_empty():
    payload = {"ok": True, "state": "partial-live", "records": [], "source_states": {"a": "live", "b": "unavailable"}}
    out, status = normalize_reliable_payload(payload, capability="humanitarian")
    assert status == 206
    assert out["ok"] is True
    assert out["data_state"] == "partial-no-records"


def test_science_country_context_no_longer_passes_unsupported_geography_kwarg(monkeypatch):
    import app.scientific_earth_systems_observatory as science
    seen = {}

    def fake(settings=None, **kwargs):
        seen.update(kwargs)
        return {"ok": True, "integration": {"state": "connected"}, "records": []}

    monkeypatch.setattr(science, "build_science_records", fake)
    out, status = probe_capability("science", Settings(), country="KEN", limit=5)
    assert status == 200
    assert "geography_code" not in seen
    assert seen["query"].startswith("Kenya")
    assert out["context_resolution"]["iso3"] == "KEN"
    assert out["context_resolution"]["iso2"] == "KE"
    assert out["context_resolution"]["context_mode"] == "metadata-query"


def test_unexpected_domain_exception_is_normalized_not_raised(monkeypatch):
    import app.scientific_earth_systems_observatory as science

    def boom(*args, **kwargs):
        raise TypeError("unexpected argument")

    monkeypatch.setattr(science, "build_science_records", boom)
    out, status = probe_capability("science", Settings(), country="KEN")
    assert status == 503
    assert out["ok"] is False
    assert out["dependency_state"] == "exception"
    assert out["data_state"] == "dependency-unavailable"
    assert out["failure"]["type"] == "TypeError"
    assert out["failure"]["normalized"] is True


def test_country_alias_retry_can_find_iso2_records(monkeypatch):
    import app.economics_markets_sustainability as economics
    attempted = []

    def fake(settings=None, *, geography_code="", limit=1, **kwargs):
        attempted.append(geography_code)
        rows = [{"id": "ke-row"}] if geography_code == "KE" else []
        return {"ok": True, "integration": {"state": "connected"}, "records": rows}

    monkeypatch.setattr(economics, "build_economic_records", fake)
    out, status = probe_capability("economics", Settings(), country="KEN", limit=5)
    assert status == 200
    assert out["record_count"] == 1
    assert attempted == ["KEN", "KE"]
    assert out["context_resolution"]["matched"] == "KE"


def test_dependency_error_does_not_retry_aliases_and_mask_failure(monkeypatch):
    import app.international_law_observatory as law
    attempted = []

    def fake(settings=None, *, country="", limit=1, **kwargs):
        attempted.append(country)
        return {"ok": True, "integration": {"state": "degraded", "message": "Core returned HTTP 500."}, "records": []}

    monkeypatch.setattr(law, "build_law_records", fake)
    out, status = probe_capability("law", Settings(), country="KEN")
    assert status == 503
    assert attempted == ["KEN"]
    assert out["truth_detail"] == "Core returned HTTP 500."


def test_capability_health_uses_exact_shared_probe_function(monkeypatch):
    import app.api_reliability_v455311 as reliability
    calls = []

    def fake(capability, settings=None, *, country="KEN", limit=1, query=""):
        calls.append((capability, country))
        state = "degraded" if capability == "law" else "connected"
        payload = {"ok": capability != "law", "integration": {"state": state}, "records": []}
        return normalize_reliable_payload(payload, capability=capability)

    monkeypatch.setattr(reliability, "probe_capability", fake)
    result = build_capability_health(Settings(platform_core_enabled=True, platform_core_url="http://core"), probe=True, country="KEN")
    assert {name for name, _ in calls} == {"economics", "law", "science", "humanitarian", "resources", "dossiers"}
    law = next(x for x in result["capabilities"] if x["capability"] == "law")
    assert law["http_status_if_requested"] == 503
    assert result["overall_state"] == "degraded"
    assert result["ok"] is False


def test_readiness_distinguishes_platform_ready_from_domain_degraded(monkeypatch):
    import app.api_reliability_v455311 as reliability
    monkeypatch.setattr(reliability, "_core_probe", lambda settings=None: {"ok": True, "state": "connected", "configured": True, "detail": "ok"})
    monkeypatch.setattr(reliability, "build_capability_health", lambda settings=None, probe=False, country="KEN": {
        "overall_state": "degraded", "canonical_probe_country": country,
        "usable_capabilities": 5, "partial_capabilities": 0, "unavailable_capabilities": 1,
        "capabilities": [{"capability": "law", "http_status_if_requested": 503}],
    })
    out = build_readiness(Settings(), country="KEN")
    assert out["platform_ready"] is True
    assert out["domain_ready"] is False
    assert out["ready"] is False
    assert out["state"] == "domain-degraded"


def test_readiness_route_returns_503_when_default_runtime_has_no_configured_core():
    response = client.get("/ready")
    assert response.status_code == 503
    data = response.json()
    assert data["ready"] is False
    assert data["state"] == "platform-unavailable"


def test_contract_manifest_requires_probe_parity_and_json_failures():
    manifest = api_contract_truth_manifest()
    assert manifest["version"] == "4.55.3.2"
    rules = " ".join(manifest["truth_rules"])
    assert "same" in manifest["semantics"]["capability_health"].lower()
    assert "JSON" in rules
    assert "ISO3/ISO2/name" in rules


def test_new_release_registry_is_truthful_and_release_bound():
    import json
    data = json.loads((ROOT / "backend/data/live_probe_consistency_registry_v455311.json").read_text())
    assert data["version"] == "4.55.3.2"
    assert data["contracts"]["readiness_requires_domain_operability"] is True
    assert data["guardrails"]["raw_unhandled_500_allowed_on_reliable_routes"] is False
    assert data["guardrails"]["new_provider_integrations"] is False


def test_standalone_views_use_reliable_domain_routes_and_live_probe():
    views = (ROOT / "web/assets/views.js").read_text()
    for route in [
        "/public/reliable/economics/records", "/public/reliable/law/records",
        "/public/reliable/science/records", "/public/reliable/humanitarian/records",
        "/public/reliable/resources/records", "/public/reliable/dossiers/country",
    ]:
        assert route in views
    assert 'probe:true' in views
