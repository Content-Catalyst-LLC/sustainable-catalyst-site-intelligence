from __future__ import annotations

from csv import DictWriter
from datetime import datetime, timezone
from html import escape
from io import StringIO
import json
import re
from typing import Any, Iterable

from .earth_observation_studio import diagnostics as earth_diagnostics
from .live_country_intelligence import countries_diagnostics
from .unified_live_events import sources_summary
from .version import APP_VERSION

VERSION = APP_VERSION
SCHEMA_VERSION = "sc-source-methodology/1.0"
METHODOLOGY_VERSION = "2026.07"
ALLOWED_EXPORT_FORMATS = ("json", "csv")

PUBLIC_STATES = {
    "live": {
        "label": "Live",
        "description": "The backend recently retrieved or verified the public source successfully.",
    },
    "cached": {
        "label": "Cached",
        "description": "A recently retrieved public record is being served from cache.",
    },
    "stale": {
        "label": "Stale",
        "description": "A last-known-good record is available but is older than the normal freshness window.",
    },
    "temporarily-unavailable": {
        "label": "Temporarily unavailable",
        "description": "The source could not be reached or validated during the latest public-safe check.",
    },
    "experimental": {
        "label": "Experimental",
        "description": "The connector or layer is public but still subject to availability, schema, or interpretation review.",
    },
    "disabled": {
        "label": "Disabled",
        "description": "The source is registered but intentionally not active in the public application.",
    },
}

SOURCE_RECORDS: list[dict[str, Any]] = [
    {
        "id": "world-bank",
        "name": "World Bank Open Data",
        "publisher": "World Bank",
        "authority": "official-intergovernmental-source",
        "domains": ["human-development", "infrastructure", "economy", "environment"],
        "data_types": ["country catalog", "country metadata", "indicator values", "time series"],
        "connector": "World Bank Country and Indicator APIs",
        "update_frequency": "Source dependent; most indicators are annual",
        "default_state": "live",
        "license": "World Bank Open Data terms and individual dataset metadata apply",
        "geographic_coverage": "Global country and territory catalog",
        "temporal_coverage": "Indicator dependent; historical annual series where available",
        "known_limits": [
            "Reporting years differ by indicator and country.",
            "Latest available values are not necessarily from the current year.",
            "Source definitions and modeled or estimated status must be reviewed before comparison.",
        ],
        "features": ["country", "compare", "thematic", "briefing"],
        "official_url": "https://data.worldbank.org/",
        "methodology_ids": ["latest-value-selection", "missing-values", "zero-vs-unavailable", "trend-construction", "reporting-year-differences", "indicator-compatibility", "cache-behavior"],
        "public_notes": "Site Intelligence keeps indicator IDs, units, years, source URLs, and delivery states visible.",
    },
    {
        "id": "nasa-gibs",
        "name": "NASA EOSDIS Global Imagery Browse Services",
        "publisher": "NASA Earth Science Data and Information System",
        "authority": "official-public-source",
        "domains": ["earth-observation", "climate-environment", "infrastructure"],
        "data_types": ["satellite imagery", "raster layers", "derived environmental products"],
        "connector": "NASA GIBS WMTS tile services",
        "update_frequency": "Layer dependent; daily, sub-daily, or composite",
        "default_state": "experimental",
        "license": "NASA Earth observation attribution and product-specific terms apply",
        "geographic_coverage": "Global or near-global depending on layer",
        "temporal_coverage": "Layer and sensor dependent",
        "known_limits": [
            "Cloud cover, compositing, sensor conditions, product latency, and missing dates may affect appearance.",
            "Spatial and temporal resolution differ by layer.",
            "Rendered map tiles are interpretive context and do not replace authoritative ground records.",
        ],
        "features": ["earth", "overview", "thematic", "briefing"],
        "official_url": "https://www.earthdata.nasa.gov/eosdis/science-system-description/eosdis-components/gibs",
        "methodology_ids": ["earth-date-validation", "imagery-interpretation", "delivery-states", "optional-source-failures", "export-generation"],
        "public_notes": "Every public layer retains source, attribution, temporal resolution, spatial resolution, observation type, and known limits.",
    },
    {
        "id": "usgs-earthquakes",
        "name": "USGS Earthquake Hazards Program",
        "publisher": "United States Geological Survey",
        "authority": "official-public-source",
        "domains": ["events", "human-security", "climate-environment", "infrastructure"],
        "data_types": ["earthquake events", "magnitude", "location", "event time"],
        "connector": "USGS GeoJSON earthquake feeds",
        "update_frequency": "Near real time; records may be revised",
        "default_state": "live",
        "license": "USGS public data policies apply",
        "geographic_coverage": "Global earthquake records",
        "temporal_coverage": "Selected rolling event window",
        "known_limits": [
            "Event parameters may change as USGS revises a record.",
            "The Site Intelligence event view is not an emergency-alert service.",
            "Country assignment may use coordinates or descriptive place strings and retains the match method.",
        ],
        "features": ["overview", "events", "country", "compare", "thematic", "briefing"],
        "official_url": "https://earthquake.usgs.gov/earthquakes/feed/",
        "methodology_ids": ["country-event-matching", "event-deduplication", "delivery-states", "optional-source-failures"],
        "public_notes": "Original USGS source links and source event IDs are preserved when available.",
    },
    {
        "id": "nasa-eonet",
        "name": "NASA Earth Observatory Natural Event Tracker",
        "publisher": "NASA Earth Observatory",
        "authority": "official-public-aggregator",
        "domains": ["events", "climate-environment", "human-security", "earth-observation"],
        "data_types": ["natural event metadata", "event geometry", "source links"],
        "connector": "NASA EONET API",
        "update_frequency": "Source dependent; updated as event records change",
        "default_state": "live",
        "license": "NASA EONET and originating-source terms apply",
        "geographic_coverage": "Global natural events",
        "temporal_coverage": "Selected rolling event window",
        "known_limits": [
            "EONET aggregates metadata from other source agencies.",
            "Event geometry and status may be incomplete or revised.",
            "An event shown near another layer does not establish causation.",
        ],
        "features": ["overview", "events", "country", "compare", "thematic", "briefing"],
        "official_url": "https://eonet.gsfc.nasa.gov/",
        "methodology_ids": ["country-event-matching", "event-deduplication", "delivery-states", "optional-source-failures"],
        "public_notes": "Site Intelligence preserves the originating source link when EONET provides one.",
    },
    {
        "id": "reliefweb",
        "name": "ReliefWeb",
        "publisher": "United Nations Office for the Coordination of Humanitarian Affairs",
        "authority": "official-humanitarian-aggregator",
        "domains": ["events", "human-security", "human-development"],
        "data_types": ["humanitarian reports", "country metadata", "publication records"],
        "connector": "ReliefWeb API",
        "update_frequency": "Continuous publication index",
        "default_state": "live",
        "license": "ReliefWeb API and originating-publisher terms apply",
        "geographic_coverage": "Global humanitarian reporting",
        "temporal_coverage": "Selected rolling publication window",
        "known_limits": [
            "ReliefWeb indexes reports from many originating publishers.",
            "A report is not equivalent to a verified incident count or needs assessment.",
            "Publication time and event time may differ.",
        ],
        "features": ["events", "country", "compare", "thematic", "briefing"],
        "official_url": "https://reliefweb.int/",
        "methodology_ids": ["country-event-matching", "event-deduplication", "delivery-states", "optional-source-failures"],
        "public_notes": "Country fields supplied by ReliefWeb are preferred over inferred country matching.",
    },
    {
        "id": "nasa-power",
        "name": "NASA POWER",
        "publisher": "NASA Langley Research Center",
        "authority": "official-public-source",
        "domains": ["climate-environment", "energy"],
        "data_types": ["meteorology", "solar energy", "climatology"],
        "connector": "NASA POWER API",
        "update_frequency": "Product dependent",
        "default_state": "experimental",
        "license": "NASA POWER terms and attribution apply",
        "geographic_coverage": "Global gridded products",
        "temporal_coverage": "Product dependent",
        "known_limits": ["Gridded and modeled products are not direct site measurements.", "The current flagship app uses this source selectively and may fall back to registered methodology records."],
        "features": ["legacy-dashboards", "source-methodology"],
        "official_url": "https://power.larc.nasa.gov/",
        "methodology_ids": ["delivery-states", "cache-behavior", "optional-source-failures"],
        "public_notes": "Registered for source-aware climate and energy context; not treated as a site assessment.",
    },
    {
        "id": "openstreetmap",
        "name": "OpenStreetMap",
        "publisher": "OpenStreetMap contributors",
        "authority": "community-maintained-public-source",
        "domains": ["basemap", "geospatial"],
        "data_types": ["basemap tiles", "place and infrastructure context"],
        "connector": "Public map tile service",
        "update_frequency": "Continuous community updates",
        "default_state": "live",
        "license": "Open Database License; map attribution required",
        "geographic_coverage": "Global",
        "temporal_coverage": "Current rendered basemap",
        "known_limits": ["Coverage and feature completeness vary by place.", "Displayed boundaries and labels are not final legal or cadastral determinations."],
        "features": ["overview", "earth", "events", "country", "compare", "thematic"],
        "official_url": "https://www.openstreetmap.org/copyright",
        "methodology_ids": ["imagery-interpretation", "export-generation"],
        "public_notes": "Attribution remains visible in interactive map views.",
    },
    {
        "id": "platform-core",
        "name": "Sustainable Catalyst Platform Core",
        "publisher": "Content Catalyst LLC",
        "authority": "optional-provenance-layer",
        "domains": ["provenance", "verification"],
        "data_types": ["evidence IDs", "source snapshots", "provenance activities"],
        "connector": "Optional backend integration",
        "update_frequency": "Only when enabled and configured",
        "default_state": "disabled",
        "license": "Sustainable Catalyst open-source project terms",
        "geographic_coverage": "Not applicable",
        "temporal_coverage": "Only records written while integration is enabled",
        "known_limits": ["Platform Core is intentionally optional.", "Its disabled state must not block public Site Intelligence views."],
        "features": ["country", "briefing", "source-methodology"],
        "official_url": "https://github.com/Content-Catalyst-LLC",
        "methodology_ids": ["brief-generation", "export-generation", "optional-source-failures"],
        "public_notes": "Disabled by default because Site Intelligence must operate without another paid persistent service.",
    },
]

METHODOLOGY_RECORDS: list[dict[str, Any]] = [
    {
        "id": "latest-value-selection",
        "title": "Latest valid indicator selection",
        "summary": "The latest non-null observation returned for a source indicator is selected while retaining the original reporting year.",
        "applies_to": ["country", "compare", "thematic", "briefing"],
        "rules": ["Null observations are skipped.", "The reporting year is never relabeled as the current year.", "No missing value is silently imputed."],
        "implementation_refs": ["live_country_intelligence.country_indicators", "comparative_intelligence.compare_indicators"],
        "limitations": ["Different indicators can have different latest reporting years."],
        "source_ids": ["world-bank"],
    },
    {
        "id": "missing-values",
        "title": "Missing-value handling",
        "summary": "Unavailable records remain visible as explicit data gaps instead of being removed or fabricated.",
        "applies_to": ["country", "compare", "thematic", "briefing", "exports"],
        "rules": ["Use explicit unavailable states.", "Keep available records visible when optional records fail.", "Preserve missing-data reasons in briefs and exports."],
        "implementation_refs": ["live_country_intelligence", "thematic_intelligence_dashboards", "public_briefing_export_studio"],
        "limitations": ["A missing value does not prove the underlying condition is absent."],
        "source_ids": ["world-bank", "usgs-earthquakes", "nasa-eonet", "reliefweb"],
    },
    {
        "id": "zero-vs-unavailable",
        "title": "Zero versus unavailable",
        "summary": "Numeric zero is treated as a valid observation and is never converted into a missing-value state.",
        "applies_to": ["country", "compare", "thematic", "exports"],
        "rules": ["Check explicitly for null or missing values.", "Render zero as zero.", "Do not use truthiness to determine availability."],
        "implementation_refs": ["live_country_intelligence", "comparative_intelligence", "thematic_intelligence_dashboards"],
        "limitations": ["Source definitions still determine what a reported zero means."],
        "source_ids": ["world-bank"],
    },
    {
        "id": "delivery-states",
        "title": "Live, cached, stale, fallback, and unavailable states",
        "summary": "Delivery state describes how the application received a record; it is separate from the substantive meaning of the data.",
        "applies_to": ["all-public-views"],
        "rules": ["Label live, cached, stale, reference-snapshot, experimental, and unavailable states.", "Do not call cached data live.", "Keep optional failures local."],
        "implementation_refs": ["country_cache", "unified_live_events", "earth_observation_studio"],
        "limitations": ["A live response can still contain older reporting periods."],
        "source_ids": ["world-bank", "nasa-gibs", "usgs-earthquakes", "nasa-eonet", "reliefweb", "nasa-power"],
    },
    {
        "id": "trend-construction",
        "title": "Trend construction",
        "summary": "Historical series preserve reported years and do not silently interpolate missing observations.",
        "applies_to": ["country", "compare", "thematic"],
        "rules": ["Sort observations chronologically.", "Keep explicit gap years.", "Provide accessible tables alongside charts."],
        "implementation_refs": ["live_country_intelligence.country_trends", "comparative_intelligence.compare_trends", "thematic_intelligence_dashboards.dashboard_trends"],
        "limitations": ["Changes in source methodology can affect apparent trends."],
        "source_ids": ["world-bank"],
    },
    {
        "id": "reporting-year-differences",
        "title": "Reporting-year differences",
        "summary": "Different reporting years remain visible and block direct mathematical differences when the comparison would be misleading.",
        "applies_to": ["compare", "briefing", "exports"],
        "rules": ["Display both reporting years.", "Label the mismatch.", "Do not calculate a difference across mismatched years."],
        "implementation_refs": ["comparative_intelligence._compatibility"],
        "limitations": ["Same-year values can still differ in collection method or coverage."],
        "source_ids": ["world-bank"],
    },
    {
        "id": "indicator-compatibility",
        "title": "Indicator compatibility",
        "summary": "Comparison requires aligned indicator IDs, units, definitions, source families, data states, and reporting periods.",
        "applies_to": ["compare", "briefing", "exports"],
        "rules": ["Distinguish aligned, year, source, unit, definition, state, partial, and unavailable conditions.", "Calculate only when all required checks pass.", "Never create an unexplained composite score."],
        "implementation_refs": ["comparative_intelligence.compare_indicators"],
        "limitations": ["Compatibility checks cannot remove every contextual difference between countries."],
        "source_ids": ["world-bank"],
    },
    {
        "id": "country-normalization",
        "title": "Country-name normalization",
        "summary": "Public display names and aliases improve findability while original source names remain stored separately.",
        "applies_to": ["country", "compare", "events", "thematic", "briefing"],
        "rules": ["Preserve source_name.", "Use ISO codes as stable identifiers.", "Support public aliases without rewriting source records."],
        "implementation_refs": ["live_country_intelligence._normalize_country"],
        "limitations": ["Territory and sovereignty classifications require careful source-specific interpretation."],
        "source_ids": ["world-bank"],
    },
    {
        "id": "country-event-matching",
        "title": "Country-event matching",
        "summary": "Event-country links retain the method and confidence used to associate a public event with a country.",
        "applies_to": ["events", "country", "compare", "thematic", "briefing"],
        "rules": ["Prefer provider country fields.", "Use geometry or country-name matching only when provider fields are absent.", "Retain country_match_method and country_match_confidence."],
        "implementation_refs": ["unified_live_events._country_match"],
        "limitations": ["Bounding boxes and place strings can be ambiguous near borders or for multi-country events."],
        "source_ids": ["usgs-earthquakes", "nasa-eonet", "reliefweb"],
    },
    {
        "id": "event-deduplication",
        "title": "Event deduplication",
        "summary": "Stable source-aware identifiers reduce duplicate rendering without collapsing distinct source records into one unsupported incident.",
        "applies_to": ["events", "compare", "thematic", "briefing"],
        "rules": ["Hash source, source event ID, title, and observation time.", "Preserve source-event identifiers.", "Keep distinct provider records separate when equivalence is not established."],
        "implementation_refs": ["unified_live_events._stable_id", "unified_live_events._deduplicate"],
        "limitations": ["Different providers may describe the same real-world event differently."],
        "source_ids": ["usgs-earthquakes", "nasa-eonet", "reliefweb"],
    },
    {
        "id": "earth-date-validation",
        "title": "Earth-observation date validation",
        "summary": "The interface validates selected dates before requesting imagery and treats missing tiles as a local availability state.",
        "applies_to": ["earth", "thematic", "briefing"],
        "rules": ["Require valid ISO dates.", "Require the before date not to exceed the after date.", "Show tile failure locally and allow retry or date changes."],
        "implementation_refs": ["earth_observation_studio", "public_app.applyEarthComparison"],
        "limitations": ["A syntactically valid date may still have no source imagery."],
        "source_ids": ["nasa-gibs"],
    },
    {
        "id": "imagery-interpretation",
        "title": "Earth-observation interpretation",
        "summary": "Satellite and derived layers are presented with resolution, observation type, attribution, and known limitations.",
        "applies_to": ["overview", "earth", "thematic", "briefing", "exports"],
        "rules": ["Keep attribution visible.", "Label derived and modeled products.", "Do not treat visual overlap as causation or imagery as direct ground truth."],
        "implementation_refs": ["earth_observation_studio.EARTH_LAYERS"],
        "limitations": ["Clouds, sensor geometry, composites, processing, and spatial resolution can change apparent conditions."],
        "source_ids": ["nasa-gibs", "openstreetmap"],
    },
    {
        "id": "comparison-calculations",
        "title": "Comparison calculations",
        "summary": "Differences and percentage changes are generated only for compatible records.",
        "applies_to": ["compare", "briefing", "exports"],
        "rules": ["Require calculation_eligible=true.", "Keep raw country values visible.", "Explain why an ineligible calculation was withheld."],
        "implementation_refs": ["comparative_intelligence"],
        "limitations": ["A valid mathematical difference is not by itself a causal or policy conclusion."],
        "source_ids": ["world-bank"],
    },
    {
        "id": "brief-generation",
        "title": "Brief generation",
        "summary": "Public briefs are deterministic documents built from selected evidence records, data gaps, sources, and interpretation limits.",
        "applies_to": ["briefing", "country", "compare", "events", "earth", "thematic"],
        "rules": ["Use a canonical investigation manifest.", "Preserve sources and gaps.", "Keep generated prose separate from retrieved evidence if AI is later enabled."],
        "implementation_refs": ["public_briefing_export_studio"],
        "limitations": ["Briefs summarize available public evidence and do not certify completeness."],
        "source_ids": ["world-bank", "nasa-gibs", "usgs-earthquakes", "nasa-eonet", "reliefweb", "platform-core"],
    },
    {
        "id": "export-generation",
        "title": "Export generation",
        "summary": "JSON, CSV, HTML, print, and browser captures preserve source identity and responsible-use boundaries.",
        "applies_to": ["compare", "thematic", "briefing", "source-methodology"],
        "rules": ["Include application and schema versions.", "Use UTF-8 CSV safeguards.", "Keep source URLs visible in print-ready HTML.", "Do not claim a browser screenshot is an authoritative source record."],
        "implementation_refs": ["comparative_intelligence", "thematic_intelligence_dashboards", "public_briefing_export_studio"],
        "limitations": ["PNG output may omit third-party tiles when browser cross-origin protections apply."],
        "source_ids": ["world-bank", "nasa-gibs", "usgs-earthquakes", "nasa-eonet", "reliefweb", "openstreetmap"],
    },
    {
        "id": "cache-behavior",
        "title": "Cache and stale-record behavior",
        "summary": "In-memory and JSON last-known-good caching reduce repeated requests and preserve useful public states during temporary upstream failures.",
        "applies_to": ["country", "events", "compare", "thematic", "briefing"],
        "rules": ["Record retrieved_at and stale state.", "Prefer a validated last-known-good record over fabricated data.", "Do not represent stale data as current live data."],
        "implementation_refs": ["country_cache", "live_country_intelligence", "unified_live_events"],
        "limitations": ["The Render filesystem is ephemeral and JSON persistence may not survive every deployment."],
        "source_ids": ["world-bank", "usgs-earthquakes", "nasa-eonet", "reliefweb", "nasa-power"],
    },
    {
        "id": "optional-source-failures",
        "title": "Optional-source failure isolation",
        "summary": "A failed optional connector produces a local source state and does not disable unrelated public evidence.",
        "applies_to": ["all-public-views"],
        "rules": ["Do not show application-wide nag banners.", "Keep local retry controls where useful.", "Continue rendering validated records from other sources."],
        "implementation_refs": ["unified_live_events", "thematic_intelligence_dashboards", "public_briefing_export_studio"],
        "limitations": ["A partial view may not contain every source normally associated with the topic."],
        "source_ids": ["world-bank", "nasa-gibs", "usgs-earthquakes", "nasa-eonet", "reliefweb", "nasa-power", "platform-core"],
    },
    {
        "id": "saved-view-state",
        "title": "Saved views and shareable research paths",
        "summary": "Public interface configuration is stored locally as a validated, portable manifest and can be reconstructed from public URL parameters.",
        "applies_to": ["overview", "earth", "country", "events", "compare", "thematic", "briefing", "sources", "saved"],
        "rules": ["Use browser localStorage only.", "Store public interface parameters rather than evidence payloads.", "Reject sensitive-looking fields and unsupported routes.", "Validate imported manifests without server persistence.", "Keep shared URLs limited to public state."],
        "implementation_refs": ["saved_views", "public_app.savedViewsState", "public_app.savedViewUrl"],
        "limitations": ["Local browser storage does not synchronize across devices and is removed when the user clears site data."],
        "source_ids": [],
    },
]


class SourceMethodologyError(ValueError):
    """Public-safe validation error for source and methodology records."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize(value: str | None) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _source_index() -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in SOURCE_RECORDS}


def _methodology_index() -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in METHODOLOGY_RECORDS}


def _state_label(state: str) -> str:
    return PUBLIC_STATES.get(state, PUBLIC_STATES["temporarily-unavailable"])["label"]


def _record_with_state(record: dict[str, Any], dynamic_states: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    status = (dynamic_states or {}).get(record["id"], {})
    state = status.get("state") or record["default_state"]
    result = {
        **record,
        "state": state,
        "state_label": _state_label(state),
        "last_checked": status.get("last_checked"),
        "last_successful_retrieval": status.get("last_successful_retrieval"),
        "status_note": status.get("status_note") or PUBLIC_STATES[state]["description"],
    }
    return result


def _public_dynamic_states() -> tuple[dict[str, dict[str, Any]], list[dict[str, str]]]:
    checked = _now()
    states: dict[str, dict[str, Any]] = {}
    issues: list[dict[str, str]] = []

    try:
        country = countries_diagnostics()
        catalog_state = str(country.get("catalog_state") or country.get("state") or "").lower()
        state = "live" if catalog_state == "live" else "cached" if "cache" in catalog_state else "stale" if "stale" in catalog_state else "temporarily-unavailable"
        states["world-bank"] = {
            "state": state,
            "last_checked": checked,
            "last_successful_retrieval": country.get("fetched_at") or country.get("retrieved_at"),
            "status_note": f"Country catalog diagnostic state: {catalog_state or 'unavailable'}.",
        }
    except Exception:
        states["world-bank"] = {"state": "temporarily-unavailable", "last_checked": checked, "status_note": "The country connector diagnostic did not complete."}
        issues.append({"source_id": "world-bank", "state": "temporarily-unavailable"})

    try:
        events = sources_summary(days=1)
        for item in events.get("sources", []):
            source_id = str(item.get("id") or "")
            mapped = {"usgs": "usgs-earthquakes", "nasa-eonet": "nasa-eonet", "reliefweb": "reliefweb"}.get(source_id)
            if not mapped:
                continue
            raw_state = str(item.get("state") or "not-requested").lower()
            state = "live" if raw_state == "live" else "cached" if "cache" in raw_state else "stale" if "stale" in raw_state else "temporarily-unavailable"
            states[mapped] = {
                "state": state,
                "last_checked": checked,
                "last_successful_retrieval": events.get("generated_at") if state in {"live", "cached", "stale"} else None,
                "status_note": f"Public event diagnostic state: {raw_state}.",
            }
            if state == "temporarily-unavailable":
                issues.append({"source_id": mapped, "state": state})
    except Exception:
        for mapped in ("usgs-earthquakes", "nasa-eonet", "reliefweb"):
            states[mapped] = {"state": "temporarily-unavailable", "last_checked": checked, "status_note": "The optional event-source diagnostic did not complete."}
            issues.append({"source_id": mapped, "state": "temporarily-unavailable"})

    try:
        earth = earth_diagnostics()
        layer_checks = earth.get("layers", [])
        ready = bool(layer_checks) and all(bool(item.get("tile_template_present") and item.get("https") and item.get("attribution_present")) for item in layer_checks)
        states["nasa-gibs"] = {
            "state": "experimental" if ready else "temporarily-unavailable",
            "last_checked": checked,
            "last_successful_retrieval": None,
            "status_note": f"{len(layer_checks)} registered Earth-observation layer definitions passed public metadata checks." if ready else "Earth layer metadata checks are incomplete.",
        }
    except Exception:
        states["nasa-gibs"] = {"state": "temporarily-unavailable", "last_checked": checked, "status_note": "Earth-observation diagnostics did not complete."}
        issues.append({"source_id": "nasa-gibs", "state": "temporarily-unavailable"})

    return states, issues


def source_directory(
    *,
    domain: str = "",
    state: str = "",
    feature: str = "",
    query: str = "",
    country: str = "",
    include_health: bool = False,
) -> dict[str, Any]:
    dynamic_states: dict[str, dict[str, Any]] = {}
    issues: list[dict[str, str]] = []
    if include_health:
        dynamic_states, issues = _public_dynamic_states()

    domain_token = _normalize(domain)
    state_token = _normalize(state).replace(" ", "-")
    feature_token = _normalize(feature)
    query_token = _normalize(query)

    records = [_record_with_state(item, dynamic_states) for item in SOURCE_RECORDS]
    if domain_token:
        records = [item for item in records if domain_token in {_normalize(value) for value in item["domains"]}]
    if state_token:
        records = [item for item in records if item["state"] == state_token or _normalize(item["state_label"]) == _normalize(state_token)]
    if feature_token:
        records = [item for item in records if feature_token in {_normalize(value) for value in item["features"]}]
    if query_token:
        records = [
            item for item in records
            if query_token in _normalize(" ".join([
                item["id"], item["name"], item["publisher"], item["connector"],
                " ".join(item["domains"]), " ".join(item["data_types"]), " ".join(item["features"]),
            ]))
        ]

    all_records = [_record_with_state(item, dynamic_states) for item in SOURCE_RECORDS]
    state_counts = {key: sum(1 for item in all_records if item["state"] == key) for key in PUBLIC_STATES}
    domains = sorted({domain for item in SOURCE_RECORDS for domain in item["domains"]})
    features = sorted({feature for item in SOURCE_RECORDS for feature in item["features"]})

    legacy_source_families = [
        {
            "slug": item["id"],
            "label": item["name"],
            "status": item["state"],
            "source_mode": item["connector"],
            "source_examples": [item["publisher"]],
            "public_use": ", ".join(item["features"]),
            "safe_display": item["public_notes"],
            "private_exclusions": ["API keys", "private URLs", "internal stack traces", "secret environment variables", "raw retry queues"],
        }
        for item in all_records
    ]

    return {
        "ok": True,
        "version": VERSION,
        "schema_version": SCHEMA_VERSION,
        "methodology_version": METHODOLOGY_VERSION,
        "version_scope": f"v{VERSION}",
        "generated_at": _now(),
        "title": "Source and Methodology Studio",
        "summary": "A public registry of the sources, connectors, coverage, delivery states, methods, and limits used across Site Intelligence.",
        "public_status": "public-beta",
        "country_filter": country.upper() if country else None,
        "filters": {"domain": domain or None, "state": state or None, "feature": feature or None, "query": query or None},
        "count": len(records),
        "total_registered": len(SOURCE_RECORDS),
        "state_counts": state_counts,
        "states": PUBLIC_STATES,
        "domains": domains,
        "features": features,
        "sources": records,
        "source_families": legacy_source_families,
        "diagnostic_issue_count": len(issues),
        "public_safe": True,
        "hidden": ["API keys", "private URLs", "internal stack traces", "secret environment variables", "raw retry queues", "private authentication state"],
        "recommended_shortcode": "[sc_source_methodology_studio height=\"1100\"]",
    }


def source_detail(source_id: str, *, include_health: bool = True) -> dict[str, Any]:
    normalized = str(source_id or "").strip().lower()
    record = _source_index().get(normalized)
    if not record:
        raise SourceMethodologyError("unknown_source")
    dynamic_states, _ = _public_dynamic_states() if include_health else ({}, [])
    item = _record_with_state(record, dynamic_states)
    methods = [method for method in METHODOLOGY_RECORDS if normalized in method.get("source_ids", [])]
    return {
        "ok": True,
        "version": VERSION,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _now(),
        "source": item,
        "methodologies": methods,
        "feature_links": [f"/app/?view={feature}" for feature in item["features"] if feature in {"overview", "earth", "events", "country", "compare", "thematic", "briefing", "sources"}],
        "responsible_use": "Source registration and connector state do not guarantee completeness, currentness, suitability, or professional validity for a specific decision.",
    }


def source_status(source_id: str) -> dict[str, Any]:
    detail = source_detail(source_id, include_health=True)
    source = detail["source"]
    return {
        "ok": True,
        "version": VERSION,
        "generated_at": detail["generated_at"],
        "source_id": source["id"],
        "source_name": source["name"],
        "state": source["state"],
        "state_label": source["state_label"],
        "last_checked": source["last_checked"],
        "last_successful_retrieval": source["last_successful_retrieval"],
        "status_note": source["status_note"],
        "public_safe": True,
    }


def source_coverage(source_id: str) -> dict[str, Any]:
    record = _source_index().get(str(source_id or "").strip().lower())
    if not record:
        raise SourceMethodologyError("unknown_source")
    return {
        "ok": True,
        "version": VERSION,
        "generated_at": _now(),
        "source_id": record["id"],
        "source_name": record["name"],
        "geographic_coverage": record["geographic_coverage"],
        "temporal_coverage": record["temporal_coverage"],
        "update_frequency": record["update_frequency"],
        "data_types": record["data_types"],
        "domains": record["domains"],
        "known_limits": record["known_limits"],
    }


def methodology_directory(*, feature: str = "", query: str = "") -> dict[str, Any]:
    feature_token = _normalize(feature)
    query_token = _normalize(query)
    records = list(METHODOLOGY_RECORDS)
    if feature_token:
        records = [item for item in records if feature_token in {_normalize(value) for value in item["applies_to"]}]
    if query_token:
        records = [item for item in records if query_token in _normalize(" ".join([item["id"], item["title"], item["summary"], " ".join(item["rules"])]))]
    return {
        "ok": True,
        "version": VERSION,
        "schema_version": SCHEMA_VERSION,
        "methodology_version": METHODOLOGY_VERSION,
        "generated_at": _now(),
        "title": "Public methodology registry",
        "summary": "Documented rules for how Site Intelligence selects, labels, compares, caches, maps, briefs, and exports public evidence.",
        "count": len(records),
        "total_registered": len(METHODOLOGY_RECORDS),
        "filters": {"feature": feature or None, "query": query or None},
        "methods": records,
        "principles": [
            "Preserve source identity, units, dates, delivery states, and known limitations.",
            "Show missing data rather than fabricating or silently imputing values.",
            "Keep optional source failures local to the affected view.",
            "Do not merge unlike evidence into an unexplained composite score.",
            "Verify consequential findings against authoritative source records and qualified professional judgment.",
        ],
        "included": [
            "Aggregated and source-linked public evidence records",
            "Public connector delivery states and coverage notes",
            "Methodology, source, and review notes",
            "Explicit missing-data and interpretation boundaries",
        ],
        "excluded": [
            "Raw GA4 user-level data",
            "Credential, token, or backend configuration values",
            "Private conversion diagnostics and authentication state",
            "Internal retry queues, stack traces, and unpublished source-review notes",
        ],
        "review_notes": [
            "Source status describes connector delivery, not the substantive age or suitability of every record.",
            "Public methodology should match actual application behavior and release tests.",
            "Consequential findings require verification against authoritative source records.",
        ],
        "recommended_shortcode": "[sc_source_methodology_studio height=\"1100\"]",
        "legacy_shortcode": "[sc_public_methodology]",
    }


def methodology_detail(method_id: str) -> dict[str, Any]:
    normalized = str(method_id or "").strip().lower()
    method = _methodology_index().get(normalized)
    if not method:
        raise SourceMethodologyError("unknown_methodology")
    sources = [_source_index()[source_id] for source_id in method.get("source_ids", []) if source_id in _source_index()]
    return {
        "ok": True,
        "version": VERSION,
        "schema_version": SCHEMA_VERSION,
        "methodology_version": METHODOLOGY_VERSION,
        "generated_at": _now(),
        "methodology": method,
        "sources": sources,
        "responsible_use": "Methodology documentation explains system behavior but does not make the underlying public evidence complete or decision-ready for every use.",
    }


def studio_diagnostics() -> dict[str, Any]:
    dynamic_states, issues = _public_dynamic_states()
    records = [_record_with_state(item, dynamic_states) for item in SOURCE_RECORDS]
    required_sources = {"world-bank", "nasa-gibs", "usgs-earthquakes", "nasa-eonet", "reliefweb"}
    required_complete = all(
        bool(item.get("official_url") and item.get("geographic_coverage") and item.get("temporal_coverage") and item.get("known_limits"))
        for item in records if item["id"] in required_sources
    )
    all_method_refs_valid = all(source_id in _source_index() for method in METHODOLOGY_RECORDS for source_id in method.get("source_ids", []))
    all_source_method_refs_valid = all(method_id in _methodology_index() for source in SOURCE_RECORDS for method_id in source.get("methodology_ids", []))
    return {
        "ok": True,
        "version": VERSION,
        "schema_version": SCHEMA_VERSION,
        "methodology_version": METHODOLOGY_VERSION,
        "generated_at": _now(),
        "source_count": len(records),
        "methodology_count": len(METHODOLOGY_RECORDS),
        "state_counts": {key: sum(1 for item in records if item["state"] == key) for key in PUBLIC_STATES},
        "checks": {
            "required_source_records_complete": required_complete,
            "all_sources_have_official_urls": all(bool(item.get("official_url")) for item in records),
            "all_sources_have_known_limits": all(bool(item.get("known_limits")) for item in records),
            "all_method_source_references_valid": all_method_refs_valid,
            "all_source_methodology_references_valid": all_source_method_refs_valid,
            "public_states_documented": set(PUBLIC_STATES) == {"live", "cached", "stale", "temporarily-unavailable", "experimental", "disabled"},
            "secrets_exposed": False,
            "platform_core_dependency": "optional",
        },
        "issues": issues,
        "sources": [{"id": item["id"], "state": item["state"], "last_checked": item["last_checked"], "status_note": item["status_note"]} for item in records],
        "supported_exports": list(ALLOWED_EXPORT_FORMATS),
        "public_safe": True,
    }


def _csv_safe(value: Any) -> str:
    text = "" if value is None else str(value)
    if text.startswith(("=", "+", "-", "@")):
        text = "'" + text
    return text


def _source_csv(records: Iterable[dict[str, Any]]) -> str:
    output = StringIO(newline="")
    fields = [
        "source_id", "source_name", "publisher", "state", "connector", "domains", "data_types",
        "geographic_coverage", "temporal_coverage", "update_frequency", "license", "official_url",
        "features", "known_limits", "last_checked", "last_successful_retrieval",
    ]
    writer = DictWriter(output, fieldnames=fields, lineterminator="\r\n")
    writer.writeheader()
    for item in records:
        writer.writerow({
            "source_id": _csv_safe(item.get("id")),
            "source_name": _csv_safe(item.get("name")),
            "publisher": _csv_safe(item.get("publisher")),
            "state": _csv_safe(item.get("state")),
            "connector": _csv_safe(item.get("connector")),
            "domains": _csv_safe(" | ".join(item.get("domains", []))),
            "data_types": _csv_safe(" | ".join(item.get("data_types", []))),
            "geographic_coverage": _csv_safe(item.get("geographic_coverage")),
            "temporal_coverage": _csv_safe(item.get("temporal_coverage")),
            "update_frequency": _csv_safe(item.get("update_frequency")),
            "license": _csv_safe(item.get("license")),
            "official_url": _csv_safe(item.get("official_url")),
            "features": _csv_safe(" | ".join(item.get("features", []))),
            "known_limits": _csv_safe(" | ".join(item.get("known_limits", []))),
            "last_checked": _csv_safe(item.get("last_checked")),
            "last_successful_retrieval": _csv_safe(item.get("last_successful_retrieval")),
        })
    return "\ufeff" + output.getvalue()


def studio_export(export_format: str = "json", *, include_health: bool = True) -> tuple[str, str, str]:
    fmt = str(export_format or "json").strip().lower()
    if fmt not in ALLOWED_EXPORT_FORMATS:
        raise SourceMethodologyError("unsupported_export_format")
    sources = source_directory(include_health=include_health)
    methods = methodology_directory()
    document = {
        "ok": True,
        "version": VERSION,
        "schema_version": SCHEMA_VERSION,
        "methodology_version": METHODOLOGY_VERSION,
        "generated_at": _now(),
        "sources": sources["sources"],
        "methodologies": methods["methods"],
        "public_states": PUBLIC_STATES,
        "hidden_fields": sources["hidden"],
        "responsible_use": "Source status and methodology records support transparent interpretation; they do not certify completeness, fitness for purpose, or professional validity.",
    }
    if fmt == "json":
        return json.dumps(document, indent=2, ensure_ascii=False), "application/json", "site-intelligence-source-methodology-registry.json"
    return _source_csv(sources["sources"]), "text/csv", "site-intelligence-source-registry.csv"
