from __future__ import annotations

from collections import deque
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Mapping

from .reproducible_spatial_packages_v4540 import verify_package
from .version import APP_VERSION

TRANSFORMATION_SCHEMA = "sc-site-intelligence-spatial-transformation-event/1.0"
CHAIN_SCHEMA = "sc-site-intelligence-spatial-provenance-lineage-chain/1.0"
GRAPH_SCHEMA = "sc-site-intelligence-spatial-provenance-lineage-graph/1.0"
TRACE_SCHEMA = "sc-site-intelligence-spatial-provenance-lineage-trace/1.0"
VERIFICATION_SCHEMA = "sc-site-intelligence-spatial-provenance-lineage-verification/1.0"
PACKAGE_CONTEXT_SCHEMA = "sc-site-intelligence-spatial-lineage-package-context/1.0"
COMPARISON_SCHEMA = "sc-site-intelligence-spatial-lineage-comparison/1.0"
REGISTRY_SCHEMA = "sc-site-intelligence-spatial-provenance-lineage-registry/1.0"
CONTRACT_VERSION = "1.0.0"
REGISTRY_PATH = Path(__file__).resolve().parents[1] / "data" / "spatial_provenance_lineage_registry_v4550.json"

_SENSITIVE = re.compile(r"(?:api[_-]?key|password|secret|authorization|cookie|session[_-]?token|access[_-]?token|private[_-]?key)", re.I)


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str).encode("utf-8")


def _digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def _text(value: Any, limit: int = 1600) -> str:
    return " ".join(str(value or "").strip().split())[:limit]


def _registry() -> dict[str, Any]:
    payload = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    if payload.get("schema") != REGISTRY_SCHEMA or payload.get("version") != APP_VERSION:
        raise ValueError("Spatial provenance lineage registry does not match runtime")
    return payload


def _scan_sensitive(value: Any, path: str = "payload") -> list[str]:
    issues: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if _SENSITIVE.search(str(key)):
                issues.append(f"Sensitive field is not allowed: {child_path}")
            issues.extend(_scan_sensitive(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            issues.extend(_scan_sensitive(child, f"{path}[{index}]"))
    return issues


def _artifact_ref(value: Mapping[str, Any], fallback: str) -> dict[str, Any]:
    digest = _text(value.get("digest") or value.get("content_digest") or value.get("result_digest") or value.get("package_digest"), 100)
    if not digest.startswith("sha256:"):
        digest = _digest(value)
    return {
        "artifact_id": _text(value.get("artifact_id") or value.get("object_id") or value.get("id"), 240) or fallback,
        "digest": digest,
        "schema": _text(value.get("schema"), 240) or None,
        "role": _text(value.get("role"), 120) or None,
        "media_type": _text(value.get("media_type"), 120) or None,
    }


def registry_manifest() -> dict[str, Any]:
    r = _registry()
    return {
        "ok": True,
        "version": APP_VERSION,
        "contract_version": CONTRACT_VERSION,
        **deepcopy(r),
        "transformation_type_count": len(r["transformation_types"]),
    }


def schema_manifest() -> dict[str, Any]:
    return {
        "ok": True,
        "version": APP_VERSION,
        "schemas": {
            "transformation": TRANSFORMATION_SCHEMA,
            "chain": CHAIN_SCHEMA,
            "graph": GRAPH_SCHEMA,
            "trace": TRACE_SCHEMA,
            "verification": VERIFICATION_SCHEMA,
            "package_context": PACKAGE_CONTEXT_SCHEMA,
            "comparison": COMPARISON_SCHEMA,
        },
        "boundaries": deepcopy(_registry()["boundaries"]),
    }


def transformation_types_manifest() -> dict[str, Any]:
    r = _registry()
    return {
        "ok": True,
        "version": APP_VERSION,
        "transformation_types": deepcopy(r["transformation_types"]),
        "count": len(r["transformation_types"]),
    }


def record_transformation(request: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(request, Mapping):
        raise ValueError("transformation request must be an object")
    issues = _scan_sensitive(request)
    if issues:
        raise ValueError("; ".join(issues[:5]))
    type_id = _text(request.get("transformation_type"), 120)
    allowed = {x["type_id"] for x in _registry()["transformation_types"]}
    if type_id not in allowed:
        raise ValueError(f"unsupported transformation_type: {type_id}")
    raw_inputs = request.get("inputs") or []
    raw_outputs = request.get("outputs") or []
    if not isinstance(raw_inputs, list) or not isinstance(raw_outputs, list):
        raise ValueError("inputs and outputs must be arrays")
    inputs = [_artifact_ref(x, f"input-{i+1}") for i, x in enumerate(raw_inputs) if isinstance(x, Mapping)]
    outputs = [_artifact_ref(x, f"output-{i+1}") for i, x in enumerate(raw_outputs) if isinstance(x, Mapping)]
    if not outputs:
        raise ValueError("at least one output artifact is required")
    source_refs = deepcopy(request.get("source_refs") or [])
    if not inputs and not source_refs:
        raise ValueError("at least one input artifact or source_ref is required")
    operator = request.get("operator") if isinstance(request.get("operator"), Mapping) else {}
    actor = request.get("actor") if isinstance(request.get("actor"), Mapping) else {}
    core = {
        "schema": TRANSFORMATION_SCHEMA,
        "version": APP_VERSION,
        "transformation_type": type_id,
        "inputs": inputs,
        "outputs": outputs,
        "source_refs": source_refs,
        "operator": {
            "operator_id": _text(operator.get("operator_id") or request.get("operator_id"), 240) or type_id,
            "operator_version": _text(operator.get("operator_version"), 120) or None,
            "implementation": _text(operator.get("implementation"), 600) or None,
            "code_digest": _text(operator.get("code_digest"), 100) or None,
        },
        "parameters": deepcopy(request.get("parameters") or {}),
        "spatial_context": deepcopy(request.get("spatial_context") or {}),
        "temporal_context": deepcopy(request.get("temporal_context") or {}),
        "runtime": deepcopy(request.get("runtime") or {}),
        "execution_receipt_digest": _text(request.get("execution_receipt_digest"), 100) or None,
        "assumptions": deepcopy(request.get("assumptions") or []),
        "uncertainties": deepcopy(request.get("uncertainties") or []),
        "actor": {
            "actor_type": _text(actor.get("actor_type"), 80) or ("human" if type_id == "manual-annotation" else "system"),
            "actor_id": _text(actor.get("actor_id"), 240) or None,
            "human_asserted": bool(actor.get("human_asserted", type_id == "manual-annotation")),
        },
        "declared_at": _text(request.get("declared_at"), 120) or None,
        "boundaries": deepcopy(_registry()["boundaries"]),
    }
    event_digest = _digest(core)
    event = {
        **core,
        "event_id": _text(request.get("event_id"), 240) or f"spatial-lineage-event:{event_digest.split(':',1)[1][:24]}",
        "event_digest": event_digest,
    }
    return {"ok": True, "version": APP_VERSION, "transformation": event}


def validate_transformation(request: Mapping[str, Any]) -> dict[str, Any]:
    event = request.get("transformation") if isinstance(request, Mapping) else None
    if not isinstance(event, Mapping):
        raise ValueError("transformation is required")
    errors = _scan_sensitive(event)
    if event.get("schema") != TRANSFORMATION_SCHEMA:
        errors.append("transformation schema mismatch")
    if event.get("version") != APP_VERSION:
        errors.append("transformation version mismatch")
    if event.get("transformation_type") not in {x["type_id"] for x in _registry()["transformation_types"]}:
        errors.append("unknown transformation type")
    core = {k: deepcopy(v) for k, v in event.items() if k not in {"event_id", "event_digest"}}
    expected = _digest(core)
    if event.get("event_digest") != expected:
        errors.append("event digest mismatch")
    if not event.get("outputs"):
        errors.append("missing output artifacts")
    return {
        "ok": not errors,
        "version": APP_VERSION,
        "validation": {
            "valid": not errors,
            "errors": errors,
            "event_id": event.get("event_id"),
            "observed_event_digest": event.get("event_digest"),
            "expected_event_digest": expected,
            "automatic_repair": False,
        },
    }


def _chain_edges(events: list[Mapping[str, Any]]) -> list[dict[str, str]]:
    produced: dict[str, str] = {}
    for event in events:
        for output in event.get("outputs") or []:
            if isinstance(output, Mapping) and output.get("digest"):
                produced[str(output["digest"])] = str(event.get("event_id"))
    edges: list[dict[str, str]] = []
    for event in events:
        target = str(event.get("event_id"))
        for item in event.get("inputs") or []:
            if not isinstance(item, Mapping) or not item.get("digest"):
                continue
            source_event = produced.get(str(item["digest"]))
            if source_event and source_event != target:
                edges.append({"from_event": source_event, "to_event": target, "via_digest": str(item["digest"])})
    edges.sort(key=lambda x: (x["from_event"], x["to_event"], x["via_digest"]))
    return edges


def build_lineage_chain(request: Mapping[str, Any]) -> dict[str, Any]:
    rows = request.get("transformations") if isinstance(request, Mapping) else None
    if not isinstance(rows, list) or not rows:
        raise ValueError("transformations must be a non-empty array")
    events: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        event = deepcopy(dict(row)) if row.get("schema") == TRANSFORMATION_SCHEMA else record_transformation(row)["transformation"]
        validation = validate_transformation({"transformation": event})["validation"]
        if not validation["valid"]:
            raise ValueError(f"invalid transformation {event.get('event_id')}: {validation['errors']}")
        events.append(event)
    events.sort(key=lambda x: (str(x.get("event_id")), str(x.get("event_digest"))))
    edges = _chain_edges(events)
    artifact_digests = sorted({str(a.get("digest")) for e in events for group in ("inputs", "outputs") for a in (e.get(group) or []) if isinstance(a, Mapping) and a.get("digest")})
    core = {
        "schema": CHAIN_SCHEMA,
        "version": APP_VERSION,
        "events": events,
        "edges": edges,
        "event_count": len(events),
        "artifact_digests": artifact_digests,
        "source_event_digests": sorted(str(e["event_digest"]) for e in events),
        "boundaries": deepcopy(_registry()["boundaries"]),
    }
    chain_digest = _digest(core)
    chain = {
        **core,
        "chain_id": _text(request.get("chain_id"), 240) or f"spatial-lineage:{chain_digest.split(':',1)[1][:24]}",
        "chain_digest": chain_digest,
        "lineage_inferred": False,
        "automatic_repair": False,
    }
    return {"ok": True, "version": APP_VERSION, "chain": chain}


def lineage_graph(request: Mapping[str, Any]) -> dict[str, Any]:
    chain = request.get("chain") if isinstance(request, Mapping) else None
    if not isinstance(chain, Mapping):
        chain = build_lineage_chain(request)["chain"]
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, str]] = []
    for event in chain.get("events") or []:
        if not isinstance(event, Mapping):
            continue
        eid = str(event.get("event_id"))
        nodes[f"event:{eid}"] = {"node_id": f"event:{eid}", "node_type": "transformation", "label": event.get("transformation_type"), "digest": event.get("event_digest")}
        for item in event.get("inputs") or []:
            if isinstance(item, Mapping) and item.get("digest"):
                aid = f"artifact:{item['digest']}"
                nodes[aid] = {"node_id": aid, "node_type": "artifact", "artifact_id": item.get("artifact_id"), "digest": item.get("digest")}
                edges.append({"from": aid, "to": f"event:{eid}", "relation": "consumed-by"})
        for item in event.get("outputs") or []:
            if isinstance(item, Mapping) and item.get("digest"):
                aid = f"artifact:{item['digest']}"
                nodes[aid] = {"node_id": aid, "node_type": "artifact", "artifact_id": item.get("artifact_id"), "digest": item.get("digest")}
                edges.append({"from": f"event:{eid}", "to": aid, "relation": "produced"})
    node_rows = sorted(nodes.values(), key=lambda x: x["node_id"])
    edges.sort(key=lambda x: (x["from"], x["to"], x["relation"]))
    core = {"schema": GRAPH_SCHEMA, "version": APP_VERSION, "chain_id": chain.get("chain_id"), "chain_digest": chain.get("chain_digest"), "nodes": node_rows, "edges": edges}
    core["graph_digest"] = _digest(core)
    return {"ok": True, "version": APP_VERSION, "graph": core}


def trace_lineage(request: Mapping[str, Any]) -> dict[str, Any]:
    chain = request.get("chain") if isinstance(request, Mapping) else None
    if not isinstance(chain, Mapping):
        raise ValueError("chain is required")
    artifact_digest = _text(request.get("artifact_digest"), 100)
    if not artifact_digest:
        raise ValueError("artifact_digest is required")
    direction = _text(request.get("direction"), 40) or "both"
    if direction not in {"ancestors", "descendants", "both"}:
        raise ValueError("direction must be ancestors, descendants, or both")
    graph = lineage_graph({"chain": chain})["graph"]
    start = f"artifact:{artifact_digest}"
    if start not in {n["node_id"] for n in graph["nodes"]}:
        raise ValueError("artifact_digest not present in chain")
    forward: dict[str, list[str]] = {}
    reverse: dict[str, list[str]] = {}
    for edge in graph["edges"]:
        forward.setdefault(edge["from"], []).append(edge["to"])
        reverse.setdefault(edge["to"], []).append(edge["from"])
    def walk(adj: dict[str, list[str]]) -> set[str]:
        seen={start}; q=deque([start])
        while q:
            cur=q.popleft()
            for nxt in adj.get(cur, []):
                if nxt not in seen:
                    seen.add(nxt); q.append(nxt)
        seen.remove(start)
        return seen
    ids=set()
    if direction in {"descendants","both"}: ids |= walk(forward)
    if direction in {"ancestors","both"}: ids |= walk(reverse)
    selected = [n for n in graph["nodes"] if n["node_id"] in ids]
    core={"schema":TRACE_SCHEMA,"version":APP_VERSION,"chain_id":chain.get("chain_id"),"artifact_digest":artifact_digest,"direction":direction,"nodes":selected,"node_count":len(selected),"lineage_inferred":False}
    core["trace_digest"]=_digest(core)
    return {"ok":True,"version":APP_VERSION,"trace":core}


def verify_lineage_chain(request: Mapping[str, Any]) -> dict[str, Any]:
    chain = request.get("chain") if isinstance(request, Mapping) else None
    if not isinstance(chain, Mapping):
        raise ValueError("chain is required")
    errors: list[str] = _scan_sensitive(chain)
    if chain.get("schema") != CHAIN_SCHEMA: errors.append("chain schema mismatch")
    if chain.get("version") != APP_VERSION: errors.append("chain version mismatch")
    for event in chain.get("events") or []:
        if isinstance(event, Mapping):
            v=validate_transformation({"transformation":event})["validation"]
            if not v["valid"]: errors.append(f"invalid event {event.get('event_id')}")
    core = {k:deepcopy(v) for k,v in chain.items() if k not in {"chain_id","chain_digest","lineage_inferred","automatic_repair"}}
    expected=_digest(core)
    if chain.get("chain_digest") != expected: errors.append("chain digest mismatch")
    expected_edges=_chain_edges([x for x in chain.get("events") or [] if isinstance(x, Mapping)])
    if chain.get("edges") != expected_edges: errors.append("chain edge mismatch")
    event_ids=[str(x.get("event_id")) for x in chain.get("events") or [] if isinstance(x, Mapping)]
    indegree={eid:0 for eid in event_ids}; adj={eid:[] for eid in event_ids}
    for edge in expected_edges:
        a=edge["from_event"]; b=edge["to_event"]
        if a in adj and b in indegree: adj[a].append(b); indegree[b]+=1
    q=deque([eid for eid,d in indegree.items() if d==0]); visited=0
    while q:
        cur=q.popleft(); visited+=1
        for nxt in adj.get(cur,[]):
            indegree[nxt]-=1
            if indegree[nxt]==0: q.append(nxt)
    if visited != len(indegree): errors.append("lineage event cycle detected")
    result={"schema":VERIFICATION_SCHEMA,"version":APP_VERSION,"valid":not errors,"errors":errors,"chain_id":chain.get("chain_id"),"observed_chain_digest":chain.get("chain_digest"),"expected_chain_digest":expected,"event_count":len(event_ids),"automatic_execution":False,"automatic_repair":False}
    result["verification_digest"]=_digest(result)
    return {"ok":not errors,"version":APP_VERSION,"verification":result}


def package_context(request: Mapping[str, Any]) -> dict[str, Any]:
    package=request.get("package") if isinstance(request,Mapping) else None
    chain=request.get("chain") if isinstance(request,Mapping) else None
    if not isinstance(package,Mapping): raise ValueError("package is required")
    if not isinstance(chain,Mapping): raise ValueError("chain is required")
    pv=verify_package({"package":package})["verification"]
    lv=verify_lineage_chain({"chain":chain})["verification"]
    package_digests=set((package.get("manifest") or {}).get("source_digests") or [])
    chain_digests=set(chain.get("artifact_digests") or [])
    overlap=sorted(package_digests & chain_digests)
    core={"schema":PACKAGE_CONTEXT_SCHEMA,"version":APP_VERSION,"package_id":package.get("package_id"),"package_digest":package.get("package_digest"),"chain_id":chain.get("chain_id"),"chain_digest":chain.get("chain_digest"),"package_valid":pv["valid"],"lineage_valid":lv["valid"],"shared_artifact_digests":overlap,"shared_artifact_count":len(overlap),"package_mutated":False,"chain_mutated":False,"automatic_reproduction":False}
    core["context_digest"]=_digest(core)
    return {"ok":True,"version":APP_VERSION,"package_context":core}


def compare_lineages(request: Mapping[str, Any]) -> dict[str, Any]:
    chains=[x for x in (request.get("chains") or []) if isinstance(x,Mapping)] if isinstance(request,Mapping) else []
    if len(chains)<2: raise ValueError("at least two chains are required")
    rows=[]
    for chain in chains:
        v=verify_lineage_chain({"chain":chain})["verification"]
        rows.append({"chain_id":chain.get("chain_id"),"chain_digest":chain.get("chain_digest"),"event_count":chain.get("event_count",len(chain.get("events") or [])),"artifact_count":len(chain.get("artifact_digests") or []),"valid":v["valid"]})
    core={"schema":COMPARISON_SCHEMA,"version":APP_VERSION,"chain_count":len(rows),"chains":rows,"automatic_lineage_ranking":False,"preferred_chain":None,"automatic_merge":False,"human_review_required":True}
    core["comparison_digest"]=_digest(core)
    return {"ok":True,"version":APP_VERSION,"comparison":core}


def compatibility_manifest() -> dict[str, Any]:
    return {
        "ok": True,
        "version": APP_VERSION,
        "preserves": [
            "v4.46-spatial-evidence", "v4.47-spatiotemporal-analysis", "v4.48-spatial-relationship-graph",
            "v4.49-live-geospatial-fusion", "v4.50-global-source-federation", "v4.51-spatial-research-objects",
            "v4.52-predictive-spatial-intelligence", "v4.53-scenario-exposure-change", "v4.53-advanced-domain-workspaces",
            "v4.54-reproducible-spatial-intelligence-packages",
        ],
        "boundaries": deepcopy(_registry()["boundaries"]),
        "lineage_authority": "declared-and-content-addressed-transformations-only",
        "automatic_lineage_inference": False,
        "automatic_chain_repair": False,
        "automatic_execution": False,
    }
