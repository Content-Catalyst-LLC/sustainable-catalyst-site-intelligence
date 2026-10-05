from __future__ import annotations

from collections import Counter, deque
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

from .spatiotemporal_query_v4470 import (
    _bbox_intersects,
    _normalize_objects,
    _temporal_interval,
    _temporal_relation,
)
from .spatial_evidence_registry_v4460 import EVIDENCE_OBJECT_SCHEMA
from .version import APP_VERSION

RELATIONSHIP_REGISTRY_SCHEMA = "sc-site-intelligence-spatial-relationship-registry/1.0"
GRAPH_SCHEMA = "sc-site-intelligence-spatial-relationship-graph/1.0"
GRAPH_QUERY_RESULT_SCHEMA = "sc-site-intelligence-spatial-graph-query-result/1.0"
NEIGHBORHOOD_RESULT_SCHEMA = "sc-site-intelligence-spatial-graph-neighborhood/1.0"
PATH_RESULT_SCHEMA = "sc-site-intelligence-spatial-graph-path/1.0"
ANALYSIS_RESULT_SCHEMA = "sc-site-intelligence-spatial-graph-analysis/1.0"
GRAPH_CONTRACT_VERSION = "1.0.0"
RELATIONSHIP_REGISTRY_PATH = Path(__file__).resolve().parents[1] / "data" / "spatial_relationship_registry_v4480.json"
MAX_NODES = 5000
MAX_EDGES = 20000
MAX_DEPTH = 8


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def _relationship_registry() -> dict[str, Any]:
    payload = json.loads(RELATIONSHIP_REGISTRY_PATH.read_text(encoding="utf-8"))
    if payload.get("schema") != RELATIONSHIP_REGISTRY_SCHEMA:
        raise ValueError("Spatial relationship registry schema mismatch")
    if payload.get("version") != APP_VERSION:
        raise ValueError("Spatial relationship registry version does not match application version")
    if payload.get("relationship_count") != len(payload.get("relationships") or []):
        raise ValueError("Spatial relationship registry count mismatch")
    return payload


def _relationship_map() -> dict[str, dict[str, Any]]:
    return {item["relationship_type"]: item for item in _relationship_registry()["relationships"]}


def relationship_manifest() -> dict[str, Any]:
    return {"ok": True, **deepcopy(_relationship_registry())}


def graph_manifest() -> dict[str, Any]:
    registry = _relationship_registry()
    return {
        "ok": True,
        "version": APP_VERSION,
        "contract_version": GRAPH_CONTRACT_VERSION,
        "graph_schema": GRAPH_SCHEMA,
        "relationship_registry_schema": RELATIONSHIP_REGISTRY_SCHEMA,
        "evidence_object_schema": EVIDENCE_OBJECT_SCHEMA,
        "spatial_semantics": registry["spatial_semantics"],
        "limits": {"nodes": MAX_NODES, "edges": MAX_EDGES, "path_depth": MAX_DEPTH},
        "endpoints": {
            "schema": "/public/spatial-graph/schema",
            "relationship_types": "/public/spatial-graph/relationship-types",
            "build": "/public/spatial-graph/build",
            "query": "/public/spatial-graph/query",
            "neighborhood": "/public/spatial-graph/neighborhood",
            "path": "/public/spatial-graph/path",
            "analyze": "/public/spatial-graph/analyze",
            "compatibility": "/public/spatial-graph/compatibility",
        },
        "principles": registry["principles"],
    }


def graph_schema_contract() -> dict[str, Any]:
    return {
        "ok": True,
        "version": APP_VERSION,
        "schema": GRAPH_SCHEMA,
        "contract_version": GRAPH_CONTRACT_VERSION,
        "node": {
            "node_id": "Canonical evidence object_id.",
            "layer_id": "v4.46 registered spatial layer.",
            "domain": "v4.46 evidence domain.",
            "capability_id": "Site Intelligence capability family.",
            "content_digest": "Canonical source evidence digest.",
            "bbox": "WGS84 bounding box.",
            "observed_at": "Optional UTC observation instant.",
            "valid_time": "Optional validity interval.",
        },
        "edge": {
            "edge_id": "Deterministic content-addressed edge identifier.",
            "relationship_type": "Registered relationship type.",
            "source_node_id": "Graph source node.",
            "target_node_id": "Graph target node.",
            "directed": "Directionality declared by relationship registry.",
            "source_object_digests": "Evidence digests supporting the edge.",
            "edge_digest": "SHA-256 digest of canonical edge content.",
        },
        "build_request": {
            "objects": f"0..{MAX_NODES} canonical v4.46 evidence objects or normalizable raw evidence objects",
            "relationships": "Optional explicit infrastructure relationships.",
            "derive_spatial_relationships": True,
            "require_temporal_overlap_for_derived_edges": False,
        },
    }


def _node_from_object(obj: dict[str, Any]) -> dict[str, Any]:
    return {
        "node_id": obj["object_id"],
        "node_type": "spatial-evidence",
        "layer_id": obj["layer_id"],
        "domain": obj.get("domain"),
        "capability_id": obj.get("capability_id"),
        "bbox": deepcopy(obj.get("bbox")),
        "observed_at": obj.get("observed_at"),
        "valid_time": deepcopy(obj.get("valid_time")),
        "visibility": obj.get("visibility"),
        "source": deepcopy(obj.get("source")),
        "properties": deepcopy(obj.get("properties") or {}),
        "content_digest": obj["content_digest"],
    }


def _edge_basis(*, relationship_type: str, source: dict[str, Any], target: dict[str, Any], directed: bool, properties: dict[str, Any], provenance: dict[str, Any]) -> dict[str, Any]:
    if not directed and source["object_id"] > target["object_id"]:
        source, target = target, source
    return {
        "relationship_type": relationship_type,
        "source_node_id": source["object_id"],
        "target_node_id": target["object_id"],
        "directed": directed,
        "properties": deepcopy(properties),
        "provenance": deepcopy(provenance),
        "source_object_digests": sorted({source["content_digest"], target["content_digest"]}),
    }


def _edge_from_basis(basis: dict[str, Any]) -> dict[str, Any]:
    digest = _digest(basis)
    return {
        "edge_id": "sge-" + digest.split(":", 1)[1][:24],
        **deepcopy(basis),
        "edge_digest": digest,
    }


def _temporal_overlap(a: dict[str, Any], b: dict[str, Any]) -> bool | None:
    a_interval = _temporal_interval(a)
    b_interval = _temporal_interval(b)
    if a_interval[0] is None or b_interval[0] is None:
        return None
    return _temporal_relation(a_interval, b_interval, "overlaps")


def _explicit_edges(raw: Any, by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    if raw in (None, []):
        return []
    if not isinstance(raw, list):
        raise ValueError("relationships must be a list")
    registry = _relationship_map()
    edges: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            raise ValueError("each relationship must be an object")
        rel = str(item.get("relationship_type") or "").strip()
        spec = registry.get(rel)
        if spec is None:
            raise ValueError(f"Unknown relationship_type: {rel or 'missing'}")
        source_id = str(item.get("source_node_id") or item.get("source_object_id") or "").strip()
        target_id = str(item.get("target_node_id") or item.get("target_object_id") or "").strip()
        if source_id not in by_id or target_id not in by_id:
            raise ValueError(f"relationship endpoints must reference graph nodes: {source_id} -> {target_id}")
        if source_id == target_id:
            raise ValueError("self relationships are not supported")
        source = by_id[source_id]
        target = by_id[target_id]
        provenance = deepcopy(item.get("provenance") if isinstance(item.get("provenance"), dict) else {})
        provenance.setdefault("derivation", "explicit-assertion")
        provenance.setdefault("relationship_registry_version", _relationship_registry()["registry_version"])
        properties = deepcopy(item.get("properties") if isinstance(item.get("properties"), dict) else {})
        edges.append(_edge_from_basis(_edge_basis(
            relationship_type=rel,
            source=source,
            target=target,
            directed=bool(spec["directed"]),
            properties=properties,
            provenance=provenance,
        )))
    return edges


def _derived_edges(objects: list[dict[str, Any]], *, require_temporal_overlap: bool) -> list[dict[str, Any]]:
    edges: list[dict[str, Any]] = []
    for index, source in enumerate(objects):
        for target in objects[index + 1:]:
            if not _bbox_intersects(source["bbox"], target["bbox"]):
                continue
            temporal_overlap = _temporal_overlap(source, target)
            if require_temporal_overlap and temporal_overlap is not True:
                continue
            relationship_type = "co-located-with" if source["bbox"] == target["bbox"] else "spatial-intersects"
            provenance = {
                "derivation": "v4.48-automatic-spatial-relationship",
                "spatial_predicate": "intersects",
                "spatial_semantics": "bounding-box-first",
                "temporal_overlap": temporal_overlap,
                "source_engine": "v4.47-spatiotemporal-query-cross-layer-analysis",
            }
            edges.append(_edge_from_basis(_edge_basis(
                relationship_type=relationship_type,
                source=source,
                target=target,
                directed=False,
                properties={"temporal_overlap": temporal_overlap},
                provenance=provenance,
            )))
    return edges


def _dedupe_edges(edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key: dict[tuple[str, str, str, bool], dict[str, Any]] = {}
    for edge in edges:
        source = edge["source_node_id"]
        target = edge["target_node_id"]
        if not edge["directed"] and source > target:
            source, target = target, source
        key = (edge["relationship_type"], source, target, bool(edge["directed"]))
        # Explicit relationships take precedence over automatically derived duplicates.
        existing = by_key.get(key)
        if existing is None or existing.get("provenance", {}).get("derivation") != "explicit-assertion":
            by_key[key] = edge
    rows = list(by_key.values())
    rows.sort(key=lambda row: (row["relationship_type"], row["source_node_id"], row["target_node_id"], row["edge_id"]))
    if len(rows) > MAX_EDGES:
        raise ValueError(f"graph exceeds maximum of {MAX_EDGES} edges")
    return rows


def build_graph(request: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise ValueError("graph build request must be a JSON object")
    objects = _normalize_objects(request.get("objects") or [])
    if len(objects) > MAX_NODES:
        raise ValueError(f"graph exceeds maximum of {MAX_NODES} nodes")
    by_id = {obj["object_id"]: obj for obj in objects}
    if len(by_id) != len(objects):
        raise ValueError("graph object_id values must be unique")
    edges = _explicit_edges(request.get("relationships"), by_id)
    derive = bool(request.get("derive_spatial_relationships", True))
    require_temporal = bool(request.get("require_temporal_overlap_for_derived_edges", False))
    if derive:
        edges.extend(_derived_edges(objects, require_temporal_overlap=require_temporal))
    edges = _dedupe_edges(edges)
    nodes = [_node_from_object(obj) for obj in objects]
    nodes.sort(key=lambda row: row["node_id"])
    source_digests = sorted(obj["content_digest"] for obj in objects)
    basis = {
        "nodes": [{"node_id": n["node_id"], "content_digest": n["content_digest"]} for n in nodes],
        "edges": [edge["edge_digest"] for edge in edges],
        "derive_spatial_relationships": derive,
        "require_temporal_overlap_for_derived_edges": require_temporal,
    }
    graph_digest = _digest(basis)
    return {
        "ok": True,
        "schema": GRAPH_SCHEMA,
        "version": APP_VERSION,
        "graph_id": "sgr-" + graph_digest.split(":", 1)[1][:24],
        "graph_digest": graph_digest,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": nodes,
        "edges": edges,
        "provenance": {
            "source_object_digests": source_digests,
            "relationship_registry_schema": RELATIONSHIP_REGISTRY_SCHEMA,
            "relationship_registry_version": _relationship_registry()["registry_version"],
            "spatial_semantics": _relationship_registry()["spatial_semantics"],
            "derived_spatial_relationships": derive,
            "require_temporal_overlap_for_derived_edges": require_temporal,
        },
    }


def _resolve_graph(request: dict[str, Any]) -> dict[str, Any]:
    graph = request.get("graph")
    if isinstance(graph, dict) and graph.get("schema") == GRAPH_SCHEMA and isinstance(graph.get("nodes"), list) and isinstance(graph.get("edges"), list):
        return deepcopy(graph)
    build_request = request.get("build") if isinstance(request.get("build"), dict) else request
    return build_graph(build_request)


def _string_set(value: Any, field: str) -> set[str]:
    if value in (None, "", []):
        return set()
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list")
    return {str(item).strip() for item in value if str(item).strip()}


def query_graph(request: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise ValueError("graph query request must be a JSON object")
    graph = _resolve_graph(request)
    query = request.get("query") if isinstance(request.get("query"), dict) else {}
    node_ids = _string_set(query.get("node_ids"), "query.node_ids")
    layers = _string_set(query.get("layer_ids"), "query.layer_ids")
    domains = _string_set(query.get("domains"), "query.domains")
    capabilities = _string_set(query.get("capability_ids"), "query.capability_ids")
    relationship_types = _string_set(query.get("relationship_types"), "query.relationship_types")
    selected = []
    for node in graph["nodes"]:
        if node_ids and node["node_id"] not in node_ids:
            continue
        if layers and node.get("layer_id") not in layers:
            continue
        if domains and node.get("domain") not in domains:
            continue
        if capabilities and node.get("capability_id") not in capabilities:
            continue
        selected.append(node)
    selected_ids = {node["node_id"] for node in selected}
    edges = [edge for edge in graph["edges"] if edge["source_node_id"] in selected_ids and edge["target_node_id"] in selected_ids]
    if relationship_types:
        edges = [edge for edge in edges if edge["relationship_type"] in relationship_types]
    basis = {"graph_digest": graph["graph_digest"], "query": query, "node_ids": sorted(selected_ids), "edge_digests": [e["edge_digest"] for e in edges]}
    digest = _digest(basis)
    return {
        "ok": True,
        "schema": GRAPH_QUERY_RESULT_SCHEMA,
        "version": APP_VERSION,
        "query_id": "sgq-" + digest.split(":", 1)[1][:24],
        "query_digest": digest,
        "graph_id": graph["graph_id"],
        "graph_digest": graph["graph_digest"],
        "node_count": len(selected),
        "edge_count": len(edges),
        "nodes": selected,
        "edges": edges,
        "provenance": {"source_graph_digest": graph["graph_digest"], "source_object_digests": graph.get("provenance", {}).get("source_object_digests", [])},
    }


def _neighbors(graph: dict[str, Any], node_id: str, *, direction: str, relationship_types: set[str]) -> list[tuple[str, dict[str, Any]]]:
    rows: list[tuple[str, dict[str, Any]]] = []
    for edge in graph["edges"]:
        if relationship_types and edge["relationship_type"] not in relationship_types:
            continue
        source = edge["source_node_id"]
        target = edge["target_node_id"]
        if edge["directed"]:
            if direction in {"out", "both"} and source == node_id:
                rows.append((target, edge))
            if direction in {"in", "both"} and target == node_id:
                rows.append((source, edge))
        else:
            if source == node_id:
                rows.append((target, edge))
            elif target == node_id:
                rows.append((source, edge))
    rows.sort(key=lambda item: (item[0], item[1]["relationship_type"], item[1]["edge_id"]))
    return rows


def graph_neighborhood(request: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise ValueError("neighborhood request must be a JSON object")
    graph = _resolve_graph(request)
    node_id = str(request.get("node_id") or "").strip()
    nodes_by_id = {node["node_id"]: node for node in graph["nodes"]}
    if node_id not in nodes_by_id:
        raise ValueError(f"unknown graph node_id: {node_id or 'missing'}")
    depth = int(request.get("depth") or 1)
    if not 1 <= depth <= MAX_DEPTH:
        raise ValueError(f"depth must be between 1 and {MAX_DEPTH}")
    direction = str(request.get("direction") or "both").strip().lower()
    if direction not in {"in", "out", "both"}:
        raise ValueError("direction must be in, out, or both")
    relationship_types = _string_set(request.get("relationship_types"), "relationship_types")
    unknown = relationship_types - set(_relationship_map())
    if unknown:
        raise ValueError(f"unknown relationship types: {sorted(unknown)}")
    distance = {node_id: 0}
    queue = deque([node_id])
    used_edges: dict[str, dict[str, Any]] = {}
    while queue:
        current = queue.popleft()
        if distance[current] >= depth:
            continue
        for neighbor, edge in _neighbors(graph, current, direction=direction, relationship_types=relationship_types):
            used_edges[edge["edge_id"]] = edge
            if neighbor not in distance:
                distance[neighbor] = distance[current] + 1
                queue.append(neighbor)
    node_rows = [dict(nodes_by_id[nid], distance=distance[nid]) for nid in sorted(distance, key=lambda nid: (distance[nid], nid))]
    edge_rows = sorted(used_edges.values(), key=lambda edge: edge["edge_id"])
    basis = {"graph_digest": graph["graph_digest"], "node_id": node_id, "depth": depth, "direction": direction, "relationship_types": sorted(relationship_types), "nodes": [(row["node_id"], row["distance"]) for row in node_rows], "edges": [e["edge_digest"] for e in edge_rows]}
    digest = _digest(basis)
    return {
        "ok": True,
        "schema": NEIGHBORHOOD_RESULT_SCHEMA,
        "version": APP_VERSION,
        "neighborhood_id": "sgn-" + digest.split(":", 1)[1][:24],
        "neighborhood_digest": digest,
        "graph_id": graph["graph_id"],
        "root_node_id": node_id,
        "depth": depth,
        "direction": direction,
        "node_count": len(node_rows),
        "edge_count": len(edge_rows),
        "nodes": node_rows,
        "edges": edge_rows,
        "provenance": {"source_graph_digest": graph["graph_digest"]},
    }


def graph_path(request: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise ValueError("path request must be a JSON object")
    graph = _resolve_graph(request)
    source_id = str(request.get("source_node_id") or "").strip()
    target_id = str(request.get("target_node_id") or "").strip()
    node_ids = {node["node_id"] for node in graph["nodes"]}
    if source_id not in node_ids or target_id not in node_ids:
        raise ValueError("source_node_id and target_node_id must reference graph nodes")
    max_depth = int(request.get("max_depth") or MAX_DEPTH)
    if not 1 <= max_depth <= MAX_DEPTH:
        raise ValueError(f"max_depth must be between 1 and {MAX_DEPTH}")
    direction = str(request.get("direction") or "both").strip().lower()
    if direction not in {"in", "out", "both"}:
        raise ValueError("direction must be in, out, or both")
    relationship_types = _string_set(request.get("relationship_types"), "relationship_types")
    queue = deque([source_id])
    parent: dict[str, tuple[str, dict[str, Any]] | None] = {source_id: None}
    depth = {source_id: 0}
    while queue and target_id not in parent:
        current = queue.popleft()
        if depth[current] >= max_depth:
            continue
        for neighbor, edge in _neighbors(graph, current, direction=direction, relationship_types=relationship_types):
            if neighbor in parent:
                continue
            parent[neighbor] = (current, edge)
            depth[neighbor] = depth[current] + 1
            queue.append(neighbor)
            if neighbor == target_id:
                break
    found = target_id in parent
    node_path: list[str] = []
    edge_path: list[dict[str, Any]] = []
    if found:
        current = target_id
        node_path.append(current)
        while current != source_id:
            previous, edge = parent[current]  # type: ignore[misc]
            edge_path.append(edge)
            current = previous
            node_path.append(current)
        node_path.reverse()
        edge_path.reverse()
    basis = {"graph_digest": graph["graph_digest"], "source": source_id, "target": target_id, "max_depth": max_depth, "direction": direction, "relationship_types": sorted(relationship_types), "node_path": node_path, "edge_path": [edge["edge_digest"] for edge in edge_path]}
    digest = _digest(basis)
    return {
        "ok": True,
        "schema": PATH_RESULT_SCHEMA,
        "version": APP_VERSION,
        "path_id": "sgp-" + digest.split(":", 1)[1][:24],
        "path_digest": digest,
        "graph_id": graph["graph_id"],
        "found": found,
        "hop_count": len(edge_path),
        "node_path": node_path,
        "edges": edge_path,
        "provenance": {"source_graph_digest": graph["graph_digest"]},
    }


def _components(graph: dict[str, Any]) -> list[list[str]]:
    adjacency: dict[str, set[str]] = {node["node_id"]: set() for node in graph["nodes"]}
    for edge in graph["edges"]:
        a, b = edge["source_node_id"], edge["target_node_id"]
        adjacency.setdefault(a, set()).add(b)
        adjacency.setdefault(b, set()).add(a)
    seen: set[str] = set()
    components: list[list[str]] = []
    for node_id in sorted(adjacency):
        if node_id in seen:
            continue
        queue = deque([node_id]); seen.add(node_id); members = []
        while queue:
            current = queue.popleft(); members.append(current)
            for neighbor in sorted(adjacency[current]):
                if neighbor not in seen:
                    seen.add(neighbor); queue.append(neighbor)
        components.append(sorted(members))
    components.sort(key=lambda row: (-len(row), row))
    return components


def analyze_graph(request: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise ValueError("graph analysis request must be a JSON object")
    graph = _resolve_graph(request)
    in_degree = Counter({node["node_id"]: 0 for node in graph["nodes"]})
    out_degree = Counter({node["node_id"]: 0 for node in graph["nodes"]})
    undirected_degree = Counter({node["node_id"]: 0 for node in graph["nodes"]})
    relation_counts = Counter()
    for edge in graph["edges"]:
        relation_counts[edge["relationship_type"]] += 1
        source, target = edge["source_node_id"], edge["target_node_id"]
        if edge["directed"]:
            out_degree[source] += 1; in_degree[target] += 1
        else:
            undirected_degree[source] += 1; undirected_degree[target] += 1
    node_rows = []
    node_map = {node["node_id"]: node for node in graph["nodes"]}
    for node_id in sorted(node_map):
        total = in_degree[node_id] + out_degree[node_id] + undirected_degree[node_id]
        node_rows.append({
            "node_id": node_id,
            "layer_id": node_map[node_id].get("layer_id"),
            "domain": node_map[node_id].get("domain"),
            "capability_id": node_map[node_id].get("capability_id"),
            "in_degree": in_degree[node_id],
            "out_degree": out_degree[node_id],
            "undirected_degree": undirected_degree[node_id],
            "total_degree": total,
        })
    critical_limit = int(request.get("critical_limit") or 10)
    if not 1 <= critical_limit <= 100:
        raise ValueError("critical_limit must be between 1 and 100")
    critical = sorted(node_rows, key=lambda row: (-row["total_degree"], row["node_id"]))[:critical_limit]
    components = _components(graph)
    cross_domain_edges = 0
    infrastructure_edges = 0
    infrastructure_domains = {"energy", "transportation", "water-infrastructure", "connectivity", "settlements", "mining"}
    for edge in graph["edges"]:
        left = node_map[edge["source_node_id"]]
        right = node_map[edge["target_node_id"]]
        if left.get("domain") != right.get("domain"):
            cross_domain_edges += 1
        if left.get("domain") in infrastructure_domains or right.get("domain") in infrastructure_domains or left.get("capability_id") == "infrastructure-energy" or right.get("capability_id") == "infrastructure-energy":
            infrastructure_edges += 1
    basis = {
        "graph_digest": graph["graph_digest"],
        "relation_counts": dict(sorted(relation_counts.items())),
        "components": components,
        "critical": critical,
        "cross_domain_edges": cross_domain_edges,
        "infrastructure_edges": infrastructure_edges,
    }
    digest = _digest(basis)
    return {
        "ok": True,
        "schema": ANALYSIS_RESULT_SCHEMA,
        "version": APP_VERSION,
        "analysis_id": "sga-" + digest.split(":", 1)[1][:24],
        "analysis_digest": digest,
        "graph_id": graph["graph_id"],
        "graph_digest": graph["graph_digest"],
        "node_count": graph["node_count"],
        "edge_count": graph["edge_count"],
        "component_count": len(components),
        "components": [{"component_id": f"component-{index+1}", "node_count": len(nodes), "node_ids": nodes} for index, nodes in enumerate(components)],
        "relationship_counts": dict(sorted(relation_counts.items())),
        "cross_domain_edge_count": cross_domain_edges,
        "infrastructure_edge_count": infrastructure_edges,
        "critical_nodes": critical,
        "node_metrics": node_rows,
        "provenance": {"source_graph_digest": graph["graph_digest"], "source_object_digests": graph.get("provenance", {}).get("source_object_digests", [])},
    }


def compatibility_contract() -> dict[str, Any]:
    return {
        "ok": True,
        "version": APP_VERSION,
        "contract_version": GRAPH_CONTRACT_VERSION,
        "v4_46_spatial_evidence": {
            "status": "preserved-and-consumed",
            "registry": "/public/spatial-evidence/registry",
            "object_schema": EVIDENCE_OBJECT_SCHEMA,
        },
        "v4_47_spatiotemporal_engine": {
            "status": "preserved-and-consumed",
            "registry": "/public/spatiotemporal/registry",
            "query": "/public/spatiotemporal/query/execute",
            "join": "/public/spatiotemporal/cross-layer/join",
        },
        "v4_48": {
            "registry": "/public/spatial-graph/registry",
            "relationship_types": "/public/spatial-graph/relationship-types",
            "build": "/public/spatial-graph/build",
            "query": "/public/spatial-graph/query",
            "neighborhood": "/public/spatial-graph/neighborhood",
            "path": "/public/spatial-graph/path",
            "analyze": "/public/spatial-graph/analyze",
        },
        "migration_rule": "v4.48 builds deterministic relationship graphs over v4.46 evidence and v4.47 spatial/temporal semantics without mutating source evidence or removing prior APIs.",
    }
