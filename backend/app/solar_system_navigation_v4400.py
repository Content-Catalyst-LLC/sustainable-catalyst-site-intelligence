from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

from .version import APP_VERSION

VERSION = APP_VERSION
CONTRACT = "solar-system-navigation-mission-ephemeris"
ROUTE = "earth"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


BODIES: dict[str, dict[str, Any]] = {
    "sun": {"title": "Sun", "body_type": "star", "naif_id": 10, "display_orbit_index": 0, "orientation_au_approx": 0.0},
    "mercury": {"title": "Mercury", "body_type": "planet", "naif_id": 199, "display_orbit_index": 1, "orientation_au_approx": 0.39},
    "venus": {"title": "Venus", "body_type": "planet", "naif_id": 299, "display_orbit_index": 2, "orientation_au_approx": 0.72},
    "earth": {"title": "Earth", "body_type": "planet", "naif_id": 399, "display_orbit_index": 3, "orientation_au_approx": 1.0},
    "moon": {"title": "Moon", "body_type": "natural satellite", "naif_id": 301, "display_orbit_index": 4, "orientation_au_approx": 1.0, "parent": "earth"},
    "mars": {"title": "Mars", "body_type": "planet", "naif_id": 499, "display_orbit_index": 5, "orientation_au_approx": 1.52},
    "jupiter": {"title": "Jupiter", "body_type": "planet", "naif_id": 599, "display_orbit_index": 6, "orientation_au_approx": 5.20},
    "saturn": {"title": "Saturn", "body_type": "planet", "naif_id": 699, "display_orbit_index": 7, "orientation_au_approx": 9.54},
    "uranus": {"title": "Uranus", "body_type": "planet", "naif_id": 799, "display_orbit_index": 8, "orientation_au_approx": 19.19},
    "neptune": {"title": "Neptune", "body_type": "planet", "naif_id": 899, "display_orbit_index": 9, "orientation_au_approx": 30.07},
    "pluto": {"title": "Pluto", "body_type": "dwarf planet", "naif_id": 999, "display_orbit_index": 10, "orientation_au_approx": 39.48},
}

MISSIONS: dict[str, dict[str, Any]] = {
    "voyager-1": {"title": "Voyager 1", "mission_context": "outer-solar-system / interstellar mission context", "reference_body": "sun"},
    "voyager-2": {"title": "Voyager 2", "mission_context": "outer-solar-system / interstellar mission context", "reference_body": "sun"},
    "new-horizons": {"title": "New Horizons", "mission_context": "outer-solar-system mission context", "reference_body": "pluto"},
    "juno": {"title": "Juno", "mission_context": "Jupiter mission context", "reference_body": "jupiter"},
    "mars-reconnaissance-orbiter": {"title": "Mars Reconnaissance Orbiter", "mission_context": "Mars orbital mission context", "reference_body": "mars"},
    "lunar-reconnaissance-orbiter": {"title": "Lunar Reconnaissance Orbiter", "mission_context": "lunar orbital mission context", "reference_body": "moon"},
}

SERVICES = {
    "jpl-horizons": {
        "title": "JPL Horizons",
        "organization": "NASA Jet Propulsion Laboratory Solar System Dynamics",
        "url": "https://ssd.jpl.nasa.gov/horizons/app.html",
        "purpose": "solar-system ephemeris computation and object/spacecraft trajectory access",
        "recognized_hosts": ["ssd.jpl.nasa.gov"],
    },
    "naif-spice": {
        "title": "NAIF SPICE",
        "organization": "NASA Navigation and Ancillary Information Facility",
        "url": "https://naif.jpl.nasa.gov/naif/",
        "purpose": "mission geometry and kernel-based position, orientation, time, and instrument context",
        "recognized_hosts": ["naif.jpl.nasa.gov"],
    },
    "nasa-eyes": {
        "title": "NASA Eyes on the Solar System",
        "organization": "NASA / JPL",
        "url": "https://eyes.nasa.gov/apps/solar-system/",
        "purpose": "external exploratory 3D solar-system visualization",
        "recognized_hosts": ["eyes.nasa.gov"],
    },
}

FRAMES = {
    "J2000": "inertial equatorial frame label for an authoritative ephemeris request",
    "ECLIPJ2000": "ecliptic J2000 frame label for an authoritative ephemeris request",
    "BODY-FIXED": "body-fixed frame request; exact frame name must be resolved by the authoritative source",
}

OBSERVERS = {
    "solar-system-barycenter": "solar-system barycenter",
    "sun-center": "Sun center",
    "earth-center": "Earth center",
}


def _normalize_epoch(value: str | None) -> dict[str, Any]:
    raw = (value or "").strip()
    if not raw:
        return {"requested": False, "epoch_utc": None, "assumed_utc": False, "note": "No observation epoch selected locally."}
    candidate = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
    try:
        dt = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise ValueError("epoch must be ISO-8601 compatible") from exc
    assumed = dt.tzinfo is None
    if assumed:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return {
        "requested": True,
        "epoch_utc": dt.isoformat().replace("+00:00", "Z"),
        "assumed_utc": assumed,
        "note": "Naive browser datetime was interpreted as UTC." if assumed else "Timezone-aware epoch normalized to UTC.",
    }


def _body(body_id: str) -> tuple[str, dict[str, Any]]:
    bid = (body_id or "earth").lower()
    if bid not in BODIES:
        raise ValueError(f"unsupported solar-system body: {bid}")
    return bid, {"id": bid, **BODIES[bid]}


def _mission(mission_id: str | None) -> dict[str, Any] | None:
    mid = (mission_id or "").strip().lower()
    if not mid:
        return None
    if mid not in MISSIONS:
        raise ValueError(f"unsupported mission context: {mid}")
    return {"id": mid, **MISSIONS[mid], "authoritative_identifier_resolved": False}


def overview() -> dict[str, Any]:
    payload = {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "title": "Solar System Navigation & Mission Ephemeris",
        "route": ROUTE,
        "parent_contract": "astronomical-observation-environment",
        "body_count": len(BODIES),
        "mission_context_count": len(MISSIONS),
        "ephemeris_services": ["jpl-horizons", "naif-spice"],
        "exploration_handoff": "nasa-eyes",
        "summary": "Connect Earth, planetary, and astronomical observation through a solar-system navigation state while refusing to invent current body positions, spacecraft trajectories, or mission geometry.",
        "capabilities": [
            "solar-system destination catalog",
            "body and mission context selection",
            "explicit epoch, observer, and reference-frame request state",
            "JPL Horizons ephemeris handoff plan",
            "NAIF SPICE mission-geometry handoff",
            "NASA Eyes exploratory visualization handoff",
            "source-attributed ephemeris normalization",
            "reproducible navigation evidence manifest",
        ],
        "truth_boundaries": [
            "The local solar-system stage is an orientation diagram, not a computed ephemeris and not to scale.",
            "No current body position, spacecraft position, velocity, ground track, trajectory, or instrument pointing is invented.",
            "Selecting a time, frame, observer, body, or mission only prepares an ephemeris request until authoritative source data is supplied.",
            "A recognized JPL or NAIF source URL establishes source attribution, not independent verification of the returned numerical record.",
            "NASA Eyes is an external exploratory visualization handoff and is not used as the numerical ephemeris authority in this contract.",
        ],
        "generated_at": _now(),
    }
    payload["contract_sha256"] = _digest(payload)
    return payload


def catalog() -> dict[str, Any]:
    bodies = [{"id": bid, **row, "orientation_only": True} for bid, row in BODIES.items()]
    missions = [{"id": mid, **row, "current_position_embedded": False, "trajectory_embedded": False, "authoritative_identifier_resolved": False} for mid, row in MISSIONS.items()]
    services = [{"id": sid, **row} for sid, row in SERVICES.items()]
    return {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "body_count": len(bodies),
        "mission_context_count": len(missions),
        "service_count": len(services),
        "frames": [{"id": key, "description": value} for key, value in FRAMES.items()],
        "observers": [{"id": key, "title": value} for key, value in OBSERVERS.items()],
        "bodies": bodies,
        "missions": missions,
        "services": services,
        "generated_at": _now(),
    }


def body(body_id: str) -> dict[str, Any]:
    try:
        bid, row = _body(body_id)
    except ValueError:
        return {"ok": False, "version": VERSION, "contract": CONTRACT, "error": "unsupported solar-system body", "supported_bodies": list(BODIES)}
    payload = {"ok": True, "version": VERSION, "contract": CONTRACT, "body_id": bid, "body": row, "orientation_only": True, "generated_at": _now()}
    payload["body_sha256"] = _digest(payload)
    return payload


def mission(mission_id: str) -> dict[str, Any]:
    try:
        row = _mission(mission_id)
    except ValueError:
        return {"ok": False, "version": VERSION, "contract": CONTRACT, "error": "unsupported mission context", "supported_missions": list(MISSIONS)}
    payload = {"ok": True, "version": VERSION, "contract": CONTRACT, "mission_id": row["id"], "mission": row, "current_position_embedded": False, "generated_at": _now()}
    payload["mission_sha256"] = _digest(payload)
    return payload


def state(
    body_id: str = "earth",
    mission_id: str = "",
    epoch: str = "",
    frame: str = "J2000",
    observer: str = "solar-system-barycenter",
) -> dict[str, Any]:
    _, selected_body = _body(body_id)
    selected_mission = _mission(mission_id)
    frame_id = (frame or "J2000").upper()
    if frame_id not in FRAMES:
        raise ValueError(f"unsupported frame: {frame_id}")
    observer_id = (observer or "solar-system-barycenter").lower()
    if observer_id not in OBSERVERS:
        raise ValueError(f"unsupported observer: {observer_id}")
    epoch_state = _normalize_epoch(epoch)
    target = selected_mission["title"] if selected_mission else selected_body["title"]
    query_plan = {
        "target": target,
        "body_naif_id": selected_body["naif_id"],
        "mission_identifier": None if not selected_mission else "resolve-at-authoritative-source",
        "epoch_utc": epoch_state["epoch_utc"],
        "observer": observer_id,
        "reference_frame": frame_id,
        "requested_outputs": ["position", "velocity"],
        "numerical_result_loaded": False,
    }
    payload = {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "mode": "solar-system-navigation",
        "route": ROUTE,
        "body": selected_body,
        "mission": selected_mission,
        "time": epoch_state,
        "view": {
            "frame": frame_id,
            "observer": {"id": observer_id, "title": OBSERVERS[observer_id]},
            "local_stage": "illustrative orientation diagram",
            "not_to_scale": True,
        },
        "ephemeris": {
            "authoritative_solution_loaded": False,
            "position_vector": None,
            "velocity_vector": None,
            "trajectory_points": [],
            "current_position_claimed": False,
            "live_trajectory_claimed": False,
            "query_plan": query_plan,
            "authorities": [
                {"id": "jpl-horizons", "url": SERVICES["jpl-horizons"]["url"], "role": "ephemeris computation handoff"},
                {"id": "naif-spice", "url": SERVICES["naif-spice"]["url"], "role": "mission geometry / kernel handoff"},
            ],
        },
        "exploration": {"id": "nasa-eyes", "url": SERVICES["nasa-eyes"]["url"], "numerical_authority_for_this_contract": False},
        "truth": {
            "local_orbit_layout_is_ephemeris": False,
            "local_orbit_layout_is_to_scale": False,
            "spacecraft_position_fabricated": False,
            "body_position_fabricated": False,
            "trajectory_fabricated": False,
            "authoritative_ephemeris_required_for_numerical_position": True,
            "boundary": "The local stage preserves navigation intent only. Open or supply an authoritative JPL Horizons/NAIF SPICE record before treating any position, velocity, or trajectory as ephemeris evidence.",
        },
        "generated_at": _now(),
    }
    payload["state_sha256"] = _digest(payload)
    return payload


def normalize_ephemeris(request: dict[str, Any]) -> dict[str, Any]:
    source_kind = str(request.get("source_kind") or "").strip().lower()
    if source_kind not in {"jpl-horizons", "naif-spice"}:
        raise ValueError("source_kind must be jpl-horizons or naif-spice")
    source_url = str(request.get("source_url") or "").strip()
    parsed = urlparse(source_url)
    if parsed.scheme != "https" or parsed.hostname not in SERVICES[source_kind]["recognized_hosts"]:
        raise ValueError("source_url must use HTTPS and the registered authoritative source host")
    target_id = str(request.get("target_id") or "").strip().lower()
    if target_id in BODIES:
        target = {"kind": "body", "id": target_id, "title": BODIES[target_id]["title"]}
    elif target_id in MISSIONS:
        target = {"kind": "mission", "id": target_id, "title": MISSIONS[target_id]["title"]}
    else:
        raise ValueError("target_id must identify a registered body or mission context")
    epoch_state = _normalize_epoch(str(request.get("epoch") or ""))
    if not epoch_state["requested"]:
        raise ValueError("epoch is required for an ephemeris record")
    frame = str(request.get("frame") or "J2000").upper()
    if frame not in FRAMES:
        raise ValueError("unsupported frame")
    position = request.get("position")
    if not isinstance(position, list) or len(position) != 3 or any(not isinstance(v, (int, float)) for v in position):
        raise ValueError("position must contain exactly three numeric components")
    position_unit = str(request.get("position_unit") or "km").lower()
    if position_unit not in {"km", "au"}:
        raise ValueError("position_unit must be km or au")
    velocity = request.get("velocity")
    if velocity is not None and (not isinstance(velocity, list) or len(velocity) != 3 or any(not isinstance(v, (int, float)) for v in velocity)):
        raise ValueError("velocity must be absent or contain exactly three numeric components")
    velocity_unit = str(request.get("velocity_unit") or "km/s").lower()
    if velocity is not None and velocity_unit not in {"km/s", "au/day"}:
        raise ValueError("velocity_unit must be km/s or au/day")
    normalized = {
        "source_kind": source_kind,
        "source_title": SERVICES[source_kind]["title"],
        "source_url": source_url,
        "source_domain_recognized": True,
        "network_response_independently_verified": False,
        "target": target,
        "epoch_utc": epoch_state["epoch_utc"],
        "frame": frame,
        "observer": str(request.get("observer") or "unspecified"),
        "position": [float(v) for v in position],
        "position_unit": position_unit,
        "velocity": None if velocity is None else [float(v) for v in velocity],
        "velocity_unit": None if velocity is None else velocity_unit,
        "retrieved_at": str(request.get("retrieved_at") or "") or None,
        "source_record_id": str(request.get("source_record_id") or "") or None,
        "evidence_state": "source-attributed-not-network-verified",
    }
    payload = {"ok": True, "version": VERSION, "contract": CONTRACT, "ephemeris_record": normalized, "generated_at": _now()}
    payload["record_sha256"] = _digest(normalized)
    return payload


def export_manifest(body_id: str = "earth", mission_id: str = "", epoch: str = "", frame: str = "J2000", observer: str = "solar-system-barycenter") -> dict[str, Any]:
    current = state(body_id, mission_id, epoch, frame, observer)
    payload = {
        "ok": True,
        "version": VERSION,
        "schema": "sc-site-intelligence-solar-system-navigation/1.0",
        "contract": CONTRACT,
        "navigation_state": current,
        "review": {
            "ephemeris_fabricated": False,
            "trajectory_fabricated": False,
            "live_spacecraft_position_claimed": False,
            "illustrative_layout_disclosed": True,
            "authoritative_source_handoff_preserved": True,
            "human_interpretation_required": True,
        },
        "generated_at": _now(),
    }
    payload["manifest_sha256"] = _digest(current)
    return payload


def readiness() -> dict[str, Any]:
    checks = {
        "route_preserved": ROUTE == "earth",
        "solar_system_bodies_registered": len(BODIES) >= 10,
        "mission_contexts_registered": len(MISSIONS) >= 6,
        "jpl_horizons_registered": SERVICES["jpl-horizons"]["url"].startswith("https://ssd.jpl.nasa.gov/"),
        "naif_spice_registered": SERVICES["naif-spice"]["url"].startswith("https://naif.jpl.nasa.gov/"),
        "nasa_eyes_separate_from_numerical_authority": True,
        "no_fake_ephemeris": True,
        "no_fake_trajectory": True,
        "source_attribution_validator_present": True,
    }
    payload = {
        "ok": all(checks.values()),
        "version": VERSION,
        "contract": CONTRACT,
        "checks": checks,
        "summary": {"route": ROUTE, "bodies": len(BODIES), "missions": len(MISSIONS), "services": len(SERVICES)},
        "generated_at": _now(),
    }
    payload["readiness_sha256"] = _digest(payload)
    return payload
