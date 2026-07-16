"""Comparative Intelligence and Scenario Studio for Site Intelligence v2.9.0.

The studio aligns published public records for transparent comparison. Scenario
operations are user-defined arithmetic transformations over compatible baseline
records; they are not forecasts, probabilities, recommendations, or causal models.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
import os
import re
from typing import Any, Iterable, Mapping, Sequence

VERSION = "2.9.0"
RELEASE_SCHEMA = "sc-site-intelligence-comparative-scenario-studio/1.0"
COMPARISON_SCHEMA = "sc-site-intelligence-comparison-matrix/1.0"
SCENARIO_SCHEMA = "sc-site-intelligence-transparent-scenario/1.0"
CORRELATION_SCHEMA = "sc-site-intelligence-correlation-review/1.0"
PACKET_SCHEMA = "sc-site-intelligence-comparison-packet/1.0"
MAX_GEOGRAPHIES = 6
MAX_INDICATORS = 16
MAX_RECORDS = 500


@dataclass(frozen=True)
class StudioConfig:
    enabled: bool
    max_geographies: int
    max_indicators: int
    max_records: int


def _as_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on", "enabled"}


def studio_config(settings: Any = None) -> StudioConfig:
    enabled = getattr(settings, "comparative_scenario_studio_enabled", None)
    geographies = getattr(settings, "comparative_scenario_max_geographies", None)
    indicators = getattr(settings, "comparative_scenario_max_indicators", None)
    records = getattr(settings, "comparative_scenario_max_records", None)
    if enabled is None:
        enabled = os.getenv("SC_SI_COMPARATIVE_SCENARIO_STUDIO_ENABLED", "true")
    if geographies is None:
        geographies = os.getenv("SC_SI_COMPARATIVE_SCENARIO_MAX_GEOGRAPHIES", "5")
    if indicators is None:
        indicators = os.getenv("SC_SI_COMPARATIVE_SCENARIO_MAX_INDICATORS", "12")
    if records is None:
        records = os.getenv("SC_SI_COMPARATIVE_SCENARIO_MAX_RECORDS", "400")
    return StudioConfig(
        enabled=_as_bool(enabled, True),
        max_geographies=max(2, min(int(geographies), MAX_GEOGRAPHIES)),
        max_indicators=max(1, min(int(indicators), MAX_INDICATORS)),
        max_records=max(50, min(int(records), MAX_RECORDS)),
    )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any, limit: int = 500) -> str:
    if value is None:
        return ""
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", str(value)).strip()[:limit]


def _safe_url(value: Any) -> str:
    text = _safe_text(value, 1200)
    if not text.lower().startswith(("https://", "http://")):
        return ""
    if re.search(r"(?:api[_-]?key|access[_-]?token|token|authorization)=", text, flags=re.I):
        return text.split("?", 1)[0]
    return text


def _codes(value: Any, *, limit: int) -> list[str]:
    if isinstance(value, str):
        values = re.split(r"[,\s]+", value)
    elif isinstance(value, Sequence):
        values = list(value)
    else:
        values = []
    result: list[str] = []
    for raw in values:
        code = _safe_text(raw, 80).upper()
        if code and code not in result:
            result.append(code)
    return result[:limit]


def _indicator_codes(value: Any, *, limit: int) -> list[str]:
    if isinstance(value, str):
        values = [item.strip() for item in value.split(",")]
    elif isinstance(value, Sequence):
        values = list(value)
    else:
        values = []
    result: list[str] = []
    for raw in values:
        code = _safe_text(raw, 160)
        if code and code not in result:
            result.append(code)
    return result[:limit]


def _period_key(record: Mapping[str, Any]) -> tuple[str, str]:
    return (
        _safe_text(record.get("period_start") or record.get("period") or record.get("observed_at"), 80),
        _safe_text(record.get("published_at") or record.get("updated_at"), 80),
    )


def _public_record(record: Mapping[str, Any], domain: str = "economics") -> dict[str, Any]:
    value = record.get("value_number")
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value)):
        value = None
    return {
        "id": _safe_text(record.get("id") or record.get("record_id"), 180),
        "domain": _safe_text(record.get("family") or domain, 80).lower() or domain,
        "record_type": _safe_text(record.get("record_type"), 100),
        "indicator_code": _safe_text(record.get("indicator_code") or record.get("metric"), 160),
        "indicator_name": _safe_text(record.get("indicator_name") or record.get("title") or record.get("metric"), 300),
        "geography_code": _safe_text(record.get("geography_code") or record.get("reporting_geography_code") or record.get("country_code"), 20).upper(),
        "geography_name": _safe_text(record.get("geography_name") or record.get("reporting_geography_name") or record.get("country"), 160),
        "counterpart_code": _safe_text(record.get("counterpart_code"), 20).upper(),
        "period": _safe_text(record.get("period") or record.get("period_start") or record.get("year"), 80),
        "period_start": _safe_text(record.get("period_start"), 80),
        "value_number": float(value) if value is not None else None,
        "value_text": _safe_text(record.get("value_text"), 240),
        "unit": _safe_text(record.get("unit"), 120),
        "frequency": _safe_text(record.get("frequency"), 80).upper(),
        "price_basis": _safe_text(record.get("price_basis"), 160),
        "seasonal_adjustment": _safe_text(record.get("seasonal_adjustment"), 160),
        "source_id": _safe_text(record.get("source_id"), 160),
        "source_url": _safe_url(record.get("source_url")),
        "data_status": _safe_text(record.get("data_status") or record.get("quality_status") or record.get("freshness_status"), 100),
        "published_at": _safe_text(record.get("published_at"), 80),
    }


def _collect_records(settings: Any, *, geographies: list[str], indicators: list[str], domains: list[str], start: str, end: str, limit: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    from .economics_markets_sustainability import build_economic_records
    from .trade_energy_resource_security_observatory import build_records as build_resource_records

    records: list[dict[str, Any]] = []
    integrations: list[dict[str, Any]] = []
    per_query = max(30, min(limit, MAX_RECORDS))
    use_economics = not domains or any(item in {"economics", "macroeconomics", "labour", "finance", "demographics", "sustainability"} for item in domains)
    use_resources = not domains or any(item in {"trade", "energy", "food-agriculture", "water", "materials", "supply-chain", "climate-transition", "resources"} for item in domains)

    for geography in geographies:
        if use_economics:
            payload = build_economic_records(settings, geography_code=geography, start=start, end=end, limit=per_query)
            integrations.append(dict(payload.get("integration") or {}))
            records.extend(_public_record(item, "economics") for item in payload.get("records", []) if isinstance(item, Mapping))
        if use_resources:
            payload = build_resource_records(settings, geography_code=geography, start=start, end=end, limit=per_query)
            integrations.append(dict(payload.get("integration") or {}))
            records.extend(_public_record(item, "resources") for item in payload.get("records", []) if isinstance(item, Mapping))

    if indicators:
        indicator_set = {item.lower() for item in indicators}
        records = [item for item in records if item["indicator_code"].lower() in indicator_set or item["indicator_name"].lower() in indicator_set]
    if domains:
        domain_set = {item.lower() for item in domains}
        records = [item for item in records if item["domain"] in domain_set or ("resources" in domain_set and item["domain"] != "economics")]

    deduped: dict[str, dict[str, Any]] = {}
    for item in records:
        digest = hashlib.sha256(json.dumps(item, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        deduped[digest] = item
    return list(deduped.values())[:limit], integrations


def _integration_state(config: StudioConfig, integrations: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    if not config.enabled:
        return {"state": "disabled", "message": "The comparative scenario studio is disabled.", "credential_exposed": False}
    states = [_safe_text(item.get("state"), 80) for item in integrations if item]
    if "connected" in states:
        state = "connected"
        message = "Public comparison records are available through existing Site Intelligence observatories."
    elif states:
        state = next((item for item in states if item not in {"", "connected"}), "unavailable")
        message = "One or more public evidence services are unavailable or degraded."
    else:
        state = "unavailable"
        message = "No public comparison records were returned."
    return {"state": state, "message": message, "credential_exposed": False}


def _compatibility_signature(record: Mapping[str, Any]) -> dict[str, str]:
    return {
        "indicator_code": _safe_text(record.get("indicator_code"), 160),
        "unit": _safe_text(record.get("unit"), 120),
        "frequency": _safe_text(record.get("frequency"), 80),
        "price_basis": _safe_text(record.get("price_basis"), 160),
        "seasonal_adjustment": _safe_text(record.get("seasonal_adjustment"), 160),
        "source_id": _safe_text(record.get("source_id"), 160),
    }


def _compatibility(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    fields = ["unit", "frequency", "price_basis", "seasonal_adjustment"]
    warnings: list[str] = []
    for field in fields:
        values = sorted({_safe_text(item.get(field), 160) for item in records if _safe_text(item.get(field), 160)})
        if len(values) > 1:
            warnings.append(f"Multiple {field.replace('_', ' ')} values are present: {', '.join(values[:8])}.")
    sources = sorted({_safe_text(item.get("source_id"), 160) for item in records if item.get("source_id")})
    periods = sorted({_safe_text(item.get("period"), 80) for item in records if item.get("period")})
    return {
        "compatible_for_direct_difference": not warnings,
        "warnings": warnings,
        "sources": sources,
        "periods": periods,
        "silent_normalization": False,
    }


def build_studio_overview(settings: Any = None) -> dict[str, Any]:
    config = studio_config(settings)
    return {
        "ok": True,
        "schema": RELEASE_SCHEMA,
        "version": VERSION,
        "release_name": "Comparative Intelligence and Scenario Studio",
        "generated_at": _now(),
        "integration": _integration_state(config, []),
        "limits": {"geographies": config.max_geographies, "indicators": config.max_indicators, "records": config.max_records},
        "capabilities": ["multi-geography comparison", "indicator baskets", "regional peers", "transparent scenarios", "correlation review", "reproducible packets"],
        "methodology": {
            "silent_normalization": False,
            "forecasting": False,
            "causal_inference": False,
            "composite_score": False,
            "scenario_definition": "User-defined arithmetic transformation of published baseline values.",
        },
    }


def build_studio_facets(settings: Any = None, *, limit: int = 400) -> dict[str, Any]:
    from .economics_markets_sustainability import build_economic_facets
    from .trade_energy_resource_security_observatory import build_facets as build_resource_facets
    from .live_country_intelligence import country_catalog

    economics = build_economic_facets(settings)
    resources = build_resource_facets(settings)
    countries = country_catalog().get("countries", [])
    indicators: dict[str, dict[str, Any]] = {}
    for item in economics.get("indicators", []):
        code = _safe_text(item.get("code"), 160)
        if code:
            indicators[code] = {"code": code, "name": _safe_text(item.get("name"), 300), "unit": _safe_text(item.get("unit"), 120), "domain": _safe_text(item.get("family"), 80) or "economics"}
    for item in resources.get("indicators", []):
        code = _safe_text(item.get("id"), 160)
        if code and code not in indicators:
            indicators[code] = {"code": code, "name": code, "unit": "", "domain": "resources"}
    regions = Counter(_safe_text(item.get("region"), 160) for item in countries if item.get("region"))
    return {
        "ok": True,
        "schema": RELEASE_SCHEMA,
        "version": VERSION,
        "indicators": sorted(indicators.values(), key=lambda item: (item["name"].lower(), item["code"]))[:limit],
        "geographies": [{"code": _safe_text(item.get("code"), 20), "name": _safe_text(item.get("name"), 160), "region": _safe_text(item.get("region"), 160)} for item in countries[:limit]],
        "regions": [{"id": key, "count": count} for key, count in sorted(regions.items()) if key],
        "domains": ["economics", "macroeconomics", "labour", "finance", "demographics", "sustainability", "trade", "energy", "food-agriculture", "water", "materials", "supply-chain", "climate-transition"],
    }


def build_comparison_matrix(settings: Any = None, *, geographies: Any, indicators: Any = None, domains: Any = None, start: str = "", end: str = "", limit: int = 400) -> dict[str, Any]:
    config = studio_config(settings)
    geography_codes = _codes(geographies, limit=config.max_geographies)
    indicator_codes = _indicator_codes(indicators, limit=config.max_indicators)
    domain_codes = [item.lower() for item in _indicator_codes(domains, limit=20)]
    if len(geography_codes) < 2:
        raise ValueError("Choose at least two different geographies.")
    if len(set(geography_codes)) != len(geography_codes):
        raise ValueError("Duplicate geographies are not allowed.")
    records, integrations = _collect_records(settings, geographies=geography_codes, indicators=indicator_codes, domains=domain_codes, start=start, end=end, limit=min(limit, config.max_records))
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        key = record["indicator_code"] or record["indicator_name"]
        if key:
            grouped[key].append(record)
    rows: list[dict[str, Any]] = []
    for indicator, items in grouped.items():
        latest: dict[str, dict[str, Any]] = {}
        for geography in geography_codes:
            candidates = [item for item in items if item["geography_code"] == geography]
            if candidates:
                latest[geography] = sorted(candidates, key=_period_key)[-1]
        compatibility = _compatibility(list(latest.values()))
        values = {code: latest.get(code) for code in geography_codes}
        rows.append({
            "indicator_code": indicator,
            "indicator_name": next((item["indicator_name"] for item in items if item["indicator_name"]), indicator),
            "domain": next((item["domain"] for item in items if item["domain"]), "economics"),
            "values": values,
            "coverage": sum(1 for value in values.values() if value),
            "compatibility": compatibility,
        })
    rows.sort(key=lambda item: (-item["coverage"], item["indicator_name"].lower()))
    return {
        "ok": True,
        "schema": COMPARISON_SCHEMA,
        "version": VERSION,
        "generated_at": _now(),
        "integration": _integration_state(config, integrations),
        "geographies": geography_codes,
        "indicators_requested": indicator_codes,
        "domains": domain_codes,
        "rows": rows[:config.max_indicators],
        "record_count": len(records),
        "methodology": {
            "silent_normalization": False,
            "withheld_when_incompatible": True,
            "latest_value_selection": "Latest published record per geography within the selected filters.",
            "ranking_created": False,
        },
    }


def build_peer_group(settings: Any = None, *, geography: str, region: str = "") -> dict[str, Any]:
    from .live_country_intelligence import country_catalog
    code = _codes([geography], limit=1)
    if not code:
        raise ValueError("A geography is required.")
    countries = country_catalog().get("countries", [])
    subject = next((item for item in countries if _safe_text(item.get("code"), 20).upper() == code[0]), None)
    if not subject:
        raise ValueError("Unsupported geography.")
    selected_region = _safe_text(region or subject.get("region"), 160)
    peers = [{"code": _safe_text(item.get("code"), 20), "name": _safe_text(item.get("name"), 160), "region": _safe_text(item.get("region"), 160)} for item in countries if _safe_text(item.get("region"), 160) == selected_region and _safe_text(item.get("code"), 20).upper() != code[0]]
    return {
        "ok": True,
        "schema": RELEASE_SCHEMA,
        "version": VERSION,
        "subject": {"code": code[0], "name": _safe_text(subject.get("name"), 160), "region": selected_region},
        "peers": peers,
        "methodology": {"membership_basis": "Site Intelligence normalized country catalog region label", "ranking_created": False, "political_membership_claim": False},
    }


def _adjustment_map(adjustments: Any) -> list[dict[str, Any]]:
    if not isinstance(adjustments, list):
        return []
    output = []
    for item in adjustments[:40]:
        if not isinstance(item, Mapping):
            continue
        mode = _safe_text(item.get("mode"), 30).lower()
        if mode not in {"percent", "absolute"}:
            continue
        try:
            amount = float(item.get("value"))
        except (TypeError, ValueError):
            continue
        if not math.isfinite(amount) or abs(amount) > 1_000_000_000:
            continue
        output.append({
            "indicator_code": _safe_text(item.get("indicator_code"), 160),
            "geography_code": _safe_text(item.get("geography_code"), 20).upper(),
            "mode": mode,
            "value": amount,
            "label": _safe_text(item.get("label"), 200),
        })
    return output


def build_transparent_scenario(settings: Any = None, *, geographies: Any, indicators: Any, adjustments: Any, domains: Any = None, start: str = "", end: str = "") -> dict[str, Any]:
    matrix = build_comparison_matrix(settings, geographies=geographies, indicators=indicators, domains=domains, start=start, end=end)
    rules = _adjustment_map(adjustments)
    results: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for row in matrix["rows"]:
        for geography, record in row["values"].items():
            if not record or record.get("value_number") is None:
                continue
            matching = [rule for rule in rules if (not rule["indicator_code"] or rule["indicator_code"].lower() == row["indicator_code"].lower()) and (not rule["geography_code"] or rule["geography_code"] == geography)]
            if not matching:
                continue
            if not row["compatibility"]["compatible_for_direct_difference"]:
                skipped.append({"indicator_code": row["indicator_code"], "geography_code": geography, "reason": "incompatible comparison signature", "warnings": row["compatibility"]["warnings"]})
                continue
            baseline = float(record["value_number"])
            scenario = baseline
            applied = []
            for rule in matching:
                scenario = scenario * (1 + rule["value"] / 100.0) if rule["mode"] == "percent" else scenario + rule["value"]
                applied.append(rule)
            results.append({
                "indicator_code": row["indicator_code"],
                "indicator_name": row["indicator_name"],
                "geography_code": geography,
                "period": record.get("period"),
                "unit": record.get("unit"),
                "baseline": baseline,
                "scenario": scenario,
                "difference": scenario - baseline,
                "percent_difference": ((scenario - baseline) / baseline * 100.0) if baseline else None,
                "source_id": record.get("source_id"),
                "source_url": record.get("source_url"),
                "adjustments": applied,
            })
    return {
        "ok": True,
        "schema": SCENARIO_SCHEMA,
        "version": VERSION,
        "generated_at": _now(),
        "integration": matrix["integration"],
        "geographies": matrix["geographies"],
        "adjustments": rules,
        "results": results,
        "skipped": skipped,
        "methodology": {
            "hypothetical": True,
            "forecast": False,
            "probability": False,
            "causal_model": False,
            "recommendation": False,
            "statement": "Scenario values are user-defined arithmetic transformations of published baselines. They do not predict future outcomes.",
        },
    }


def _pearson(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    if len(xs) != len(ys) or len(xs) < 3:
        return None
    x_mean = sum(xs) / len(xs)
    y_mean = sum(ys) / len(ys)
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
    x_var = sum((x - x_mean) ** 2 for x in xs)
    y_var = sum((y - y_mean) ** 2 for y in ys)
    if x_var <= 0 or y_var <= 0:
        return None
    return numerator / math.sqrt(x_var * y_var)


def build_correlation_review(settings: Any = None, *, geography: str, indicator_x: str, indicator_y: str, limit: int = 200) -> dict[str, Any]:
    from .economics_markets_sustainability import build_economic_series
    code = _codes([geography], limit=1)
    if not code or not _safe_text(indicator_x, 160) or not _safe_text(indicator_y, 160):
        raise ValueError("A geography and two indicators are required.")
    x_payload = build_economic_series(settings, indicator_code=indicator_x, geography_code=code[0], limit=min(limit, 300))
    y_payload = build_economic_series(settings, indicator_code=indicator_y, geography_code=code[0], limit=min(limit, 300))
    x_points = {str(item.get("period")): item for item in x_payload.get("points", []) if isinstance(item.get("value_number"), (int, float)) and item.get("period")}
    y_points = {str(item.get("period")): item for item in y_payload.get("points", []) if isinstance(item.get("value_number"), (int, float)) and item.get("period")}
    periods = sorted(set(x_points) & set(y_points))
    xs = [float(x_points[period]["value_number"]) for period in periods]
    ys = [float(y_points[period]["value_number"]) for period in periods]
    correlation = _pearson(xs, ys)
    return {
        "ok": True,
        "schema": CORRELATION_SCHEMA,
        "version": VERSION,
        "geography_code": code[0],
        "indicator_x": indicator_x,
        "indicator_y": indicator_y,
        "overlapping_periods": periods,
        "pairs": [{"period": period, "x": x_points[period]["value_number"], "y": y_points[period]["value_number"]} for period in periods],
        "pearson_correlation": correlation,
        "sufficient_overlap": len(periods) >= 3 and correlation is not None,
        "methodology": {"minimum_pairs": 3, "causal_inference": False, "forecasting": False, "statement": "Correlation describes linear co-movement in overlapping published periods and does not establish causation."},
    }


def build_comparison_packet(settings: Any = None, *, payload: Mapping[str, Any]) -> dict[str, Any]:
    comparison = build_comparison_matrix(
        settings,
        geographies=payload.get("geographies"),
        indicators=payload.get("indicators"),
        domains=payload.get("domains"),
        start=_safe_text(payload.get("start"), 40),
        end=_safe_text(payload.get("end"), 40),
    )
    scenario = None
    if payload.get("adjustments"):
        scenario = build_transparent_scenario(
            settings,
            geographies=payload.get("geographies"),
            indicators=payload.get("indicators"),
            domains=payload.get("domains"),
            adjustments=payload.get("adjustments"),
            start=_safe_text(payload.get("start"), 40),
            end=_safe_text(payload.get("end"), 40),
        )
    packet = {
        "schema": PACKET_SCHEMA,
        "version": VERSION,
        "generated_at": _now(),
        "title": _safe_text(payload.get("title"), 200) or "Comparative intelligence packet",
        "comparison": comparison,
        "scenario": scenario,
        "notes": _safe_text(payload.get("notes"), 2000),
        "responsible_use": [
            "No ranking or composite score is created.",
            "Scenario values are hypothetical arithmetic transformations, not forecasts.",
            "Correlation does not establish causation.",
            "Source units, periods, frequencies, price bases, and adjustment states remain visible.",
        ],
    }
    digest_payload = json.dumps(packet, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    packet["integrity"] = {"algorithm": "sha256", "digest": hashlib.sha256(digest_payload).hexdigest(), "canonicalization": "sorted compact JSON before integrity field"}
    return {"ok": True, **packet}


def build_studio_diagnostics(settings: Any = None) -> dict[str, Any]:
    config = studio_config(settings)
    return {
        "ok": True,
        "schema": RELEASE_SCHEMA,
        "version": VERSION,
        "configuration": {"enabled": config.enabled, "max_geographies": config.max_geographies, "max_indicators": config.max_indicators, "max_records": config.max_records},
        "public_safety": {"paid_api_required": False, "silent_normalization": False, "ranking": False, "composite_score": False, "forecasting": False, "causal_inference": False, "investment_advice": False, "fabricated_records": False},
        "routes": [
            "/public/comparative-scenario-studio",
            "/public/comparative-scenario-studio/facets",
            "/public/comparative-scenario-studio/compare",
            "/public/comparative-scenario-studio/peers",
            "/public/comparative-scenario-studio/scenario",
            "/public/comparative-scenario-studio/correlation",
            "/public/comparative-scenario-studio/packet",
            "/public/comparative-scenario-studio/diagnostics",
        ],
    }
