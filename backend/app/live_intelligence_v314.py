"""Selectable, balanced public-interest ticker feed for Site Intelligence v3.7.2.

The feed combines verified public events, weather/environment observations,
open-research metadata, and periodic development indicators. Administrators
and shortcodes can select or exclude named feeds without exposing browser API
keys or overriding WordPress/Astra navigation and breadcrumb styling.
"""
from __future__ import annotations

from collections import Counter, defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from statistics import mean
from typing import Any, Iterable
from urllib.parse import urlencode

from .config import Settings
from .connectors.advanced_external import AdvancedExternalDataHub
from .connectors.external_data import ExternalDataHub
from .unified_live_events import unified_events
from .version import APP_VERSION, RELEASE_NAME
from .live_intelligence_source_operations_v320 import LiveIntelligenceSourceOperations
from .live_intelligence_clustering_v330 import (
    cluster_event_records, ranking_policy, select_ranked_signals, SCHEMA_VERSION as CLUSTERING_SCHEMA_VERSION,
)
from .live_intelligence_context_v340 import enrich_signal_links

SCHEMA_VERSION = "sc-site-intelligence-live-intelligence/1.4"
DEFAULT_SIGNAL_LIMIT = 16
MAX_SIGNAL_LIMIT = 24
DEFAULT_MAX_SIGNALS_PER_SOURCE = 2
MAX_CONFIGURABLE_SIGNALS_PER_SOURCE = 5
CATEGORY_LABELS = {
    "earth_systems": "Earth Systems",
    "human_systems": "Human Systems",
    "research": "Science & Research",
    "economy_resources": "Economy, Energy & Resources",
    "platform": "Platform",
}
SOURCE_SHORT_NAMES = {
    "NOAA / National Weather Service": "NOAA/NWS",
    "USGS Earthquake Hazards Program": "USGS",
    "NASA Earth Observatory Natural Event Tracker": "NASA EONET",
    "NASA EONET": "NASA EONET",
    "ReliefWeb": "ReliefWeb",
    "NASA POWER": "NASA POWER",
    "OpenAlex": "OpenAlex",
    "World Bank": "World Bank",
    "Sustainable Catalyst": "Sustainable Catalyst",
}
CATEGORY_ALIASES = {
    "all": "",
    "planet": "earth_systems",
    "earth": "earth_systems",
    "society": "human_systems",
    "humanitarian": "human_systems",
    "weather": "earth_systems",
    "economy": "economy_resources",
    "development": "economy_resources",
    "research": "research",
    "publications": "research",
    "platform": "platform",
}
NATURAL_EVENT_CATEGORIES = {
    "wildfire", "storm", "flood", "volcano", "extreme-heat", "drought",
}
FEED_REGISTRY = {
    "noaa_nws": {"label": "NOAA / National Weather Service", "category": "earth_systems"},
    "usgs_earthquakes": {"label": "USGS Earthquakes", "category": "earth_systems"},
    "nasa_eonet": {"label": "NASA EONET Natural Events", "category": "earth_systems"},
    "reliefweb": {"label": "ReliefWeb Humanitarian Reports", "category": "human_systems"},
    "nasa_power": {"label": "NASA POWER Observations", "category": "earth_systems"},
    "openalex": {"label": "OpenAlex Research", "category": "research"},
    "world_bank": {"label": "World Bank Indicators", "category": "economy_resources"},
    "platform_status": {"label": "Site Intelligence Platform Status", "category": "platform"},
}
DEFAULT_FEEDS = (
    "noaa_nws", "usgs_earthquakes", "nasa_eonet", "reliefweb",
    "nasa_power", "openalex", "world_bank", "platform_status",
)
FEED_ALIASES = {
    "noaa": "noaa_nws", "nws": "noaa_nws", "weather": "noaa_nws",
    "usgs": "usgs_earthquakes", "earthquake": "usgs_earthquakes", "earthquakes": "usgs_earthquakes",
    "eonet": "nasa_eonet", "natural_events": "nasa_eonet",
    "humanitarian": "reliefweb", "relief_web": "reliefweb",
    "power": "nasa_power", "climate": "nasa_power",
    "research": "openalex",
    "worldbank": "world_bank", "development": "world_bank",
    "platform": "platform_status", "status": "platform_status",
}


def _now_dt() -> datetime:
    return datetime.now(timezone.utc)


def _now() -> str:
    return _now_dt().isoformat()


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
        "value": _clean(value, 160),
        "unit": "",
        "status": status,
        "severity": "attention" if status in {"degraded", "stale", "attention"} else "informational",
        "source_name": _clean(source, 120),
        "source_short_name": _clean(SOURCE_SHORT_NAMES.get(_clean(source, 120), _clean(source, 48)), 48),
        "source_url": source_url if str(source_url).startswith(("https://", "http://")) else "",
        "updated_at": updated_at,
        "observed_at": observed_at or updated_at,
        "destination_url": destination,
        "detail": _clean(detail, 440),
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
    cluster_id = str(record.get("cluster_id") or record.get("id") or "event")
    signal = _signal(
        signal_id=f"event.{cluster_id}",
        category="human_systems" if record.get("category") in {"humanitarian", "displacement", "conflict"} else "earth_systems",
        label=label,
        value=_clean(record.get("title") or record.get("summary") or "Verified public event", 150),
        source=source,
        status=status,
        destination=_event_destination(record),
        source_url=str(record.get("source_url") or ""),
        updated_at=str(record.get("updated_at") or observed),
        observed_at=observed,
        detail=_clean(record.get("summary") or record.get("title") or "Public event record.", 440),
        priority=priority,
        data_state=state,
    )
    signal.update({
        "cluster_id": str(record.get("cluster_id") or ""),
        "cluster_size": int(record.get("cluster_size") or 1),
        "cluster_source_count": int(record.get("cluster_source_count") or 1),
        "corroborating_sources": list(record.get("corroborating_sources") or [source]),
        "cluster_confidence": float(record.get("cluster_confidence") or record.get("confidence") or 0.0),
        "cluster_reason": _clean(record.get("cluster_reason") or "single verified source record", 180),
        "cluster_source_urls": list(record.get("cluster_source_urls") or []),
        "cluster_member_ids": list(record.get("cluster_member_ids") or []),
        "event_category": _clean(record.get("category"), 80),
        "coordinates": list(record.get("coordinates") or [])[:2],
        "location_label": _clean(record.get("location_label") or (record.get("metadata") or {}).get("location"), 160),
        "country": _clean(record.get("country") or (record.get("metadata") or {}).get("country"), 100),
        "country_code": _clean(record.get("country_code") or (record.get("metadata") or {}).get("country_code"), 12).upper(),
        "region": _clean(record.get("region") or (record.get("metadata") or {}).get("region"), 100),
        "magnitude": record.get("magnitude"),
    })
    return signal


def _record_places(records: Iterable[dict[str, Any]]) -> list[str]:
    places: set[str] = set()
    for record in records:
        metadata = record.get("metadata") or {}
        for candidate in (
            record.get("country"), record.get("location_label"), record.get("region"),
            metadata.get("country"), metadata.get("country_name"), metadata.get("region"),
        ):
            value = _clean(candidate, 80)
            if value and value.lower() not in {"global", "unknown", "none"}:
                places.add(value)
                break
    return sorted(places)


def _event_signals(settings: Settings) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not bool(getattr(settings, "external_live", False)):
        return [], {"data_state": "live-disabled", "source_states": {}}
    try:
        payload = unified_events(days=14, limit=200, allow_fallback=False)
    except Exception as exc:
        return [], {"data_state": "unavailable", "source_states": {}, "error": exc.__class__.__name__}

    records = [
        item for item in (payload.get("events") or [])
        if item.get("source") != "local-fallback"
        and item.get("data_state") != "fallback"
        and not (item.get("metadata") or {}).get("fabricated_for_demo")
    ]
    records.sort(key=lambda item: str(item.get("observed_at") or item.get("updated_at") or ""), reverse=True)
    raw_record_count = len(records)
    if bool(getattr(settings, "live_intelligence_clustering_enabled", True)):
        records, clustering = cluster_event_records(
            records,
            time_window_hours=int(getattr(settings, "live_intelligence_cluster_time_window_hours", 72)),
            distance_km=float(getattr(settings, "live_intelligence_cluster_distance_km", 300.0)),
            text_similarity=float(getattr(settings, "live_intelligence_cluster_text_similarity", 0.34)),
        )
    else:
        clustering = {
            "schema": CLUSTERING_SCHEMA_VERSION,
            "version": APP_VERSION,
            "enabled": False,
            "input_records": len(records),
            "canonical_events": len(records),
            "duplicates_suppressed": 0,
            "multi_source_clusters": 0,
        }
    counts = Counter(str(item.get("category") or "other") for item in records)
    delivery = str(payload.get("delivery_state") or payload.get("data_state") or "unavailable")
    count_status = "stale" if delivery == "stale" else "current"
    generated_at = str(payload.get("generated_at") or _now())
    output: list[dict[str, Any]] = []

    earthquakes = [item for item in records if item.get("category") == "earthquake"]
    if earthquakes:
        latest = dict(earthquakes[0])
        magnitude = latest.get("magnitude")
        magnitude_text = f"M{float(magnitude):.1f}" if isinstance(magnitude, (int, float)) else "RECENT"
        latest["title"] = f"{magnitude_text} · {_clean(latest.get('title') or latest.get('summary') or 'Earthquake', 120)}"
        output.append(_event_signal(latest, label="LATEST EARTHQUAKE", priority=10))

        strongest = max(
            (item for item in earthquakes if isinstance(item.get("magnitude"), (int, float))),
            key=lambda item: float(item.get("magnitude") or 0),
            default=None,
        )
        if strongest and strongest.get("id") != latest.get("id"):
            strongest_copy = dict(strongest)
            strongest_copy["title"] = f"M{float(strongest_copy['magnitude']):.1f} · {_clean(strongest_copy.get('title') or 'Earthquake', 120)}"
            output.append(_event_signal(strongest_copy, label="STRONGEST EARTHQUAKE · 14D", priority=18))

        output.append(_signal(
            signal_id="events.earthquakes-14d",
            category="earth_systems",
            label="M4.5+ EARTHQUAKES",
            value=f"{len(earthquakes)} IN 14 DAYS",
            source="USGS Earthquake Hazards Program",
            status=count_status,
            destination="https://earthquake.usgs.gov/earthquakes/map/",
            source_url="https://earthquake.usgs.gov/earthquakes/map/",
            updated_at=generated_at,
            detail="Verified USGS earthquake records represented in the current 14-day event window.",
            priority=24,
            data_state=delivery,
        ))

    natural = [item for item in records if item.get("category") in NATURAL_EVENT_CATEGORIES]
    if natural:
        output.append(_event_signal(natural[0], label="OPEN NATURAL EVENT", priority=30))
        natural_counts = Counter(str(item.get("category")) for item in natural)
        leading = " · ".join(
            f"{name.replace('-', ' ').upper()} {count}"
            for name, count in natural_counts.most_common(4)
        )
        output.append(_signal(
            signal_id="events.natural-open",
            category="earth_systems",
            label="NATURAL EVENTS",
            value=f"{len(natural)} OPEN · {leading}" if leading else f"{len(natural)} OPEN",
            source="NASA EONET",
            status=count_status,
            destination="https://eonet.gsfc.nasa.gov/",
            source_url="https://eonet.gsfc.nasa.gov/",
            updated_at=generated_at,
            detail="Open NASA EONET natural-event records in the current public snapshot.",
            priority=40,
            data_state=delivery,
        ))
        top_category, top_count = natural_counts.most_common(1)[0]
        output.append(_signal(
            signal_id=f"events.natural-leading-{top_category}",
            category="earth_systems",
            label="LEADING NATURAL-EVENT TYPE",
            value=f"{top_category.replace('-', ' ').upper()} · {top_count} OPEN",
            source="NASA EONET",
            status=count_status,
            destination="https://eonet.gsfc.nasa.gov/",
            source_url="https://eonet.gsfc.nasa.gov/",
            updated_at=generated_at,
            detail="Most represented open NASA EONET category in the current event snapshot.",
            priority=52,
            data_state=delivery,
        ))

    humanitarian = [item for item in records if item.get("category") in {"humanitarian", "displacement", "conflict"}]
    if humanitarian:
        output.append(_event_signal(humanitarian[0], label="LATEST HUMANITARIAN REPORT", priority=14))
        output.append(_signal(
            signal_id="events.humanitarian-14d",
            category="human_systems",
            label="HUMANITARIAN REPORTS",
            value=f"{len(humanitarian)} IN 14 DAYS",
            source="ReliefWeb",
            status=count_status,
            destination="https://reliefweb.int/updates",
            source_url="https://reliefweb.int/updates",
            updated_at=generated_at,
            detail="Indexed ReliefWeb reports and related humanitarian records in the current window.",
            priority=34,
            data_state=delivery,
        ))
        places = _record_places(humanitarian)
        if places:
            preview = ", ".join(places[:4])
            suffix = f" +{len(places) - 4}" if len(places) > 4 else ""
            output.append(_signal(
                signal_id="events.humanitarian-coverage",
                category="human_systems",
                label="HUMANITARIAN COVERAGE",
                value=f"{len(places)} LOCATIONS · {preview}{suffix}",
                source="ReliefWeb",
                status=count_status,
                destination="https://reliefweb.int/updates",
                source_url="https://reliefweb.int/updates",
                updated_at=generated_at,
                detail="Distinct named locations represented in the current ReliefWeb event window; not a completeness measure.",
                priority=62,
                data_state=delivery,
            ))

    return output, {
        "data_state": delivery,
        "source_states": payload.get("source_states") or {},
        "event_count": len(records),
        "raw_event_count": raw_record_count,
        "category_counts": dict(counts),
        "clustering": clustering,
    }


def _weather_signals(settings: Settings) -> tuple[list[dict[str, Any]], dict[str, Any]]:
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
            priority=72,
            data_state=state,
        ))
    return output, {"data_state": state, "cache_status": cache_status}


def _average_parameter(parameters: dict[str, Any], key: str) -> float | None:
    values: list[float] = []
    for value in (parameters.get(key) or {}).values():
        try:
            values.append(float(value))
        except (TypeError, ValueError):
            continue
    return round(mean(values), 2) if values else None


def _nasa_power_signals(settings: Settings) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    end_dt = _now_dt() - timedelta(days=1)
    start_dt = end_dt - timedelta(days=6)
    try:
        payload = ExternalDataHub(settings).nasa_power_timeseries(
            start=start_dt.strftime("%Y%m%d"),
            end=end_dt.strftime("%Y%m%d"),
            parameters=["T2M", "PRECTOTCORR", "WS10M", "ALLSKY_SFC_SW_DWN"],
        )
    except Exception as exc:
        return [], {"data_state": "unavailable", "error": exc.__class__.__name__}

    source = str(payload.get("source") or "")
    cache_status = str((payload.get("cache") or {}).get("status") or "")
    usable = source == "NASA POWER" and (bool(payload.get("live")) or cache_status in {"hit", "stale"})
    if not usable:
        return [], {"data_state": "fallback-suppressed", "cache_status": cache_status}
    state = "stale" if cache_status == "stale" else ("cached" if cache_status == "hit" else "live")
    status = "stale" if state == "stale" else "current"
    updated_at = _now()
    params = payload.get("parameters") or {}
    values = {
        "T2M": (_average_parameter(params, "T2M"), "RECENT MEAN TEMPERATURE", "°C"),
        "PRECTOTCORR": (_average_parameter(params, "PRECTOTCORR"), "RECENT PRECIPITATION", "MM/DAY"),
        "ALLSKY_SFC_SW_DWN": (_average_parameter(params, "ALLSKY_SFC_SW_DWN"), "SOLAR RESOURCE", "KWH/M²/DAY"),
    }
    output: list[dict[str, Any]] = []
    for index, (key, (value, label, unit)) in enumerate(values.items()):
        if value is None:
            continue
        output.append(_signal(
            signal_id=f"nasa-power.{key.lower()}",
            category="earth_systems",
            label=label,
            value=f"{value:.2f} {unit} · 7D AVG",
            source="NASA POWER",
            status=status,
            destination="https://power.larc.nasa.gov/",
            source_url="https://power.larc.nasa.gov/",
            updated_at=updated_at,
            observed_at=end_dt.isoformat(),
            detail=f"Seven-day average near {settings.external_default_latitude:.4f}, {settings.external_default_longitude:.4f}; observational context, not a forecast.",
            priority=84 + index,
            data_state=state,
        ))
    return output, {"data_state": state, "cache_status": cache_status, "window": f"{start_dt.date()}/{end_dt.date()}"}


def _openalex_signals(settings: Settings) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    since = (_now_dt() - timedelta(days=45)).date().isoformat()
    params = {
        "search": "sustainability climate resilience",
        "filter": f"from_publication_date:{since},is_oa:true",
        "sort": "publication_date:desc",
        "per-page": "5",
    }
    url = f"{settings.openalex_base_url.rstrip('/')}/works?{urlencode(params)}"
    hub = ExternalDataHub(settings)
    if not settings.external_live or not settings.public_connector_live_checks:
        return [], {"data_state": "live-disabled"}

    def fetcher() -> dict[str, Any]:
        payload, latency = hub._http_json(url)  # shared public connector boundary
        if not isinstance(payload, dict):
            raise ValueError("Unexpected OpenAlex response")
        return {"source": "OpenAlex", "live": True, "latency_ms": latency, "payload": payload}

    try:
        wrapped = hub._cached_or_fetch(f"live-intelligence:openalex:{since}", "openalex", fetcher)
    except Exception as exc:
        return [], {"data_state": "unavailable", "error": exc.__class__.__name__}
    cache_status = str((wrapped.get("cache") or {}).get("status") or "")
    state = "stale" if cache_status == "stale" else ("cached" if cache_status == "hit" else "live")
    payload = wrapped.get("payload") or {}
    works = [item for item in (payload.get("results") or []) if isinstance(item, dict) and item.get("title")]
    output: list[dict[str, Any]] = []
    if works:
        work = works[0]
        destination = str(work.get("doi") or work.get("id") or "https://openalex.org/")
        source_name = (((work.get("primary_location") or {}).get("source") or {}).get("display_name") or "OpenAlex")
        output.append(_signal(
            signal_id=f"research.openalex.{str(work.get('id') or 'latest').rsplit('/', 1)[-1]}",
            category="research",
            label="LATEST OPEN RESEARCH",
            value=_clean(work.get("title"), 155),
            source=f"OpenAlex · {source_name}",
            status="stale" if state == "stale" else "current",
            destination=destination if destination.startswith(("http://", "https://")) else "https://openalex.org/",
            source_url=destination if destination.startswith(("http://", "https://")) else "https://openalex.org/",
            updated_at=_now(),
            observed_at=str(work.get("publication_date") or _now()),
            detail="Open-access research metadata selected by recency and topic query; inclusion is not an authority endorsement.",
            priority=44,
            data_state=state,
        ))
    total = (payload.get("meta") or {}).get("count")
    if isinstance(total, int):
        output.append(_signal(
            signal_id="research.openalex.recent-count",
            category="research",
            label="OPEN RESEARCH INDEX",
            value=f"{total:,} MATCHING WORKS SINCE {since}",
            source="OpenAlex",
            status="stale" if state == "stale" else "current",
            destination="https://openalex.org/works",
            source_url="https://openalex.org/works",
            updated_at=_now(),
            detail="Query-result count for recent open-access works matching the ticker's sustainability, climate, and resilience terms.",
            priority=76,
            data_state=state,
        ))
    return output, {"data_state": state, "result_count": len(works), "query_count": total}


def _world_bank_indicator(settings: Settings, indicator: str) -> tuple[dict[str, Any] | None, str]:
    params = urlencode({"format": "json", "per_page": 10})
    url = f"{settings.world_bank_base_url.rstrip('/')}/country/WLD/indicator/{indicator}?{params}"
    hub = ExternalDataHub(settings)

    def fetcher() -> dict[str, Any]:
        payload, latency = hub._http_json(url)
        if not isinstance(payload, list) or len(payload) < 2:
            raise ValueError("Unexpected World Bank response")
        return {"source": "World Bank", "live": True, "latency_ms": latency, "payload": payload}

    wrapped = hub._cached_or_fetch(f"live-intelligence:world-bank:{indicator}", "world-bank", fetcher)
    cache_status = str((wrapped.get("cache") or {}).get("status") or "")
    rows = (wrapped.get("payload") or [None, []])[1] or []
    record = next((item for item in rows if isinstance(item, dict) and item.get("value") is not None), None)
    return record, cache_status


def _world_bank_signals(settings: Settings) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not settings.external_live or not settings.public_connector_live_checks:
        return [], {"data_state": "live-disabled"}
    specs = [
        ("SP.POP.GROW", "WORLD POPULATION GROWTH", "% ANNUAL"),
        ("EG.FEC.RNEW.ZS", "RENEWABLE ENERGY SHARE", "% OF FINAL CONSUMPTION"),
    ]
    output: list[dict[str, Any]] = []
    states: list[str] = []
    errors: list[str] = []
    with ThreadPoolExecutor(max_workers=2, thread_name_prefix="scsi-world-bank") as executor:
        futures = {executor.submit(_world_bank_indicator, settings, indicator): (indicator, label, unit) for indicator, label, unit in specs}
        for future, (indicator, label, unit) in futures.items():
            try:
                record, cache_status = future.result()
            except Exception as exc:
                errors.append(f"{indicator}:{exc.__class__.__name__}")
                continue
            if not record:
                continue
            state = "stale" if cache_status == "stale" else ("cached" if cache_status == "hit" else "live")
            states.append(state)
            try:
                value = float(record.get("value"))
            except (TypeError, ValueError):
                continue
            year = str(record.get("date") or "")
            output.append(_signal(
                signal_id=f"world-bank.{indicator.lower()}",
                category="economy_resources",
                label=label,
                value=f"{value:.2f} {unit} · DATA YEAR {year}",
                source="World Bank",
                status="stale" if state == "stale" else "current",
                destination=f"https://data.worldbank.org/indicator/{indicator}",
                source_url=f"https://data.worldbank.org/indicator/{indicator}",
                updated_at=_now(),
                observed_at=f"{year}-12-31T00:00:00+00:00" if year.isdigit() else _now(),
                detail="Periodic global indicator; the data year is shown explicitly and should not be read as a real-time measurement.",
                priority=88 if indicator == "SP.POP.GROW" else 90,
                data_state=state,
            ))
    aggregate = "stale" if "stale" in states else ("cached" if "cached" in states else ("live" if states else "unavailable"))
    return output, {"data_state": aggregate, "indicator_count": len(output), "errors": errors}


def _normalize_feed_ids(value: str | Iterable[str] | None, *, use_defaults: bool = False) -> list[str]:
    if value is None or value == "":
        return list(DEFAULT_FEEDS) if use_defaults else []
    if isinstance(value, str):
        raw = value.replace(";", ",").split(",")
    else:
        raw = list(value)
    normalized: list[str] = []
    for item in raw:
        feed_id = str(item or "").strip().lower().replace("-", "_").replace(" ", "_")
        if not feed_id:
            continue
        if feed_id == "all":
            return list(FEED_REGISTRY)
        feed_id = FEED_ALIASES.get(feed_id, feed_id)
        if feed_id in FEED_REGISTRY and feed_id not in normalized:
            normalized.append(feed_id)
    return normalized


def _signal_feed_id(signal: dict[str, Any]) -> str:
    signal_id = str(signal.get("signal_id") or "").lower()
    source = str(signal.get("source_name") or "").lower()
    if signal_id.startswith("platform.") or "sustainable catalyst" in source:
        return "platform_status"
    if signal_id.startswith("weather.") or "weather service" in source or source.startswith("noaa"):
        return "noaa_nws"
    if "earthquake" in signal_id or "usgs" in source:
        return "usgs_earthquakes"
    if "natural" in signal_id or "eonet" in source:
        return "nasa_eonet"
    if "humanitarian" in signal_id or "reliefweb" in source:
        return "reliefweb"
    if signal_id.startswith("nasa-power.") or "nasa power" in source:
        return "nasa_power"
    if signal_id.startswith("research.openalex.") or "openalex" in source:
        return "openalex"
    if signal_id.startswith("world-bank.") or "world bank" in source:
        return "world_bank"
    return ""


def _apply_feed_selection(signals: Iterable[dict[str, Any]], active_feeds: set[str]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for source_signal in signals:
        signal = dict(source_signal)
        feed_id = _signal_feed_id(signal)
        if not feed_id or feed_id not in active_feeds:
            continue
        signal["feed_id"] = feed_id
        output.append(signal)
    return output


def _deduplicate(signals: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    output: list[dict[str, Any]] = []
    for signal in sorted(signals, key=lambda item: (int(item.get("priority", 50)), int(item.get("source_priority", 50)), item.get("signal_id", ""))):
        signal_id = str(signal.get("signal_id") or "")
        if not signal_id or signal_id in seen:
            continue
        seen.add(signal_id)
        output.append(signal)
    return output


def _balanced_selection(
    signals: Iterable[dict[str, Any]],
    limit: int,
    *,
    max_per_source: int = DEFAULT_MAX_SIGNALS_PER_SOURCE,
) -> list[dict[str, Any]]:
    """Limit source repetition and round-robin categories after urgent items."""
    ordered = _deduplicate(signals)
    max_per_source = max(1, min(int(max_per_source), MAX_CONFIGURABLE_SIGNALS_PER_SOURCE))
    source_counts: Counter[str] = Counter()
    eligible: list[dict[str, Any]] = []
    for signal in ordered:
        source = str(signal.get("source_name") or "Unknown")
        if source_counts[source] >= max_per_source:
            continue
        source_counts[source] += 1
        eligible.append(signal)

    chosen: list[dict[str, Any]] = []
    chosen_ids: set[str] = set()
    for signal in eligible:
        if signal.get("severity") != "attention":
            continue
        chosen.append(signal)
        chosen_ids.add(str(signal["signal_id"]))
        if len(chosen) >= min(3, limit):
            break

    queues: dict[str, deque[dict[str, Any]]] = defaultdict(deque)
    for signal in eligible:
        if str(signal.get("signal_id")) in chosen_ids:
            continue
        queues[str(signal.get("category") or "other")].append(signal)
    category_order = ["earth_systems", "human_systems", "research", "economy_resources", "platform"]
    category_order.extend(sorted(set(queues) - set(category_order)))
    while len(chosen) < limit and any(queues.values()):
        progressed = False
        for category in category_order:
            if len(chosen) >= limit:
                break
            queue = queues.get(category)
            if not queue:
                continue
            chosen.append(queue.popleft())
            progressed = True
        if not progressed:
            break
    return chosen[:limit]


def build_live_intelligence(
    settings: Settings,
    *,
    category: str = "",
    limit: int = DEFAULT_SIGNAL_LIMIT,
    feeds: str | Iterable[str] | None = None,
    exclude: str | Iterable[str] | None = None,
    max_per_source: int = DEFAULT_MAX_SIGNALS_PER_SOURCE,
    record_operations: bool = True,
) -> dict[str, Any]:
    generated_at = _now()
    requested = CATEGORY_ALIASES.get((category or "").strip().lower(), (category or "").strip().lower())
    limit = max(1, min(int(limit), MAX_SIGNAL_LIMIT))
    selected_feeds = _normalize_feed_ids(feeds, use_defaults=True)
    excluded_feeds = set(_normalize_feed_ids(exclude))
    active_feeds = {feed_id for feed_id in selected_feeds if feed_id not in excluded_feeds}

    source_operations = None
    source_configs: dict[str, dict[str, Any]] = {}
    if bool(getattr(settings, "live_source_operations_enabled", True)):
        try:
            source_operations = LiveIntelligenceSourceOperations(settings)
            source_configs = source_operations.effective_sources()
            active_feeds = {
                feed_id for feed_id in active_feeds
                if bool((source_configs.get(feed_id, {}).get("effective") or {}).get("enabled", True))
            }
        except (OSError, ValueError):
            source_operations = None
            source_configs = {}

    collectors: dict[str, Any] = {}
    if requested != "platform":
        event_feeds = {"usgs_earthquakes", "nasa_eonet", "reliefweb"}
        if active_feeds.intersection(event_feeds) and requested in {"", "earth_systems", "human_systems"}:
            collectors["events"] = _event_signals
        if "noaa_nws" in active_feeds and requested in {"", "earth_systems"}:
            collectors["weather"] = _weather_signals
        if "nasa_power" in active_feeds and requested in {"", "earth_systems"}:
            collectors["nasa_power"] = _nasa_power_signals
        if "openalex" in active_feeds and requested in {"", "research"}:
            collectors["research"] = _openalex_signals
        if "world_bank" in active_feeds and requested in {"", "economy_resources"}:
            collectors["development"] = _world_bank_signals

    collector_results: dict[str, tuple[list[dict[str, Any]], dict[str, Any]]] = {}
    if bool(getattr(settings, "external_live", False)) and collectors:
        with ThreadPoolExecutor(max_workers=min(5, len(collectors)), thread_name_prefix="scsi-live") as executor:
            futures = {name: executor.submit(fn, settings) for name, fn in collectors.items()}
            for name, future in futures.items():
                try:
                    collector_results[name] = future.result()
                except Exception as exc:
                    collector_results[name] = ([], {"data_state": "unavailable", "error": exc.__class__.__name__})
    else:
        for name, fn in collectors.items():
            collector_results[name] = fn(settings)

    all_signals: list[dict[str, Any]] = []
    feed_state: dict[str, Any] = {}
    for name, (items, meta) in collector_results.items():
        all_signals.extend(items)
        feed_state[name] = meta

    if "platform_status" in active_feeds:
        all_signals.append(_signal(
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

    all_signals = _apply_feed_selection(all_signals, active_feeds)
    for signal in all_signals:
        source_config = source_configs.get(str(signal.get("feed_id") or ""), {})
        effective = source_config.get("effective") or {}
        signal["source_priority"] = int(effective.get("priority", 50) or 50)
    if requested:
        all_signals = [item for item in all_signals if item["category"] == requested]
    selected = (
        select_ranked_signals(all_signals, limit, max_per_source=max_per_source)
        if bool(getattr(settings, "live_intelligence_ranking_enabled", True))
        else _balanced_selection(all_signals, limit, max_per_source=max_per_source)
    )
    selected = enrich_signal_links(selected)
    present_feeds = Counter(str(item.get("feed_id") or "unknown") for item in selected)
    if source_operations is not None and record_operations:
        collector_for_feed = {
            "usgs_earthquakes": "events",
            "nasa_eonet": "events",
            "reliefweb": "events",
            "noaa_nws": "weather",
            "nasa_power": "nasa_power",
            "openalex": "research",
            "world_bank": "development",
        }
        generated_counts = Counter(str(item.get("feed_id") or "") for item in all_signals)
        for feed_id in active_feeds:
            if feed_id == "platform_status":
                source_operations.record_result(feed_id, ok=True, data_state="current", record_count=generated_counts.get(feed_id, 0))
                continue
            collector_name = collector_for_feed.get(feed_id)
            if collector_name not in collector_results:
                continue
            meta = collector_results[collector_name][1] or {}
            data_state = str(meta.get("data_state") or "empty")
            ok = data_state not in {"unavailable", "error"}
            source_operations.record_result(
                feed_id,
                ok=ok,
                data_state=data_state,
                record_count=generated_counts.get(feed_id, 0),
                error=str(meta.get("error") or "") if not ok else "",
            )

    operations_summary: dict[str, Any] = {"enabled": False}
    if source_operations is not None:
        source_registry = source_operations.registry(public=True)
        operations_summary = {
            "enabled": True,
            "schema": source_registry["schema"],
            "summary": source_registry["summary"],
            "source_count": source_registry["source_count"],
            "registry_url": "/public/live-intelligence/sources",
        }

    ranking_scores = [int(item.get("selection_score") or 0) for item in selected]
    cluster_signals = [item for item in selected if item.get("cluster_id")]
    feed_state.update({
        "useful_signal_count": len([item for item in selected if item["category"] != "platform"]),
        "platform_signal_count": len([item for item in selected if item["category"] == "platform"]),
        "source_counts": dict(Counter(str(item.get("source_name") or "Unknown") for item in selected)),
        "category_counts": dict(Counter(str(item.get("category") or "other") for item in selected)),
        "feed_counts": dict(present_feeds),
        "requested_feeds": selected_feeds,
        "excluded_feeds": sorted(excluded_feeds),
        "active_feeds": [feed_id for feed_id in FEED_REGISTRY if feed_id in active_feeds],
        "default_signal_limit": DEFAULT_SIGNAL_LIMIT,
        "maximum_signals_per_source": max(1, min(int(max_per_source), MAX_CONFIGURABLE_SIGNALS_PER_SOURCE)),
        "ranking": {
            "schema": CLUSTERING_SCHEMA_VERSION,
            "selected_count": len(selected),
            "highest_score": max(ranking_scores) if ranking_scores else 0,
            "lowest_score": min(ranking_scores) if ranking_scores else 0,
            "clustered_signal_count": len(cluster_signals),
            "multi_source_signal_count": len([item for item in cluster_signals if int(item.get("cluster_source_count") or 1) > 1]),
            "policy_url": "/public/live-intelligence/ranking-policy",
        },
    })
    return {
        "ok": True,
        "version": APP_VERSION,
        "schema": SCHEMA_VERSION,
        "generated_at": generated_at,
        "category": requested or "all",
        "count": len(selected),
        "signals": selected,
        "feeds": [
            {"id": feed_id, **metadata, "enabled": feed_id in active_feeds, "signal_count": present_feeds.get(feed_id, 0)}
            for feed_id, metadata in FEED_REGISTRY.items()
        ],
        "feed_state": feed_state,
        "source_operations": operations_summary,
        "display": {
            "label": "Live Intelligence",
            "theme": "electronic",
            "default_motion": "slow",
            "source_attribution_required": True,
            "freshness_required": True,
            "hover_pause_required": True,
            "theme_navigation_styles": "untouched",
            "feed_selection_supported": True,
            "readability_controls_supported": True,
            "source_operations_supported": True,
            "event_clustering_supported": True,
            "transparent_ranking_supported": True,
            "selection_reasons_supported": True,
            "signal_context_supported": True,
            "signal_evidence_download_supported": True,
            "signal_timeline_supported": True,
            "signal_map_context_supported": True,
            "decision_studio_handoff_supported": True,
            "category_labels": CATEGORY_LABELS,
            "default_desktop_cycle_seconds": 30,
            "default_mobile_cycle_seconds": 36,
            "default_signal_text_limit": 120,
        },
        "boundaries": [
            "Only verified live, cached, or stale public-source records are summarized.",
            "Demonstration fallback records and sample connector values are excluded from the ticker.",
            "Periodic indicators display their data year and are not described as real-time measurements.",
            "Clustering reduces duplicate presentation; it does not prove that a repeated report is accurate.",
            "Selection scores rank display relevance and are not danger, truth, or institutional-importance scores.",
            "Signals are informational and do not replace official emergency, legal, medical, or financial guidance.",
        ],
    }



def live_intelligence_ranking_policy() -> dict[str, Any]:
    """Return the public explainability contract for clustering and ranking."""
    return ranking_policy()

def live_intelligence_status(settings: Settings) -> dict[str, Any]:
    payload = build_live_intelligence(settings, limit=MAX_SIGNAL_LIMIT)
    return {
        "ok": True,
        "version": APP_VERSION,
        "schema": SCHEMA_VERSION,
        "signal_count": payload["count"],
        "useful_signal_count": payload["feed_state"]["useful_signal_count"],
        "generated_at": payload["generated_at"],
        "service": "available",
        "cache_safe": bool(settings.external_cache_enabled),
        "available_feeds": list(FEED_REGISTRY),
        "default_feeds": list(DEFAULT_FEEDS),
        "feed_state": payload["feed_state"],
    }
