from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from .spatial_evidence_registry_v4460 import EVIDENCE_OBJECT_SCHEMA, normalize_evidence_object
from .version import APP_VERSION

QUERY_SCHEMA = "sc-site-intelligence-spatiotemporal-query/1.0"
QUERY_PLAN_SCHEMA = "sc-site-intelligence-spatiotemporal-query-plan/1.0"
QUERY_RESULT_SCHEMA = "sc-site-intelligence-spatiotemporal-query-result/1.0"
JOIN_RESULT_SCHEMA = "sc-site-intelligence-cross-layer-join-result/1.0"
ANALYSIS_RESULT_SCHEMA = "sc-site-intelligence-cross-layer-analysis-result/1.0"
OPERATOR_REGISTRY_SCHEMA = "sc-site-intelligence-spatiotemporal-operator-registry/1.0"
ENGINE_CONTRACT_VERSION = "1.0.0"
OPERATOR_REGISTRY_PATH = Path(__file__).resolve().parents[1] / "data" / "spatiotemporal_operator_registry_v4470.json"
MAX_OBJECTS = 5000
MAX_RESULTS = 2000
MAX_PAIRS = 5000


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def _iso(value: Any) -> str | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        text = str(value).strip().replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(text)
        except ValueError as exc:
            raise ValueError(f"Invalid ISO-8601 datetime: {value}") from exc
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


def _dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _bbox(value: Any) -> list[float]:
    if not isinstance(value, (list, tuple)) or len(value) != 4:
        raise ValueError("bbox must be [west,south,east,north]")
    west, south, east, north = [float(item) for item in value]
    if not (-180 <= west <= 180 and -180 <= east <= 180 and -90 <= south <= 90 and -90 <= north <= 90):
        raise ValueError("bbox must use WGS84 coordinate bounds")
    if west > east or south > north:
        raise ValueError("bbox west/south must not exceed east/north")
    return [west, south, east, north]


def _bbox_intersects(a: list[float], b: list[float]) -> bool:
    return not (a[2] < b[0] or a[0] > b[2] or a[3] < b[1] or a[1] > b[3])


def _bbox_within(a: list[float], b: list[float]) -> bool:
    return a[0] >= b[0] and a[1] >= b[1] and a[2] <= b[2] and a[3] <= b[3]


def _bbox_contains(a: list[float], b: list[float]) -> bool:
    return _bbox_within(b, a)


def _spatial_relation(a: list[float], b: list[float], operator: str) -> bool:
    if operator == "intersects":
        return _bbox_intersects(a, b)
    if operator == "within":
        return _bbox_within(a, b)
    if operator == "contains":
        return _bbox_contains(a, b)
    if operator == "disjoint":
        return not _bbox_intersects(a, b)
    raise ValueError(f"Unsupported spatial predicate: {operator}")


def _temporal_interval(obj: dict[str, Any]) -> tuple[datetime | None, datetime | None]:
    valid = obj.get("valid_time") if isinstance(obj.get("valid_time"), dict) else {}
    start = _dt(valid.get("start"))
    end = _dt(valid.get("end"))
    observed = _dt(obj.get("observed_at"))
    if start is None and end is None and observed is not None:
        return observed, observed
    if start is None:
        start = end
    if end is None:
        end = start
    if start and end and start > end:
        raise ValueError(f"Object {obj.get('object_id')} has valid_time.start after valid_time.end")
    return start, end


def _query_interval(temporal: dict[str, Any]) -> tuple[datetime | None, datetime | None]:
    start = _dt(_iso(temporal.get("start")))
    end = _dt(_iso(temporal.get("end")))
    at = _dt(_iso(temporal.get("at")))
    if at:
        return at, at
    if start is None and end is None:
        return None, None
    if start is None:
        start = end
    if end is None:
        end = start
    if start and end and start > end:
        raise ValueError("temporal.start must not be after temporal.end")
    return start, end


def _temporal_relation(a: tuple[datetime | None, datetime | None], b: tuple[datetime | None, datetime | None], operator: str) -> bool:
    a0, a1 = a
    b0, b1 = b
    if None in (a0, a1, b0, b1):
        return False
    assert a0 is not None and a1 is not None and b0 is not None and b1 is not None
    if operator == "overlaps":
        return a0 <= b1 and a1 >= b0
    if operator == "within":
        return a0 >= b0 and a1 <= b1
    if operator == "contains":
        return a0 <= b0 and a1 >= b1
    if operator == "before":
        return a1 < b0
    if operator == "after":
        return a0 > b1
    if operator == "at":
        return a0 <= b0 <= a1
    raise ValueError(f"Unsupported temporal predicate: {operator}")


def _operator_registry() -> dict[str, Any]:
    payload = json.loads(OPERATOR_REGISTRY_PATH.read_text(encoding="utf-8"))
    if payload.get("schema") != OPERATOR_REGISTRY_SCHEMA:
        raise ValueError("Spatiotemporal operator registry schema mismatch")
    if payload.get("version") != APP_VERSION:
        raise ValueError("Spatiotemporal operator registry version does not match application version")
    return payload


def operator_manifest() -> dict[str, Any]:
    payload = _operator_registry()
    return {"ok": True, **deepcopy(payload)}


def engine_manifest() -> dict[str, Any]:
    operators = _operator_registry()
    return {
        "ok": True,
        "version": APP_VERSION,
        "contract_version": ENGINE_CONTRACT_VERSION,
        "query_schema": QUERY_SCHEMA,
        "query_plan_schema": QUERY_PLAN_SCHEMA,
        "query_result_schema": QUERY_RESULT_SCHEMA,
        "join_result_schema": JOIN_RESULT_SCHEMA,
        "analysis_result_schema": ANALYSIS_RESULT_SCHEMA,
        "evidence_object_schema": EVIDENCE_OBJECT_SCHEMA,
        "coordinate_reference_system": "EPSG:4326",
        "spatial_semantics": operators["spatial_semantics"],
        "limits": {"objects": MAX_OBJECTS, "results": MAX_RESULTS, "join_pairs": MAX_PAIRS},
        "endpoints": {
            "query_schema": "/public/spatiotemporal/query-schema",
            "operators": "/public/spatiotemporal/operators",
            "plan": "/public/spatiotemporal/query/plan",
            "execute": "/public/spatiotemporal/query/execute",
            "join": "/public/spatiotemporal/cross-layer/join",
            "analyze": "/public/spatiotemporal/cross-layer/analyze",
            "compatibility": "/public/spatiotemporal/compatibility",
        },
        "principles": operators["principles"],
    }


def query_schema_contract() -> dict[str, Any]:
    return {
        "ok": True,
        "version": APP_VERSION,
        "schema": QUERY_SCHEMA,
        "contract_version": ENGINE_CONTRACT_VERSION,
        "query_fields": {
            "layer_ids": "Optional registered layer IDs.",
            "domains": "Optional v4.46 spatial evidence domains.",
            "capability_ids": "Optional Site Intelligence capability IDs.",
            "spatial": {"bbox": "WGS84 [west,south,east,north]", "predicate": ["intersects", "within", "contains", "disjoint"]},
            "temporal": {"start": "ISO-8601", "end": "ISO-8601", "at": "ISO-8601", "predicate": ["overlaps", "within", "contains", "before", "after", "at"], "include_timeless": False},
            "properties": [{"path": "properties.metric", "operator": "eq", "value": "caller-defined"}],
            "limit": f"1..{MAX_RESULTS}",
        },
        "execution_request": {"objects": f"1..{MAX_OBJECTS} v4.46 evidence objects or normalizable raw objects", "query": QUERY_SCHEMA},
        "join_request": {"objects": f"1..{MAX_OBJECTS}", "left": "query selector", "right": "query selector", "spatial_predicate": "intersects", "temporal_predicate": "overlaps", "max_pairs": MAX_PAIRS},
    }


def _list(value: Any, field: str) -> list[str]:
    if value in (None, ""):
        return []
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list")
    return [str(item).strip() for item in value if str(item).strip()]


def _normalize_property_filter(item: Any) -> dict[str, Any]:
    if not isinstance(item, dict):
        raise ValueError("property filters must be objects")
    path = str(item.get("path") or "").strip()
    operator = str(item.get("operator") or "eq").strip().lower()
    if not path:
        raise ValueError("property filter path is required")
    allowed = set(_operator_registry()["property_operators"])
    if operator not in allowed:
        raise ValueError(f"Unsupported property operator: {operator}")
    payload = {"path": path, "operator": operator}
    if operator != "exists":
        payload["value"] = deepcopy(item.get("value"))
    elif "value" in item:
        payload["value"] = bool(item.get("value"))
    return payload


def normalize_query(query: Any) -> dict[str, Any]:
    if query in (None, {}):
        query = {}
    if not isinstance(query, dict):
        raise ValueError("query must be a JSON object")
    operators = _operator_registry()
    spatial_raw = query.get("spatial") if isinstance(query.get("spatial"), dict) else {}
    temporal_raw = query.get("temporal") if isinstance(query.get("temporal"), dict) else {}

    spatial = None
    if spatial_raw:
        predicate = str(spatial_raw.get("predicate") or "intersects").strip().lower()
        allowed_spatial = {row["operator"] for row in operators["spatial_predicates"]}
        if predicate not in allowed_spatial:
            raise ValueError(f"Unsupported spatial predicate: {predicate}")
        spatial = {"bbox": _bbox(spatial_raw.get("bbox")), "predicate": predicate}

    temporal = None
    if temporal_raw:
        predicate = str(temporal_raw.get("predicate") or ("at" if temporal_raw.get("at") else "overlaps")).strip().lower()
        allowed_temporal = {row["operator"] for row in operators["temporal_predicates"]}
        if predicate not in allowed_temporal:
            raise ValueError(f"Unsupported temporal predicate: {predicate}")
        start, end = _query_interval(temporal_raw)
        if start is None or end is None:
            raise ValueError("temporal filter requires start/end or at")
        temporal = {
            "start": start.astimezone(timezone.utc).isoformat(),
            "end": end.astimezone(timezone.utc).isoformat(),
            "predicate": predicate,
            "include_timeless": bool(temporal_raw.get("include_timeless", False)),
        }

    properties_raw = query.get("properties") or []
    if not isinstance(properties_raw, list):
        raise ValueError("query.properties must be a list")
    properties = [_normalize_property_filter(item) for item in properties_raw]
    limit = int(query.get("limit") or 250)
    if not 1 <= limit <= MAX_RESULTS:
        raise ValueError(f"query.limit must be between 1 and {MAX_RESULTS}")

    return {
        "schema": QUERY_SCHEMA,
        "version": APP_VERSION,
        "layer_ids": _list(query.get("layer_ids"), "layer_ids"),
        "domains": _list(query.get("domains"), "domains"),
        "capability_ids": _list(query.get("capability_ids"), "capability_ids"),
        "spatial": spatial,
        "temporal": temporal,
        "properties": properties,
        "limit": limit,
    }


def compile_query_plan(query: Any) -> dict[str, Any]:
    normalized = normalize_query(query)
    stages = []
    if normalized["layer_ids"] or normalized["domains"] or normalized["capability_ids"]:
        stages.append("layer-domain-capability-filter")
    if normalized["spatial"]:
        stages.append("spatial-bbox-filter")
    if normalized["temporal"]:
        stages.append("temporal-interval-filter")
    if normalized["properties"]:
        stages.append("property-filter")
    stages.append("stable-object-id-order")
    stages.append("result-limit")
    basis = {"query": normalized, "stages": stages, "engine_contract_version": ENGINE_CONTRACT_VERSION}
    return {
        "ok": True,
        "schema": QUERY_PLAN_SCHEMA,
        "version": APP_VERSION,
        "plan_id": "stq-" + _digest(basis).split(":", 1)[1][:24],
        "plan_digest": _digest(basis),
        "query": normalized,
        "stages": stages,
        "spatial_semantics": _operator_registry()["spatial_semantics"],
        "deterministic": True,
    }


def _normalize_objects(raw: Any) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        raise ValueError("objects must be a list")
    if not raw:
        return []
    if len(raw) > MAX_OBJECTS:
        raise ValueError(f"objects exceeds maximum of {MAX_OBJECTS}")
    rows = []
    for item in raw:
        if not isinstance(item, dict):
            raise ValueError("each object must be a JSON object")
        if item.get("schema") == EVIDENCE_OBJECT_SCHEMA and item.get("content_digest") and item.get("bbox"):
            if item.get("crs") != "EPSG:4326":
                raise ValueError("canonical evidence objects must use EPSG:4326 for v4.47 query execution")
            rows.append(deepcopy(item))
        else:
            rows.append(normalize_evidence_object(item))
    rows.sort(key=lambda row: (row.get("layer_id", ""), row.get("object_id", ""), row.get("content_digest", "")))
    return rows


def _get_path(obj: dict[str, Any], path: str) -> tuple[bool, Any]:
    current: Any = obj
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return False, None
        current = current[part]
    return True, current


def _property_match(obj: dict[str, Any], filt: dict[str, Any]) -> bool:
    exists, actual = _get_path(obj, filt["path"])
    operator = filt["operator"]
    expected = filt.get("value")
    if operator == "exists":
        desired = bool(filt.get("value", True))
        return exists is desired
    if not exists:
        return False
    if operator == "eq":
        return actual == expected
    if operator == "ne":
        return actual != expected
    if operator == "in":
        if not isinstance(expected, list):
            raise ValueError("property operator 'in' requires a list value")
        return actual in expected
    if operator == "contains":
        if isinstance(actual, (str, list, tuple, set, dict)):
            return expected in actual
        return False
    if operator in {"gt", "gte", "lt", "lte"}:
        try:
            left = float(actual)
            right = float(expected)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"property filter {filt['path']} requires numeric values for {operator}") from exc
        return {"gt": left > right, "gte": left >= right, "lt": left < right, "lte": left <= right}[operator]
    raise ValueError(f"Unsupported property operator: {operator}")


def _matches(obj: dict[str, Any], query: dict[str, Any]) -> bool:
    if query["layer_ids"] and obj.get("layer_id") not in set(query["layer_ids"]):
        return False
    if query["domains"] and obj.get("domain") not in set(query["domains"]):
        return False
    if query["capability_ids"] and obj.get("capability_id") not in set(query["capability_ids"]):
        return False
    if query["spatial"] and not _spatial_relation(obj["bbox"], query["spatial"]["bbox"], query["spatial"]["predicate"]):
        return False
    if query["temporal"]:
        object_interval = _temporal_interval(obj)
        if object_interval[0] is None:
            if not query["temporal"]["include_timeless"]:
                return False
        else:
            query_interval = (_dt(query["temporal"]["start"]), _dt(query["temporal"]["end"]))
            if not _temporal_relation(object_interval, query_interval, query["temporal"]["predicate"]):
                return False
    return all(_property_match(obj, filt) for filt in query["properties"])


def execute_query(request: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise ValueError("execution request must be a JSON object")
    objects = _normalize_objects(request.get("objects") or [])
    plan = compile_query_plan(request.get("query") or {})
    query = plan["query"]
    matched = [obj for obj in objects if _matches(obj, query)]
    total = len(matched)
    matched = matched[: query["limit"]]
    source_digests = [obj["content_digest"] for obj in matched]
    provenance = {
        "source_object_count": len(objects),
        "matched_object_count": total,
        "returned_object_count": len(matched),
        "source_object_digests": source_digests,
        "query_plan_digest": plan["plan_digest"],
        "spatial_semantics": _operator_registry()["spatial_semantics"],
    }
    basis = {"plan_digest": plan["plan_digest"], "source_object_digests": source_digests}
    return {
        "ok": True,
        "schema": QUERY_RESULT_SCHEMA,
        "version": APP_VERSION,
        "result_id": "str-" + _digest(basis).split(":", 1)[1][:24],
        "result_digest": _digest(basis),
        "plan": plan,
        "count": len(matched),
        "total_matched": total,
        "truncated": total > len(matched),
        "objects": matched,
        "provenance": provenance,
    }


def _selector(value: Any) -> dict[str, Any]:
    if value in (None, {}):
        return normalize_query({"limit": MAX_RESULTS})
    if not isinstance(value, dict):
        raise ValueError("join selectors must be JSON objects")
    selector = dict(value)
    selector.setdefault("limit", MAX_RESULTS)
    return normalize_query(selector)


def cross_layer_join(request: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise ValueError("join request must be a JSON object")
    objects = _normalize_objects(request.get("objects") or [])
    left_query = _selector(request.get("left"))
    right_query = _selector(request.get("right"))
    operators = _operator_registry()
    spatial_predicate = str(request.get("spatial_predicate") or "intersects").strip().lower()
    temporal_predicate = str(request.get("temporal_predicate") or "overlaps").strip().lower()
    allowed_spatial = set(operators["join_contract"]["spatial_predicates"])
    allowed_temporal = set(operators["join_contract"]["temporal_predicates"])
    if spatial_predicate not in allowed_spatial:
        raise ValueError(f"Unsupported join spatial predicate: {spatial_predicate}")
    if temporal_predicate not in allowed_temporal:
        raise ValueError(f"Unsupported join temporal predicate: {temporal_predicate}")
    max_pairs = int(request.get("max_pairs") or 500)
    if not 1 <= max_pairs <= MAX_PAIRS:
        raise ValueError(f"max_pairs must be between 1 and {MAX_PAIRS}")
    left = [obj for obj in objects if _matches(obj, left_query)]
    right = [obj for obj in objects if _matches(obj, right_query)]
    pairs: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    total_pairs = 0
    for a in left:
        for b in right:
            if a["object_id"] == b["object_id"]:
                continue
            key = (a["object_id"], b["object_id"])
            if key in seen:
                continue
            spatial_ok = _spatial_relation(a["bbox"], b["bbox"], spatial_predicate)
            if not spatial_ok:
                continue
            a_interval = _temporal_interval(a)
            b_interval = _temporal_interval(b)
            temporal_ok = _temporal_relation(a_interval, b_interval, temporal_predicate)
            if not temporal_ok:
                continue
            total_pairs += 1
            seen.add(key)
            if len(pairs) < max_pairs:
                pairs.append({
                    "left_object_id": a["object_id"],
                    "left_layer_id": a["layer_id"],
                    "right_object_id": b["object_id"],
                    "right_layer_id": b["layer_id"],
                    "spatial_relation": spatial_predicate,
                    "temporal_relation": temporal_predicate,
                    "left_content_digest": a["content_digest"],
                    "right_content_digest": b["content_digest"],
                })
    basis = {
        "left_query": left_query,
        "right_query": right_query,
        "spatial_predicate": spatial_predicate,
        "temporal_predicate": temporal_predicate,
        "pairs": pairs,
    }
    return {
        "ok": True,
        "schema": JOIN_RESULT_SCHEMA,
        "version": APP_VERSION,
        "join_id": "stj-" + _digest(basis).split(":", 1)[1][:24],
        "join_digest": _digest(basis),
        "spatial_semantics": operators["spatial_semantics"],
        "left_count": len(left),
        "right_count": len(right),
        "pair_count": len(pairs),
        "total_pair_count": total_pairs,
        "truncated": total_pairs > len(pairs),
        "pairs": pairs,
        "provenance": {
            "source_object_digests": sorted({obj["content_digest"] for obj in [*left, *right]}),
            "operators": {"spatial": spatial_predicate, "temporal": temporal_predicate},
        },
    }


def _numeric(values: list[Any]) -> list[float]:
    rows = []
    for value in values:
        if isinstance(value, bool):
            continue
        try:
            number = float(value)
        except (TypeError, ValueError):
            continue
        if math.isfinite(number):
            rows.append(number)
    return rows


def _aggregate(rows: list[dict[str, Any]], metric: dict[str, Any]) -> Any:
    operator = str(metric.get("operator") or "count").strip().lower()
    if operator == "count":
        return len(rows)
    path = str(metric.get("path") or "properties.value").strip()
    values = []
    for row in rows:
        exists, value = _get_path(row, path)
        if exists:
            values.append(value)
    numeric = _numeric(values)
    if not numeric:
        return None
    if operator == "sum":
        return sum(numeric)
    if operator == "mean":
        return sum(numeric) / len(numeric)
    if operator == "min":
        return min(numeric)
    if operator == "max":
        return max(numeric)
    raise ValueError(f"Unsupported aggregate operator: {operator}")


def cross_layer_analysis(request: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise ValueError("analysis request must be a JSON object")
    query_request = deepcopy(request.get("query") if isinstance(request.get("query"), dict) else {})
    query_request.setdefault("limit", MAX_RESULTS)
    execution = execute_query({"objects": request.get("objects") or [], "query": query_request})
    rows = execution["objects"]
    group_by = str(request.get("group_by") or "layer_id").strip()
    if group_by not in {"layer_id", "domain", "capability_id"}:
        raise ValueError("group_by must be layer_id, domain, or capability_id")
    metrics = request.get("metrics") or [{"name": "count", "operator": "count"}]
    if not isinstance(metrics, list) or not metrics:
        raise ValueError("metrics must be a non-empty list")
    allowed_aggregates = set(_operator_registry()["aggregate_operators"])
    normalized_metrics = []
    for metric in metrics:
        if not isinstance(metric, dict):
            raise ValueError("each metric must be an object")
        operator = str(metric.get("operator") or "count").strip().lower()
        if operator not in allowed_aggregates:
            raise ValueError(f"Unsupported aggregate operator: {operator}")
        normalized_metrics.append({
            "name": str(metric.get("name") or (operator if operator == "count" else f"{operator}_{metric.get('path') or 'properties.value'}")).strip(),
            "operator": operator,
            "path": str(metric.get("path") or "properties.value").strip() if operator != "count" else None,
        })
    groups = []
    for key in sorted({str(row.get(group_by) or "unknown") for row in rows}):
        members = [row for row in rows if str(row.get(group_by) or "unknown") == key]
        groups.append({
            "key": key,
            "object_count": len(members),
            "metrics": {metric["name"]: _aggregate(members, metric) for metric in normalized_metrics},
            "source_object_digests": [row["content_digest"] for row in members],
        })

    layer_overlap = []
    layer_ids = sorted({row["layer_id"] for row in rows})
    for index, left_layer in enumerate(layer_ids):
        for right_layer in layer_ids[index + 1:]:
            left_rows = [row for row in rows if row["layer_id"] == left_layer]
            right_rows = [row for row in rows if row["layer_id"] == right_layer]
            count = 0
            for a in left_rows:
                for b in right_rows:
                    if _bbox_intersects(a["bbox"], b["bbox"]):
                        a_interval = _temporal_interval(a)
                        b_interval = _temporal_interval(b)
                        if a_interval[0] is None or b_interval[0] is None or _temporal_relation(a_interval, b_interval, "overlaps"):
                            count += 1
            if count:
                layer_overlap.append({"left_layer_id": left_layer, "right_layer_id": right_layer, "overlap_pair_count": count})

    basis = {"query_result_digest": execution["result_digest"], "group_by": group_by, "metrics": normalized_metrics, "groups": groups, "layer_overlap": layer_overlap}
    return {
        "ok": True,
        "schema": ANALYSIS_RESULT_SCHEMA,
        "version": APP_VERSION,
        "analysis_id": "sta-" + _digest(basis).split(":", 1)[1][:24],
        "analysis_digest": _digest(basis),
        "query_result_id": execution["result_id"],
        "group_by": group_by,
        "metrics": normalized_metrics,
        "group_count": len(groups),
        "groups": groups,
        "cross_layer_overlap": layer_overlap,
        "provenance": execution["provenance"],
        "spatial_semantics": _operator_registry()["spatial_semantics"],
    }


def compatibility_contract() -> dict[str, Any]:
    return {
        "ok": True,
        "version": APP_VERSION,
        "contract_version": ENGINE_CONTRACT_VERSION,
        "v4_46_spatial_evidence": {
            "status": "preserved-and-consumed",
            "registry": "/public/spatial-evidence/registry",
            "layers": "/public/spatial-evidence/layers",
            "object_schema": EVIDENCE_OBJECT_SCHEMA,
        },
        "legacy_spatial_studio": {
            "status": "preserved",
            "summary": "/public/spatial",
            "layers": "/public/spatial/layers",
        },
        "v4_47": {
            "registry": "/public/spatiotemporal/registry",
            "query_plan": "/public/spatiotemporal/query/plan",
            "query_execute": "/public/spatiotemporal/query/execute",
            "cross_layer_join": "/public/spatiotemporal/cross-layer/join",
            "cross_layer_analysis": "/public/spatiotemporal/cross-layer/analyze",
        },
        "migration_rule": "v4.47 consumes normalized v4.46 evidence objects and adds deterministic query/join/analysis results without changing source objects or legacy spatial endpoints.",
    }
