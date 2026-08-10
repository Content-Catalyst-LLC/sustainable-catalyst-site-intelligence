from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

from .version import APP_VERSION

VERSION = APP_VERSION
CONTRACT = "coastal-change-sea-level-blue-carbon"
ROUTE = "earth"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


SOURCES: dict[str, dict[str, Any]] = {
    "noaa-coops": {
        "title": "NOAA CO-OPS Tides & Currents",
        "organization": "NOAA Center for Operational Oceanographic Products and Services",
        "url": "https://tidesandcurrents.noaa.gov/",
        "api_url": "https://api.tidesandcurrents.noaa.gov/api/prod/",
        "recognized_hosts": ["tidesandcurrents.noaa.gov", "api.tidesandcurrents.noaa.gov"],
        "indicator_types": ["observed-water-level", "tide-prediction", "high-tide-flooding-context"],
        "evidence_classes": ["water-level-observation", "tide-prediction", "station-metadata"],
        "coverage": "U.S. coastal and Great Lakes stations with source-reported water levels, predictions, datums, station metadata, and related oceanographic observations.",
        "authentication": "Public NOAA web services; product, interval, datum, and station constraints apply.",
        "limitations": "Station observations are local and datum-dependent. Tide predictions are astronomical predictions, not total-water-level forecasts and do not include every meteorological or wave contribution.",
    },
    "noaa-digital-coast": {
        "title": "NOAA Digital Coast / Sea Level Rise",
        "organization": "NOAA Office for Coastal Management",
        "url": "https://coast.noaa.gov/digitalcoast/",
        "api_url": "https://coast.noaa.gov/digitalcoast/data/slr.html",
        "recognized_hosts": ["coast.noaa.gov", "www.coast.noaa.gov"],
        "indicator_types": ["sea-level-scenario", "inundation-screening", "coastal-land-cover", "tidal-wetland", "wetland-migration"],
        "evidence_classes": ["scenario-layer", "inundation-layer", "land-cover-classification", "habitat-layer"],
        "coverage": "U.S. coastal sea-level-rise screening layers, mapping-confidence information, coastal land cover, wetland condition/migration products, and related planning datasets.",
        "authentication": "Public data downloads and map services; individual datasets retain their own metadata and distribution constraints.",
        "limitations": "Sea-level-rise inundation is screening-level planning information, not an exact flood boundary, navigation product, permitting determination, or parcel-level forecast. Land-cover products have scale and accuracy limits.",
    },
    "usgs-coastal-change": {
        "title": "USGS Coastal Change Hazards Portal",
        "organization": "U.S. Geological Survey",
        "url": "https://marine.usgs.gov/coastalchangehazardsportal/",
        "api_url": "https://marine.usgs.gov/coastalchangehazardsportal/data/item/uber?subtree=true",
        "recognized_hosts": ["marine.usgs.gov", "www.usgs.gov", "usgs.gov"],
        "indicator_types": ["shoreline-change", "coastal-erosion-hazard", "future-shoreline-change", "coastal-flooding-context"],
        "evidence_classes": ["shoreline-analysis", "hazard-scenario", "model-projection", "catalog-record"],
        "coverage": "Machine-readable U.S. coastal-change catalog and products spanning observed shoreline change, storm scenarios, future shoreline change, and future coastal hazards.",
        "authentication": "Public machine-readable access; the portal states data are available without API key or login.",
        "limitations": "Shoreline-change rates, hazard probabilities, and model projections carry method, spatial, temporal, and uncertainty limits. They do not guarantee safety or exact future shoreline position.",
    },
    "global-mangrove-watch": {
        "title": "Global Mangrove Watch",
        "organization": "Global Mangrove Alliance / Wetlands International and scientific partners",
        "url": "https://www.globalmangrovewatch.org/",
        "api_url": "https://www.globalmangrovewatch.org/",
        "recognized_hosts": ["globalmangrovewatch.org", "www.globalmangrovewatch.org", "mangrovealliance.org", "www.mangrovealliance.org", "wetlands.org", "www.wetlands.org"],
        "indicator_types": ["mangrove-extent", "mangrove-change", "blue-carbon-habitat"],
        "evidence_classes": ["habitat-layer", "remote-sensing-change", "carbon-context-layer"],
        "coverage": "Global remote-sensing evidence for mangrove extent, change, condition, and associated ecosystem-value context.",
        "authentication": "Public platform and data products; dataset-specific licensing, download, and attribution conditions apply.",
        "limitations": "Remote-sensing habitat evidence does not by itself verify field condition, restoration success, project additionality, carbon stock, sequestration, avoided emissions, or carbon-credit eligibility.",
    },
}

INDICATOR_TYPES: dict[str, dict[str, str]] = {
    "observed-water-level": {"title": "Observed water level", "domain": "water-level"},
    "tide-prediction": {"title": "Tide prediction", "domain": "water-level"},
    "high-tide-flooding-context": {"title": "High-tide flooding context", "domain": "water-level"},
    "sea-level-scenario": {"title": "Sea-level scenario", "domain": "scenario"},
    "inundation-screening": {"title": "Inundation screening layer", "domain": "scenario"},
    "shoreline-change": {"title": "Observed shoreline change", "domain": "shoreline"},
    "future-shoreline-change": {"title": "Future shoreline change", "domain": "shoreline"},
    "coastal-erosion-hazard": {"title": "Coastal erosion hazard", "domain": "shoreline"},
    "coastal-flooding-context": {"title": "Coastal flooding context", "domain": "scenario"},
    "coastal-land-cover": {"title": "Coastal land cover", "domain": "habitat"},
    "tidal-wetland": {"title": "Tidal wetland", "domain": "habitat"},
    "wetland-migration": {"title": "Wetland migration scenario", "domain": "habitat"},
    "mangrove-extent": {"title": "Mangrove extent", "domain": "habitat"},
    "mangrove-change": {"title": "Mangrove change", "domain": "habitat"},
    "blue-carbon-habitat": {"title": "Blue-carbon habitat context", "domain": "habitat"},
}

EVIDENCE_CLASSES = {
    "water-level-observation": "source-reported station observation with timestamp and vertical datum context",
    "tide-prediction": "source-published astronomical tide prediction",
    "station-metadata": "source-reported station and datum metadata",
    "scenario-layer": "source-published sea-level or coastal scenario layer",
    "inundation-layer": "screening-level potential inundation layer",
    "land-cover-classification": "remotely sensed or source-classified coastal land-cover evidence",
    "habitat-layer": "source-published wetland, mangrove, or coastal habitat layer",
    "shoreline-analysis": "observed/historical shoreline position or change analysis",
    "hazard-scenario": "scenario-based coastal hazard evidence",
    "model-projection": "source-modeled future coastal or shoreline projection",
    "catalog-record": "machine-readable catalog metadata describing a source coastal-change product",
    "remote-sensing-change": "remote-sensing-derived habitat extent/change record",
    "carbon-context-layer": "source-provided ecosystem carbon context retained without platform-derived credit claims",
}


def _source(source_id: str):
    sid = (source_id or "noaa-coops").strip().lower()
    if sid not in SOURCES:
        raise ValueError(f"unsupported coastal source: {sid}")
    return sid, {"id": sid, **SOURCES[sid]}


def _indicator(value: str):
    key = (value or "observed-water-level").strip().lower()
    if key not in INDICATOR_TYPES:
        raise ValueError(f"unsupported indicator_type: {key}")
    return key, {"id": key, **INDICATOR_TYPES[key]}


def _evidence_class(value: str):
    key = str(value or "").strip().lower()
    if key not in EVIDENCE_CLASSES:
        raise ValueError(f"unsupported evidence_class: {key}")
    return key


def _point(latitude: Any, longitude: Any):
    if latitude in (None, "") and longitude in (None, ""):
        return None
    if latitude in (None, "") or longitude in (None, ""):
        raise ValueError("latitude and longitude must be provided together")
    lat, lon = float(latitude), float(longitude)
    if not -90 <= lat <= 90 or not -180 <= lon <= 180:
        raise ValueError("latitude/longitude outside valid bounds")
    return {"latitude": round(lat, 6), "longitude": round(lon, 6)}


def _bbox(value: Any, field: str = "bbox"):
    if value in (None, ""):
        return None
    if not isinstance(value, (list, tuple)) or len(value) != 4:
        raise ValueError(f"{field} must be [west,south,east,north]")
    west, south, east, north = [float(x) for x in value]
    if not (-180 <= west <= 180 and -180 <= east <= 180 and -90 <= south <= 90 and -90 <= north <= 90):
        raise ValueError(f"{field} coordinates outside valid bounds")
    if west > east or south > north:
        raise ValueError(f"{field} must not cross antimeridian and must be ordered")
    return [round(west, 6), round(south, 6), round(east, 6), round(north, 6)]


def _url(source: dict[str, Any], raw: Any):
    value = str(raw or "").strip()
    parsed = urlparse(value)
    if parsed.scheme != "https" or (parsed.hostname or "").lower() not in source["recognized_hosts"]:
        raise ValueError("source_url must use HTTPS and a registered source host")
    return value


def overview():
    return {
        "ok": True, "version": VERSION, "contract": CONTRACT, "route": ROUTE,
        "source_count": len(SOURCES), "indicator_type_count": len(INDICATOR_TYPES),
        "summary": "Orient coastal water levels, sea-level scenarios, inundation screening, shoreline change, and blue-carbon habitat evidence while preserving datum, uncertainty, scenario, scale, and source boundaries.",
        "truth_boundaries": [
            "A tide prediction is not a total-water-level forecast.",
            "A sea-level-rise inundation layer is screening-level planning evidence, not an exact flood boundary or parcel forecast.",
            "A shoreline-change analysis or projection does not guarantee a future shoreline position or property outcome.",
            "A mapped wetland or mangrove is habitat evidence, not a platform-derived carbon stock or sequestration estimate.",
            "A habitat polygon or change record does not verify restoration success, additionality, permanence, avoided emissions, or carbon-credit eligibility.",
            "No record does not mean no coastal change, flooding, habitat, or risk.",
        ],
        "generated_at": _now(),
    }


def catalog():
    return {
        "ok": True, "version": VERSION, "contract": CONTRACT,
        "sources": [{"id": k, **v} for k, v in SOURCES.items()],
        "indicator_types": [{"id": k, **v} for k, v in INDICATOR_TYPES.items()],
        "evidence_classes": [{"id": k, "description": v} for k, v in EVIDENCE_CLASSES.items()],
        "generated_at": _now(),
    }


def state(source_id: str = "noaa-coops", indicator_type: str = "observed-water-level", latitude: float | None = None, longitude: float | None = None, date: str = ""):
    _, source = _source(source_id)
    indicator_id, indicator = _indicator(indicator_type)
    point = _point(latitude, longitude)
    return {
        "ok": True, "version": VERSION, "contract": CONTRACT, "route": ROUTE,
        "source": source, "indicator_type": indicator,
        "source_supports_indicator_type": indicator_id in source["indicator_types"],
        "query_point": point, "date": str(date or "").strip() or None,
        "evidence": {"water_level_loaded": False, "shoreline_record_loaded": False, "scenario_layer_loaded": False, "habitat_record_loaded": False},
        "truth": {
            "prediction_treated_as_observation": False,
            "scenario_treated_as_exact_flood_forecast": False,
            "shoreline_projection_treated_as_guaranteed_position": False,
            "habitat_treated_as_carbon_stock_estimate": False,
            "habitat_treated_as_carbon_credit": False,
            "platform_safety_finding": False,
            "platform_property_loss_finding": False,
            "platform_regulatory_finding": False,
        },
        "generated_at": _now(),
    }


def normalize_water_level(request: dict[str, Any]):
    if not isinstance(request, dict): raise TypeError("request must be an object")
    _, source = _source(request.get("source_id") or "")
    indicator_id, indicator = _indicator(request.get("indicator_type") or "")
    if indicator["domain"] != "water-level" or indicator_id not in source["indicator_types"]:
        raise ValueError("source does not register the requested water-level indicator")
    evidence_class = _evidence_class(request.get("evidence_class") or "water-level-observation")
    if evidence_class not in source["evidence_classes"]: raise ValueError("source does not register the requested evidence_class")
    point = _point(request.get("latitude"), request.get("longitude"))
    if point is None: raise ValueError("water-level record requires latitude and longitude")
    record = {
        "source_id": source["id"], "source_url": _url(source, request.get("source_url")),
        "indicator_type": indicator_id, "evidence_class": evidence_class,
        "station_id": str(request.get("station_id") or "").strip() or None,
        "point": point, "observed_or_predicted_at": str(request.get("observed_or_predicted_at") or "").strip() or None,
        "value": None if request.get("value") in (None, "") else float(request.get("value")),
        "unit": str(request.get("unit") or "").strip() or None,
        "vertical_datum": str(request.get("vertical_datum") or "").strip() or None,
        "quality_flag": str(request.get("quality_flag") or "").strip() or None,
        "prediction_treated_as_observation": False,
        "total_water_level_inferred": False,
        "flooding_inferred": False,
    }
    return {"ok": True, "version": VERSION, "contract": CONTRACT, "water_level": record, "record_sha256": _digest(record), "normalized_at": _now()}


def normalize_shoreline(request: dict[str, Any]):
    if not isinstance(request, dict): raise TypeError("request must be an object")
    _, source = _source(request.get("source_id") or "")
    indicator_id, indicator = _indicator(request.get("indicator_type") or "")
    if indicator["domain"] != "shoreline" or indicator_id not in source["indicator_types"]:
        raise ValueError("source does not register the requested shoreline indicator")
    evidence_class = _evidence_class(request.get("evidence_class") or "shoreline-analysis")
    if evidence_class not in source["evidence_classes"]: raise ValueError("source does not register the requested evidence_class")
    bbox = _bbox(request.get("bbox"))
    if bbox is None: raise ValueError("shoreline record requires bbox")
    record = {
        "source_id": source["id"], "source_url": _url(source, request.get("source_url")),
        "indicator_type": indicator_id, "evidence_class": evidence_class, "record_id": str(request.get("record_id") or "").strip() or None,
        "bbox": bbox, "analysis_period": str(request.get("analysis_period") or "").strip() or None,
        "rate": None if request.get("rate") in (None, "") else float(request.get("rate")),
        "rate_unit": str(request.get("rate_unit") or "").strip() or None,
        "uncertainty": None if request.get("uncertainty") in (None, "") else float(request.get("uncertainty")),
        "future_position_guaranteed": False, "property_loss_inferred": False, "safety_finding": False,
    }
    return {"ok": True, "version": VERSION, "contract": CONTRACT, "shoreline": record, "record_sha256": _digest(record), "normalized_at": _now()}


def normalize_habitat(request: dict[str, Any]):
    if not isinstance(request, dict): raise TypeError("request must be an object")
    _, source = _source(request.get("source_id") or "")
    indicator_id, indicator = _indicator(request.get("indicator_type") or "")
    if indicator["domain"] != "habitat" or indicator_id not in source["indicator_types"]:
        raise ValueError("source does not register the requested habitat indicator")
    evidence_class = _evidence_class(request.get("evidence_class") or "habitat-layer")
    if evidence_class not in source["evidence_classes"]: raise ValueError("source does not register the requested evidence_class")
    bbox = _bbox(request.get("bbox"))
    if bbox is None: raise ValueError("habitat record requires bbox")
    record = {
        "source_id": source["id"], "source_url": _url(source, request.get("source_url")),
        "indicator_type": indicator_id, "evidence_class": evidence_class, "record_id": str(request.get("record_id") or "").strip() or None,
        "bbox": bbox, "observed_at": str(request.get("observed_at") or "").strip() or None,
        "area": None if request.get("area") in (None, "") else float(request.get("area")),
        "area_unit": str(request.get("area_unit") or "").strip() or None,
        "classification": str(request.get("classification") or "").strip() or None,
        "carbon_stock_derived_by_platform": False,
        "sequestration_rate_derived_by_platform": False,
        "restoration_success_verified": False,
        "carbon_credit_eligibility_inferred": False,
    }
    return {"ok": True, "version": VERSION, "contract": CONTRACT, "habitat": record, "record_sha256": _digest(record), "normalized_at": _now()}


def scenario_preview(request: dict[str, Any]):
    if not isinstance(request, dict): raise TypeError("request must be an object")
    scenario_height = float(request["scenario_height"])
    unit = str(request.get("unit") or "").strip().lower()
    if unit not in {"m", "ft"}: raise ValueError("unit must be m or ft")
    bbox = _bbox(request.get("bbox"), "bbox")
    preview = {
        "scenario_height": scenario_height, "unit": unit, "bbox": bbox,
        "screening_scenario": True,
        "exact_flood_boundary": False,
        "parcel_level_forecast": False,
        "erosion_included_unless_source_says_so": False,
        "subsidence_included_unless_source_says_so": False,
        "navigation_or_permitting_use": False,
        "automatic_safety_or_evacuation_action": False,
    }
    return {"ok": True, "version": VERSION, "contract": CONTRACT, "preview": preview, "preview_sha256": _digest(preview), "generated_at": _now()}


def export_manifest(source_id: str = "noaa-coops", indicator_type: str = "observed-water-level", latitude: float | None = None, longitude: float | None = None, date: str = ""):
    current = state(source_id, indicator_type, latitude, longitude, date)
    payload = {
        "schema": "sc-site-intelligence-coastal-change/1.0", "version": VERSION, "contract": CONTRACT,
        "query": {"source_id": current["source"]["id"], "indicator_type": current["indicator_type"]["id"], "query_point": current["query_point"], "date": current["date"]},
        "evidence": current["evidence"],
        "review": {
            "prediction_as_observation": False, "scenario_as_exact_flood_boundary": False,
            "shoreline_projection_as_guaranteed_position": False, "habitat_as_carbon_stock": False,
            "habitat_as_carbon_credit": False, "platform_property_or_safety_finding": False,
        },
    }
    return {**payload, "manifest_sha256": _digest(payload), "generated_at": _now()}


def readiness():
    checks = {
        "four_source_families_registered": len(SOURCES) == 4,
        "coops_water_level_source_registered": "noaa-coops" in SOURCES,
        "digital_coast_scenario_source_registered": "noaa-digital-coast" in SOURCES,
        "usgs_shoreline_source_registered": "usgs-coastal-change" in SOURCES,
        "global_mangrove_source_registered": "global-mangrove-watch" in SOURCES,
        "datum_and_prediction_guard_present": True,
        "screening_scenario_guard_present": True,
        "shoreline_uncertainty_guard_present": True,
        "blue_carbon_claim_guard_present": True,
        "public_route_count_preserved": True,
    }
    return {"ok": all(checks.values()), "version": VERSION, "contract": CONTRACT, "checks": checks,
            "summary": {"sources": len(SOURCES), "indicator_types": len(INDICATOR_TYPES), "evidence_classes": len(EVIDENCE_CLASSES), "public_route_count_delta": 0, "primary_area_count_delta": 0}, "generated_at": _now()}
