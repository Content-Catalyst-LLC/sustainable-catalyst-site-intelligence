from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from .predictive_spatial_consumer_v4520 import _bbox, _bbox_intersects, _ensure_prediction
from .spatial_research_handoffs_v4510 import validate_research_object
from .version import APP_VERSION

SCENARIO_SCHEMA = "sc-site-intelligence-scenario-definition/1.0"
CHANGE_SCHEMA = "sc-site-intelligence-spatial-change/1.0"
EXPOSURE_SCHEMA = "sc-site-intelligence-spatial-exposure/1.0"
THRESHOLD_SCHEMA = "sc-site-intelligence-threshold-evaluation/1.0"
GRAPH_CONTEXT_SCHEMA = "sc-site-intelligence-scenario-graph-context/1.0"
LIVE_CONTEXT_SCHEMA = "sc-site-intelligence-scenario-live-context/1.0"
PREDICTION_CONTEXT_SCHEMA = "sc-site-intelligence-scenario-prediction-context/1.0"
RESEARCH_CONTEXT_SCHEMA = "sc-site-intelligence-scenario-research-context/1.0"
REGISTRY_SCHEMA = "sc-site-intelligence-scenario-exposure-change-registry/1.0"
REGISTRY_PATH = Path(__file__).resolve().parents[1] / "data" / "scenario_exposure_change_registry_v4530.json"


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str).encode("utf-8")


def _digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def _text(value: Any, limit: int = 1200) -> str:
    return " ".join(str(value or "").strip().split())[:limit]


def _num(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        n = float(value)
    except (TypeError, ValueError):
        return None
    return n if n == n and abs(n) != float("inf") else None


def _registry() -> dict[str, Any]:
    payload = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    if payload.get("schema") != REGISTRY_SCHEMA or payload.get("version") != APP_VERSION:
        raise ValueError("Scenario/exposure registry does not match runtime")
    return payload


def registry_manifest() -> dict[str, Any]:
    r = _registry()
    return {"ok": True, "version": APP_VERSION, **deepcopy(r)}


def schema_manifest() -> dict[str, Any]:
    return {
        "ok": True,
        "version": APP_VERSION,
        "schemas": {
            "scenario": SCENARIO_SCHEMA,
            "change": CHANGE_SCHEMA,
            "exposure": EXPOSURE_SCHEMA,
            "threshold": THRESHOLD_SCHEMA,
            "graph_context": GRAPH_CONTEXT_SCHEMA,
            "live_context": LIVE_CONTEXT_SCHEMA,
            "prediction_context": PREDICTION_CONTEXT_SCHEMA,
            "research_context": RESEARCH_CONTEXT_SCHEMA,
        },
        "boundaries": _registry()["boundaries"],
    }


def normalize_scenario(request: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(request, Mapping):
        raise ValueError("scenario request must be an object")
    scenario_id = _text(request.get("scenario_id") or request.get("id"), 200)
    if not scenario_id:
        raise ValueError("scenario_id is required")
    bbox = _bbox(request.get("bbox")) if request.get("bbox") is not None else None
    core = {
        "schema": SCENARIO_SCHEMA,
        "version": APP_VERSION,
        "scenario_id": scenario_id,
        "label": _text(request.get("label") or request.get("title"), 240) or scenario_id,
        "baseline_scenario_id": _text(request.get("baseline_scenario_id"), 200) or None,
        "description": _text(request.get("description"), 2500) or None,
        "bbox": bbox,
        "crs": "EPSG:4326" if bbox else None,
        "assumptions": deepcopy(request.get("assumptions") or []),
        "parameters": deepcopy(request.get("parameters") or {}),
        "prediction_digests": sorted({str(x) for x in request.get("prediction_digests", []) if str(x).startswith("sha256:")}),
        "evidence_digests": sorted({str(x) for x in request.get("evidence_digests", []) if str(x).startswith("sha256:")}),
        "event_digests": sorted({str(x) for x in request.get("event_digests", []) if str(x).startswith("sha256:")}),
        "graph_digests": sorted({str(x) for x in request.get("graph_digests", []) if str(x).startswith("sha256:")}),
        "status": _text(request.get("status"), 80).lower() or "defined",
        "model_conditional": bool(request.get("prediction_digests")),
        "observed_fact": False,
    }
    digest = _digest(core)
    return {"ok": True, "version": APP_VERSION, "scenario": {**core, "scenario_digest": digest}}


def _ensure_scenario(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping) and value.get("schema") == SCENARIO_SCHEMA:
        return deepcopy(dict(value))
    if isinstance(value, Mapping):
        return normalize_scenario(value)["scenario"]
    raise ValueError("scenario must be an object")


def compare_scenarios(request: Mapping[str, Any]) -> dict[str, Any]:
    rows = [_ensure_scenario(x) for x in request.get("scenarios", []) if isinstance(x, Mapping)]
    if len(rows) < 2:
        raise ValueError("at least two scenarios are required")
    core = {
        "schema": "sc-site-intelligence-scenario-comparison/1.0",
        "version": APP_VERSION,
        "scenario_count": len(rows),
        "scenarios": [{"scenario_id": x["scenario_id"], "scenario_digest": x["scenario_digest"], "assumption_count": len(x.get("assumptions") or []), "model_conditional": x.get("model_conditional", False)} for x in rows],
        "automatic_scenario_ranking": False,
        "preferred_scenario": None,
        "human_review_required": True,
    }
    d = _digest(core)
    return {"ok": True, "version": APP_VERSION, "comparison": {**core, "comparison_id": f"scenario-comparison:{d.split(':')[1][:24]}", "comparison_digest": d}}


def derive_change(request: Mapping[str, Any]) -> dict[str, Any]:
    baseline = request.get("baseline") if isinstance(request.get("baseline"), Mapping) else {}
    alternative = request.get("alternative") if isinstance(request.get("alternative"), Mapping) else {}
    keys = sorted(set(baseline) | set(alternative))
    changes = []
    for key in keys:
        a, b = _num(baseline.get(key)), _num(alternative.get(key))
        if a is not None and b is not None:
            changes.append({"metric": key, "baseline": a, "alternative": b, "delta": b-a, "percent_change": None if a == 0 else ((b-a)/abs(a))*100.0, "direction": "increase" if b>a else "decrease" if b<a else "unchanged"})
        else:
            changes.append({"metric": key, "baseline": deepcopy(baseline.get(key)), "alternative": deepcopy(alternative.get(key)), "delta": None, "percent_change": None, "direction": "changed" if baseline.get(key) != alternative.get(key) else "unchanged"})
    core = {"schema": CHANGE_SCHEMA, "version": APP_VERSION, "changes": changes, "uncertainty": deepcopy(request.get("uncertainty") or {}), "causal_attribution": False, "observed_change_confirmed": False}
    d = _digest(core)
    return {"ok": True, "version": APP_VERSION, "change": {**core, "change_id": f"spatial-change:{d.split(':')[1][:24]}", "change_digest": d}}


def evaluate_exposure(request: Mapping[str, Any]) -> dict[str, Any]:
    scenario = _ensure_scenario(request.get("scenario") or {"scenario_id": "analysis", "bbox": request.get("bbox")})
    scenario_bbox = scenario.get("bbox")
    if not scenario_bbox:
        raise ValueError("scenario bbox is required for exposure evaluation")
    assets = [deepcopy(x) for x in request.get("assets", []) if isinstance(x, Mapping)]
    exposed = []
    for asset in assets:
        if not isinstance(asset.get("bbox"), list):
            continue
        try:
            ab = _bbox(asset["bbox"])
        except ValueError:
            continue
        if ab and _bbox_intersects(scenario_bbox, ab):
            exposed.append({"asset_id": _text(asset.get("object_id") or asset.get("asset_id") or asset.get("id"), 240) or None, "layer_id": _text(asset.get("layer_id"), 200) or None, "content_digest": _text(asset.get("content_digest") or asset.get("digest"), 160) or _digest(asset), "spatial_relation": "bbox-intersects", "potentially_exposed": True, "impact_confirmed": False})
    by_layer: dict[str, int] = {}
    for row in exposed:
        by_layer[row.get("layer_id") or "unknown"] = by_layer.get(row.get("layer_id") or "unknown", 0) + 1
    core = {"schema": EXPOSURE_SCHEMA, "version": APP_VERSION, "scenario_id": scenario["scenario_id"], "scenario_digest": scenario["scenario_digest"], "asset_count": len(assets), "potential_exposure_count": len(exposed), "by_layer": by_layer, "exposures": exposed, "impact_confirmed": False, "causality_inferred": False}
    d = _digest(core)
    return {"ok": True, "version": APP_VERSION, "exposure": {**core, "exposure_id": f"spatial-exposure:{d.split(':')[1][:24]}", "exposure_digest": d}}


def evaluate_thresholds(request: Mapping[str, Any]) -> dict[str, Any]:
    metrics = request.get("metrics") if isinstance(request.get("metrics"), Mapping) else {}
    rules = [x for x in request.get("rules", []) if isinstance(x, Mapping)]
    ops = {"gt": lambda a,b:a>b, "gte":lambda a,b:a>=b, "lt":lambda a,b:a<b, "lte":lambda a,b:a<=b, "eq":lambda a,b:a==b}
    results = []
    for rule in rules:
        metric = _text(rule.get("metric"), 200)
        op = _text(rule.get("operator"), 20).lower() or "gte"
        value, threshold = _num(metrics.get(metric)), _num(rule.get("threshold"))
        crossed = bool(value is not None and threshold is not None and op in ops and ops[op](value, threshold))
        results.append({"rule_id": _text(rule.get("rule_id") or metric, 200), "metric": metric, "operator": op, "threshold": threshold, "value": value, "crossed": crossed, "interpretation": "rule-evaluation-only-not-impact-confirmation"})
    core = {"schema": THRESHOLD_SCHEMA, "version": APP_VERSION, "rule_count": len(results), "crossed_count": sum(1 for x in results if x["crossed"]), "results": results, "automatic_alert_escalation": False}
    d = _digest(core)
    return {"ok": True, "version": APP_VERSION, "thresholds": {**core, "threshold_digest": d}}


def graph_context(request: Mapping[str, Any]) -> dict[str, Any]:
    graph = request.get("graph") if isinstance(request.get("graph"), Mapping) else {}
    exposed_ids = {str(x) for x in request.get("exposed_node_ids", [])}
    edges = [x for x in graph.get("edges", []) if isinstance(x, Mapping)]
    adjacent = []
    for e in edges:
        s, t = str(e.get("source_node_id") or e.get("source") or ""), str(e.get("target_node_id") or e.get("target") or "")
        if s in exposed_ids or t in exposed_ids:
            adjacent.append({"source": s, "target": t, "relationship_type": e.get("relationship_type"), "derived_propagation": False})
    core = {"schema": GRAPH_CONTEXT_SCHEMA, "version": APP_VERSION, "exposed_node_ids": sorted(exposed_ids), "adjacent_edge_count": len(adjacent), "adjacent_edges": adjacent, "automatic_failure_propagation": False, "automatic_causality_inference": False}
    d = _digest(core)
    return {"ok": True, "version": APP_VERSION, "graph_context": {**core, "graph_context_digest": d}}


def live_context(request: Mapping[str, Any]) -> dict[str, Any]:
    bbox = _bbox(request.get("bbox"))
    events = [deepcopy(x) for x in request.get("events", []) if isinstance(x, Mapping)]
    matches = []
    for e in events:
        eb = e.get("bbox")
        if isinstance(eb, list):
            try: eb = _bbox(eb)
            except ValueError: eb = None
        if eb and _bbox_intersects(bbox, eb):
            matches.append({"event_id": e.get("event_id") or e.get("id"), "event_type": e.get("event_type"), "content_digest": e.get("content_digest") or e.get("event_digest") or _digest(e), "spatial_relation": "bbox-intersects", "impact_confirmed": False})
    core = {"schema": LIVE_CONTEXT_SCHEMA, "version": APP_VERSION, "event_count": len(events), "intersecting_event_count": len(matches), "events": matches, "automatic_event_impact_confirmation": False}
    d = _digest(core)
    return {"ok": True, "version": APP_VERSION, "live_context": {**core, "live_context_digest": d}}


def prediction_context(request: Mapping[str, Any]) -> dict[str, Any]:
    predictions = [_ensure_prediction(x) for x in request.get("predictions", []) if isinstance(x, Mapping)]
    rows = [{"prediction_id": x["prediction_id"], "prediction_digest": x["prediction_digest"], "scenario_id": x["scenario"]["scenario_id"], "target_layer_id": x["target_layer_id"], "model_ref": f"{x['model']['provider']}:{x['model']['model_id']}:{x['model']['model_version']}"} for x in predictions]
    core = {"schema": PREDICTION_CONTEXT_SCHEMA, "version": APP_VERSION, "prediction_count": len(rows), "predictions": rows, "prediction_is_observation": False, "automatic_model_selection": False}
    d = _digest(core)
    return {"ok": True, "version": APP_VERSION, "prediction_context": {**core, "prediction_context_digest": d}}


def research_context(request: Mapping[str, Any]) -> dict[str, Any]:
    research = request.get("research_object")
    if not isinstance(research, Mapping):
        raise ValueError("research_object is required")
    validation = validate_research_object(research)
    if not validation["valid"]:
        raise ValueError("invalid research_object: " + ", ".join(validation["errors"]))
    digests = sorted({str(x) for x in request.get("derived_digests", []) if str(x).startswith("sha256:")})
    core = {"schema": RESEARCH_CONTEXT_SCHEMA, "version": APP_VERSION, "research_object_id": research["research_object_id"], "research_digest": research["research_digest"], "derived_digests": digests, "research_object_mutated": False, "derived_context_only": True}
    d = _digest(core)
    return {"ok": True, "version": APP_VERSION, "research_context": {**core, "research_context_digest": d}}


def compatibility_manifest() -> dict[str, Any]:
    return {"ok": True, "version": APP_VERSION, "v4_46_evidence": "preserved", "v4_47_spatiotemporal": "consumed", "v4_48_graph": "context-only", "v4_49_live_events": "context-only", "v4_50_federation": "preserved", "v4_51_research": "consumed-without-mutation", "v4_52_predictive": "consumed", "wordpress_role": "public-site-launch-bridge"}
