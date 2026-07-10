from __future__ import annotations

from datetime import datetime, timezone
from functools import lru_cache
import json
from .platform_core_integration import PlatformCoreClient, utc_now
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

VERSION = "1.17.0"

COUNTRIES: dict[str, dict[str, Any]] = {
    "KEN": {"name": "Kenya", "iso2": "KE", "region": "Sub-Saharan Africa", "capital": "Nairobi", "latitude": 0.0236, "longitude": 37.9062},
    "GHA": {"name": "Ghana", "iso2": "GH", "region": "Sub-Saharan Africa", "capital": "Accra", "latitude": 7.9465, "longitude": -1.0232},
    "USA": {"name": "United States", "iso2": "US", "region": "North America", "capital": "Washington, D.C.", "latitude": 37.0902, "longitude": -95.7129},
    "IND": {"name": "India", "iso2": "IN", "region": "South Asia", "capital": "New Delhi", "latitude": 20.5937, "longitude": 78.9629},
    "BRA": {"name": "Brazil", "iso2": "BR", "region": "Latin America and the Caribbean", "capital": "Brasília", "latitude": -14.2350, "longitude": -51.9253},
}

INDICATORS: list[dict[str, str]] = [
    {"id": "SP.POP.TOTL", "key": "population", "label": "Population", "unit": "people", "format": "compact", "domain": "Population"},
    {"id": "SP.DYN.LE00.IN", "key": "life_expectancy", "label": "Life expectancy", "unit": "years", "format": "decimal", "domain": "Health"},
    {"id": "NY.GDP.PCAP.CD", "key": "gdp_per_capita", "label": "GDP per capita", "unit": "current US$", "format": "currency", "domain": "Economy"},
    {"id": "EG.ELC.ACCS.ZS", "key": "electricity_access", "label": "Access to electricity", "unit": "% of population", "format": "percent", "domain": "Infrastructure"},
    {"id": "SH.H2O.BASW.ZS", "key": "water_access", "label": "Basic drinking water", "unit": "% of population", "format": "percent", "domain": "Water"},
    {"id": "SE.SEC.ENRR", "key": "secondary_enrollment", "label": "Secondary enrollment", "unit": "% gross", "format": "percent", "domain": "Education"},
    {"id": "EN.ATM.CO2E.PC", "key": "co2_per_capita", "label": "CO₂ emissions per capita", "unit": "metric tons", "format": "decimal", "domain": "Environment"},
    {"id": "SI.POV.GINI", "key": "gini", "label": "Gini index", "unit": "index", "format": "decimal", "domain": "Inequality"},
]

_RAW_SOURCE_PAYLOADS: dict[tuple[str, str], dict[str, Any]] = {}

FALLBACKS: dict[str, dict[str, Any]] = {
    "KEN": {
        "population": (55100586, 2023), "life_expectancy": (66.7, 2022),
        "gdp_per_capita": (2099.3, 2023), "electricity_access": (76.5, 2022),
        "water_access": (63.0, 2022), "secondary_enrollment": (60.4, 2022),
        "co2_per_capita": (0.4, 2020), "gini": (38.7, 2021),
    },
    "GHA": {
        "population": (34121985, 2023), "life_expectancy": (64.5, 2022),
        "gdp_per_capita": (2238.1, 2023), "electricity_access": (89.5, 2022),
        "water_access": (87.7, 2022), "secondary_enrollment": (77.7, 2022),
        "co2_per_capita": (0.6, 2020), "gini": (43.5, 2016),
    },
}

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _fetch_json(url: str, timeout: int = 9) -> Any:
    request = Request(url, headers={"User-Agent": "Sustainable-Catalyst-Site-Intelligence/1.17.0"})
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))

def _country(code: str) -> tuple[str, dict[str, Any]]:
    normalized = (code or "").strip().upper()
    if normalized not in COUNTRIES:
        raise ValueError("unsupported_country")
    return normalized, COUNTRIES[normalized]

def _world_bank_series(iso2: str, indicator_id: str, per_page: int = 30) -> list[dict[str, Any]]:
    url = f"https://api.worldbank.org/v2/country/{iso2}/indicator/{indicator_id}?{urlencode({'format':'json','per_page':per_page})}"
    payload = _fetch_json(url)
    _RAW_SOURCE_PAYLOADS[(iso2, indicator_id)] = {"payload": payload, "retrieved_at": utc_now(), "canonical_url": url}
    if not isinstance(payload, list) or len(payload) < 2 or not isinstance(payload[1], list):
        return []
    records = []
    for row in payload[1]:
        value = row.get("value")
        if value is None:
            continue
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            continue
        records.append({
            "year": int(row.get("date")),
            "value": numeric,
            "unit": row.get("unit") or "",
            "source_note": row.get("indicator", {}).get("value") or indicator_id,
        })
    records.sort(key=lambda item: item["year"])
    return records

@lru_cache(maxsize=64)
def _live_indicator_bundle(code: str) -> tuple[dict[str, Any], ...]:
    _, country = _country(code)
    results = []
    for definition in INDICATORS:
        try:
            series = _world_bank_series(country["iso2"], definition["id"])
        except Exception:
            series = []
        latest = series[-1] if series else None
        results.append({
            **definition,
            "latest": latest,
            "series": series[-12:],
            "source": "World Bank Open Data",
            "source_url": f"https://data.worldbank.org/indicator/{definition['id']}?locations={country['iso2']}",
            "data_state": "live" if latest else "unavailable",
        })
    return tuple(results)


def _attach_platform_core_lineage(
    code: str,
    country: dict[str, Any],
    definition: dict[str, str],
    record: dict[str, Any],
) -> dict[str, Any]:
    latest = record.get("latest")
    if not latest or record.get("data_state") != "live":
        record["lineage"] = {
            "platform_core_enabled": PlatformCoreClient().settings.enabled,
            "platform_core_state": "not-recorded",
            "reason": "Only live validated connector records are written to Platform Core.",
        }
        return record

    raw = _RAW_SOURCE_PAYLOADS.get((country["iso2"], definition["id"]))
    if not raw:
        record["lineage"] = {
            "platform_core_enabled": PlatformCoreClient().settings.enabled,
            "platform_core_state": "not-recorded",
            "reason": "Raw source response was unavailable for snapshotting.",
        }
        return record

    client = PlatformCoreClient()
    record["lineage"] = client.record_indicator_lineage(
        country_code=code,
        country_name=country["name"],
        indicator_id=definition["id"],
        indicator_key=definition["key"],
        indicator_label=definition["label"],
        canonical_url=raw["canonical_url"],
        retrieved_at=raw["retrieved_at"],
        raw_payload=raw["payload"],
        latest=latest,
        series=record.get("series") or [],
        source_name=record.get("source") or "World Bank Open Data",
    )
    return record


def _fallback_indicator(code: str, definition: dict[str, str]) -> dict[str, Any] | None:
    pair = FALLBACKS.get(code, {}).get(definition["key"])
    if not pair:
        return None
    value, year = pair
    return {
        **definition,
        "latest": {"year": year, "value": value, "unit": definition["unit"]},
        "series": [],
        "source": "World Bank reference snapshot",
        "source_url": f"https://data.worldbank.org/indicator/{definition['id']}",
        "data_state": "reference-snapshot",
    }

def country_indicators(code: str) -> dict[str, Any]:
    normalized, country = _country(code)
    live = list(_live_indicator_bundle(normalized))
    merged = []
    live_count = 0
    for definition, record in zip(INDICATORS, live):
        if record.get("latest"):
            live_count += 1
            merged.append(_attach_platform_core_lineage(normalized, country, definition, record))
        else:
            fallback = _fallback_indicator(normalized, definition) or record
            fallback["lineage"] = {
                "platform_core_enabled": PlatformCoreClient().settings.enabled,
                "platform_core_state": "not-recorded",
                "reason": "Reference snapshots are not published as live evidence.",
            }
            merged.append(fallback)
    available = [item for item in merged if item.get("latest")]
    state = "live" if live_count else ("reference-snapshot" if available else "unavailable")
    return {
        "ok": True,
        "version": VERSION,
        "generated_at": _now(),
        "country": {"code": normalized, **country},
        "data_state": state,
        "live_indicator_count": live_count,
        "available_indicator_count": len(available),
        "indicator_count": len(merged),
        "indicators": merged,
        "methodology": [
            "Latest non-null World Bank observation is used for each indicator.",
            "Reporting years differ by indicator and remain visible.",
            "Reference snapshots are labeled and used only when the live source is unavailable.",
            "No missing value is silently imputed.",
        ],
    }

def country_trends(code: str) -> dict[str, Any]:
    payload = country_indicators(code)
    return {
        "ok": True,
        "version": VERSION,
        "generated_at": payload["generated_at"],
        "country": payload["country"],
        "data_state": payload["data_state"],
        "trends": [
            {
                "id": item["id"],
                "key": item["key"],
                "label": item["label"],
                "unit": item["unit"],
                "format": item["format"],
                "source": item["source"],
                "series": item["series"],
            }
            for item in payload["indicators"] if item.get("series")
        ],
    }

def country_profile(code: str) -> dict[str, Any]:
    payload = country_indicators(code)
    country = payload["country"]
    indicators = payload["indicators"]
    latest = {item["key"]: item.get("latest") for item in indicators if item.get("latest")}
    highlights = []
    for item in indicators[:6]:
        if item.get("latest"):
            highlights.append({
                "key": item["key"], "label": item["label"], "value": item["latest"]["value"],
                "year": item["latest"]["year"], "unit": item["unit"], "format": item["format"],
                "source": item["source"], "data_state": item["data_state"], "lineage": item.get("lineage", {}),
            })
    return {
        "ok": True,
        "version": VERSION,
        "generated_at": payload["generated_at"],
        "country": country,
        "data_state": payload["data_state"],
        "summary": f"{country['name']} country intelligence combines live development indicators, satellite context, and recent public event records.",
        "highlights": highlights,
        "indicator_endpoint": f"/public/country/{country['code']}/indicators",
        "trends_endpoint": f"/public/country/{country['code']}/trends",
        "events_endpoint": f"/public/country/{country['code']}/events",
        "briefing": {
            "population": latest.get("population"),
            "life_expectancy": latest.get("life_expectancy"),
            "gdp_per_capita": latest.get("gdp_per_capita"),
            "electricity_access": latest.get("electricity_access"),
            "water_access": latest.get("water_access"),
        },
        "interpretation": [
            "Values are descriptive public indicators and do not constitute a national ranking.",
            "Indicators may refer to different reporting years and methodologies.",
            "Country context does not establish causality, eligibility, liability, or legal responsibility.",
        ],
    }

def country_brief(code: str) -> dict[str, Any]:
    profile = country_profile(code)
    country = profile["country"]
    highlights = profile["highlights"]
    paragraphs = []
    for item in highlights:
        paragraphs.append(
            f"{item['label']}: {item['value']} {item['unit']} ({item['year']}, {item['source']})."
        )
    return {
        "ok": True,
        "version": VERSION,
        "generated_at": profile["generated_at"],
        "country": country,
        "title": f"{country['name']} — Live Country Intelligence Brief",
        "summary": profile["summary"],
        "evidence_lines": paragraphs,
        "data_state": profile["data_state"],
        "boundary": "This brief organizes public evidence for orientation and research. Verify important findings against the linked source.",
    }
