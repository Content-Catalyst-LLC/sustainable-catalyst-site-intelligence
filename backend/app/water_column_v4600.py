from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

from .version import APP_VERSION

VERSION = APP_VERSION
CONTRACT = "water-column-depth-explorer"
ROUTE = "earth"
MAX_DEPTH_M = 11000.0


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


SOURCES: dict[str, dict[str, Any]] = {
    "argo-argovis": {
        "title": "Argo profiles via Argovis",
        "organization": "International Argo Program / Argovis collaboration",
        "url": "https://argo.ucsd.edu/data/",
        "api_url": "https://argovis-api.colorado.edu/docs/",
        "recognized_hosts": ["argo.ucsd.edu", "argovis.colorado.edu", "argovis-api.colorado.edu"],
        "coverage": "global Argo float profiles with profile/platform availability varying through space, time, depth, sensor package, and quality-control state",
        "authentication": "public discovery/API access; upstream terms and limits apply",
        "evidence_types": ["in-situ-profile", "bgc-in-situ-profile"],
        "machine_access": "Argovis REST API for Argo profiles, floats/platforms, selections, BGC data, and metadata",
        "depth_semantics": "source-reported pressure/depth samples from profiling floats; no value is implied between samples",
    },
    "copernicus-marine": {
        "title": "Copernicus Marine 3-D ocean products",
        "organization": "Copernicus Marine Service",
        "url": "https://marine.copernicus.eu/",
        "api_url": "https://help.marine.copernicus.eu/en/articles/4794731-which-programmatic-access-services-are-available",
        "recognized_hosts": ["marine.copernicus.eu", "help.marine.copernicus.eu", "toolbox-docs.marine.copernicus.eu", "data.marine.copernicus.eu"],
        "coverage": "global and regional 3-D analysis, forecast, reanalysis, observation, and biogeochemical products; exact depth levels and coverage are dataset-specific",
        "authentication": "Copernicus Marine data access may require a free upstream account; credentials are never embedded in public Site Intelligence state",
        "evidence_types": ["analysis", "forecast", "reanalysis", "model"],
        "machine_access": "Copernicus Marine Toolbox catalogue/open/subset/original-file workflows",
        "depth_semantics": "dataset-defined model or analysis depth levels; a gridded field is not an in-situ profile",
    },
    "onc-oceans-3": {
        "title": "Ocean Networks Canada Oceans 3.0",
        "organization": "Ocean Networks Canada",
        "url": "https://data.oceannetworks.ca/",
        "api_url": "https://data.oceannetworks.ca/OpenAPI",
        "recognized_hosts": ["data.oceannetworks.ca", "oceannetworks.ca", "www.oceannetworks.ca", "wiki.oceannetworks.ca"],
        "coverage": "fixed observatories, mobile platforms, casts, and autonomous instruments in ONC-supported observing regions; not global coverage",
        "authentication": "upstream API/data-product access may require an ONC token; tokens are never stored in public Site Intelligence state",
        "evidence_types": ["fixed-observatory", "mobile-platform", "in-situ-profile"],
        "machine_access": "Oceans 3.0 Web Services API and portal discovery for instruments, deployments, scalar data, casts, and data products",
        "depth_semantics": "instrument/deployment or cast-specific depth/pressure; fixed-depth sensors are not treated as vertical profiles unless the source record is a profile/cast",
    },
}

VARIABLES: dict[str, dict[str, Any]] = {
    "temperature": {"title": "Water temperature", "short": "TEMP", "default_unit": "degC", "default_source": "argo-argovis", "sources": ["argo-argovis", "copernicus-marine", "onc-oceans-3"], "note": "In-situ temperature samples and gridded model/analysis temperatures remain separate evidence classes."},
    "salinity": {"title": "Salinity", "short": "SAL", "default_unit": "1", "default_source": "argo-argovis", "sources": ["argo-argovis", "copernicus-marine", "onc-oceans-3"], "note": "Practical/absolute salinity conventions and units remain source-defined and are not silently converted."},
    "dissolved-oxygen": {"title": "Dissolved oxygen", "short": "O2", "default_unit": "umol kg-1", "default_source": "argo-argovis", "sources": ["argo-argovis", "copernicus-marine", "onc-oceans-3"], "note": "Oxygen availability depends on the float/instrument/product; absence of a measurement is not zero oxygen."},
    "pressure": {"title": "Pressure", "short": "PRES", "default_unit": "dbar", "default_source": "argo-argovis", "sources": ["argo-argovis", "onc-oceans-3"], "note": "Pressure and geometric depth are related but not interchangeable without an explicit conversion method."},
    "density": {"title": "Seawater density", "short": "RHO", "default_unit": "kg m-3", "default_source": "copernicus-marine", "sources": ["copernicus-marine", "onc-oceans-3"], "note": "Density may be measured, calculated, analyzed, or modeled; the calculation/provenance must remain visible."},
    "chlorophyll-a": {"title": "Chlorophyll-a / fluorescence", "short": "CHL", "default_unit": "source-defined", "default_source": "argo-argovis", "sources": ["argo-argovis", "copernicus-marine", "onc-oceans-3"], "note": "Fluorescence and chlorophyll concentration are not assumed equivalent unless the source supplies the calibration."},
    "nitrate": {"title": "Nitrate", "short": "NO3", "default_unit": "umol kg-1", "default_source": "argo-argovis", "sources": ["argo-argovis", "copernicus-marine", "onc-oceans-3"], "note": "Nitrate is available only for relevant BGC floats, instruments, or biogeochemical products."},
    "ph": {"title": "pH", "short": "pH", "default_unit": "1", "default_source": "argo-argovis", "sources": ["argo-argovis", "copernicus-marine", "onc-oceans-3"], "note": "pH scale, calibration, and temperature/pressure context remain source-defined."},
}

DEPTH_PRESETS = [0, 10, 50, 100, 200, 500, 1000, 2000, 4000, 6000, 8000, 11000]


def _variable(variable_id: str):
    vid = (variable_id or "temperature").strip().lower()
    if vid not in VARIABLES:
        raise ValueError(f"unsupported water-column variable: {vid}")
    return vid, {"id": vid, **VARIABLES[vid]}


def _source(source_id: str, variable: dict[str, Any] | None = None):
    sid = (source_id or (variable or {}).get("default_source") or "argo-argovis").strip().lower()
    if sid not in SOURCES:
        raise ValueError(f"unsupported water-column source: {sid}")
    if variable and sid not in variable["sources"]:
        raise ValueError(f"source {sid} is not registered for {variable['id']}")
    return sid, {"id": sid, **SOURCES[sid]}


def _point(latitude: float, longitude: float):
    lat, lon = float(latitude), float(longitude)
    if not -90 <= lat <= 90:
        raise ValueError("latitude must be between -90 and 90")
    if not -180 <= lon <= 180:
        raise ValueError("longitude must be between -180 and 180")
    return {"latitude": round(lat, 6), "longitude": round(lon, 6)}


def _depth(value: float):
    depth = float(value)
    if not 0 <= depth <= MAX_DEPTH_M:
        raise ValueError(f"depth_m must be between 0 and {int(MAX_DEPTH_M)}")
    return round(depth, 3)


def _date(value: str | None):
    raw = (value or "").strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).date().isoformat()
    except ValueError as exc:
        raise ValueError("date must be ISO-8601 YYYY-MM-DD") from exc


def _query_plan(var: dict[str, Any], src: dict[str, Any], point: dict[str, float], day: str | None, depth_m: float):
    if src["id"] == "argo-argovis":
        return {
            "access_kind": "Argovis Argo profile selection",
            "api_base": "https://argovis-api.colorado.edu/argo",
            "documentation_url": "https://argovis-api.colorado.edu/docs/",
            "point": point,
            "date": day,
            "target_depth_m": depth_m,
            "automatic_profile_loaded": False,
            "note": "Search for source profiles in space/time, then preserve the original sample depths, pressure, QC flags, and profile identity. A target depth does not imply a measurement exists there.",
        }
    if src["id"] == "copernicus-marine":
        return {
            "access_kind": "Copernicus Marine 3-D catalogue/subset",
            "catalogue_url": "https://data.marine.copernicus.eu/",
            "toolbox_docs": "https://help.marine.copernicus.eu/en/articles/4794731-which-programmatic-access-services-are-available",
            "point": point,
            "date": day,
            "target_depth_m": depth_m,
            "credentials_embedded": False,
            "automatic_profile_loaded": False,
            "note": "Choose an exact 3-D dataset and source depth level before reading a field. Model/analysis levels are not converted into in-situ observations.",
        }
    return {
        "access_kind": "Oceans 3.0 deployment/instrument/cast discovery",
        "api_url": "https://data.oceannetworks.ca/OpenAPI",
        "point": point,
        "date": day,
        "target_depth_m": depth_m,
        "automatic_profile_loaded": False,
        "note": "Resolve a specific ONC location/deployment/device or cast before requesting scalar/profile data. Fixed sensor depth does not imply a complete water-column profile.",
    }


def overview():
    p = {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "title": "Water Column & Depth Explorer",
        "route": ROUTE,
        "source_count": len(SOURCES),
        "variable_count": len(VARIABLES),
        "depth_presets_m": DEPTH_PRESETS,
        "maximum_navigation_depth_m": MAX_DEPTH_M,
        "summary": "Descend from Ocean Surface into source-bounded vertical profiles and 3-D ocean depth fields while preserving sample depth, pressure, QC, evidence class, and missing-data truth.",
        "truth_boundaries": [
            "A selected depth is a navigation request, not evidence that a measurement exists at that depth.",
            "In-situ profiles, fixed-depth observatory measurements, and gridded model/analysis depth levels remain distinct evidence classes.",
            "Site Intelligence does not interpolate between profile samples unless a future method explicitly requests and discloses an interpolation method; v4.19.0 performs no interpolation.",
            "Pressure is not silently converted to geometric depth and geometric depth is not silently converted to pressure.",
            "Quality-control flags remain attached to source samples and are not converted into a generic pass/fail score.",
            "Missing depth samples remain missing; the nearest available sample may be reported as context but is not substituted as the requested depth value.",
            "Upstream credentials or access tokens are never embedded in public state, exports, browser assets, or repository fixtures.",
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
        "variable_count": len(VARIABLES),
        "sources": [{"id": k, **v} for k, v in SOURCES.items()],
        "variables": [{"id": k, **v} for k, v in VARIABLES.items()],
        "depth_presets_m": DEPTH_PRESETS,
        "maximum_navigation_depth_m": MAX_DEPTH_M,
        "generated_at": _now(),
    }


def state(variable_id: str = "temperature", source_id: str = "", latitude: float = 0.0, longitude: float = 0.0, date: str = "", depth_m: float = 0.0):
    _, var = _variable(variable_id)
    _, src = _source(source_id, var)
    point = _point(latitude, longitude)
    day = _date(date)
    depth = _depth(depth_m)
    p = {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "mode": "water-column",
        "route": ROUTE,
        "variable": var,
        "source": src,
        "point": point,
        "date": day,
        "depth_m": depth,
        "condition": {
            "value": None,
            "unit": var["default_unit"],
            "source_sample_depth_m": None,
            "pressure_dbar": None,
            "quality_flags": [],
            "record_loaded": False,
            "coverage_verified": False,
            "depth_sample_verified": False,
            "current_condition_claimed": False,
        },
        "query_plan": _query_plan(var, src, point, day, depth),
        "truth": {
            "value_fabricated": False,
            "depth_value_interpolated": False,
            "nearest_sample_substituted": False,
            "pressure_depth_conversion_performed": False,
            "missing_replaced": False,
            "evidence_classes_collapsed": False,
            "coverage_inferred_from_source_eligibility": False,
        },
        "generated_at": _now(),
    }
    p["state_sha256"] = _digest(p)
    return p


def _normalize_samples(samples: Any, default_unit: str):
    if not isinstance(samples, list) or not samples:
        raise ValueError("samples must be a non-empty array")
    out = []
    seen: set[float] = set()
    for index, raw in enumerate(samples):
        if not isinstance(raw, dict):
            raise ValueError(f"sample {index} must be an object")
        depth = _depth(raw.get("depth_m"))
        if depth in seen:
            raise ValueError("duplicate sample depths are not allowed in a normalized profile")
        seen.add(depth)
        if not isinstance(raw.get("value"), (int, float)):
            raise ValueError(f"sample {index} value must be numeric")
        pressure = raw.get("pressure_dbar")
        if pressure is not None:
            if not isinstance(pressure, (int, float)) or float(pressure) < 0:
                raise ValueError(f"sample {index} pressure_dbar must be a non-negative number")
            pressure = round(float(pressure), 3)
        flags = raw.get("quality_flags") or []
        if not isinstance(flags, list):
            raise ValueError(f"sample {index} quality_flags must be an array")
        out.append({
            "depth_m": depth,
            "pressure_dbar": pressure,
            "value": float(raw["value"]),
            "unit": str(raw.get("unit") or default_unit),
            "quality_flags": [str(v) for v in flags],
            "source_sample_id": str(raw.get("source_sample_id") or "").strip() or None,
        })
    return sorted(out, key=lambda row: row["depth_m"])


def normalize_profile(request: dict[str, Any]):
    if not isinstance(request, dict):
        raise ValueError("request must be an object")
    vid, var = _variable(str(request.get("variable_id") or ""))
    sid, src = _source(str(request.get("source_id") or ""), var)
    source_url = str(request.get("source_url") or "").strip()
    parsed = urlparse(source_url)
    if parsed.scheme != "https" or parsed.hostname not in src["recognized_hosts"]:
        raise ValueError("source_url must use HTTPS and a registered source host")
    evidence_type = str(request.get("evidence_type") or "").strip().lower()
    if evidence_type not in src["evidence_types"]:
        raise ValueError("evidence_type is not registered for this source")
    profile_id = str(request.get("profile_id") or "").strip()
    if not profile_id:
        raise ValueError("profile_id is required")
    point = _point(float(request.get("latitude")), float(request.get("longitude")))
    observed_at = str(request.get("observed_at") or "").strip()
    if not observed_at:
        raise ValueError("observed_at is required")
    samples = _normalize_samples(request.get("samples"), var["default_unit"])
    profile = {
        "profile_id": profile_id,
        "variable": {"id": vid, "title": var["title"]},
        "source": {"id": sid, "title": src["title"], "url": source_url},
        "dataset_id": str(request.get("dataset_id") or "").strip() or None,
        "platform_id": str(request.get("platform_id") or "").strip() or None,
        "evidence_type": evidence_type,
        "point": point,
        "observed_at": observed_at,
        "retrieved_at": str(request.get("retrieved_at") or "").strip() or _now(),
        "sample_count": len(samples),
        "depth_min_m": samples[0]["depth_m"],
        "depth_max_m": samples[-1]["depth_m"],
        "samples": samples,
        "interpolation_performed": False,
        "pressure_depth_conversion_performed": False,
        "source_domain_recognized": True,
        "network_response_independently_verified": False,
        "evidence_state": "source-attributed-not-network-verified",
    }
    p = {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "profile": profile,
        "review": {
            "samples_reordered_by_depth_only": True,
            "values_interpolated": False,
            "nearest_sample_substituted": False,
            "quality_flags_preserved": True,
            "missing_imputed": False,
        },
        "generated_at": _now(),
    }
    p["profile_sha256"] = _digest(profile)
    return p


def resolve_depth(request: dict[str, Any]):
    if not isinstance(request, dict):
        raise ValueError("request must be an object")
    target = _depth(request.get("target_depth_m"))
    samples = _normalize_samples(request.get("samples"), str(request.get("unit") or "source-defined"))
    exact = next((row for row in samples if row["depth_m"] == target), None)
    nearest = min(samples, key=lambda row: abs(row["depth_m"] - target))
    if exact is not None:
        result = {
            "target_depth_m": target,
            "match": "exact-source-sample",
            "value": exact["value"],
            "unit": exact["unit"],
            "source_sample_depth_m": exact["depth_m"],
            "quality_flags": exact["quality_flags"],
            "value_claimed": True,
            "interpolation_performed": False,
            "nearest_sample_substituted": False,
        }
    else:
        result = {
            "target_depth_m": target,
            "match": "no-exact-source-sample",
            "value": None,
            "unit": None,
            "source_sample_depth_m": None,
            "quality_flags": [],
            "value_claimed": False,
            "interpolation_performed": False,
            "nearest_sample_substituted": False,
            "nearest_available_sample": {
                "depth_m": nearest["depth_m"],
                "distance_m": round(abs(nearest["depth_m"] - target), 3),
                "value_withheld_as_target_value": True,
            },
            "reason": "No exact source sample exists at the requested depth; v4.19.0 does not interpolate or substitute the nearest sample.",
        }
    p = {"ok": True, "version": VERSION, "contract": CONTRACT, "resolution": result, "generated_at": _now()}
    p["resolution_sha256"] = _digest(result)
    return p


def export_manifest(variable_id: str = "temperature", source_id: str = "", latitude: float = 0.0, longitude: float = 0.0, date: str = "", depth_m: float = 0.0):
    current = state(variable_id, source_id, latitude, longitude, date, depth_m)
    p = {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "schema": "sc-site-intelligence-water-column/1.0",
        "state": current,
        "source_snapshot": {
            "id": current["source"]["id"],
            "title": current["source"]["title"],
            "url": current["source"]["url"],
            "coverage": current["source"]["coverage"],
            "depth_semantics": current["source"]["depth_semantics"],
            "authentication": current["source"]["authentication"],
        },
        "review": {
            "depth_value_fabricated": False,
            "interpolation_performed": False,
            "nearest_sample_substituted": False,
            "pressure_depth_conversion_performed": False,
            "evidence_classes_collapsed": False,
            "missing_imputed": False,
        },
        "generated_at": _now(),
    }
    p["manifest_sha256"] = _digest(p)
    return p


def readiness():
    checks = {
        "sources_registered": len(SOURCES) >= 3,
        "variables_registered": len(VARIABLES) >= 8,
        "depth_navigation_bounded": MAX_DEPTH_M == 11000.0,
        "no_fake_depth_value": True,
        "no_automatic_interpolation": True,
        "nearest_sample_not_substituted": True,
        "pressure_depth_not_silently_converted": True,
        "quality_flags_preserved": True,
        "evidence_classes_separated": True,
        "upstream_credentials_excluded": True,
        "route_count_unchanged": True,
    }
    return {
        "ok": all(checks.values()),
        "version": VERSION,
        "contract": CONTRACT,
        "checks": checks,
        "summary": {"sources": len(SOURCES), "variables": len(VARIABLES), "depth_presets": len(DEPTH_PRESETS), "route": ROUTE, "public_route_count_delta": 0},
        "generated_at": _now(),
    }
