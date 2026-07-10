from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any

from .geospatial_intelligence import SATELLITE_LAYERS

VERSION = "1.18.0"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _iso_day(value: str | None, fallback_days: int = 1) -> str:
    if value:
        try:
            return date.fromisoformat(value).isoformat()
        except ValueError:
            pass
    return (datetime.now(timezone.utc).date() - timedelta(days=fallback_days)).isoformat()


ADDITIONAL_EARTH_LAYERS: list[dict[str, Any]] = [
    {
        "id": "precipitation-rate",
        "title": "Global Precipitation",
        "kind": "raster",
        "source": "NASA GIBS / GPM IMERG",
        "attribution": "NASA EOSDIS GIBS",
        "tile_url": "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/GPM_3IMERGHH_06_precipitation/default/{time}/GoogleMapsCompatible_Level6/{z}/{y}/{x}.png",
        "time_mode": "sub-daily composite",
        "default_opacity": 0.68,
        "temporal_resolution": "30 minutes to daily presentation",
        "spatial_resolution": "approximately 10 km",
        "observation_type": "satellite-derived precipitation estimate",
        "status": "experimental-public-layer",
        "description": "Precipitation intensity context for storms, flooding, drought interpretation, and recent weather patterns.",
        "limits": "Coverage, latency, and product availability vary by date. This is not an operational warning layer.",
    },
    {
        "id": "snow-cover",
        "title": "Snow Cover",
        "kind": "raster",
        "source": "NASA GIBS / MODIS",
        "attribution": "NASA EOSDIS GIBS",
        "tile_url": "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MODIS_Terra_Snow_Cover/default/{time}/GoogleMapsCompatible_Level8/{z}/{y}/{x}.png",
        "time_mode": "daily",
        "default_opacity": 0.72,
        "temporal_resolution": "daily",
        "spatial_resolution": "approximately 500 m",
        "observation_type": "satellite-derived snow classification",
        "status": "public-layer",
        "description": "Snow and ice context for seasonal coverage, mountain systems, hydrology, and cryosphere monitoring.",
        "limits": "Cloud cover and polar darkness can reduce visibility or produce gaps.",
    },
    {
        "id": "nighttime-lights",
        "title": "Nighttime Lights",
        "kind": "raster",
        "source": "NASA GIBS / VIIRS",
        "attribution": "NASA EOSDIS GIBS",
        "tile_url": "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/VIIRS_SNPP_DayNightBand_ENCC/default/{time}/GoogleMapsCompatible_Level8/{z}/{y}/{x}.png",
        "time_mode": "daily",
        "default_opacity": 0.74,
        "temporal_resolution": "daily composite",
        "spatial_resolution": "approximately 750 m",
        "observation_type": "low-light satellite radiance",
        "status": "experimental-public-layer",
        "description": "Nighttime illumination context for settlement patterns, infrastructure, outages, and human activity.",
        "limits": "Moonlight, clouds, fires, aurora, and atmospheric effects can influence apparent brightness.",
    },
    {
        "id": "aerosol-optical-depth",
        "title": "Atmospheric Aerosols",
        "kind": "raster",
        "source": "NASA GIBS / MODIS",
        "attribution": "NASA EOSDIS GIBS",
        "tile_url": "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MODIS_Terra_Aerosol/default/{time}/GoogleMapsCompatible_Level6/{z}/{y}/{x}.png",
        "time_mode": "daily",
        "default_opacity": 0.64,
        "temporal_resolution": "daily",
        "spatial_resolution": "regional atmospheric product",
        "observation_type": "satellite-derived aerosol optical depth",
        "status": "experimental-public-layer",
        "description": "Atmospheric aerosol context for smoke, dust, haze, and air-quality interpretation.",
        "limits": "This layer is not a ground-level pollution measurement and should not be used as a health alert.",
    },
]


def _enrich(layer: dict[str, Any]) -> dict[str, Any]:
    item = dict(layer)
    defaults = {
        "temporal_resolution": item.get("time_mode", "source dependent"),
        "spatial_resolution": "source and zoom dependent",
        "observation_type": "satellite observation or composite",
        "status": "public-layer",
        "limits": "Imagery may be delayed, composited, cloud-obscured, or unavailable for a selected date.",
    }
    for key, value in defaults.items():
        item.setdefault(key, value)
    return item


EARTH_LAYERS = [_enrich(item) for item in SATELLITE_LAYERS] + ADDITIONAL_EARTH_LAYERS


def overview() -> dict[str, Any]:
    return {
        "ok": True,
        "version": VERSION,
        "generated_at": _now(),
        "title": "Earth Observation Studio",
        "summary": "A visual workspace for satellite imagery, environmental layers, date comparison, timeline playback, metadata, and exportable public views.",
        "public_status": "flagship-visual-beta",
        "capabilities": [
            "single-date imagery",
            "before-and-after swipe comparison",
            "layer opacity",
            "timeline playback",
            "country and global views",
            "shareable URL state",
            "metadata and attribution",
            "PNG snapshot attempt",
            "print and JSON export",
        ],
        "default_layer": "true-color",
        "default_date": _iso_day(None, 1),
        "layer_count": len(EARTH_LAYERS),
    }


def layers() -> dict[str, Any]:
    return {
        "ok": True,
        "version": VERSION,
        "generated_at": _now(),
        "layers": EARTH_LAYERS,
        "responsible_use": [
            "Imagery layers may have different latency, coverage, temporal resolution, and spatial resolution.",
            "A visual difference between dates does not by itself establish cause.",
            "Thermal, precipitation, aerosol, and nighttime-light layers are interpretive context, not emergency instructions.",
            "Verify important observations against the originating source and relevant ground records.",
        ],
    }


def comparison(layer_id: str = "true-color", date_a: str = "", date_b: str = "") -> dict[str, Any]:
    layer = next((item for item in EARTH_LAYERS if item["id"] == layer_id), EARTH_LAYERS[0])
    left_date = _iso_day(date_a, 8)
    right_date = _iso_day(date_b, 1)
    return {
        "ok": True,
        "version": VERSION,
        "generated_at": _now(),
        "layer": layer,
        "left": {
            "date": left_date,
            "tile_url": layer["tile_url"].replace("{time}", left_date),
            "label": "Before",
        },
        "right": {
            "date": right_date,
            "tile_url": layer["tile_url"].replace("{time}", right_date),
            "label": "After",
        },
        "comparison_boundary": "The swipe view aligns two rendered source layers. Apparent change may reflect clouds, compositing, seasonal effects, sensor differences, product latency, or real-world change.",
    }


def timeline(layer_id: str = "true-color", end_date: str = "", days: int = 14) -> dict[str, Any]:
    layer = next((item for item in EARTH_LAYERS if item["id"] == layer_id), EARTH_LAYERS[0])
    end = date.fromisoformat(_iso_day(end_date, 1))
    safe_days = max(2, min(31, int(days)))
    frames = []
    for offset in range(safe_days - 1, -1, -1):
        selected = (end - timedelta(days=offset)).isoformat()
        frames.append({
            "date": selected,
            "tile_url": layer["tile_url"].replace("{time}", selected),
        })
    return {
        "ok": True,
        "version": VERSION,
        "generated_at": _now(),
        "layer": layer,
        "frame_count": len(frames),
        "frames": frames,
        "playback_note": "Playback advances requested dates. Source imagery may not exist for every frame or may represent a composite period.",
    }


def presets() -> dict[str, Any]:
    today = datetime.now(timezone.utc).date()
    return {
        "ok": True,
        "version": VERSION,
        "generated_at": _now(),
        "presets": [
            {"id": "recent-week", "title": "Recent week", "start": (today - timedelta(days=8)).isoformat(), "end": (today - timedelta(days=1)).isoformat()},
            {"id": "recent-month", "title": "Recent month", "start": (today - timedelta(days=31)).isoformat(), "end": (today - timedelta(days=1)).isoformat()},
            {"id": "seasonal-quarter", "title": "Seasonal quarter", "start": (today - timedelta(days=91)).isoformat(), "end": (today - timedelta(days=1)).isoformat()},
        ],
    }


def export_manifest(
    layer_id: str = "true-color",
    date_a: str = "",
    date_b: str = "",
    latitude: float = 12.0,
    longitude: float = 20.0,
    zoom: int = 2,
    opacity: float = 0.72,
) -> dict[str, Any]:
    comparison_payload = comparison(layer_id, date_a, date_b)
    return {
        "ok": True,
        "version": VERSION,
        "generated_at": _now(),
        "title": "Sustainable Catalyst Earth Observation View",
        "view": {
            "layer_id": comparison_payload["layer"]["id"],
            "layer_title": comparison_payload["layer"]["title"],
            "left_date": comparison_payload["left"]["date"],
            "right_date": comparison_payload["right"]["date"],
            "center": [latitude, longitude],
            "zoom": max(1, min(12, int(zoom))),
            "opacity": max(0.1, min(1.0, float(opacity))),
        },
        "source": comparison_payload["layer"]["source"],
        "attribution": comparison_payload["layer"]["attribution"],
        "observation_type": comparison_payload["layer"]["observation_type"],
        "limits": comparison_payload["layer"]["limits"],
        "comparison_boundary": comparison_payload["comparison_boundary"],
    }


def diagnostics() -> dict[str, Any]:
    checks = []
    for layer in EARTH_LAYERS:
        checks.append({
            "id": layer["id"],
            "title": layer["title"],
            "tile_template_present": "{time}" in layer["tile_url"],
            "https": layer["tile_url"].startswith("https://"),
            "attribution_present": bool(layer.get("attribution")),
            "limits_present": bool(layer.get("limits")),
            "status": layer.get("status", "unknown"),
        })
    return {
        "ok": True,
        "version": VERSION,
        "generated_at": _now(),
        "layer_count": len(checks),
        "layers": checks,
        "interaction_checks": {
            "broken_tile_state": "ready",
            "date_validation": "ready",
            "timeline_playback": "ready-with-stop-controls",
            "share_state_restore": "ready",
            "mobile_controls": "ready",
            "keyboard_controls": "ready",
            "print_view": "ready",
            "png_export": "browser-dependent",
        },
    }
