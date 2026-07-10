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
    return {"ok":True,"generated_at":_now(),"version_scope":"v1.6.0","title":"Sustainable Development Public Source Registry","summary":"Public-source registry for planetary boundaries, SDGs, poverty, education, food, water, climate, and human development.","counts":{"sources":len(connectors),"families":len(set(x["family"] for x in connectors)),"no_key_required":sum(not x["requires_key"] for x in connectors)},"connectors":connectors,"freshness_definitions":FRESHNESS_CLASSES,"methodology":["Official, observational, modeled, research, and derived records remain explicitly distinguished.","A current observation does not automatically constitute an official planetary-boundary assessment.","Every public value should retain source, geography, period, unit, freshness, and caveat metadata."],"observation_schema":OBSERVATION_SCHEMA}

def source_families() -> Dict[str, Any]:
    groups={}
    for item in SOURCE_REGISTRY:
        groups.setdefault(item["family"],[]).append(item["source_id"])
    return {"ok":True,"generated_at":_now(),"version_scope":"v1.6.0","title":"Sustainable Development Connector Families","summary":"Connector coverage across environmental limits and human development.","families":[{"family":k,"source_count":len(v),"sources":v} for k,v in sorted(groups.items())]}

def planetary_boundary_registry() -> Dict[str, Any]:
    return {"ok":True,"generated_at":_now(),"version_scope":"v1.6.0","title":"Planetary Boundaries Adapter Registry","summary":"Boundary definitions and source mappings for future derived, methodology-forward assessments.","boundaries":PLANETARY_BOUNDARIES,"counts":{"boundaries":len(PLANETARY_BOUNDARIES),"adapter_ready":sum(x["assessment_status"]=="derived_adapter_ready" for x in PLANETARY_BOUNDARIES)},"methodology":["Threshold definitions must be sourced from peer-reviewed planetary-boundary research.","Site Intelligence assessments must be labeled derived unless directly reproduced from an official assessment.","Underlying indicators and assessment conclusions are separate records."]}

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
    return {"ok":True,"generated_at":_now(),"version_scope":"v1.6.0","title":"Sustainable Development Connector Health","summary":"Public-safe source health, freshness, cache, and fallback status.","public_status":"live_checks" if live else "registry_only","counts":counts,"connectors":rows,"display_guidance":["Never hide a dashboard solely because a source is temporarily unavailable.","Show last-known-good timestamps and stale labels.","Do not call periodic statistical data real time."]}

def methodology() -> Dict[str, Any]:
    return {"ok":True,"generated_at":_now(),"version_scope":"v1.6.0","title":"Sustainable Development Data Methodology","summary":"Normalization, provenance, freshness, and planetary-boundary assessment rules.","observation_schema":OBSERVATION_SCHEMA,"freshness_definitions":FRESHNESS_CLASSES,"methodology":["Preserve upstream series identifiers and revisions.","Normalize units only when conversion is deterministic and documented.","Retain disaggregation dimensions rather than flattening them into a single national value.","Separate observed, reported, modeled, forecast, and derived records.","Use explicit last-known-good and unavailable states.","Treat public dashboards as educational evidence infrastructure, not professional advice."],"hidden":["API credentials","raw exception traces","private analytics","unreviewed derived claims"]}
