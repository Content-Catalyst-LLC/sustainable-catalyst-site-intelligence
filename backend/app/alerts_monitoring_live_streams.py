"""Alerts, Monitoring, and Live Intelligence Streams for Site Intelligence v2.8.0.

The module creates a public, source-aware stream from existing Site Intelligence
observatories. Rules are evaluated statelessly; user rules and watched places are
stored by the browser, not by the backend. The stream does not create operational
emergency warnings, individual risk scores, investment signals, legal conclusions,
or military/security targeting recommendations.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
import re
from typing import Any, Callable, Iterable, Mapping, Sequence

VERSION = "2.8.0"
RELEASE_SCHEMA = "sc-site-intelligence-alerts-monitoring/1.0"
STREAM_SCHEMA = "sc-site-intelligence-live-stream/1.0"
RULE_SCHEMA = "sc-site-intelligence-alert-rule/1.0"
DIGEST_SCHEMA = "sc-site-intelligence-monitoring-digest/1.0"
MAX_SIGNALS = 400
MAX_RULES = 50
MAX_MATCHES = 250

FAMILY_LABELS = {
    "conditions": "Global conditions",
    "humanitarian": "Humanitarian and displacement",
    "economics": "Economics and sustainability",
    "law": "International law and governance",
    "science": "Scientific and Earth systems",
    "resources": "Trade, energy, and resources",
}

# The thresholds classify how old the displayed record is relative to the
# current request. They do not override a provider's own freshness status.
FRESHNESS_WINDOWS_HOURS = {
    "conditions": 36,
    "humanitarian": 72,
    "economics": 24 * 45,
    "law": 24 * 60,
    "science": 24 * 30,
    "resources": 24 * 45,
}

ALLOWED_OPERATORS = {"gt", "gte", "lt", "lte", "eq"}


@dataclass(frozen=True)
class MonitoringConfig:
    enabled: bool
    reconnect_seconds: int
    max_signals: int
    stale_source_hours: int


def _as_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on", "enabled"}


def monitoring_config(settings: Any = None) -> MonitoringConfig:
    enabled = getattr(settings, "alerts_monitoring_enabled", None)
    reconnect = getattr(settings, "alerts_stream_reconnect_seconds", None)
    limit = getattr(settings, "alerts_stream_max_signals", None)
    stale = getattr(settings, "alerts_stale_source_hours", None)
    if enabled is None:
        enabled = os.getenv("SC_SI_ALERTS_MONITORING_ENABLED", "true")
    if reconnect is None:
        reconnect = os.getenv("SC_SI_ALERTS_STREAM_RECONNECT_SECONDS", "30")
    if limit is None:
        limit = os.getenv("SC_SI_ALERTS_STREAM_MAX_SIGNALS", "180")
    if stale is None:
        stale = os.getenv("SC_SI_ALERTS_STALE_SOURCE_HOURS", "72")
    return MonitoringConfig(
        enabled=_as_bool(enabled, True),
        reconnect_seconds=max(10, min(int(reconnect), 300)),
        max_signals=max(20, min(int(limit), MAX_SIGNALS)),
        stale_source_hours=max(6, min(int(stale), 24 * 365)),
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
    lowered = text.lower()
    if re.search(r"(?:api[_-]?key|access[_-]?token|token|authorization)=", lowered):
        return text.split("?", 1)[0]
    return text


def _parse_time(value: Any) -> datetime | None:
    text = _safe_text(value, 80)
    if not text:
        return None
    if re.fullmatch(r"\d{4}", text):
        text = f"{text}-12-31T00:00:00+00:00"
    elif re.fullmatch(r"\d{4}-\d{2}", text):
        text = f"{text}-28T00:00:00+00:00"
    elif re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        text += "T00:00:00+00:00"
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return None


def _first(row: Mapping[str, Any], keys: Sequence[str]) -> Any:
    for key in keys:
        value = row.get(key)
        if value not in (None, "", [], {}):
            return value
    return None


def _rows(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    for key in ("records", "signals", "events", "observations", "features", "items"):
        value = payload.get(key)
        if isinstance(value, list):
            if key == "features":
                output = []
                for feature in value:
                    if not isinstance(feature, Mapping):
                        continue
                    props = dict(feature.get("properties") or {})
                    props.setdefault("id", feature.get("id"))
                    props.setdefault("geometry", feature.get("geometry"))
                    output.append(props)
                return output
            return [dict(item) for item in value if isinstance(item, Mapping)]
    return []


def _state(payload: Mapping[str, Any]) -> str:
    integration = payload.get("integration")
    if isinstance(integration, Mapping) and integration.get("state"):
        return _safe_text(integration.get("state"), 80)
    for key in ("state", "data_state", "delivery_state", "status"):
        if payload.get(key):
            return _safe_text(payload.get(key), 80)
    return "unavailable"


def _countries(row: Mapping[str, Any]) -> list[str]:
    values: list[Any] = []
    for key in ("countries", "country_codes", "geographies"):
        value = row.get(key)
        if isinstance(value, list):
            values.extend(value)
    for key in ("country", "country_code", "geography_code", "reporting_geography_code"):
        value = row.get(key)
        if value:
            values.append(value)
    result = []
    for value in values:
        token = _safe_text(value, 20).upper()
        if token and token not in result:
            result.append(token)
    return result[:40]


def _numeric(row: Mapping[str, Any]) -> float | None:
    latest = row.get("latest")
    if isinstance(latest, Mapping):
        value = latest.get("value")
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)
    for key in ("value_number", "numeric_value", "value", "magnitude"):
        value = row.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)
    return None


def _geometry(row: Mapping[str, Any]) -> dict[str, Any] | None:
    geometry = row.get("geometry")
    if isinstance(geometry, Mapping) and geometry.get("type") in {
        "Point", "MultiPoint", "LineString", "MultiLineString",
        "Polygon", "MultiPolygon", "GeometryCollection",
    }:
        return dict(geometry)
    lat = _first(row, ("latitude", "lat"))
    lon = _first(row, ("longitude", "lng", "lon"))
    try:
        lat_f = float(lat)
        lon_f = float(lon)
    except (TypeError, ValueError):
        return None
    if -90 <= lat_f <= 90 and -180 <= lon_f <= 180:
        return {"type": "Point", "coordinates": [lon_f, lat_f]}
    return None


def _record_time(row: Mapping[str, Any]) -> str:
    value = _first(row, (
        "observed_at", "event_date", "date", "published_at", "publication_date",
        "retrieved_at", "updated_at", "period", "year", "observation_start",
    ))
    if value is None and isinstance(row.get("latest"), Mapping):
        value = row["latest"].get("year")
    return _safe_text(value, 80)


def _freshness(family: str, row: Mapping[str, Any], *, now: datetime) -> tuple[str, int | None]:
    provider = _safe_text(_first(row, ("freshness_status", "freshness", "data_state")), 80).lower()
    timestamp = _parse_time(_record_time(row))
    age_hours = int(max(0, (now - timestamp).total_seconds() // 3600)) if timestamp else None
    if provider in {"stale", "expired"}:
        return "stale", age_hours
    if provider in {"live", "near-real-time", "near_real_time", "current", "fresh"}:
        return "current", age_hours
    if age_hours is None:
        return "unknown", None
    threshold = FRESHNESS_WINDOWS_HOURS.get(family, 24 * 30)
    return ("recent" if age_hours <= threshold else "older"), age_hours


def _signal_id(family: str, row: Mapping[str, Any], index: int) -> str:
    candidate = _first(row, ("id", "record_id", "observation_id", "event_id", "source_record_id"))
    if candidate:
        return f"{family}:{_safe_text(candidate, 200)}"
    seed = json.dumps({
        "family": family,
        "title": _first(row, ("title", "indicator_name", "metric", "label")),
        "source": _first(row, ("source_id", "source")),
        "date": _record_time(row),
        "index": index,
    }, sort_keys=True, default=str)
    return f"{family}:{hashlib.sha256(seed.encode()).hexdigest()[:24]}"


def _normalize_signal(family: str, row: Mapping[str, Any], index: int, *, now: datetime) -> dict[str, Any]:
    title = _safe_text(_first(row, ("title", "indicator_name", "metric", "label", "summary")), 500) or "Public intelligence signal"
    source_id = _safe_text(_first(row, ("source_id", "source", "provider")), 180) or "source-unavailable"
    freshness, age_hours = _freshness(family, row, now=now)
    value = _numeric(row)
    unit = _safe_text(_first(row, ("unit", "unit_label")), 100)
    record_type = _safe_text(_first(row, ("record_type", "category", "family", "domain", "signal_type")), 140) or family
    source_url = _safe_url(_first(row, ("source_url", "public_url", "landing_page_url", "access_url", "url")))
    status = _safe_text(_first(row, ("status", "quality_status", "quality_label", "data_state", "severity")), 100)
    summary = _safe_text(_first(row, ("summary", "description", "interpretation", "notes")), 1000)
    return {
        "id": _signal_id(family, row, index),
        "family": family,
        "family_label": FAMILY_LABELS[family],
        "title": title,
        "summary": summary,
        "record_type": record_type,
        "source_id": source_id,
        "source_url": source_url,
        "observed_at": _record_time(row),
        "freshness": freshness,
        "age_hours": age_hours,
        "provider_status": status,
        "countries": _countries(row),
        "geometry": _geometry(row),
        "value_number": value,
        "unit": unit,
        "quality_status": _safe_text(_first(row, ("quality_status", "quality_label")), 100),
        "license": _safe_text(row.get("license"), 240),
        "attribution": _safe_text(row.get("attribution"), 300),
    }


def _collectors() -> dict[str, Callable[[Any, int], Mapping[str, Any]]]:
    def conditions(settings: Any, limit: int) -> Mapping[str, Any]:
        from .global_conditions_observatory import build_global_conditions_signals
        return build_global_conditions_signals(settings, limit=limit)

    def humanitarian(settings: Any, limit: int) -> Mapping[str, Any]:
        from .humanitarian_conflict_displacement_observatory import build_records
        return build_records(settings, days=30, include_hazards=True, limit=limit)

    def economics(settings: Any, limit: int) -> Mapping[str, Any]:
        from .economics_markets_sustainability import build_economic_records
        return build_economic_records(settings, limit=limit)

    def law(settings: Any, limit: int) -> Mapping[str, Any]:
        from .international_law_observatory import build_law_records
        return build_law_records(settings, limit=limit)

    def science(settings: Any, limit: int) -> Mapping[str, Any]:
        from .scientific_earth_systems_observatory import build_science_records
        return build_science_records(settings, limit=limit)

    def resources(settings: Any, limit: int) -> Mapping[str, Any]:
        from .trade_energy_resource_security_observatory import build_records
        return build_records(settings, limit=limit)

    return {
        "conditions": conditions,
        "humanitarian": humanitarian,
        "economics": economics,
        "law": law,
        "science": science,
        "resources": resources,
    }


def _family_list(value: str | Sequence[str] | None) -> list[str]:
    if value is None or value == "":
        return list(FAMILY_LABELS)
    if isinstance(value, str):
        raw = value.split(",")
    else:
        raw = list(value)
    families = []
    for item in raw:
        token = _safe_text(item, 40).lower()
        if token in FAMILY_LABELS and token not in families:
            families.append(token)
    return families or list(FAMILY_LABELS)


def build_stream_snapshot(
    settings: Any = None,
    *,
    families: str | Sequence[str] | None = None,
    country: str = "",
    query: str = "",
    source_id: str = "",
    freshness: str = "",
    limit: int = 180,
) -> dict[str, Any]:
    config = monitoring_config(settings)
    generated = _now()
    bounded = max(1, min(int(limit), config.max_signals, MAX_SIGNALS))
    if not config.enabled:
        return {
            "ok": True, "schema": STREAM_SCHEMA, "version": VERSION,
            "generated_at": generated, "state": "disabled", "signals": [],
            "count": 0, "source_states": {}, "fallback_used": False,
        }
    wanted = _family_list(families)
    per_family = max(8, min(80, (bounded // max(1, len(wanted))) + 8))
    now_dt = datetime.now(timezone.utc)
    signals: list[dict[str, Any]] = []
    source_states: dict[str, str] = {}
    errors: dict[str, str] = {}
    collectors = _collectors()
    for family in wanted:
        try:
            payload = collectors[family](settings, per_family)
            if not isinstance(payload, Mapping):
                raise RuntimeError("invalid public workspace payload")
            source_states[family] = _state(payload)
            for index, row in enumerate(_rows(payload)):
                signals.append(_normalize_signal(family, row, index, now=now_dt))
        except Exception as exc:  # optional upstream failures remain local
            source_states[family] = "unavailable"
            errors[family] = _safe_text(exc, 240)

    country_token = _safe_text(country, 20).upper()
    query_token = _safe_text(query, 240).lower()
    source_token = _safe_text(source_id, 180).lower()
    freshness_token = _safe_text(freshness, 80).lower()
    filtered = []
    for item in signals:
        if country_token and country_token not in item["countries"]:
            continue
        if source_token and item["source_id"].lower() != source_token:
            continue
        if freshness_token and item["freshness"].lower() != freshness_token:
            continue
        if query_token:
            haystack = " ".join(
                str(item.get(key) or "")
                for key in ("title", "summary", "record_type", "source_id", "countries", "family")
            ).lower()
            if query_token not in haystack:
                continue
        filtered.append(item)

    def sort_key(item: Mapping[str, Any]) -> tuple[int, float, str]:
        parsed = _parse_time(item.get("observed_at"))
        stamp = parsed.timestamp() if parsed else 0.0
        stale_rank = {"stale": 0, "older": 1, "recent": 2, "current": 3, "unknown": 4}.get(str(item.get("freshness")), 5)
        return (stale_rank, -stamp, str(item.get("title") or ""))

    # Current/recent records should display before older records, while explicit
    # stale records remain visible through source-watch and filters.
    filtered.sort(key=lambda item: (
        {"current": 0, "recent": 1, "unknown": 2, "older": 3, "stale": 4}.get(item["freshness"], 5),
        -((_parse_time(item.get("observed_at")) or datetime(1970, 1, 1, tzinfo=timezone.utc)).timestamp()),
    ))
    page = filtered[:bounded]
    connected = sum(1 for state in source_states.values() if state in {"connected", "live", "partial-live", "cached"})
    overall = "connected" if page and connected else ("degraded" if page or connected else "unavailable")
    return {
        "ok": True,
        "schema": STREAM_SCHEMA,
        "version": VERSION,
        "generated_at": generated,
        "state": overall,
        "signals": page,
        "count": len(page),
        "total_before_limit": len(filtered),
        "source_states": source_states,
        "source_errors": errors,
        "filters": {
            "families": wanted,
            "country": country_token,
            "query": query_token,
            "source_id": source_token,
            "freshness": freshness_token,
        },
        "fallback_used": False,
        "credential_exposed": False,
        "operational_emergency_alert": False,
    }


def build_monitoring_facets(settings: Any = None, *, limit: int = 240) -> dict[str, Any]:
    payload = build_stream_snapshot(settings, limit=limit)
    signals = payload["signals"]
    sources = Counter(item["source_id"] for item in signals if item["source_id"])
    countries = Counter(code for item in signals for code in item["countries"])
    types = Counter(item["record_type"] for item in signals if item["record_type"])
    return {
        "ok": True,
        "version": VERSION,
        "state": payload["state"],
        "families": [
            {"id": key, "label": label, "count": sum(1 for item in signals if item["family"] == key)}
            for key, label in FAMILY_LABELS.items()
        ],
        "sources": [{"id": key, "count": count} for key, count in sources.most_common()],
        "countries": [{"code": key, "count": count} for key, count in countries.most_common()],
        "record_types": [{"id": key, "count": count} for key, count in types.most_common()],
        "freshness": dict(Counter(item["freshness"] for item in signals)),
    }


def _normalize_rule(rule: Mapping[str, Any], index: int) -> dict[str, Any]:
    operator = _safe_text(rule.get("threshold_operator"), 12).lower()
    if operator not in ALLOWED_OPERATORS:
        operator = ""
    threshold = rule.get("threshold_value")
    try:
        threshold_number = float(threshold) if threshold not in (None, "") else None
    except (TypeError, ValueError):
        threshold_number = None
    return {
        "id": _safe_text(rule.get("id"), 120) or f"rule-{index + 1}",
        "name": _safe_text(rule.get("name"), 180) or f"Alert rule {index + 1}",
        "active": _as_bool(rule.get("active"), True),
        "family": _safe_text(rule.get("family"), 40).lower(),
        "country": _safe_text(rule.get("country"), 20).upper(),
        "keyword": _safe_text(rule.get("keyword"), 180).lower(),
        "source_id": _safe_text(rule.get("source_id"), 180).lower(),
        "record_type": _safe_text(rule.get("record_type"), 140).lower(),
        "freshness": _safe_text(rule.get("freshness"), 80).lower(),
        "threshold_operator": operator,
        "threshold_value": threshold_number,
    }


def _threshold_matches(value: float | None, operator: str, threshold: float | None) -> bool:
    if not operator:
        return True
    if value is None or threshold is None:
        return False
    return {
        "gt": value > threshold,
        "gte": value >= threshold,
        "lt": value < threshold,
        "lte": value <= threshold,
        "eq": value == threshold,
    }[operator]


def _rule_matches(rule: Mapping[str, Any], signal: Mapping[str, Any]) -> bool:
    if not rule.get("active"):
        return False
    if rule.get("family") and rule["family"] != signal.get("family"):
        return False
    if rule.get("country") and rule["country"] not in signal.get("countries", []):
        return False
    if rule.get("source_id") and rule["source_id"] != str(signal.get("source_id") or "").lower():
        return False
    if rule.get("record_type") and rule["record_type"] != str(signal.get("record_type") or "").lower():
        return False
    if rule.get("freshness") and rule["freshness"] != str(signal.get("freshness") or "").lower():
        return False
    if rule.get("keyword"):
        haystack = " ".join(
            str(signal.get(key) or "")
            for key in ("title", "summary", "record_type", "source_id", "countries", "family")
        ).lower()
        if rule["keyword"] not in haystack:
            return False
    return _threshold_matches(signal.get("value_number"), str(rule.get("threshold_operator") or ""), rule.get("threshold_value"))


def evaluate_alert_rules(
    settings: Any = None,
    *,
    rules: Sequence[Mapping[str, Any]] | None,
    signals: Sequence[Mapping[str, Any]] | None = None,
    limit: int = MAX_MATCHES,
) -> dict[str, Any]:
    raw_rules = list(rules or [])[:MAX_RULES]
    normalized = [_normalize_rule(rule, index) for index, rule in enumerate(raw_rules) if isinstance(rule, Mapping)]
    if signals is None:
        families = sorted({rule["family"] for rule in normalized if rule["family"] in FAMILY_LABELS})
        snapshot = build_stream_snapshot(settings, families=families or None, limit=monitoring_config(settings).max_signals)
        signal_rows = snapshot["signals"]
        state = snapshot["state"]
    else:
        signal_rows = [dict(signal) for signal in signals if isinstance(signal, Mapping)][:MAX_SIGNALS]
        state = "provided"
    matches = []
    counts: Counter[str] = Counter()
    for rule in normalized:
        for signal in signal_rows:
            if _rule_matches(rule, signal):
                counts[rule["id"]] += 1
                matches.append({"rule": rule, "signal": dict(signal)})
                if len(matches) >= max(1, min(limit, MAX_MATCHES)):
                    break
        if len(matches) >= max(1, min(limit, MAX_MATCHES)):
            break
    return {
        "ok": True,
        "schema": RULE_SCHEMA,
        "version": VERSION,
        "generated_at": _now(),
        "state": state,
        "rules": normalized,
        "rule_count": len(normalized),
        "active_rule_count": sum(1 for rule in normalized if rule["active"]),
        "matches": matches,
        "match_count": len(matches),
        "match_counts_by_rule": dict(counts),
        "rules_persisted_server_side": False,
        "automated_decision": False,
        "operational_emergency_alert": False,
    }


def build_source_watch(settings: Any = None, *, limit: int = 240) -> dict[str, Any]:
    config = monitoring_config(settings)
    payload = build_stream_snapshot(settings, limit=limit)
    now_dt = datetime.now(timezone.utc)
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for signal in payload["signals"]:
        grouped.setdefault((signal["family"], signal["source_id"]), []).append(signal)
    sources = []
    for (family, source_id), rows in sorted(grouped.items()):
        parsed = [_parse_time(row.get("observed_at")) for row in rows]
        valid = [value for value in parsed if value]
        latest = max(valid) if valid else None
        age_hours = int((now_dt - latest).total_seconds() // 3600) if latest else None
        threshold_hours = max(config.stale_source_hours, FRESHNESS_WINDOWS_HOURS.get(family, config.stale_source_hours))
        stale = bool(age_hours is not None and age_hours > threshold_hours)
        sources.append({
            "family": family,
            "family_label": FAMILY_LABELS[family],
            "source_id": source_id,
            "record_count": len(rows),
            "latest_record_at": latest.isoformat() if latest else "",
            "age_hours": age_hours,
            "watch_state": "stale" if stale else ("unknown" if latest is None else "current"),
            "threshold_hours": threshold_hours,
            "provider_states": sorted({row.get("provider_status") for row in rows if row.get("provider_status")}),
        })
    # Include families that returned no records so source outages are visible.
    for family, state in payload["source_states"].items():
        if not any(item["family"] == family for item in sources):
            sources.append({
                "family": family,
                "family_label": FAMILY_LABELS.get(family, family),
                "source_id": "workspace",
                "record_count": 0,
                "latest_record_at": "",
                "age_hours": None,
                "watch_state": state if state else "unavailable",
                "provider_states": [state] if state else [],
            })
    return {
        "ok": True,
        "version": VERSION,
        "generated_at": payload["generated_at"],
        "state": payload["state"],
        "sources": sources,
        "count": len(sources),
        "stale_count": sum(1 for item in sources if item["watch_state"] == "stale"),
        "unavailable_count": sum(1 for item in sources if item["watch_state"] in {"unavailable", "degraded", "unconfigured"}),
        "stale_threshold_hours": config.stale_source_hours,
        "interpretation": "Source-watch states describe public record recency and connector availability, not the absence of real-world events.",
    }


def build_monitoring_digest(
    settings: Any = None,
    *,
    rules: Sequence[Mapping[str, Any]] | None = None,
    country: str = "",
    families: str | Sequence[str] | None = None,
    limit: int = 120,
) -> dict[str, Any]:
    snapshot = build_stream_snapshot(settings, country=country, families=families, limit=limit)
    evaluation = evaluate_alert_rules(settings, rules=rules or [], signals=snapshot["signals"])
    family_counts = Counter(signal["family"] for signal in snapshot["signals"])
    source_counts = Counter(signal["source_id"] for signal in snapshot["signals"])
    freshness_counts = Counter(signal["freshness"] for signal in snapshot["signals"])
    return {
        "ok": True,
        "schema": DIGEST_SCHEMA,
        "version": VERSION,
        "generated_at": snapshot["generated_at"],
        "state": snapshot["state"],
        "filters": snapshot["filters"],
        "summary": {
            "signals": snapshot["count"],
            "families": dict(family_counts),
            "sources": len(source_counts),
            "freshness": dict(freshness_counts),
            "rule_matches": evaluation["match_count"],
        },
        "top_sources": [{"source_id": key, "count": count} for key, count in source_counts.most_common(12)],
        "latest_signals": snapshot["signals"][:20],
        "rule_matches": evaluation["matches"][:40],
        "methodology": {
            "generated_from_public_records": True,
            "ai_generated": False,
            "rules_stored_server_side": False,
            "composite_risk_score": False,
            "emergency_instruction": False,
        },
    }


def build_monitoring_overview(settings: Any = None) -> dict[str, Any]:
    config = monitoring_config(settings)
    return {
        "ok": True,
        "schema": RELEASE_SCHEMA,
        "version": VERSION,
        "release_name": "Alerts, Monitoring, and Live Intelligence Streams",
        "generated_at": _now(),
        "state": "enabled" if config.enabled else "disabled",
        "families": [{"id": key, "label": label} for key, label in FAMILY_LABELS.items()],
        "features": [
            "Reconnectable server-sent public stream snapshots",
            "Browser-local alert rules and watched places",
            "Stateless source-aware rule evaluation",
            "Stale-source and unavailable-workspace monitoring",
            "Deterministic public intelligence digests",
        ],
        "stream": {
            "endpoint": "/public/live-intelligence-stream/events",
            "reconnect_seconds": config.reconnect_seconds,
            "persistent_connection_required": False,
        },
        "governance": {
            "paid_provider_required": False,
            "server_side_user_tracking": False,
            "operational_emergency_alert": False,
            "individual_risk_scoring": False,
            "investment_signal": False,
            "legal_determination": False,
            "military_targeting": False,
        },
    }


def build_monitoring_diagnostics(settings: Any = None) -> dict[str, Any]:
    config = monitoring_config(settings)
    return {
        "ok": True,
        "version": VERSION,
        "enabled": config.enabled,
        "reconnect_seconds": config.reconnect_seconds,
        "max_signals": config.max_signals,
        "stale_source_hours": config.stale_source_hours,
        "browser_local_rules": True,
        "server_side_rule_storage": False,
        "server_sent_events": True,
        "fallback_records": False,
        "credential_exposed": False,
        "paid_provider_required": False,
        "public_safety": {
            "emergency_dispatch": False,
            "emergency_warning": False,
            "individual_risk_scoring": False,
            "automated_eligibility": False,
            "investment_advice": False,
            "legal_advice": False,
            "military_targeting": False,
        },
    }


def build_sse_snapshot(
    settings: Any = None,
    *,
    families: str = "",
    country: str = "",
    query: str = "",
    source_id: str = "",
    freshness: str = "",
    limit: int = 120,
) -> str:
    config = monitoring_config(settings)
    snapshot = build_stream_snapshot(
        settings,
        families=families,
        country=country,
        query=query,
        source_id=source_id,
        freshness=freshness,
        limit=limit,
    )
    event_id = hashlib.sha256(
        json.dumps({"generated_at": snapshot["generated_at"], "count": snapshot["count"]}, sort_keys=True).encode()
    ).hexdigest()[:20]
    data = json.dumps(snapshot, separators=(",", ":"), ensure_ascii=False)
    return (
        f"retry: {config.reconnect_seconds * 1000}\n"
        f"id: {event_id}\n"
        "event: snapshot\n"
        f"data: {data}\n\n"
        "event: heartbeat\n"
        f"data: {{\"generated_at\":\"{snapshot['generated_at']}\"}}\n\n"
    )
