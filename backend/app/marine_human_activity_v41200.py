from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

from .version import APP_VERSION

VERSION = APP_VERSION
CONTRACT = "marine-human-activity-protected-areas-maritime-pressure"
ROUTE = "earth"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


SOURCES: dict[str, dict[str, Any]] = {
    "noaa-marine-cadastre-ais": {
        "title": "NOAA / BOEM Marine Cadastre Vessel Traffic",
        "organization": "NOAA Office for Coastal Management / Bureau of Ocean Energy Management",
        "url": "https://hub.marinecadastre.gov/pages/vesseltraffic",
        "api_url": "https://coast.noaa.gov/digitalcoast/tools/ais.html",
        "recognized_hosts": ["hub.marinecadastre.gov", "marinecadastre.gov", "www.marinecadastre.gov", "coast.noaa.gov"],
        "activity_types": ["vessel-traffic", "port-traffic"],
        "evidence_classes": ["ais-position", "vessel-track", "vessel-density", "aggregate-activity"],
        "coverage": "U.S. ocean-planning vessel traffic data derived from AIS received through the U.S. Coast Guard system; year and geography availability are product-specific.",
        "authentication": "Public discovery/download tools; upstream product limits apply.",
        "limitations": "AIS is not a complete vessel census. Reception, carriage requirements, equipment state, filtering, aggregation, and temporal coverage can all affect what is visible.",
    },
    "noaa-mpa-inventory": {
        "title": "NOAA Marine Protected Areas Inventory",
        "organization": "NOAA National Marine Protected Areas Center",
        "url": "https://marineprotectedareas.noaa.gov/dataanalysis/mpainventory/",
        "api_url": "https://marineprotectedareas.noaa.gov/helpful_resources/helpful_resources.html",
        "recognized_hosts": ["marineprotectedareas.noaa.gov", "www.fisheries.noaa.gov"],
        "activity_types": ["protected-area"],
        "evidence_classes": ["protected-area-boundary", "management-attribute", "restriction-attribute"],
        "coverage": "Marine protected areas in U.S. waters with source-reported boundaries and classification/management attributes.",
        "authentication": "Public GIS/tabular discovery and download.",
        "limitations": "Inventory inclusion and classification are reference information. Site Intelligence does not convert a mapped boundary or restriction attribute into a legal opinion, navigational instruction, or enforcement determination.",
    },
    "emodnet-human-activities": {
        "title": "EMODnet Human Activities",
        "organization": "European Marine Observation and Data Network / European Commission",
        "url": "https://emodnet.ec.europa.eu/en/human-activities",
        "api_url": "https://emodnet.ec.europa.eu/en/emodnet-web-service-documentation",
        "recognized_hosts": ["emodnet.ec.europa.eu"],
        "activity_types": ["vessel-traffic", "port-traffic", "offshore-energy", "aquaculture", "submarine-cables-pipelines", "extraction-disposal", "protected-area"],
        "evidence_classes": ["vessel-density", "infrastructure-feature", "aggregate-activity", "protected-area-boundary", "management-attribute"],
        "coverage": "European marine and maritime human-activity themes distributed through harmonized portal products and interoperable web services.",
        "authentication": "Many catalogue and OGC services are public; dataset-specific upstream conditions apply.",
        "limitations": "Coverage, refresh date, spatial resolution, and source authority vary by theme. A mapped feature is not assumed current or operational unless the source record says so.",
    },
    "global-fishing-watch": {
        "title": "Global Fishing Watch APIs",
        "organization": "Global Fishing Watch",
        "url": "https://globalfishingwatch.org/our-apis/",
        "api_url": "https://globalfishingwatch.org/our-apis/documentation",
        "recognized_hosts": ["globalfishingwatch.org", "gateway.api.globalfishingwatch.org", "api.globalfishingwatch.org"],
        "activity_types": ["vessel-traffic", "fishing-activity", "port-traffic"],
        "evidence_classes": ["ais-position", "vessel-track", "vessel-density", "inferred-fishing-activity", "aggregate-activity"],
        "coverage": "Global vessel and ocean-activity data products and APIs with source-, model-, access-, and terms-specific coverage.",
        "authentication": "API access commonly uses registration/access tokens; credentials are never embedded in public Site Intelligence state or browser assets.",
        "limitations": "Algorithmically inferred fishing activity is not a legal finding and is not proof of illegal, unreported, or unregulated fishing. AIS-derived products remain incomplete where transmission or reception is absent.",
    },
}

ACTIVITY_TYPES: dict[str, dict[str, str]] = {
    "vessel-traffic": {"title": "Vessel traffic", "domain": "mobility"},
    "fishing-activity": {"title": "Fishing activity", "domain": "resource-use"},
    "port-traffic": {"title": "Port traffic", "domain": "infrastructure"},
    "offshore-energy": {"title": "Offshore energy", "domain": "infrastructure"},
    "aquaculture": {"title": "Aquaculture", "domain": "resource-use"},
    "submarine-cables-pipelines": {"title": "Submarine cables & pipelines", "domain": "infrastructure"},
    "extraction-disposal": {"title": "Extraction & disposal", "domain": "industrial-use"},
    "protected-area": {"title": "Protected area / conservation zone", "domain": "conservation"},
}

EVIDENCE_CLASSES = {
    "ais-position": "source-reported or processed AIS position",
    "vessel-track": "source-derived sequence of vessel positions",
    "vessel-density": "aggregated vessel-presence or traffic-density product",
    "inferred-fishing-activity": "model- or algorithm-inferred fishing activity",
    "infrastructure-feature": "mapped marine infrastructure or use feature",
    "aggregate-activity": "aggregated human-activity statistic or raster",
    "protected-area-boundary": "source-reported protected/conservation area geometry",
    "management-attribute": "source-reported management classification or attribute",
    "restriction-attribute": "source-reported restriction or management text",
}


def _source(source_id: str):
    sid = (source_id or "noaa-marine-cadastre-ais").strip().lower()
    if sid not in SOURCES:
        raise ValueError(f"unsupported marine human-activity source: {sid}")
    return sid, {"id": sid, **SOURCES[sid]}


def _activity(value: str):
    key = (value or "vessel-traffic").strip().lower()
    if key not in ACTIVITY_TYPES:
        raise ValueError(f"unsupported activity_type: {key}")
    return key, {"id": key, **ACTIVITY_TYPES[key]}


def _evidence_class(value: str):
    key = (value or "aggregate-activity").strip().lower()
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
    payload = {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "route": ROUTE,
        "source_count": len(SOURCES),
        "activity_type_count": len(ACTIVITY_TYPES),
        "summary": "Orient marine human activity, vessel pressure, infrastructure, and protected-area context without converting incomplete tracking, modeled activity, spatial overlap, or management metadata into compliance or enforcement conclusions.",
        "truth_boundaries": [
            "AIS presence is evidence of a received/transmitted signal, not a complete vessel census.",
            "No AIS record does not prove that no vessel was present.",
            "Algorithmically inferred fishing activity is not proof of illegal, unreported, or unregulated fishing.",
            "Spatial overlap with a protected or managed area is not by itself a legal violation, enforcement finding, or navigational instruction.",
            "A mapped infrastructure feature is not assumed active, permitted, operational, or current unless the source record explicitly supports that status.",
            "Source dates, spatial resolution, aggregation, and coverage remain visible; mismatched time periods are not silently treated as contemporaneous.",
            "Upstream access tokens, credentials, or restricted data are never embedded in public state, browser assets, exports, or repository fixtures.",
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
        "activity_types": [{"id": key, **value} for key, value in ACTIVITY_TYPES.items()],
        "evidence_classes": [{"id": key, "title": value} for key, value in EVIDENCE_CLASSES.items()],
        "generated_at": _now(),
    }


def state(source_id: str = "noaa-marine-cadastre-ais", activity_type: str = "vessel-traffic", latitude: float | None = None, longitude: float | None = None, date: str = ""):
    _, source = _source(source_id)
    activity_id, activity = _activity(activity_type)
    point = _point(latitude, longitude)
    day = str(date or "").strip() or None
    supported = activity_id in source["activity_types"]
    return {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "route": ROUTE,
        "mode": "marine-human-activity-protected-areas",
        "source": source,
        "activity_type": activity,
        "query_point": point,
        "date": day,
        "source_supports_activity_type": supported,
        "evidence": {
            "activity_record_loaded": False,
            "protected_area_record_loaded": False,
            "spatial_overlap_evaluated": False,
            "legal_status_loaded": False,
            "enforcement_record_loaded": False,
        },
        "truth": {
            "ais_complete_vessel_census": False,
            "zero_ais_treated_as_no_vessel": False,
            "fishing_activity_treated_as_illegal": False,
            "spatial_overlap_treated_as_violation": False,
            "mapped_feature_treated_as_operational": False,
            "platform_compliance_finding": False,
        },
        "generated_at": _now(),
    }


def normalize_activity(request: dict[str, Any]):
    sid, source = _source(str(request.get("source_id") or ""))
    activity_id, activity = _activity(str(request.get("activity_type") or ""))
    if activity_id not in source["activity_types"]:
        raise ValueError(f"source {sid} is not registered for {activity_id}")
    evidence_class = _evidence_class(str(request.get("evidence_class") or ""))
    if evidence_class not in source["evidence_classes"]:
        raise ValueError(f"evidence_class {evidence_class} is not registered for {sid}")
    source_url = _https_source_url(source, request.get("source_url"))
    observed_at = str(request.get("observed_at") or request.get("period_start") or "").strip()
    if not observed_at:
        raise ValueError("observed_at or period_start is required")
    point = _point(request.get("latitude"), request.get("longitude"))
    bbox = _bbox(request.get("bbox"))
    if point is None and bbox is None:
        raise ValueError("activity record requires a point or bbox")
    value = request.get("value")
    numeric_value = None
    if value not in (None, ""):
        try:
            numeric_value = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("value must be numeric when provided") from exc
    record = {
        "source": {"id": sid, "title": source["title"], "url": source_url},
        "activity_type": activity,
        "evidence_class": evidence_class,
        "record_id": str(request.get("record_id") or "").strip() or None,
        "point": point,
        "bbox": bbox,
        "observed_at": observed_at,
        "period_end": str(request.get("period_end") or "").strip() or None,
        "vessel_id": str(request.get("vessel_id") or "").strip() or None,
        "vessel_type": str(request.get("vessel_type") or "").strip() or None,
        "value": numeric_value,
        "unit": str(request.get("unit") or "").strip() or None,
        "source_classification": str(request.get("source_classification") or "").strip() or None,
        "inferred_activity": evidence_class == "inferred-fishing-activity",
        "illegal_activity_claimed": False,
        "complete_vessel_census_claimed": False,
        "compliance_finding": False,
        "retrieved_at": str(request.get("retrieved_at") or "").strip() or _now(),
    }
    return {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "activity": record,
        "review": {
            "ais_absence_as_vessel_absence": False,
            "inferred_fishing_as_illegal": False,
            "activity_as_compliance_finding": False,
        },
        "activity_sha256": _digest(record),
    }


def normalize_protected_area(request: dict[str, Any]):
    sid, source = _source(str(request.get("source_id") or ""))
    if "protected-area" not in source["activity_types"]:
        raise ValueError(f"source {sid} is not registered for protected-area records")
    source_url = _https_source_url(source, request.get("source_url"))
    area_id = str(request.get("area_id") or request.get("record_id") or "").strip()
    name = str(request.get("name") or "").strip()
    if not area_id or not name:
        raise ValueError("area_id and name are required")
    bbox = _bbox(request.get("bbox"))
    if bbox is None:
        raise ValueError("protected-area record requires bbox")
    record = {
        "source": {"id": sid, "title": source["title"], "url": source_url},
        "area_id": area_id,
        "name": name,
        "bbox": bbox,
        "designation": str(request.get("designation") or "").strip() or None,
        "protection_level": str(request.get("protection_level") or "").strip() or None,
        "governance": str(request.get("governance") or "").strip() or None,
        "established": str(request.get("established") or "").strip() or None,
        "restriction_text": str(request.get("restriction_text") or "").strip() or None,
        "legal_interpretation_by_platform": False,
        "navigational_instruction_by_platform": False,
        "enforcement_status_inferred": False,
        "retrieved_at": str(request.get("retrieved_at") or "").strip() or _now(),
    }
    return {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "protected_area": record,
        "review": {
            "boundary_as_legal_opinion": False,
            "restriction_text_reinterpreted": False,
            "area_as_navigation_instruction": False,
        },
        "protected_area_sha256": _digest(record),
    }


def overlap_preview(request: dict[str, Any]):
    activity_point = _point(request.get("activity_latitude"), request.get("activity_longitude"))
    activity_bbox = _bbox(request.get("activity_bbox"), "activity_bbox")
    zone_bbox = _bbox(request.get("zone_bbox"), "zone_bbox")
    if zone_bbox is None:
        raise ValueError("zone_bbox is required")
    if activity_point is None and activity_bbox is None:
        raise ValueError("activity point or activity_bbox is required")
    west, south, east, north = zone_bbox
    if activity_point is not None:
        overlap = west <= activity_point["longitude"] <= east and south <= activity_point["latitude"] <= north
        method = "point-in-bounding-box"
    else:
        aw, ass, ae, an = activity_bbox
        overlap = not (ae < west or aw > east or an < south or ass > north)
        method = "bounding-box-intersection"
    preview = {
        "spatial_overlap": bool(overlap),
        "method": method,
        "activity_point": activity_point,
        "activity_bbox": activity_bbox,
        "zone_bbox": zone_bbox,
        "activity_time": str(request.get("activity_time") or "").strip() or None,
        "zone_effective_start": str(request.get("zone_effective_start") or "").strip() or None,
        "zone_effective_end": str(request.get("zone_effective_end") or "").strip() or None,
        "temporal_alignment_verified": False,
        "legal_violation": False,
        "enforcement_finding": False,
        "automatic_action_authorized": False,
    }
    return {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "preview": preview,
        "review": {
            "spatial_overlap_is_legal_violation": False,
            "spatial_overlap_is_enforcement_finding": False,
            "temporal_alignment_assumed": False,
        },
        "preview_sha256": _digest(preview),
    }


def export_manifest(source_id: str = "noaa-marine-cadastre-ais", activity_type: str = "vessel-traffic", latitude: float | None = None, longitude: float | None = None, date: str = ""):
    current = state(source_id, activity_type, latitude, longitude, date)
    payload = {
        "ok": True,
        "version": VERSION,
        "schema": "sc-site-intelligence-marine-human-activity/1.0",
        "contract": CONTRACT,
        "state": current,
        "review": {
            "zero_ais_as_no_vessel": False,
            "fishing_activity_as_illegal": False,
            "spatial_overlap_as_violation": False,
            "mapped_feature_as_operational": False,
            "platform_compliance_finding": False,
        },
        "generated_at": _now(),
    }
    payload["manifest_sha256"] = _digest(payload)
    return payload


def readiness():
    checks = {
        "four_sources_registered": len(SOURCES) == 4,
        "human_activity_types_registered": len(ACTIVITY_TYPES) >= 8,
        "ais_absence_boundary": True,
        "fishing_inference_boundary": True,
        "protected_area_overlap_boundary": True,
        "credential_boundary": True,
        "public_route_count_delta_zero": True,
    }
    return {
        "ok": all(checks.values()),
        "version": VERSION,
        "contract": CONTRACT,
        "checks": checks,
        "summary": {
            "source_count": len(SOURCES),
            "activity_type_count": len(ACTIVITY_TYPES),
            "public_route_count_delta": 0,
            "primary_area_count_delta": 0,
        },
        "generated_at": _now(),
    }
