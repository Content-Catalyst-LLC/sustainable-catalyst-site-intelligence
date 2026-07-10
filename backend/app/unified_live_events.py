from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json

VERSION = "1.17.0"

CATEGORY_ORDER = [
    "earthquake",
    "wildfire",
    "storm",
    "flood",
    "volcano",
    "extreme-heat",
    "drought",
    "humanitarian",
    "displacement",
    "conflict",
    "other",
]

CATEGORY_LABELS = {
    "earthquake": "Earthquakes",
    "wildfire": "Wildfires",
    "storm": "Storms",
    "flood": "Floods",
    "volcano": "Volcanic activity",
    "extreme-heat": "Extreme heat",
    "drought": "Drought",
    "humanitarian": "Humanitarian reports",
    "displacement": "Displacement",
    "conflict": "Conflict-related records",
    "other": "Other public events",
}

SOURCE_REGISTRY = {
    "usgs": {
        "name": "USGS Earthquake Hazards Program",
        "authority": "official-public-source",
        "license_note": "Public event feed; verify significant events against the original USGS record.",
    },
    "nasa-eonet": {
        "name": "NASA EONET",
        "authority": "official-public-aggregator",
        "license_note": "Public natural-event metadata aggregated from source agencies.",
    },
    "reliefweb": {
        "name": "ReliefWeb",
        "authority": "official-humanitarian-aggregator",
        "license_note": "Humanitarian reporting index; individual reports retain their originating publisher.",
    },
}

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _request_json(url: str, timeout: int = 10) -> Any:
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": f"Sustainable-Catalyst-Site-Intelligence/{VERSION}",
        },
    )
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))

def _stable_id(source: str, source_id: str, title: str, observed_at: str) -> str:
    digest = sha256(f"{source}|{source_id}|{title}|{observed_at}".encode("utf-8")).hexdigest()[:24]
    return f"sc:event:{digest}"

def _normalize_category(value: str | None) -> str:
    text = (value or "").strip().lower()
    if "earthquake" in text:
        return "earthquake"
    if "wildfire" in text or "fire" in text:
        return "wildfire"
    if "storm" in text or "cyclone" in text or "hurricane" in text or "typhoon" in text:
        return "storm"
    if "flood" in text:
        return "flood"
    if "volcano" in text:
        return "volcano"
    if "heat" in text:
        return "extreme-heat"
    if "drought" in text:
        return "drought"
    if "displacement" in text or "refugee" in text:
        return "displacement"
    if "conflict" in text or "violence" in text:
        return "conflict"
    if "humanitarian" in text or "emergency" in text or "appeal" in text:
        return "humanitarian"
    return "other"

def _severity_from_magnitude(magnitude: float | None) -> str:
    if magnitude is None:
        return "unknown"
    if magnitude >= 7:
        return "critical"
    if magnitude >= 6:
        return "high"
    if magnitude >= 5:
        return "moderate"
    return "low"

def _country_hint(title: str, coordinates: list[float] | None = None) -> str | None:
    text = title.lower()
    matches = {
        "kenya": "KEN",
        "ghana": "GHA",
        "india": "IND",
        "brazil": "BRA",
        "united states": "USA",
        "california": "USA",
        "alaska": "USA",
        "hawaii": "USA",
    }
    for token, code in matches.items():
        if token in text:
            return code
    return None

def _usgs_events(days: int = 7, limit: int = 200) -> list[dict[str, Any]]:
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=max(1, min(days, 30)))
    params = {
        "format": "geojson",
        "starttime": start.strftime("%Y-%m-%d"),
        "endtime": end.strftime("%Y-%m-%d"),
        "minmagnitude": 4.5,
        "orderby": "time",
        "limit": max(1, min(limit, 1000)),
    }
    payload = _request_json(f"https://earthquake.usgs.gov/fdsnws/event/1/query?{urlencode(params)}")
    records = []
    for feature in payload.get("features", []):
        properties = feature.get("properties") or {}
        geometry = feature.get("geometry") or {}
        coordinates = geometry.get("coordinates") or []
        if len(coordinates) < 2:
            continue
        milliseconds = properties.get("time")
        observed_at = datetime.fromtimestamp(milliseconds / 1000, tz=timezone.utc).isoformat() if milliseconds else _now()
        magnitude = properties.get("mag")
        source_id = str(feature.get("id") or properties.get("code") or observed_at)
        title = properties.get("title") or "Earthquake event"
        records.append({
            "id": _stable_id("usgs", source_id, title, observed_at),
            "source_event_id": source_id,
            "title": title,
            "summary": properties.get("place") or title,
            "category": "earthquake",
            "category_label": CATEGORY_LABELS["earthquake"],
            "source": "usgs",
            "source_name": SOURCE_REGISTRY["usgs"]["name"],
            "source_url": properties.get("url"),
            "observed_at": observed_at,
            "updated_at": datetime.fromtimestamp((properties.get("updated") or milliseconds) / 1000, tz=timezone.utc).isoformat() if milliseconds else observed_at,
            "coordinates": [float(coordinates[0]), float(coordinates[1])],
            "depth_km": float(coordinates[2]) if len(coordinates) > 2 and coordinates[2] is not None else None,
            "severity": _severity_from_magnitude(magnitude),
            "magnitude": magnitude,
            "confidence": 0.99,
            "status": properties.get("status") or "reviewed",
            "country_code": _country_hint(title, coordinates),
            "record_type": "observed-event",
            "data_state": "live",
            "metadata": {
                "alert": properties.get("alert"),
                "felt": properties.get("felt"),
                "tsunami": properties.get("tsunami"),
                "significance": properties.get("sig"),
            },
        })
    return records

def _eonet_events(days: int = 30, limit: int = 200) -> list[dict[str, Any]]:
    payload = _request_json(f"https://eonet.gsfc.nasa.gov/api/v3/events?status=open&days={max(1,min(days,365))}&limit={max(1,min(limit,500))}")
    records = []
    for event in payload.get("events", []):
        geometries = event.get("geometry") or []
        if not geometries:
            continue
        latest = geometries[-1]
        coordinates = latest.get("coordinates")
        if not isinstance(coordinates, list) or len(coordinates) < 2:
            continue
        category_title = ((event.get("categories") or [{}])[0].get("title") or "Natural event")
        category = _normalize_category(category_title)
        observed_at = latest.get("date") or _now()
        source_id = str(event.get("id") or observed_at)
        title = event.get("title") or category_title
        source_url = None
        sources = event.get("sources") or []
        if sources:
            source_url = sources[0].get("url")
        records.append({
            "id": _stable_id("nasa-eonet", source_id, title, observed_at),
            "source_event_id": source_id,
            "title": title,
            "summary": event.get("description") or category_title,
            "category": category,
            "category_label": CATEGORY_LABELS.get(category, CATEGORY_LABELS["other"]),
            "source": "nasa-eonet",
            "source_name": SOURCE_REGISTRY["nasa-eonet"]["name"],
            "source_url": source_url or event.get("link"),
            "observed_at": observed_at,
            "updated_at": observed_at,
            "coordinates": [float(coordinates[0]), float(coordinates[1])],
            "severity": "unknown",
            "magnitude": None,
            "confidence": 0.9,
            "status": "open",
            "country_code": _country_hint(title, coordinates),
            "record_type": "reported-event",
            "data_state": "live",
            "metadata": {
                "category_title": category_title,
                "geometry_type": latest.get("type"),
                "magnitude_value": latest.get("magnitudeValue"),
                "magnitude_unit": latest.get("magnitudeUnit"),
            },
        })
    return records

def _reliefweb_reports(days: int = 14, limit: int = 80) -> list[dict[str, Any]]:
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=max(1, min(days, 90)))
    params = {
        "appname": "sustainable-catalyst-site-intelligence",
        "limit": max(1, min(limit, 200)),
        "profile": "full",
        "sort[]": "date:desc",
        "filter[field]": "date.created",
        "filter[value][from]": start.strftime("%Y-%m-%dT00:00:00+00:00"),
        "filter[value][to]": end.strftime("%Y-%m-%dT23:59:59+00:00"),
    }
    payload = _request_json(f"https://api.reliefweb.int/v1/reports?{urlencode(params, doseq=True)}")
    records = []
    for item in payload.get("data", []):
        fields = item.get("fields") or {}
        title = fields.get("title") or "Humanitarian report"
        created = ((fields.get("date") or {}).get("created") or _now())
        countries = fields.get("country") or []
        country_code = None
        if countries:
            iso3 = countries[0].get("iso3")
            country_code = iso3.upper() if isinstance(iso3, str) else None
        records.append({
            "id": _stable_id("reliefweb", str(item.get("id")), title, created),
            "source_event_id": str(item.get("id")),
            "title": title,
            "summary": fields.get("body") or fields.get("headline") or "Humanitarian public report.",
            "category": "humanitarian",
            "category_label": CATEGORY_LABELS["humanitarian"],
            "source": "reliefweb",
            "source_name": SOURCE_REGISTRY["reliefweb"]["name"],
            "source_url": fields.get("url_alias") or item.get("href"),
            "observed_at": created,
            "updated_at": ((fields.get("date") or {}).get("changed") or created),
            "coordinates": None,
            "severity": "unknown",
            "magnitude": None,
            "confidence": 0.85,
            "status": "published",
            "country_code": country_code,
            "record_type": "published-report",
            "data_state": "live",
            "metadata": {
                "countries": [country.get("name") for country in countries if country.get("name")],
                "sources": [source.get("name") for source in (fields.get("source") or []) if source.get("name")],
                "format": [fmt.get("name") for fmt in (fields.get("format") or []) if fmt.get("name")],
            },
        })
    return records

def _fallback_events() -> list[dict[str, Any]]:
    now = datetime.now(timezone.utc)
    examples = [
        ("Demonstration earthquake record", "earthquake", [36.8, -1.2], "KEN"),
        ("Demonstration wildfire record", "wildfire", [-120.5, 38.2], "USA"),
        ("Demonstration humanitarian report", "humanitarian", None, "GHA"),
    ]
    output = []
    for index, (title, category, coordinates, country_code) in enumerate(examples):
        observed = (now - timedelta(hours=index * 7 + 2)).isoformat()
        output.append({
            "id": _stable_id("fallback", str(index), title, observed),
            "source_event_id": f"fallback-{index}",
            "title": title,
            "summary": "Demonstration fallback shown because one or more live event services were unavailable.",
            "category": category,
            "category_label": CATEGORY_LABELS[category],
            "source": "local-fallback",
            "source_name": "Sustainable Catalyst demonstration fallback",
            "source_url": None,
            "observed_at": observed,
            "updated_at": observed,
            "coordinates": coordinates,
            "severity": "unknown",
            "magnitude": None,
            "confidence": 0.0,
            "status": "demonstration",
            "country_code": country_code,
            "record_type": "demonstration-record",
            "data_state": "fallback",
            "metadata": {"fabricated_for_demo": True},
        })
    return output

def _deduplicate(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    output = []
    for record in sorted(records, key=lambda item: item.get("observed_at") or "", reverse=True):
        key = (
            record.get("source"),
            record.get("source_event_id"),
            record.get("title"),
        )
        if key in seen:
            continue
        seen.add(key)
        output.append(record)
    return output

def unified_events(
    *,
    days: int = 14,
    limit: int = 300,
    categories: list[str] | None = None,
    sources: list[str] | None = None,
    country_code: str | None = None,
) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    source_states: dict[str, str] = {}
    for source_id, loader in [
        ("usgs", lambda: _usgs_events(days=min(days, 30), limit=limit)),
        ("nasa-eonet", lambda: _eonet_events(days=max(days, 30), limit=limit)),
        ("reliefweb", lambda: _reliefweb_reports(days=days, limit=min(limit, 120))),
    ]:
        try:
            source_records = loader()
            records.extend(source_records)
            source_states[source_id] = "live"
        except Exception:
            source_states[source_id] = "unavailable"

    records = _deduplicate(records)
    if categories:
        wanted = {item.strip().lower() for item in categories if item.strip()}
        records = [item for item in records if item.get("category") in wanted]
    if sources:
        wanted_sources = {item.strip().lower() for item in sources if item.strip()}
        records = [item for item in records if item.get("source") in wanted_sources]
    if country_code:
        normalized_country = country_code.upper()
        records = [item for item in records if item.get("country_code") == normalized_country]

    if not records:
        records = _fallback_events()
        overall_state = "fallback"
    else:
        overall_state = "live" if all(value == "live" for value in source_states.values()) else "partial-live"

    records = records[:max(1, min(limit, 1000))]
    return {
        "ok": True,
        "version": VERSION,
        "generated_at": _now(),
        "data_state": overall_state,
        "source_states": source_states,
        "count": len(records),
        "events": records,
        "geojson": {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "id": record["id"],
                    "geometry": {"type": "Point", "coordinates": record["coordinates"]} if record.get("coordinates") else None,
                    "properties": {key: value for key, value in record.items() if key != "coordinates"},
                }
                for record in records if record.get("coordinates")
            ],
        },
    }

def categories_summary(days: int = 14) -> dict[str, Any]:
    payload = unified_events(days=days, limit=500)
    counts = Counter(item.get("category", "other") for item in payload["events"])
    return {
        "ok": True,
        "version": VERSION,
        "generated_at": payload["generated_at"],
        "data_state": payload["data_state"],
        "categories": [
            {
                "id": category,
                "label": CATEGORY_LABELS[category],
                "count": counts.get(category, 0),
            }
            for category in CATEGORY_ORDER
        ],
    }

def sources_summary(days: int = 14) -> dict[str, Any]:
    payload = unified_events(days=days, limit=500)
    counts = Counter(item.get("source") for item in payload["events"])
    return {
        "ok": True,
        "version": VERSION,
        "generated_at": payload["generated_at"],
        "data_state": payload["data_state"],
        "sources": [
            {
                "id": source_id,
                **metadata,
                "count": counts.get(source_id, 0),
                "state": payload["source_states"].get(source_id, "not-requested"),
            }
            for source_id, metadata in SOURCE_REGISTRY.items()
        ],
    }

def event_detail(event_id: str, days: int = 30) -> dict[str, Any] | None:
    payload = unified_events(days=days, limit=1000)
    for event in payload["events"]:
        if event["id"] == event_id:
            return {
                "ok": True,
                "version": VERSION,
                "generated_at": payload["generated_at"],
                "event": event,
                "interpretation": [
                    "This record reflects the originating public source and its update schedule.",
                    "Reported location and timing may change as source agencies revise the record.",
                    "The event is public context, not an operational alert or professional recommendation.",
                ],
            }
    return None

def timeline(days: int = 14, interval_hours: int = 24) -> dict[str, Any]:
    payload = unified_events(days=days, limit=1000)
    interval = max(1, min(interval_hours, 168))
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=max(1, min(days, 90)))
    buckets: list[dict[str, Any]] = []
    cursor = start
    while cursor < end:
        next_cursor = cursor + timedelta(hours=interval)
        bucket_events = []
        for event in payload["events"]:
            try:
                observed = datetime.fromisoformat((event.get("observed_at") or "").replace("Z", "+00:00"))
            except ValueError:
                continue
            if cursor <= observed < next_cursor:
                bucket_events.append(event["id"])
        buckets.append({
            "start": cursor.isoformat(),
            "end": next_cursor.isoformat(),
            "count": len(bucket_events),
            "event_ids": bucket_events,
        })
        cursor = next_cursor
    return {
        "ok": True,
        "version": VERSION,
        "generated_at": payload["generated_at"],
        "data_state": payload["data_state"],
        "interval_hours": interval,
        "buckets": buckets,
    }

def summary(days: int = 14) -> dict[str, Any]:
    payload = unified_events(days=days, limit=500)
    category_counts = Counter(item.get("category", "other") for item in payload["events"])
    source_counts = Counter(item.get("source", "unknown") for item in payload["events"])
    country_counts = Counter(item.get("country_code") for item in payload["events"] if item.get("country_code"))
    return {
        "ok": True,
        "version": VERSION,
        "generated_at": payload["generated_at"],
        "data_state": payload["data_state"],
        "event_count": payload["count"],
        "mapped_event_count": len(payload["geojson"]["features"]),
        "top_categories": [{"id": key, "label": CATEGORY_LABELS.get(key, key), "count": value} for key, value in category_counts.most_common(6)],
        "top_sources": [{"id": key, "name": SOURCE_REGISTRY.get(key, {}).get("name", key), "count": value} for key, value in source_counts.most_common(6)],
        "top_country_codes": [{"country_code": key, "count": value} for key, value in country_counts.most_common(10)],
        "source_states": payload["source_states"],
        "boundary": "Counts describe records returned by connected public sources. They do not represent complete incidence, severity, or causality.",
    }
