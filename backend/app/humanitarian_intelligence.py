from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

SCHEMA = "sc-humanitarian-intelligence/1.0"

SOURCES: List[Dict[str, Any]] = [
    {"source_id":"gdacs","title":"Global Disaster Alert and Coordination System","organization":"United Nations / European Commission","base_url":"https://www.gdacs.org/gdacsapi/api","endpoint":"/Events/geteventlist/latest","freshness":"near_real_time","update_note":"Popular feeds are refreshed approximately every six minutes.","coverage":"global","access":"public_api","requires_key":False,"role":"multi-hazard alerts and preliminary impact context","limitations":"Preliminary alerts and impact estimates; not a substitute for national emergency authorities."},
    {"source_id":"reliefweb","title":"ReliefWeb API","organization":"UN Office for the Coordination of Humanitarian Affairs","base_url":"https://api.reliefweb.int/v1","endpoint":"/reports","freshness":"live_publication","update_note":"Updated whenever curated ReliefWeb content is published.","coverage":"global","access":"public_api_appname","requires_key":False,"role":"humanitarian reports, disasters, assessments, maps, and situation updates","limitations":"A pre-approved appname is required for production API use from November 2025."},
    {"source_id":"usgs-earthquakes","title":"USGS Real-time Earthquake Feeds","organization":"U.S. Geological Survey","base_url":"https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary","endpoint":"/all_hour.geojson","freshness":"real_time","update_note":"GeoJSON summary feeds are designed for automated current-event displays.","coverage":"global","access":"public_feed","requires_key":False,"role":"earthquake location, magnitude, depth, time, and product links","limitations":"Event parameters can be revised as scientific review continues."},
    {"source_id":"nasa-eonet","title":"NASA EONET","organization":"NASA Earth Observatory Natural Event Tracker","base_url":"https://eonet.gsfc.nasa.gov/api/v3","endpoint":"/events?status=open&limit=100","freshness":"near_real_time","update_note":"Continuously updated curated natural-event metadata.","coverage":"global","access":"public_api","requires_key":False,"role":"natural-event discovery and imagery references","limitations":"For visualization and general information; spatial and temporal extents may be approximate."},
    {"source_id":"unhcr-refugee-statistics","title":"UNHCR Refugee Statistics API","organization":"UN High Commissioner for Refugees","base_url":"https://api.unhcr.org/population/v1","endpoint":"/population/","freshness":"periodic_official","update_note":"Official displacement statistics follow UNHCR statistical release cycles.","coverage":"global","access":"public_api","requires_key":False,"role":"refugees, asylum seekers, internally displaced, stateless, returned, and resettled populations","limitations":"Not a real-time movement tracker; years, population categories, and geographic definitions require careful interpretation."},
]

EVENT_CATEGORIES = [
    {"id":"earthquake","label":"Earthquake","sources":["usgs-earthquakes","gdacs","nasa-eonet"]},
    {"id":"tropical-cyclone","label":"Tropical cyclone","sources":["gdacs","nasa-eonet","reliefweb"]},
    {"id":"flood","label":"Flood","sources":["gdacs","nasa-eonet","reliefweb"]},
    {"id":"wildfire","label":"Wildfire","sources":["gdacs","nasa-eonet","reliefweb"]},
    {"id":"volcano","label":"Volcano","sources":["gdacs","nasa-eonet","reliefweb"]},
    {"id":"drought","label":"Drought","sources":["gdacs","nasa-eonet","reliefweb"]},
    {"id":"displacement","label":"Forced displacement","sources":["unhcr-refugee-statistics","reliefweb"]},
]

NORMALIZED_EVENT_SCHEMA = {
    "schema": SCHEMA,
    "required": ["event_id","source_id","event_type","title","started_at","geographies","freshness","retrieved_at"],
    "optional": ["ended_at","coordinates","severity","alert_level","magnitude","depth_km","affected_population","displacement_context","source_url","report_count","caveats"],
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def source_registry() -> Dict[str, Any]:
    return {
        "ok": True, "generated_at": _now(), "version_scope": "v1.10.0", "schema": SCHEMA,
        "title": "Live Disaster, Displacement, and Humanitarian Source Registry",
        "summary": "Public-source registry for hazards, humanitarian reporting, earthquakes, natural events, and official displacement statistics.",
        "counts": {"sources": len(SOURCES), "no_key_required": sum(not x["requires_key"] for x in SOURCES)},
        "connectors": [{**x, "slug": x["source_id"], "label": x["title"], "status": "registered", "source_mode": x["access"], "safe_display": x["limitations"]} for x in SOURCES],
    }


def overview() -> Dict[str, Any]:
    return {
        "ok": True, "generated_at": _now(), "version_scope": "v1.10.0", "schema": SCHEMA,
        "title": "Live Disaster, Displacement, and Humanitarian Intelligence",
        "summary": "A source-aware public observatory linking physical hazards, humanitarian reporting, and displacement context without presenting itself as an emergency-warning or legal-determination service.",
        "sources": SOURCES, "categories": EVENT_CATEGORIES,
        "freshness_labels": ["real_time","near_real_time","live_publication","periodic_official","last_known_good","temporarily_unavailable"],
        "public_boundaries": [
            "Use national and local authorities for emergency instructions.",
            "Treat GDACS estimates as preliminary.",
            "Treat EONET extents as approximate visualization metadata.",
            "Treat UNHCR statistics as official periodic population statistics, not live movements.",
            "Preserve the publication date and source of every ReliefWeb report.",
        ],
    }


def crisis_map() -> Dict[str, Any]:
    return {
        "ok": True, "generated_at": _now(), "version_scope": "v1.10.0", "schema": SCHEMA,
        "title": "Global Crisis Map",
        "summary": "Map-ready source contracts for current hazards and humanitarian context.",
        "layers": [
            {"id":"gdacs-alerts","label":"GDACS alerts","source_id":"gdacs","geometry":"point_or_polygon","status":"connector_ready"},
            {"id":"usgs-earthquakes","label":"USGS earthquakes","source_id":"usgs-earthquakes","geometry":"point","status":"connector_ready"},
            {"id":"eonet-events","label":"NASA EONET events","source_id":"nasa-eonet","geometry":"point_or_polygon","status":"connector_ready"},
            {"id":"reliefweb-disasters","label":"ReliefWeb disasters and reports","source_id":"reliefweb","geometry":"country_or_region","status":"appname_required_for_live_production"},
            {"id":"unhcr-displacement","label":"UNHCR displacement context","source_id":"unhcr-refugee-statistics","geometry":"country_or_subnational_where_available","status":"periodic_context"},
        ],
        "events": [],
        "display_state": "registry_ready",
        "note": "Live event records are fetched by the connector runtime after deployment; empty arrays do not imply no active crises.",
    }


def displacement_context() -> Dict[str, Any]:
    return {
        "ok": True, "generated_at": _now(), "version_scope": "v1.10.0", "schema": SCHEMA,
        "title": "Displacement Context",
        "summary": "Official periodic forced-displacement context linked to current humanitarian situations.",
        "population_categories": ["refugees","asylum_seekers","internally_displaced","stateless_people","returned_refugees","returned_idps","resettled_refugees"],
        "sources": [x for x in SOURCES if x["source_id"] in {"unhcr-refugee-statistics","reliefweb"}],
        "methodology": ["Keep population category definitions separate.","Display reference year prominently.","Do not infer legal status from aggregate counts.","Do not call periodic statistics real time."],
    }


def humanitarian_reports() -> Dict[str, Any]:
    return {
        "ok": True, "generated_at": _now(), "version_scope": "v1.10.0", "schema": SCHEMA,
        "title": "Humanitarian Report Stream",
        "summary": "Curated report and situation-update layer designed for ReliefWeb integration.",
        "source": next(x for x in SOURCES if x["source_id"] == "reliefweb"),
        "filters": ["country","disaster","theme","source organization","publication date","language","format"],
        "reports": [], "display_state": "connector_ready_appname_required",
    }


def methodology() -> Dict[str, Any]:
    return {
        "ok": True, "generated_at": _now(), "version_scope": "v1.10.0", "schema": SCHEMA,
        "title": "Disaster and Humanitarian Intelligence Methodology",
        "normalized_event_schema": NORMALIZED_EVENT_SCHEMA,
        "source_roles": {x["source_id"]: x["role"] for x in SOURCES},
        "rules": [
            "Never merge records from different sources without retaining every source identifier.",
            "Separate physical hazard observations from humanitarian reports and displacement statistics.",
            "Do not present preliminary impact estimates as confirmed losses.",
            "Use explicit source freshness and last-known-good states.",
            "Do not provide emergency, legal, immigration, protection-status, or humanitarian eligibility advice.",
        ],
    }


def export_manifest() -> Dict[str, Any]:
    return {
        "ok": True, "generated_at": _now(), "version_scope": "v1.10.0", "schema": SCHEMA,
        "title": "Humanitarian Intelligence Export Manifest",
        "formats": ["json","csv-ready"],
        "datasets": ["source_registry","event_categories","crisis_map_layers","displacement_context","humanitarian_report_contract"],
        "records": {"sources": SOURCES, "categories": EVENT_CATEGORIES, "event_schema": NORMALIZED_EVENT_SCHEMA},
        "required_attribution": True,
    }
