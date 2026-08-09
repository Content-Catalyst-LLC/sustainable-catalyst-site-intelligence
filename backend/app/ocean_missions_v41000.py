from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

from .version import APP_VERSION

VERSION = APP_VERSION
CONTRACT = "ocean-missions-vehicles-observatory-network"
ROUTE = "earth"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


SOURCES: dict[str, dict[str, Any]] = {
    "argo": {
        "title": "Argo observing network / Argovis access",
        "organization": "International Argo Program and contributing data centers",
        "url": "https://argo.ucsd.edu/data/",
        "api_url": "https://argovis.colorado.edu/",
        "recognized_hosts": ["argo.ucsd.edu", "argovis.colorado.edu", "argovis-api.colorado.edu"],
        "platform_types": ["float"],
        "scope": "Profiling-float identifiers, trajectories, cycles, profiles, and source-reported positions/metadata where supplied by the network or an approved access service.",
        "limitations": "A most-recent reported float position is not a verified current position. Surface fixes do not imply a continuous underwater trajectory between fixes.",
    },
    "ioos": {
        "title": "U.S. Integrated Ocean Observing System (IOOS)",
        "organization": "NOAA U.S. IOOS and regional associations",
        "url": "https://ioos.noaa.gov/data/access-ioos-data/",
        "api_url": "https://data.ioos.us/",
        "recognized_hosts": ["ioos.noaa.gov", "www.ioos.noaa.gov", "data.ioos.us"],
        "platform_types": ["glider", "buoy", "mooring", "fixed-observatory"],
        "scope": "Regional and national observing-system platform metadata and observations including gliders, buoys, moorings, and coastal stations where published.",
        "limitations": "IOOS aggregation spans multiple operators and update cadences. Registry presence does not prove a platform is currently operating or reporting.",
    },
    "onc": {
        "title": "Ocean Networks Canada Oceans 3.0",
        "organization": "Ocean Networks Canada",
        "url": "https://data.oceannetworks.ca/",
        "api_url": "https://data.oceannetworks.ca/OpenAPI",
        "recognized_hosts": ["data.oceannetworks.ca", "oceannetworks.ca", "www.oceannetworks.ca"],
        "platform_types": ["fixed-observatory", "camera-station", "hydrophone-station", "auv", "rov"],
        "scope": "Observatory deployments, devices, instruments, mobile platforms, cameras, hydrophones, and related source metadata where published in Oceans 3.0.",
        "limitations": "A deployment/device record does not establish current operational state. Media or sensor availability is evaluated separately from platform registration.",
    },
    "noaa-ocean-exploration": {
        "title": "NOAA Ocean Exploration",
        "organization": "NOAA Ocean Exploration / NCEI archives",
        "url": "https://oceanexplorer.noaa.gov/data/access-tools/",
        "api_url": "https://www.ncei.noaa.gov/",
        "recognized_hosts": ["oceanexplorer.noaa.gov", "www.oceanexplorer.noaa.gov", "ncei.noaa.gov", "www.ncei.noaa.gov"],
        "platform_types": ["research-vessel", "rov", "auv"],
        "scope": "Expedition, dive, navigation, vehicle, vessel, sensor, and archive metadata associated with NOAA-supported ocean exploration where published.",
        "limitations": "An archived expedition or dive track is historical evidence, not a live vehicle feed or current mission position.",
    },
}

PLATFORM_TYPES: dict[str, dict[str, str]] = {
    "float": {"title": "Profiling float", "motion": "drifting / profiling"},
    "glider": {"title": "Ocean glider", "motion": "mobile / piloted mission"},
    "buoy": {"title": "Buoy", "motion": "moored or drifting by source record"},
    "mooring": {"title": "Mooring", "motion": "fixed deployment"},
    "auv": {"title": "Autonomous underwater vehicle", "motion": "mobile mission"},
    "rov": {"title": "Remotely operated vehicle", "motion": "mobile tethered mission"},
    "research-vessel": {"title": "Research vessel", "motion": "mobile surface platform"},
    "fixed-observatory": {"title": "Fixed observatory", "motion": "fixed deployment"},
    "camera-station": {"title": "Underwater camera station", "motion": "fixed or source-defined"},
    "hydrophone-station": {"title": "Hydrophone station", "motion": "fixed or source-defined"},
}

MISSION_STATES = {
    "planned": "source reports planned",
    "deployed": "source reports deployed",
    "operating": "source reports operating",
    "recovered": "source reports recovered",
    "completed": "source reports completed",
    "inactive": "source reports inactive",
    "unknown": "source state unknown",
}

POSITION_KINDS = {
    "last-reported": "last source-reported position",
    "deployment": "deployment position",
    "recovery": "recovery position",
    "observation": "observation-associated position",
    "track-point": "source-reported track point",
}


def _source(source_id: str):
    sid = (source_id or "argo").strip().lower()
    if sid not in SOURCES:
        raise ValueError(f"unsupported ocean mission source: {sid}")
    return sid, {"id": sid, **SOURCES[sid]}


def _platform_type(value: str):
    key = (value or "float").strip().lower()
    if key not in PLATFORM_TYPES:
        raise ValueError(f"unsupported platform_type: {key}")
    return key, {"id": key, **PLATFORM_TYPES[key]}


def _point(latitude: Any, longitude: Any):
    if latitude in (None, "") and longitude in (None, ""):
        return None
    if latitude in (None, "") or longitude in (None, ""):
        raise ValueError("latitude and longitude must be provided together")
    lat, lon = float(latitude), float(longitude)
    if not -90 <= lat <= 90:
        raise ValueError("latitude must be between -90 and 90")
    if not -180 <= lon <= 180:
        raise ValueError("longitude must be between -180 and 180")
    return {"latitude": round(lat, 6), "longitude": round(lon, 6)}


def _depth(value: Any):
    if value in (None, ""):
        return None
    depth = float(value)
    if depth < 0 or depth > 11000:
        raise ValueError("depth_m must be between 0 and 11000")
    return round(depth, 3)


def _https_source_url(source: dict[str, Any], value: Any, field: str = "source_url"):
    raw = str(value or "").strip()
    parsed = urlparse(raw)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or host not in source["recognized_hosts"]:
        raise ValueError(f"{field} must use HTTPS and a registered source host")
    return raw


def _source_state(value: Any):
    state = str(value or "unknown").strip().lower()
    if state not in MISSION_STATES:
        raise ValueError(f"unsupported source_status: {state}")
    return state


def overview():
    payload = {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "route": ROUTE,
        "source_count": len(SOURCES),
        "platform_type_count": len(PLATFORM_TYPES),
        "summary": "Connect ocean floats, gliders, buoys, vehicles, vessels, and fixed observatories without fabricating current position, trajectory, deployment state, or live operation.",
        "truth_boundaries": [
            "A registry record does not prove a platform is currently operating.",
            "A last reported position is not a verified current position.",
            "Discrete source track points are not silently interpolated into a continuous trajectory.",
            "An archived ROV dive or vessel track is historical evidence, not a live vehicle feed.",
            "A planned or source-reported operating status remains source-attributed and time-bounded.",
            "A platform location is not inferred from a nearby observation, camera, hydrophone, or environmental record.",
            "Future position or trajectory is never predicted by this contract.",
        ],
        "generated_at": _now(),
    }
    payload["contract_sha256"] = _digest(payload)
    return payload


def catalog():
    return {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "sources": [{"id": key, **value} for key, value in SOURCES.items()],
        "platform_types": [{"id": key, **value} for key, value in PLATFORM_TYPES.items()],
        "mission_states": [{"id": key, "title": value} for key, value in MISSION_STATES.items()],
        "position_kinds": [{"id": key, "title": value} for key, value in POSITION_KINDS.items()],
        "generated_at": _now(),
    }


def state(
    source_id: str = "argo",
    platform_type: str = "float",
    platform_id: str = "",
    latitude: float | None = None,
    longitude: float | None = None,
    date: str = "",
):
    _, source = _source(source_id)
    type_id, type_row = _platform_type(platform_type)
    if type_id not in source["platform_types"]:
        # The selector may intentionally compare platform types across networks, but the
        # state contract must not imply source coverage where none is registered.
        source_supports_type = False
    else:
        source_supports_type = True
    query_point = _point(latitude, longitude)
    pid = str(platform_id or "").strip()[:200] or None
    day = str(date or "").strip() or None
    payload = {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "route": ROUTE,
        "mode": "ocean-missions-network",
        "source": source,
        "platform_type": type_row,
        "platform_id": pid,
        "query_point": query_point,
        "date": day,
        "source_supports_platform_type": source_supports_type,
        "evidence": {
            "platform_record_loaded": False,
            "mission_record_loaded": False,
            "position_record_loaded": False,
            "track_loaded": False,
            "operational_status_loaded": False,
        },
        "truth": {
            "current_position_verified": False,
            "current_operational_status_verified": False,
            "continuous_trajectory_verified": False,
            "future_trajectory_predicted": False,
            "nearby_observation_as_platform_position": False,
            "registry_presence_as_active_operation": False,
        },
        "generated_at": _now(),
    }
    payload["state_sha256"] = _digest(payload)
    return payload


def normalize_platform(request: dict[str, Any]):
    if not isinstance(request, dict):
        raise ValueError("request must be an object")
    sid, source = _source(str(request.get("source_id") or "argo"))
    type_id, type_row = _platform_type(str(request.get("platform_type") or "float"))
    if type_id not in source["platform_types"]:
        raise ValueError(f"platform_type {type_id} is not registered for source {sid}")
    source_url = _https_source_url(source, request.get("source_url"))
    platform_id = str(request.get("platform_id") or "").strip()
    if not platform_id:
        raise ValueError("platform_id is required")
    position = _point(request.get("latitude"), request.get("longitude"))
    position_time = str(request.get("position_time") or "").strip() or None
    if position and not position_time:
        raise ValueError("position_time is required when a source position is supplied")
    position_kind = str(request.get("position_kind") or "last-reported").strip().lower()
    if position and position_kind not in POSITION_KINDS:
        raise ValueError(f"unsupported position_kind: {position_kind}")
    source_status = _source_state(request.get("source_status"))
    status_time = str(request.get("status_time") or "").strip() or None
    record = {
        "platform_id": platform_id,
        "name": str(request.get("name") or "").strip() or None,
        "platform_type": type_row,
        "operator": str(request.get("operator") or "").strip() or None,
        "mission_id": str(request.get("mission_id") or "").strip() or None,
        "deployment_id": str(request.get("deployment_id") or "").strip() or None,
        "source_status": source_status,
        "status_time": status_time,
        "position": position,
        "position_time": position_time,
        "position_kind": position_kind if position else None,
        "depth_m": _depth(request.get("depth_m")),
        "source": {"id": sid, "title": source["title"], "url": source_url},
        "source_reported_status": source_status != "unknown",
        "source_reported_position": bool(position),
        "current_position_claimed": False,
        "current_operational_status_claimed": False,
        "trajectory_claimed": False,
        "network_response_independently_verified": False,
        "retrieved_at": str(request.get("retrieved_at") or "").strip() or _now(),
    }
    payload = {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "platform": record,
        "review": {
            "last_reported_position_recast_as_current": False,
            "source_status_recast_as_current": False,
            "registry_record_recast_as_active": False,
            "nearby_observation_recast_as_position": False,
        },
        "generated_at": _now(),
    }
    payload["platform_sha256"] = _digest(record)
    return payload


def normalize_mission(request: dict[str, Any]):
    if not isinstance(request, dict):
        raise ValueError("request must be an object")
    sid, source = _source(str(request.get("source_id") or "noaa-ocean-exploration"))
    source_url = _https_source_url(source, request.get("source_url"))
    mission_id = str(request.get("mission_id") or "").strip()
    if not mission_id:
        raise ValueError("mission_id is required")
    source_status = _source_state(request.get("source_status"))
    platforms = request.get("platform_ids") if isinstance(request.get("platform_ids"), list) else []
    platforms = [str(x).strip() for x in platforms if str(x).strip()]
    record = {
        "mission_id": mission_id,
        "title": str(request.get("title") or "").strip() or None,
        "operator": str(request.get("operator") or "").strip() or None,
        "platform_ids": platforms,
        "start_time": str(request.get("start_time") or "").strip() or None,
        "end_time": str(request.get("end_time") or "").strip() or None,
        "source_status": source_status,
        "status_time": str(request.get("status_time") or "").strip() or None,
        "objective": str(request.get("objective") or "").strip() or None,
        "source": {"id": sid, "title": source["title"], "url": source_url},
        "current_operation_claimed": False,
        "future_activity_claimed": False,
        "network_response_independently_verified": False,
        "retrieved_at": str(request.get("retrieved_at") or "").strip() or _now(),
    }
    payload = {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "mission": record,
        "review": {
            "historical_mission_recast_as_live": False,
            "source_status_recast_as_current": False,
            "planned_activity_recast_as_future_position": False,
        },
        "generated_at": _now(),
    }
    payload["mission_sha256"] = _digest(record)
    return payload


def normalize_track(request: dict[str, Any]):
    if not isinstance(request, dict):
        raise ValueError("request must be an object")
    sid, source = _source(str(request.get("source_id") or "argo"))
    source_url = _https_source_url(source, request.get("source_url"))
    platform_id = str(request.get("platform_id") or "").strip()
    track_id = str(request.get("track_id") or "").strip()
    if not platform_id or not track_id:
        raise ValueError("platform_id and track_id are required")
    raw_points = request.get("points")
    if not isinstance(raw_points, list) or not raw_points:
        raise ValueError("points must be a non-empty list")
    points = []
    for index, row in enumerate(raw_points):
        if not isinstance(row, dict):
            raise ValueError(f"points[{index}] must be an object")
        point = _point(row.get("latitude"), row.get("longitude"))
        timestamp = str(row.get("time") or "").strip()
        if point is None or not timestamp:
            raise ValueError(f"points[{index}] requires latitude, longitude, and time")
        points.append({
            "sequence": index,
            "point": point,
            "time": timestamp,
            "depth_m": _depth(row.get("depth_m")),
            "position_kind": str(row.get("position_kind") or "track-point").strip().lower(),
        })
        if points[-1]["position_kind"] not in POSITION_KINDS:
            raise ValueError(f"unsupported position_kind: {points[-1]['position_kind']}")
    record = {
        "track_id": track_id,
        "platform_id": platform_id,
        "points": points,
        "point_count": len(points),
        "source": {"id": sid, "title": source["title"], "url": source_url},
        "interpolation_applied": False,
        "continuous_path_claimed": False,
        "current_position_claimed": False,
        "future_trajectory_claimed": False,
        "network_response_independently_verified": False,
        "retrieved_at": str(request.get("retrieved_at") or "").strip() or _now(),
    }
    payload = {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "track": record,
        "review": {
            "points_interpolated": False,
            "last_point_recast_as_current": False,
            "track_extended_into_future": False,
        },
        "generated_at": _now(),
    }
    payload["track_sha256"] = _digest(record)
    return payload


def export_manifest(
    source_id: str = "argo",
    platform_type: str = "float",
    platform_id: str = "",
    latitude: float | None = None,
    longitude: float | None = None,
    date: str = "",
):
    current = state(source_id, platform_type, platform_id, latitude, longitude, date)
    payload = {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "schema": "sc-site-intelligence-ocean-missions-network/1.0",
        "state": current,
        "review": {
            "registry_presence_as_active": False,
            "last_reported_position_as_current": False,
            "discrete_points_as_continuous_trajectory": False,
            "future_position_predicted": False,
            "historical_track_as_live_feed": False,
        },
        "generated_at": _now(),
    }
    payload["manifest_sha256"] = _digest(payload)
    return payload


def readiness():
    checks = {
        "argo_registered": "argo" in SOURCES,
        "ioos_registered": "ioos" in SOURCES,
        "onc_registered": "onc" in SOURCES,
        "noaa_ocean_exploration_registered": "noaa-ocean-exploration" in SOURCES,
        "multiple_platform_classes": len(PLATFORM_TYPES) >= 10,
        "registry_not_active_status": True,
        "last_position_not_current_position": True,
        "track_points_not_continuous_trajectory": True,
        "historical_track_not_live_feed": True,
        "future_position_not_predicted": True,
        "nearby_observation_not_platform_position": True,
        "route_count_unchanged": True,
    }
    return {
        "ok": all(checks.values()),
        "version": VERSION,
        "contract": CONTRACT,
        "checks": checks,
        "summary": {
            "sources": len(SOURCES),
            "platform_types": len(PLATFORM_TYPES),
            "route": ROUTE,
            "public_route_count_delta": 0,
        },
        "generated_at": _now(),
    }
