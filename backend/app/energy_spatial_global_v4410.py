from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
from hashlib import sha256
import json
from math import asin, cos, radians, sin, sqrt
from typing import Any

from fastapi import APIRouter, HTTPException

from .version import APP_VERSION
from .energy_systems_v42800 import SOURCES as ENERGY_SOURCES

ENERGY_SYSTEMS_VERSION = "1.5.0"
SCHEMA = "sc-energy-spatial-global-intelligence/1.0"
PROFILE_SCHEMA = "sc-energy-spatial-profile/1.0"
COMPARISON_SCHEMA = "sc-energy-spatial-comparison/1.0"

router = APIRouter(prefix="/v1/energy-spatial", tags=["energy-spatial-global"])

FEATURE_CLASSES = {
    "generation", "substation", "transmission", "storage", "demand-center",
    "resource-observation", "market-observation", "system-observation",
}


def _fingerprint(value: Any) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def _finite_number(value: Any, field: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=f"{field} must be numeric") from exc
    if number != number or number in (float("inf"), float("-inf")):
        raise HTTPException(status_code=422, detail=f"{field} must be finite")
    return number


def _point(value: Any, field: str = "point") -> dict[str, float] | None:
    if value in (None, {}):
        return None
    if not isinstance(value, dict):
        raise HTTPException(status_code=422, detail=f"{field} must be an object")
    lat = _finite_number(value.get("latitude"), f"{field}.latitude")
    lon = _finite_number(value.get("longitude"), f"{field}.longitude")
    if not -90 <= lat <= 90 or not -180 <= lon <= 180:
        raise HTTPException(status_code=422, detail=f"{field} is outside valid latitude/longitude bounds")
    return {"latitude": round(lat, 6), "longitude": round(lon, 6)}


def _distance_km(a: dict[str, float], b: dict[str, float]) -> float:
    radius_km = 6371.0088
    lat1, lon1, lat2, lon2 = map(radians, (a["latitude"], a["longitude"], b["latitude"], b["longitude"]))
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return round(2 * radius_km * asin(min(1.0, sqrt(h))), 3)


def _normalize_record(raw: Any, index: int) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise HTTPException(status_code=422, detail=f"records[{index}] must be an object")
    rid = str(raw.get("record_id") or f"record-{index+1}").strip()
    source_ref = str(raw.get("source_ref") or "").strip()
    indicator = str(raw.get("indicator") or "").strip()
    unit = str(raw.get("unit") or "").strip()
    feature_class = str(raw.get("feature_class") or "system-observation").strip().lower()
    if not source_ref:
        raise HTTPException(status_code=422, detail=f"records[{index}].source_ref is required")
    if not indicator:
        raise HTTPException(status_code=422, detail=f"records[{index}].indicator is required")
    if feature_class not in FEATURE_CLASSES:
        raise HTTPException(status_code=422, detail=f"records[{index}].feature_class is unsupported")
    point = _point(raw.get("point"), f"records[{index}].point")
    year = raw.get("year")
    if year not in (None, ""):
        try: year = int(year)
        except (TypeError, ValueError) as exc: raise HTTPException(status_code=422, detail=f"records[{index}].year must be an integer") from exc
        if year < 1800 or year > 2200:
            raise HTTPException(status_code=422, detail=f"records[{index}].year is outside the supported range")
    value = raw.get("value")
    if value not in (None, ""):
        value = _finite_number(value, f"records[{index}].value")
    return {
        "record_id": rid,
        "source_ref": source_ref,
        "indicator": indicator,
        "value": value,
        "unit": unit or None,
        "year": year,
        "feature_class": feature_class,
        "technology": str(raw.get("technology") or "").strip() or None,
        "point": point,
        "properties": deepcopy(raw.get("properties")) if isinstance(raw.get("properties"), dict) else {},
    }


def source_registry() -> dict[str, Any]:
    rows = []
    for key, value in ENERGY_SOURCES.items():
        rows.append({
            "key": key,
            "title": value["title"],
            "organization": value["organization"],
            "coverage": value["coverage"],
            "limitations": value["limitations"],
            "indicator_types": list(value["indicator_types"]),
            "ingestion_boundary": "Existing Site Intelligence connector/public-energy routes may retrieve source data. The v1.5 spatial analysis routes consume explicit provenance-bound records and do not silently fetch or substitute data.",
        })
    return {"ok": True, "schema": "sc-energy-spatial-source-registry/1.0", "version": ENERGY_SYSTEMS_VERSION, "site_intelligence_version": APP_VERSION, "sources": rows}


def framework() -> dict[str, Any]:
    return {
        "ok": True,
        "schema": SCHEMA,
        "version": ENERGY_SYSTEMS_VERSION,
        "site_intelligence_version": APP_VERSION,
        "release": "Spatial & Global Energy Intelligence",
        "source_registry_route": "/v1/energy-spatial/source-registry",
        "profile_route": "/v1/energy-spatial/profile",
        "compare_route": "/v1/energy-spatial/compare",
        "validation_route": "/v1/energy-spatial/validate-result",
        "feature_classes": sorted(FEATURE_CLASSES),
        "capabilities": {
            "provenance_bound_spatial_profiles": True,
            "focus_point_distance_analysis": True,
            "geographic_extent_summary": True,
            "source_and_temporal_coverage_summary": True,
            "indicator_summary_without_cross_unit_coercion": True,
            "neutral_cross_geography_comparison": True,
            "deterministic_profile_ids": True,
            "connector_source_registry": True,
            "automatic_external_fetch": False,
            "site_suitability_scoring": False,
            "technical_potential_inference": False,
            "technology_ranking": False,
            "automatic_recommendation": False,
            "grid_reliability_determination": False,
            "outage_declaration": False,
            "current_year_inference": False,
        },
        "boundary": "Site Intelligence v4.41.0 organizes explicit spatial and global energy evidence. Distances, extents, counts, and descriptive summaries are evidence orientation, not site suitability, technical potential, grid reliability, outage status, investment advice, or technology ranking.",
    }


def profile(body: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(body, dict):
        raise HTTPException(status_code=422, detail="profile request must be a JSON object")
    geography = body.get("geography") if isinstance(body.get("geography"), dict) else {}
    name = str(geography.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=422, detail="geography.name is required")
    focus = _point(geography.get("focus_point"), "geography.focus_point")
    records_raw = body.get("records")
    if not isinstance(records_raw, list) or not records_raw:
        raise HTTPException(status_code=422, detail="records must be a non-empty array")
    if len(records_raw) > 5000:
        raise HTTPException(status_code=422, detail="records exceeds the 5000-record profile limit")
    records = [_normalize_record(x, i) for i, x in enumerate(records_raw)]

    classes = Counter(x["feature_class"] for x in records)
    technologies = Counter(x["technology"] for x in records if x["technology"])
    sources = sorted({x["source_ref"] for x in records})
    years = [x["year"] for x in records if isinstance(x["year"], int)]
    points = [x["point"] for x in records if x["point"]]

    extent = None
    if points:
        extent = {
            "min_latitude": min(p["latitude"] for p in points),
            "max_latitude": max(p["latitude"] for p in points),
            "min_longitude": min(p["longitude"] for p in points),
            "max_longitude": max(p["longitude"] for p in points),
        }

    nearest: dict[str, Any] = {}
    if focus:
        by_class: dict[str, list[tuple[float, dict[str, Any]]]] = defaultdict(list)
        for record in records:
            if record["point"]:
                by_class[record["feature_class"]].append((_distance_km(focus, record["point"]), record))
        for key, rows in by_class.items():
            distance, record = min(rows, key=lambda x: (x[0], x[1]["record_id"]))
            nearest[key] = {"record_id": record["record_id"], "distance_km": distance, "source_ref": record["source_ref"]}

    grouped: dict[tuple[str, str], list[float]] = defaultdict(list)
    for record in records:
        if isinstance(record["value"], float):
            grouped[(record["indicator"], record["unit"] or "unspecified")].append(record["value"])
    observations = []
    for (indicator, unit), values in sorted(grouped.items()):
        observations.append({
            "indicator": indicator,
            "unit": unit,
            "count": len(values),
            "minimum": min(values),
            "maximum": max(values),
            "mean": sum(values) / len(values),
        })

    canonical = {
        "geography": {"name": name, "iso3": str(geography.get("iso3") or "").upper() or None, "region": str(geography.get("region") or "").strip() or None, "focus_point": focus},
        "records": records,
        "provenance": body.get("provenance") if isinstance(body.get("provenance"), list) else [],
    }
    profile_id = "esp-" + _fingerprint(canonical)[:20]
    result = {
        "ok": True,
        "schema": PROFILE_SCHEMA,
        "version": ENERGY_SYSTEMS_VERSION,
        "site_intelligence_version": APP_VERSION,
        "profile_id": profile_id,
        "geography": canonical["geography"],
        "summary": {
            "record_count": len(records),
            "source_count": len(sources),
            "spatial_record_count": len(points),
            "feature_class_counts": dict(sorted(classes.items())),
            "technology_counts": dict(sorted(technologies.items())),
            "year_range": {"earliest": min(years), "latest": max(years)} if years else None,
        },
        "spatial_extent": extent,
        "nearest_to_focus": nearest,
        "observation_summaries": observations,
        "source_refs": sources,
        "provenance": canonical["provenance"],
        "truth": {
            "site_suitability_determined": False,
            "technical_potential_determined": False,
            "grid_reliability_determined": False,
            "outage_declared": False,
            "current_year_status_inferred": False,
            "technology_ranked": False,
            "recommendation_issued": False,
        },
        "content_fingerprint": _fingerprint(canonical),
    }
    return result


def compare(body: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(body, dict) or not isinstance(body.get("profiles"), list):
        raise HTTPException(status_code=422, detail="profiles must be an array")
    profiles = body["profiles"]
    if len(profiles) < 2 or len(profiles) > 20:
        raise HTTPException(status_code=422, detail="compare requires 2 to 20 profiles")
    items = []
    for i, p in enumerate(profiles):
        if not isinstance(p, dict) or p.get("schema") != PROFILE_SCHEMA:
            raise HTTPException(status_code=422, detail=f"profiles[{i}] is not a {PROFILE_SCHEMA} packet")
        items.append({
            "profile_id": p.get("profile_id"),
            "geography": p.get("geography"),
            "summary": p.get("summary"),
            "source_refs": p.get("source_refs", []),
            "observation_summaries": p.get("observation_summaries", []),
        })
    canonical = {"profiles": items, "comparison_note": str(body.get("comparison_note") or "").strip()}
    return {
        "ok": True,
        "schema": COMPARISON_SCHEMA,
        "version": ENERGY_SYSTEMS_VERSION,
        "site_intelligence_version": APP_VERSION,
        "comparison_id": "esc-" + _fingerprint(canonical)[:20],
        "profile_count": len(items),
        "profiles": items,
        "ranking": {"performed": False},
        "recommendation": {"performed": False},
        "boundary": "Comparison is side-by-side evidence orientation only; no composite score, winner, site suitability determination, technology ranking, or recommendation is produced.",
        "content_fingerprint": _fingerprint(canonical),
    }


def validate_result(body: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(body, dict):
        raise HTTPException(status_code=422, detail="result must be a JSON object")
    schema = body.get("schema")
    errors: list[str] = []
    if schema not in {PROFILE_SCHEMA, COMPARISON_SCHEMA}:
        errors.append("unsupported result schema")
    if body.get("version") != ENERGY_SYSTEMS_VERSION:
        errors.append("Energy Systems version mismatch")
    if body.get("site_intelligence_version") != APP_VERSION:
        errors.append("Site Intelligence version mismatch")
    if schema == PROFILE_SCHEMA:
        truth = body.get("truth") if isinstance(body.get("truth"), dict) else {}
        forbidden = [k for k in ("site_suitability_determined", "technical_potential_determined", "grid_reliability_determined", "outage_declared", "current_year_status_inferred", "technology_ranked", "recommendation_issued") if truth.get(k) is True]
        if forbidden: errors.append("forbidden determination(s): " + ", ".join(forbidden))
        if not body.get("profile_id") or not body.get("content_fingerprint"): errors.append("profile identity/fingerprint missing")
    if schema == COMPARISON_SCHEMA:
        if (body.get("ranking") or {}).get("performed") is not False: errors.append("ranking must remain disabled")
        if (body.get("recommendation") or {}).get("performed") is not False: errors.append("recommendation must remain disabled")
    return {"ok": not errors, "valid": not errors, "schema": "sc-energy-spatial-result-validation/1.0", "version": ENERGY_SYSTEMS_VERSION, "site_intelligence_version": APP_VERSION, "errors": errors}


@router.get("/framework")
def route_framework() -> dict[str, Any]: return framework()

@router.get("/source-registry")
def route_source_registry() -> dict[str, Any]: return source_registry()

@router.post("/profile")
def route_profile(body: dict[str, Any]) -> dict[str, Any]: return profile(body)

@router.post("/compare")
def route_compare(body: dict[str, Any]) -> dict[str, Any]: return compare(body)

@router.post("/validate-result")
def route_validate_result(body: dict[str, Any]) -> dict[str, Any]: return validate_result(body)
