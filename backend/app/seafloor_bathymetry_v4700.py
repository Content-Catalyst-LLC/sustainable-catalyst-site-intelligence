from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

from .version import APP_VERSION

VERSION = APP_VERSION
CONTRACT = "seafloor-bathymetric-intelligence"
ROUTE = "earth"
DEPTH_SIGN_CONVENTION = "positive-down-navigation; source elevation/depth semantics preserved"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


SOURCES: dict[str, dict[str, Any]] = {
    "gebco-2026": {
        "title": "GEBCO_2026 global bathymetry",
        "organization": "General Bathymetric Chart of the Oceans (GEBCO)",
        "url": "https://www.gebco.net/data-products/gridded-bathymetry-data",
        "api_url": "https://www.gebco.net/data-products/gebco-web-services/web-map-service",
        "recognized_hosts": ["gebco.net", "www.gebco.net", "download.gebco.net", "wms.gebco.net"],
        "coverage": "global ocean-and-land terrain grid; source type and underlying measurement density vary spatially",
        "machine_access": "GEBCO grid download/subset services and OGC Web Map Service",
        "evidence_types": ["global-gridded-bathymetry", "source-type-grid", "rendered-map-service"],
        "resolution": "15 arc-second global grid for GEBCO_2026; underlying measured-data resolution and density vary",
        "vertical_semantics": "grid elevations are source-product values; a gridded cell is not equivalent to an individual sounding",
        "limitations": "The global grid combines measured and estimated/interpolated terrain information. Grid spacing must not be represented as measurement spacing or positional accuracy.",
    },
    "emodnet-bathymetry": {
        "title": "EMODnet Bathymetry",
        "organization": "European Marine Observation and Data Network (EMODnet)",
        "url": "https://emodnet.ec.europa.eu/en/bathymetry",
        "api_url": "https://emodnet.ec.europa.eu/en/emodnet-web-service-documentation",
        "recognized_hosts": ["emodnet.ec.europa.eu", "ows.emodnet-bathymetry.eu", "tiles.emodnet-bathymetry.eu", "portal.emodnet-bathymetry.eu"],
        "coverage": "harmonised bathymetric Digital Terrain Model and related products for European sea regions",
        "machine_access": "OGC web services including WMS and other published EMODnet service endpoints",
        "evidence_types": ["regional-dtm", "survey-index", "source-reference", "rendered-map-service"],
        "resolution": "product- and region-specific; harmonised DTM resolution is not treated as the resolution of every contributing survey",
        "vertical_semantics": "DTM depth/elevation products are harmonised surfaces derived from heterogeneous source surveys",
        "limitations": "Source surveys differ in age, acquisition method, density, datum, and resolution. Harmonisation does not erase those differences.",
    },
    "noaa-ncei-bathymetry": {
        "title": "NOAA NCEI Bathymetry & Seafloor Mapping",
        "organization": "NOAA National Centers for Environmental Information",
        "url": "https://www.ncei.noaa.gov/products/bathymetry",
        "api_url": "https://www.ncei.noaa.gov/maps-and-geospatial-products",
        "recognized_hosts": ["ncei.noaa.gov", "www.ncei.noaa.gov", "ngdc.noaa.gov", "www.ngdc.noaa.gov", "gis.ngdc.noaa.gov"],
        "coverage": "archived multibeam, singlebeam, lidar, crowdsourced bathymetry, digital elevation models, and related seafloor holdings with dataset-specific spatial coverage",
        "machine_access": "NCEI catalog/search and GIS/REST services plus direct/archive access for registered holdings",
        "evidence_types": ["multibeam-survey", "singlebeam-survey", "lidar-bathymetry", "crowdsourced-bathymetry", "digital-elevation-model", "survey-footprint"],
        "resolution": "survey- and product-specific",
        "vertical_semantics": "individual sounding, survey mosaic, DEM, and catalog footprint records remain distinct evidence classes",
        "limitations": "Catalog presence or survey footprint does not imply uniform sounding density, modern acquisition, or verified depth at every point inside the footprint.",
    },
}

LAYERS: dict[str, dict[str, Any]] = {
    "bathymetric-elevation": {"title": "Bathymetric elevation / depth", "short": "DEPTH", "default_source": "gebco-2026", "sources": ["gebco-2026", "emodnet-bathymetry", "noaa-ncei-bathymetry"], "unit": "m", "note": "Source sign convention and vertical datum remain explicit; Site Intelligence does not silently flip elevation into depth."},
    "terrain-relief": {"title": "Seafloor terrain relief", "short": "RELIEF", "default_source": "gebco-2026", "sources": ["gebco-2026", "emodnet-bathymetry", "noaa-ncei-bathymetry"], "unit": "source-defined", "note": "Hillshade/relief is presentation derived from a terrain surface and is not an independent depth observation."},
    "source-type": {"title": "Grid source type / provenance class", "short": "SOURCE", "default_source": "gebco-2026", "sources": ["gebco-2026", "emodnet-bathymetry"], "unit": "categorical", "note": "Source-type products describe how terrain cells were constructed; they are not certainty scores."},
    "multibeam-coverage": {"title": "Multibeam survey coverage", "short": "MBES", "default_source": "noaa-ncei-bathymetry", "sources": ["noaa-ncei-bathymetry", "emodnet-bathymetry"], "unit": "coverage", "note": "A survey footprint establishes registered coverage, not continuous verified sounding density at every pixel."},
    "singlebeam-tracklines": {"title": "Singlebeam tracklines", "short": "SBES", "default_source": "noaa-ncei-bathymetry", "sources": ["noaa-ncei-bathymetry"], "unit": "trackline", "note": "Tracklines are acquisition paths, not continuous seafloor surfaces."},
    "lidar-bathymetry": {"title": "Bathymetric lidar", "short": "LIDAR", "default_source": "noaa-ncei-bathymetry", "sources": ["noaa-ncei-bathymetry"], "unit": "source-defined", "note": "Coastal lidar products have sensor-, water-clarity-, processing-, and vertical-datum limitations."},
    "crowdsourced-bathymetry": {"title": "Crowdsourced bathymetry", "short": "CSB", "default_source": "noaa-ncei-bathymetry", "sources": ["noaa-ncei-bathymetry"], "unit": "source-defined", "note": "Crowdsourced observations remain distinct from hydrographic survey products and global gridded terrain models."},
    "survey-footprints": {"title": "Survey & dataset footprints", "short": "FOOTPRINT", "default_source": "noaa-ncei-bathymetry", "sources": ["noaa-ncei-bathymetry", "emodnet-bathymetry"], "unit": "geometry", "note": "A footprint indicates a catalogued spatial extent; it does not assert data quality or point-level coverage."},
}

FEATURE_PRESETS = [
    {"id": "mid-ocean-ridge", "title": "Mid-ocean ridge", "claim": "morphologic orientation only until source terrain is loaded"},
    {"id": "trench", "title": "Ocean trench", "claim": "morphologic orientation only until source terrain is loaded"},
    {"id": "seamount", "title": "Seamount", "claim": "morphologic orientation only until source terrain is loaded"},
    {"id": "abyssal-plain", "title": "Abyssal plain", "claim": "morphologic orientation only until source terrain is loaded"},
    {"id": "continental-slope", "title": "Continental slope", "claim": "morphologic orientation only until source terrain is loaded"},
]


def _layer(layer_id: str):
    lid = (layer_id or "bathymetric-elevation").strip().lower()
    if lid not in LAYERS:
        raise ValueError(f"unsupported seafloor layer: {lid}")
    return lid, {"id": lid, **LAYERS[lid]}


def _source(source_id: str, layer: dict[str, Any] | None = None):
    sid = (source_id or (layer or {}).get("default_source") or "gebco-2026").strip().lower()
    if sid not in SOURCES:
        raise ValueError(f"unsupported seafloor source: {sid}")
    if layer and sid not in layer["sources"]:
        raise ValueError(f"source {sid} is not registered for {layer['id']}")
    return sid, {"id": sid, **SOURCES[sid]}


def _point(latitude: float, longitude: float):
    lat, lon = float(latitude), float(longitude)
    if not -90 <= lat <= 90:
        raise ValueError("latitude must be between -90 and 90")
    if not -180 <= lon <= 180:
        raise ValueError("longitude must be between -180 and 180")
    return {"latitude": round(lat, 6), "longitude": round(lon, 6)}


def _date(value: str | None):
    raw = (value or "").strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).date().isoformat()
    except ValueError as exc:
        raise ValueError("date must be ISO-8601 YYYY-MM-DD") from exc


def _query_plan(layer: dict[str, Any], source: dict[str, Any], point: dict[str, float], day: str | None):
    if source["id"] == "gebco-2026":
        return {
            "access_kind": "GEBCO grid / WMS discovery",
            "grid_release": "GEBCO_2026",
            "download_url": "https://download.gebco.net/",
            "wms_url": "https://wms.gebco.net/mapserv?",
            "point": point,
            "date": day,
            "automatic_cell_loaded": False,
            "note": "Resolve an explicit GEBCO grid cell or rendered WMS layer before displaying terrain. Grid spacing is not measurement spacing.",
        }
    if source["id"] == "emodnet-bathymetry":
        return {
            "access_kind": "EMODnet Bathymetry DTM / OGC service discovery",
            "catalogue_url": "https://emodnet.ec.europa.eu/en/bathymetry",
            "service_docs": "https://emodnet.ec.europa.eu/en/emodnet-web-service-documentation",
            "point": point,
            "date": day,
            "automatic_cell_loaded": False,
            "note": "Resolve the applicable DTM or survey/index service and preserve product resolution, source lineage, and datum metadata.",
        }
    return {
        "access_kind": "NOAA NCEI bathymetry survey/catalog discovery",
        "catalogue_url": "https://www.ncei.noaa.gov/products/bathymetry",
        "gis_services": "https://www.ncei.noaa.gov/maps-and-geospatial-products",
        "point": point,
        "date": day,
        "automatic_cell_loaded": False,
        "note": "Resolve an exact survey, DEM, sounding collection, or footprint before claiming depth or coverage. Catalog footprint alone is not a sounding.",
    }


def overview():
    p = {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "title": "Seafloor & Bathymetric Intelligence",
        "route": ROUTE,
        "source_count": len(SOURCES),
        "layer_count": len(LAYERS),
        "feature_preset_count": len(FEATURE_PRESETS),
        "summary": "Reach the seabed through source-bounded global/regional terrain models and survey archives while preserving whether a value is a grid cell, DEM, sounding, survey footprint, or presentation derivative.",
        "truth_boundaries": [
            "A bathymetric grid cell does not prove an individual sounding exists at that exact point.",
            "Grid spacing is not measurement spacing, positional accuracy, or uncertainty.",
            "Survey footprints do not prove uniform sounding density inside the footprint.",
            "Hillshade and terrain relief are presentation derivatives, not independent measurements.",
            "Depth/elevation sign convention and vertical datum are never silently converted.",
            "Measured, interpolated/estimated, harmonised, crowdsourced, and modeled terrain evidence remain distinct.",
            "No seafloor feature name or morphology is inferred from the local orientation drawing.",
        ],
        "generated_at": _now(),
    }
    p["contract_sha256"] = _digest(p)
    return p


def catalog():
    return {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "source_count": len(SOURCES),
        "layer_count": len(LAYERS),
        "sources": [{"id": k, **v} for k, v in SOURCES.items()],
        "layers": [{"id": k, **v} for k, v in LAYERS.items()],
        "feature_presets": FEATURE_PRESETS,
        "depth_sign_convention": DEPTH_SIGN_CONVENTION,
        "generated_at": _now(),
    }


def state(layer_id: str = "bathymetric-elevation", source_id: str = "", latitude: float = 0.0, longitude: float = 0.0, date: str = ""):
    _, layer = _layer(layer_id)
    _, source = _source(source_id, layer)
    point = _point(latitude, longitude)
    day = _date(date)
    p = {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "mode": "seafloor",
        "route": ROUTE,
        "layer": layer,
        "source": source,
        "point": point,
        "date": day,
        "terrain": {
            "value": None,
            "unit": layer["unit"],
            "vertical_datum": None,
            "source_resolution": None,
            "source_record_id": None,
            "source_type": None,
            "record_loaded": False,
            "point_coverage_verified": False,
            "individual_sounding_verified": False,
        },
        "query_plan": _query_plan(layer, source, point, day),
        "truth": {
            "terrain_fabricated": False,
            "grid_spacing_as_accuracy": False,
            "survey_footprint_as_point_measurement": False,
            "vertical_datum_converted": False,
            "depth_sign_converted": False,
            "hillshade_as_measurement": False,
            "measured_and_estimated_collapsed": False,
            "missing_replaced": False,
        },
        "generated_at": _now(),
    }
    p["state_sha256"] = _digest(p)
    return p


def normalize_sample(request: dict[str, Any]):
    if not isinstance(request, dict):
        raise ValueError("request must be an object")
    lid, layer = _layer(str(request.get("layer_id") or ""))
    sid, source = _source(str(request.get("source_id") or ""), layer)
    source_url = str(request.get("source_url") or "").strip()
    parsed = urlparse(source_url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or host not in source["recognized_hosts"]:
        raise ValueError("source_url must use HTTPS and a registered source host")
    evidence_type = str(request.get("evidence_type") or "").strip().lower()
    if evidence_type not in source["evidence_types"]:
        raise ValueError("evidence_type is not registered for this source")
    record_id = str(request.get("source_record_id") or "").strip()
    if not record_id:
        raise ValueError("source_record_id is required")
    point = _point(float(request.get("latitude")), float(request.get("longitude")))
    value = request.get("value")
    if value is not None and not isinstance(value, (int, float)):
        raise ValueError("value must be numeric or null")
    unit = str(request.get("unit") or layer["unit"]).strip()
    vertical_datum = str(request.get("vertical_datum") or "").strip() or None
    source_resolution = str(request.get("source_resolution") or "").strip() or None
    source_type = str(request.get("source_type") or "").strip() or None
    observed_at = str(request.get("observed_at") or "").strip() or None
    sample = {
        "source_record_id": record_id,
        "layer": {"id": lid, "title": layer["title"]},
        "source": {"id": sid, "title": source["title"], "url": source_url},
        "evidence_type": evidence_type,
        "point": point,
        "value": float(value) if value is not None else None,
        "unit": unit,
        "vertical_datum": vertical_datum,
        "source_resolution": source_resolution,
        "source_type": source_type,
        "observed_at": observed_at,
        "retrieved_at": str(request.get("retrieved_at") or "").strip() or _now(),
        "individual_sounding": evidence_type in {"multibeam-survey", "singlebeam-survey", "crowdsourced-bathymetry"} and bool(request.get("individual_sounding", False)),
        "network_response_independently_verified": False,
        "evidence_state": "source-attributed-not-network-verified",
        "sign_or_datum_conversion_performed": False,
    }
    p = {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "sample": sample,
        "review": {
            "source_domain_recognized": True,
            "value_fabricated": False,
            "vertical_datum_converted": False,
            "depth_sign_converted": False,
            "grid_resolution_recast_as_accuracy": False,
            "survey_footprint_recast_as_point_measurement": False,
        },
        "generated_at": _now(),
    }
    p["sample_sha256"] = _digest(sample)
    return p


def normalize_footprint(request: dict[str, Any]):
    if not isinstance(request, dict):
        raise ValueError("request must be an object")
    sid, source = _source(str(request.get("source_id") or "noaa-ncei-bathymetry"))
    source_url = str(request.get("source_url") or "").strip()
    parsed = urlparse(source_url)
    if parsed.scheme != "https" or (parsed.hostname or "").lower() not in source["recognized_hosts"]:
        raise ValueError("source_url must use HTTPS and a registered source host")
    fid = str(request.get("footprint_id") or "").strip()
    if not fid:
        raise ValueError("footprint_id is required")
    geometry = request.get("geometry")
    if not isinstance(geometry, dict) or geometry.get("type") not in {"Polygon", "MultiPolygon"} or not isinstance(geometry.get("coordinates"), list):
        raise ValueError("geometry must be GeoJSON Polygon or MultiPolygon")
    footprint = {
        "footprint_id": fid,
        "source": {"id": sid, "title": source["title"], "url": source_url},
        "dataset_id": str(request.get("dataset_id") or "").strip() or None,
        "survey_type": str(request.get("survey_type") or "").strip() or None,
        "geometry": geometry,
        "point_measurement_claimed": False,
        "uniform_density_claimed": False,
        "quality_claimed": False,
        "retrieved_at": str(request.get("retrieved_at") or "").strip() or _now(),
        "network_response_independently_verified": False,
    }
    p = {"ok": True, "version": VERSION, "contract": CONTRACT, "footprint": footprint, "generated_at": _now()}
    p["footprint_sha256"] = _digest(footprint)
    return p


def export_manifest(layer_id: str = "bathymetric-elevation", source_id: str = "", latitude: float = 0.0, longitude: float = 0.0, date: str = ""):
    current = state(layer_id, source_id, latitude, longitude, date)
    p = {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "schema": "sc-site-intelligence-seafloor-bathymetry/1.0",
        "state": current,
        "source_snapshot": {
            "id": current["source"]["id"],
            "title": current["source"]["title"],
            "url": current["source"]["url"],
            "coverage": current["source"]["coverage"],
            "resolution": current["source"]["resolution"],
            "vertical_semantics": current["source"]["vertical_semantics"],
            "limitations": current["source"]["limitations"],
        },
        "review": {
            "terrain_fabricated": False,
            "grid_spacing_as_accuracy": False,
            "survey_footprint_as_point_measurement": False,
            "vertical_datum_converted": False,
            "depth_sign_converted": False,
            "hillshade_as_measurement": False,
            "evidence_classes_collapsed": False,
        },
        "generated_at": _now(),
    }
    p["manifest_sha256"] = _digest(p)
    return p


def readiness():
    checks = {
        "sources_registered": len(SOURCES) >= 3,
        "layers_registered": len(LAYERS) >= 8,
        "global_bathymetry_registered": "gebco-2026" in SOURCES,
        "regional_dtm_registered": "emodnet-bathymetry" in SOURCES,
        "survey_archive_registered": "noaa-ncei-bathymetry" in SOURCES,
        "no_fake_terrain_value": True,
        "grid_spacing_not_accuracy": True,
        "footprint_not_point_measurement": True,
        "vertical_datum_not_silently_converted": True,
        "sign_convention_not_silently_converted": True,
        "presentation_relief_not_measurement": True,
        "measured_and_estimated_separated": True,
        "route_count_unchanged": True,
    }
    return {
        "ok": all(checks.values()),
        "version": VERSION,
        "contract": CONTRACT,
        "checks": checks,
        "summary": {"sources": len(SOURCES), "layers": len(LAYERS), "feature_presets": len(FEATURE_PRESETS), "route": ROUTE, "public_route_count_delta": 0},
        "generated_at": _now(),
    }
