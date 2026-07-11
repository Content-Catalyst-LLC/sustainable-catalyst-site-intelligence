from __future__ import annotations

from csv import DictWriter
from datetime import datetime, timezone
from html import escape
from io import StringIO
import json
import re
from typing import Any, Iterable

from .earth_observation_studio import layers as earth_layers
from .live_country_intelligence import country_indicators, country_trends
from .unified_live_events import unified_events
from .version import APP_VERSION

VERSION = APP_VERSION
SCHEMA_VERSION = "sc-thematic-dashboard/1.0"
METHODOLOGY_VERSION = "2026.07"

ALLOWED_EXPORT_FORMATS = ("json", "csv", "html")

CORE_INDICATOR_DEFINITIONS: dict[str, dict[str, str]] = {
    "SP.POP.TOTL": {"label": "Population", "domain": "Population"},
    "SP.DYN.LE00.IN": {"label": "Life expectancy", "domain": "Health"},
    "NY.GDP.PCAP.CD": {"label": "GDP per capita", "domain": "Economy"},
    "EG.ELC.ACCS.ZS": {"label": "Access to electricity", "domain": "Infrastructure"},
    "SH.H2O.BASW.ZS": {"label": "Basic drinking water", "domain": "Water"},
    "SE.SEC.ENRR": {"label": "Secondary enrollment", "domain": "Education"},
    "EN.ATM.CO2E.PC": {"label": "CO₂ emissions per capita", "domain": "Environment"},
    "SI.POV.GINI": {"label": "Gini index", "domain": "Inequality"},
}

THEMATIC_DASHBOARDS: dict[str, dict[str, Any]] = {
    "climate-environment": {
        "id": "climate-environment",
        "title": "Climate and Environment",
        "eyebrow": "Climate and environmental intelligence",
        "summary": "Source-aware climate, emissions, water, energy-access, Earth-observation, and recent environmental-event context for a selected country.",
        "maturity": "Public beta",
        "public_status": "public-beta",
        "indicator_ids": ["EN.ATM.CO2E.PC", "SH.H2O.BASW.ZS", "EG.ELC.ACCS.ZS"],
        "layer_ids": ["land-surface-temperature", "precipitation-rate", "vegetation-index", "fires-thermal-anomalies", "aerosol-optical-depth"],
        "event_categories": ["wildfire", "flood", "storm", "drought", "extreme-heat", "volcano"],
        "map_note": "Environmental layers and events provide geographic context; visual overlap does not establish causation.",
        "methodology": [
            "Latest non-null public indicator observations are displayed with their reporting year, unit, source, and data state.",
            "Earth-observation layers are presented as source metadata and view options rather than as certified ground conditions.",
            "Recent events are filtered to environmental and natural-hazard categories when source records support country matching.",
        ],
        "boundaries": [
            "This dashboard is not a climate-risk assessment, weather warning, environmental impact assessment, or compliance determination.",
            "Satellite-derived and modeled products may differ in resolution, latency, cloud conditions, and processing method.",
        ],
    },
    "human-development": {
        "id": "human-development",
        "title": "Human Development",
        "eyebrow": "Human development intelligence",
        "summary": "Population, health, education, water, electricity, income, inequality, trend, and public-event context for a selected country.",
        "maturity": "Public beta",
        "public_status": "public-beta",
        "indicator_ids": ["SP.POP.TOTL", "SP.DYN.LE00.IN", "NY.GDP.PCAP.CD", "SH.H2O.BASW.ZS", "EG.ELC.ACCS.ZS", "SE.SEC.ENRR", "SI.POV.GINI"],
        "layer_ids": ["nighttime-lights", "true-color", "precipitation-rate"],
        "event_categories": ["humanitarian", "displacement", "conflict", "flood", "storm", "drought"],
        "map_note": "Country-level indicators and mapped records operate at different scales and should not be treated as directly causal.",
        "methodology": [
            "Indicators retain their original World Bank definitions, units, reporting years, and delivery states.",
            "Trend charts use available historical observations without silently interpolating missing years.",
            "Recent events are contextual records and do not measure national wellbeing or determine responsibility.",
        ],
        "boundaries": [
            "This dashboard does not rank countries or determine development eligibility, performance, or policy success.",
            "Differences in reporting period, collection method, and coverage must be reviewed before drawing conclusions.",
        ],
    },
    "human-security": {
        "id": "human-security",
        "title": "Human Security",
        "eyebrow": "Human security intelligence",
        "summary": "Public event, humanitarian, displacement, natural-hazard, essential-service, and country-indicator context without converting unlike evidence into a single risk score.",
        "maturity": "Public beta",
        "public_status": "public-beta",
        "indicator_ids": ["SP.POP.TOTL", "SH.H2O.BASW.ZS", "EG.ELC.ACCS.ZS", "NY.GDP.PCAP.CD"],
        "layer_ids": ["true-color", "nighttime-lights", "fires-thermal-anomalies", "precipitation-rate"],
        "event_categories": ["humanitarian", "displacement", "conflict", "earthquake", "flood", "storm", "wildfire", "drought"],
        "map_note": "Event proximity, country context, and essential-service indicators remain separate evidence types.",
        "methodology": [
            "Event records preserve source identity, publication or observation time, category, country-match method, and match confidence where available.",
            "Optional event-source failures remain local and do not suppress available country indicators.",
            "No composite threat, fragility, or security score is generated.",
        ],
        "boundaries": [
            "This dashboard is not an emergency-alert system, conflict early-warning service, humanitarian needs assessment, or security advisory.",
            "Verify urgent or operational information directly with authoritative local and international sources.",
        ],
    },
    "infrastructure": {
        "id": "infrastructure",
        "title": "Infrastructure and Connectivity",
        "eyebrow": "Infrastructure intelligence",
        "summary": "Electricity, water, population, economic, nighttime-light, mapped-event, and resilience context for public infrastructure research.",
        "maturity": "Public beta",
        "public_status": "public-beta",
        "indicator_ids": ["EG.ELC.ACCS.ZS", "SH.H2O.BASW.ZS", "SP.POP.TOTL", "NY.GDP.PCAP.CD"],
        "layer_ids": ["nighttime-lights", "true-color", "fires-thermal-anomalies", "precipitation-rate"],
        "event_categories": ["earthquake", "flood", "storm", "wildfire", "extreme-heat", "humanitarian"],
        "map_note": "Nighttime lights and public event records are contextual signals, not direct measures of asset condition or service continuity.",
        "methodology": [
            "Infrastructure indicators retain source definitions and reporting years and are not normalized into a proprietary score.",
            "Nighttime-light imagery is presented as interpretive context and may be influenced by clouds, moonlight, fires, aurora, or product latency.",
            "Event context is limited to public records that can be linked to the selected country.",
        ],
        "boundaries": [
            "This dashboard does not perform engineering inspection, asset certification, outage confirmation, site-suitability review, or investment analysis.",
            "Consequential infrastructure decisions require current local records and qualified professional review.",
        ],
    },
}

DASHBOARD_ALIASES = {
    "climate": "climate-environment",
    "environment": "climate-environment",
    "climate-and-environment": "climate-environment",
    "development": "human-development",
    "security": "human-security",
    "infrastructure-connectivity": "infrastructure",
    "connectivity": "infrastructure",
}


class ThematicDashboardError(ValueError):
    """Public-safe validation error for thematic dashboards."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _dashboard_id(value: str) -> str:
    normalized = str(value or "").strip().lower()
    normalized = DASHBOARD_ALIASES.get(normalized, normalized)
    if normalized not in THEMATIC_DASHBOARDS:
        raise ThematicDashboardError("unknown_dashboard")
    return normalized


def _country_code(value: str) -> str:
    normalized = str(value or "KEN").strip().upper()
    if not re.fullmatch(r"[A-Z]{2,3}", normalized):
        raise ThematicDashboardError("unsupported_country")
    return normalized


def _safe_events(*, days: int, categories: list[str], country_code: str, limit: int = 40) -> dict[str, Any]:
    try:
        payload = unified_events(
            days=max(1, min(int(days), 90)),
            limit=max(1, min(int(limit), 100)),
            categories=categories,
            country_code=country_code,
            allow_fallback=False,
        )
        if not isinstance(payload, dict):
            raise TypeError("invalid event payload")
        payload.setdefault("events", [])
        payload.setdefault("count", len(payload["events"]))
        payload.setdefault("data_state", "unavailable")
        payload.setdefault("source_states", {})
        return payload
    except Exception:
        return {
            "ok": False,
            "version": VERSION,
            "generated_at": _now(),
            "data_state": "temporarily-unavailable",
            "delivery_state": "unavailable",
            "source_states": {},
            "count": 0,
            "events": [],
            "geojson": {"type": "FeatureCollection", "features": []},
            "message": "Optional public event context is temporarily unavailable.",
        }


def _source_records(
    indicators: Iterable[dict[str, Any]],
    layer_records: Iterable[dict[str, Any]],
    events: dict[str, Any],
) -> list[dict[str, Any]]:
    records: dict[tuple[str, str], dict[str, Any]] = {}

    for item in indicators:
        name = str(item.get("source") or "World Bank Open Data")
        url = str(item.get("source_url") or "")
        key = (name, url)
        record = records.setdefault(key, {
            "name": name,
            "url": url or None,
            "record_types": set(),
            "data_states": set(),
        })
        record["record_types"].add("indicator")
        record["data_states"].add(str(item.get("data_state") or "unavailable"))

    for item in layer_records:
        name = str(item.get("source") or "Earth-observation source")
        url = str(item.get("source_url") or "https://gibs.earthdata.nasa.gov/")
        key = (name, url)
        record = records.setdefault(key, {
            "name": name,
            "url": url or None,
            "record_types": set(),
            "data_states": set(),
        })
        record["record_types"].add("earth-layer")
        record["data_states"].add(str(item.get("data_state") or "registered"))

    event_source_names = {
        "usgs": ("USGS Earthquake Hazards Program", "https://earthquake.usgs.gov/"),
        "nasa-eonet": ("NASA EONET", "https://eonet.gsfc.nasa.gov/"),
        "reliefweb": ("ReliefWeb", "https://reliefweb.int/"),
    }
    for source_id, state in (events.get("source_states") or {}).items():
        name, url = event_source_names.get(source_id, (source_id, ""))
        key = (name, url)
        record = records.setdefault(key, {
            "name": name,
            "url": url or None,
            "record_types": set(),
            "data_states": set(),
        })
        record["record_types"].add("event")
        record["data_states"].add(str(state or "unavailable"))

    output: list[dict[str, Any]] = []
    for record in records.values():
        output.append({
            **record,
            "record_types": sorted(record["record_types"]),
            "data_states": sorted(record["data_states"]),
        })
    return sorted(output, key=lambda item: item["name"].lower())


def _layer_records(definition: dict[str, Any]) -> list[dict[str, Any]]:
    registry = earth_layers()
    selected = set(definition["layer_ids"])
    records = []
    for item in registry.get("layers", []):
        if item.get("id") not in selected:
            continue
        records.append({
            "id": item.get("id"),
            "title": item.get("title"),
            "description": item.get("description"),
            "source": item.get("source"),
            "source_url": "https://gibs.earthdata.nasa.gov/",
            "attribution": item.get("attribution"),
            "temporal_resolution": item.get("temporal_resolution"),
            "spatial_resolution": item.get("spatial_resolution"),
            "observation_type": item.get("observation_type"),
            "status": item.get("status"),
            "data_state": "registered",
            "limits": item.get("limits"),
        })
    return records


def _indicator_records(definition: dict[str, Any], country_code: str) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    try:
        indicator_payload = country_indicators(country_code)
        trend_payload = country_trends(country_code)
    except ValueError as exc:
        raise ThematicDashboardError("unsupported_country") from exc

    allowed = set(definition["indicator_ids"])
    indicators = []
    for item in indicator_payload.get("indicators", []):
        if item.get("id") not in allowed:
            continue
        latest = item.get("latest") or {}
        indicators.append({
            "id": item.get("id"),
            "key": item.get("key"),
            "label": item.get("label") or CORE_INDICATOR_DEFINITIONS.get(str(item.get("id")), {}).get("label"),
            "domain": item.get("domain") or CORE_INDICATOR_DEFINITIONS.get(str(item.get("id")), {}).get("domain"),
            "value": latest.get("value") if latest else None,
            "reporting_year": latest.get("year") if latest else None,
            "unit": item.get("unit"),
            "format": item.get("format"),
            "source": item.get("source"),
            "source_id": item.get("source_id") or item.get("id"),
            "source_url": item.get("source_url"),
            "data_state": item.get("data_state") or "unavailable",
            "cache_state": item.get("cache_state"),
            "retrieved_at": item.get("retrieved_at"),
            "stale": bool(item.get("stale")),
            "available": bool(latest),
        })

    trends = []
    for item in trend_payload.get("trends", []):
        if item.get("id") not in allowed:
            continue
        series = [
            {"year": point.get("year"), "value": point.get("value")}
            for point in item.get("series", [])
            if point.get("year") is not None and point.get("value") is not None
        ]
        trends.append({
            "id": item.get("id"),
            "key": item.get("key"),
            "label": item.get("label"),
            "unit": item.get("unit"),
            "source": item.get("source"),
            "source_url": item.get("source_url"),
            "data_state": item.get("data_state") or "unavailable",
            "stale": bool(item.get("stale")),
            "series": series,
            "point_count": len(series),
            "chartable": len(series) >= 2,
            "gap_years": _gap_years(series),
        })

    country = indicator_payload.get("country") or trend_payload.get("country") or {"code": country_code, "name": country_code}
    return country, indicators, trends


def _gap_years(series: list[dict[str, Any]]) -> list[int]:
    years = sorted({int(item["year"]) for item in series if item.get("year") is not None})
    if len(years) < 2:
        return []
    present = set(years)
    return [year for year in range(years[0], years[-1] + 1) if year not in present]


def dashboard_directory() -> dict[str, Any]:
    dashboards = []
    for definition in THEMATIC_DASHBOARDS.values():
        dashboards.append({
            "id": definition["id"],
            "title": definition["title"],
            "eyebrow": definition["eyebrow"],
            "summary": definition["summary"],
            "maturity": definition["maturity"],
            "public_status": definition["public_status"],
            "indicator_count": len(definition["indicator_ids"]),
            "layer_count": len(definition["layer_ids"]),
            "route": f"/app/?view=thematic&dashboard={definition['id']}&country=KEN",
        })
    return {
        "ok": True,
        "version": VERSION,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _now(),
        "title": "Thematic Intelligence Dashboards",
        "summary": "Four source-aware public-beta dashboards built from country indicators, trends, Earth-observation layers, event context, methodology, and exportable evidence.",
        "dashboard_count": len(dashboards),
        "dashboards": dashboards,
        "maturity_scale": ["Registered", "Prototype", "Public beta", "Validated public release"],
        "default_dashboard": "climate-environment",
        "default_country": "KEN",
        "export_formats": list(ALLOWED_EXPORT_FORMATS),
        "wordpress_shortcode": '[sc_thematic_intelligence dashboard="climate-environment" country="KEN" height="1150"]',
        "responsible_use": "Thematic dashboards organize public evidence for research and orientation. They do not replace authoritative records, field investigation, or qualified professional judgment.",
    }


def build_dashboard(dashboard_id: str, country: str = "KEN", days: int = 30, include_events: bool = True) -> dict[str, Any]:
    normalized_dashboard = _dashboard_id(dashboard_id)
    country_code = _country_code(country)
    safe_days = max(1, min(int(days), 90))
    definition = THEMATIC_DASHBOARDS[normalized_dashboard]

    country_record, indicators, trends = _indicator_records(definition, country_code)
    layer_records = _layer_records(definition)
    event_payload = _safe_events(
        days=safe_days,
        categories=definition["event_categories"],
        country_code=str(country_record.get("code") or country_code),
    ) if include_events else {
        "ok": True,
        "version": VERSION,
        "generated_at": _now(),
        "data_state": "not-requested",
        "source_states": {},
        "count": 0,
        "events": [],
        "geojson": {"type": "FeatureCollection", "features": []},
    }

    missing_indicators = [
        {"id": item["id"], "label": item["label"], "reason": "No validated public value is currently available."}
        for item in indicators if not item["available"]
    ]
    missing = list(missing_indicators)
    if include_events and event_payload.get("data_state") in {"unavailable", "temporarily-unavailable"}:
        missing.append({
            "id": "event-context",
            "label": "Recent public event context",
            "reason": event_payload.get("message") or "Optional event records are temporarily unavailable.",
        })

    available_count = sum(1 for item in indicators if item["available"])
    chartable_count = sum(1 for item in trends if item["chartable"])
    states = [item["data_state"] for item in indicators]
    states.append(str(event_payload.get("data_state") or "unavailable"))

    if available_count == len(indicators) and event_payload.get("data_state") == "live":
        data_state = "live"
    elif available_count > 0:
        data_state = "partial-live"
    elif any(item.get("data_state") in {"cached", "stale", "reference-snapshot"} for item in indicators):
        data_state = "cached-or-reference"
    else:
        data_state = "unavailable"

    sources = _source_records(indicators, layer_records, event_payload)
    recent_events = []
    for item in event_payload.get("events", []):
        recent_events.append({
            "id": item.get("id"),
            "title": item.get("title"),
            "summary": item.get("summary"),
            "category": item.get("category"),
            "category_label": item.get("category_label"),
            "severity": item.get("severity"),
            "observed_at": item.get("observed_at"),
            "source": item.get("source_name") or item.get("source"),
            "source_id": item.get("source"),
            "source_url": item.get("source_url"),
            "data_state": item.get("data_state") or "live",
            "coordinates": item.get("coordinates"),
            "country_code": item.get("country_code"),
            "country_match_method": item.get("country_match_method"),
            "country_match_confidence": item.get("country_match_confidence"),
        })

    return {
        "ok": True,
        "version": VERSION,
        "schema_version": SCHEMA_VERSION,
        "methodology_version": METHODOLOGY_VERSION,
        "generated_at": _now(),
        "dashboard": {
            "id": definition["id"],
            "title": definition["title"],
            "eyebrow": definition["eyebrow"],
            "summary": definition["summary"],
            "maturity": definition["maturity"],
            "public_status": definition["public_status"],
            "map_note": definition["map_note"],
        },
        "country": country_record,
        "data_state": data_state,
        "stale": any(bool(item.get("stale")) for item in indicators),
        "summary": {
            "indicator_count": len(indicators),
            "available_indicator_count": available_count,
            "missing_indicator_count": len(missing_indicators),
            "chartable_trend_count": chartable_count,
            "event_count": int(event_payload.get("count") or 0),
            "layer_count": len(layer_records),
            "source_count": len(sources),
        },
        "indicators": indicators,
        "trends": trends,
        "events": {
            "data_state": event_payload.get("data_state"),
            "delivery_state": event_payload.get("delivery_state"),
            "source_states": event_payload.get("source_states") or {},
            "count": int(event_payload.get("count") or 0),
            "records": recent_events,
            "geojson": event_payload.get("geojson") or {"type": "FeatureCollection", "features": []},
            "categories": definition["event_categories"],
        },
        "earth_layers": layer_records,
        "map": {
            "latitude": country_record.get("latitude"),
            "longitude": country_record.get("longitude"),
            "default_zoom": 5 if country_record.get("latitude") is not None and country_record.get("longitude") is not None else 2,
            "layer_ids": definition["layer_ids"],
            "event_feature_count": len((event_payload.get("geojson") or {}).get("features") or []),
            "note": definition["map_note"],
        },
        "sources": sources,
        "missing_data": missing,
        "methodology": definition["methodology"],
        "interpretation_limits": definition["boundaries"],
        "responsible_use": "Confirm consequential findings against cited authoritative sources, current local information, and qualified professional advice.",
        "share_state": {
            "view": "thematic",
            "dashboard": definition["id"],
            "country": str(country_record.get("code") or country_code),
            "days": safe_days,
        },
        "routes": {
            "dashboard": f"/public/thematic-dashboard/{definition['id']}?country={country_record.get('code') or country_code}&days={safe_days}",
            "indicators": f"/public/thematic-dashboard/{definition['id']}/indicators?country={country_record.get('code') or country_code}",
            "trends": f"/public/thematic-dashboard/{definition['id']}/trends?country={country_record.get('code') or country_code}",
            "events": f"/public/thematic-dashboard/{definition['id']}/events?country={country_record.get('code') or country_code}&days={safe_days}",
            "brief": f"/public/thematic-dashboard/{definition['id']}/brief?country={country_record.get('code') or country_code}&days={safe_days}",
            "export": f"/public/thematic-dashboard/{definition['id']}/export?country={country_record.get('code') or country_code}&days={safe_days}&format=json",
            "diagnostics": f"/public/thematic-dashboard/{definition['id']}/diagnostics?country={country_record.get('code') or country_code}&days={safe_days}",
        },
    }


def dashboard_indicators(dashboard_id: str, country: str = "KEN") -> dict[str, Any]:
    payload = build_dashboard(dashboard_id, country, include_events=False)
    return {
        "ok": True,
        "version": VERSION,
        "schema_version": SCHEMA_VERSION,
        "generated_at": payload["generated_at"],
        "dashboard": payload["dashboard"],
        "country": payload["country"],
        "data_state": payload["data_state"],
        "indicators": payload["indicators"],
        "missing_data": [item for item in payload["missing_data"] if item.get("id") != "event-context"],
        "methodology": payload["methodology"],
    }


def dashboard_trends(dashboard_id: str, country: str = "KEN") -> dict[str, Any]:
    payload = build_dashboard(dashboard_id, country, include_events=False)
    return {
        "ok": True,
        "version": VERSION,
        "schema_version": SCHEMA_VERSION,
        "generated_at": payload["generated_at"],
        "dashboard": payload["dashboard"],
        "country": payload["country"],
        "data_state": payload["data_state"],
        "trends": payload["trends"],
        "chartable_trend_count": payload["summary"]["chartable_trend_count"],
        "methodology": [
            "Trend series preserve observed reporting years and explicit gaps.",
            "A series is chartable only when at least two validated observations are available.",
        ],
    }


def dashboard_events(dashboard_id: str, country: str = "KEN", days: int = 30, limit: int = 40) -> dict[str, Any]:
    normalized_dashboard = _dashboard_id(dashboard_id)
    country_code = _country_code(country)
    definition = THEMATIC_DASHBOARDS[normalized_dashboard]
    try:
        country_record = country_indicators(country_code).get("country") or {"code": country_code, "name": country_code}
    except ValueError as exc:
        raise ThematicDashboardError("unsupported_country") from exc
    payload = _safe_events(days=days, categories=definition["event_categories"], country_code=str(country_record.get("code") or country_code), limit=limit)
    return {
        "ok": True,
        "version": VERSION,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _now(),
        "dashboard": {"id": definition["id"], "title": definition["title"], "maturity": definition["maturity"]},
        "country": country_record,
        "data_state": payload.get("data_state"),
        "source_states": payload.get("source_states") or {},
        "categories": definition["event_categories"],
        "count": int(payload.get("count") or 0),
        "events": payload.get("events") or [],
        "geojson": payload.get("geojson") or {"type": "FeatureCollection", "features": []},
        "boundary": "These public event records are contextual and do not constitute an operational alert or complete incident inventory.",
    }


def dashboard_brief(dashboard_id: str, country: str = "KEN", days: int = 30) -> dict[str, Any]:
    payload = build_dashboard(dashboard_id, country, days=days, include_events=True)
    country_record = payload["country"]
    available = [item for item in payload["indicators"] if item["available"]]
    evidence_lines = [
        f"{item['label']}: {item['value']} {item.get('unit') or ''} ({item.get('reporting_year') or 'year unavailable'}, {item.get('source') or 'source unavailable'}, {item.get('data_state') or 'state unavailable'})."
        for item in available
    ]
    return {
        "ok": True,
        "version": VERSION,
        "schema_version": SCHEMA_VERSION,
        "methodology_version": METHODOLOGY_VERSION,
        "generated_at": payload["generated_at"],
        "title": f"{country_record.get('name') or country_record.get('code')} — {payload['dashboard']['title']} Brief",
        "summary": payload["dashboard"]["summary"],
        "dashboard": payload["dashboard"],
        "country": country_record,
        "data_state": payload["data_state"],
        "sections": [
            {"heading": "Scope", "text": f"{payload['dashboard']['title']} for {country_record.get('name') or country_record.get('code')}."},
            {"heading": "Latest public indicators", "item_count": len(available), "evidence_lines": evidence_lines},
            {"heading": "Trend coverage", "item_count": payload["summary"]["chartable_trend_count"], "text": "Historical series retain reporting-year gaps and source definitions."},
            {"heading": "Recent public events", "item_count": payload["summary"]["event_count"], "text": f"Event context covers the selected {max(1, min(int(days), 90))}-day window."},
            {"heading": "Earth-observation context", "item_count": payload["summary"]["layer_count"], "text": payload["map"]["note"]},
            {"heading": "Data gaps", "item_count": len(payload["missing_data"]), "text": "Unavailable records remain explicit and are not silently imputed."},
        ],
        "evidence": {
            "indicators": payload["indicators"],
            "trends": payload["trends"],
            "events": payload["events"]["records"],
            "layers": payload["earth_layers"],
        },
        "sources": payload["sources"],
        "missing_data": payload["missing_data"],
        "methodology": payload["methodology"],
        "interpretation_limits": payload["interpretation_limits"],
        "responsible_use": payload["responsible_use"],
    }


def _csv_safe(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value
    text = str(value)
    if text.startswith(("=", "+", "-", "@", "\t", "\r")):
        return "'" + text
    return text


def _flatten_dashboard(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in payload.get("indicators", []):
        rows.append({
            "record_type": "indicator",
            "id": item.get("id"),
            "label": item.get("label"),
            "value": item.get("value"),
            "unit": item.get("unit"),
            "date_or_year": item.get("reporting_year"),
            "source": item.get("source"),
            "source_id": item.get("source_id"),
            "source_url": item.get("source_url"),
            "data_state": item.get("data_state"),
            "notes": item.get("domain"),
        })
    for item in payload.get("events", {}).get("records", []):
        rows.append({
            "record_type": "event",
            "id": item.get("id"),
            "label": item.get("title"),
            "value": item.get("category"),
            "unit": "",
            "date_or_year": item.get("observed_at"),
            "source": item.get("source"),
            "source_id": item.get("source_id"),
            "source_url": item.get("source_url"),
            "data_state": item.get("data_state"),
            "notes": f"match={item.get('country_match_method')}; confidence={item.get('country_match_confidence')}",
        })
    for item in payload.get("earth_layers", []):
        rows.append({
            "record_type": "earth-layer",
            "id": item.get("id"),
            "label": item.get("title"),
            "value": item.get("observation_type"),
            "unit": item.get("spatial_resolution"),
            "date_or_year": item.get("temporal_resolution"),
            "source": item.get("source"),
            "source_id": item.get("id"),
            "source_url": item.get("source_url"),
            "data_state": item.get("data_state"),
            "notes": item.get("limits"),
        })
    return rows


def _html_export(payload: dict[str, Any]) -> str:
    rows = "".join(
        "<tr>"
        f"<td>{escape(str(item.get('record_type') or ''))}</td>"
        f"<td>{escape(str(item.get('label') or item.get('id') or ''))}</td>"
        f"<td>{escape(str(item.get('value') if item.get('value') is not None else 'Unavailable'))}</td>"
        f"<td>{escape(str(item.get('unit') or ''))}</td>"
        f"<td>{escape(str(item.get('date_or_year') or ''))}</td>"
        f"<td>{escape(str(item.get('source') or ''))}</td>"
        f"<td>{escape(str(item.get('data_state') or ''))}</td>"
        "</tr>"
        for item in _flatten_dashboard(payload)
    )
    sources = "".join(
        f"<li><strong>{escape(str(item.get('name') or 'Source'))}</strong>"
        + (f" — <a href=\"{escape(str(item.get('url')))}\">{escape(str(item.get('url')))}</a>" if item.get("url") else "")
        + f" <span>({escape(', '.join(item.get('data_states') or []))})</span></li>"
        for item in payload.get("sources", [])
    ) or "<li>No source records were returned.</li>"
    missing = "".join(
        f"<li><strong>{escape(str(item.get('label') or item.get('id')))}</strong>: {escape(str(item.get('reason') or 'Unavailable'))}</li>"
        for item in payload.get("missing_data", [])
    ) or "<li>No explicit missing-data record was generated.</li>"
    methodology = "".join(f"<li>{escape(str(item))}</li>" for item in payload.get("methodology", []))
    limits = "".join(f"<li>{escape(str(item))}</li>" for item in payload.get("interpretation_limits", []))
    country = payload.get("country") or {}
    dashboard = payload.get("dashboard") or {}
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(str(country.get('name') or country.get('code')))} — {escape(str(dashboard.get('title')))}</title>
<style>
body{{font-family:Arial,sans-serif;max-width:1100px;margin:0 auto;padding:36px;color:#181818;line-height:1.55}}
h1{{font-size:34px;margin-bottom:6px}}h2{{margin-top:28px;font-size:20px}}.meta{{color:#555;font-size:13px}}.boundary{{padding:14px;border-left:4px solid #d71920;background:#f7f7f7}}
table{{width:100%;border-collapse:collapse;margin-top:16px;font-size:12px}}th,td{{padding:8px;border:1px solid #ddd;text-align:left;vertical-align:top}}th{{background:#f2f2f2}}a{{color:#8b1116;overflow-wrap:anywhere}}
@media print{{body{{max-width:none;padding:0}}section,table{{break-inside:avoid}}a[href]::after{{content:" (" attr(href) ")";font-size:9px}}}}
</style></head><body>
<p class="meta">Sustainable Catalyst Site Intelligence · v{escape(VERSION)} · schema {escape(SCHEMA_VERSION)}</p>
<h1>{escape(str(country.get('name') or country.get('code')))} — {escape(str(dashboard.get('title')))}</h1>
<p>{escape(str(dashboard.get('summary') or ''))}</p>
<p class="meta">Generated: {escape(str(payload.get('generated_at')))} · Maturity: {escape(str(dashboard.get('maturity')))} · Data state: {escape(str(payload.get('data_state')))}</p>
<h2>Evidence records</h2><table><thead><tr><th>Type</th><th>Record</th><th>Value/context</th><th>Unit/resolution</th><th>Date/year</th><th>Source</th><th>State</th></tr></thead><tbody>{rows}</tbody></table>
<h2>Sources</h2><ul>{sources}</ul><h2>Missing data</h2><ul>{missing}</ul><h2>Methodology</h2><ul>{methodology}</ul><h2>Interpretation limits</h2><ul>{limits}</ul>
<p class="boundary"><strong>Responsible-use boundary:</strong> {escape(str(payload.get('responsible_use') or ''))}</p>
</body></html>"""


def dashboard_export(dashboard_id: str, country: str = "KEN", days: int = 30, export_format: str = "json") -> tuple[str, str, str]:
    payload = build_dashboard(dashboard_id, country, days=days, include_events=True)
    fmt = str(export_format or "json").strip().lower()
    if fmt not in ALLOWED_EXPORT_FORMATS:
        raise ThematicDashboardError("unsupported_export_format")
    dashboard = payload["dashboard"]
    country_record = payload["country"]
    stem = re.sub(r"[^a-z0-9-]+", "-", f"site-intelligence-{dashboard['id']}-{country_record.get('code') or country}".lower()).strip("-")

    if fmt == "json":
        document = {
            **payload,
            "export_manifest": {
                "format": "json",
                "filename": f"{stem}.json",
                "application_version": VERSION,
                "schema_version": SCHEMA_VERSION,
                "methodology_version": METHODOLOGY_VERSION,
                "generated_at": payload["generated_at"],
            },
        }
        return json.dumps(document, indent=2, ensure_ascii=False), "application/json", f"{stem}.json"

    if fmt == "csv":
        fieldnames = [
            "dashboard_id", "dashboard_title", "country_code", "country_name", "record_type", "id", "label", "value", "unit", "date_or_year", "source", "source_id", "source_url", "data_state", "notes",
        ]
        output = StringIO(newline="")
        writer = DictWriter(output, fieldnames=fieldnames, lineterminator="\r\n")
        writer.writeheader()
        for item in _flatten_dashboard(payload):
            writer.writerow({
                "dashboard_id": _csv_safe(dashboard["id"]),
                "dashboard_title": _csv_safe(dashboard["title"]),
                "country_code": _csv_safe(country_record.get("code")),
                "country_name": _csv_safe(country_record.get("name")),
                "record_type": _csv_safe(item.get("record_type")),
                "id": _csv_safe(item.get("id")),
                "label": _csv_safe(item.get("label")),
                "value": _csv_safe(item.get("value")),
                "unit": _csv_safe(item.get("unit")),
                "date_or_year": _csv_safe(item.get("date_or_year")),
                "source": _csv_safe(item.get("source")),
                "source_id": _csv_safe(item.get("source_id")),
                "source_url": _csv_safe(item.get("source_url")),
                "data_state": _csv_safe(item.get("data_state")),
                "notes": _csv_safe(item.get("notes")),
            })
        return "\ufeff" + output.getvalue(), "text/csv", f"{stem}.csv"

    return _html_export(payload), "text/html", f"{stem}.html"


def dashboard_diagnostics(dashboard_id: str, country: str = "KEN", days: int = 30) -> dict[str, Any]:
    payload = build_dashboard(dashboard_id, country, days=days, include_events=True)
    issue_count = len(payload["missing_data"]) + sum(1 for trend in payload["trends"] if not trend["chartable"])
    return {
        "ok": True,
        "version": VERSION,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _now(),
        "dashboard": payload["dashboard"],
        "country": payload["country"],
        "data_state": payload["data_state"],
        "checks": {
            "dashboard_registered": True,
            "maturity": payload["dashboard"]["maturity"],
            "indicator_count": payload["summary"]["indicator_count"],
            "available_indicator_count": payload["summary"]["available_indicator_count"],
            "missing_indicator_count": payload["summary"]["missing_indicator_count"],
            "chartable_trend_count": payload["summary"]["chartable_trend_count"],
            "event_state": payload["events"]["data_state"],
            "event_count": payload["events"]["count"],
            "layer_count": payload["summary"]["layer_count"],
            "source_count": payload["summary"]["source_count"],
            "issue_count": issue_count,
            "source_attribution_complete": all(bool(item.get("name")) for item in payload["sources"]),
            "local_optional_failure_state": True,
            "composite_score": "not-generated",
            "platform_core_dependency": "optional",
        },
        "missing_data": payload["missing_data"],
        "non_chartable_trends": [
            {"id": item["id"], "label": item["label"], "point_count": item["point_count"], "gap_years": item["gap_years"]}
            for item in payload["trends"] if not item["chartable"]
        ],
        "supported_exports": list(ALLOWED_EXPORT_FORMATS),
        "public_safe": True,
    }
