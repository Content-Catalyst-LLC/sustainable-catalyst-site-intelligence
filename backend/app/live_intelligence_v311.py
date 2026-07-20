"""Useful public-interest Live Intelligence ticker feed for Site Intelligence v3.1.1.

The ticker summarizes verified public event records and cache-safe NOAA/NWS context.
It deliberately excludes demonstration fixtures, raw upstream payloads, API keys,
automated causal interpretation, emergency instructions, and investment advice.
"""
from __future__ import annotations

from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any, Iterable

from .config import Settings
from .connectors.advanced_external import AdvancedExternalDataHub
from .unified_live_events import unified_events
from .version import APP_VERSION, RELEASE_NAME

SCHEMA_VERSION = "sc-site-intelligence-live-intelligence/1.1"
CATEGORY_ALIASES = {
    "all": "",
    "planet": "earth_systems",
    "earth": "earth_systems",
    "society": "human_systems",
    "humanitarian": "human_systems",
    "weather": "earth_systems",
    "economy": "economy_resources",
    "platform": "platform",
}
NATURAL_EVENT_CATEGORIES = {
    "wildfire", "storm", "flood", "volcano", "extreme-heat", "drought",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean(value: Any, limit: int = 180) -> str:
    return " ".join(str(value or "").split())[:limit]


def _signal(
    *,
    signal_id: str,
    category: str,
    label: str,
    value: str,
    source: str,
    status: str,
    destination: str,
    updated_at: str,
    observed_at: str | None = None,
    detail: str = "",
    source_url: str = "",
    priority: int = 50,
    data_state: str = "current",
) -> dict[str, Any]:
    return {
        "signal_id": signal_id,
        "category": category,
        "label": _clean(label, 90),
        "value": _clean(value, 150),
        "unit": "",
        "status": status,
        "severity": "attention" if status in {"degraded", "stale", "attention"} else "informational",
        "source_name": _clean(source, 120),
        "source_url": source_url if str(source_url).startswith(("https://", "http://")) else "",
        "updated_at": updated_at,
        "observed_at": observed_at or updated_at,
        "destination_url": destination,
        "detail": _clean(detail, 420),
        "priority": int(priority),
        "data_state": data_state,
    }


def _event_destination(record: dict[str, Any]) -> str:
    source_url = str(record.get("source_url") or "")
    if source_url.startswith(("https://", "http://")):
        return source_url
    return "/platform/site-intelligence/"


def _event_signal(record: dict[str, Any], *, label: str, priority: int) -> dict[str, Any]:
    source = _clean(record.get("source_name") or record.get("source") or "Public source")
    observed = str(record.get("observed_at") or record.get("updated_at") or _now())
    state = str(record.get("data_state") or "live")
    status = "stale" if state == "stale" else "current"
    return _signal(
        signal_id=f"event.{record.get('id')}",
        category="human_systems" if record.get("category") in {"humanitarian", "displacement", "conflict"} else "earth_systems",
        label=label,
        value=_clean(record.get("title") or record.get("summary") or "Verified public event", 145),
        source=source,
        status=status,
        destination=_event_destination(record),
        source_url=str(record.get("source_url") or ""),
        updated_at=str(record.get("updated_at") or observed),
        observed_at=observed,
        detail=_clean(record.get("summary") or record.get("title") or "Public event record.", 420),
        priority=priority,
        data_state=state,
    )


def _event_signals(settings: Settings) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Return useful event summaries without ever exposing demonstration fixtures."""
    if not bool(getattr(settings, "external_live", False)):
        return [], {"data_state": "live-disabled", "source_states": {}}
    try:
        payload = unified_events(days=14, limit=160, allow_fallback=False)
    except Exception as exc:  # defensive boundary for optional public APIs
        return [], {"data_state": "unavailable", "source_states": {}, "error": exc.__class__.__name__}

    records = [
        item for item in (payload.get("events") or [])
        if item.get("source") != "local-fallback"
        and item.get("data_state") != "fallback"
        and not (item.get("metadata") or {}).get("fabricated_for_demo")
    ]
    records.sort(key=lambda item: str(item.get("observed_at") or item.get("updated_at") or ""), reverse=True)
    counts = Counter(str(item.get("category") or "other") for item in records)
    delivery = str(payload.get("delivery_state") or payload.get("data_state") or "unavailable")
    count_status = "stale" if delivery == "stale" else "current"
    generated_at = str(payload.get("generated_at") or _now())
    output: list[dict[str, Any]] = []

    earthquakes = [item for item in records if item.get("category") == "earthquake"]
    if earthquakes:
        latest = earthquakes[0]
        magnitude = latest.get("magnitude")
        magnitude_text = f"M{float(magnitude):.1f}" if isinstance(magnitude, (int, float)) else "RECENT"
        title = _clean(latest.get("title") or latest.get("summary") or "Earthquake", 120)
        latest = dict(latest)
        latest["title"] = f"{magnitude_text} · {title}"
        output.append(_event_signal(latest, label="LATEST EARTHQUAKE", priority=10))
        output.append(_signal(
            signal_id="events.earthquakes-14d",
            category="earth_systems",
            label="M4.5+ EARTHQUAKES",
            value=f"{len(earthquakes)} IN 14 DAYS",
            source="USGS Earthquake Hazards Program",
            status=count_status,
            destination="/platform/site-intelligence/",
            updated_at=generated_at,
            detail="Count of verified USGS earthquake records included in the current 14-day public event window.",
            priority=20,
            data_state=delivery,
        ))

    natural = [item for item in records if item.get("category") in NATURAL_EVENT_CATEGORIES]
    if natural:
        output.append(_event_signal(natural[0], label="OPEN NATURAL EVENT", priority=30))
        natural_counts = Counter(str(item.get("category")) for item in natural)
        leading = ", ".join(
            f"{name.replace('-', ' ').upper()} {count}"
            for name, count in natural_counts.most_common(3)
        )
        output.append(_signal(
            signal_id="events.natural-open",
            category="earth_systems",
            label="NATURAL EVENTS",
            value=f"{len(natural)} OPEN · {leading}" if leading else f"{len(natural)} OPEN",
            source="NASA EONET",
            status=count_status,
            destination="/platform/site-intelligence/",
            updated_at=generated_at,
            detail="Open NASA EONET natural-event records represented in the current public event snapshot.",
            priority=40,
            data_state=delivery,
        ))

    humanitarian = [item for item in records if item.get("category") in {"humanitarian", "displacement", "conflict"}]
    if humanitarian:
        output.append(_event_signal(humanitarian[0], label="LATEST HUMANITARIAN REPORT", priority=50))
        output.append(_signal(
            signal_id="events.humanitarian-14d",
            category="human_systems",
            label="HUMANITARIAN REPORTS",
            value=f"{len(humanitarian)} IN 14 DAYS",
            source="ReliefWeb",
            status=count_status,
            destination="/platform/site-intelligence/",
            updated_at=generated_at,
            detail="Count of indexed ReliefWeb public reports and related humanitarian records in the current window.",
            priority=60,
            data_state=delivery,
        ))

    return output, {
        "data_state": delivery,
        "source_states": payload.get("source_states") or {},
        "event_count": len(records),
        "category_counts": dict(counts),
    }


def _weather_signals(settings: Settings) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Use NOAA/NWS only when the connector produced live or cached source data."""
    try:
        payload = AdvancedExternalDataHub(settings).noaa_weather_climate()
    except Exception as exc:
        return [], {"data_state": "unavailable", "error": exc.__class__.__name__}

    source = str(payload.get("source") or "")
    cache = payload.get("cache") or {}
    cache_status = str(cache.get("status") or "")
    source_is_real = source and source.lower() != "sample"
    is_usable = bool(payload.get("live")) or (source_is_real and cache_status in {"hit", "stale"})
    if not is_usable:
        return [], {"data_state": "fallback-suppressed", "cache_status": cache_status}

    state = "stale" if cache_status == "stale" else ("cached" if cache_status == "hit" else "live")
    status = "stale" if state == "stale" else "current"
    generated_at = _now()
    indicators = {str(item.get("label") or "").lower(): item for item in (payload.get("indicators") or [])}
    output: list[dict[str, Any]] = []

    alert = next((item for key, item in indicators.items() if "alert" in key), None)
    if alert and isinstance(alert.get("value"), (int, float)):
        count = int(alert["value"])
        output.append(_signal(
            signal_id="weather.active-alerts",
            category="earth_systems",
            label="LOCAL WEATHER ALERTS",
            value=f"{count} ACTIVE" if count else "NONE ACTIVE",
            source=source,
            status="attention" if count else status,
            destination="https://www.weather.gov/alerts",
            source_url="https://www.weather.gov/alerts",
            updated_at=generated_at,
            detail=_clean(alert.get("interpretation") or payload.get("summary") or "NOAA/NWS alert context."),
            priority=5 if count else 70,
            data_state=state,
        ))

    temperature = next((item for key, item in indicators.items() if "temperature" in key), None)
    if temperature and isinstance(temperature.get("value"), (int, float)):
        output.append(_signal(
            signal_id="weather.forecast-temperature",
            category="earth_systems",
            label="SHORT-TERM TEMPERATURE",
            value=f"{float(temperature['value']):.1f} {temperature.get('unit') or '°C'}",
            source=source,
            status=status,
            destination="https://www.weather.gov/",
            source_url="https://www.weather.gov/",
            updated_at=generated_at,
            detail=_clean(temperature.get("interpretation") or payload.get("summary") or "NOAA/NWS forecast context."),
            priority=80,
            data_state=state,
        ))
    return output, {"data_state": state, "cache_status": cache_status}


def _deduplicate(signals: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    output: list[dict[str, Any]] = []
    for signal in sorted(signals, key=lambda item: (int(item.get("priority", 50)), item.get("signal_id", ""))):
        signal_id = str(signal.get("signal_id") or "")
        if not signal_id or signal_id in seen:
            continue
        seen.add(signal_id)
        output.append(signal)
    return output


def build_live_intelligence(settings: Settings, *, category: str = "", limit: int = 8) -> dict[str, Any]:
    generated_at = _now()
    requested = CATEGORY_ALIASES.get((category or "").strip().lower(), (category or "").strip().lower())
    limit = max(1, min(int(limit), 20))

    if requested == "platform":
        event_signals, event_meta = [], {"data_state": "not-requested", "source_states": {}}
        weather_signals, weather_meta = [], {"data_state": "not-requested"}
    elif bool(getattr(settings, "external_live", False)):
        # Event and NOAA/NWS collectors are independent and can each involve
        # multiple cache-safe public API calls. Run them concurrently so a cold
        # feed does not add their worst-case latency together.
        with ThreadPoolExecutor(max_workers=2, thread_name_prefix="scsi-live") as executor:
            event_future = executor.submit(_event_signals, settings)
            weather_future = executor.submit(_weather_signals, settings)
            event_signals, event_meta = event_future.result()
            weather_signals, weather_meta = weather_future.result()
    else:
        event_signals, event_meta = _event_signals(settings)
        weather_signals, weather_meta = _weather_signals(settings)
    signals = _deduplicate([*weather_signals, *event_signals])

    # One operational item remains as a quiet end-of-feed confidence marker.
    signals.append(_signal(
        signal_id="platform.site-intelligence-api",
        category="platform",
        label="SITE INTELLIGENCE",
        value=f"v{APP_VERSION} CONNECTED",
        source="Sustainable Catalyst",
        status="current",
        destination="/platform/site-intelligence/",
        updated_at=generated_at,
        detail=RELEASE_NAME,
        priority=900,
        data_state="current",
    ))

    if requested:
        signals = [item for item in signals if item["category"] == requested]
    selected = signals[:limit]
    return {
        "ok": True,
        "version": APP_VERSION,
        "schema": SCHEMA_VERSION,
        "generated_at": generated_at,
        "category": requested or "all",
        "count": len(selected),
        "signals": selected,
        "feed_state": {
            "events": event_meta,
            "weather": weather_meta,
            "useful_signal_count": len([item for item in selected if item["category"] != "platform"]),
            "platform_signal_count": len([item for item in selected if item["category"] == "platform"]),
        },
        "display": {
            "label": "Live Intelligence",
            "theme": "electronic",
            "default_motion": "slow",
            "source_attribution_required": True,
            "freshness_required": True,
            "hover_pause_required": True,
        },
        "boundaries": [
            "Only verified live, cached, or stale public-source records are summarized.",
            "Demonstration fallback records and sample connector values are excluded from the ticker.",
            "Signals are informational and do not replace official emergency, legal, medical, or financial guidance.",
        ],
    }


def live_intelligence_status(settings: Settings) -> dict[str, Any]:
    payload = build_live_intelligence(settings, limit=20)
    return {
        "ok": True,
        "version": APP_VERSION,
        "schema": SCHEMA_VERSION,
        "signal_count": payload["count"],
        "useful_signal_count": payload["feed_state"]["useful_signal_count"],
        "generated_at": payload["generated_at"],
        "service": "available",
        "cache_safe": bool(settings.external_cache_enabled),
        "feed_state": payload["feed_state"],
    }
