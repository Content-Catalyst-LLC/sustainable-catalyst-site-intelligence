from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .config import Settings

FRESHNESS_CLASSES = {
    "live": "Continuously or frequently updated operational data.",
    "near_real_time": "Recently observed data with a short publication delay.",
    "recent": "Recently published observations suitable for current context.",
    "daily": "Updated approximately daily.",
    "monthly": "Updated approximately monthly.",
    "annual": "Updated annually or by statistical release cycle.",
    "periodic": "Updated according to the source agency's reporting cycle.",
    "historical": "Historical reference series rather than current monitoring.",
    "forecast": "Forecast data; not an observed measurement.",
    "last_known_good": "Cached successful response shown during an upstream outage.",
}

SOURCE_REGISTRY: List[Dict[str, Any]] = [
    {"source_id":"nasa-eonet","title":"NASA EONET","organization":"NASA Earth Observatory Natural Event Tracker","family":"earth-observation","domains":["natural-events","climate","hazards"],"base_url":"https://eonet.gsfc.nasa.gov/api/v3","health_path":"/events?limit=1","access_type":"public_api","freshness_class":"near_real_time","geographic_coverage":"global","official_status":"observational-curated","requires_key":False,"cache_ttl_seconds":1800,"attribution_required":True,"public_use":"Active natural-event metadata and links to related imagery.","limitations":"General information and visualization; not an emergency alert or exact hazard-boundary service."},
    {"source_id":"nasa-power","title":"NASA POWER","organization":"NASA Langley Research Center","family":"climate-energy","domains":["climate","weather","solar","energy"],"base_url":"https://power.larc.nasa.gov/api/temporal/daily/point","health_path":"?parameters=T2M&community=RE&longitude=-87.6298&latitude=41.8781&start=20250101&end=20250102&format=JSON","access_type":"public_api","freshness_class":"recent","geographic_coverage":"global point and regional products","official_status":"analysis-ready-observational","requires_key":False,"cache_ttl_seconds":21600,"attribution_required":True,"public_use":"Meteorological and solar-resource time series.","limitations":"Publication latency and parameter coverage vary; not a live emergency-weather feed."},
    {"source_id":"un-sdg","title":"United Nations SDG Global Database","organization":"United Nations Statistics Division","family":"sustainable-development","domains":["sdgs","poverty","education","health","environment"],"base_url":"https://unstats.un.org/SDGAPI/v1/sdg","health_path":"/Goal/List","access_type":"public_api","freshness_class":"periodic","geographic_coverage":"global","official_status":"official-custodian-data","requires_key":False,"cache_ttl_seconds":86400,"attribution_required":True,"supports_disaggregation":True,"public_use":"Official SDG goal, target, indicator, series, and observation context.","limitations":"Reporting years and disaggregation vary by indicator and country."},
    {"source_id":"world-bank-indicators","title":"World Bank Indicators","organization":"World Bank","family":"human-development","domains":["poverty","education","health","economy","environment"],"base_url":"https://api.worldbank.org/v2","health_path":"/country/USA/indicator/SI.POV.DDAY?format=json&per_page=1","access_type":"public_api","freshness_class":"periodic","geographic_coverage":"global","official_status":"official-development-statistics","requires_key":False,"cache_ttl_seconds":21600,"attribution_required":True,"public_use":"Country and regional development indicators.","limitations":"Series definitions, coverage, and revision schedules differ."},
    {"source_id":"world-bank-pip","title":"World Bank Poverty and Inequality Platform","organization":"World Bank","family":"poverty-inequality","domains":["poverty","inequality","shared-prosperity"],"base_url":"https://api.worldbank.org/pip/v1","health_path":"/pip","access_type":"public_api","freshness_class":"periodic","geographic_coverage":"global","official_status":"official-poverty-estimates","requires_key":False,"cache_ttl_seconds":86400,"attribution_required":True,"public_use":"Poverty and inequality estimates with methodology-aware dimensions.","limitations":"Poverty lines, survey years, interpolation, and comparability require explicit display."},
    {"source_id":"unesco-uis","title":"UNESCO Institute for Statistics Data","organization":"UNESCO UIS","family":"education","domains":["education","literacy","science","culture"],"base_url":"https://api.uis.unesco.org","health_path":"","access_type":"public_data_service","freshness_class":"periodic","geographic_coverage":"global","official_status":"official-education-statistics","requires_key":False,"cache_ttl_seconds":86400,"attribution_required":True,"public_use":"Education access, completion, literacy, expenditure, and SDG 4 context.","limitations":"API availability and current endpoint contracts must be verified per dataset release."},
    {"source_id":"faostat","title":"FAOSTAT","organization":"Food and Agriculture Organization of the United Nations","family":"food-agriculture","domains":["food","agriculture","land","emissions","nutrition"],"base_url":"https://fenixservices.fao.org/faostat/api/v1","health_path":"/en/definitions/domain","access_type":"public_api","freshness_class":"annual","geographic_coverage":"global","official_status":"official-agriculture-statistics","requires_key":False,"cache_ttl_seconds":86400,"attribution_required":True,"public_use":"Agriculture, food systems, land use, fertilizer, forestry, and emissions statistics.","limitations":"Domain-specific definitions and release cycles require source notes."},
    {"source_id":"un-water-sdg6","title":"UN-Water SDG 6 Data","organization":"UN-Water","family":"water-sanitation","domains":["water","sanitation","hygiene","ecosystems"],"base_url":"https://sdg6data.org/api","health_path":"","access_type":"public_api","freshness_class":"periodic","geographic_coverage":"global","official_status":"official-sdg6-aggregation","requires_key":False,"cache_ttl_seconds":86400,"attribution_required":True,"public_use":"SDG 6 indicator data and water/sanitation context.","limitations":"Indicator ownership and reporting schedules differ among custodian agencies."},
    {"source_id":"oecd-sdmx","title":"OECD Data Explorer API","organization":"OECD","family":"economic-social-development","domains":["economy","education","health","employment","environment","development-finance"],"base_url":"https://sdmx.oecd.org/public/rest/v1","health_path":"/dataflow/OECD.SDD.STES,DSD_STES@DF_FINMARK,/.?format=csvfile","access_type":"public_sdmx_api","freshness_class":"periodic","geographic_coverage":"OECD and partner economies","official_status":"official-statistics","requires_key":False,"cache_ttl_seconds":21600,"attribution_required":True,"public_use":"Comparable economic, social, education, health, and environmental statistics.","limitations":"SDMX structures and dataset-specific dimensions must be normalized carefully."},
]

PLANETARY_BOUNDARIES = [
    {"boundary_id":"climate-change","label":"Climate change","control_variables":["atmospheric CO2 concentration","radiative forcing"],"source_mappings":["nasa-power","un-sdg"],"assessment_status":"derived_adapter_ready"},
    {"boundary_id":"biosphere-integrity","label":"Biosphere integrity","control_variables":["genetic diversity","functional integrity"],"source_mappings":["un-sdg","faostat"],"assessment_status":"source_mapping_foundation"},
    {"boundary_id":"land-system-change","label":"Land-system change","control_variables":["forest cover by biome"],"source_mappings":["faostat","un-sdg"],"assessment_status":"source_mapping_foundation"},
    {"boundary_id":"freshwater-change","label":"Freshwater change","control_variables":["blue water","green water"],"source_mappings":["un-water-sdg6","un-sdg"],"assessment_status":"source_mapping_foundation"},
    {"boundary_id":"biogeochemical-flows","label":"Biogeochemical flows","control_variables":["nitrogen flows","phosphorus flows"],"source_mappings":["faostat","un-sdg"],"assessment_status":"source_mapping_foundation"},
    {"boundary_id":"ocean-acidification","label":"Ocean acidification","control_variables":["carbonate ion saturation state"],"source_mappings":["un-sdg"],"assessment_status":"planned_connector"},
    {"boundary_id":"stratospheric-ozone","label":"Stratospheric ozone depletion","control_variables":["stratospheric ozone concentration"],"source_mappings":["nasa-eonet"],"assessment_status":"planned_connector"},
    {"boundary_id":"atmospheric-aerosol-loading","label":"Atmospheric aerosol loading","control_variables":["regional aerosol optical depth"],"source_mappings":["nasa-eonet"],"assessment_status":"planned_connector"},
    {"boundary_id":"novel-entities","label":"Novel entities","control_variables":["chemical pollution and material release indicators"],"source_mappings":["un-sdg"],"assessment_status":"research_registry"},
]

OBSERVATION_SCHEMA = {
    "schema":"sc-sustainable-development-observation/1.0",
    "required":["source_id","indicator_id","geography","period","value","unit","freshness","observation_type","retrieved_at","is_derived"],
    "optional":["sdg_goals","planetary_boundaries","dimensions","methodology_version","source_revision","confidence","caveats"],
    "observation_types":["reported","observed","modeled","reanalysis","forecast","derived"],
}

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _public_source(item: Dict[str, Any]) -> Dict[str, Any]:
    row=dict(item)
    row.update({"slug":item["source_id"],"label":item["title"],"status":"live_ready" if item["access_type"] in {"public_api","public_sdmx_api"} else "planned","source_mode":item["access_type"],"freshness_window":item["freshness_class"],"safe_display":"Show source, period, geography, unit, freshness, and methodology with every observation.","fallback_reason":"Use last-known-good data or methodology-only state when the upstream source is unavailable.","private_exclusions":["credentials","raw debug payloads","unsupported causal claims","professional advice"]})
    return row

def source_registry(settings: Settings) -> Dict[str, Any]:
    connectors=[_public_source(x) for x in SOURCE_REGISTRY]
    return {"ok":True,"generated_at":_now(),"version_scope":"v1.9.0","title":"Sustainable Development Public Source Registry","summary":"Public-source registry for planetary boundaries, SDGs, poverty, education, food, water, climate, and human development.","counts":{"sources":len(connectors),"families":len(set(x["family"] for x in connectors)),"no_key_required":sum(not x["requires_key"] for x in connectors)},"connectors":connectors,"freshness_definitions":FRESHNESS_CLASSES,"methodology":["Official, observational, modeled, research, and derived records remain explicitly distinguished.","A current observation does not automatically constitute an official planetary-boundary assessment.","Every public value should retain source, geography, period, unit, freshness, and caveat metadata."],"observation_schema":OBSERVATION_SCHEMA}

def source_families() -> Dict[str, Any]:
    groups={}
    for item in SOURCE_REGISTRY:
        groups.setdefault(item["family"],[]).append(item["source_id"])
    return {"ok":True,"generated_at":_now(),"version_scope":"v1.9.0","title":"Sustainable Development Connector Families","summary":"Connector coverage across environmental limits and human development.","families":[{"family":k,"source_count":len(v),"sources":v} for k,v in sorted(groups.items())]}

def planetary_boundary_registry() -> Dict[str, Any]:
    return {"ok":True,"generated_at":_now(),"version_scope":"v1.9.0","title":"Planetary Boundaries Adapter Registry","summary":"Boundary definitions and source mappings for future derived, methodology-forward assessments.","boundaries":PLANETARY_BOUNDARIES,"counts":{"boundaries":len(PLANETARY_BOUNDARIES),"adapter_ready":sum(x["assessment_status"]=="derived_adapter_ready" for x in PLANETARY_BOUNDARIES)},"methodology":["Threshold definitions must be sourced from peer-reviewed planetary-boundary research.","Site Intelligence assessments must be labeled derived unless directly reproduced from an official assessment.","Underlying indicators and assessment conclusions are separate records."]}

def connector_health(settings: Settings, live: bool=False) -> Dict[str, Any]:
    rows=[]
    for item in SOURCE_REGISTRY:
        status="configured"
        detail="Live check disabled; registry metadata and fallback state are available."
        latency_ms=None
        if live and settings.public_connector_live_checks and item.get("health_path"):
            import time
            started=time.perf_counter()
            try:
                req=Request(item["base_url"]+item["health_path"],headers={"User-Agent":"SustainableCatalystSiteIntelligence/1.6"})
                with urlopen(req,timeout=settings.external_request_timeout_seconds) as resp:
                    status="healthy" if 200 <= resp.status < 400 else "degraded"
                    detail=f"Upstream returned HTTP {resp.status}."
            except (HTTPError,URLError,TimeoutError) as exc:
                status="fallback_safe"
                detail=f"Upstream check unavailable ({exc.__class__.__name__}); use cached or methodology-only display."
            latency_ms=round((time.perf_counter()-started)*1000,1)
        rows.append({"source_id":item["source_id"],"label":item["title"],"status":status,"freshness_class":item["freshness_class"],"cache_ttl_seconds":item["cache_ttl_seconds"],"latency_ms":latency_ms,"detail":detail})
    counts={k:sum(r["status"]==k for r in rows) for k in {r["status"] for r in rows}}
    return {"ok":True,"generated_at":_now(),"version_scope":"v1.9.0","title":"Sustainable Development Connector Health","summary":"Public-safe source health, freshness, cache, and fallback status.","public_status":"live_checks" if live else "registry_only","counts":counts,"connectors":rows,"display_guidance":["Never hide a dashboard solely because a source is temporarily unavailable.","Show last-known-good timestamps and stale labels.","Do not call periodic statistical data real time."]}

def methodology() -> Dict[str, Any]:
    return {"ok":True,"generated_at":_now(),"version_scope":"v1.9.0","title":"Sustainable Development Data Methodology","summary":"Normalization, provenance, freshness, and planetary-boundary assessment rules.","observation_schema":OBSERVATION_SCHEMA,"freshness_definitions":FRESHNESS_CLASSES,"methodology":["Preserve upstream series identifiers and revisions.","Normalize units only when conversion is deterministic and documented.","Retain disaggregation dimensions rather than flattening them into a single national value.","Separate observed, reported, modeled, forecast, and derived records.","Use explicit last-known-good and unavailable states.","Treat public dashboards as educational evidence infrastructure, not professional advice."],"hidden":["API credentials","raw exception traces","private analytics","unreviewed derived claims"]}

# v1.9.0 connector reliability, freshness, and schema-validation layer.
import json
import threading
import time
from datetime import timedelta
from email.utils import parsedate_to_datetime

_CACHE_LOCK = threading.RLock()
_CONNECTOR_CACHE: Dict[str, Dict[str, Any]] = {}
_FAILURE_STATE: Dict[str, Dict[str, Any]] = {}

FRESHNESS_THRESHOLDS_SECONDS = {
    "live": 15 * 60,
    "near_real_time": 6 * 60 * 60,
    "recent": 3 * 24 * 60 * 60,
    "daily": 2 * 24 * 60 * 60,
    "monthly": 45 * 24 * 60 * 60,
    "annual": 400 * 24 * 60 * 60,
    "periodic": 400 * 24 * 60 * 60,
    "historical": 10 * 365 * 24 * 60 * 60,
    "forecast": 14 * 24 * 60 * 60,
    "last_known_good": 7 * 24 * 60 * 60,
}

CONNECTOR_RESPONSE_SCHEMA = {
    "schema": "sc-sustainable-development-connector-response/1.1",
    "required": ["source_id", "status", "checked_at", "freshness_status", "schema_status"],
    "statuses": ["healthy", "degraded", "stale", "fallback_safe", "unavailable", "configured"],
    "freshness_statuses": ["fresh", "aging", "stale", "unknown", "last_known_good"],
    "schema_statuses": ["valid", "invalid", "not_checked"],
}


def _source_by_id(source_id: str) -> Dict[str, Any]:
    for item in SOURCE_REGISTRY:
        if item["source_id"] == source_id:
            return item
    raise KeyError(source_id)


def _parse_retry_after(value: str | None) -> int | None:
    if not value:
        return None
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        try:
            parsed = parsedate_to_datetime(value)
            return max(0, int((parsed - datetime.now(timezone.utc)).total_seconds()))
        except (TypeError, ValueError, OverflowError):
            return None


def classify_freshness(freshness_class: str, observed_at: str | None, *, last_known_good: bool = False) -> str:
    if last_known_good:
        return "last_known_good"
    if not observed_at:
        return "unknown"
    try:
        timestamp = datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return "unknown"
    age = max(0.0, (datetime.now(timezone.utc) - timestamp).total_seconds())
    threshold = FRESHNESS_THRESHOLDS_SECONDS.get(freshness_class, 400 * 24 * 60 * 60)
    if age <= threshold:
        return "fresh"
    if age <= threshold * 2:
        return "aging"
    return "stale"


def validate_observation(record: Dict[str, Any]) -> Dict[str, Any]:
    errors: List[str] = []
    warnings: List[str] = []
    for field in OBSERVATION_SCHEMA["required"]:
        if field not in record or record[field] in (None, ""):
            errors.append(f"Missing required field: {field}")
    if record.get("source_id") and record["source_id"] not in {x["source_id"] for x in SOURCE_REGISTRY}:
        errors.append("Unknown source_id")
    if record.get("observation_type") and record["observation_type"] not in OBSERVATION_SCHEMA["observation_types"]:
        errors.append("Unsupported observation_type")
    if record.get("freshness") and record["freshness"] not in FRESHNESS_CLASSES:
        errors.append("Unsupported freshness class")
    if "value" in record and not isinstance(record.get("value"), (int, float, str)):
        errors.append("value must be numeric or a source-preserved string")
    geography = record.get("geography")
    if geography is not None and not isinstance(geography, dict):
        errors.append("geography must be an object")
    if record.get("is_derived") and not record.get("methodology_version"):
        warnings.append("Derived records should include methodology_version")
    return {
        "ok": not errors,
        "schema": OBSERVATION_SCHEMA["schema"],
        "errors": errors,
        "warnings": warnings,
    }


def _validate_upstream_payload(source_id: str, content_type: str, body: bytes) -> Dict[str, Any]:
    errors: List[str] = []
    warnings: List[str] = []
    if not body:
        errors.append("Empty upstream response")
    is_json = "json" in (content_type or "").lower() or body[:1] in (b"{", b"[")
    parsed: Any = None
    if is_json and body:
        try:
            parsed = json.loads(body.decode("utf-8", errors="replace"))
        except json.JSONDecodeError:
            errors.append("Invalid JSON response")
    if parsed is not None:
        if source_id == "nasa-eonet" and not isinstance(parsed, dict):
            errors.append("EONET response must be an object")
        elif source_id == "nasa-eonet" and "events" not in parsed:
            warnings.append("EONET response does not include events")
        elif source_id == "un-sdg" and not isinstance(parsed, (dict, list)):
            errors.append("UN SDG response must be an object or list")
        elif source_id == "world-bank-indicators" and not isinstance(parsed, list):
            warnings.append("World Bank response normally uses a list envelope")
    return {"ok": not errors, "errors": errors, "warnings": warnings, "content_type": content_type or "unknown"}


def _cache_record(source_id: str, payload: Dict[str, Any], ttl_seconds: int, stale_ttl_seconds: int) -> None:
    now = datetime.now(timezone.utc)
    with _CACHE_LOCK:
        _CONNECTOR_CACHE[source_id] = {
            "payload": payload,
            "stored_at": now.isoformat(),
            "expires_at": (now + timedelta(seconds=ttl_seconds)).isoformat(),
            "stale_expires_at": (now + timedelta(seconds=stale_ttl_seconds)).isoformat(),
        }


def _cached_record(source_id: str) -> Dict[str, Any] | None:
    with _CACHE_LOCK:
        row = _CONNECTOR_CACHE.get(source_id)
        return dict(row) if row else None


def _probe_connector(item: Dict[str, Any], settings: Settings, *, force: bool = False) -> Dict[str, Any]:
    source_id = item["source_id"]
    cached = _cached_record(source_id)
    now = datetime.now(timezone.utc)
    if cached and not force:
        expires = datetime.fromisoformat(cached["expires_at"])
        if now <= expires:
            payload = dict(cached["payload"])
            payload.update({"cache_state": "fresh_cache", "served_from_cache": True})
            return payload

    failure = _FAILURE_STATE.get(source_id, {})
    circuit_until = failure.get("circuit_open_until")
    if circuit_until and now < datetime.fromisoformat(circuit_until):
        if cached and now <= datetime.fromisoformat(cached["stale_expires_at"]):
            payload = dict(cached["payload"])
            payload.update({"status": "fallback_safe", "freshness_status": "last_known_good", "cache_state": "stale_while_revalidate", "served_from_cache": True, "detail": "Circuit breaker open; serving last-known-good status."})
            return payload
        return {"source_id": source_id, "label": item["title"], "status": "unavailable", "checked_at": _now(), "freshness_status": "unknown", "schema_status": "not_checked", "cache_state": "miss", "served_from_cache": False, "detail": "Circuit breaker open after repeated upstream failures."}

    if not item.get("health_path"):
        return {"source_id": source_id, "label": item["title"], "status": "configured", "checked_at": _now(), "freshness_status": "unknown", "schema_status": "not_checked", "cache_state": "not_applicable", "served_from_cache": False, "detail": "No stable public health endpoint is registered; connector remains metadata-only."}

    attempts = max(1, int(getattr(settings, "sustainable_development_retry_attempts", 3)))
    backoff = float(getattr(settings, "sustainable_development_retry_backoff_seconds", 0.25))
    last_error = "unknown"
    rate_limited = False
    retry_after = None
    started = time.perf_counter()
    for attempt in range(1, attempts + 1):
        try:
            req = Request(item["base_url"] + item["health_path"], headers={"User-Agent": "SustainableCatalystSiteIntelligence/1.9.0", "Accept": "application/json,text/csv,*/*"})
            with urlopen(req, timeout=settings.external_request_timeout_seconds) as resp:
                body = resp.read(262144)
                validation = _validate_upstream_payload(source_id, resp.headers.get("Content-Type", ""), body)
                status = "healthy" if validation["ok"] else "degraded"
                payload = {
                    "source_id": source_id,
                    "label": item["title"],
                    "status": status,
                    "checked_at": _now(),
                    "freshness_status": "fresh",
                    "schema_status": "valid" if validation["ok"] else "invalid",
                    "cache_state": "refreshed",
                    "served_from_cache": False,
                    "http_status": int(resp.status),
                    "attempts": attempt,
                    "latency_ms": round((time.perf_counter() - started) * 1000, 1),
                    "rate_limited": False,
                    "schema_warnings": validation["warnings"],
                    "detail": f"Upstream returned HTTP {resp.status}; response schema {'validated' if validation['ok'] else 'requires review'}.",
                }
                _FAILURE_STATE.pop(source_id, None)
                _cache_record(source_id, payload, item["cache_ttl_seconds"], int(getattr(settings, "sustainable_development_stale_ttl_seconds", 604800)))
                return payload
        except HTTPError as exc:
            last_error = f"HTTP {exc.code}"
            if exc.code == 429:
                rate_limited = True
                retry_after = _parse_retry_after(exc.headers.get("Retry-After"))
                break
            if 400 <= exc.code < 500:
                break
        except (URLError, TimeoutError, OSError) as exc:
            last_error = exc.__class__.__name__
        if attempt < attempts:
            time.sleep(min(backoff * (2 ** (attempt - 1)), 2.0))

    failures = int(failure.get("consecutive_failures", 0)) + 1
    threshold = int(getattr(settings, "sustainable_development_circuit_breaker_failures", 3))
    state = {"consecutive_failures": failures, "last_error": last_error, "last_failure_at": _now()}
    if failures >= threshold:
        state["circuit_open_until"] = (now + timedelta(seconds=int(getattr(settings, "sustainable_development_circuit_breaker_seconds", 300)))).isoformat()
    _FAILURE_STATE[source_id] = state

    if cached and now <= datetime.fromisoformat(cached["stale_expires_at"]):
        payload = dict(cached["payload"])
        payload.update({"status": "fallback_safe", "freshness_status": "last_known_good", "cache_state": "stale_while_revalidate", "served_from_cache": True, "rate_limited": rate_limited, "retry_after_seconds": retry_after, "attempts": attempts, "detail": f"Upstream unavailable ({last_error}); serving last-known-good status."})
        return payload
    return {"source_id": source_id, "label": item["title"], "status": "unavailable" if failures >= threshold else "degraded", "checked_at": _now(), "freshness_status": "unknown", "schema_status": "not_checked", "cache_state": "miss", "served_from_cache": False, "rate_limited": rate_limited, "retry_after_seconds": retry_after, "attempts": attempts, "detail": f"Upstream check failed ({last_error}); no last-known-good record is available."}


def connector_reliability(settings: Settings, *, live: bool = False, force: bool = False) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    enabled = bool(live and settings.sustainable_development_live_checks)
    for item in SOURCE_REGISTRY:
        if enabled:
            row = _probe_connector(item, settings, force=force)
        else:
            row = {"source_id": item["source_id"], "label": item["title"], "status": "configured", "checked_at": _now(), "freshness_status": "unknown", "schema_status": "not_checked", "cache_state": "registry_only", "served_from_cache": False, "detail": "Live reliability checks are disabled; registry metadata remains available."}
        row.update({"freshness_class": item["freshness_class"], "cache_ttl_seconds": item["cache_ttl_seconds"], "stale_ttl_seconds": int(getattr(settings, "sustainable_development_stale_ttl_seconds", 604800))})
        rows.append(row)
    statuses = {status: sum(1 for row in rows if row["status"] == status) for status in CONNECTOR_RESPONSE_SCHEMA["statuses"]}
    return {"ok": True, "generated_at": _now(), "version_scope": "v1.9.0", "title": "Sustainable Development Connector Reliability", "summary": "Retry, circuit-breaker, schema-validation, freshness, cache, rate-limit, and last-known-good status.", "live_checks": enabled, "counts": statuses, "connectors": rows, "response_schema": CONNECTOR_RESPONSE_SCHEMA}


def freshness_policy() -> Dict[str, Any]:
    rows = []
    for item in SOURCE_REGISTRY:
        rows.append({"source_id": item["source_id"], "label": item["title"], "freshness_class": item["freshness_class"], "fresh_seconds": FRESHNESS_THRESHOLDS_SECONDS[item["freshness_class"]], "aging_seconds": FRESHNESS_THRESHOLDS_SECONDS[item["freshness_class"]] * 2, "cache_ttl_seconds": item["cache_ttl_seconds"]})
    return {"ok": True, "generated_at": _now(), "version_scope": "v1.9.0", "title": "Sustainable Development Freshness Policy", "classes": FRESHNESS_CLASSES, "thresholds": rows, "public_labels": ["fresh", "aging", "stale", "last_known_good", "unknown", "temporarily_unavailable"]}


def schema_validation_report() -> Dict[str, Any]:
    sample = {"source_id": "nasa-power", "indicator_id": "T2M", "geography": {"type": "point", "latitude": 41.8781, "longitude": -87.6298}, "period": "2026-07-10", "value": 25.0, "unit": "celsius", "freshness": "recent", "observation_type": "observed", "retrieved_at": _now(), "is_derived": False}
    source_checks = []
    for item in SOURCE_REGISTRY:
        missing = [field for field in ("source_id", "title", "organization", "family", "base_url", "access_type", "freshness_class", "cache_ttl_seconds", "limitations") if field not in item or item[field] in (None, "")]
        source_checks.append({"source_id": item["source_id"], "valid": not missing, "missing": missing})
    return {"ok": all(x["valid"] for x in source_checks), "generated_at": _now(), "version_scope": "v1.9.0", "title": "Connector and Observation Schema Validation", "registry_schema": {"valid": all(x["valid"] for x in source_checks), "sources": source_checks}, "observation_schema": OBSERVATION_SCHEMA, "connector_response_schema": CONNECTOR_RESPONSE_SCHEMA, "sample_validation": validate_observation(sample)}


def connector_cache_status() -> Dict[str, Any]:
    rows = []
    now = datetime.now(timezone.utc)
    with _CACHE_LOCK:
        cache_copy = {key: dict(value) for key, value in _CONNECTOR_CACHE.items()}
    for item in SOURCE_REGISTRY:
        cached = cache_copy.get(item["source_id"])
        if not cached:
            rows.append({"source_id": item["source_id"], "state": "empty", "stored_at": None, "expires_at": None, "stale_expires_at": None})
            continue
        expires = datetime.fromisoformat(cached["expires_at"])
        stale_expires = datetime.fromisoformat(cached["stale_expires_at"])
        state = "fresh" if now <= expires else "stale_servable" if now <= stale_expires else "expired"
        rows.append({"source_id": item["source_id"], "state": state, "stored_at": cached["stored_at"], "expires_at": cached["expires_at"], "stale_expires_at": cached["stale_expires_at"]})
    return {"ok": True, "generated_at": _now(), "version_scope": "v1.9.0", "title": "Sustainable Development Connector Cache", "connectors": rows, "counts": {state: sum(1 for row in rows if row["state"] == state) for state in ("fresh", "stale_servable", "expired", "empty")}}
