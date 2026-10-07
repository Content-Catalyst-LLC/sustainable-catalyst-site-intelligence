from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Any, Mapping

from .spatial_evidence_registry_v4460 import load_layer_registry
from .spatial_research_handoffs_v4510 import validate_research_object
from .version import APP_VERSION

PREDICTIVE_OBJECT_SCHEMA = "sc-site-intelligence-predictive-spatial-intelligence/1.0"
MODEL_BINDING_SCHEMA = "sc-site-intelligence-predictive-model-binding/1.0"
COMPARISON_SCHEMA = "sc-site-intelligence-predictive-spatial-comparison/1.0"
SCENARIO_SCHEMA = "sc-site-intelligence-predictive-spatial-scenario/1.0"
CALIBRATION_CONTEXT_SCHEMA = "sc-site-intelligence-predictive-calibration-context/1.0"
RESEARCH_CONTEXT_SCHEMA = "sc-site-intelligence-predictive-spatial-research-context/1.0"
REGISTRY_SCHEMA = "sc-site-intelligence-predictive-spatial-consumer-registry/1.0"
CONTRACT_VERSION = "1.0.0"
REGISTRY_PATH = Path(__file__).resolve().parents[1] / "data" / "predictive_spatial_consumer_registry_v4520.json"

_SENSITIVE = re.compile(r"(?:api[_-]?key|password|secret|authorization|cookie|session[_-]?token|access[_-]?token|private[_-]?key)", re.I)


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str).encode("utf-8")


def _digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def _text(value: Any, limit: int = 1200) -> str:
    return " ".join(str(value or "").strip().split())[:limit]


def _list(value: Any, limit: int = 500) -> list[Any]:
    return deepcopy(value[:limit]) if isinstance(value, list) else []


def _number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        result = float(value)
        return result if math.isfinite(result) else None
    return None


def _iso(value: Any) -> str | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        try:
            dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(f"Invalid ISO-8601 datetime: {value}") from exc
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


def _dt(value: Any) -> datetime | None:
    text = _iso(value)
    return datetime.fromisoformat(text) if text else None


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


def _registry() -> dict[str, Any]:
    payload = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    if payload.get("schema") != REGISTRY_SCHEMA:
        raise ValueError("Predictive spatial consumer registry schema mismatch")
    if payload.get("version") != APP_VERSION:
        raise ValueError("Predictive spatial consumer registry version does not match application version")
    return payload


def _layer_map() -> dict[str, dict[str, Any]]:
    return {row["layer_id"]: row for row in load_layer_registry()["layers"]}


def _bbox(value: Any) -> list[float] | None:
    if value in (None, []):
        return None
    if not isinstance(value, list) or len(value) != 4:
        raise ValueError("bbox must be [west,south,east,north]")
    vals = [_number(item) for item in value]
    if any(item is None for item in vals):
        raise ValueError("bbox coordinates must be finite numbers")
    west, south, east, north = [float(item) for item in vals]
    if not (-180 <= west <= 180 and -180 <= east <= 180 and -90 <= south <= 90 and -90 <= north <= 90):
        raise ValueError("bbox must use WGS84 longitude/latitude bounds")
    if west > east or south > north:
        raise ValueError("bbox west/south must not exceed east/north")
    return [west, south, east, north]


def _walk_positions(value: Any):
    if isinstance(value, (list, tuple)):
        if len(value) >= 2 and all(_number(v) is not None for v in value[:2]):
            lon, lat = float(value[0]), float(value[1])
            if not -180 <= lon <= 180 or not -90 <= lat <= 90:
                raise ValueError("geometry must use WGS84 coordinates")
            yield lon, lat
        else:
            for item in value:
                yield from _walk_positions(item)


def _geometry_bbox(geometry: Any) -> tuple[dict[str, Any] | None, list[float] | None]:
    if geometry in (None, {}):
        return None, None
    if not isinstance(geometry, Mapping):
        raise ValueError("geometry must be GeoJSON or null")
    result = deepcopy(dict(geometry))
    kind = _text(result.get("type"), 80)
    if kind == "GeometryCollection":
        positions: list[tuple[float, float]] = []
        for child in result.get("geometries") or []:
            _, child_bbox = _geometry_bbox(child)
            if child_bbox:
                positions.extend([(child_bbox[0], child_bbox[1]), (child_bbox[2], child_bbox[3])])
    else:
        positions = list(_walk_positions(result.get("coordinates")))
    if not positions:
        raise ValueError("geometry contains no valid WGS84 positions")
    lons = [p[0] for p in positions]
    lats = [p[1] for p in positions]
    return result, [min(lons), min(lats), max(lons), max(lats)]


def _bbox_intersects(a: list[float], b: list[float]) -> bool:
    return not (a[2] < b[0] or a[0] > b[2] or a[3] < b[1] or a[1] > b[3])


def _normalize_model(value: Any) -> dict[str, Any]:
    source = value if isinstance(value, Mapping) else {}
    model_id = _text(source.get("model_id") or source.get("id"), 240)
    model_version = _text(source.get("model_version") or source.get("version"), 120)
    provider = _text(source.get("provider") or source.get("provider_id"), 160)
    if not model_id or not model_version or not provider:
        raise ValueError("model.model_id, model.model_version, and model.provider are required")
    digest = _text(source.get("model_digest") or source.get("artifact_digest") or source.get("fingerprint"), 160) or None
    if digest and not digest.startswith("sha256:"):
        raise ValueError("model digest must use sha256: prefix")
    return {
        "model_id": model_id,
        "model_version": model_version,
        "provider": provider,
        "model_type": _text(source.get("model_type"), 120) or None,
        "model_digest": digest,
        "execution_receipt_digest": _text(source.get("execution_receipt_digest"), 160) or None,
        "intended_use": _text(source.get("intended_use"), 1500) or None,
        "limitations": _text(source.get("limitations"), 2500) or None,
    }


def _normalize_values(value: Any) -> list[dict[str, Any]]:
    rows = _list(value, 5000)
    normalized: list[dict[str, Any]] = []
    for index, raw in enumerate(rows):
        if not isinstance(raw, Mapping):
            raise ValueError("prediction values must be objects")
        point: dict[str, Any] = {
            "period": _text(raw.get("period") or raw.get("time") or raw.get("valid_at"), 160) or str(index),
            "valid_at": _iso(raw.get("valid_at") or raw.get("time")),
            "value": _number(raw.get("value")),
            "probability": _number(raw.get("probability")),
            "lower": _number(raw.get("lower")),
            "upper": _number(raw.get("upper")),
            "unit": _text(raw.get("unit"), 80) or None,
            "category": _text(raw.get("category"), 160) or None,
            "properties": deepcopy(raw.get("properties")) if isinstance(raw.get("properties"), Mapping) else {},
        }
        if point["probability"] is not None and not 0 <= point["probability"] <= 1:
            raise ValueError("probability must be between 0 and 1")
        if (point["lower"] is None) != (point["upper"] is None):
            raise ValueError("prediction intervals require both lower and upper")
        if point["lower"] is not None and point["upper"] is not None and point["lower"] > point["upper"]:
            raise ValueError("prediction lower interval cannot exceed upper")
        if point["value"] is None and point["probability"] is None and point["category"] is None:
            raise ValueError("each prediction value requires value, probability, or category")
        normalized.append(point)
    if not normalized:
        raise ValueError("values must contain at least one prediction point")
    return normalized


def registry_manifest() -> dict[str, Any]:
    registry = _registry()
    return {
        "ok": True,
        "version": APP_VERSION,
        "contract_version": CONTRACT_VERSION,
        "schema": REGISTRY_SCHEMA,
        "predictive_object_schema": PREDICTIVE_OBJECT_SCHEMA,
        "provider_count": len(registry["providers"]),
        "providers": deepcopy(registry["providers"]),
        "boundaries": deepcopy(registry["boundaries"]),
        "endpoints": deepcopy(registry["endpoints"]),
    }


def schema_manifest() -> dict[str, Any]:
    return {
        "ok": True,
        "version": APP_VERSION,
        "schema": PREDICTIVE_OBJECT_SCHEMA,
        "required": ["target_layer_id", "model", "issued_at", "valid_time", "values"],
        "spatial": {"crs": "EPSG:4326", "geometry_or_bbox_required": True},
        "prediction_semantics": "model-conditional-derived-information-not-observation",
        "probability_semantics": "probability-is-not-truth",
        "model_authority": {"training": False, "retraining": False, "automatic_selection": False},
        "integrity": {"algorithm": "sha256", "content_addressed": True},
    }


def provider_manifest() -> dict[str, Any]:
    registry = _registry()
    return {"ok": True, "version": APP_VERSION, "count": len(registry["providers"]), "providers": deepcopy(registry["providers"])}


def normalize_prediction(request: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(request, Mapping):
        raise ValueError("Predictive spatial request must be an object")
    issues = _scan_sensitive(request)
    if issues:
        raise ValueError("; ".join(issues[:5]))
    target_layer_id = _text(request.get("target_layer_id") or request.get("layer_id"), 200)
    layer = _layer_map().get(target_layer_id)
    if layer is None:
        raise ValueError(f"Unknown target_layer_id: {target_layer_id or 'missing'}")
    geometry, geometry_bbox = _geometry_bbox(request.get("geometry"))
    supplied_bbox = _bbox(request.get("bbox"))
    if geometry_bbox and supplied_bbox and geometry_bbox != supplied_bbox:
        raise ValueError("bbox must match geometry-derived WGS84 bounds when both are supplied")
    bbox = geometry_bbox or supplied_bbox
    if bbox is None:
        raise ValueError("geometry or bbox is required")
    valid = request.get("valid_time") if isinstance(request.get("valid_time"), Mapping) else {}
    start = _iso(valid.get("start") or request.get("valid_from"))
    end = _iso(valid.get("end") or request.get("valid_to"))
    if not start or not end:
        raise ValueError("valid_time.start and valid_time.end are required")
    if _dt(start) > _dt(end):
        raise ValueError("valid_time.start must not exceed valid_time.end")
    issued_at = _iso(request.get("issued_at") or request.get("generated_at"))
    if not issued_at:
        raise ValueError("issued_at is required")
    scenario = request.get("scenario") if isinstance(request.get("scenario"), Mapping) else {}
    calibration = request.get("calibration") if isinstance(request.get("calibration"), Mapping) else {}
    uncertainty = request.get("uncertainty") if isinstance(request.get("uncertainty"), Mapping) else {}
    provenance = request.get("provenance") if isinstance(request.get("provenance"), Mapping) else {}
    core = {
        "schema": PREDICTIVE_OBJECT_SCHEMA,
        "version": APP_VERSION,
        "object_type": "model-conditional-prediction",
        "target_layer_id": target_layer_id,
        "target_domain": layer["domain"],
        "target_capability_id": layer["capability_id"],
        "target_metric": _text(request.get("target_metric") or request.get("metric"), 240) or None,
        "geometry": geometry,
        "bbox": bbox,
        "crs": "EPSG:4326",
        "issued_at": issued_at,
        "valid_time": {"start": start, "end": end},
        "horizon": _text(request.get("horizon"), 160) or None,
        "model": _normalize_model(request.get("model")),
        "values": _normalize_values(request.get("values")),
        "scenario": {
            "scenario_id": _text(scenario.get("scenario_id") or scenario.get("id"), 200) or "baseline",
            "label": _text(scenario.get("label") or scenario.get("title"), 240) or "Baseline",
            "assumptions": _list(scenario.get("assumptions"), 100),
        },
        "uncertainty": deepcopy(uncertainty),
        "calibration": deepcopy(calibration),
        "provenance": deepcopy(provenance),
        "source_evidence_digests": sorted({str(x) for x in _list(request.get("source_evidence_digests"), 500) if str(x).startswith("sha256:")}),
        "status": _text(request.get("status"), 80).lower() or "published",
        "boundaries": [
            "prediction-is-derived-model-output-not-observation",
            "probability-is-not-truth",
            "spatial-overlap-is-not-confirmed-impact",
            "site-intelligence-does-not-train-retrain-or-auto-select-models",
            "calibration-and-uncertainty-remain-explicit",
        ],
    }
    digest = _digest(core)
    prediction = {
        **core,
        "prediction_id": _text(request.get("prediction_id") or request.get("forecast_id"), 240) or f"predictive-spatial:{digest.split(':', 1)[1][:24]}",
        "prediction_digest": digest,
    }
    return {"ok": True, "version": APP_VERSION, "prediction": prediction}


def validate_prediction(request: Mapping[str, Any]) -> dict[str, Any]:
    obj = request.get("prediction") if isinstance(request, Mapping) and isinstance(request.get("prediction"), Mapping) else request
    if not isinstance(obj, Mapping):
        raise ValueError("prediction must be an object")
    errors: list[str] = []
    warnings: list[str] = []
    if obj.get("schema") != PREDICTIVE_OBJECT_SCHEMA:
        errors.append("schema-mismatch")
    if obj.get("version") != APP_VERSION:
        errors.append("version-mismatch")
    if obj.get("object_type") != "model-conditional-prediction":
        errors.append("object-type-mismatch")
    if obj.get("target_layer_id") not in _layer_map():
        errors.append("unknown-target-layer")
    if not isinstance(obj.get("model"), Mapping):
        errors.append("model-missing")
    if not isinstance(obj.get("values"), list) or not obj.get("values"):
        errors.append("values-missing")
    if not obj.get("uncertainty"):
        warnings.append("uncertainty-context-missing")
    if not obj.get("calibration"):
        warnings.append("calibration-context-missing")
    core = {k: deepcopy(v) for k, v in obj.items() if k not in {"prediction_id", "prediction_digest"}}
    expected = _digest(core)
    if obj.get("prediction_digest") != expected:
        errors.append("prediction-digest-mismatch")
    return {
        "ok": not errors,
        "version": APP_VERSION,
        "schema": PREDICTIVE_OBJECT_SCHEMA,
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "expected_prediction_digest": expected,
    }


def _ensure_prediction(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping) and value.get("schema") == PREDICTIVE_OBJECT_SCHEMA:
        obj = deepcopy(dict(value))
        validation = validate_prediction(obj)
        if not validation["valid"]:
            raise ValueError("Invalid predictive object: " + ", ".join(validation["errors"]))
        return obj
    if isinstance(value, Mapping):
        return normalize_prediction(value)["prediction"]
    raise ValueError("prediction must be an object")


def bind_prediction(request: Mapping[str, Any]) -> dict[str, Any]:
    prediction = _ensure_prediction(request.get("prediction") if isinstance(request, Mapping) else None)
    evidence = [deepcopy(row) for row in _list(request.get("evidence_objects"), 5000) if isinstance(row, Mapping)]
    bindings: list[dict[str, Any]] = []
    for row in evidence:
        bbox = row.get("bbox")
        if not isinstance(bbox, list) or len(bbox) != 4:
            continue
        try:
            eb = _bbox(bbox)
        except ValueError:
            continue
        if not eb or not _bbox_intersects(prediction["bbox"], eb):
            continue
        digest = _text(row.get("content_digest") or row.get("digest"), 160) or _digest(row)
        bindings.append({
            "evidence_object_id": _text(row.get("object_id") or row.get("id"), 240) or None,
            "evidence_digest": digest,
            "layer_id": _text(row.get("layer_id"), 200) or None,
            "spatial_relation": "bbox-intersects",
            "impact_confirmed": False,
        })
    core = {
        "schema": MODEL_BINDING_SCHEMA,
        "version": APP_VERSION,
        "prediction_id": prediction["prediction_id"],
        "prediction_digest": prediction["prediction_digest"],
        "target_layer_id": prediction["target_layer_id"],
        "binding_count": len(bindings),
        "bindings": bindings,
        "semantics": "spatial-binding-does-not-establish-impact-or-causality",
    }
    digest = _digest(core)
    return {"ok": True, "version": APP_VERSION, "binding": {**core, "binding_id": f"predictive-binding:{digest.split(':',1)[1][:24]}", "binding_digest": digest}}


def query_predictions(request: Mapping[str, Any]) -> dict[str, Any]:
    predictions = [_ensure_prediction(row) for row in _list(request.get("predictions"), 5000)]
    filters = request.get("filters") if isinstance(request.get("filters"), Mapping) else {}
    layer_ids = {str(x) for x in _list(filters.get("layer_ids"), 200)}
    model_ids = {str(x) for x in _list(filters.get("model_ids"), 200)}
    provider_ids = {str(x) for x in _list(filters.get("providers"), 200)}
    scenario_ids = {str(x) for x in _list(filters.get("scenario_ids"), 200)}
    query_bbox = _bbox(filters.get("bbox")) if filters.get("bbox") is not None else None
    start = _dt(filters.get("start")) if filters.get("start") else None
    end = _dt(filters.get("end")) if filters.get("end") else None
    rows: list[dict[str, Any]] = []
    for obj in predictions:
        if layer_ids and obj["target_layer_id"] not in layer_ids:
            continue
        if model_ids and obj["model"]["model_id"] not in model_ids:
            continue
        if provider_ids and obj["model"]["provider"] not in provider_ids:
            continue
        if scenario_ids and obj["scenario"]["scenario_id"] not in scenario_ids:
            continue
        if query_bbox and not _bbox_intersects(obj["bbox"], query_bbox):
            continue
        obj_start, obj_end = _dt(obj["valid_time"]["start"]), _dt(obj["valid_time"]["end"])
        if start and obj_end and obj_end < start:
            continue
        if end and obj_start and obj_start > end:
            continue
        rows.append(obj)
    core = {
        "schema": "sc-site-intelligence-predictive-spatial-query-result/1.0",
        "version": APP_VERSION,
        "filters": deepcopy(filters),
        "count": len(rows),
        "predictions": rows,
        "prediction_digests": sorted(obj["prediction_digest"] for obj in rows),
    }
    digest = _digest(core)
    return {"ok": True, "version": APP_VERSION, "result": {**core, "result_id": f"predictive-query:{digest.split(':',1)[1][:24]}", "result_digest": digest}}


def compare_predictions(request: Mapping[str, Any]) -> dict[str, Any]:
    predictions = [_ensure_prediction(row) for row in _list(request.get("predictions"), 100)]
    if len(predictions) < 2:
        raise ValueError("At least two predictions are required for comparison")
    layer_ids = {obj["target_layer_id"] for obj in predictions}
    if len(layer_ids) != 1:
        raise ValueError("Comparison requires a common target_layer_id")
    summaries = []
    for obj in predictions:
        numeric = [row["value"] for row in obj["values"] if row.get("value") is not None]
        summaries.append({
            "prediction_id": obj["prediction_id"],
            "prediction_digest": obj["prediction_digest"],
            "model_id": obj["model"]["model_id"],
            "model_version": obj["model"]["model_version"],
            "provider": obj["model"]["provider"],
            "scenario_id": obj["scenario"]["scenario_id"],
            "point_count": len(obj["values"]),
            "numeric_mean": (sum(numeric) / len(numeric)) if numeric else None,
            "has_uncertainty": bool(obj.get("uncertainty")),
            "has_calibration": bool(obj.get("calibration")),
        })
    core = {
        "schema": COMPARISON_SCHEMA,
        "version": APP_VERSION,
        "target_layer_id": predictions[0]["target_layer_id"],
        "comparison_count": len(summaries),
        "summaries": summaries,
        "automatic_model_ranking": False,
        "preferred_prediction": None,
        "human_review_required": True,
    }
    digest = _digest(core)
    return {"ok": True, "version": APP_VERSION, "comparison": {**core, "comparison_id": f"predictive-comparison:{digest.split(':',1)[1][:24]}", "comparison_digest": digest}}


def scenario_context(request: Mapping[str, Any]) -> dict[str, Any]:
    predictions = [_ensure_prediction(row) for row in _list(request.get("predictions"), 500)]
    if not predictions:
        raise ValueError("predictions are required")
    groups: dict[str, list[dict[str, Any]]] = {}
    for obj in predictions:
        groups.setdefault(obj["scenario"]["scenario_id"], []).append(obj)
    scenario_rows = []
    for scenario_id in sorted(groups):
        rows = groups[scenario_id]
        scenario_rows.append({
            "scenario_id": scenario_id,
            "label": rows[0]["scenario"]["label"],
            "assumptions": deepcopy(rows[0]["scenario"].get("assumptions") or []),
            "prediction_count": len(rows),
            "prediction_digests": sorted(row["prediction_digest"] for row in rows),
            "target_layer_ids": sorted({row["target_layer_id"] for row in rows}),
        })
    core = {
        "schema": SCENARIO_SCHEMA,
        "version": APP_VERSION,
        "scenario_count": len(scenario_rows),
        "scenarios": scenario_rows,
        "automatic_scenario_selection": False,
        "preferred_scenario": None,
        "scenario_results_are_model_conditional": True,
    }
    digest = _digest(core)
    return {"ok": True, "version": APP_VERSION, "scenario_context": {**core, "scenario_context_id": f"predictive-scenarios:{digest.split(':',1)[1][:24]}", "scenario_digest": digest}}


def calibration_context(request: Mapping[str, Any]) -> dict[str, Any]:
    prediction = _ensure_prediction(request.get("prediction"))
    calibration = request.get("calibration") if isinstance(request.get("calibration"), Mapping) else prediction.get("calibration") or {}
    metrics = calibration.get("metrics") if isinstance(calibration.get("metrics"), Mapping) else {}
    status = _text(calibration.get("status"), 80).lower() or ("provided" if calibration else "not-provided")
    core = {
        "schema": CALIBRATION_CONTEXT_SCHEMA,
        "version": APP_VERSION,
        "prediction_id": prediction["prediction_id"],
        "prediction_digest": prediction["prediction_digest"],
        "status": status,
        "method": _text(calibration.get("method"), 240) or None,
        "evaluation_period": deepcopy(calibration.get("evaluation_period")) if isinstance(calibration.get("evaluation_period"), Mapping) else {},
        "metrics": deepcopy(metrics),
        "artifact_digest": _text(calibration.get("artifact_digest") or calibration.get("digest"), 160) or None,
        "consumer_recomputed_metrics": False,
        "calibration_is_evidence_not_guarantee": True,
    }
    digest = _digest(core)
    return {"ok": True, "version": APP_VERSION, "calibration_context": {**core, "calibration_context_id": f"predictive-calibration:{digest.split(':',1)[1][:24]}", "calibration_context_digest": digest}}


def research_context(request: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(request, Mapping):
        raise ValueError("Research context request must be an object")
    research = request.get("research_object")
    if not isinstance(research, Mapping):
        raise ValueError("research_object is required")
    validation = validate_research_object(research)
    if not validation["valid"]:
        raise ValueError("Invalid spatial research object: " + ", ".join(validation["errors"]))
    predictions = [_ensure_prediction(row) for row in _list(request.get("predictions"), 500)]
    if not predictions:
        raise ValueError("predictions are required")
    core = {
        "schema": RESEARCH_CONTEXT_SCHEMA,
        "version": APP_VERSION,
        "research_object_id": research["research_object_id"],
        "research_digest": research["research_digest"],
        "prediction_count": len(predictions),
        "prediction_digests": sorted(row["prediction_digest"] for row in predictions),
        "target_layer_ids": sorted({row["target_layer_id"] for row in predictions}),
        "model_refs": sorted({f"{row['model']['provider']}:{row['model']['model_id']}:{row['model']['model_version']}" for row in predictions}),
        "source_evidence_digests": sorted({digest for row in predictions for digest in row.get("source_evidence_digests") or []}),
        "research_object_mutated": False,
        "derived_prediction_context_only": True,
    }
    digest = _digest(core)
    return {"ok": True, "version": APP_VERSION, "research_context": {**core, "research_context_id": f"predictive-research:{digest.split(':',1)[1][:24]}", "research_context_digest": digest}}


def compatibility_manifest() -> dict[str, Any]:
    return {
        "ok": True,
        "version": APP_VERSION,
        "v4_46_spatial_evidence": {"status": "preserved-and-consumed", "prediction_is_observation": False},
        "v4_47_spatiotemporal": {"status": "preserved-and-consumed", "spatial_semantics": "bbox-compatible"},
        "v4_48_spatial_graph": {"status": "preserved", "automatic_causal_edges_from_prediction": False},
        "v4_49_live_geospatial": {"status": "preserved", "prediction_does_not_confirm_event_impact": True},
        "v4_50_source_federation": {"status": "preserved", "authority_quality_and_trust_separate": True},
        "v4_51_spatial_research": {"status": "preserved-and-consumed", "research_object_mutation": False},
        "legacy_model_governance": {"status": "preserved", "routes": ["/public/models", "/public/forecasts", "/public/forecast-evaluations"]},
        "workspace_core_consumption": {"mode": "provider-neutral-import", "network_fetch_by_consumer": False},
        "wordpress_role": "public-site-launch-bridge",
        "model_training_authority": False,
        "automatic_model_selection": False,
    }
