"""Economics, Markets, and Sustainability Signals for Site Intelligence v2.2.0.

The module is a public-safe, server-side read bridge to the Sustainable Catalyst
Core economics APIs. It never exposes Core credentials, does not claim licensed
real-time exchange data, preserves reporting frequency and publication dates,
and degrades cleanly when Core is not configured or has no records.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
import math
import os
from typing import Any, Iterable, Mapping

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .global_conditions_observatory import CoreReadConfig, _core_json, _items, _safe_text, _safe_url, core_read_config

RELEASE_SCHEMA = "sc-site-intelligence-economics-sustainability/1.0"
RECORDS_SCHEMA = "sc-site-intelligence-economic-records/1.0"
MAX_RECORDS = 300
MAX_SERIES_POINTS = 240

_ALLOWED_RECORD_TYPES = {
    "official_statistic",
    "macroeconomic_indicator",
    "labour_statistic",
    "trade_statistic",
    "energy_statistic",
    "company_filing_fact",
    "agriculture_statistic",
    "demographic_statistic",
}

_FAMILY_LABELS = {
    "macroeconomics": "Macroeconomics",
    "labour": "Labour and livelihoods",
    "trade": "Trade and production",
    "finance": "Financial conditions",
    "energy": "Energy systems",
    "sustainability": "Sustainability and development",
    "agriculture": "Food and agriculture",
    "demographics": "Population and society",
    "companies": "Company filings",
    "other": "Other official statistics",
}

_EXPECTED_SOURCES = [
    {"id": "world-bank", "name": "World Bank", "family": "development"},
    {"id": "imf", "name": "International Monetary Fund", "family": "macroeconomics"},
    {"id": "oecd", "name": "OECD", "family": "official-statistics"},
    {"id": "eurostat", "name": "Eurostat", "family": "official-statistics"},
    {"id": "ecb", "name": "European Central Bank", "family": "financial-conditions"},
    {"id": "bis", "name": "Bank for International Settlements", "family": "financial-conditions"},
    {"id": "fred", "name": "FRED / ALFRED", "family": "macroeconomics"},
    {"id": "bea", "name": "U.S. Bureau of Economic Analysis", "family": "national-accounts"},
    {"id": "bls", "name": "U.S. Bureau of Labor Statistics", "family": "labour"},
    {"id": "census", "name": "U.S. Census Bureau", "family": "demographics"},
    {"id": "sec-edgar", "name": "SEC EDGAR", "family": "company-filings"},
    {"id": "eia", "name": "U.S. Energy Information Administration", "family": "energy"},
    {"id": "faostat", "name": "FAOSTAT", "family": "agriculture"},
    {"id": "ilostat", "name": "ILOSTAT", "family": "labour"},
    {"id": "un-comtrade", "name": "UN Comtrade", "family": "trade"},
    {"id": "un-sdg", "name": "UN SDG Indicators", "family": "sustainability"},
    {"id": "un-population", "name": "UN Population Division", "family": "demographics"},
]

_SENSITIVE_KEYS = {
    "api_key", "apikey", "key", "token", "authorization", "password", "secret",
    "credential", "write_api_key", "public_api_key",
}


def _sensitive_key(value: Any) -> bool:
    normalized = "".join(character for character in str(value or "").lower() if character.isalnum())
    return any(token in normalized for token in ("apikey", "token", "authorization", "password", "secret", "credential")) or normalized == "key"


def _public_url(value: Any) -> str:
    safe = _safe_url(value)
    if not safe:
        return ""
    parts = urlsplit(safe)
    query = [(key, item) for key, item in parse_qsl(parts.query, keep_blank_values=True) if not _sensitive_key(key)]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query, doseq=True), parts.fragment))


@dataclass(frozen=True)
class EconomicsConfig:
    enabled: bool
    timeout_seconds: float
    cache_ttl_seconds: int


def _as_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on", "enabled"}


def economics_config(settings: Any = None) -> EconomicsConfig:
    enabled_value = getattr(settings, "economics_sustainability_enabled", None)
    if enabled_value is None:
        enabled_value = os.getenv("SC_SI_ECONOMICS_SUSTAINABILITY_ENABLED", "true")
    timeout_value = getattr(settings, "economics_sustainability_timeout_seconds", None)
    if timeout_value is None:
        timeout_value = os.getenv("SC_SI_ECONOMICS_SUSTAINABILITY_TIMEOUT_SECONDS", "9")
    ttl_value = getattr(settings, "economics_sustainability_cache_ttl_seconds", None)
    if ttl_value is None:
        ttl_value = os.getenv("SC_SI_ECONOMICS_SUSTAINABILITY_CACHE_TTL_SECONDS", "120")
    return EconomicsConfig(
        enabled=_as_bool(enabled_value, True),
        timeout_seconds=max(2.0, min(float(timeout_value), 30.0)),
        cache_ttl_seconds=max(15, min(int(ttl_value), 1800)),
    )


def _clean_scalar(value: Any, limit: int = 1200) -> Any:
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return _safe_text(value, limit)


def _safe_mapping(value: Any, *, depth: int = 0) -> dict[str, Any]:
    if not isinstance(value, Mapping) or depth > 2:
        return {}
    output: dict[str, Any] = {}
    for raw_key, raw_value in value.items():
        key = _safe_text(raw_key, 80)
        if not key or key.lower() in _SENSITIVE_KEYS or _sensitive_key(key):
            continue
        if isinstance(raw_value, Mapping):
            nested = _safe_mapping(raw_value, depth=depth + 1)
            if nested:
                output[key] = nested
        elif isinstance(raw_value, list):
            cleaned = [_clean_scalar(item, 240) for item in raw_value[:30] if not isinstance(item, (dict, list))]
            if cleaned:
                output[key] = cleaned
        else:
            output[key] = _clean_scalar(raw_value, 500)
    return output


def _family(record: Mapping[str, Any]) -> str:
    record_type = str(record.get("record_type") or "").lower()
    text = " ".join(
        str(record.get(field) or "").lower()
        for field in ("subject", "indicator_name", "indicator_code", "dataset_id", "notes")
    )
    if record_type == "company_filing_fact":
        return "companies"
    if record_type == "labour_statistic" or any(term in text for term in ("employment", "unemployment", "wage", "labour", "labor", "productivity")):
        return "labour"
    if record_type == "trade_statistic" or any(term in text for term in ("trade", "export", "import", "commodity")):
        return "trade"
    if record_type == "energy_statistic" or any(term in text for term in ("energy", "electric", "power", "fuel", "oil", "gas", "renewable")):
        return "energy"
    if record_type == "agriculture_statistic" or any(term in text for term in ("agriculture", "crop", "food", "forest", "fishery")):
        return "agriculture"
    if record_type == "demographic_statistic" or any(term in text for term in ("population", "poverty", "housing", "household", "demographic")):
        return "demographics"
    if any(term in text for term in ("sdg", "sustain", "emission", "carbon", "climate", "water", "environment", "development")):
        return "sustainability"
    if any(term in text for term in ("interest rate", "exchange rate", "yield", "credit", "bank", "money", "financial", "inflation")):
        return "finance"
    if record_type == "macroeconomic_indicator" or any(term in text for term in ("gdp", "gross domestic", "national account", "debt", "price index", "cpi")):
        return "macroeconomics"
    return "other"


def _frequency_label(value: Any) -> str:
    text = str(value or "").strip().lower()
    mapping = {
        "a": "ANNUAL", "annual": "ANNUAL", "yearly": "ANNUAL", "y": "ANNUAL",
        "q": "QUARTERLY", "quarterly": "QUARTERLY",
        "m": "MONTHLY", "monthly": "MONTHLY",
        "w": "WEEKLY", "weekly": "WEEKLY",
        "d": "DAILY", "daily": "DAILY",
        "h": "HOURLY", "hourly": "HOURLY",
    }
    return mapping.get(text, "")


def _data_status(record: Mapping[str, Any]) -> str:
    status = str(record.get("status") or "").strip().lower().replace("-", "_").replace(" ", "_")
    explicit = {
        "official_release": "OFFICIAL RELEASE",
        "latest_available": "LATEST AVAILABLE",
        "delayed": "DELAYED",
        "end_of_day": "END OF DAY",
        "stale": "STALE",
    }
    if status in explicit:
        return explicit[status]
    frequency = _frequency_label(record.get("frequency"))
    if frequency:
        return frequency
    # Official-statistics records are release observations unless the source says otherwise.
    return "LATEST AVAILABLE"


def _number(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _public_record(record: Mapping[str, Any]) -> dict[str, Any]:
    record_type = _safe_text(record.get("record_type"), 80)
    if record_type not in _ALLOWED_RECORD_TYPES:
        record_type = "official_statistic"
    output = {
        "id": _safe_text(record.get("id"), 180),
        "source_record_id": _safe_text(record.get("source_record_id"), 240),
        "source_id": _safe_text(record.get("source_id"), 140),
        "connector_id": _safe_text(record.get("connector_id"), 180),
        "record_type": record_type,
        "subject": _safe_text(record.get("subject"), 180),
        "family": "",
        "family_label": "",
        "indicator_code": _safe_text(record.get("indicator_code"), 180),
        "indicator_name": _safe_text(record.get("indicator_name"), 360),
        "dataset_id": _safe_text(record.get("dataset_id"), 180),
        "geography_code": _safe_text(record.get("geography_code"), 20).upper(),
        "geography_name": _safe_text(record.get("geography_name"), 180),
        "counterpart_code": _safe_text(record.get("counterpart_code"), 20).upper(),
        "period": _safe_text(record.get("period"), 80),
        "period_start": _safe_text(record.get("period_start"), 50),
        "period_end": _safe_text(record.get("period_end"), 50),
        "frequency": _safe_text(record.get("frequency"), 40),
        "value_number": _number(record.get("value_number")),
        "value_text": _safe_text(record.get("value_text"), 500),
        "unit": _safe_text(record.get("unit"), 160),
        "multiplier": _safe_text(record.get("multiplier"), 80),
        "seasonal_adjustment": _safe_text(record.get("seasonal_adjustment"), 120),
        "price_basis": _safe_text(record.get("price_basis"), 120),
        "status": _safe_text(record.get("status"), 80),
        "data_status": "",
        "release_name": _safe_text(record.get("release_name"), 240),
        "vintage_date": _safe_text(record.get("vintage_date"), 50),
        "published_at": _safe_text(record.get("published_at"), 50),
        "dimensions": _safe_mapping(record.get("dimensions")),
        "notes": _safe_text(record.get("notes"), 1200),
        "source_url": _public_url(record.get("source_url")),
        "license_name": _safe_text(record.get("license_name"), 180),
        "attribution": _safe_text(record.get("attribution"), 400),
        "content_hash": _safe_text(record.get("content_hash"), 180),
    }
    output["family"] = _family(output)
    output["family_label"] = _FAMILY_LABELS[output["family"]]
    output["data_status"] = _data_status(output)
    return output


def _core_records_payload(settings: Any, query: Mapping[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    base_core = core_read_config(settings)
    local = economics_config(settings)
    core = CoreReadConfig(
        enabled=base_core.enabled,
        base_url=base_core.base_url,
        api_key=base_core.api_key,
        timeout_seconds=local.timeout_seconds,
        cache_ttl_seconds=local.cache_ttl_seconds,
    )
    if not local.enabled:
        raise RuntimeError("The economics and sustainability workspace is disabled.")
    if not core.configured:
        raise RuntimeError("Platform Core public economics reading is not configured.")
    query_values = dict(query)
    query_values["limit"] = min(max(int(query_values.get("limit") or 100), 1), MAX_RECORDS)
    payload = _core_json(
        core,
        "/api/v1/economics/records",
        query_values,
        cache_key="economics:" + "&".join(f"{key}={query_values[key]}" for key in sorted(query_values)),
    )
    records = [_public_record(item) for item in _items(payload, "items", "records")]
    meta = payload.get("meta") if isinstance(payload, dict) and isinstance(payload.get("meta"), dict) else {}
    return records, meta


def _integration_state(settings: Any, *, error: str = "") -> dict[str, Any]:
    core = core_read_config(settings)
    local = economics_config(settings)
    configured = bool(local.enabled and core.configured)
    if not local.enabled:
        state, message = "disabled", "The economics and sustainability workspace is disabled by configuration."
    elif not core.configured:
        state, message = "core-unconfigured", "Platform Core is not configured; no economic values are fabricated locally."
    elif error:
        state, message = "degraded", error
    else:
        state, message = "connected", "Core economics and official-statistics records are available through the Site Intelligence public bridge."
    return {
        "enabled": local.enabled,
        "configured": configured,
        "state": state,
        "message": message,
        "credential_exposed": False,
    }


def build_economics_overview(settings: Any = None) -> dict[str, Any]:
    generated_at = datetime.now(timezone.utc).isoformat()
    records: list[dict[str, Any]] = []
    meta: dict[str, Any] = {}
    error = ""
    try:
        records, meta = _core_records_payload(settings, {"limit": 200})
    except RuntimeError as exc:
        error = str(exc)
    families = Counter(item["family"] for item in records)
    sources = Counter(item["source_id"] for item in records if item.get("source_id"))
    geographies = {item["geography_code"] for item in records if item.get("geography_code")}
    indicators = {item["indicator_code"] or item["indicator_name"] for item in records if item.get("indicator_code") or item.get("indicator_name")}
    pagination = meta.get("pagination") if isinstance(meta.get("pagination"), dict) else {}
    return {
        "ok": True,
        "schema": RELEASE_SCHEMA,
        "version": "2.2.0",
        "release_name": "Economics, Markets, and Sustainability Signals",
        "generated_at": generated_at,
        "integration": _integration_state(settings, error=error),
        "counts": {
            "records_visible": len(records),
            "records_available": int(pagination.get("total") or len(records)),
            "sources_visible": len(sources),
            "geographies_visible": len(geographies),
            "indicators_visible": len(indicators),
        },
        "families": [
            {"id": key, "label": _FAMILY_LABELS[key], "count": int(families.get(key, 0))}
            for key in _FAMILY_LABELS
        ],
        "sources": [
            {**source, "visible_records": int(sources.get(source["id"], 0))}
            for source in _EXPECTED_SOURCES
        ],
        "market_data_policy": {
            "licensed_real_time_exchange_data": False,
            "allowed_labels": [
                "OFFICIAL RELEASE", "LATEST AVAILABLE", "DELAYED", "END OF DAY",
                "HOURLY", "DAILY", "WEEKLY", "MONTHLY", "QUARTERLY", "ANNUAL", "STALE",
            ],
            "statement": "Site Intelligence displays official releases and source-defined frequencies; it does not represent free official-statistics feeds as licensed real-time exchange data.",
        },
    }


def build_economic_records(
    settings: Any = None,
    *,
    family: str = "",
    record_type: str = "",
    subject: str = "",
    source_id: str = "",
    indicator_code: str = "",
    geography_code: str = "",
    frequency: str = "",
    query: str = "",
    start: str = "",
    end: str = "",
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    parameters = {
        "record_type": record_type,
        "subject": subject,
        "source_id": source_id,
        "indicator_code": indicator_code,
        "geography_code": geography_code.upper(),
        "frequency": frequency,
        "query": query,
        "start": start,
        "end": end,
        "limit": min(max(int(limit), 1), MAX_RECORDS),
        "offset": max(int(offset), 0),
    }
    parameters = {key: value for key, value in parameters.items() if value not in (None, "")}
    try:
        records, meta = _core_records_payload(settings, parameters)
        integration = _integration_state(settings)
    except RuntimeError as exc:
        records, meta = [], {}
        integration = _integration_state(settings, error=str(exc))
    if family:
        family = family.strip().lower()
        records = [item for item in records if item["family"] == family]
    pagination = meta.get("pagination") if isinstance(meta.get("pagination"), dict) else {}
    return {
        "ok": True,
        "schema": RECORDS_SCHEMA,
        "version": "2.2.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "integration": integration,
        "filters": {**parameters, "family": family},
        "pagination": {
            "total": int(pagination.get("total") or len(records)),
            "limit": int(parameters.get("limit") or limit),
            "offset": int(parameters.get("offset") or 0),
            "returned": len(records),
        },
        "records": records,
    }


def build_economic_facets(settings: Any = None, *, geography_code: str = "") -> dict[str, Any]:
    payload = build_economic_records(settings, geography_code=geography_code, limit=MAX_RECORDS)
    records = payload["records"]
    indicators: dict[str, dict[str, str]] = {}
    geographies: dict[str, str] = {}
    for item in records:
        code = item.get("indicator_code") or item.get("indicator_name")
        if code:
            indicators[str(code)] = {
                "code": str(code),
                "name": item.get("indicator_name") or str(code),
                "unit": item.get("unit") or "",
                "family": item.get("family") or "other",
            }
        if item.get("geography_code"):
            geographies[item["geography_code"]] = item.get("geography_name") or item["geography_code"]
    def count(field: str) -> list[dict[str, Any]]:
        values = Counter(str(item.get(field) or "") for item in records if item.get(field))
        return [{"id": key, "label": _FAMILY_LABELS.get(key, key.replace("_", " ").title()), "count": value} for key, value in values.most_common()]
    return {
        "ok": True,
        "schema": "sc-site-intelligence-economic-facets/1.0",
        "version": "2.2.0",
        "integration": payload["integration"],
        "families": count("family"),
        "record_types": count("record_type"),
        "sources": count("source_id"),
        "frequencies": count("frequency"),
        "indicators": sorted(indicators.values(), key=lambda item: (item["name"].lower(), item["code"])),
        "geographies": [{"code": code, "name": name} for code, name in sorted(geographies.items(), key=lambda pair: pair[1])],
    }


def _period_sort_key(record: Mapping[str, Any]) -> tuple[str, str]:
    return (str(record.get("period_start") or record.get("period") or ""), str(record.get("published_at") or ""))


def build_economic_series(
    settings: Any = None,
    *,
    indicator_code: str,
    geography_code: str = "",
    source_id: str = "",
    limit: int = 120,
) -> dict[str, Any]:
    if not indicator_code.strip():
        raise ValueError("indicator_code is required.")
    payload = build_economic_records(
        settings,
        indicator_code=indicator_code,
        geography_code=geography_code,
        source_id=source_id,
        limit=min(max(int(limit), 1), MAX_SERIES_POINTS),
    )
    records = sorted(payload["records"], key=_period_sort_key)
    return {
        "ok": True,
        "schema": "sc-site-intelligence-economic-series/1.0",
        "version": "2.2.0",
        "integration": payload["integration"],
        "indicator_code": indicator_code,
        "geography_code": geography_code.upper(),
        "source_id": source_id,
        "points": [
            {
                "period": item.get("period") or item.get("period_start"),
                "period_start": item.get("period_start"),
                "value_number": item.get("value_number"),
                "value_text": item.get("value_text"),
                "unit": item.get("unit"),
                "status": item.get("data_status"),
                "source_id": item.get("source_id"),
                "published_at": item.get("published_at"),
                "record_id": item.get("id"),
            }
            for item in records
        ],
        "latest": records[-1] if records else None,
    }


def _latest_by_geography(records: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in records:
        if item.get("geography_code"):
            grouped[item["geography_code"]].append(item)
    return {code: sorted(items, key=_period_sort_key)[-1] for code, items in grouped.items() if items}


def build_economic_comparison(
    settings: Any = None,
    *,
    indicator_code: str,
    geography_a: str,
    geography_b: str,
    limit: int = 120,
) -> dict[str, Any]:
    if not indicator_code.strip():
        raise ValueError("indicator_code is required.")
    geography_a = geography_a.strip().upper()
    geography_b = geography_b.strip().upper()
    if not geography_a or not geography_b:
        raise ValueError("Two geography codes are required.")
    if geography_a == geography_b:
        raise ValueError("Choose two different geographies.")
    series_a = build_economic_series(settings, indicator_code=indicator_code, geography_code=geography_a, limit=limit)
    series_b = build_economic_series(settings, indicator_code=indicator_code, geography_code=geography_b, limit=limit)
    return {
        "ok": True,
        "schema": "sc-site-intelligence-economic-comparison/1.0",
        "version": "2.2.0",
        "indicator_code": indicator_code,
        "geographies": [geography_a, geography_b],
        "integration": series_a["integration"] if series_a["integration"]["state"] != "connected" else series_b["integration"],
        "series": {geography_a: series_a, geography_b: series_b},
        "latest": {geography_a: series_a.get("latest"), geography_b: series_b.get("latest")},
        "interpretation": "Values are aligned by published period where possible. Differences in source, unit, price basis, seasonal adjustment, and reporting frequency remain visible and are not normalized silently.",
    }


def build_economics_brief(
    settings: Any = None,
    *,
    geography_code: str = "",
    family: str = "",
    limit: int = 80,
) -> dict[str, Any]:
    payload = build_economic_records(settings, geography_code=geography_code, family=family, limit=min(limit, 150))
    latest = _latest_by_geography(payload["records"])
    records = payload["records"]
    return {
        "ok": True,
        "schema": "sc-site-intelligence-economic-brief/1.0",
        "version": "2.2.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "integration": payload["integration"],
        "scope": {"geography_code": geography_code.upper(), "family": family},
        "summary": {
            "records_reviewed": len(records),
            "sources": sorted({item["source_id"] for item in records if item.get("source_id")}),
            "indicators": len({item["indicator_code"] or item["indicator_name"] for item in records if item.get("indicator_code") or item.get("indicator_name")}),
            "latest_by_geography": latest,
        },
        "method_note": "This deterministic brief organizes official statistical records. It does not forecast markets, recommend investments, infer causality, or replace professional economic analysis.",
    }


def build_economics_diagnostics(settings: Any = None) -> dict[str, Any]:
    overview = build_economics_overview(settings)
    return {
        "ok": True,
        "schema": "sc-site-intelligence-economics-diagnostics/1.0",
        "version": "2.2.0",
        "release_name": "Economics, Markets, and Sustainability Signals",
        "integration": overview["integration"],
        "counts": overview["counts"],
        "free_provider_policy": {
            "paid_api_required": False,
            "credit_card_required": False,
            "browser_credential_exposure": False,
            "licensed_real_time_exchange_feed_claimed": False,
        },
        "expected_sources": _EXPECTED_SOURCES,
    }
