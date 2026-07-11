from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from csv import DictWriter
from datetime import datetime, timezone
from io import StringIO
import json
import re
from typing import Any, Iterable
from urllib.parse import urlparse

from .live_country_intelligence import country_catalog, country_indicators, country_trends
from .unified_live_events import unified_events
from .version import APP_VERSION

VERSION = APP_VERSION

VALID_VALUE_STATES = {
    "live",
    "partial-live",
    "cached",
    "stale",
    "reference-snapshot",
}

UNIT_ALIASES = {
    "current us$": "current-usd",
    "current usd": "current-usd",
    "current us dollars": "current-usd",
    "us$": "usd",
    "usd": "usd",
    "%": "percent",
    "percent": "percent",
    "metric tons": "metric-tons",
    "metric tonnes": "metric-tons",
    "people": "people",
    "persons": "people",
}


class ComparisonError(ValueError):
    """Public-safe comparison input or export error."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_text(value: Any) -> str:
    return " ".join(str(value or "").split()).strip().lower()


def _clean_code(value: str) -> str:
    code = str(value or "").strip().upper()
    if not re.fullmatch(r"[A-Z]{2,3}", code):
        raise ComparisonError("unsupported_country")
    payload = country_catalog()
    match = next(
        (
            item
            for item in payload.get("countries", [])
            if item.get("code") == code or item.get("iso2") == code
        ),
        None,
    )
    if not match:
        raise ComparisonError("unsupported_country")
    return str(match["code"])


def _country_pair(country: str, compare: str) -> tuple[str, str]:
    left_code = _clean_code(country)
    right_code = _clean_code(compare)
    if left_code == right_code:
        raise ComparisonError("duplicate_country")
    return left_code, right_code


def _indicator_map(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(item.get("id")): item
        for item in payload.get("indicators", [])
        if item.get("id")
    }


def _normalize_unit(value: Any) -> str | None:
    text = _normalize_text(value)
    if not text:
        return None
    text = text.replace("％", "%")
    text = re.sub(r"\s+", " ", text)
    return UNIT_ALIASES.get(text, text)


def _source_family(source: Any, source_url: Any) -> str | None:
    text = _normalize_text(source)
    if "world bank" in text:
        return "world-bank"
    if "united nations" in text or text.startswith("un "):
        return "united-nations"
    if "nasa" in text:
        return "nasa"
    if "usgs" in text:
        return "usgs"

    try:
        host = (urlparse(str(source_url or "")).hostname or "").lower()
    except ValueError:
        host = ""
    if not host:
        return text or None
    parts = host.split(".")
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return host


def _source_signature(item: dict[str, Any] | None) -> dict[str, Any]:
    item = item or {}
    source_id = _normalize_text(item.get("source_id")) or None
    family = _source_family(item.get("source"), item.get("source_url"))
    return {
        "source_id": source_id,
        "source_family": family,
        "source": item.get("source"),
        "source_url": item.get("source_url"),
    }


def _source_match(left_item: dict[str, Any] | None, right_item: dict[str, Any] | None) -> bool:
    if not left_item or not right_item:
        return False
    left = _source_signature(left_item)
    right = _source_signature(right_item)

    if left["source_id"] and right["source_id"] and left["source_id"] != right["source_id"]:
        return False
    if left["source_family"] and right["source_family"] and left["source_family"] != right["source_family"]:
        return False
    return bool(
        (left["source_id"] and right["source_id"])
        or (left["source_family"] and right["source_family"])
    )


def _definition_match(
    definition: dict[str, Any],
    left_item: dict[str, Any] | None,
    right_item: dict[str, Any] | None,
) -> bool:
    if not left_item or not right_item:
        return False
    indicator_id = _normalize_text(definition.get("id"))
    ids = {
        _normalize_text(left_item.get("id")),
        _normalize_text(right_item.get("id")),
    }
    if ids != {indicator_id}:
        return False

    left_key = _normalize_text(left_item.get("key"))
    right_key = _normalize_text(right_item.get("key"))
    if left_key and right_key and left_key != right_key:
        return False

    left_label = _normalize_text(left_item.get("label"))
    right_label = _normalize_text(right_item.get("label"))
    if left_label and right_label and left_label != right_label:
        return False
    return True


def _safe_year(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        year = int(value)
    except (TypeError, ValueError):
        return None
    return year if 1800 <= year <= 2200 else None


def _latest_record(item: dict[str, Any] | None) -> dict[str, Any] | None:
    if not item:
        return None
    latest = item.get("latest")
    if not isinstance(latest, dict) or latest.get("value") is None:
        return None
    return {
        "value": latest.get("value"),
        "year": _safe_year(latest.get("year")),
        "unit": item.get("unit"),
        "format": item.get("format"),
        "source": item.get("source"),
        "source_id": item.get("source_id"),
        "source_url": item.get("source_url"),
        "data_state": item.get("data_state", "unavailable"),
        "cache_state": item.get("cache_state"),
        "retrieved_at": item.get("retrieved_at"),
        "stale": bool(item.get("stale")),
        "lineage": item.get("lineage") or {},
    }


def _numeric(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in {float("inf"), float("-inf")}:
        return None
    return number


def _availability(left: dict[str, Any] | None, right: dict[str, Any] | None) -> str:
    if left and right:
        return "both"
    if left:
        return "primary-only"
    if right:
        return "comparison-only"
    return "none"


def _comparison_row(
    definition: dict[str, Any],
    left_item: dict[str, Any] | None,
    right_item: dict[str, Any] | None,
    left_code: str,
    right_code: str,
) -> dict[str, Any]:
    left = _latest_record(left_item)
    right = _latest_record(right_item)
    availability = _availability(left, right)
    both_available = availability == "both"

    unit_left = (left or left_item or {}).get("unit")
    unit_right = (right or right_item or {}).get("unit")
    normalized_unit_left = _normalize_unit(unit_left)
    normalized_unit_right = _normalize_unit(unit_right)
    unit_match = bool(
        normalized_unit_left
        and normalized_unit_right
        and normalized_unit_left == normalized_unit_right
    )
    definition_match = _definition_match(definition, left_item, right_item)
    source_match = _source_match(left_item, right_item)

    valid_states = bool(
        left
        and right
        and left.get("data_state") in VALID_VALUE_STATES
        and right.get("data_state") in VALID_VALUE_STATES
    )

    left_year = left.get("year") if left else None
    right_year = right.get("year") if right else None
    years_match = bool(
        left_year is not None
        and right_year is not None
        and left_year == right_year
    )

    display_comparable = bool(
        both_available
        and valid_states
        and unit_match
        and definition_match
        and source_match
    )
    calculation_eligible = bool(display_comparable and years_match)

    warnings: list[str] = []
    flags: list[str] = []

    if availability == "none":
        warnings.append("No validated public value is currently available for either country.")
        flags.append("missing-both")
    elif availability != "both":
        missing_code = right_code if availability == "primary-only" else left_code
        warnings.append(
            f"No validated public value is currently available for {missing_code}."
        )
        flags.append("missing-one-country")

    if both_available and not valid_states:
        warnings.append(
            "One or both values have an unsupported delivery state; no mathematical difference is calculated."
        )
        flags.append("state-conflict")
    if both_available and not unit_match:
        warnings.append(
            "Units differ; values are displayed separately and no mathematical difference is calculated."
        )
        flags.append("unit-conflict")
    if both_available and not definition_match:
        warnings.append(
            "Indicator definitions differ and are not methodologically equivalent."
        )
        flags.append("definition-conflict")
    if both_available and not source_match:
        warnings.append(
            "Source identifiers or publishers differ; values are displayed separately and no mathematical difference is calculated."
        )
        flags.append("source-conflict")
    if display_comparable and not years_match:
        warnings.append(
            f"Reporting years differ: {left_code} {left_year or 'unavailable'}, "
            f"{right_code} {right_year or 'unavailable'}. No mathematical difference is calculated."
        )
        flags.append("reporting-year-mismatch")
    if left and left.get("data_state") == "reference-snapshot":
        warnings.append(f"{left_code} uses a labeled reference snapshot.")
        flags.append("primary-reference-snapshot")
    if right and right.get("data_state") == "reference-snapshot":
        warnings.append(f"{right_code} uses a labeled reference snapshot.")
        flags.append("comparison-reference-snapshot")
    if left and left.get("stale"):
        warnings.append(f"{left_code} uses a stale last-known-good value.")
        flags.append("primary-stale")
    if right and right.get("stale"):
        warnings.append(f"{right_code} uses a stale last-known-good value.")
        flags.append("comparison-stale")

    absolute_difference = None
    percent_difference = None
    if calculation_eligible:
        left_number = _numeric(left.get("value"))
        right_number = _numeric(right.get("value"))
        if left_number is not None and right_number is not None:
            absolute_difference = right_number - left_number
            if left_number != 0:
                percent_difference = (
                    (right_number - left_number) / abs(left_number)
                ) * 100

    if availability == "none":
        compatibility = "unavailable"
    elif availability != "both":
        compatibility = "partial"
    elif not valid_states:
        compatibility = "state-conflict"
    elif not definition_match:
        compatibility = "definition-conflict"
    elif not unit_match:
        compatibility = "unit-conflict"
    elif not source_match:
        compatibility = "source-conflict"
    elif not years_match:
        compatibility = "different-reporting-years"
    else:
        compatibility = "aligned"

    return {
        "id": definition.get("id"),
        "key": definition.get("key"),
        "label": definition.get("label"),
        "domain": definition.get("domain"),
        "unit": unit_left or unit_right or definition.get("unit"),
        "normalized_unit": normalized_unit_left or normalized_unit_right,
        "format": definition.get("format"),
        "primary": left,
        "comparison": right,
        "availability": availability,
        "compatibility": compatibility,
        "display_comparable": display_comparable,
        "calculation_eligible": calculation_eligible,
        "comparable": calculation_eligible,
        "reporting_years_match": years_match,
        "unit_match": unit_match,
        "definition_match": definition_match,
        "source_match": source_match,
        "value_states_valid": valid_states,
        "absolute_difference": absolute_difference,
        "percent_difference": percent_difference,
        "warnings": list(dict.fromkeys(warnings)),
        "methodology_flags": list(dict.fromkeys(flags)),
        "source_attribution": {
            "primary": _source_signature(left_item),
            "comparison": _source_signature(right_item),
        },
    }


def _fetch_country_pair(
    country: str,
    compare: str,
) -> tuple[str, str, dict[str, Any], dict[str, Any]]:
    left_code, right_code = _country_pair(country, compare)
    with ThreadPoolExecutor(max_workers=2) as executor:
        left_future = executor.submit(country_indicators, left_code)
        right_future = executor.submit(country_indicators, right_code)
        left_payload = left_future.result()
        right_payload = right_future.result()
    return left_code, right_code, left_payload, right_payload


def _definitions(
    left_payload: dict[str, Any],
    right_payload: dict[str, Any],
) -> list[dict[str, Any]]:
    definitions: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in [
        *left_payload.get("indicators", []),
        *right_payload.get("indicators", []),
    ]:
        indicator_id = str(item.get("id") or "")
        if not indicator_id or indicator_id in seen:
            continue
        seen.add(indicator_id)
        definitions.append(item)
    return definitions


def _aggregate_data_state(left_state: Any, right_state: Any) -> str:
    left = str(left_state or "unavailable")
    right = str(right_state or "unavailable")
    if left == right:
        return left
    if "unavailable" in {left, right}:
        return "partial"
    if "stale" in {left, right}:
        return "mixed-stale"
    return "mixed"


def _build_indicator_comparison(
    left_code: str,
    right_code: str,
    left_payload: dict[str, Any],
    right_payload: dict[str, Any],
) -> dict[str, Any]:
    left_map = _indicator_map(left_payload)
    right_map = _indicator_map(right_payload)
    rows = [
        _comparison_row(
            definition,
            left_map.get(str(definition.get("id"))),
            right_map.get(str(definition.get("id"))),
            left_code,
            right_code,
        )
        for definition in _definitions(left_payload, right_payload)
    ]

    compatibility_counts: dict[str, int] = {}
    for row in rows:
        key = str(row["compatibility"])
        compatibility_counts[key] = compatibility_counts.get(key, 0) + 1

    available_count = sum(1 for row in rows if row["availability"] != "none")
    complete_count = sum(1 for row in rows if row["availability"] == "both")
    partial_count = sum(
        1
        for row in rows
        if row["availability"] in {"primary-only", "comparison-only"}
    )

    return {
        "ok": True,
        "version": VERSION,
        "generated_at": _now(),
        "data_state": _aggregate_data_state(
            left_payload.get("data_state"), right_payload.get("data_state")
        ),
        "primary_country": left_payload.get("country"),
        "comparison_country": right_payload.get("country"),
        "indicator_count": len(rows),
        "available_indicator_count": available_count,
        "complete_indicator_count": complete_count,
        "partial_indicator_count": partial_count,
        "unavailable_indicator_count": compatibility_counts.get("unavailable", 0),
        "aligned_indicator_count": compatibility_counts.get("aligned", 0),
        "calculation_eligible_count": sum(
            1 for row in rows if row["calculation_eligible"]
        ),
        "conflict_count": sum(
            compatibility_counts.get(key, 0)
            for key in (
                "state-conflict",
                "definition-conflict",
                "unit-conflict",
                "source-conflict",
                "different-reporting-years",
            )
        ),
        "compatibility_counts": compatibility_counts,
        "rows": rows,
        "methodology": [
            "Indicator IDs, definitions, units, and source families must match before values are treated as display-comparable.",
            "A mathematical difference is calculated only when reporting years also match.",
            "Reporting-year mismatches, source conflicts, unit conflicts, and missing records remain explicit.",
            "Reference snapshots, cached values, stale values, and missing records remain labeled.",
            "No proprietary composite score or unexplained country ranking is produced.",
        ],
    }


def compare_indicators(country: str, compare: str) -> dict[str, Any]:
    left_code, right_code, left_payload, right_payload = _fetch_country_pair(
        country, compare
    )
    return _build_indicator_comparison(
        left_code, right_code, left_payload, right_payload
    )


def _clean_series(series: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    by_year: dict[int, float] = {}
    for item in series or []:
        year = _safe_year(item.get("year"))
        value = _numeric(item.get("value"))
        if year is None or value is None:
            continue
        by_year[year] = value
    return [{"year": year, "value": by_year[year]} for year in sorted(by_year)]


def _build_trend_comparison(
    left_payload: dict[str, Any],
    right_payload: dict[str, Any],
) -> dict[str, Any]:
    left_map = _indicator_map(left_payload)
    right_map = _indicator_map(right_payload)
    trends: list[dict[str, Any]] = []

    for definition in _definitions(left_payload, right_payload):
        indicator_id = str(definition.get("id") or "")
        left = left_map.get(indicator_id)
        right = right_map.get(indicator_id)
        left_series = _clean_series((left or {}).get("series") or [])
        right_series = _clean_series((right or {}).get("series") or [])
        left_by_year = {item["year"]: item["value"] for item in left_series}
        right_by_year = {item["year"]: item["value"] for item in right_series}
        years = sorted(set(left_by_year) | set(right_by_year))
        common_years = sorted(set(left_by_year) & set(right_by_year))

        unit_match = bool(
            _normalize_unit((left or {}).get("unit"))
            and _normalize_unit((left or {}).get("unit"))
            == _normalize_unit((right or {}).get("unit"))
        )
        definition_match = _definition_match(definition, left, right)
        source_match = _source_match(left, right)
        both_series = bool(left_series and right_series)
        chartable = bool(
            both_series
            and unit_match
            and definition_match
            and source_match
            and common_years
        )

        if not left_series and not right_series:
            display_mode = "unavailable"
            chart_warning = "No validated multi-year series is available for either country."
        elif not left_series:
            display_mode = "comparison-only"
            chart_warning = "A validated multi-year series is unavailable for the primary country."
        elif not right_series:
            display_mode = "primary-only"
            chart_warning = "A validated multi-year series is unavailable for the comparison country."
        elif not definition_match:
            display_mode = "definition-conflict"
            chart_warning = "Indicator definitions differ; the series are not plotted together."
        elif not unit_match:
            display_mode = "unit-conflict"
            chart_warning = "Units differ; the series are not plotted together."
        elif not source_match:
            display_mode = "source-conflict"
            chart_warning = "Source identifiers or publishers differ; the series are not plotted together."
        elif not common_years:
            display_mode = "no-overlap"
            chart_warning = "The series have no shared reporting year and are not plotted as a synchronized comparison."
        else:
            display_mode = "paired"
            chart_warning = None

        aligned_series = [
            {
                "year": year,
                "primary_value": left_by_year.get(year),
                "comparison_value": right_by_year.get(year),
                "primary_missing": year not in left_by_year,
                "comparison_missing": year not in right_by_year,
            }
            for year in years
        ]

        trends.append(
            {
                "id": indicator_id,
                "key": definition.get("key"),
                "label": definition.get("label"),
                "domain": definition.get("domain"),
                "unit": (left or right or definition).get("unit"),
                "format": (left or right or definition).get("format"),
                "primary_series": left_series,
                "comparison_series": right_series,
                "aligned_series": aligned_series,
                "common_years": common_years,
                "common_year_count": len(common_years),
                "latest_common_year": common_years[-1] if common_years else None,
                "primary_gap_years": [year for year in years if year not in left_by_year],
                "comparison_gap_years": [
                    year for year in years if year not in right_by_year
                ],
                "coverage": {
                    "start_year": years[0] if years else None,
                    "end_year": years[-1] if years else None,
                    "primary_point_count": len(left_series),
                    "comparison_point_count": len(right_series),
                    "common_year_count": len(common_years),
                },
                "chartable": chartable,
                "display_mode": display_mode,
                "unit_match": unit_match,
                "definition_match": definition_match,
                "source_match": source_match,
                "chart_warning": chart_warning,
                "comparison_note": (
                    "Series are synchronized only when indicator definition, unit, source family, and at least one reporting year align."
                ),
                "source_attribution": {
                    "primary": _source_signature(left),
                    "comparison": _source_signature(right),
                },
            }
        )

    return {
        "ok": True,
        "version": VERSION,
        "generated_at": _now(),
        "primary_country": left_payload.get("country"),
        "comparison_country": right_payload.get("country"),
        "trend_count": len(trends),
        "chartable_trend_count": sum(1 for item in trends if item["chartable"]),
        "non_chartable_trend_count": sum(
            1 for item in trends if not item["chartable"]
        ),
        "trends": trends,
    }


def compare_trends(country: str, compare: str) -> dict[str, Any]:
    _, _, left_payload, right_payload = _fetch_country_pair(country, compare)
    return _build_trend_comparison(left_payload, right_payload)


def _unavailable_events(code: str, reason: str) -> dict[str, Any]:
    return {
        "ok": False,
        "version": VERSION,
        "data_state": "temporarily-unavailable",
        "country_code": code,
        "count": 0,
        "events": [],
        "message": "Public event context is temporarily unavailable for this country.",
        "reason": reason,
    }


def _safe_events(code: str, days: int, limit: int) -> dict[str, Any]:
    try:
        payload = unified_events(
            days=days,
            limit=limit,
            country_code=code,
            allow_fallback=False,
        )
        if not isinstance(payload, dict):
            return _unavailable_events(code, "invalid-event-payload")
        payload.setdefault("country_code", code)
        payload.setdefault("events", [])
        payload.setdefault("count", len(payload["events"]))
        payload.setdefault("data_state", "live")
        return payload
    except Exception:
        return _unavailable_events(code, "event-source-error")


def compare_events(
    country: str,
    compare: str,
    days: int = 30,
    limit: int = 20,
) -> dict[str, Any]:
    left_code, right_code = _country_pair(country, compare)
    normalized_days = max(1, min(int(days), 90))
    normalized_limit = max(1, min(int(limit), 100))

    with ThreadPoolExecutor(max_workers=2) as executor:
        left_future = executor.submit(
            _safe_events, left_code, normalized_days, normalized_limit
        )
        right_future = executor.submit(
            _safe_events, right_code, normalized_days, normalized_limit
        )
        left = left_future.result()
        right = right_future.result()

    states = {left.get("data_state"), right.get("data_state")}
    data_state = (
        "live"
        if states == {"live"}
        else "partial"
        if "live" in states
        else "temporarily-unavailable"
    )

    return {
        "ok": True,
        "version": VERSION,
        "generated_at": _now(),
        "data_state": data_state,
        "days": normalized_days,
        "limit": normalized_limit,
        "primary_country": left_code,
        "comparison_country": right_code,
        "primary": left,
        "comparison": right,
        "boundary": "Event counts reflect available public source records and are not measures of total incidence, severity, or risk.",
    }


def _comparison_payload(
    country: str,
    compare: str,
    *,
    include_events: bool,
    days: int,
    limit: int,
) -> dict[str, Any]:
    # Warm the catalog before threaded work to avoid duplicate cold catalog loads.
    country_catalog()

    if include_events:
        with ThreadPoolExecutor(max_workers=2) as executor:
            pair_future = executor.submit(_fetch_country_pair, country, compare)
            event_future = executor.submit(
                compare_events, country, compare, days, limit
            )
            left_code, right_code, left_payload, right_payload = pair_future.result()
            events = event_future.result()
    else:
        left_code, right_code, left_payload, right_payload = _fetch_country_pair(
            country, compare
        )
        events = None

    indicators = _build_indicator_comparison(
        left_code, right_code, left_payload, right_payload
    )
    trends = _build_trend_comparison(left_payload, right_payload)
    left = indicators["primary_country"]
    right = indicators["comparison_country"]

    return {
        "ok": True,
        "version": VERSION,
        "generated_at": _now(),
        "title": f"{left['name']} and {right['name']} — Comparative Intelligence",
        "scope": {
            "primary_country": left,
            "comparison_country": right,
            "country_count": 2,
        },
        "data_state": indicators.get("data_state"),
        "summary": {
            "indicator_count": indicators.get("indicator_count", 0),
            "available_indicator_count": indicators.get(
                "available_indicator_count", 0
            ),
            "complete_indicator_count": indicators.get(
                "complete_indicator_count", 0
            ),
            "partial_indicator_count": indicators.get(
                "partial_indicator_count", 0
            ),
            "aligned_indicator_count": indicators.get(
                "aligned_indicator_count", 0
            ),
            "conflict_count": indicators.get("conflict_count", 0),
            "trend_count": trends.get("trend_count", 0),
            "chartable_trend_count": trends.get("chartable_trend_count", 0),
            "primary_event_count": (events or {}).get("primary", {}).get(
                "count", 0
            ),
            "comparison_event_count": (events or {}).get(
                "comparison", {}
            ).get("count", 0),
            "event_data_state": (events or {}).get("data_state", "not-requested"),
        },
        "indicators": indicators,
        "trends": trends,
        "events": events,
        "routes": {
            "indicators": f"/public/compare/indicators?country={left['code']}&compare={right['code']}",
            "trends": f"/public/compare/trends?country={left['code']}&compare={right['code']}",
            "events": f"/public/compare/events?country={left['code']}&compare={right['code']}",
            "brief": f"/public/compare/brief?country={left['code']}&compare={right['code']}",
            "export": f"/public/compare/export?country={left['code']}&compare={right['code']}",
            "diagnostics": f"/public/compare/diagnostics?country={left['code']}&compare={right['code']}",
        },
        "boundaries": [
            "Comparison organizes public evidence; it does not create a national ranking.",
            "Reporting years, units, source definitions, source families, and delivery states remain visible.",
            "A mathematical difference is calculated only for aligned reporting years and compatible evidence records.",
            "Visual alignment does not establish causality or methodological equivalence.",
        ],
    }


def compare_countries(
    country: str,
    compare: str,
    include_events: bool = True,
    include_brief: bool = False,
    days: int = 30,
    limit: int = 20,
) -> dict[str, Any]:
    payload = _comparison_payload(
        country,
        compare,
        include_events=include_events,
        days=days,
        limit=limit,
    )
    if include_brief:
        payload["brief"] = _brief_from_comparison(payload)
    return payload


def _filter_rows(
    rows: list[dict[str, Any]], indicator: str | None
) -> list[dict[str, Any]]:
    if not indicator:
        return rows
    normalized = str(indicator).strip()
    matches = [row for row in rows if str(row.get("id")) == normalized]
    if not matches:
        raise ComparisonError("unsupported_indicator")
    return matches


def _source_list(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sources: dict[tuple[str, str | None, str | None], dict[str, Any]] = {}
    for row in rows:
        indicator_id = str(row.get("id") or "")
        for side_name in ("primary", "comparison"):
            side = row.get(side_name)
            if not side:
                continue
            name = str(side.get("source") or "Source unavailable")
            url = side.get("source_url")
            source_id = side.get("source_id")
            key = (name, url, source_id)
            entry = sources.setdefault(
                key,
                {
                    "name": name,
                    "url": url,
                    "source_id": source_id,
                    "indicator_ids": [],
                    "sides": [],
                },
            )
            if indicator_id and indicator_id not in entry["indicator_ids"]:
                entry["indicator_ids"].append(indicator_id)
            if side_name not in entry["sides"]:
                entry["sides"].append(side_name)
    return sorted(
        sources.values(),
        key=lambda item: (
            _normalize_text(item["name"]),
            _normalize_text(item.get("source_id")),
        ),
    )


def _brief_from_comparison(
    comparison: dict[str, Any],
    indicator: str | None = None,
) -> dict[str, Any]:
    left = comparison["scope"]["primary_country"]
    right = comparison["scope"]["comparison_country"]
    rows = _filter_rows(comparison["indicators"]["rows"], indicator)

    evidence_lines: list[dict[str, Any]] = []
    caveats: list[str] = []
    data_gaps: list[dict[str, Any]] = []
    for row in rows:
        primary = row.get("primary")
        secondary = row.get("comparison")
        evidence_lines.append(
            {
                "indicator_id": row.get("id"),
                "indicator": row.get("label"),
                "domain": row.get("domain"),
                "primary": primary,
                "comparison": secondary,
                "compatibility": row.get("compatibility"),
                "calculation_eligible": row.get("calculation_eligible"),
                "difference": row.get("absolute_difference"),
                "percent_difference": row.get("percent_difference"),
                "warnings": row.get("warnings") or [],
            }
        )
        caveats.extend(row.get("warnings") or [])
        if row.get("availability") != "both" or row.get("compatibility") != "aligned":
            data_gaps.append(
                {
                    "indicator_id": row.get("id"),
                    "indicator": row.get("label"),
                    "availability": row.get("availability"),
                    "compatibility": row.get("compatibility"),
                    "warnings": row.get("warnings") or [],
                }
            )

    trend_ids = {str(row.get("id")) for row in rows}
    trend_differences = [
        item
        for item in comparison["trends"]["trends"]
        if str(item.get("id")) in trend_ids
    ]

    return {
        "ok": True,
        "version": VERSION,
        "generated_at": comparison.get("generated_at") or _now(),
        "title": f"{left['name']} and {right['name']} — Comparative Intelligence Brief",
        "comparison_scope": {
            "primary_country": left,
            "comparison_country": right,
            "indicator_count": len(rows),
            "indicator_filter": indicator,
        },
        "compatibility_summary": comparison["indicators"].get(
            "compatibility_counts", {}
        ),
        "country_summaries": [
            {
                "country": left,
                "event_count": comparison["summary"]["primary_event_count"],
            },
            {
                "country": right,
                "event_count": comparison["summary"]["comparison_event_count"],
            },
        ],
        "latest_available_indicators": evidence_lines,
        "trend_differences": trend_differences,
        "recent_public_events": comparison.get("events"),
        "data_gaps": data_gaps,
        "methodological_caveats": list(dict.fromkeys(caveats))
        + comparison["boundaries"],
        "source_list": _source_list(rows),
        "boundary": "This brief organizes public evidence for research and orientation. Verify consequential findings against the linked authoritative sources.",
    }


def comparison_brief(
    country: str,
    compare: str,
    indicator: str | None = None,
) -> dict[str, Any]:
    comparison = compare_countries(
        country,
        compare,
        include_events=True,
        include_brief=False,
    )
    return _brief_from_comparison(comparison, indicator=indicator)


def comparison_diagnostics(country: str, compare: str) -> dict[str, Any]:
    comparison = compare_countries(
        country,
        compare,
        include_events=False,
        include_brief=False,
    )
    indicators = comparison["indicators"]
    trends = comparison["trends"]
    issues = [
        {
            "indicator_id": row.get("id"),
            "indicator": row.get("label"),
            "compatibility": row.get("compatibility"),
            "flags": row.get("methodology_flags") or [],
        }
        for row in indicators.get("rows", [])
        if row.get("compatibility") != "aligned"
    ]
    return {
        "ok": True,
        "version": VERSION,
        "generated_at": _now(),
        "pair": comparison["scope"],
        "data_state": comparison.get("data_state"),
        "indicator_count": indicators.get("indicator_count", 0),
        "compatibility_counts": indicators.get("compatibility_counts", {}),
        "calculation_eligible_count": indicators.get(
            "calculation_eligible_count", 0
        ),
        "chartable_trend_count": trends.get("chartable_trend_count", 0),
        "non_chartable_trend_count": trends.get(
            "non_chartable_trend_count", 0
        ),
        "issue_count": len(issues),
        "issues": issues,
        "export_formats": ["json", "csv", "html", "print"],
        "public_safe": True,
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


def comparison_export(
    country: str,
    compare: str,
    export_format: str = "json",
    indicator: str | None = None,
) -> tuple[str, str, str]:
    brief = comparison_brief(country, compare, indicator=indicator)
    fmt = str(export_format or "json").lower().strip()
    left = brief["comparison_scope"]["primary_country"]
    right = brief["comparison_scope"]["comparison_country"]
    indicator_suffix = (
        f"-{re.sub(r'[^A-Za-z0-9._-]+', '-', indicator)}" if indicator else ""
    )
    stem = (
        f"site-intelligence-comparison-{left['code']}-{right['code']}"
        f"{indicator_suffix}"
    )

    if fmt == "json":
        export_payload = {
            **brief,
            "export_manifest": {
                "format": "json",
                "schema_version": VERSION,
                "application_version": VERSION,
                "generated_at": brief["generated_at"],
                "filename": f"{stem}.json",
            },
        }
        return (
            json.dumps(export_payload, indent=2, ensure_ascii=False),
            "application/json",
            f"{stem}.json",
        )

    if fmt == "csv":
        output = StringIO(newline="")
        fieldnames = [
            "indicator_id",
            "indicator",
            "domain",
            "primary_country",
            "primary_value",
            "primary_year",
            "primary_unit",
            "primary_source",
            "primary_source_id",
            "primary_source_url",
            "primary_data_state",
            "comparison_country",
            "comparison_value",
            "comparison_year",
            "comparison_unit",
            "comparison_source",
            "comparison_source_id",
            "comparison_source_url",
            "comparison_data_state",
            "compatibility",
            "calculation_eligible",
            "absolute_difference",
            "percent_difference",
            "warnings",
        ]
        writer = DictWriter(output, fieldnames=fieldnames, lineterminator="\r\n")
        writer.writeheader()
        for item in brief["latest_available_indicators"]:
            primary = item.get("primary") or {}
            secondary = item.get("comparison") or {}
            writer.writerow(
                {
                    "indicator_id": _csv_safe(item.get("indicator_id")),
                    "indicator": _csv_safe(item.get("indicator")),
                    "domain": _csv_safe(item.get("domain")),
                    "primary_country": _csv_safe(left.get("name")),
                    "primary_value": _csv_safe(primary.get("value")),
                    "primary_year": _csv_safe(primary.get("year")),
                    "primary_unit": _csv_safe(primary.get("unit")),
                    "primary_source": _csv_safe(primary.get("source")),
                    "primary_source_id": _csv_safe(primary.get("source_id")),
                    "primary_source_url": _csv_safe(primary.get("source_url")),
                    "primary_data_state": _csv_safe(primary.get("data_state")),
                    "comparison_country": _csv_safe(right.get("name")),
                    "comparison_value": _csv_safe(secondary.get("value")),
                    "comparison_year": _csv_safe(secondary.get("year")),
                    "comparison_unit": _csv_safe(secondary.get("unit")),
                    "comparison_source": _csv_safe(secondary.get("source")),
                    "comparison_source_id": _csv_safe(secondary.get("source_id")),
                    "comparison_source_url": _csv_safe(secondary.get("source_url")),
                    "comparison_data_state": _csv_safe(secondary.get("data_state")),
                    "compatibility": _csv_safe(item.get("compatibility")),
                    "calculation_eligible": _csv_safe(
                        item.get("calculation_eligible")
                    ),
                    "absolute_difference": _csv_safe(item.get("difference")),
                    "percent_difference": _csv_safe(
                        item.get("percent_difference")
                    ),
                    "warnings": _csv_safe(" | ".join(item.get("warnings") or [])),
                }
            )
        return "\ufeff" + output.getvalue(), "text/csv", f"{stem}.csv"

    if fmt in {"html", "print"}:
        rows: list[str] = []
        for item in brief["latest_available_indicators"]:
            primary = item.get("primary") or {}
            secondary = item.get("comparison") or {}
            warnings = "<br>".join(
                _html(message) for message in item.get("warnings") or []
            ) or "None"
            rows.append(
                "<tr>"
                f"<td><strong>{_html(item.get('indicator'))}</strong><br><small>{_html(item.get('indicator_id'))}</small></td>"
                f"<td>{_html_value(primary)}{_html_source(primary)}</td>"
                f"<td>{_html_value(secondary)}{_html_source(secondary)}</td>"
                f"<td>{_html(item.get('compatibility'))}<br><small>{warnings}</small></td>"
                "</tr>"
            )

        source_items = "".join(
            "<li>"
            + (
                f'<a href="{_html(source.get("url"))}">{_html(source.get("name"))}</a>'
                if source.get("url")
                else _html(source.get("name"))
            )
            + (
                f" — {_html(source.get('source_id'))}"
                if source.get("source_id")
                else ""
            )
            + "</li>"
            for source in brief.get("source_list", [])
        ) or "<li>No source records were available.</li>"

        caveats = "".join(
            f"<li>{_html(item)}</li>"
            for item in brief.get("methodological_caveats", [])
        )

        html_document = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_html(brief['title'])}</title>
<style>
body{{font-family:Arial,sans-serif;max-width:1080px;margin:40px auto;padding:0 22px;color:#171717;line-height:1.55}}
h1{{font-size:2rem;margin-bottom:6px}}.meta{{color:#555}}table{{width:100%;border-collapse:collapse;margin:24px 0}}
th,td{{padding:10px;border:1px solid #bbb;text-align:left;vertical-align:top}}th{{background:#f2f2f2}}small{{color:#555}}.note{{padding:14px;border-left:4px solid #9b1111;background:#f7f3ea}}a{{color:#6d0d0d}}@media print{{body{{margin:0;max-width:none}}a{{color:#111;text-decoration:none}}a[href]::after{{content:" (" attr(href) ")";font-size:9px}}}}
</style></head><body>
<h1>{_html(brief['title'])}</h1>
<p class="meta">Generated {_html(brief['generated_at'])} · Site Intelligence v{_html(VERSION)}</p>
<table><thead><tr><th>Indicator</th><th>{_html(left['name'])}</th><th>{_html(right['name'])}</th><th>Compatibility and cautions</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
<h2>Sources</h2><ul>{source_items}</ul>
<h2>Methodological cautions</h2><ul>{caveats}</ul>
<p class="note">{_html(brief['boundary'])}</p>
</body></html>"""
        return html_document, "text/html", f"{stem}.html"

    raise ComparisonError("unsupported_export_format")


def _html(value: Any) -> str:
    import html

    if value is None or value == "":
        return "Unavailable"
    return html.escape(str(value), quote=True)


def _html_value(record: dict[str, Any]) -> str:
    if not record:
        return "No validated public value is currently available.<br>"
    return (
        f"{_html(record.get('value'))} {_html(record.get('unit'))}"
        f"<br><small>{_html(record.get('year'))} · {_html(record.get('data_state'))}</small><br>"
    )


def _html_source(record: dict[str, Any]) -> str:
    if not record:
        return ""
    name = _html(record.get("source"))
    source_id = _html(record.get("source_id"))
    url = record.get("source_url")
    source = f'<a href="{_html(url)}">{name}</a>' if url else name
    return f"<small>{source} · {source_id}</small>"
