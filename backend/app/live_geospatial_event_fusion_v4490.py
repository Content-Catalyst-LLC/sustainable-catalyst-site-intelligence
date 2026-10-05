from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from .spatial_evidence_registry_v4460 import EVIDENCE_OBJECT_SCHEMA, normalize_evidence_object
from .spatial_relationship_graph_v4480 import GRAPH_SCHEMA, build_graph
from .version import APP_VERSION

EVENT_SCHEMA = "sc-site-intelligence-live-geospatial-event/1.0"
EVENT_CLUSTER_SCHEMA = "sc-site-intelligence-live-event-cluster/1.0"
FUSION_RESULT_SCHEMA = "sc-site-intelligence-live-geospatial-fusion-result/1.0"
GRAPH_FUSION_SCHEMA = "sc-site-intelligence-live-event-graph-fusion/1.0"
EVENT_QUERY_RESULT_SCHEMA = "sc-site-intelligence-live-event-query-result/1.0"
SNAPSHOT_SCHEMA = "sc-site-intelligence-live-geospatial-snapshot/1.0"
TRANSITION_SCHEMA = "sc-site-intelligence-live-event-lifecycle-transition/1.0"
REGISTRY_SCHEMA = "sc-site-intelligence-live-geospatial-event-fusion-registry/1.0"
CONTRACT_VERSION = "1.0.0"
REGISTRY_PATH = Path(__file__).resolve().parents[1] / "data" / "live_geospatial_event_fusion_registry_v4490.json"
LIVE_SOURCE_REGISTRY_PATH = Path(__file__).resolve().parents[1] / "data" / "live_intelligence_source_registry_v320.json"
_SAFE = re.compile(r"[^a-zA-Z0-9_.:-]+")
_SPACE = re.compile(r"\s+")
MAX_EVENTS = 5000
MAX_EVIDENCE_OBJECTS = 10000
MAX_FUSION_MATCHES = 50000


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def _safe_id(value: Any, fallback: str) -> str:
    cleaned = _SAFE.sub("-", str(value or "").strip()).strip("-.")
    return (cleaned or fallback)[:200]


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
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _registry() -> dict[str, Any]:
    payload = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    if payload.get("schema") != REGISTRY_SCHEMA:
        raise ValueError("Live geospatial fusion registry schema mismatch")
    if payload.get("version") != APP_VERSION:
        raise ValueError("Live geospatial fusion registry version does not match application version")
    return payload


def _live_sources() -> dict[str, Any]:
    payload = json.loads(LIVE_SOURCE_REGISTRY_PATH.read_text(encoding="utf-8"))
    if payload.get("version") != APP_VERSION:
        raise ValueError("Live intelligence source registry version does not match application version")
    return payload


def _source_map() -> dict[str, dict[str, Any]]:
    return {str(row["feed_id"]): row for row in _live_sources().get("sources") or []}


def _severity_map() -> dict[str, int]:
    return {row["level"]: int(row["rank"]) for row in _registry()["severity_levels"]}


def _bbox_intersects(a: list[float] | None, b: list[float] | None) -> bool:
    if not a or not b or len(a) != 4 or len(b) != 4:
        return False
    return not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])


def _interval(record: dict[str, Any]) -> tuple[datetime | None, datetime | None]:
    valid = record.get("valid_time") if isinstance(record.get("valid_time"), dict) else {}
    start = _dt(valid.get("start")) or _dt(record.get("observed_at"))
    end = _dt(valid.get("end")) or start
    return start, end


def _interval_overlaps(a: dict[str, Any], b: dict[str, Any]) -> bool | None:
    a_start, a_end = _interval(a)
    b_start, b_end = _interval(b)
    if a_start is None or a_end is None or b_start is None or b_end is None:
        return None
    return a_start <= b_end and b_start <= a_end


def _normalize_title(value: Any) -> str:
    text = _SPACE.sub(" ", str(value or "").strip().lower())
    return re.sub(r"[^a-z0-9 .:_/-]+", "", text)[:300]


def _strict_fingerprint(event: dict[str, Any]) -> str:
    observed = event.get("observed_at")
    observed_minute = observed[:16] if isinstance(observed, str) else None
    basis = {
        "event_type": event["event_type"],
        "title": _normalize_title(event.get("title")),
        "bbox": [round(float(v), 5) for v in event["bbox"]],
        "observed_minute": observed_minute,
    }
    return "strict:" + _digest(basis).split(":", 1)[1][:32]


def registry_manifest() -> dict[str, Any]:
    registry = _registry()
    return {
        "ok": True,
        "version": APP_VERSION,
        "contract_version": CONTRACT_VERSION,
        "schema": registry["schema"],
        "event_object_schema": EVENT_SCHEMA,
        "event_cluster_schema": EVENT_CLUSTER_SCHEMA,
        "fusion_result_schema": FUSION_RESULT_SCHEMA,
        "spatial_semantics": registry["spatial_semantics"],
        "temporal_semantics": registry["temporal_semantics"],
        "identity_semantics": registry["identity_semantics"],
        "event_type_count": len(registry["event_types"]),
        "source_adapter_count": len(registry["source_adapters"]),
        "lifecycle_state_count": len(registry["lifecycle_states"]),
        "endpoints": {
            "event_schema": "/public/live-geospatial/event-schema",
            "sources": "/public/live-geospatial/sources",
            "lifecycle": "/public/live-geospatial/lifecycle",
            "normalize": "/public/live-geospatial/events/normalize",
            "normalize_source": "/public/live-geospatial/events/normalize-source",
            "reconcile": "/public/live-geospatial/events/reconcile",
            "query": "/public/live-geospatial/events/query",
            "transition": "/public/live-geospatial/lifecycle/transition",
            "fuse_layers": "/public/live-geospatial/fuse/layers",
            "fuse_graph": "/public/live-geospatial/fuse/graph",
            "snapshot": "/public/live-geospatial/snapshot",
            "compatibility": "/public/live-geospatial/compatibility",
        },
        "principles": deepcopy(registry["principles"]),
    }


def event_schema_contract() -> dict[str, Any]:
    registry = _registry()
    return {
        "ok": True,
        "version": APP_VERSION,
        "schema": EVENT_SCHEMA,
        "contract_version": CONTRACT_VERSION,
        "required": ["event_type", "geometry", "source"],
        "event_types": deepcopy(registry["event_types"]),
        "lifecycle_states": deepcopy(registry["lifecycle_states"]),
        "severity_levels": deepcopy(registry["severity_levels"]),
        "fields": {
            "event_id": "Stable caller/source identifier or deterministic content-derived ID.",
            "event_type": "Registered live-event category.",
            "title": "Source-supplied event title/headline.",
            "lifecycle_state": "detected, active, updated, resolved, or retracted.",
            "severity": "Source-preserving categorical severity; not a risk score.",
            "confidence": "Optional source/adapter supplied [0,1] confidence; never silently imputed.",
            "geometry": "WGS84 geometry validated through the v4.46 live-events-hazards layer.",
            "bbox": "Derived WGS84 bounding box.",
            "observed_at": "UTC observation timestamp.",
            "updated_at": "Optional UTC source update timestamp.",
            "valid_time": "Optional start/end event validity interval.",
            "source": "Source/feed/record identity and source URL.",
            "correlation_keys": "Explicit cross-source keys plus a strict deterministic fingerprint.",
            "evidence_object": "Canonical v4.46 spatial evidence representation of the event.",
            "content_digest": "SHA-256 digest over normalized event content.",
        },
    }


def source_manifest() -> dict[str, Any]:
    registry = _registry()
    live = _live_sources()
    source_by_id = {row["feed_id"]: row for row in live.get("sources") or []}
    rows = []
    for adapter in registry["source_adapters"]:
        source = source_by_id.get(adapter["feed_id"], {})
        rows.append({
            **deepcopy(adapter),
            "label": source.get("label"),
            "provider": source.get("provider"),
            "data_classification": source.get("data_classification"),
            "stale_after_minutes": source.get("stale_after_minutes"),
            "quality": deepcopy(source.get("quality") or {}),
            "coverage": deepcopy(source.get("coverage") or {}),
        })
    return {"ok": True, "version": APP_VERSION, "count": len(rows), "sources": rows}


def lifecycle_manifest() -> dict[str, Any]:
    registry = _registry()
    return {
        "ok": True,
        "version": APP_VERSION,
        "schema": TRANSITION_SCHEMA,
        "states": deepcopy(registry["lifecycle_states"]),
        "transitions": deepcopy(registry["lifecycle_transitions"]),
        "severity_levels": deepcopy(registry["severity_levels"]),
    }


def normalize_event(request: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise ValueError("Live geospatial event must be a JSON object")
    registry = _registry()
    event_type = str(request.get("event_type") or "").strip().lower()
    if event_type not in set(registry["event_types"]):
        raise ValueError(f"Unsupported event_type: {event_type or 'missing'}")
    lifecycle = str(request.get("lifecycle_state") or "detected").strip().lower()
    if lifecycle not in set(registry["lifecycle_states"]):
        raise ValueError(f"Unsupported lifecycle_state: {lifecycle}")
    severity_raw = request.get("severity")
    if isinstance(severity_raw, dict):
        severity_level = str(severity_raw.get("level") or "unknown").strip().lower()
        severity_source_value = severity_raw.get("source_value")
    else:
        severity_level = str(severity_raw or "unknown").strip().lower()
        severity_source_value = severity_raw if severity_raw not in (None, "") else None
    severity_ranks = _severity_map()
    if severity_level not in severity_ranks:
        raise ValueError(f"Unsupported severity level: {severity_level}")
    confidence = request.get("confidence")
    if confidence is not None:
        if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not 0 <= float(confidence) <= 1:
            raise ValueError("confidence must be between 0 and 1")
        confidence = float(confidence)
    source = request.get("source")
    if not isinstance(source, dict) or not str(source.get("source_id") or source.get("authority") or "").strip():
        raise ValueError("source must identify source_id or authority")
    feed_id = str(source.get("feed_id") or "").strip() or None
    if feed_id and feed_id not in _source_map():
        raise ValueError(f"Unknown live feed_id: {feed_id}")
    evidence_request = {
        "object_id": request.get("evidence_object_id") or request.get("event_id"),
        "layer_id": "live-events-hazards",
        "geometry": deepcopy(request.get("geometry")),
        "observed_at": request.get("observed_at"),
        "valid_time": deepcopy(request.get("valid_time") if isinstance(request.get("valid_time"), dict) else {}),
        "properties": {
            "event_type": event_type,
            "title": str(request.get("title") or "").strip() or None,
            "lifecycle_state": lifecycle,
            "severity": severity_level,
            **deepcopy(request.get("properties") if isinstance(request.get("properties"), dict) else {}),
        },
        "source": {
            "source_id": str(source.get("source_id") or source.get("authority") or "").strip(),
            "authority": str(source.get("authority") or source.get("source_id") or "").strip(),
            "record_id": str(source.get("record_id") or "").strip() or None,
            "url": str(source.get("url") or "").strip() or None,
            "license": str(source.get("license") or "").strip() or None,
            "retrieved_at": source.get("retrieved_at"),
        },
        "provenance": {
            **deepcopy(request.get("provenance") if isinstance(request.get("provenance"), dict) else {}),
            "transformations": list((request.get("provenance") or {}).get("transformations") or []) + ["live-event-to-v4.46-spatial-evidence"],
            "live_feed_id": feed_id,
        },
        "quality": deepcopy(request.get("quality") if isinstance(request.get("quality"), dict) else {}),
        "visibility": request.get("visibility") or "public",
    }
    evidence = normalize_evidence_object(evidence_request)
    observed_at = evidence.get("observed_at")
    updated_at = _iso(request.get("updated_at")) or observed_at
    correlation_keys = {str(value).strip() for value in (request.get("correlation_keys") or []) if str(value).strip()}
    if not isinstance(request.get("correlation_keys") or [], list):
        raise ValueError("correlation_keys must be a list")
    record_id = evidence["source"].get("record_id")
    if record_id:
        correlation_keys.add(f"source:{evidence['source']['source_id']}:{record_id}")
    normalized = {
        "schema": EVENT_SCHEMA,
        "version": APP_VERSION,
        "event_id": None,
        "event_type": event_type,
        "title": str(request.get("title") or "").strip() or None,
        "lifecycle_state": lifecycle,
        "severity": {"level": severity_level, "rank": severity_ranks[severity_level], "source_value": severity_source_value},
        "confidence": confidence,
        "geometry": deepcopy(evidence["geometry"]),
        "bbox": deepcopy(evidence["bbox"]),
        "crs": evidence["crs"],
        "observed_at": observed_at,
        "updated_at": updated_at,
        "valid_time": deepcopy(evidence["valid_time"]),
        "source": {**deepcopy(evidence["source"]), "feed_id": feed_id},
        "properties": deepcopy(request.get("properties") if isinstance(request.get("properties"), dict) else {}),
        "quality": deepcopy(request.get("quality") if isinstance(request.get("quality"), dict) else {}),
        "visibility": evidence["visibility"],
        "correlation_keys": [],
        "evidence_object": evidence,
        "provenance": {
            "normalization_contract": CONTRACT_VERSION,
            "source_adapter": str((request.get("provenance") or {}).get("source_adapter") or "canonical"),
            "transformations": list((request.get("provenance") or {}).get("transformations") or []),
            "impact_confirmed": False,
        },
    }
    normalized["correlation_keys"] = sorted(correlation_keys)
    normalized["correlation_keys"].append(_strict_fingerprint(normalized))
    normalized["correlation_keys"] = sorted(set(normalized["correlation_keys"]))
    basis = deepcopy(normalized)
    basis.pop("event_id", None)
    event_digest = _digest(basis)
    normalized["event_id"] = _safe_id(request.get("event_id"), "lge-" + event_digest.split(":", 1)[1][:24])
    normalized["content_digest"] = _digest({k: v for k, v in normalized.items() if k != "content_digest"})
    return normalized


def _epoch_ms_to_iso(value: Any) -> str | None:
    if value in (None, ""):
        return None
    try:
        return datetime.fromtimestamp(float(value) / 1000.0, tz=timezone.utc).isoformat()
    except (TypeError, ValueError, OSError) as exc:
        raise ValueError(f"Invalid epoch milliseconds: {value}") from exc


def _usgs_event(record: dict[str, Any]) -> dict[str, Any]:
    props = record.get("properties") if isinstance(record.get("properties"), dict) else {}
    geometry = record.get("geometry")
    mag = props.get("mag")
    severity = "unknown"
    if isinstance(mag, (int, float)) and not isinstance(mag, bool):
        severity = "minor" if mag < 4 else "moderate" if mag < 5.5 else "severe" if mag < 7 else "extreme"
    return normalize_event({
        "event_id": record.get("id"),
        "event_type": "earthquake",
        "title": props.get("title") or props.get("place"),
        "lifecycle_state": "updated" if props.get("updated") and props.get("updated") != props.get("time") else "active",
        "severity": {"level": severity, "source_value": mag},
        "geometry": geometry,
        "observed_at": _epoch_ms_to_iso(props.get("time")),
        "updated_at": _epoch_ms_to_iso(props.get("updated")),
        "properties": {"magnitude": mag, "place": props.get("place"), "status": props.get("status"), "tsunami": props.get("tsunami")},
        "source": {"feed_id": "usgs_earthquakes", "source_id": "usgs_earthquakes", "authority": "U.S. Geological Survey", "record_id": record.get("id"), "url": props.get("url")},
        "provenance": {"source_adapter": "usgs-geojson", "transformations": ["usgs-geojson-to-live-event"]},
    })


def _eonet_event(record: dict[str, Any]) -> dict[str, Any]:
    geometries = record.get("geometry") if isinstance(record.get("geometry"), list) else []
    if not geometries:
        raise ValueError("NASA EONET event has no geometry")
    latest = geometries[-1]
    categories = record.get("categories") if isinstance(record.get("categories"), list) else []
    cat = str((categories[0] if categories else {}).get("title") or "").lower()
    mapping = {"wildfires": "wildfire", "severe storms": "storm", "floods": "flood", "volcanoes": "volcano", "drought": "drought", "earthquakes": "earthquake"}
    event_type = next((etype for key, etype in mapping.items() if key in cat), "environmental-event")
    sources = record.get("sources") if isinstance(record.get("sources"), list) else []
    url = (sources[0] if sources else {}).get("url")
    return normalize_event({
        "event_id": record.get("id"), "event_type": event_type, "title": record.get("title"),
        "lifecycle_state": "resolved" if bool(record.get("closed")) else "active", "severity": "unknown",
        "geometry": {"type": latest.get("type"), "coordinates": latest.get("coordinates")},
        "observed_at": latest.get("date"), "updated_at": latest.get("date"),
        "properties": {"categories": [c.get("title") for c in categories], "closed": record.get("closed")},
        "source": {"feed_id": "nasa_eonet", "source_id": "nasa_eonet", "authority": "NASA EONET", "record_id": record.get("id"), "url": url},
        "provenance": {"source_adapter": "nasa-eonet-v3", "transformations": ["nasa-eonet-v3-to-live-event"]},
    })


def _noaa_event(record: dict[str, Any]) -> dict[str, Any]:
    props = record.get("properties") if isinstance(record.get("properties"), dict) else {}
    geometry = record.get("geometry")
    if not geometry:
        raise ValueError("NOAA/NWS alert requires geospatial geometry for fusion")
    source_severity = str(props.get("severity") or "unknown").strip().lower()
    sev_map = {"minor": "minor", "moderate": "moderate", "severe": "severe", "extreme": "extreme", "unknown": "unknown"}
    lifecycle = "resolved" if str(props.get("status") or "").lower() in {"cancelled", "expired"} else "active"
    return normalize_event({
        "event_id": record.get("id") or props.get("id"), "event_type": "weather-alert",
        "title": props.get("headline") or props.get("event"), "lifecycle_state": lifecycle,
        "severity": {"level": sev_map.get(source_severity, "unknown"), "source_value": props.get("severity")},
        "geometry": geometry, "observed_at": props.get("effective") or props.get("sent"), "updated_at": props.get("sent"),
        "valid_time": {"start": props.get("onset") or props.get("effective"), "end": props.get("expires") or props.get("ends")},
        "properties": {"event": props.get("event"), "urgency": props.get("urgency"), "certainty": props.get("certainty"), "area": props.get("areaDesc")},
        "source": {"feed_id": "noaa_nws", "source_id": "noaa_nws", "authority": "NOAA / National Weather Service", "record_id": record.get("id") or props.get("id"), "url": props.get("web") or props.get("@id")},
        "provenance": {"source_adapter": "noaa-nws-geojson", "transformations": ["noaa-nws-geojson-to-live-event"]},
    })


def normalize_source_event(request: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise ValueError("source event request must be a JSON object")
    feed_id = str(request.get("feed_id") or "").strip()
    record = request.get("record")
    if not isinstance(record, dict):
        raise ValueError("record must be a JSON object")
    if feed_id == "usgs_earthquakes":
        return _usgs_event(record)
    if feed_id == "nasa_eonet":
        return _eonet_event(record)
    if feed_id == "noaa_nws":
        return _noaa_event(record)
    if feed_id not in _source_map():
        raise ValueError(f"Unknown live feed_id: {feed_id or 'missing'}")
    canonical = deepcopy(record)
    canonical.setdefault("source", {})
    canonical["source"] = {**canonical["source"], "feed_id": feed_id, "source_id": canonical["source"].get("source_id") or feed_id}
    canonical.setdefault("provenance", {})
    canonical["provenance"] = {**canonical["provenance"], "source_adapter": "generic-with-required-geometry", "transformations": list(canonical["provenance"].get("transformations") or []) + ["generic-live-source-to-live-event"]}
    return normalize_event(canonical)


def _normalized_events(raw: Any) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        raise ValueError("events must be a list")
    if len(raw) > MAX_EVENTS:
        raise ValueError(f"events exceeds maximum of {MAX_EVENTS}")
    rows = []
    for item in raw:
        if isinstance(item, dict) and item.get("schema") == EVENT_SCHEMA and item.get("version") == APP_VERSION and item.get("content_digest"):
            rows.append(deepcopy(item))
        else:
            rows.append(normalize_event(item))
    return rows


def reconcile_events(request: dict[str, Any]) -> dict[str, Any]:
    events = _normalized_events((request or {}).get("events") or [])
    if not events:
        return {"ok": True, "version": APP_VERSION, "schema": EVENT_CLUSTER_SCHEMA, "cluster_count": 0, "clusters": [], "unmerged_event_count": 0}
    parent = list(range(len(events)))
    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)
    key_owner: dict[str, int] = {}
    for index, event in enumerate(events):
        for key in event.get("correlation_keys") or []:
            if key.startswith("source:"):
                continue
            if key in key_owner:
                union(index, key_owner[key])
            else:
                key_owner[key] = index
    groups: dict[int, list[dict[str, Any]]] = {}
    for i, event in enumerate(events):
        groups.setdefault(find(i), []).append(event)
    clusters = []
    for members in groups.values():
        members = sorted(members, key=lambda row: row["event_id"])
        source_digests = sorted(row["content_digest"] for row in members)
        common_keys = sorted(set.intersection(*(set(row["correlation_keys"]) for row in members))) if len(members) > 1 else []
        basis = {"source_event_digests": source_digests, "shared_correlation_keys": common_keys}
        cluster_digest = _digest(basis)
        clusters.append({
            "cluster_id": "lec-" + cluster_digest.split(":", 1)[1][:24],
            "cluster_digest": cluster_digest,
            "canonical_event_id": members[0]["event_id"],
            "event_count": len(members),
            "source_count": len({row["source"]["source_id"] for row in members}),
            "event_ids": [row["event_id"] for row in members],
            "source_event_digests": source_digests,
            "shared_correlation_keys": common_keys,
            "merge_basis": "shared-explicit-or-strict-deterministic-correlation-key" if len(members) > 1 else "no-merge",
        })
    clusters.sort(key=lambda row: row["cluster_id"])
    return {
        "ok": True, "version": APP_VERSION, "schema": EVENT_CLUSTER_SCHEMA,
        "cluster_count": len(clusters), "clusters": clusters,
        "merged_cluster_count": sum(1 for row in clusters if row["event_count"] > 1),
        "unmerged_event_count": sum(1 for row in clusters if row["event_count"] == 1),
        "identity_semantics": _registry()["identity_semantics"],
    }


def _freshness(event: dict[str, Any], as_of: str | None) -> dict[str, Any]:
    if not as_of:
        return {"state": "unknown", "age_minutes": None, "stale_after_minutes": None}
    analysis = _dt(_iso(as_of))
    observed = _dt(event.get("updated_at") or event.get("observed_at"))
    if analysis is None or observed is None:
        return {"state": "unknown", "age_minutes": None, "stale_after_minutes": None}
    age = (analysis - observed).total_seconds() / 60.0
    feed_id = event.get("source", {}).get("feed_id")
    source = _source_map().get(feed_id or "", {})
    stale_after = source.get("stale_after_minutes")
    if age < 0:
        state = "future-relative-to-analysis-time"
    elif stale_after is None:
        state = "age-known-threshold-unknown"
    else:
        state = "fresh" if age <= float(stale_after) else "stale"
    return {"state": state, "age_minutes": round(age, 3), "stale_after_minutes": stale_after}


def query_events(request: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise ValueError("event query request must be a JSON object")
    events = _normalized_events(request.get("events") or [])
    query = request.get("query") if isinstance(request.get("query"), dict) else {}
    event_types = {str(v).strip() for v in query.get("event_types") or [] if str(v).strip()}
    lifecycle = {str(v).strip() for v in query.get("lifecycle_states") or [] if str(v).strip()}
    min_rank = int(query.get("minimum_severity_rank") or 0)
    bbox = query.get("bbox")
    if bbox is not None:
        if not isinstance(bbox, list) or len(bbox) != 4:
            raise ValueError("query.bbox must be [west,south,east,north]")
        bbox = [float(v) for v in bbox]
    start = _dt(_iso(query.get("start"))) if query.get("start") else None
    end = _dt(_iso(query.get("end"))) if query.get("end") else None
    if start and end and end < start:
        raise ValueError("query.end must be on or after query.start")
    rows = []
    for event in events:
        if event_types and event["event_type"] not in event_types:
            continue
        if lifecycle and event["lifecycle_state"] not in lifecycle:
            continue
        if int(event["severity"]["rank"]) < min_rank:
            continue
        if bbox is not None and not _bbox_intersects(event["bbox"], bbox):
            continue
        event_start, event_end = _interval(event)
        if start and event_end and event_end < start:
            continue
        if end and event_start and event_start > end:
            continue
        row = deepcopy(event)
        row["freshness"] = _freshness(event, request.get("as_of"))
        rows.append(row)
    rows.sort(key=lambda row: (-int(row["severity"]["rank"]), str(row.get("observed_at") or ""), row["event_id"]), reverse=False)
    basis = {"event_digests": sorted(row["content_digest"] for row in rows), "query": query, "as_of": request.get("as_of")}
    result_digest = _digest(basis)
    return {
        "ok": True, "version": APP_VERSION, "schema": EVENT_QUERY_RESULT_SCHEMA,
        "result_id": "leq-" + result_digest.split(":", 1)[1][:24], "result_digest": result_digest,
        "count": len(rows), "events": rows, "query": deepcopy(query), "analysis_as_of": _iso(request.get("as_of")) if request.get("as_of") else None,
    }


def transition_event(request: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise ValueError("lifecycle transition request must be a JSON object")
    event = normalize_event(request.get("event") or {}) if (request.get("event") or {}).get("schema") != EVENT_SCHEMA else deepcopy(request["event"])
    new_state = str(request.get("new_state") or "").strip().lower()
    transitions = _registry()["lifecycle_transitions"]
    allowed = transitions.get(event["lifecycle_state"], [])
    if new_state not in allowed:
        raise ValueError(f"Invalid lifecycle transition: {event['lifecycle_state']} -> {new_state}")
    transitioned = deepcopy(event)
    transitioned["lifecycle_state"] = new_state
    transitioned["updated_at"] = _iso(request.get("transitioned_at")) or event.get("updated_at") or event.get("observed_at")
    transitioned["provenance"] = {**transitioned.get("provenance", {}), "lifecycle_transition": {"from": event["lifecycle_state"], "to": new_state, "reason": request.get("reason")}}
    transitioned.pop("content_digest", None)
    transitioned["content_digest"] = _digest(transitioned)
    return {
        "ok": True, "version": APP_VERSION, "schema": TRANSITION_SCHEMA,
        "from_state": event["lifecycle_state"], "to_state": new_state,
        "source_event_digest": event["content_digest"], "event": transitioned,
    }


def _evidence_objects(raw: Any) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        raise ValueError("objects must be a list")
    if len(raw) > MAX_EVIDENCE_OBJECTS:
        raise ValueError(f"objects exceeds maximum of {MAX_EVIDENCE_OBJECTS}")
    rows = []
    for item in raw:
        if isinstance(item, dict) and item.get("schema") == EVIDENCE_OBJECT_SCHEMA and item.get("version") == APP_VERSION and item.get("content_digest"):
            rows.append(deepcopy(item))
        else:
            rows.append(normalize_evidence_object(item))
    return rows


def fuse_layers(request: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise ValueError("layer fusion request must be a JSON object")
    events = _normalized_events(request.get("events") or [])
    objects = _evidence_objects(request.get("objects") or [])
    require_temporal = bool(request.get("require_temporal_overlap", False))
    layer_ids = {str(v).strip() for v in request.get("layer_ids") or [] if str(v).strip()}
    matches = []
    for event in events:
        for obj in objects:
            if obj["layer_id"] == "live-events-hazards":
                continue
            if layer_ids and obj["layer_id"] not in layer_ids:
                continue
            if not _bbox_intersects(event["bbox"], obj["bbox"]):
                continue
            temporal = _interval_overlaps(event, obj)
            if require_temporal and temporal is not True:
                continue
            basis = {"event_digest": event["content_digest"], "object_digest": obj["content_digest"], "spatial_relation": "intersects", "temporal_overlap": temporal}
            digest = _digest(basis)
            matches.append({
                "match_id": "lef-" + digest.split(":", 1)[1][:24], "match_digest": digest,
                "event_id": event["event_id"], "event_type": event["event_type"], "severity": deepcopy(event["severity"]),
                "object_id": obj["object_id"], "layer_id": obj["layer_id"], "domain": obj.get("domain"),
                "spatial_relation": "intersects", "temporal_overlap": temporal,
                "relationship_type": "potentially-exposed-to-event", "impact_confirmed": False,
                "source_content_digests": sorted([event["content_digest"], obj["content_digest"]]),
            })
            if len(matches) > MAX_FUSION_MATCHES:
                raise ValueError(f"fusion matches exceed maximum of {MAX_FUSION_MATCHES}")
    matches.sort(key=lambda row: (row["event_id"], row["layer_id"], row["object_id"]))
    by_layer: dict[str, int] = {}
    for row in matches:
        by_layer[row["layer_id"]] = by_layer.get(row["layer_id"], 0) + 1
    result_digest = _digest({"matches": [m["match_digest"] for m in matches], "require_temporal_overlap": require_temporal})
    return {
        "ok": True, "version": APP_VERSION, "schema": FUSION_RESULT_SCHEMA,
        "result_id": "lfr-" + result_digest.split(":", 1)[1][:24], "result_digest": result_digest,
        "event_count": len(events), "evidence_object_count": len(objects), "match_count": len(matches),
        "matches": matches, "layer_match_counts": dict(sorted(by_layer.items())),
        "semantics": {"spatial": "bounding-box-first", "impact_confirmed": False, "require_temporal_overlap": require_temporal},
    }


def _resolve_graph(request: dict[str, Any]) -> dict[str, Any]:
    graph = request.get("graph")
    if isinstance(graph, dict) and graph.get("schema") == GRAPH_SCHEMA and isinstance(graph.get("nodes"), list):
        return deepcopy(graph)
    build = request.get("graph_build")
    if isinstance(build, dict):
        return build_graph(build)
    raise ValueError("graph or graph_build is required")


def fuse_graph(request: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise ValueError("graph fusion request must be a JSON object")
    events = _normalized_events(request.get("events") or [])
    graph = _resolve_graph(request)
    require_temporal = bool(request.get("require_temporal_overlap", False))
    edges = []
    for event in events:
        for node in graph.get("nodes") or []:
            if not _bbox_intersects(event["bbox"], node.get("bbox")):
                continue
            temporal = _interval_overlaps(event, node)
            if require_temporal and temporal is not True:
                continue
            node_digest = node.get("content_digest")
            if not node_digest:
                continue
            basis = {"event_digest": event["content_digest"], "node_digest": node_digest, "relationship_type": "potentially-exposed-to-event", "temporal_overlap": temporal}
            digest = _digest(basis)
            edges.append({
                "fusion_edge_id": "lge-" + digest.split(":", 1)[1][:24], "fusion_edge_digest": digest,
                "source_node_id": node["node_id"], "target_event_id": event["event_id"],
                "relationship_type": "potentially-exposed-to-event", "directed": True,
                "spatial_relation": "intersects", "temporal_overlap": temporal,
                "impact_confirmed": False, "ephemeral": True,
                "source_content_digests": sorted([node_digest, event["content_digest"]]),
            })
            if len(edges) > MAX_FUSION_MATCHES:
                raise ValueError(f"fusion edges exceed maximum of {MAX_FUSION_MATCHES}")
    edges.sort(key=lambda row: (row["target_event_id"], row["source_node_id"]))
    result_digest = _digest({"graph_digest": graph.get("graph_digest"), "fusion_edges": [e["fusion_edge_digest"] for e in edges], "require_temporal_overlap": require_temporal})
    return {
        "ok": True, "version": APP_VERSION, "schema": GRAPH_FUSION_SCHEMA,
        "result_id": "lgf-" + result_digest.split(":", 1)[1][:24], "result_digest": result_digest,
        "source_graph_id": graph.get("graph_id"), "source_graph_digest": graph.get("graph_digest"),
        "event_count": len(events), "fusion_edge_count": len(edges), "fusion_edges": edges,
        "graph_mutated": False, "impact_confirmed": False,
        "semantics": {"spatial": "bounding-box-first", "relationship": "potentially-exposed-to-event", "require_temporal_overlap": require_temporal},
    }


def build_snapshot(request: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise ValueError("snapshot request must be a JSON object")
    query_request = {"events": request.get("events") or [], "query": request.get("query") or {}, "as_of": request.get("as_of")}
    queried = query_events(query_request)
    payload: dict[str, Any] = {
        "ok": True, "version": APP_VERSION, "schema": SNAPSHOT_SCHEMA,
        "analysis_as_of": queried.get("analysis_as_of"), "event_count": queried["count"], "events": queried["events"],
        "event_query_result_digest": queried["result_digest"],
    }
    if isinstance(request.get("objects"), list):
        payload["layer_fusion"] = fuse_layers({"events": queried["events"], "objects": request["objects"], "layer_ids": request.get("layer_ids") or [], "require_temporal_overlap": request.get("require_temporal_overlap", False)})
    if isinstance(request.get("graph"), dict) or isinstance(request.get("graph_build"), dict):
        payload["graph_fusion"] = fuse_graph({"events": queried["events"], "graph": request.get("graph"), "graph_build": request.get("graph_build"), "require_temporal_overlap": request.get("require_temporal_overlap", False)})
    basis = {
        "event_query_result_digest": queried["result_digest"],
        "layer_fusion_digest": (payload.get("layer_fusion") or {}).get("result_digest"),
        "graph_fusion_digest": (payload.get("graph_fusion") or {}).get("result_digest"),
    }
    payload["snapshot_digest"] = _digest(basis)
    payload["snapshot_id"] = "lgs-" + payload["snapshot_digest"].split(":", 1)[1][:24]
    payload["interpretation_boundary"] = "Spatial/temporal fusion identifies intersections and potential exposure only; it does not establish impact, damage, causality, or emergency guidance."
    return payload


def compatibility_contract() -> dict[str, Any]:
    return {
        "ok": True,
        "version": APP_VERSION,
        "contract_version": CONTRACT_VERSION,
        "v4_46_spatial_evidence": {"status": "preserved-and-consumed", "registry": "/public/spatial-evidence/registry", "event_layer": "live-events-hazards"},
        "v4_47_spatiotemporal": {"status": "preserved-and-consumed", "registry": "/public/spatiotemporal/registry", "semantics": "bounding-box-first-plus-explicit-time"},
        "v4_48_spatial_graph": {"status": "preserved-and-consumed", "registry": "/public/spatial-graph/registry", "graph_mutation": False},
        "v4_49": {"registry": "/public/live-geospatial/registry", "normalize": "/public/live-geospatial/events/normalize", "reconcile": "/public/live-geospatial/events/reconcile", "fuse_layers": "/public/live-geospatial/fuse/layers", "fuse_graph": "/public/live-geospatial/fuse/graph", "snapshot": "/public/live-geospatial/snapshot"},
        "migration_rule": "v4.49 consumes existing live-source records and canonical v4.46-v4.48 objects; it does not replace source collectors, mutate source evidence, or infer confirmed impacts from proximity.",
    }
