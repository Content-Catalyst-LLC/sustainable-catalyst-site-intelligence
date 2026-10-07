from __future__ import annotations

from collections import Counter
import json
from pathlib import Path

from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from app.main import app
from app.route_registry_v4430 import capability_manifest, route_inventory
from app.spatial_evidence_registry_v4460 import (
    EVIDENCE_OBJECT_SCHEMA,
    LAYER_REGISTRY_SCHEMA,
    normalize_evidence_object,
)
from app.version import APP_VERSION, RELEASE_NAME

ROOT = Path(__file__).resolve().parents[2]
client = TestClient(app)


def _sample() -> dict:
    return {
        "layer_id": "energy-power-systems",
        "geometry": {"type": "Point", "coordinates": [-90.1994, 38.6270]},
        "observed_at": "2026-10-04T12:00:00Z",
        "properties": {"metric": "capacity_mw", "value": 125.5},
        "source": {
            "source_id": "example-authoritative-source",
            "authority": "Example Authority",
            "record_id": "asset-42",
            "license": "source-defined",
            "retrieved_at": "2026-10-04T12:05:00Z",
        },
        "provenance": {"transformations": ["source-record-to-wgs84-point"]},
        "quality": {"spatial_resolution": "source-defined", "temporal_resolution": "source-defined"},
        "visibility": "public",
    }


def test_release_identity() -> None:
    assert APP_VERSION == "4.55.2"
    assert RELEASE_NAME == "Advanced Domain Intelligence Workspace Expansion"


def test_registry_manifest_is_cross_domain_and_versioned() -> None:
    payload = client.get("/public/spatial-evidence/registry").json()
    assert payload["ok"] is True
    assert payload["version"] == APP_VERSION
    assert payload["schema"] == LAYER_REGISTRY_SCHEMA
    assert payload["evidence_object_schema"] == EVIDENCE_OBJECT_SCHEMA
    assert payload["coordinate_reference_system"] == "EPSG:4326"
    assert payload["layer_count"] == 18
    assert payload["domain_count"] >= 15
    assert payload["legacy_compatibility"]["catalog_endpoint"] == "/public/spatial/layers"


def test_layer_registry_has_unique_ids_and_provenance_contracts() -> None:
    payload = client.get("/public/spatial-evidence/layers").json()
    ids = [item["layer_id"] for item in payload["layers"]]
    assert len(ids) == len(set(ids)) == 18
    for item in payload["layers"]:
        assert item["spatial_contract"]["crs"] == "EPSG:4326"
        assert item["evidence_contract"]["provenance_required"] is True
        assert item["evidence_contract"]["transformation_lineage_preserved"] is True
        assert item["source_contract"]["source_identity_preserved"] is True
        assert item["internal_endpoints"]["overview"].startswith(("/public/", "/v1/"))


def test_layer_filtering_and_detail() -> None:
    filtered = client.get("/public/spatial-evidence/layers", params={"capability_id": "infrastructure-energy"}).json()
    assert filtered["count"] >= 5
    assert all(item["capability_id"] == "infrastructure-energy" for item in filtered["layers"])
    detail = client.get("/public/spatial-evidence/layers/energy-power-systems")
    assert detail.status_code == 200
    assert detail.json()["layer"]["domain"] == "energy"
    missing = client.get("/public/spatial-evidence/layers/not-a-layer")
    assert missing.status_code == 404


def test_domains_are_queryable() -> None:
    payload = client.get("/public/spatial-evidence/domains").json()
    assert payload["count"] >= 15
    assert any(item["domain"] == "energy" and "energy-power-systems" in item["layer_ids"] for item in payload["domains"])
    assert any(item["domain"] == "climate" for item in payload["domains"])


def test_object_schema_contract_is_explicit() -> None:
    payload = client.get("/public/spatial-evidence/object-schema").json()
    assert payload["schema"] == EVIDENCE_OBJECT_SCHEMA
    assert payload["required"] == ["layer_id", "geometry", "source"]
    assert payload["coordinate_reference_system"] == "EPSG:4326"
    assert "content_digest" in payload["fields"]


def test_normalization_is_deterministic_and_provenance_preserving() -> None:
    a = normalize_evidence_object(_sample())
    b = normalize_evidence_object(_sample())
    assert a == b
    assert a["schema"] == EVIDENCE_OBJECT_SCHEMA
    assert a["domain"] == "energy"
    assert a["capability_id"] == "infrastructure-energy"
    assert a["bbox"] == [-90.1994, 38.627, -90.1994, 38.627]
    assert a["crs"] == "EPSG:4326"
    assert a["source"]["record_id"] == "asset-42"
    assert a["provenance"]["transformations"] == ["source-record-to-wgs84-point"]
    assert a["content_digest"].startswith("sha256:")


def test_normalize_endpoint_and_validation_endpoint() -> None:
    response = client.post("/public/spatial-evidence/objects/normalize", json=_sample())
    assert response.status_code == 200
    assert response.json()["object"]["layer_id"] == "energy-power-systems"
    valid = client.post("/public/spatial-evidence/objects/validate", json=_sample()).json()
    assert valid["valid"] is True
    bad = _sample()
    bad["geometry"] = {"type": "Point", "coordinates": [999, 999]}
    invalid = client.post("/public/spatial-evidence/objects/validate", json=bad).json()
    assert invalid["valid"] is False
    assert invalid["errors"]


def test_unknown_layer_and_domain_mismatch_are_rejected() -> None:
    unknown = _sample(); unknown["layer_id"] = "unknown-layer"
    assert client.post("/public/spatial-evidence/objects/normalize", json=unknown).status_code == 400
    mismatch = _sample(); mismatch["domain"] = "climate"
    assert client.post("/public/spatial-evidence/objects/normalize", json=mismatch).status_code == 400


def test_legacy_spatial_studio_is_preserved() -> None:
    contract = client.get("/public/spatial-evidence/compatibility").json()
    assert contract["legacy_spatial_studio"]["status"] == "preserved"
    assert contract["legacy_spatial_studio"]["layers"] == "/public/spatial/layers"
    paths = {route.path for route in app.routes if isinstance(route, APIRoute)}
    for path in ("/public/spatial", "/public/spatial/layers", "/public/spatial/methodology", "/public/spatial/evidence"):
        assert path in paths


def test_capability_registry_has_first_class_spatial_evidence_family() -> None:
    manifest = capability_manifest(app.routes)
    assert manifest["version"] == APP_VERSION
    assert manifest["registry_version"] == "2.3.0"
    assert manifest["unclassified_route_count"] == 0
    spatial = next(item for item in manifest["capabilities"] if item["capability_id"] == "spatial-evidence-registry")
    assert spatial["route_count"] == 8
    assert spatial["modularized_route_count"] == 8



def test_standalone_navigation_promotes_unified_spatial_registry() -> None:
    navigation = client.get("/public/app/navigation").json()
    spatial = next(item for item in navigation["items"] if item["route"] == "spatial")
    assert spatial["capability_id"] == "spatial-relationship-graph"
    assert spatial["available"] is True
    bootstrap = client.get("/public/app/bootstrap").json()
    assert bootstrap["endpoints"]["spatial_evidence_registry"] == "/public/spatial-evidence/registry"


def test_static_registry_is_release_bound() -> None:
    payload = json.loads((ROOT / "backend/data/spatial_layer_registry_v4460.json").read_text(encoding="utf-8"))
    assert payload["version"] == APP_VERSION
    assert payload["schema"] == LAYER_REGISTRY_SCHEMA
    assert payload["layer_count"] == len(payload["layers"]) == 18


def test_route_contract_remains_duplicate_free() -> None:
    pairs=[]
    for item in route_inventory(app.routes):
        for method in item["methods"]:
            pairs.append((method,item["path"]))
    assert {pair:count for pair,count in Counter(pairs).items() if count > 1} == {}
