from __future__ import annotations

from csv import DictWriter
from datetime import date, datetime, timezone
from hashlib import sha256
from html import escape
from io import StringIO
import json
import re
from typing import Any, Iterable

from .comparative_intelligence import compare_countries
from .thematic_intelligence_dashboards import build_dashboard as dashboard_export
from .earth_observation_studio import export_manifest as earth_export_manifest
from .live_country_intelligence import country_indicators, country_profile, country_trends
from .unified_live_events import event_detail, unified_events
from .version import APP_VERSION

VERSION = APP_VERSION
SCHEMA_VERSION = "sc-public-briefing/1.0"
METHODOLOGY_VERSION = "2026.07"

BRIEF_TYPES: dict[str, dict[str, Any]] = {
    "country": {
        "title": "Country Intelligence Brief",
        "description": "Country indicators, trend coverage, recent public events, sources, data gaps, and interpretation limits.",
        "required": ["country"],
    },
    "comparison": {
        "title": "Country Comparison Brief",
        "description": "Two-country indicator, trend, event, source, and methodological comparison.",
        "required": ["country", "compare"],
    },
    "event": {
        "title": "Event Situation Brief",
        "description": "A source-aware brief for one event or a filtered public event situation.",
        "required": [],
    },
    "earth": {
        "title": "Earth Observation Brief",
        "description": "Layer, date, location, attribution, and interpretation context for an Earth-observation view.",
        "required": ["layer_id", "date_a", "date_b"],
    },
    "thematic": {
        "title": "Thematic Intelligence Brief",
        "description": "A cross-domain dashboard brief with filters, source registry, evidence state, and limits.",
        "required": ["dashboard_id"],
    },
}

EXPORT_FORMATS = ["json", "csv", "html"]
BROWSER_EXPORTS = ["png"]


class BriefingError(ValueError):
    """Public-safe briefing validation error."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean_code(value: Any, fallback: str = "KEN") -> str:
    code = str(value or fallback).strip().upper()
    if not re.fullmatch(r"[A-Z]{2,3}", code):
        raise BriefingError("unsupported_country")
    return code


def _clean_identifier(value: Any, fallback: str = "") -> str:
    text = str(value or fallback).strip()
    if text and not re.fullmatch(r"[A-Za-z0-9._-]{1,96}", text):
        raise BriefingError("unsupported_identifier")
    return text


def _clean_date(value: Any, *, fallback_days: int | None = None) -> str:
    text = str(value or "").strip()
    if not text and fallback_days is not None:
        return (date.today()).isoformat()
    if not text:
        return ""
    try:
        return date.fromisoformat(text).isoformat()
    except ValueError as exc:
        raise BriefingError("invalid_date") from exc


def _clamp_int(value: Any, minimum: int, maximum: int, default: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = default
    return max(minimum, min(maximum, number))


def _clamp_float(value: Any, minimum: float, maximum: float, default: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = default
    return max(minimum, min(maximum, number))


def _safe_event_payload(**kwargs: Any) -> dict[str, Any]:
    try:
        payload = unified_events(allow_fallback=False, **kwargs)
        if not isinstance(payload, dict):
            raise TypeError("invalid event payload")
        payload.setdefault("events", [])
        payload.setdefault("count", len(payload["events"]))
        payload.setdefault("data_state", "unavailable")
        return payload
    except Exception:
        return {
            "ok": False,
            "version": VERSION,
            "generated_at": _now(),
            "data_state": "temporarily-unavailable",
            "count": 0,
            "events": [],
            "source_states": {},
            "message": "Optional public event context is temporarily unavailable.",
        }


def _dedupe_sources(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    output: dict[tuple[str, str, str], dict[str, Any]] = {}
    for record in records:
        if not isinstance(record, dict):
            continue
        name = str(record.get("name") or record.get("source") or "Source unavailable").strip()
        url = str(record.get("url") or record.get("source_url") or "").strip()
        source_id = str(record.get("source_id") or "").strip()
        key = (name.lower(), url, source_id)
        item = output.setdefault(
            key,
            {
                "name": name,
                "url": url or None,
                "source_id": source_id or None,
                "publisher": record.get("publisher") or name,
                "data_states": [],
                "record_types": [],
                "retrieved_at": record.get("retrieved_at"),
            },
        )
        state = str(record.get("data_state") or "").strip()
        if state and state not in item["data_states"]:
            item["data_states"].append(state)
        record_type = str(record.get("record_type") or "").strip()
        if record_type and record_type not in item["record_types"]:
            item["record_types"].append(record_type)
        if not item.get("retrieved_at") and record.get("retrieved_at"):
            item["retrieved_at"] = record.get("retrieved_at")
    return sorted(output.values(), key=lambda item: (item["name"].lower(), item.get("source_id") or ""))


def _state_summary(states: Iterable[Any]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for state in states:
        key = str(state or "unavailable")
        counts[key] = counts.get(key, 0) + 1
    available = sum(value for key, value in counts.items() if key not in {"unavailable", "temporarily-unavailable", "not-requested"})
    return {
        "counts": counts,
        "available_record_count": available,
        "has_stale_data": counts.get("stale", 0) > 0,
        "has_fallback_data": counts.get("fallback", 0) > 0 or counts.get("reference-snapshot", 0) > 0,
        "has_unavailable_data": counts.get("unavailable", 0) > 0 or counts.get("temporarily-unavailable", 0) > 0,
    }


def _brief_id(brief_type: str, state: dict[str, Any]) -> str:
    canonical = json.dumps({"brief_type": brief_type, "state": state}, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return "scb-" + sha256(canonical.encode("utf-8")).hexdigest()[:20]


def _base_bundle(
    brief_type: str,
    *,
    title: str,
    summary: str,
    scope: dict[str, Any],
    state: dict[str, Any],
    geography: dict[str, Any],
    selected_dates: dict[str, Any],
    filters: dict[str, Any],
    evidence: dict[str, Any],
    source_records: list[dict[str, Any]],
    data_states: dict[str, Any],
    missing_data: list[dict[str, Any]],
    sections: list[dict[str, Any]],
    methodology_notes: list[str],
    interpretation_limits: list[str],
) -> dict[str, Any]:
    generated_at = _now()
    brief_id = _brief_id(brief_type, state)
    return {
        "ok": True,
        "version": VERSION,
        "schema_version": SCHEMA_VERSION,
        "methodology_version": METHODOLOGY_VERSION,
        "generated_at": generated_at,
        "brief_id": brief_id,
        "brief_type": brief_type,
        "title": title,
        "summary": summary,
        "scope": scope,
        "state": state,
        "geography": geography,
        "selected_dates": selected_dates,
        "filters": filters,
        "evidence": evidence,
        "source_records": source_records,
        "data_states": data_states,
        "missing_data": missing_data,
        "sections": sections,
        "methodology_notes": methodology_notes,
        "interpretation_limits": interpretation_limits,
        "responsible_use": "This public brief supports orientation, research, source review, and documentation. Verify consequential findings against cited authoritative sources and seek qualified professional advice where decisions carry legal, financial, environmental, engineering, humanitarian, operational, or safety consequences.",
        "export_options": {
            "server_formats": EXPORT_FORMATS,
            "browser_formats": BROWSER_EXPORTS,
            "pdf_status": "deferred-until-print-html-stable",
        },
        "provenance": {
            "application": "Sustainable Catalyst Site Intelligence",
            "application_version": VERSION,
            "schema_version": SCHEMA_VERSION,
            "methodology_version": METHODOLOGY_VERSION,
            "generated_at": generated_at,
            "platform_core_state": "optional-not-required",
        },
    }


def _country_bundle(country: str, *, days: int, include_events: bool) -> dict[str, Any]:
    code = _clean_code(country)
    profile = country_profile(code)
    indicators = country_indicators(code)
    trends = country_trends(code)
    events = _safe_event_payload(days=days, limit=50, country_code=profile["country"]["code"]) if include_events else {
        "ok": True,
        "data_state": "not-requested",
        "count": 0,
        "events": [],
    }

    indicator_records: list[dict[str, Any]] = []
    missing_data: list[dict[str, Any]] = []
    source_candidates: list[dict[str, Any]] = []
    for item in indicators.get("indicators", []):
        latest = item.get("latest") or {}
        record = {
            "record_type": "indicator",
            "id": item.get("id"),
            "key": item.get("key"),
            "label": item.get("label"),
            "country_code": profile["country"]["code"],
            "value": latest.get("value"),
            "unit": item.get("unit"),
            "reporting_year": latest.get("year"),
            "source": item.get("source"),
            "source_id": item.get("source_id"),
            "source_url": item.get("source_url"),
            "data_state": item.get("data_state", "unavailable"),
            "cache_state": item.get("cache_state"),
            "retrieved_at": item.get("retrieved_at"),
            "stale": bool(item.get("stale")),
        }
        indicator_records.append(record)
        source_candidates.append(record)
        if latest.get("value") is None:
            missing_data.append({
                "record_type": "indicator",
                "id": item.get("id"),
                "label": item.get("label"),
                "reason": "No validated public value is currently available.",
            })

    event_records: list[dict[str, Any]] = []
    for item in events.get("events", []):
        record = {
            "record_type": "event",
            "id": item.get("id"),
            "label": item.get("title"),
            "country_code": item.get("country_code") or profile["country"]["code"],
            "category": item.get("category"),
            "observed_at": item.get("observed_at"),
            "source": item.get("source_name") or item.get("source"),
            "source_id": item.get("source"),
            "source_url": item.get("source_url"),
            "data_state": item.get("data_state") or events.get("data_state"),
            "coordinates": item.get("coordinates"),
            "country_match_method": item.get("country_match_method"),
            "country_match_confidence": item.get("country_match_confidence"),
        }
        event_records.append(record)
        source_candidates.append(record)

    trend_records = [
        {
            "record_type": "trend",
            "id": item.get("id"),
            "key": item.get("key"),
            "label": item.get("label"),
            "unit": item.get("unit"),
            "source": item.get("source"),
            "source_url": item.get("source_url"),
            "data_state": item.get("data_state"),
            "series": item.get("series") or [],
        }
        for item in trends.get("trends", [])
    ]

    country_name = profile["country"]["name"]
    states = [item.get("data_state") for item in indicator_records] + [events.get("data_state")]
    return _base_bundle(
        "country",
        title=f"{country_name} — Public Country Intelligence Brief",
        summary=profile.get("summary") or f"Source-aware public evidence for {country_name}.",
        scope={"country_count": 1, "indicator_count": len(indicator_records), "trend_count": len(trend_records), "event_count": len(event_records)},
        state={"view_type": "country", "country": profile["country"]["code"], "days": days, "include_events": include_events},
        geography={"countries": [profile["country"]], "map_reference": {"latitude": profile["country"].get("latitude"), "longitude": profile["country"].get("longitude")}},
        selected_dates={"event_window_days": days, "indicator_reporting_years": sorted({item.get("reporting_year") for item in indicator_records if item.get("reporting_year")})},
        filters={"country": profile["country"]["code"], "include_events": include_events, "days": days},
        evidence={"indicators": indicator_records, "trends": trend_records, "events": event_records, "layers": [], "thematic_items": []},
        source_records=_dedupe_sources(source_candidates),
        data_states=_state_summary(states),
        missing_data=missing_data,
        sections=[
            {"heading": "Country scope", "text": f"This brief organizes public evidence for {country_name} without creating a country ranking."},
            {"heading": "Latest available indicators", "item_count": len([item for item in indicator_records if item.get("value") is not None]), "record_type": "indicators"},
            {"heading": "Trend coverage", "item_count": len(trend_records), "record_type": "trends"},
            {"heading": "Recent public events", "item_count": len(event_records), "record_type": "events", "data_state": events.get("data_state")},
            {"heading": "Data gaps", "item_count": len(missing_data), "record_type": "missing_data"},
        ],
        methodology_notes=[
            "Latest non-null public observations are used and reporting years remain visible.",
            "Missing values are not imputed and zero remains distinct from unavailable.",
            "Country-linked event records retain their source and matching basis where available.",
            "Cached, stale, reference-snapshot, and unavailable states remain labeled.",
        ],
        interpretation_limits=profile.get("interpretation") or [
            "Indicators describe public conditions but do not establish causality.",
            "Event counts reflect available source records rather than total incidence or severity.",
        ],
    )


def _comparison_bundle(country: str, compare: str, *, days: int, indicator: str | None) -> dict[str, Any]:
    left = _clean_code(country)
    right = _clean_code(compare, "GHA")
    if left == right:
        raise BriefingError("duplicate_country")
    indicator_filter = _clean_identifier(indicator)
    payload = compare_countries(left, right, include_events=True, include_brief=True, days=days, limit=50)
    brief = payload.get("brief") or {}

    rows = list(payload.get("indicators", {}).get("rows") or [])
    if indicator_filter:
        rows = [item for item in rows if item.get("id") == indicator_filter]
        if not rows:
            raise BriefingError("unsupported_indicator")
    indicator_records: list[dict[str, Any]] = []
    source_candidates: list[dict[str, Any]] = []
    missing_data: list[dict[str, Any]] = []
    for row in rows:
        for side_name, country_record in (("primary", payload["scope"]["primary_country"]), ("comparison", payload["scope"]["comparison_country"])):
            record = row.get(side_name) or {}
            item = {
                "record_type": "indicator",
                "side": side_name,
                "id": row.get("id"),
                "label": row.get("label"),
                "domain": row.get("domain"),
                "country_code": country_record.get("code"),
                "country_name": country_record.get("name"),
                "value": record.get("value"),
                "unit": record.get("unit") or row.get("unit"),
                "reporting_year": record.get("year"),
                "source": record.get("source"),
                "source_id": record.get("source_id"),
                "source_url": record.get("source_url"),
                "data_state": record.get("data_state", "unavailable"),
                "compatibility": row.get("compatibility"),
                "calculation_eligible": row.get("calculation_eligible"),
                "absolute_difference": row.get("absolute_difference"),
                "percent_difference": row.get("percent_difference"),
                "warnings": row.get("warnings") or [],
            }
            indicator_records.append(item)
            source_candidates.append(item)
        if row.get("availability") != "both" or row.get("compatibility") != "aligned":
            missing_data.append({
                "record_type": "comparison-gap",
                "id": row.get("id"),
                "label": row.get("label"),
                "availability": row.get("availability"),
                "compatibility": row.get("compatibility"),
                "warnings": row.get("warnings") or [],
            })

    trend_records = [
        item for item in payload.get("trends", {}).get("trends", [])
        if not indicator_filter or item.get("id") == indicator_filter
    ]
    event_records: list[dict[str, Any]] = []
    for side_name in ("primary", "comparison"):
        event_payload = (payload.get("events") or {}).get(side_name) or {}
        for item in event_payload.get("events", []):
            record = {
                "record_type": "event",
                "side": side_name,
                "id": item.get("id"),
                "label": item.get("title"),
                "country_code": item.get("country_code"),
                "observed_at": item.get("observed_at"),
                "source": item.get("source_name") or item.get("source"),
                "source_id": item.get("source"),
                "source_url": item.get("source_url"),
                "data_state": item.get("data_state") or event_payload.get("data_state"),
            }
            event_records.append(record)
            source_candidates.append(record)

    left_country = payload["scope"]["primary_country"]
    right_country = payload["scope"]["comparison_country"]
    states = [item.get("data_state") for item in indicator_records + event_records]
    return _base_bundle(
        "comparison",
        title=brief.get("title") or f"{left_country['name']} and {right_country['name']} — Public Comparison Brief",
        summary=f"A source-aware comparison of {left_country['name']} and {right_country['name']} that preserves reporting years, units, source identity, delivery state, and methodological conflicts.",
        scope={
            "country_count": 2,
            "indicator_row_count": len(rows),
            "trend_count": len(trend_records),
            "event_count": len(event_records),
            "aligned_indicator_count": sum(1 for item in rows if item.get("compatibility") == "aligned"),
            "conflict_count": sum(1 for item in rows if item.get("compatibility") not in {"aligned", "unavailable", "partial"}),
        },
        state={"view_type": "comparison", "country": left_country["code"], "compare": right_country["code"], "days": days, "indicator": indicator_filter or None},
        geography={"countries": [left_country, right_country]},
        selected_dates={"event_window_days": days, "reporting_years": sorted({item.get("reporting_year") for item in indicator_records if item.get("reporting_year")})},
        filters={"country": left_country["code"], "compare": right_country["code"], "indicator": indicator_filter or None, "days": days},
        evidence={"indicators": indicator_records, "trends": trend_records, "events": event_records, "layers": [], "thematic_items": []},
        source_records=_dedupe_sources(source_candidates),
        data_states=_state_summary(states),
        missing_data=missing_data,
        sections=[
            {"heading": "Comparison scope", "text": f"{left_country['name']} and {right_country['name']} are aligned by indicator ID while source, unit, definition, year, and state differences remain explicit."},
            {"heading": "Latest available indicators", "item_count": len(rows), "record_type": "indicators"},
            {"heading": "Trend differences", "item_count": len(trend_records), "record_type": "trends"},
            {"heading": "Recent public events", "item_count": len(event_records), "record_type": "events"},
            {"heading": "Methodological conflicts and data gaps", "item_count": len(missing_data), "record_type": "missing_data"},
        ],
        methodology_notes=brief.get("methodological_caveats") or payload.get("boundaries") or [],
        interpretation_limits=[
            "A mathematical difference is calculated only when indicator definition, source family, unit, delivery state, and reporting year are compatible.",
            "Visual alignment does not establish methodological equivalence or causality.",
            "The comparison does not create a proprietary composite score or country ranking.",
        ],
    )


def _event_bundle(
    *,
    event_id: str | None,
    days: int,
    country: str | None,
    category: str | None,
    source: str | None,
) -> dict[str, Any]:
    clean_event_id = _clean_identifier(event_id)
    clean_category = _clean_identifier(category)
    clean_source = _clean_identifier(source)
    country_code = _clean_code(country) if country else None

    filters = {
        "event_id": clean_event_id or None,
        "days": days,
        "country": country_code,
        "category": clean_category or None,
        "source": clean_source or None,
    }
    if clean_event_id:
        try:
            detail = event_detail(clean_event_id, days=days)
        except Exception:
            detail = None
        if not detail:
            raise BriefingError("event_not_found")
        events_payload = {
            "ok": True,
            "data_state": detail.get("data_state", "live"),
            "count": 1,
            "events": [detail],
            "source_states": {},
        }
    else:
        events_payload = _safe_event_payload(
            days=days,
            limit=100,
            categories=[clean_category] if clean_category else None,
            sources=[clean_source] if clean_source else None,
            country_code=country_code,
        )

    event_records: list[dict[str, Any]] = []
    source_candidates: list[dict[str, Any]] = []
    for item in events_payload.get("events", []):
        record = {
            "record_type": "event",
            "id": item.get("id"),
            "label": item.get("title"),
            "category": item.get("category"),
            "severity": item.get("severity"),
            "country_code": item.get("country_code"),
            "observed_at": item.get("observed_at"),
            "published_at": item.get("published_at"),
            "coordinates": item.get("coordinates"),
            "source": item.get("source_name") or item.get("source"),
            "source_id": item.get("source"),
            "source_url": item.get("source_url"),
            "data_state": item.get("data_state") or events_payload.get("data_state"),
            "country_match_method": item.get("country_match_method"),
            "country_match_confidence": item.get("country_match_confidence"),
            "description": item.get("description") or item.get("summary"),
        }
        event_records.append(record)
        source_candidates.append(record)

    title = (
        f"{event_records[0]['label']} — Public Event Situation Brief"
        if clean_event_id and event_records
        else "Public Event Situation Brief"
    )
    summary = (
        "A source-aware record of one selected public event."
        if clean_event_id
        else f"A source-aware situation brief covering {len(event_records)} public records from the selected event filters."
    )
    geography_codes = sorted({item.get("country_code") for item in event_records if item.get("country_code")})
    missing_data = []
    if not event_records:
        missing_data.append({"record_type": "events", "reason": "No validated public event records matched the selected filters."})
    return _base_bundle(
        "event",
        title=title,
        summary=summary,
        scope={"event_count": len(event_records), "country_count": len(geography_codes), "source_count": len(_dedupe_sources(source_candidates))},
        state={"view_type": "event", **filters},
        geography={"country_codes": geography_codes, "mapped_event_count": sum(1 for item in event_records if item.get("coordinates"))},
        selected_dates={"event_window_days": days, "observed_dates": sorted({str(item.get("observed_at"))[:10] for item in event_records if item.get("observed_at")})},
        filters=filters,
        evidence={"indicators": [], "trends": [], "events": event_records, "layers": [], "thematic_items": []},
        source_records=_dedupe_sources(source_candidates),
        data_states=_state_summary([item.get("data_state") for item in event_records] or [events_payload.get("data_state")]),
        missing_data=missing_data,
        sections=[
            {"heading": "Situation scope", "text": summary},
            {"heading": "Public event records", "item_count": len(event_records), "record_type": "events"},
            {"heading": "Source coverage", "item_count": len(_dedupe_sources(source_candidates)), "record_type": "sources"},
            {"heading": "Data gaps", "item_count": len(missing_data), "record_type": "missing_data"},
        ],
        methodology_notes=[
            "Event time, publication time, source identity, location, and record type remain distinct where available.",
            "Event records are deduplicated by provider identity and source event ID where supported.",
            "Country attribution retains the matching method and confidence where the connector provides them.",
        ],
        interpretation_limits=[
            "Event counts reflect available public source records and are not measures of total incidence, severity, or risk.",
            "This is not an emergency-alert, operational-response, or safety-critical service.",
            "Mapped proximity does not establish causality or legal responsibility.",
        ],
    )


def _earth_bundle(
    *,
    layer_id: str,
    date_a: str,
    date_b: str,
    latitude: float,
    longitude: float,
    zoom: int,
    opacity: float,
) -> dict[str, Any]:
    clean_layer = _clean_identifier(layer_id, "true-color") or "true-color"
    left_date = _clean_date(date_a)
    right_date = _clean_date(date_b)
    if not left_date or not right_date:
        raise BriefingError("missing_earth_dates")
    if left_date > right_date:
        raise BriefingError("invalid_date_range")
    manifest = earth_export_manifest(
        clean_layer,
        left_date,
        right_date,
        latitude,
        longitude,
        zoom,
        opacity,
    )
    layer_record = {
        "record_type": "earth-observation-layer",
        "id": manifest["view"].get("layer_id"),
        "label": manifest["view"].get("layer_title"),
        "source": manifest.get("source"),
        "source_url": None,
        "source_id": manifest["view"].get("layer_id"),
        "data_state": "requested-view-manifest",
        "left_date": manifest["view"].get("left_date"),
        "right_date": manifest["view"].get("right_date"),
        "center": manifest["view"].get("center"),
        "zoom": manifest["view"].get("zoom"),
        "opacity": manifest["view"].get("opacity"),
        "attribution": manifest.get("attribution"),
        "observation_type": manifest.get("observation_type"),
        "limits": manifest.get("limits"),
    }
    source_records = _dedupe_sources([layer_record])
    return _base_bundle(
        "earth",
        title=f"{layer_record['label']} — Earth Observation Brief",
        summary="A documented Earth-observation view preserving layer identity, selected dates, map center, zoom, opacity, attribution, and interpretation limits.",
        scope={"layer_count": 1, "date_count": 2, "mapped_center_count": 1},
        state={"view_type": "earth", "layer_id": clean_layer, "date_a": left_date, "date_b": right_date, "latitude": latitude, "longitude": longitude, "zoom": zoom, "opacity": opacity},
        geography={"center": manifest["view"].get("center"), "zoom": manifest["view"].get("zoom")},
        selected_dates={"before": manifest["view"].get("left_date"), "after": manifest["view"].get("right_date")},
        filters={"layer_id": clean_layer, "opacity": manifest["view"].get("opacity")},
        evidence={"indicators": [], "trends": [], "events": [], "layers": [layer_record], "thematic_items": []},
        source_records=source_records,
        data_states=_state_summary([layer_record["data_state"]]),
        missing_data=[],
        sections=[
            {"heading": "Observation view", "text": f"{layer_record['label']} from {left_date} to {right_date}."},
            {"heading": "Geographic context", "text": f"Map center {latitude:.4f}, {longitude:.4f}; zoom {manifest['view'].get('zoom')}."},
            {"heading": "Source and attribution", "text": f"{manifest.get('source')}: {manifest.get('attribution')}"},
            {"heading": "Interpretation limits", "text": manifest.get("comparison_boundary")},
        ],
        methodology_notes=[
            "The manifest documents the requested map state rather than certifying that every tile rendered successfully.",
            "Before-and-after views preserve layer, dates, center, zoom, opacity, source, and attribution.",
            "Browser PNG capture is a visual record of the rendered interface, not an authoritative source artifact.",
        ],
        interpretation_limits=[
            str(manifest.get("comparison_boundary")),
            str(manifest.get("limits")),
            "Satellite and derived products may be affected by cloud cover, compositing, sensor conditions, processing choices, latency, and spatial resolution.",
        ],
    )


def _thematic_bundle(
    *,
    dashboard_id: str,
    country: str | None,
    compare: str | None,
    start: str | None,
    end: str | None,
) -> dict[str, Any]:
    clean_dashboard = _clean_identifier(dashboard_id, "climate-environment") or "climate-environment"
    country_code = _clean_code(country) if country else "KEN"
    compare_code = _clean_code(compare) if compare else ""
    start_date = _clean_date(start)
    end_date = _clean_date(end)
    if start_date and end_date and start_date > end_date:
        raise BriefingError("invalid_date_range")

    try:
        payload = dashboard_export(clean_dashboard, country=country_code)
    except ValueError as exc:
        raise BriefingError("dashboard_not_found") from exc

    # v1.21.0 first-class thematic payload.
    if isinstance(payload, dict) and "indicators" in payload:
        if not payload.get("ok"):
            raise BriefingError("dashboard_not_found")
        dashboard = payload.get("dashboard") or {}
        country_record = payload.get("country") or {"code": country_code, "name": country_code}
        indicators = list(payload.get("indicators") or [])
        trends = list(payload.get("trends") or [])
        events = list((payload.get("events") or {}).get("records") or [])
        layers = list(payload.get("earth_layers") or [])
        source_records = _dedupe_sources([
            {
                "record_type": ",".join(item.get("record_types") or []),
                "source": item.get("name"),
                "source_url": item.get("url"),
                "data_state": ",".join(item.get("data_states") or []),
            }
            for item in payload.get("sources") or []
        ])
        evidence_states = [item.get("data_state") for item in indicators]
        evidence_states.extend(item.get("data_state") for item in events)
        evidence_states.extend(item.get("data_state") for item in layers)
        filters = {
            "dashboard_id": clean_dashboard,
            "country": country_record.get("code") or country_code,
            "compare": compare_code or None,
            "start": start_date or None,
            "end": end_date or None,
        }
        return _base_bundle(
            "thematic",
            title=f"{country_record.get('name') or country_record.get('code')} — {dashboard.get('title')} Brief",
            summary=dashboard.get("summary") or "Source-aware thematic public intelligence brief.",
            scope={
                "dashboard_id": clean_dashboard,
                "indicator_count": len(indicators),
                "trend_count": len(trends),
                "event_count": len(events),
                "layer_count": len(layers),
                "registered_source_count": len(source_records),
            },
            state={"view_type": "thematic", **filters},
            geography={
                "country": country_record.get("code") or country_code,
                "country_name": country_record.get("name"),
                "compare": compare_code or None,
                "region": country_record.get("region"),
            },
            selected_dates={"start": start_date or None, "end": end_date or None},
            filters=filters,
            evidence={
                "indicators": indicators,
                "trends": trends,
                "events": events,
                "layers": layers,
                "thematic_items": [],
            },
            source_records=source_records,
            data_states=_state_summary(evidence_states),
            missing_data=list(payload.get("missing_data") or []),
            sections=[
                {"heading": "Dashboard scope", "text": dashboard.get("summary")},
                {"heading": "Latest public indicators", "item_count": len(indicators), "record_type": "indicators"},
                {"heading": "Historical trends", "item_count": len(trends), "record_type": "trends"},
                {"heading": "Recent public events", "item_count": len(events), "record_type": "events"},
                {"heading": "Earth-observation context", "item_count": len(layers), "record_type": "layers"},
                {"heading": "Data gaps", "item_count": len(payload.get("missing_data") or []), "record_type": "missing_data"},
            ],
            methodology_notes=list(payload.get("methodology") or []),
            interpretation_limits=list(payload.get("interpretation_limits") or []),
        )

    # Compatibility for pre-v1.21.0 dashboard fixtures and callers.
    if not payload.get("dashboard", {}).get("ok"):
        raise BriefingError("dashboard_not_found")
    data = payload.get("data") or {}
    dashboard = payload.get("dashboard") or {}
    brief = payload.get("brief") or {}
    sources = payload.get("sources", {}).get("sources") or []
    thematic_items = list(data.get("evidence_items") or [])
    source_records = _dedupe_sources([
        {
            "record_type": "thematic-source",
            "source": item.get("source"),
            "data_state": item.get("health") or item.get("data_state"),
        }
        for item in sources
    ])
    missing_data = [
        {
            "record_type": "thematic-item",
            "id": item.get("domain"),
            "label": item.get("label"),
            "reason": item.get("value_status"),
        }
        for item in thematic_items
        if str(item.get("data_state")) in {"source-registry-ready", "unavailable"}
    ]
    filters = {
        "dashboard_id": clean_dashboard,
        "country": country_code or None,
        "compare": compare_code or None,
        "start": start_date or None,
        "end": end_date or None,
    }
    return _base_bundle(
        "thematic",
        title=brief.get("title") or f"{dashboard.get('title')} — Thematic Intelligence Brief",
        summary=brief.get("summary") or dashboard.get("summary") or "Source-aware thematic public intelligence brief.",
        scope={"dashboard_id": clean_dashboard, "domain_count": len(dashboard.get("domains") or []), "evidence_item_count": len(thematic_items), "registered_source_count": len(source_records)},
        state={"view_type": "thematic", **filters},
        geography={"country": country_code or None, "compare": compare_code or None, "region": None},
        selected_dates={"start": start_date or None, "end": end_date or None},
        filters=filters,
        evidence={"indicators": [], "trends": [], "events": [], "layers": [], "thematic_items": thematic_items},
        source_records=source_records,
        data_states=_state_summary([item.get("data_state") for item in thematic_items]),
        missing_data=missing_data,
        sections=brief.get("sections") or [
            {"heading": "Dashboard scope", "text": dashboard.get("summary")},
            {"heading": "Evidence domains", "item_count": len(thematic_items), "record_type": "thematic_items"},
            {"heading": "Registered sources", "item_count": len(source_records), "record_type": "sources"},
        ],
        methodology_notes=data.get("notes") or [
            "Live values appear only when a connector returns a validated public record.",
            "Source-registry context remains visible when a live value is unavailable.",
        ],
        interpretation_limits=[
            str(dashboard.get("public_disclaimer") or "Cross-domain views preserve source-specific dates, units, methods, uncertainty, and freshness."),
            "Unlike indicators are not merged into a proprietary composite score.",
        ],
    )


def briefing_directory() -> dict[str, Any]:
    return {
        "ok": True,
        "version": VERSION,
        "schema_version": SCHEMA_VERSION,
        "methodology_version": METHODOLOGY_VERSION,
        "generated_at": _now(),
        "brief_types": [
            {"id": key, **value}
            for key, value in BRIEF_TYPES.items()
        ],
        "server_export_formats": EXPORT_FORMATS,
        "browser_export_formats": BROWSER_EXPORTS,
        "pdf_status": "deferred-until-print-html-stable",
        "routes": {
            "brief": "/public/briefing-studio/brief",
            "export": "/public/briefing-studio/export",
            "diagnostics": "/public/briefing-studio/diagnostics",
        },
        "boundaries": [
            "Briefs are deterministic assemblies of available public evidence and do not invent missing values.",
            "Source identity, dates, units, delivery states, missing data, and interpretation limits remain visible.",
            "Platform Core is optional and is not required for public brief generation or export.",
        ],
    }


def build_brief(
    brief_type: str,
    *,
    country: str = "KEN",
    compare: str = "GHA",
    event_id: str | None = None,
    days: int = 14,
    category: str | None = None,
    source: str | None = None,
    layer_id: str = "true-color",
    date_a: str = "",
    date_b: str = "",
    latitude: float = 12.0,
    longitude: float = 20.0,
    zoom: int = 2,
    opacity: float = 0.72,
    dashboard_id: str = "climate-environment",
    start: str | None = None,
    end: str | None = None,
    indicator: str | None = None,
    include_events: bool = True,
) -> dict[str, Any]:
    normalized_type = str(brief_type or "country").strip().lower()
    if normalized_type not in BRIEF_TYPES:
        raise BriefingError("unsupported_brief_type")
    safe_days = _clamp_int(days, 1, 90, 14)

    if normalized_type == "country":
        return _country_bundle(country, days=safe_days, include_events=bool(include_events))
    if normalized_type == "comparison":
        return _comparison_bundle(country, compare, days=safe_days, indicator=indicator)
    if normalized_type == "event":
        return _event_bundle(event_id=event_id, days=safe_days, country=country if country else None, category=category, source=source)
    if normalized_type == "earth":
        return _earth_bundle(
            layer_id=layer_id,
            date_a=date_a,
            date_b=date_b,
            latitude=_clamp_float(latitude, -90.0, 90.0, 12.0),
            longitude=_clamp_float(longitude, -180.0, 180.0, 20.0),
            zoom=_clamp_int(zoom, 1, 12, 2),
            opacity=_clamp_float(opacity, 0.1, 1.0, 0.72),
        )
    return _thematic_bundle(
        dashboard_id=dashboard_id,
        country=country if country else None,
        compare=compare if compare else None,
        start=start,
        end=end,
    )


def _csv_safe(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value
    text = str(value)
    if text.startswith(("=", "+", "-", "@", "\t", "\r")):
        return "'" + text
    return text


def _flatten_records(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    evidence = bundle.get("evidence") or {}
    for group in ("indicators", "trends", "events", "layers", "thematic_items"):
        for item in evidence.get(group, []) or []:
            output.append({"evidence_group": group, **item})
    if not output:
        output.append({"evidence_group": "brief", "label": bundle.get("title"), "data_state": "no-records"})
    return output


def _html_value(value: Any) -> str:
    if value is None or value == "":
        return "Unavailable"
    if isinstance(value, (dict, list)):
        return escape(json.dumps(value, ensure_ascii=False))
    return escape(str(value))


def _html_export(bundle: dict[str, Any]) -> str:
    source_items = "".join(
        f'<li><strong>{escape(str(item.get("name") or "Source"))}</strong>'
        + (f' — <a href="{escape(str(item.get("url")))}">{escape(str(item.get("url")))}</a>' if item.get("url") else "")
        + (f' <span>({escape(", ".join(item.get("data_states") or []))})</span>' if item.get("data_states") else "")
        + "</li>"
        for item in bundle.get("source_records", [])
    ) or "<li>No source record was returned for this brief.</li>"

    section_items = "".join(
        f'<section><h2>{escape(str(item.get("heading") or "Section"))}</h2>'
        + (f'<p>{escape(str(item.get("text")))}</p>' if item.get("text") else "")
        + (f'<p><strong>Records:</strong> {escape(str(item.get("item_count")))}</p>' if item.get("item_count") is not None else "")
        + "</section>"
        for item in bundle.get("sections", [])
    )

    rows = []
    for item in _flatten_records(bundle):
        rows.append(
            "<tr>"
            f'<td>{_html_value(item.get("evidence_group"))}</td>'
            f'<td>{_html_value(item.get("id"))}</td>'
            f'<td>{_html_value(item.get("label"))}</td>'
            f'<td>{_html_value(item.get("country_name") or item.get("country_code"))}</td>'
            f'<td>{_html_value(item.get("value"))}</td>'
            f'<td>{_html_value(item.get("unit"))}</td>'
            f'<td>{_html_value(item.get("reporting_year") or item.get("observed_at"))}</td>'
            f'<td>{_html_value(item.get("source"))}</td>'
            f'<td>{_html_value(item.get("data_state"))}</td>'
            "</tr>"
        )

    methodology = "".join(f"<li>{escape(str(item))}</li>" for item in bundle.get("methodology_notes", []))
    limits = "".join(f"<li>{escape(str(item))}</li>" for item in bundle.get("interpretation_limits", []))
    missing = "".join(f"<li>{escape(json.dumps(item, ensure_ascii=False))}</li>" for item in bundle.get("missing_data", [])) or "<li>No explicit missing-data record was generated.</li>"

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(bundle['title'])}</title>
<style>
body{{font-family:Arial,sans-serif;max-width:1100px;margin:0 auto;padding:36px;color:#181818;line-height:1.55}}
h1{{font-size:34px;margin-bottom:8px}}h2{{margin-top:28px;font-size:20px}}.meta{{color:#555;font-size:13px}}
.boundary{{padding:14px;border-left:4px solid #d71920;background:#f7f7f7}}table{{width:100%;border-collapse:collapse;margin-top:16px;font-size:12px}}
th,td{{padding:8px;border:1px solid #ddd;text-align:left;vertical-align:top}}th{{background:#f2f2f2}}a{{color:#8b1116;overflow-wrap:anywhere}}
@media print{{body{{max-width:none;padding:0}}section,table{{break-inside:avoid}}a[href]::after{{content:" (" attr(href) ")";font-size:9px}}}}
</style>
</head>
<body>
<p class="meta">Sustainable Catalyst Site Intelligence · v{escape(VERSION)} · schema {escape(SCHEMA_VERSION)}</p>
<h1>{escape(bundle['title'])}</h1>
<p>{escape(bundle['summary'])}</p>
<p class="meta">Brief ID: {escape(bundle['brief_id'])}<br>Generated: {escape(bundle['generated_at'])}<br>Methodology: {escape(bundle['methodology_version'])}</p>
{section_items}
<h2>Evidence records</h2>
<table><thead><tr><th>Type</th><th>ID</th><th>Label</th><th>Geography</th><th>Value</th><th>Unit</th><th>Date/year</th><th>Source</th><th>State</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
<h2>Sources</h2><ul>{source_items}</ul>
<h2>Missing data</h2><ul>{missing}</ul>
<h2>Methodology</h2><ul>{methodology}</ul>
<h2>Interpretation limits</h2><ul>{limits}</ul>
<p class="boundary"><strong>Responsible-use boundary:</strong> {escape(bundle['responsible_use'])}</p>
</body>
</html>"""


def briefing_export(
    brief_type: str,
    export_format: str = "json",
    **kwargs: Any,
) -> tuple[str, str, str]:
    bundle = build_brief(brief_type, **kwargs)
    fmt = str(export_format or "json").strip().lower()
    if fmt not in EXPORT_FORMATS:
        raise BriefingError("unsupported_export_format")
    stem = re.sub(r"[^a-z0-9-]+", "-", f"site-intelligence-{bundle['brief_type']}-{bundle['brief_id']}".lower()).strip("-")

    if fmt == "json":
        payload = {
            **bundle,
            "export_manifest": {
                "format": "json",
                "filename": f"{stem}.json",
                "application_version": VERSION,
                "schema_version": SCHEMA_VERSION,
                "methodology_version": METHODOLOGY_VERSION,
                "generated_at": bundle["generated_at"],
            },
        }
        return json.dumps(payload, indent=2, ensure_ascii=False), "application/json", f"{stem}.json"

    if fmt == "csv":
        records = _flatten_records(bundle)
        fieldnames = [
            "brief_id",
            "brief_type",
            "evidence_group",
            "record_type",
            "id",
            "label",
            "side",
            "country_code",
            "country_name",
            "value",
            "unit",
            "reporting_year",
            "observed_at",
            "source",
            "source_id",
            "source_url",
            "data_state",
            "compatibility",
            "notes",
        ]
        output = StringIO(newline="")
        writer = DictWriter(output, fieldnames=fieldnames, lineterminator="\r\n")
        writer.writeheader()
        for item in records:
            writer.writerow({
                "brief_id": _csv_safe(bundle["brief_id"]),
                "brief_type": _csv_safe(bundle["brief_type"]),
                "evidence_group": _csv_safe(item.get("evidence_group")),
                "record_type": _csv_safe(item.get("record_type")),
                "id": _csv_safe(item.get("id")),
                "label": _csv_safe(item.get("label")),
                "side": _csv_safe(item.get("side")),
                "country_code": _csv_safe(item.get("country_code")),
                "country_name": _csv_safe(item.get("country_name")),
                "value": _csv_safe(item.get("value")),
                "unit": _csv_safe(item.get("unit")),
                "reporting_year": _csv_safe(item.get("reporting_year")),
                "observed_at": _csv_safe(item.get("observed_at")),
                "source": _csv_safe(item.get("source")),
                "source_id": _csv_safe(item.get("source_id")),
                "source_url": _csv_safe(item.get("source_url")),
                "data_state": _csv_safe(item.get("data_state")),
                "compatibility": _csv_safe(item.get("compatibility")),
                "notes": _csv_safe(" | ".join(item.get("warnings") or []) if isinstance(item.get("warnings"), list) else item.get("description") or item.get("limits")),
            })
        return "\ufeff" + output.getvalue(), "text/csv", f"{stem}.csv"

    return _html_export(bundle), "text/html", f"{stem}.html"


def briefing_diagnostics() -> dict[str, Any]:
    return {
        "ok": True,
        "version": VERSION,
        "schema_version": SCHEMA_VERSION,
        "methodology_version": METHODOLOGY_VERSION,
        "generated_at": _now(),
        "brief_type_count": len(BRIEF_TYPES),
        "brief_types": sorted(BRIEF_TYPES),
        "server_export_formats": EXPORT_FORMATS,
        "browser_export_formats": BROWSER_EXPORTS,
        "checks": {
            "country_builder": "ready",
            "comparison_builder": "ready",
            "event_builder": "ready-with-local-source-failure-state",
            "earth_builder": "ready-manifest-based",
            "thematic_builder": "ready-source-aware",
            "json_export": "ready",
            "csv_export": "ready-with-spreadsheet-formula-safeguards",
            "html_export": "ready-print-first",
            "png_export": "browser-rendered",
            "pdf_export": "deferred",
            "platform_core_dependency": "optional",
        },
        "public_safe": True,
    }
