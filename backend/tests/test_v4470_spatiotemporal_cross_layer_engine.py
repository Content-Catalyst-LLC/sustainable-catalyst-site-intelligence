from __future__ import annotations

from collections import Counter
import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.route_registry_v4430 import capability_manifest, route_inventory
from app.spatiotemporal_query_v4470 import (
    ANALYSIS_RESULT_SCHEMA,
    JOIN_RESULT_SCHEMA,
    OPERATOR_REGISTRY_SCHEMA,
    QUERY_PLAN_SCHEMA,
    QUERY_RESULT_SCHEMA,
    QUERY_SCHEMA,
    compile_query_plan,
    cross_layer_analysis,
    cross_layer_join,
    execute_query,
)
from app.version import APP_VERSION, RELEASE_NAME

ROOT = Path(__file__).resolve().parents[2]
client = TestClient(app)


def _obj(layer_id: str, lon: float, lat: float, observed: str, value: float, object_id: str) -> dict:
    return {
        "object_id": object_id,
        "layer_id": layer_id,
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
        "observed_at": observed,
        "properties": {"metric": "value", "value": value, "status": "active"},
        "source": {"source_id": "test-source", "authority": "Test Authority", "record_id": object_id},
        "provenance": {"transformations": ["test-fixture-to-wgs84"]},
        "visibility": "public",
    }


def _objects() -> list[dict]:
    return [
        _obj("energy-power-systems", -90.20, 38.63, "2026-10-04T12:00:00Z", 125.5, "energy-a"),
        _obj("transportation-networks", -90.20, 38.63, "2026-10-04T12:00:00Z", 75.0, "transport-a"),
        _obj("live-events-hazards", -90.20, 38.63, "2026-10-04T12:00:00Z", 3.0, "event-a"),
        _obj("climate-baselines-extremes", -122.42, 37.77, "2026-09-01T00:00:00Z", 12.0, "climate-far"),
    ]


def test_release_identity() -> None:
    assert APP_VERSION == "4.55.3.2.2"
    assert RELEASE_NAME == "Browser API Transport & CORS Repair"


def test_engine_registry_and_operator_registry() -> None:
    manifest = client.get("/public/spatiotemporal/registry").json()
    assert manifest["ok"] is True
    assert manifest["version"] == APP_VERSION
    assert manifest["query_schema"] == QUERY_SCHEMA
    assert manifest["spatial_semantics"] == "bounding-box-first"
    operators = client.get("/public/spatiotemporal/operators").json()
    assert operators["schema"] == OPERATOR_REGISTRY_SCHEMA
    assert operators["version"] == APP_VERSION
    assert {row["operator"] for row in operators["spatial_predicates"]} == {"intersects", "within", "contains", "disjoint"}
    assert "overlaps" in {row["operator"] for row in operators["temporal_predicates"]}


def test_query_schema_is_explicit() -> None:
    payload = client.get("/public/spatiotemporal/query-schema").json()
    assert payload["schema"] == QUERY_SCHEMA
    assert payload["query_fields"]["spatial"]["bbox"].startswith("WGS84")
    assert payload["execution_request"]["objects"].startswith("1..")


def test_query_plan_is_deterministic_and_content_addressed() -> None:
    query = {
        "domains": ["energy"],
        "spatial": {"bbox": [-91, 38, -89, 39], "predicate": "intersects"},
        "temporal": {"start": "2026-10-04T00:00:00Z", "end": "2026-10-05T00:00:00Z", "predicate": "overlaps"},
        "properties": [{"path": "properties.value", "operator": "gte", "value": 100}],
    }
    a = compile_query_plan(query)
    b = compile_query_plan(query)
    assert a == b
    assert a["schema"] == QUERY_PLAN_SCHEMA
    assert a["plan_digest"].startswith("sha256:")
    assert "spatial-bbox-filter" in a["stages"]
    assert "temporal-interval-filter" in a["stages"]


def test_query_execution_filters_space_time_domain_and_property() -> None:
    result = execute_query({
        "objects": _objects(),
        "query": {
            "domains": ["energy", "transportation"],
            "spatial": {"bbox": [-90.5, 38.4, -89.8, 38.9]},
            "temporal": {"start": "2026-10-04T11:00:00Z", "end": "2026-10-04T13:00:00Z"},
            "properties": [{"path": "properties.value", "operator": "gte", "value": 70}],
        },
    })
    assert result["schema"] == QUERY_RESULT_SCHEMA
    assert result["count"] == 2
    assert [row["object_id"] for row in result["objects"]] == ["energy-a", "transport-a"]
    assert len(result["provenance"]["source_object_digests"]) == 2
    assert result["provenance"]["query_plan_digest"] == result["plan"]["plan_digest"]


def test_query_endpoint_and_invalid_bbox() -> None:
    response = client.post("/public/spatiotemporal/query/execute", json={"objects": _objects(), "query": {"layer_ids": ["live-events-hazards"]}})
    assert response.status_code == 200
    assert response.json()["count"] == 1
    bad = client.post("/public/spatiotemporal/query/plan", json={"spatial": {"bbox": [90, 10, -90, 20]}})
    assert bad.status_code == 400


def test_cross_layer_join_preserves_pair_provenance() -> None:
    result = cross_layer_join({
        "objects": _objects(),
        "left": {"layer_ids": ["energy-power-systems"]},
        "right": {"layer_ids": ["transportation-networks", "live-events-hazards"]},
        "spatial_predicate": "intersects",
        "temporal_predicate": "overlaps",
    })
    assert result["schema"] == JOIN_RESULT_SCHEMA
    assert result["pair_count"] == 2
    assert {pair["right_layer_id"] for pair in result["pairs"]} == {"transportation-networks", "live-events-hazards"}
    assert all(pair["left_content_digest"].startswith("sha256:") for pair in result["pairs"])
    assert result["spatial_semantics"] == "bounding-box-first"


def test_cross_layer_analysis_groups_and_computes_overlap_matrix() -> None:
    result = cross_layer_analysis({
        "objects": _objects(),
        "query": {"spatial": {"bbox": [-90.5, 38.4, -89.8, 38.9]}},
        "group_by": "domain",
        "metrics": [
            {"name": "records", "operator": "count"},
            {"name": "sum_value", "operator": "sum", "path": "properties.value"},
        ],
    })
    assert result["schema"] == ANALYSIS_RESULT_SCHEMA
    groups = {row["key"]: row for row in result["groups"]}
    assert groups["energy"]["metrics"]["records"] == 1
    assert groups["energy"]["metrics"]["sum_value"] == 125.5
    assert result["cross_layer_overlap"]
    assert result["analysis_digest"].startswith("sha256:")


def test_api_join_and_analysis_routes() -> None:
    join = client.post("/public/spatiotemporal/cross-layer/join", json={
        "objects": _objects(),
        "left": {"domains": ["energy"]},
        "right": {"domains": ["events"]},
    })
    assert join.status_code == 200
    assert join.json()["pair_count"] == 1
    analysis = client.post("/public/spatiotemporal/cross-layer/analyze", json={"objects": _objects(), "group_by": "layer_id"})
    assert analysis.status_code == 200
    assert analysis.json()["group_count"] == 4


def test_v4460_canonical_object_digest_is_preserved_as_source_lineage() -> None:
    normalized = client.post("/public/spatial-evidence/objects/normalize", json=_objects()[0]).json()["object"]
    original_digest = normalized["content_digest"]
    # Simulate a canonical object created under the preceding release: v4.47 accepts
    # the schema/digest as evidence rather than rewriting it before derived analysis.
    normalized["version"] = "4.46.0"
    result = execute_query({"objects": [normalized], "query": {"domains": ["energy"]}})
    assert result["provenance"]["source_object_digests"] == [original_digest]
    assert result["objects"][0]["version"] == "4.46.0"


def test_compatibility_preserves_v446_and_legacy_spatial_surfaces() -> None:
    payload = client.get("/public/spatiotemporal/compatibility").json()
    assert payload["v4_46_spatial_evidence"]["status"] == "preserved-and-consumed"
    assert payload["legacy_spatial_studio"]["status"] == "preserved"
    assert client.get("/public/spatial-evidence/registry").status_code == 200
    paths = {item["path"] for item in route_inventory(app.routes)}
    assert "/public/spatial" in paths


def test_capability_registry_has_spatiotemporal_family() -> None:
    manifest = capability_manifest(app.routes)
    assert manifest["registry_version"] == "2.6.2"
    assert manifest["unclassified_route_count"] == 0
    spatial = next(item for item in manifest["capabilities"] if item["capability_id"] == "spatiotemporal-analysis")
    assert spatial["route_count"] == 8
    assert spatial["modularized_route_count"] == 8


def test_standalone_navigation_promotes_spatiotemporal_analysis() -> None:
    navigation = client.get("/public/app/navigation").json()
    spatial = next(item for item in navigation["items"] if item["route"] == "spatial")
    assert spatial["capability_id"] == "spatial-relationship-graph"
    assert spatial["available"] is True
    bootstrap = client.get("/public/app/bootstrap").json()
    assert bootstrap["endpoints"]["spatial_evidence_registry"] == "/public/spatial-evidence/registry"
    assert bootstrap["endpoints"]["spatiotemporal_registry"] == "/public/spatiotemporal/registry"


def test_operator_registry_is_release_bound() -> None:
    payload = json.loads((ROOT / "backend/data/spatiotemporal_operator_registry_v4470.json").read_text(encoding="utf-8"))
    assert payload["version"] == APP_VERSION
    assert payload["schema"] == OPERATOR_REGISTRY_SCHEMA
    assert payload["spatial_semantics"] == "bounding-box-first"


def test_route_contract_remains_duplicate_free() -> None:
    pairs = []
    for item in route_inventory(app.routes):
        for method in item["methods"]:
            pairs.append((method, item["path"]))
    assert {pair: count for pair, count in Counter(pairs).items() if count > 1} == {}
