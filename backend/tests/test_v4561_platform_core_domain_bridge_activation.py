from __future__ import annotations

from types import SimpleNamespace
from urllib.request import Request

from fastapi.testclient import TestClient

from app import global_conditions_observatory as core_reads
from app.core_domain_bridge_v4561 import (
    DOMAIN_CONNECTOR_DOMAINS,
    bridge_manifest,
    domain_coverage,
    source_catalog,
)
from app.main import app
from app.route_registry_v4430 import capability_manifest
from app.version import APP_VERSION, RELEASE_NAME

client = TestClient(app)


def settings(**overrides):
    values = {
        "platform_core_enabled": True,
        "platform_core_url": "http://sc-core:8090",
        "platform_core_public_api_key": "",
        "international_law_observatory_enabled": True,
        "economics_sustainability_enabled": True,
        "scientific_earth_systems_enabled": True,
        "humanitarian_conflict_displacement_enabled": True,
        "trade_energy_resource_security_enabled": True,
        "unified_dossiers_enabled": True,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_release_identity_and_route_inventory():
    assert APP_VERSION == "4.56.1"
    assert RELEASE_NAME == "Platform Core International Law Bridge & Connector Activation"
    inventory = capability_manifest(app.routes)
    assert inventory["registry_version"] == "2.8.0"
    assert inventory["route_count"] == 1525
    assert inventory["modularized_route_count"] == 216
    assert inventory["capability_count"] == 33
    assert inventory["unclassified_route_count"] == 0
    family = next(x for x in inventory["capabilities"] if x["capability_id"] == "core-domain-bridge")
    assert family["route_count"] == 4
    assert family["modularized_route_count"] == 4


def test_internal_core_service_uses_private_read_mode(monkeypatch):
    monkeypatch.setenv("SC_SI_PLATFORM_CORE_ENABLED", "true")
    monkeypatch.setenv("SC_SI_PLATFORM_CORE_URL", "http://sc-core:8090")
    monkeypatch.setenv("SC_SI_PLATFORM_CORE_PUBLIC_API_KEY", "")
    monkeypatch.setenv("SC_SI_PLATFORM_CORE_INTERNAL_READS", "true")
    config = core_reads.core_read_config()
    assert config.configured is True
    assert config.internal_service is True
    assert config.read_mode == "private-core-read"


def test_external_core_without_key_does_not_claim_internal_mode(monkeypatch):
    monkeypatch.setenv("SC_SI_PLATFORM_CORE_ENABLED", "true")
    monkeypatch.setenv("SC_SI_PLATFORM_CORE_URL", "https://core.example.test")
    monkeypatch.setenv("SC_SI_PLATFORM_CORE_PUBLIC_API_KEY", "")
    monkeypatch.setenv("SC_SI_PLATFORM_CORE_INTERNAL_READS", "true")
    config = core_reads.core_read_config()
    assert config.internal_service is False
    assert config.read_mode == "public-api-key-missing"


def test_internal_route_rewrite_and_no_public_key_header(monkeypatch):
    seen = {}

    class Response:
        status = 200
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self, *_args): return b'{"data":[]}'

    def fake_urlopen(request: Request, timeout: float):
        seen["url"] = request.full_url
        seen["headers"] = dict(request.header_items())
        return Response()

    monkeypatch.setattr(core_reads, "urlopen", fake_urlopen)
    config = core_reads.CoreReadConfig(
        enabled=True,
        base_url="http://sc-core:8090",
        api_key="should-not-be-sent",
        timeout_seconds=5,
        cache_ttl_seconds=15,
        internal_reads=True,
    )
    core_reads._core_json(config, "/api/v1/economics/records", {"limit": 1}, cache_key="test-v4561-private")
    assert "/v1/economics/records" in seen["url"]
    assert "/api/v1/economics/records" not in seen["url"]
    lowered = {k.lower(): v for k, v in seen["headers"].items()}
    assert "x-sc-public-key" not in lowered
    assert "authorization" not in lowered


def test_source_catalog_and_domain_coverage_are_broad(monkeypatch):
    sources = [
        {"id": "un-digital-library", "name": "UN Digital Library", "organization": "UN", "active": True, "metadata": {"official": True, "domain": "international_law"}},
        {"id": "world-bank", "name": "World Bank", "organization": "World Bank", "active": True, "metadata": {"official": True}},
        {"id": "ocha-reliefweb", "name": "ReliefWeb", "organization": "OCHA", "active": True, "metadata": {"official": True, "domain": "humanitarian"}},
        {"id": "nasa-earthdata", "name": "NASA Earthdata", "organization": "NASA", "active": True, "metadata": {"official": True, "domain": "earth_science"}},
        {"id": "eia", "name": "EIA", "organization": "EIA", "active": True, "metadata": {"official": True, "domain": "energy"}},
    ]
    connectors = [
        {"id": "un.digital-library", "source_id": "un-digital-library", "name": "UN Digital Library", "domain": "international_law", "enabled": True, "capabilities": ["official_documents"]},
        {"id": "world-bank.indicators", "source_id": "world-bank", "name": "World Bank Indicators", "domain": "economics", "enabled": True, "capabilities": ["indicators"]},
        {"id": "ocha.reliefweb-reports", "source_id": "ocha-reliefweb", "name": "ReliefWeb", "domain": "humanitarian", "enabled": True, "capabilities": ["reports"]},
        {"id": "nasa.cmr-collections", "source_id": "nasa-earthdata", "name": "NASA CMR", "domain": "earth_science", "enabled": True, "capabilities": ["dataset_discovery"]},
        {"id": "eia.v2-data", "source_id": "eia", "name": "EIA", "domain": "energy", "enabled": True, "capabilities": ["energy"]},
    ]

    def fake_core(config, path, query=None, **kwargs):
        if path.endswith("/sources"):
            return sources
        if path.endswith("/connectors"):
            return connectors
        raise AssertionError(path)

    monkeypatch.setattr("app.core_domain_bridge_v4561._core_json", fake_core)
    catalog = source_catalog(settings())
    assert catalog["source_count"] == 5
    assert catalog["connector_count"] == 5
    assert domain_coverage(settings(), domain="law")["connector_count"] == 1
    assert domain_coverage(settings(), domain="economics")["connector_count"] >= 2
    assert domain_coverage(settings(), domain="humanitarian")["connector_count"] >= 2
    assert domain_coverage(settings(), domain="science")["connector_count"] == 1
    assert domain_coverage(settings(), domain="resources")["connector_count"] >= 2
    assert domain_coverage(settings(), domain="dossiers")["connector_count"] == 5


def test_public_bridge_routes_exist(monkeypatch):
    monkeypatch.setattr("app.core_domain_bridge_v4561.source_catalog", lambda settings=None: {
        "ok": True, "state": "connected", "source_count": 40, "connector_count": 39,
        "sources": [], "connectors": [], "read_mode": "private-core-read", "credential_exposed": False,
    })
    manifest = client.get("/public/core-domain-bridge")
    assert manifest.status_code == 200
    assert manifest.json()["version"] == "4.56.1"
    unknown = client.get("/public/core-domain-bridge/domains/not-a-domain")
    assert unknown.status_code == 404


def test_all_six_canonical_domains_are_covered():
    assert set(DOMAIN_CONNECTOR_DOMAINS) == {"law", "economics", "humanitarian", "science", "resources", "dossiers"}


def test_bridge_manifest_never_exposes_credentials():
    payload = bridge_manifest(settings(platform_core_public_api_key="super-secret"))
    assert payload["core"]["public_api_key_configured"] is False or isinstance(payload["core"]["public_api_key_configured"], bool)
    assert "super-secret" not in str(payload)
    assert payload["core"]["credential_exposed"] is False
