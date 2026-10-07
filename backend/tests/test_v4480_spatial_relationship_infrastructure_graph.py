from __future__ import annotations

from collections import Counter
import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.route_registry_v4430 import capability_manifest, route_inventory
from app.spatial_relationship_graph_v4480 import (
    ANALYSIS_RESULT_SCHEMA,
    GRAPH_QUERY_RESULT_SCHEMA,
    GRAPH_SCHEMA,
    NEIGHBORHOOD_RESULT_SCHEMA,
    PATH_RESULT_SCHEMA,
    RELATIONSHIP_REGISTRY_SCHEMA,
    analyze_graph,
    build_graph,
    graph_neighborhood,
    graph_path,
    query_graph,
)
from app.version import APP_VERSION, RELEASE_NAME

ROOT = Path(__file__).resolve().parents[2]
client = TestClient(app)


def _obj(layer_id: str, object_id: str, lon: float, lat: float, observed: str = "2026-10-05T00:00:00Z") -> dict:
    return {
        "object_id": object_id,
        "layer_id": layer_id,
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
        "observed_at": observed,
        "properties": {"name": object_id, "status": "active"},
        "source": {"source_id": "test-source", "authority": "Test Authority", "record_id": object_id},
        "provenance": {"transformations": ["test-fixture-to-wgs84"]},
        "visibility": "public",
    }


def _objects() -> list[dict]:
    return [
        _obj("energy-power-systems", "power-a", -90.20, 38.63),
        _obj("transportation-networks", "transport-a", -90.20, 38.63),
        _obj("water-sanitation-infrastructure", "water-a", -90.21, 38.64),
        _obj("human-settlements-built-environment", "settlement-a", -90.22, 38.65),
        _obj("mining-critical-materials", "mine-a", -90.30, 38.70),
        _obj("live-events-hazards", "event-a", -90.20, 38.63),
    ]


def _relationships() -> list[dict]:
    return [
        {"source_node_id": "power-a", "target_node_id": "water-a", "relationship_type": "supplies", "properties": {"resource": "electricity"}},
        {"source_node_id": "water-a", "target_node_id": "settlement-a", "relationship_type": "serves"},
        {"source_node_id": "transport-a", "target_node_id": "settlement-a", "relationship_type": "connected-to"},
        {"source_node_id": "power-a", "target_node_id": "mine-a", "relationship_type": "depends-on"},
        {"source_node_id": "settlement-a", "target_node_id": "event-a", "relationship_type": "exposed-to"},
    ]


def _build() -> dict:
    return build_graph({"objects": _objects(), "relationships": _relationships(), "derive_spatial_relationships": True})


def test_release_identity() -> None:
    assert APP_VERSION == "4.55.3"
    assert RELEASE_NAME == "Standalone Web Application Foundation & WordPress Decoupling"


def test_registry_and_schema_endpoints() -> None:
    registry = client.get("/public/spatial-graph/registry")
    assert registry.status_code == 200
    payload = registry.json()
    assert payload["version"] == APP_VERSION
    assert payload["graph_schema"] == GRAPH_SCHEMA
    relationships = client.get("/public/spatial-graph/relationship-types").json()
    assert relationships["schema"] == RELATIONSHIP_REGISTRY_SCHEMA
    assert relationships["version"] == APP_VERSION
    assert relationships["relationship_count"] == 12
    assert {row["relationship_type"] for row in relationships["relationships"]} >= {"supplies", "depends-on", "connected-to", "spatial-intersects", "co-located-with"}
    schema = client.get("/public/spatial-graph/schema").json()
    assert schema["schema"] == GRAPH_SCHEMA
    assert schema["node"]["content_digest"].startswith("Canonical")


def test_graph_build_is_deterministic_and_content_addressed() -> None:
    a = _build()
    b = _build()
    assert a == b
    assert a["schema"] == GRAPH_SCHEMA
    assert a["graph_digest"].startswith("sha256:")
    assert a["graph_id"].startswith("sgr-")
    assert a["node_count"] == 6
    assert a["edge_count"] >= 8
    assert len(a["provenance"]["source_object_digests"]) == 6


def test_automatic_spatial_edges_use_v447_semantics_without_inventing_dependencies() -> None:
    graph = build_graph({"objects": _objects(), "derive_spatial_relationships": True})
    auto = [edge for edge in graph["edges"] if edge["provenance"]["derivation"] == "v4.48-automatic-spatial-relationship"]
    assert auto
    colocated = [edge for edge in auto if edge["relationship_type"] == "co-located-with"]
    assert len(colocated) == 3  # three pairings among power/transport/event at the same point
    assert all(edge["directed"] is False for edge in auto)
    assert not any(edge["relationship_type"] in {"depends-on", "supplies", "serves"} for edge in auto)
    assert all(edge["provenance"]["spatial_semantics"] == "bounding-box-first" for edge in auto)


def test_explicit_infrastructure_edges_preserve_direction_and_evidence_lineage() -> None:
    graph = _build()
    supplies = next(edge for edge in graph["edges"] if edge["relationship_type"] == "supplies")
    assert supplies["source_node_id"] == "power-a"
    assert supplies["target_node_id"] == "water-a"
    assert supplies["directed"] is True
    assert supplies["provenance"]["derivation"] == "explicit-assertion"
    assert len(supplies["source_object_digests"]) == 2
    assert supplies["edge_digest"].startswith("sha256:")


def test_unknown_relationship_and_missing_node_are_rejected() -> None:
    bad_type = client.post("/public/spatial-graph/build", json={"objects": _objects(), "relationships": [{"source_node_id": "power-a", "target_node_id": "water-a", "relationship_type": "magically-controls"}]})
    assert bad_type.status_code == 400
    bad_node = client.post("/public/spatial-graph/build", json={"objects": _objects(), "relationships": [{"source_node_id": "missing", "target_node_id": "water-a", "relationship_type": "supplies"}]})
    assert bad_node.status_code == 400


def test_graph_query_filters_domain_and_relationship_type() -> None:
    graph = _build()
    result = query_graph({"graph": graph, "query": {"capability_ids": ["infrastructure-energy"], "relationship_types": ["supplies", "depends-on", "connected-to"]}})
    assert result["schema"] == GRAPH_QUERY_RESULT_SCHEMA
    assert {node["node_id"] for node in result["nodes"]} == {"power-a", "transport-a", "water-a", "mine-a"}
    assert {edge["relationship_type"] for edge in result["edges"]} <= {"supplies", "depends-on", "connected-to"}
    assert result["query_digest"].startswith("sha256:")


def test_neighborhood_traverses_dependency_and_service_chain() -> None:
    graph = _build()
    result = graph_neighborhood({"graph": graph, "node_id": "power-a", "depth": 2, "direction": "out", "relationship_types": ["supplies", "serves", "depends-on"]})
    assert result["schema"] == NEIGHBORHOOD_RESULT_SCHEMA
    distances = {row["node_id"]: row["distance"] for row in result["nodes"]}
    assert distances["power-a"] == 0
    assert distances["water-a"] == 1
    assert distances["mine-a"] == 1
    assert distances["settlement-a"] == 2


def test_shortest_path_is_deterministic_and_respects_direction() -> None:
    graph = _build()
    result = graph_path({"graph": graph, "source_node_id": "power-a", "target_node_id": "settlement-a", "direction": "out", "relationship_types": ["supplies", "serves"]})
    assert result["schema"] == PATH_RESULT_SCHEMA
    assert result["found"] is True
    assert result["node_path"] == ["power-a", "water-a", "settlement-a"]
    assert result["hop_count"] == 2
    assert result["path_digest"].startswith("sha256:")
    reverse = graph_path({"graph": graph, "source_node_id": "settlement-a", "target_node_id": "power-a", "direction": "out", "relationship_types": ["supplies", "serves"]})
    assert reverse["found"] is False


def test_graph_analysis_reports_components_relationships_and_critical_nodes() -> None:
    graph = _build()
    result = analyze_graph({"graph": graph, "critical_limit": 3})
    assert result["schema"] == ANALYSIS_RESULT_SCHEMA
    assert result["component_count"] >= 1
    assert result["relationship_counts"]["supplies"] == 1
    assert result["relationship_counts"]["serves"] == 1
    assert result["infrastructure_edge_count"] >= 4
    assert result["cross_domain_edge_count"] >= 4
    assert len(result["critical_nodes"]) == 3
    assert result["analysis_digest"].startswith("sha256:")


def test_api_build_query_neighborhood_path_and_analysis() -> None:
    request = {"objects": _objects(), "relationships": _relationships()}
    graph = client.post("/public/spatial-graph/build", json=request)
    assert graph.status_code == 200
    payload = graph.json()
    assert payload["node_count"] == 6
    query = client.post("/public/spatial-graph/query", json={"graph": payload, "query": {"domains": ["energy", "transportation"]}})
    assert query.status_code == 200
    neighborhood = client.post("/public/spatial-graph/neighborhood", json={"graph": payload, "node_id": "power-a", "depth": 1})
    assert neighborhood.status_code == 200
    path = client.post("/public/spatial-graph/path", json={"graph": payload, "source_node_id": "power-a", "target_node_id": "water-a", "direction": "out", "relationship_types": ["supplies"]})
    assert path.status_code == 200 and path.json()["found"] is True
    analysis = client.post("/public/spatial-graph/analyze", json={"graph": payload})
    assert analysis.status_code == 200


def test_v446_digest_and_v447_contract_are_preserved() -> None:
    normalized = client.post("/public/spatial-evidence/objects/normalize", json=_objects()[0]).json()["object"]
    digest = normalized["content_digest"]
    normalized["version"] = "4.46.0"
    graph = build_graph({"objects": [normalized], "derive_spatial_relationships": False})
    assert graph["nodes"][0]["content_digest"] == digest
    assert graph["provenance"]["source_object_digests"] == [digest]
    assert client.get("/public/spatiotemporal/registry").status_code == 200


def test_compatibility_contract_preserves_prior_spatial_generations() -> None:
    payload = client.get("/public/spatial-graph/compatibility").json()
    assert payload["v4_46_spatial_evidence"]["status"] == "preserved-and-consumed"
    assert payload["v4_47_spatiotemporal_engine"]["status"] == "preserved-and-consumed"
    assert payload["v4_48"]["build"] == "/public/spatial-graph/build"


def test_capability_registry_has_graph_family_and_no_unclassified_routes() -> None:
    manifest = capability_manifest(app.routes)
    assert manifest["registry_version"] == "2.4.0"
    assert manifest["unclassified_route_count"] == 0
    graph = next(item for item in manifest["capabilities"] if item["capability_id"] == "spatial-relationship-graph")
    assert graph["route_count"] == 9
    assert graph["modularized_route_count"] == 9


def test_standalone_navigation_promotes_graph_without_losing_prior_registries() -> None:
    navigation = client.get("/public/app/navigation").json()
    spatial = next(item for item in navigation["items"] if item["route"] == "spatial")
    assert spatial["capability_id"] == "spatial-relationship-graph"
    assert spatial["available"] is True
    bootstrap = client.get("/public/app/bootstrap").json()
    assert bootstrap["endpoints"]["spatial_graph_registry"] == "/public/spatial-graph/registry"
    assert bootstrap["endpoints"]["spatiotemporal_registry"] == "/public/spatiotemporal/registry"
    assert bootstrap["endpoints"]["spatial_evidence_registry"] == "/public/spatial-evidence/registry"


def test_relationship_registry_is_release_bound() -> None:
    payload = json.loads((ROOT / "backend/data/spatial_relationship_registry_v4480.json").read_text(encoding="utf-8"))
    assert payload["version"] == APP_VERSION
    assert payload["schema"] == RELATIONSHIP_REGISTRY_SCHEMA
    assert payload["relationship_count"] == 12


def test_route_contract_remains_duplicate_free() -> None:
    pairs = []
    for item in route_inventory(app.routes):
        for method in item["methods"]:
            pairs.append((method, item["path"]))
    assert {pair: count for pair, count in Counter(pairs).items() if count > 1} == {}
