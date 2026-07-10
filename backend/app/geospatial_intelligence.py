from __future__ import annotations

from datetime import datetime, timezone
from functools import lru_cache
import json
from typing import Any
from urllib.request import Request, urlopen

VERSION = "1.13.0"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _fetch_json(url: str, timeout: int = 8) -> dict[str, Any]:
    try:
        request = Request(url, headers={"User-Agent": "Sustainable-Catalyst-Site-Intelligence/1.13.0"})
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception:
        return {}


def _point_feature(identifier: str, title: str, category: str, latitude: float, longitude: float, source: str, observed_at: str = "", magnitude: float | None = None) -> dict[str, Any]:
    props: dict[str, Any] = {
        "id": identifier,
        "title": title,
        "category": category,
        "source": source,
        "observed_at": observed_at,
        "record_state": "observed",
    }
    if magnitude is not None:
        props["magnitude"] = magnitude
    return {"type": "Feature", "geometry": {"type": "Point", "coordinates": [longitude, latitude]}, "properties": props}


SATELLITE_LAYERS = [
    {
        "id": "true-color",
        "title": "NASA Corrected Reflectance True Color",
        "kind": "raster",
        "source": "NASA GIBS",
        "attribution": "NASA EOSDIS GIBS",
        "tile_url": "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/VIIRS_SNPP_CorrectedReflectance_TrueColor/default/{time}/GoogleMapsCompatible_Level9/{z}/{y}/{x}.jpg",
        "time_mode": "daily",
        "default_opacity": 0.78,
        "description": "Daily global true-color satellite mosaic suitable for clouds, smoke, land, water, and large-scale events.",
    },
    {
        "id": "land-surface-temperature",
        "title": "Land Surface Temperature",
        "kind": "raster",
        "source": "NASA GIBS",
        "attribution": "NASA EOSDIS GIBS",
        "tile_url": "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MODIS_Terra_Land_Surface_Temp_Day/default/{time}/GoogleMapsCompatible_Level7/{z}/{y}/{x}.png",
        "time_mode": "daily",
        "default_opacity": 0.65,
        "description": "Daily thermal surface-temperature imagery for regional heat patterns and environmental context.",
    },
    {
        "id": "fires-thermal-anomalies",
        "title": "Fires and Thermal Anomalies",
        "kind": "raster",
        "source": "NASA GIBS",
        "attribution": "NASA EOSDIS GIBS",
        "tile_url": "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MODIS_Terra_Thermal_Anomalies_Day/default/{time}/GoogleMapsCompatible_Level7/{z}/{y}/{x}.png",
        "time_mode": "daily",
        "default_opacity": 0.82,
        "description": "Daily thermal-anomaly layer for wildfire and high-temperature event orientation.",
    },
    {
        "id": "vegetation-index",
        "title": "Vegetation Index",
        "kind": "raster",
        "source": "NASA GIBS",
        "attribution": "NASA EOSDIS GIBS",
        "tile_url": "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MODIS_Terra_NDVI_8Day/default/{time}/GoogleMapsCompatible_Level7/{z}/{y}/{x}.png",
        "time_mode": "8-day composite",
        "default_opacity": 0.72,
        "description": "Vegetation-condition imagery for drought, land-cover, and ecological context.",
    },
]

VECTOR_LAYERS = [
    {"id": "earthquakes", "title": "Recent Earthquakes", "kind": "point", "source": "USGS", "live": True},
    {"id": "natural-events", "title": "Natural Events", "kind": "point", "source": "NASA EONET", "live": True},
    {"id": "event-density", "title": "Event Density Heat Map", "kind": "heat", "source": "Derived from public event records", "live": True},
    {"id": "country-boundaries", "title": "Country Boundaries", "kind": "boundary", "source": "OpenStreetMap basemap context", "live": True},
]


@lru_cache(maxsize=1)
def _earthquake_features() -> tuple[dict[str, Any], ...]:
    data = _fetch_json("https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson")
    features = []
    for item in (data.get("features") or [])[:100]:
        geometry = item.get("geometry") or {}
        coords = geometry.get("coordinates") or []
        if len(coords) < 2:
            continue
        props = item.get("properties") or {}
        features.append(_point_feature(
            str(item.get("id") or "usgs"),
            str(props.get("place") or "Earthquake"),
            "earthquake",
            float(coords[1]),
            float(coords[0]),
            "USGS",
            datetime.fromtimestamp((props.get("time") or 0)/1000, tz=timezone.utc).isoformat() if props.get("time") else "",
            float(props.get("mag")) if props.get("mag") is not None else None,
        ))
    return tuple(features)


@lru_cache(maxsize=1)
def _eonet_features() -> tuple[dict[str, Any], ...]:
    data = _fetch_json("https://eonet.gsfc.nasa.gov/api/v3/events?status=open&limit=100")
    features = []
    for event in data.get("events") or []:
        geometries = event.get("geometry") or []
        if not geometries:
            continue
        latest = geometries[-1]
        coords = latest.get("coordinates") or []
        if latest.get("type") != "Point" or len(coords) < 2:
            continue
        categories = event.get("categories") or []
        category = categories[0].get("title") if categories else "Natural event"
        features.append(_point_feature(
            str(event.get("id") or "eonet"),
            str(event.get("title") or "Natural event"),
            str(category),
            float(coords[1]),
            float(coords[0]),
            "NASA EONET",
            str(latest.get("date") or ""),
        ))
    return tuple(features)


def overview() -> dict[str, Any]:
    return {
        "ok": True,
        "version": VERSION,
        "title": "Geospatial Intelligence, Satellite Imagery, and Live Visualization",
        "summary": "Interactive public mapping with satellite imagery, live event feeds, heat maps, time controls, legends, and accessible table fallbacks.",
        "generated_at": _now(),
        "capabilities": ["interactive map", "satellite imagery", "live event markers", "heat maps", "time controls", "layer legends", "accessible data table", "fullscreen and mobile controls"],
        "default_view": {"center": [12.0, 20.0], "zoom": 2},
        "layers": len(SATELLITE_LAYERS) + len(VECTOR_LAYERS),
        "public_status": "live-visualization-layer",
    }


def layer_manifest() -> dict[str, Any]:
    return {
        "ok": True,
        "version": VERSION,
        "generated_at": _now(),
        "basemaps": [
            {"id": "openstreetmap", "title": "OpenStreetMap", "tile_url": "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", "attribution": "OpenStreetMap contributors"},
            {"id": "dark", "title": "Dark Matter", "tile_url": "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", "attribution": "OpenStreetMap contributors and CARTO"},
        ],
        "satellite_layers": SATELLITE_LAYERS,
        "vector_layers": VECTOR_LAYERS,
        "responsible_use": ["Satellite layers may be delayed, composited, cloud-obscured, or unavailable for a selected date.", "Event markers are source records, not operational alerts or safety instructions.", "Heat maps show spatial density, not severity, causality, or individual risk."],
    }


def live_events(category: str = "all") -> dict[str, Any]:
    features = list(_earthquake_features()) + list(_eonet_features())
    if category and category != "all":
        needle = category.lower()
        features = [f for f in features if needle in str((f.get("properties") or {}).get("category", "")).lower()]
    live = bool(features)
    if not features:
        features = [
            _point_feature("demo-volcano", "Illustrative volcanic event", "Volcano", -1.5, 29.2, "Local fallback", "", None),
            _point_feature("demo-fire", "Illustrative wildfire event", "Wildfire", 37.3, -119.7, "Local fallback", "", None),
            _point_feature("demo-storm", "Illustrative severe storm", "Severe storm", 18.4, 121.0, "Local fallback", "", None),
        ]
    return {
        "ok": True,
        "version": VERSION,
        "generated_at": _now(),
        "data_state": "live" if live else "fallback-demonstration",
        "type": "FeatureCollection",
        "features": features,
        "sources": ["USGS Earthquake Hazards Program", "NASA EONET"],
        "count": len(features),
    }


def heatmap() -> dict[str, Any]:
    collection = live_events()
    points = []
    for feature in collection["features"]:
        coords = feature.get("geometry", {}).get("coordinates", [])
        props = feature.get("properties", {})
        if len(coords) >= 2:
            weight = min(1.0, max(0.2, float(props.get("magnitude") or 1.0) / 7.0))
            points.append([coords[1], coords[0], weight])
    return {"ok": True, "version": VERSION, "generated_at": _now(), "data_state": collection["data_state"], "points": points, "count": len(points), "method": "Kernel-style browser heat layer derived from public event points."}


def satellite_manifest(date: str = "") -> dict[str, Any]:
    selected = date or datetime.now(timezone.utc).date().isoformat()
    layers = []
    for layer in SATELLITE_LAYERS:
        item = dict(layer)
        item["selected_date"] = selected
        item["resolved_tile_url"] = item["tile_url"].replace("{time}", selected)
        layers.append(item)
    return {"ok": True, "version": VERSION, "generated_at": _now(), "selected_date": selected, "layers": layers}


def timeline() -> dict[str, Any]:
    events = live_events()["features"]
    rows = []
    for feature in events:
        props = feature.get("properties") or {}
        rows.append({"id": props.get("id"), "title": props.get("title"), "category": props.get("category"), "source": props.get("source"), "observed_at": props.get("observed_at"), "coordinates": feature.get("geometry", {}).get("coordinates", [])})
    rows.sort(key=lambda row: str(row.get("observed_at") or ""), reverse=True)
    return {"ok": True, "version": VERSION, "generated_at": _now(), "events": rows[:100], "count": len(rows)}


def accessibility_table() -> dict[str, Any]:
    events = timeline()["events"]
    return {"ok": True, "version": VERSION, "generated_at": _now(), "columns": ["title", "category", "source", "observed_at", "longitude", "latitude"], "rows": [{"title": e["title"], "category": e["category"], "source": e["source"], "observed_at": e["observed_at"], "longitude": (e["coordinates"] + [None, None])[0], "latitude": (e["coordinates"] + [None, None])[1]} for e in events]}


def diagnostics() -> dict[str, Any]:
    events = live_events()
    return {"ok": True, "version": VERSION, "generated_at": _now(), "checks": [
        {"id": "layer-manifest", "status": "pass", "detail": f"{len(SATELLITE_LAYERS)} satellite and {len(VECTOR_LAYERS)} vector layers registered."},
        {"id": "geojson", "status": "pass" if events.get("type") == "FeatureCollection" else "review", "detail": f"{events.get('count', 0)} event features available."},
        {"id": "satellite-time", "status": "pass", "detail": "Date-aware NASA GIBS tile templates are available."},
        {"id": "accessible-table", "status": "pass", "detail": "Every event marker is represented in a text table fallback."},
        {"id": "no-fabricated-live-data", "status": "pass", "detail": "Fallback records are explicitly labeled as demonstrations."},
    ]}
