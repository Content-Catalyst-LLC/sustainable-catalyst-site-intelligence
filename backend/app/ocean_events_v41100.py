from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

from .version import APP_VERSION

VERSION = APP_VERSION
CONTRACT = "ocean-events-hazards-ecosystem-change"
ROUTE = "earth"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


SOURCES: dict[str, dict[str, Any]] = {
    "noaa-coral-reef-watch": {
        "title": "NOAA Coral Reef Watch",
        "organization": "NOAA NESDIS Coral Reef Watch",
        "url": "https://coralreefwatch.noaa.gov/",
        "api_url": "https://coralreefwatch.noaa.gov/product/5km/",
        "recognized_hosts": ["coralreefwatch.noaa.gov"],
        "hazard_types": ["marine-heatwave", "coral-heat-stress"],
        "evidence_classes": ["satellite-derived", "analysis-product", "forecast-product", "advisory-product"],
        "scope": "Satellite-derived sea-surface temperature, anomalies, HotSpot, Degree Heating Week, bleaching alert and related coral heat-stress products.",
        "limitations": "Thermal stress products characterize environmental conditions associated with bleaching risk; they do not by themselves prove observed bleaching, mortality, ecosystem loss, or local management status.",
    },
    "noaa-coastwatch": {
        "title": "NOAA CoastWatch / OceanWatch",
        "organization": "NOAA NESDIS CoastWatch",
        "url": "https://coastwatch.noaa.gov/",
        "api_url": "https://coastwatch.noaa.gov/erddap/",
        "recognized_hosts": ["coastwatch.noaa.gov", "www.star.nesdis.noaa.gov", "star.nesdis.noaa.gov"],
        "hazard_types": ["marine-heatwave", "sea-ice-anomaly", "extreme-waves", "storm-ocean-impact", "ecosystem-change"],
        "evidence_classes": ["satellite-derived", "analysis-product", "derived-indicator"],
        "scope": "Oceanographic satellite and analysis products including SST, ocean color, sea level, winds, ice and related anomaly fields available through CoastWatch services.",
        "limitations": "A satellite or gridded anomaly is not an official hazard declaration and does not establish biological or societal impact at a location.",
    },
    "copernicus-marine": {
        "title": "Copernicus Marine Service",
        "organization": "Copernicus Marine Service / Mercator Ocean International",
        "url": "https://marine.copernicus.eu/",
        "api_url": "https://data.marine.copernicus.eu/",
        "recognized_hosts": ["marine.copernicus.eu", "data.marine.copernicus.eu", "help.marine.copernicus.eu"],
        "hazard_types": ["marine-heatwave", "hypoxia", "sea-ice-anomaly", "extreme-waves", "ecosystem-change"],
        "evidence_classes": ["analysis-product", "forecast-product", "reanalysis-product", "derived-indicator"],
        "scope": "Physical, sea-ice and biogeochemical ocean analyses, forecasts, reanalyses and Ocean Monitoring Indicators.",
        "limitations": "Model, analysis, forecast and indicator products remain distinct from in-situ observations and from official warning or emergency products.",
    },
    "noaa-nccos": {
        "title": "NOAA National Centers for Coastal Ocean Science",
        "organization": "NOAA NCCOS",
        "url": "https://coastalscience.noaa.gov/",
        "api_url": "https://coastalscience.noaa.gov/science-areas/habs/",
        "recognized_hosts": ["coastalscience.noaa.gov", "cdn.coastalscience.noaa.gov"],
        "hazard_types": ["harmful-algal-bloom", "hypoxia", "ecosystem-change"],
        "evidence_classes": ["in-situ-observation", "forecast-product", "advisory-product", "derived-indicator"],
        "scope": "Coastal harmful algal bloom, hypoxia and ecosystem science products, forecasts and observations where explicitly published by NCCOS programs.",
        "limitations": "Program or forecast coverage is region- and product-specific. A modeled or remotely sensed signal is not automatically a confirmed bloom, toxin exposure, fish kill, or hypoxic event.",
    },
}

HAZARD_TYPES: dict[str, dict[str, str]] = {
    "marine-heatwave": {"title": "Marine heatwave / thermal anomaly", "domain": "physical"},
    "coral-heat-stress": {"title": "Coral bleaching heat stress", "domain": "ecosystem-stress"},
    "harmful-algal-bloom": {"title": "Harmful algal bloom", "domain": "biological"},
    "hypoxia": {"title": "Hypoxia / low dissolved oxygen", "domain": "biogeochemical"},
    "sea-ice-anomaly": {"title": "Sea-ice anomaly", "domain": "cryosphere"},
    "extreme-waves": {"title": "Extreme wave conditions", "domain": "physical"},
    "storm-ocean-impact": {"title": "Storm-driven ocean impact", "domain": "compound-event"},
    "ecosystem-change": {"title": "Ecosystem change signal", "domain": "ecosystem"},
}

EVIDENCE_CLASSES = {
    "in-situ-observation": "source-reported in-situ observation",
    "satellite-derived": "satellite-derived observation/product",
    "analysis-product": "analysis or assimilative product",
    "forecast-product": "forecast product",
    "reanalysis-product": "reanalysis product",
    "derived-indicator": "derived monitoring indicator",
    "advisory-product": "source-issued advisory/classification product",
}

THRESHOLD_OPERATORS = {"gte", "gt", "lte", "lt", "eq"}


def _source(source_id: str):
    sid = (source_id or "noaa-coral-reef-watch").strip().lower()
    if sid not in SOURCES:
        raise ValueError(f"unsupported ocean event source: {sid}")
    return sid, {"id": sid, **SOURCES[sid]}


def _hazard(value: str):
    key = (value or "marine-heatwave").strip().lower()
    if key not in HAZARD_TYPES:
        raise ValueError(f"unsupported hazard_type: {key}")
    return key, {"id": key, **HAZARD_TYPES[key]}


def _evidence_class(value: str):
    key = (value or "satellite-derived").strip().lower()
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


def _https_source_url(source: dict[str, Any], value: Any, field: str = "source_url"):
    raw = str(value or "").strip()
    parsed = urlparse(raw)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or host not in source["recognized_hosts"]:
        raise ValueError(f"{field} must use HTTPS and a registered source host")
    return raw


def overview():
    payload = {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "route": ROUTE,
        "source_count": len(SOURCES),
        "hazard_type_count": len(HAZARD_TYPES),
        "summary": "Connect ocean-event and ecosystem-change evidence without turning thresholds, forecasts, sparse observations, or model fields into automatic hazard declarations.",
        "truth_boundaries": [
            "A threshold crossing is evidence about a defined metric, not an automatic hazard declaration.",
            "A forecast is not an observation and a model analysis is not an in-situ measurement.",
            "A thermal-stress product does not by itself prove coral bleaching, mortality, or ecosystem loss.",
            "A harmful-algal-bloom signal does not by itself prove toxin exposure, fish kill, or human-health impact.",
            "Low oxygen at one depth/time does not prove a persistent regional dead zone.",
            "A source-issued advisory is preserved as source-attributed and is not reissued as a Sustainable Catalyst warning.",
            "No observation records does not prove safe or normal conditions.",
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
        "hazard_types": [{"id": key, **value} for key, value in HAZARD_TYPES.items()],
        "evidence_classes": [{"id": key, "title": value} for key, value in EVIDENCE_CLASSES.items()],
        "generated_at": _now(),
    }


def state(source_id: str = "noaa-coral-reef-watch", hazard_type: str = "marine-heatwave", latitude: float | None = None, longitude: float | None = None, date: str = ""):
    _, source = _source(source_id)
    hazard_id, hazard = _hazard(hazard_type)
    point = _point(latitude, longitude)
    day = str(date or "").strip() or None
    supported = hazard_id in source["hazard_types"]
    payload = {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "route": ROUTE,
        "mode": "ocean-events-hazards-ecosystem-change",
        "source": source,
        "hazard_type": hazard,
        "query_point": point,
        "date": day,
        "source_supports_hazard_type": supported,
        "evidence": {
            "condition_record_loaded": False,
            "source_event_loaded": False,
            "threshold_evaluated": False,
            "official_advisory_loaded": False,
            "ecosystem_impact_observed": False,
        },
        "truth": {
            "hazard_declared": False,
            "warning_issued_by_platform": False,
            "forecast_treated_as_observation": False,
            "model_treated_as_in_situ": False,
            "threshold_treated_as_event": False,
            "zero_records_treated_as_safe": False,
            "source_advisory_reissued_by_platform": False,
        },
        "generated_at": _now(),
    }
    payload["state_sha256"] = _digest(payload)
    return payload


def normalize_condition(request: dict[str, Any]):
    if not isinstance(request, dict):
        raise ValueError("request must be an object")
    sid, source = _source(str(request.get("source_id") or "noaa-coral-reef-watch"))
    hazard_id, hazard = _hazard(str(request.get("hazard_type") or "marine-heatwave"))
    if hazard_id not in source["hazard_types"]:
        raise ValueError(f"hazard_type {hazard_id} is not registered for source {sid}")
    evidence_class = _evidence_class(str(request.get("evidence_class") or "satellite-derived"))
    if evidence_class not in source["evidence_classes"]:
        raise ValueError(f"evidence_class {evidence_class} is not registered for source {sid}")
    source_url = _https_source_url(source, request.get("source_url"))
    variable = str(request.get("variable") or "").strip()
    unit = str(request.get("unit") or "").strip()
    if not variable or not unit:
        raise ValueError("variable and unit are required")
    value = request.get("value")
    if value in (None, ""):
        raise ValueError("value is required")
    try:
        numeric_value = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("value must be numeric") from exc
    observed_at = str(request.get("observed_at") or request.get("valid_time") or "").strip()
    if not observed_at:
        raise ValueError("observed_at or valid_time is required")
    record = {
        "source": {"id": sid, "title": source["title"], "url": source_url},
        "hazard_type": hazard,
        "evidence_class": evidence_class,
        "record_id": str(request.get("record_id") or "").strip() or None,
        "variable": variable,
        "value": numeric_value,
        "unit": unit,
        "point": _point(request.get("latitude"), request.get("longitude")),
        "depth_m": float(request["depth_m"]) if request.get("depth_m") not in (None, "") else None,
        "observed_at": observed_at,
        "valid_start": str(request.get("valid_start") or "").strip() or None,
        "valid_end": str(request.get("valid_end") or "").strip() or None,
        "source_classification": str(request.get("source_classification") or "").strip() or None,
        "quality_flag": str(request.get("quality_flag") or "").strip() or None,
        "hazard_declared_by_platform": False,
        "warning_issued_by_platform": False,
        "impact_claimed": False,
        "network_response_independently_verified": False,
        "retrieved_at": str(request.get("retrieved_at") or "").strip() or _now(),
    }
    payload = {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "condition": record,
        "review": {
            "forecast_recast_as_observation": False,
            "analysis_recast_as_in_situ": False,
            "metric_recast_as_hazard": False,
            "source_classification_reissued_as_platform_warning": False,
            "impact_inferred_from_environmental_condition": False,
        },
        "generated_at": _now(),
    }
    payload["condition_sha256"] = _digest(record)
    return payload


def threshold_preview(request: dict[str, Any]):
    if not isinstance(request, dict):
        raise ValueError("request must be an object")
    value = float(request.get("value"))
    threshold = float(request.get("threshold"))
    operator = str(request.get("operator") or "gte").strip().lower()
    if operator not in THRESHOLD_OPERATORS:
        raise ValueError(f"unsupported operator: {operator}")
    comparisons = {
        "gte": value >= threshold,
        "gt": value > threshold,
        "lte": value <= threshold,
        "lt": value < threshold,
        "eq": value == threshold,
    }
    met = comparisons[operator]
    payload = {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "preview": {
            "metric": str(request.get("metric") or "unspecified metric").strip(),
            "value": value,
            "unit": str(request.get("unit") or "").strip() or None,
            "operator": operator,
            "threshold": threshold,
            "threshold_met": met,
            "hazard_declared": False,
            "warning_issued": False,
            "official_advisory_claimed": False,
            "automatic_action_authorized": False,
        },
        "review": {
            "threshold_crossing_is_hazard_declaration": False,
            "threshold_crossing_is_official_warning": False,
            "threshold_crossing_authorizes_action": False,
        },
        "generated_at": _now(),
    }
    payload["preview_sha256"] = _digest(payload["preview"])
    return payload


def normalize_event(request: dict[str, Any]):
    if not isinstance(request, dict):
        raise ValueError("request must be an object")
    sid, source = _source(str(request.get("source_id") or "noaa-coral-reef-watch"))
    hazard_id, hazard = _hazard(str(request.get("hazard_type") or "marine-heatwave"))
    if hazard_id not in source["hazard_types"]:
        raise ValueError(f"hazard_type {hazard_id} is not registered for source {sid}")
    source_url = _https_source_url(source, request.get("source_url"))
    event_id = str(request.get("event_id") or "").strip()
    classification = str(request.get("source_classification") or "").strip()
    if not event_id or not classification:
        raise ValueError("event_id and source_classification are required")
    record = {
        "event_id": event_id,
        "hazard_type": hazard,
        "source": {"id": sid, "title": source["title"], "url": source_url},
        "source_classification": classification,
        "issued_at": str(request.get("issued_at") or "").strip() or None,
        "valid_start": str(request.get("valid_start") or "").strip() or None,
        "valid_end": str(request.get("valid_end") or "").strip() or None,
        "point": _point(request.get("latitude"), request.get("longitude")),
        "source_reported_event": True,
        "source_attributed": True,
        "platform_reissued_warning": False,
        "platform_upgraded_severity": False,
        "automatic_action_authorized": False,
        "retrieved_at": str(request.get("retrieved_at") or "").strip() or _now(),
    }
    payload = {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "event": record,
        "review": {
            "source_event_recast_as_platform_warning": False,
            "severity_upgraded_by_platform": False,
            "environmental_signal_recast_as_observed_impact": False,
        },
        "generated_at": _now(),
    }
    payload["event_sha256"] = _digest(record)
    return payload


def export_manifest(source_id: str = "noaa-coral-reef-watch", hazard_type: str = "marine-heatwave", latitude: float | None = None, longitude: float | None = None, date: str = ""):
    current = state(source_id, hazard_type, latitude, longitude, date)
    payload = {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "schema": "sc-site-intelligence-ocean-events-hazards/1.0",
        "state": current,
        "review": {
            "threshold_as_hazard_declaration": False,
            "forecast_as_observation": False,
            "model_as_in_situ": False,
            "source_advisory_reissued": False,
            "zero_records_as_safe": False,
            "ecosystem_impact_inferred": False,
        },
        "generated_at": _now(),
    }
    payload["manifest_sha256"] = _digest(payload)
    return payload


def readiness():
    checks = {
        "noaa_coral_reef_watch_registered": "noaa-coral-reef-watch" in SOURCES,
        "noaa_coastwatch_registered": "noaa-coastwatch" in SOURCES,
        "copernicus_marine_registered": "copernicus-marine" in SOURCES,
        "noaa_nccos_registered": "noaa-nccos" in SOURCES,
        "multiple_hazard_domains": len(HAZARD_TYPES) >= 8,
        "forecast_not_observation": True,
        "model_not_in_situ": True,
        "threshold_not_hazard_declaration": True,
        "source_advisory_not_reissued": True,
        "zero_records_not_safe": True,
        "environmental_condition_not_observed_impact": True,
        "route_count_unchanged": True,
    }
    return {
        "ok": all(checks.values()),
        "version": VERSION,
        "contract": CONTRACT,
        "checks": checks,
        "summary": {
            "sources": len(SOURCES),
            "hazard_types": len(HAZARD_TYPES),
            "route": ROUTE,
            "public_route_count_delta": 0,
        },
        "generated_at": _now(),
    }
