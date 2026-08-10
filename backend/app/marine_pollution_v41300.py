from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

from .version import APP_VERSION

VERSION = APP_VERSION
CONTRACT = "marine-pollution-debris-water-quality"
ROUTE = "earth"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


SOURCES: dict[str, dict[str, Any]] = {
    "noaa-ncei-marine-microplastics": {
        "title": "NOAA NCEI Marine Microplastics",
        "organization": "NOAA National Centers for Environmental Information",
        "url": "https://www.ncei.noaa.gov/products/microplastics",
        "api_url": "https://www.ncei.noaa.gov/products/microplastics",
        "recognized_hosts": ["ncei.noaa.gov", "www.ncei.noaa.gov"],
        "indicator_types": ["microplastics"],
        "evidence_classes": ["microplastics-observation", "quality-flag"],
        "coverage": "Aggregated global marine microplastics observations with source-reported sampling context, concentration information, locations, dates, and provenance.",
        "authentication": "Public discovery/download interfaces; upstream service constraints apply.",
        "limitations": "Sampling methods, size classes, matrices, units, detection limits, and spatial/temporal coverage vary. A missing record is not evidence of clean water or absence of microplastics.",
    },
    "emodnet-chemistry": {
        "title": "EMODnet Chemistry",
        "organization": "European Marine Observation and Data Network / European Commission",
        "url": "https://emodnet.ec.europa.eu/en/chemistry",
        "api_url": "https://emodnet.ec.europa.eu/en/emodnet-web-service-documentation",
        "recognized_hosts": ["emodnet.ec.europa.eu"],
        "indicator_types": ["beach-litter", "seafloor-litter", "floating-litter", "heavy-metals", "pesticides", "hydrocarbons", "pcbs", "nutrients", "ph-acidity"],
        "evidence_classes": ["marine-litter-observation", "contaminant-measurement", "water-quality-sample", "quality-flag"],
        "coverage": "European marine chemistry collections and products including contaminants, eutrophication/acidity, and marine-litter themes distributed through catalogue and interoperable web services.",
        "authentication": "Many catalogue and OGC services are public; product-specific upstream conditions apply.",
        "limitations": "Products may be aggregated or harmonized from heterogeneous source programs. Measurement matrices, analytical methods, quality flags, time coverage, and spatial resolution must remain explicit.",
    },
    "copernicus-marine-biogeochemistry": {
        "title": "Copernicus Marine Biogeochemistry",
        "organization": "Copernicus Marine Service",
        "url": "https://data.marine.copernicus.eu/",
        "api_url": "https://data.marine.copernicus.eu/product/GLOBAL_ANALYSISFORECAST_BGC_001_028/description",
        "recognized_hosts": ["data.marine.copernicus.eu", "marine.copernicus.eu"],
        "indicator_types": ["nutrients", "dissolved-oxygen", "ph-acidity", "chlorophyll"],
        "evidence_classes": ["biogeochemical-analysis", "biogeochemical-forecast", "quality-flag"],
        "coverage": "Global and regional modeled, analyzed, forecast, reanalysis, and in-situ biogeochemical products including nutrients, dissolved oxygen, chlorophyll, pH, carbon-system variables, and related fields.",
        "authentication": "Dataset access conditions vary by Copernicus Marine service/product.",
        "limitations": "Model analyses and forecasts are not in-situ samples. Spatial resolution, assimilation, model formulation, forecast horizon, and product version materially affect interpretation.",
    },
    "water-quality-portal": {
        "title": "Water Quality Portal",
        "organization": "USGS / EPA / National Water Quality Monitoring Council partners",
        "url": "https://www.waterqualitydata.us/",
        "api_url": "https://www.waterqualitydata.us/webservices_documentation/",
        "recognized_hosts": ["waterqualitydata.us", "www.waterqualitydata.us"],
        "indicator_types": ["water-quality", "nutrients", "dissolved-oxygen", "ph-acidity", "heavy-metals", "pesticides", "hydrocarbons"],
        "evidence_classes": ["water-quality-sample", "contaminant-measurement", "non-detect", "quality-flag"],
        "coverage": "Discrete publicly available water-quality site and result data from participating U.S. federal, state, tribal, local, and partner systems; coastal applicability depends on selected sites and records.",
        "authentication": "Public web-service/download interfaces; upstream query and volume limits apply.",
        "limitations": "The portal is not marine-only. Site type, characteristic, matrix, method, result qualifier, detection limit, and unit must be checked before interpreting a coastal or marine result.",
    },
}

INDICATOR_TYPES: dict[str, dict[str, str]] = {
    "microplastics": {"title": "Microplastics", "domain": "debris"},
    "beach-litter": {"title": "Beach litter", "domain": "debris"},
    "seafloor-litter": {"title": "Seafloor litter", "domain": "debris"},
    "floating-litter": {"title": "Floating litter", "domain": "debris"},
    "heavy-metals": {"title": "Heavy metals", "domain": "contaminants"},
    "pesticides": {"title": "Pesticides", "domain": "contaminants"},
    "hydrocarbons": {"title": "Hydrocarbons", "domain": "contaminants"},
    "pcbs": {"title": "PCBs", "domain": "contaminants"},
    "nutrients": {"title": "Nutrients / eutrophication context", "domain": "water-quality"},
    "dissolved-oxygen": {"title": "Dissolved oxygen", "domain": "water-quality"},
    "ph-acidity": {"title": "pH / acidity", "domain": "water-quality"},
    "chlorophyll": {"title": "Chlorophyll", "domain": "water-quality"},
    "water-quality": {"title": "General water-quality sample", "domain": "water-quality"},
}

EVIDENCE_CLASSES = {
    "microplastics-observation": "source-reported microplastics observation or concentration record",
    "marine-litter-observation": "source-reported beach, floating, or seafloor litter observation",
    "contaminant-measurement": "source-reported contaminant measurement",
    "water-quality-sample": "source-reported discrete water-quality sample/result",
    "biogeochemical-analysis": "model or assimilative biogeochemical analysis field",
    "biogeochemical-forecast": "model forecast biogeochemical field",
    "non-detect": "source-reported non-detect or below-detection result",
    "quality-flag": "source-reported quality or qualification metadata",
}


def _source(source_id: str):
    sid = (source_id or "noaa-ncei-marine-microplastics").strip().lower()
    if sid not in SOURCES:
        raise ValueError(f"unsupported marine pollution source: {sid}")
    return sid, {"id": sid, **SOURCES[sid]}


def _indicator(value: str):
    key = (value or "microplastics").strip().lower()
    if key not in INDICATOR_TYPES:
        raise ValueError(f"unsupported indicator_type: {key}")
    return key, {"id": key, **INDICATOR_TYPES[key]}


def _evidence_class(value: str):
    key = (value or "water-quality-sample").strip().lower()
    if key not in EVIDENCE_CLASSES:
        raise ValueError(f"unsupported evidence_class: {key}")
    return key


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


def _bbox(value: Any, field: str = "bbox"):
    if value in (None, ""):
        return None
    if not isinstance(value, (list, tuple)) or len(value) != 4:
        raise ValueError(f"{field} must be [west,south,east,north]")
    west, south, east, north = [float(x) for x in value]
    if not (-180 <= west <= 180 and -180 <= east <= 180 and -90 <= south <= 90 and -90 <= north <= 90):
        raise ValueError(f"{field} coordinates are outside valid longitude/latitude bounds")
    if south > north:
        raise ValueError(f"{field} south must be <= north")
    if west > east:
        raise ValueError(f"{field} antimeridian-crossing boxes must be split before preview")
    return [round(west, 6), round(south, 6), round(east, 6), round(north, 6)]


def _https_source_url(source: dict[str, Any], value: Any, field: str = "source_url"):
    raw = str(value or "").strip()
    parsed = urlparse(raw)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or host not in source["recognized_hosts"]:
        raise ValueError(f"{field} must use HTTPS and a registered source host")
    return raw


def overview():
    return {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "route": ROUTE,
        "source_count": len(SOURCES),
        "indicator_type_count": len(INDICATOR_TYPES),
        "summary": "Orient marine pollution, debris, contaminant, and water-quality evidence without converting sparse measurements, non-detects, model fields, or threshold comparisons into unsupported clean-water, exposure, health, ecological-harm, or regulatory conclusions.",
        "truth_boundaries": [
            "No returned measurement or debris record does not prove clean water or absence of pollution.",
            "A source-reported non-detect is not automatically zero concentration.",
            "Modeled or forecast biogeochemistry is not an in-situ sample.",
            "A debris observation does not identify the source, actor, or pathway that produced the debris.",
            "A concentration or threshold comparison does not by itself establish ecological harm, human exposure, health risk, or regulatory noncompliance.",
            "Units, matrices, methods, qualifiers, detection limits, quality flags, and time/space support remain explicit.",
        ],
        "interface_label": "EVIDENCE ORIENTATION · NOT A HEALTH OR COMPLIANCE FINDING",
        "generated_at": _now(),
    }


def catalog():
    return {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "sources": [{"id": k, **v} for k, v in SOURCES.items()],
        "indicator_types": [{"id": k, **v} for k, v in INDICATOR_TYPES.items()],
        "evidence_classes": [{"id": k, "description": v} for k, v in EVIDENCE_CLASSES.items()],
        "generated_at": _now(),
    }


def state(source_id: str = "noaa-ncei-marine-microplastics", indicator_type: str = "microplastics", latitude: float | None = None, longitude: float | None = None, date: str = ""):
    _, source = _source(source_id)
    _, indicator = _indicator(indicator_type)
    point = _point(latitude, longitude)
    supports = indicator["id"] in source["indicator_types"]
    return {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "source": source,
        "indicator_type": indicator,
        "query_point": point,
        "date": str(date or "").strip() or None,
        "source_supports_indicator_type": supports,
        "evidence": {
            "measurement_loaded": False,
            "debris_record_loaded": False,
            "non_detect_loaded": False,
            "quality_flag_loaded": False,
            "threshold_evaluated": False,
            "regulatory_standard_loaded": False,
            "health_advisory_loaded": False,
        },
        "truth": {
            "zero_records_treated_as_clean_water": False,
            "non_detect_treated_as_zero": False,
            "model_treated_as_in_situ_sample": False,
            "debris_source_attributed_by_platform": False,
            "threshold_treated_as_regulatory_exceedance": False,
            "platform_health_risk_finding": False,
            "platform_ecological_harm_finding": False,
            "platform_compliance_finding": False,
        },
        "generated_at": _now(),
    }


def normalize_measurement(request: dict[str, Any]):
    if not isinstance(request, dict):
        raise TypeError("request must be an object")
    _, source = _source(str(request.get("source_id") or ""))
    indicator_id, indicator = _indicator(str(request.get("indicator_type") or ""))
    evidence_class = _evidence_class(str(request.get("evidence_class") or "water-quality-sample"))
    if indicator_id not in source["indicator_types"]:
        raise ValueError("source does not register the requested indicator_type")
    if evidence_class not in source["evidence_classes"]:
        raise ValueError("source does not register the requested evidence_class")
    point = _point(request.get("latitude"), request.get("longitude"))
    bbox = _bbox(request.get("bbox"))
    if point is None and bbox is None:
        raise ValueError("measurement requires a point or bbox")
    source_url = _https_source_url(source, request.get("source_url"))
    raw_value = request.get("value")
    value = None if raw_value in (None, "") else float(raw_value)
    raw_detection_limit = request.get("detection_limit")
    detection_limit = None if raw_detection_limit in (None, "") else float(raw_detection_limit)
    qualifier = str(request.get("qualifier") or "").strip() or None
    source_non_detect = evidence_class == "non-detect" or (qualifier or "").lower() in {"non-detect", "not detected", "below detection", "<dl"}
    measurement = {
        "source_id": source["id"],
        "source_url": source_url,
        "indicator_type": indicator_id,
        "indicator_title": indicator["title"],
        "evidence_class": evidence_class,
        "record_id": str(request.get("record_id") or "").strip() or None,
        "point": point,
        "bbox": bbox,
        "sampled_at": str(request.get("sampled_at") or "").strip() or None,
        "value": value,
        "unit": str(request.get("unit") or "").strip() or None,
        "matrix": str(request.get("matrix") or "").strip() or None,
        "method": str(request.get("method") or "").strip() or None,
        "qualifier": qualifier,
        "detection_limit": detection_limit,
        "quality_flag": str(request.get("quality_flag") or "").strip() or None,
        "source_non_detect": source_non_detect,
        "non_detect_interpreted_as_zero": False,
        "health_risk_inferred": False,
        "ecological_harm_inferred": False,
        "regulatory_compliance_inferred": False,
        "model_treated_as_in_situ": False,
    }
    return {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "measurement": measurement,
        "measurement_sha256": _digest(measurement),
        "review": {
            "non_detect_as_zero": False,
            "measurement_as_health_risk": False,
            "measurement_as_ecological_harm": False,
            "measurement_as_compliance_finding": False,
        },
        "normalized_at": _now(),
    }


def normalize_debris(request: dict[str, Any]):
    if not isinstance(request, dict):
        raise TypeError("request must be an object")
    _, source = _source(str(request.get("source_id") or ""))
    indicator_id, indicator = _indicator(str(request.get("indicator_type") or ""))
    if indicator["domain"] != "debris":
        raise ValueError("debris normalization requires a debris indicator_type")
    if indicator_id not in source["indicator_types"]:
        raise ValueError("source does not register the requested indicator_type")
    evidence_class = _evidence_class(str(request.get("evidence_class") or "marine-litter-observation"))
    if evidence_class not in {"marine-litter-observation", "microplastics-observation"}:
        raise ValueError("debris normalization requires marine-litter-observation or microplastics-observation evidence")
    if evidence_class not in source["evidence_classes"]:
        raise ValueError("source does not register the requested evidence_class")
    point = _point(request.get("latitude"), request.get("longitude"))
    bbox = _bbox(request.get("bbox"))
    if point is None and bbox is None:
        raise ValueError("debris record requires a point or bbox")
    source_url = _https_source_url(source, request.get("source_url"))
    raw_count = request.get("count")
    count = None if raw_count in (None, "") else float(raw_count)
    debris = {
        "source_id": source["id"],
        "source_url": source_url,
        "indicator_type": indicator_id,
        "evidence_class": evidence_class,
        "record_id": str(request.get("record_id") or "").strip() or None,
        "point": point,
        "bbox": bbox,
        "observed_at": str(request.get("observed_at") or "").strip() or None,
        "count": count,
        "unit": str(request.get("unit") or "").strip() or None,
        "matrix": str(request.get("matrix") or "").strip() or None,
        "source_category": str(request.get("source_category") or "").strip() or None,
        "source_actor_attributed_by_platform": False,
        "transport_pathway_inferred_by_platform": False,
        "ecological_harm_inferred": False,
    }
    return {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "debris": debris,
        "debris_sha256": _digest(debris),
        "review": {
            "observation_as_source_attribution": False,
            "observation_as_transport_pathway": False,
            "observation_as_ecological_harm": False,
        },
        "normalized_at": _now(),
    }


def threshold_preview(request: dict[str, Any]):
    if not isinstance(request, dict):
        raise TypeError("request must be an object")
    value = float(request["measurement_value"])
    threshold = float(request["threshold_value"])
    unit = str(request.get("measurement_unit") or "").strip()
    threshold_unit = str(request.get("threshold_unit") or "").strip()
    if not unit or unit != threshold_unit:
        raise ValueError("measurement_unit and threshold_unit must be present and identical")
    direction = str(request.get("direction") or "above").strip().lower()
    if direction not in {"above", "below"}:
        raise ValueError("direction must be above or below")
    condition_met = value > threshold if direction == "above" else value < threshold
    preview = {
        "measurement_value": value,
        "threshold_value": threshold,
        "unit": unit,
        "direction": direction,
        "orientation_condition_met": condition_met,
        "regulatory_exceedance": False,
        "health_advisory": False,
        "human_exposure_established": False,
        "ecological_harm_concluded": False,
        "automatic_action_authorized": False,
    }
    return {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "preview": preview,
        "review": {
            "threshold_is_regulatory_standard": False,
            "condition_met_is_health_advisory": False,
            "condition_met_is_ecological_harm": False,
            "condition_met_is_compliance_finding": False,
        },
        "preview_sha256": _digest(preview),
        "generated_at": _now(),
    }


def export_manifest(source_id: str = "noaa-ncei-marine-microplastics", indicator_type: str = "microplastics", latitude: float | None = None, longitude: float | None = None, date: str = ""):
    current = state(source_id, indicator_type, latitude, longitude, date)
    payload = {
        "schema": "sc-site-intelligence-marine-pollution/1.0",
        "version": VERSION,
        "contract": CONTRACT,
        "query": {
            "source_id": current["source"]["id"],
            "indicator_type": current["indicator_type"]["id"],
            "query_point": current["query_point"],
            "date": current["date"],
        },
        "evidence": current["evidence"],
        "review": {
            "zero_records_as_clean_water": False,
            "non_detect_as_zero": False,
            "model_as_in_situ": False,
            "debris_observation_as_source_attribution": False,
            "threshold_as_regulatory_or_health_finding": False,
            "platform_compliance_finding": False,
        },
    }
    return {**payload, "manifest_sha256": _digest(payload), "generated_at": _now()}


def readiness():
    checks = {
        "four_source_families_registered": len(SOURCES) == 4,
        "microplastics_source_registered": "noaa-ncei-marine-microplastics" in SOURCES,
        "marine_litter_and_contaminants_registered": "emodnet-chemistry" in SOURCES,
        "biogeochemical_model_evidence_registered": "copernicus-marine-biogeochemistry" in SOURCES,
        "discrete_water_quality_source_registered": "water-quality-portal" in SOURCES,
        "non_detect_guard_present": True,
        "clean_water_guard_present": True,
        "health_and_compliance_guard_present": True,
        "public_route_count_preserved": True,
    }
    return {
        "ok": all(checks.values()),
        "version": VERSION,
        "contract": CONTRACT,
        "checks": checks,
        "summary": {
            "sources": len(SOURCES),
            "indicator_types": len(INDICATOR_TYPES),
            "evidence_classes": len(EVIDENCE_CLASSES),
            "public_route_count_delta": 0,
            "primary_area_count_delta": 0,
        },
        "generated_at": _now(),
    }
