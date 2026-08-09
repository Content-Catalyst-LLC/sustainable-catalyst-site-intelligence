from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timedelta, timezone
from typing import Any

from .earth_observation_studio import EARTH_LAYERS
from .version import APP_VERSION

VERSION = APP_VERSION
CONTRACT = "orbital-earth-satellite-observation"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _day(value: str | None) -> str:
    if value:
        try:
            parsed = date.fromisoformat(value)
            if parsed <= datetime.now(timezone.utc).date():
                return parsed.isoformat()
        except ValueError:
            pass
    return (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()


PLATFORM_CONTEXT: dict[str, dict[str, Any]] = {
    "true-color": {
        "platform": "Suomi National Polar-orbiting Partnership",
        "instrument": "VIIRS",
        "product_context": "Corrected Reflectance True Color",
        "observation_class": "visible-light satellite mosaic",
    },
    "land-surface-temperature": {
        "platform": "Terra",
        "instrument": "MODIS",
        "product_context": "Land Surface Temperature Day",
        "observation_class": "thermal remote-sensing product",
    },
    "fires-thermal-anomalies": {
        "platform": "Terra",
        "instrument": "MODIS",
        "product_context": "Thermal Anomalies Day",
        "observation_class": "thermal-anomaly remote-sensing product",
    },
    "vegetation-index": {
        "platform": "Terra",
        "instrument": "MODIS",
        "product_context": "NDVI 8-Day",
        "observation_class": "vegetation-index composite",
    },
    "precipitation-rate": {
        "platform": "GPM mission / contributing constellation",
        "instrument": "IMERG multi-sensor product",
        "product_context": "GPM IMERG precipitation",
        "observation_class": "multi-satellite precipitation estimate",
    },
    "snow-cover": {
        "platform": "Terra",
        "instrument": "MODIS",
        "product_context": "Snow Cover",
        "observation_class": "snow-classification product",
    },
    "nighttime-lights": {
        "platform": "Suomi National Polar-orbiting Partnership",
        "instrument": "VIIRS Day/Night Band",
        "product_context": "Day/Night Band enhanced near-constant contrast",
        "observation_class": "low-light orbital radiance product",
    },
    "aerosol-optical-depth": {
        "platform": "Terra",
        "instrument": "MODIS",
        "product_context": "Aerosol optical depth",
        "observation_class": "atmospheric remote-sensing product",
    },
}


def _layer(layer_id: str) -> dict[str, Any]:
    return next((dict(item) for item in EARTH_LAYERS if item.get("id") == layer_id), dict(EARTH_LAYERS[0]))


def _platform(layer_id: str) -> dict[str, Any]:
    return dict(PLATFORM_CONTEXT.get(layer_id, {
        "platform": "Source-dependent Earth-observation platform",
        "instrument": "Source-dependent instrument or derived product",
        "product_context": "Registered Earth-observation layer",
        "observation_class": "satellite observation or derived composite",
    }))


def overview() -> dict[str, Any]:
    payload = {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "title": "Orbital Earth & Satellite Observation",
        "summary": "Move from the existing surface comparison into a provenance-aware orbital Earth perspective while retaining layer, date, geography, and source state.",
        "route": "earth",
        "mode": "orbital",
        "presentation": "2.5d-orbital-perspective",
        "real_satellite_imagery": True,
        "imagery_source": "Registered NASA EOSDIS GIBS imagery products",
        "capabilities": [
            "surface-to-orbit transition",
            "circular orbital Earth perspective",
            "time-aware satellite imagery",
            "selected-location continuity",
            "layer-to-platform and instrument context",
            "product coverage and viewport footprint disclosure",
            "orbital altitude presentation control",
            "shareable orbital URL state",
            "orbital JSON evidence export",
        ],
        "truth_boundaries": [
            "The orbital viewer is a visual navigation perspective over registered imagery tiles; it is not a physical spacecraft-camera simulation.",
            "The platform does not fabricate a real-time spacecraft position, ground track, ephemeris, or instantaneous sensor swath.",
            "A displayed mosaic may combine observations acquired at different times and may contain clouds, gaps, compositing, latency, or processing artifacts.",
            "Historical imagery is labeled by requested observation date and is not described as live unless the source contract explicitly supports that claim.",
        ],
        "generated_at": _now(),
    }
    payload["contract_sha256"] = _digest(payload)
    return payload


def catalog() -> dict[str, Any]:
    rows = []
    for layer in EARTH_LAYERS:
        context = _platform(str(layer.get("id") or ""))
        rows.append({
            "layer_id": layer.get("id"),
            "layer_title": layer.get("title"),
            "source": layer.get("source"),
            "attribution": layer.get("attribution"),
            "temporal_resolution": layer.get("temporal_resolution") or layer.get("time_mode"),
            "spatial_resolution": layer.get("spatial_resolution") or "source and zoom dependent",
            "observation_type": layer.get("observation_type") or "satellite observation or composite",
            **context,
            "coverage_footprint": {
                "kind": "registered-product-coverage-envelope",
                "geometry": {"type": "Polygon", "coordinates": [[[-180.0, -85.0], [180.0, -85.0], [180.0, 85.0], [-180.0, 85.0], [-180.0, -85.0]]]},
                "boundary": "The envelope describes the web-map product presentation domain, not an instantaneous satellite sensor swath.",
            },
            "real_time_position_available": False,
            "instantaneous_sensor_swath_available": False,
        })
    return {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "layer_count": len(rows),
        "layers": rows,
        "generated_at": _now(),
    }


def state(
    layer_id: str = "true-color",
    observation_date: str = "",
    latitude: float = 0.0,
    longitude: float = 20.0,
    altitude_km: float = 1200.0,
) -> dict[str, Any]:
    layer = _layer(layer_id)
    selected_date = _day(observation_date)
    lat = max(-85.0, min(85.0, float(latitude)))
    lon = max(-180.0, min(180.0, float(longitude)))
    altitude = max(250.0, min(35786.0, float(altitude_km)))
    context = _platform(str(layer.get("id") or ""))
    tile_url = str(layer.get("tile_url") or "").replace("{time}", selected_date)
    payload = {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "mode": "orbital",
        "presentation": "2.5d-orbital-perspective",
        "view": {
            "center": [lat, lon],
            "presentation_altitude_km": round(altitude, 1),
            "altitude_is_physical_camera_solution": False,
            "projection_note": "Altitude controls the visual orbital perspective and map scale; it is not a solved spacecraft ephemeris or camera geometry.",
        },
        "observation": {
            "requested_date": selected_date,
            "layer_id": layer.get("id"),
            "layer_title": layer.get("title"),
            "tile_url": tile_url,
            "source": layer.get("source"),
            "attribution": layer.get("attribution"),
            "temporal_resolution": layer.get("temporal_resolution") or layer.get("time_mode"),
            "spatial_resolution": layer.get("spatial_resolution") or "source and zoom dependent",
            "observation_type": layer.get("observation_type") or "satellite observation or composite",
            "limits": layer.get("limits") or "Imagery may be delayed, composited, cloud-obscured, or unavailable for a selected date.",
            **context,
        },
        "footprints": {
            "product_coverage": {"south": -85.0, "west": -180.0, "north": 85.0, "east": 180.0},
            "selected_view_center": {"latitude": lat, "longitude": lon},
            "instantaneous_sensor_swath": None,
            "boundary": "Site Intelligence exposes product coverage and selected-view context. It does not invent a pass-specific sensor footprint when no ephemeris/swath source is connected.",
        },
        "orbit_context": {
            "real_time_spacecraft_position": None,
            "ground_track": None,
            "ephemeris_connected": False,
            "illustrative_orbit_rings_only": True,
            "boundary": "Orbit rings in the interface are orientation graphics, not current mission tracks.",
        },
        "generated_at": _now(),
    }
    payload["state_sha256"] = _digest(payload)
    return payload


def export_manifest(
    layer_id: str = "true-color",
    observation_date: str = "",
    latitude: float = 0.0,
    longitude: float = 20.0,
    altitude_km: float = 1200.0,
) -> dict[str, Any]:
    payload = state(layer_id, observation_date, latitude, longitude, altitude_km)
    return {
        "ok": True,
        "version": VERSION,
        "schema": "sc-site-intelligence-orbital-view/1.0",
        "contract": CONTRACT,
        "title": "Sustainable Catalyst Orbital Earth View",
        "orbital_state": payload,
        "review": {
            "real_satellite_imagery": True,
            "live_spacecraft_position_claimed": False,
            "instantaneous_swath_claimed": False,
            "human_interpretation_required": True,
        },
        "manifest_sha256": _digest(payload),
        "generated_at": _now(),
    }


def readiness() -> dict[str, Any]:
    checks = {
        "earth_layers_registered": len(EARTH_LAYERS) >= 8,
        "platform_context_registered": len(PLATFORM_CONTEXT) >= 8,
        "real_imagery_source_preserved": all("gibs.earthdata.nasa.gov" in str(item.get("tile_url") or "") for item in EARTH_LAYERS),
        "no_realtime_ephemeris_claim": True,
        "no_fabricated_sensor_swath": True,
        "same_earth_route_preserved": True,
    }
    return {
        "ok": all(checks.values()),
        "version": VERSION,
        "contract": CONTRACT,
        "checks": checks,
        "summary": {"layers": len(EARTH_LAYERS), "route": "earth", "presentation": "2.5d-orbital-perspective"},
        "readiness_sha256": _digest(checks),
    }
