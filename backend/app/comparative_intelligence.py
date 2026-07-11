from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from csv import DictWriter
from datetime import datetime, timezone
from io import StringIO
from typing import Any

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


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean_code(value: str) -> str:
    code = "".join(ch for ch in str(value or "").upper() if ch.isalpha())
    if len(code) not in {2, 3}:
        raise ValueError("unsupported_country")
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
        raise ValueError("unsupported_country")
    return str(match["code"])


def _indicator_map(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(item.get("id")): item for item in payload.get("indicators", []) if item.get("id")}


def _latest_record(item: dict[str, Any] | None) -> dict[str, Any] | None:
    if not item:
        return None
    latest = item.get("latest")
    if not isinstance(latest, dict) or latest.get("value") is None:
        return None
    return {
        "value": latest.get("value"),
        "year": latest.get("year"),
        "unit": item.get("unit"),
        "format": item.get("format"),
        "source": item.get("source"),
        "source_id": item.get("source_id"),
        "source_url": item.get("source_url"),
        "data_state": item.get("data_state", "unavailable"),
        "cache_state": item.get("cache_state"),
        "retrieved_at": item.get("retrieved_at"),
        "stale": bool(item.get("stale")),
    }


def _numeric(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _comparison_row(
    definition: dict[str, Any],
    left_item: dict[str, Any] | None,
    right_item: dict[str, Any] | None,
    left_code: str,
    right_code: str,
) -> dict[str, Any]:
    left = _latest_record(left_item)
    right = _latest_record(right_item)

    unit_left = left.get("unit") if left else (left_item or {}).get("unit")
    unit_right = right.get("unit") if right else (right_item or {}).get("unit")
    unit_match = bool(unit_left and unit_right and unit_left == unit_right)
    definition_match = bool(
        left_item
        and right_item
        and left_item.get("id") == right_item.get("id") == definition.get("id")
    )
    both_available = bool(left and right)
    explicitly_labeled = bool(
        left
        and right
        and left.get("data_state") in VALID_VALUE_STATES
        and right.get("data_state") in VALID_VALUE_STATES
    )
    comparable = bool(both_available and explicitly_labeled and unit_match and definition_match)

    left_year = left.get("year") if left else None
    right_year = right.get("year") if right else None
    years_match = bool(left_year is not None and right_year is not None and left_year == right_year)

    warnings: list[str] = []
    if not both_available:
        warnings.append("No validated public value is currently available for one or both countries.")
    if both_available and not unit_match:
        warnings.append("Units differ; values are displayed but no mathematical difference is calculated.")
    if both_available and not definition_match:
        warnings.append("Indicator definitions differ and are not methodologically equivalent.")
    if both_available and left_year != right_year:
        warnings.append(
            f"Reporting years differ: {left_code} {left_year or 'unavailable'}, "
            f"{right_code} {right_year or 'unavailable'}."
        )
    if left and left.get("data_state") == "reference-snapshot":
        warnings.append(f"{left_code} uses a labeled reference snapshot.")
    if right and right.get("data_state") == "reference-snapshot":
        warnings.append(f"{right_code} uses a labeled reference snapshot.")

    absolute_difference = None
    percent_difference = None
    if comparable:
        left_number = _numeric(left.get("value"))
        right_number = _numeric(right.get("value"))
        if left_number is not None and right_number is not None:
            absolute_difference = right_number - left_number
            if left_number != 0:
                percent_difference = ((right_number - left_number) / abs(left_number)) * 100

    if comparable and years_match:
        compatibility = "aligned"
    elif comparable:
        compatibility = "different-reporting-years"
    elif both_available:
        compatibility = "display-only"
    else:
        compatibility = "unavailable"

    return {
        "id": definition.get("id"),
        "key": definition.get("key"),
        "label": definition.get("label"),
        "domain": definition.get("domain"),
        "unit": unit_left or unit_right or definition.get("unit"),
        "format": definition.get("format"),
        "primary": left,
        "comparison": right,
        "compatibility": compatibility,
        "comparable": comparable,
        "reporting_years_match": years_match,
        "unit_match": unit_match,
        "definition_match": definition_match,
        "absolute_difference": absolute_difference,
        "percent_difference": percent_difference,
        "warnings": warnings,
    }


def compare_indicators(country: str, compare: str) -> dict[str, Any]:
    left_code = _clean_code(country)
    right_code = _clean_code(compare)
    if left_code == right_code:
        raise ValueError("duplicate_country")

    with ThreadPoolExecutor(max_workers=2) as executor:
        left_future = executor.submit(country_indicators, left_code)
        right_future = executor.submit(country_indicators, right_code)
        left_payload = left_future.result()
        right_payload = right_future.result()
    left_map = _indicator_map(left_payload)
    right_map = _indicator_map(right_payload)

    definitions: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in [*left_payload.get("indicators", []), *right_payload.get("indicators", [])]:
        indicator_id = str(item.get("id") or "")
        if not indicator_id or indicator_id in seen:
            continue
        seen.add(indicator_id)
        definitions.append(item)

    rows = [
        _comparison_row(definition, left_map.get(str(definition.get("id"))), right_map.get(str(definition.get("id"))), left_code, right_code)
        for definition in definitions
    ]

    aligned_count = sum(1 for row in rows if row["compatibility"] == "aligned")
    available_count = sum(1 for row in rows if row["primary"] or row["comparison"])
    data_state = "live" if left_payload.get("data_state") == right_payload.get("data_state") == "live" else "mixed"

    return {
        "ok": True,
        "version": VERSION,
        "generated_at": _now(),
        "data_state": data_state,
        "primary_country": left_payload.get("country"),
        "comparison_country": right_payload.get("country"),
        "indicator_count": len(rows),
        "available_indicator_count": available_count,
        "aligned_indicator_count": aligned_count,
        "rows": rows,
        "methodology": [
            "Indicator IDs and units must match before a mathematical difference is calculated.",
            "Reporting years remain visible and differences in year are explicitly labeled.",
            "Reference snapshots, cached values, stale values, and missing records remain labeled.",
            "No proprietary composite score or unexplained country ranking is produced.",
        ],
    }


def compare_trends(country: str, compare: str) -> dict[str, Any]:
    left_code = _clean_code(country)
    right_code = _clean_code(compare)
    if left_code == right_code:
        raise ValueError("duplicate_country")

    with ThreadPoolExecutor(max_workers=2) as executor:
        left_future = executor.submit(country_trends, left_code)
        right_future = executor.submit(country_trends, right_code)
        left_payload = left_future.result()
        right_payload = right_future.result()
    left_map = {str(item.get("id")): item for item in left_payload.get("trends", [])}
    right_map = {str(item.get("id")): item for item in right_payload.get("trends", [])}
    ids = list(dict.fromkeys([*left_map.keys(), *right_map.keys()]))

    trends = []
    for indicator_id in ids:
        left = left_map.get(indicator_id)
        right = right_map.get(indicator_id)
        definition = left or right or {}
        left_series = list((left or {}).get("series") or [])
        right_series = list((right or {}).get("series") or [])
        left_years = {item.get("year") for item in left_series}
        right_years = {item.get("year") for item in right_series}
        common_years = sorted(year for year in left_years.intersection(right_years) if year is not None)
        trends.append({
            "id": indicator_id,
            "key": definition.get("key"),
            "label": definition.get("label"),
            "unit": definition.get("unit"),
            "format": definition.get("format"),
            "primary_series": left_series,
            "comparison_series": right_series,
            "common_years": common_years,
            "common_year_count": len(common_years),
            "comparison_note": "Series are shown on the same chart only when the indicator ID and unit match.",
        })

    return {
        "ok": True,
        "version": VERSION,
        "generated_at": _now(),
        "primary_country": left_payload.get("country"),
        "comparison_country": right_payload.get("country"),
        "trend_count": len(trends),
        "trends": trends,
    }


def compare_events(country: str, compare: str, days: int = 30, limit: int = 20) -> dict[str, Any]:
    left_code = _clean_code(country)
    right_code = _clean_code(compare)
    if left_code == right_code:
        raise ValueError("duplicate_country")

    normalized_days = max(1, min(int(days), 90))
    normalized_limit = max(1, min(int(limit), 100))
    left = unified_events(days=normalized_days, limit=normalized_limit, country_code=left_code, allow_fallback=False)
    right = unified_events(days=normalized_days, limit=normalized_limit, country_code=right_code, allow_fallback=False)

    return {
        "ok": True,
        "version": VERSION,
        "generated_at": _now(),
        "days": normalized_days,
        "primary_country": left_code,
        "comparison_country": right_code,
        "primary": left,
        "comparison": right,
        "boundary": "Event counts reflect available public source records and are not measures of total incidence, severity, or risk.",
    }


def compare_countries(country: str, compare: str, include_events: bool = True) -> dict[str, Any]:
    # Warm the shared country catalog before parallel work so a cold direct API
    # request cannot start duplicate World Bank catalog fetches in two threads.
    country_catalog()
    # Indicator retrieval and optional event retrieval are independent. Run
    # them together so a temporarily unavailable optional event feed does not
    # add its full timeout after country indicators have already loaded.
    if include_events:
        with ThreadPoolExecutor(max_workers=2) as executor:
            indicator_future = executor.submit(compare_indicators, country, compare)
            event_future = executor.submit(compare_events, country, compare)
            indicators = indicator_future.result()
            events = event_future.result()
    else:
        indicators = compare_indicators(country, compare)
        events = None
    trends = compare_trends(country, compare)
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
            "available_indicator_count": indicators.get("available_indicator_count", 0),
            "aligned_indicator_count": indicators.get("aligned_indicator_count", 0),
            "trend_count": trends.get("trend_count", 0),
            "primary_event_count": (events or {}).get("primary", {}).get("count", 0),
            "comparison_event_count": (events or {}).get("comparison", {}).get("count", 0),
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
        },
        "boundaries": [
            "Comparison organizes public evidence; it does not create a national ranking.",
            "Reporting years, units, source definitions, and delivery states remain visible.",
            "Visual alignment does not establish causality or methodological equivalence.",
        ],
    }


def comparison_brief(country: str, compare: str) -> dict[str, Any]:
    comparison = compare_countries(country, compare, include_events=True)
    left = comparison["scope"]["primary_country"]
    right = comparison["scope"]["comparison_country"]
    rows = comparison["indicators"]["rows"]

    evidence_lines = []
    caveats: list[str] = []
    for row in rows:
        primary = row.get("primary")
        secondary = row.get("comparison")
        if primary or secondary:
            evidence_lines.append({
                "indicator": row.get("label"),
                "primary": primary,
                "comparison": secondary,
                "compatibility": row.get("compatibility"),
                "difference": row.get("absolute_difference"),
                "percent_difference": row.get("percent_difference"),
            })
        caveats.extend(row.get("warnings") or [])

    return {
        "ok": True,
        "version": VERSION,
        "generated_at": _now(),
        "title": f"{left['name']} and {right['name']} — Comparative Intelligence Brief",
        "comparison_scope": {
            "primary_country": left,
            "comparison_country": right,
            "indicator_count": comparison["summary"]["indicator_count"],
        },
        "country_summaries": [
            {"country": left, "event_count": comparison["summary"]["primary_event_count"]},
            {"country": right, "event_count": comparison["summary"]["comparison_event_count"]},
        ],
        "latest_available_indicators": evidence_lines,
        "trend_differences": comparison["trends"]["trends"],
        "recent_public_events": comparison["events"],
        "methodological_caveats": list(dict.fromkeys(caveats)) + comparison["boundaries"],
        "source_list": _source_list(rows),
        "boundary": "This brief organizes public evidence for research and orientation. Verify consequential findings against the linked authoritative sources.",
    }


def _source_list(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sources: dict[tuple[str, str | None], dict[str, Any]] = {}
    for row in rows:
        for side in (row.get("primary"), row.get("comparison")):
            if not side:
                continue
            name = str(side.get("source") or "Source unavailable")
            url = side.get("source_url")
            sources[(name, url)] = {"name": name, "url": url}
    return sorted(sources.values(), key=lambda item: item["name"])


def comparison_export(country: str, compare: str, export_format: str = "json") -> tuple[str, str, str]:
    brief = comparison_brief(country, compare)
    fmt = str(export_format or "json").lower()
    left = brief["comparison_scope"]["primary_country"]["code"]
    right = brief["comparison_scope"]["comparison_country"]["code"]
    stem = f"site-intelligence-comparison-{left}-{right}"

    if fmt == "json":
        import json
        return json.dumps(brief, indent=2, ensure_ascii=False), "application/json", f"{stem}.json"

    if fmt == "csv":
        output = StringIO()
        writer = DictWriter(output, fieldnames=[
            "indicator", "primary_value", "primary_year", "comparison_value", "comparison_year",
            "unit", "compatibility", "absolute_difference", "percent_difference",
        ])
        writer.writeheader()
        for item in brief["latest_available_indicators"]:
            primary = item.get("primary") or {}
            secondary = item.get("comparison") or {}
            writer.writerow({
                "indicator": item.get("indicator"),
                "primary_value": primary.get("value"),
                "primary_year": primary.get("year"),
                "comparison_value": secondary.get("value"),
                "comparison_year": secondary.get("year"),
                "unit": primary.get("unit") or secondary.get("unit"),
                "compatibility": item.get("compatibility"),
                "absolute_difference": item.get("difference"),
                "percent_difference": item.get("percent_difference"),
            })
        return output.getvalue(), "text/csv", f"{stem}.csv"

    if fmt in {"html", "print"}:
        rows = []
        for item in brief["latest_available_indicators"]:
            primary = item.get("primary") or {}
            secondary = item.get("comparison") or {}
            rows.append(
                "<tr>"
                f"<td>{_html(item.get('indicator'))}</td>"
                f"<td>{_html(primary.get('value'))} {_html(primary.get('unit'))}<br><small>{_html(primary.get('year'))}</small></td>"
                f"<td>{_html(secondary.get('value'))} {_html(secondary.get('unit'))}<br><small>{_html(secondary.get('year'))}</small></td>"
                f"<td>{_html(item.get('compatibility'))}</td>"
                "</tr>"
            )
        html = f"""<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><title>{_html(brief['title'])}</title>
<style>body{{font-family:Arial,sans-serif;max-width:980px;margin:40px auto;padding:0 20px;color:#171717}}h1{{font-size:2rem}}table{{width:100%;border-collapse:collapse}}th,td{{padding:10px;border:1px solid #ccc;text-align:left;vertical-align:top}}small{{color:#555}}.note{{padding:14px;border-left:4px solid #9b1111;background:#f7f3ea}}</style></head><body>
<h1>{_html(brief['title'])}</h1><p>Generated {_html(brief['generated_at'])}</p><table><thead><tr><th>Indicator</th><th>{_html(brief['comparison_scope']['primary_country']['name'])}</th><th>{_html(brief['comparison_scope']['comparison_country']['name'])}</th><th>Compatibility</th></tr></thead><tbody>{''.join(rows)}</tbody></table><p class=\"note\">{_html(brief['boundary'])}</p></body></html>"""
        return html, "text/html", f"{stem}.html"

    raise ValueError("unsupported_export_format")


def _html(value: Any) -> str:
    import html
    if value is None:
        return "Unavailable"
    return html.escape(str(value))
