from __future__ import annotations

from datetime import datetime, timezone
from functools import lru_cache
import json
from time import perf_counter
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .country_cache import country_cache
from .platform_core_integration import PlatformCoreClient, utc_now
from .version import APP_VERSION

VERSION = APP_VERSION

COUNTRIES: dict[str, dict[str, Any]] = {
    "KEN": {"name": "Kenya", "iso2": "KE", "region": "Sub-Saharan Africa", "capital": "Nairobi", "latitude": 0.0236, "longitude": 37.9062},
    "GHA": {"name": "Ghana", "iso2": "GH", "region": "Sub-Saharan Africa", "capital": "Accra", "latitude": 7.9465, "longitude": -1.0232},
    "USA": {"name": "United States", "iso2": "US", "region": "North America", "capital": "Washington, D.C.", "latitude": 37.0902, "longitude": -95.7129},
    "IND": {"name": "India", "iso2": "IN", "region": "South Asia", "capital": "New Delhi", "latitude": 20.5937, "longitude": 78.9629},
    "BRA": {"name": "Brazil", "iso2": "BR", "region": "Latin America and the Caribbean", "capital": "Brasília", "latitude": -14.2350, "longitude": -51.9253},
}

FALLBACK_COUNTRY_CATALOG: dict[str, dict[str, Any]] = {
    "ARG": {"name": "Argentina", "iso2": "AR", "region": "Latin America & Caribbean", "capital": "Buenos Aires", "latitude": -38.4161, "longitude": -63.6167},
    "AUS": {"name": "Australia", "iso2": "AU", "region": "East Asia & Pacific", "capital": "Canberra", "latitude": -25.2744, "longitude": 133.7751},
    "CAN": {"name": "Canada", "iso2": "CA", "region": "North America", "capital": "Ottawa", "latitude": 56.1304, "longitude": -106.3468},
    "CHN": {"name": "China", "iso2": "CN", "region": "East Asia & Pacific", "capital": "Beijing", "latitude": 35.8617, "longitude": 104.1954},
    "DEU": {"name": "Germany", "iso2": "DE", "region": "Europe & Central Asia", "capital": "Berlin", "latitude": 51.1657, "longitude": 10.4515},
    "EGY": {"name": "Egypt, Arab Rep.", "iso2": "EG", "region": "Middle East, North Africa, Afghanistan & Pakistan", "capital": "Cairo", "latitude": 26.8206, "longitude": 30.8025},
    "ESP": {"name": "Spain", "iso2": "ES", "region": "Europe & Central Asia", "capital": "Madrid", "latitude": 40.4637, "longitude": -3.7492},
    "ETH": {"name": "Ethiopia", "iso2": "ET", "region": "Sub-Saharan Africa", "capital": "Addis Ababa", "latitude": 9.1450, "longitude": 40.4897},
    "FRA": {"name": "France", "iso2": "FR", "region": "Europe & Central Asia", "capital": "Paris", "latitude": 46.2276, "longitude": 2.2137},
    "GBR": {"name": "United Kingdom", "iso2": "GB", "region": "Europe & Central Asia", "capital": "London", "latitude": 55.3781, "longitude": -3.4360},
    "IDN": {"name": "Indonesia", "iso2": "ID", "region": "East Asia & Pacific", "capital": "Jakarta", "latitude": -0.7893, "longitude": 113.9213},
    "JPN": {"name": "Japan", "iso2": "JP", "region": "East Asia & Pacific", "capital": "Tokyo", "latitude": 36.2048, "longitude": 138.2529},
    "MEX": {"name": "Mexico", "iso2": "MX", "region": "Latin America & Caribbean", "capital": "Mexico City", "latitude": 23.6345, "longitude": -102.5528},
    "NGA": {"name": "Nigeria", "iso2": "NG", "region": "Sub-Saharan Africa", "capital": "Abuja", "latitude": 9.0820, "longitude": 8.6753},
    "PAK": {"name": "Pakistan", "iso2": "PK", "region": "South Asia", "capital": "Islamabad", "latitude": 30.3753, "longitude": 69.3451},
    "RUS": {"name": "Russian Federation", "iso2": "RU", "region": "Europe & Central Asia", "capital": "Moscow", "latitude": 61.5240, "longitude": 105.3188},
    "SAU": {"name": "Saudi Arabia", "iso2": "SA", "region": "Middle East, North Africa, Afghanistan & Pakistan", "capital": "Riyadh", "latitude": 23.8859, "longitude": 45.0792},
    "ZAF": {"name": "South Africa", "iso2": "ZA", "region": "Sub-Saharan Africa", "capital": "Pretoria", "latitude": -30.5595, "longitude": 22.9375},
}

DISPLAY_NAMES = {
    "Egypt, Arab Rep.": "Egypt",
    "Iran, Islamic Rep.": "Iran",
    "Korea, Rep.": "South Korea",
    "Korea, Dem. People's Rep.": "North Korea",
    "Russian Federation": "Russia",
    "Venezuela, RB": "Venezuela",
    "Yemen, Rep.": "Yemen",
    "Congo, Dem. Rep.": "Democratic Republic of the Congo",
    "Congo, Rep.": "Republic of the Congo",
    "Gambia, The": "The Gambia",
    "Bahamas, The": "The Bahamas",
    "Lao PDR": "Laos",
    "Slovak Republic": "Slovakia",
    "Kyrgyz Republic": "Kyrgyzstan",
    "West Bank and Gaza": "Palestinian Territories",
}

SEARCH_ALIASES = {
    "COD": ["DR Congo", "DRC", "Congo-Kinshasa"],
    "COG": ["Congo-Brazzaville"],
    "KOR": ["Republic of Korea"],
    "PRK": ["DPRK"],
    "RUS": ["Russian Federation"],
    "USA": ["United States of America", "US", "U.S."],
    "GBR": ["Britain", "Great Britain", "UK", "U.K."],
    "VEN": ["Bolivarian Republic of Venezuela"],
    "PSE": ["Palestine", "West Bank and Gaza"],
}

TERRITORY_CODES = {
    "ABW", "ASM", "BMU", "CYM", "CUW", "FRO", "GIB", "GRL", "GUM", "HKG", "IMN", "MAC", "MNP", "NCL", "PRI", "PYF", "SXM", "TCA", "VGB", "VIR",
}

_COUNTRY_CATALOG_CACHE: dict[str, dict[str, Any]] | None = None
_COUNTRY_CATALOG_FETCHED_AT: str | None = None
_COUNTRY_CATALOG_STATE = "uninitialized"
_COUNTRY_CATALOG_TIMING_MS: float | None = None
_COUNTRY_DIAGNOSTICS: dict[str, dict[str, Any]] = {}
_RAW_SOURCE_PAYLOADS: dict[tuple[str, str], dict[str, Any]] = {}

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

FALLBACKS: dict[str, dict[str, Any]] = {
    "KEN": {
        "population": (55100586, 2023), "life_expectancy": (66.7, 2022), "gdp_per_capita": (2099.3, 2023),
        "electricity_access": (76.5, 2022), "water_access": (63.0, 2022), "secondary_enrollment": (60.4, 2022),
        "co2_per_capita": (0.4, 2020), "gini": (38.7, 2021),
    },
    "GHA": {
        "population": (34121985, 2023), "life_expectancy": (64.5, 2022), "gdp_per_capita": (2238.1, 2023),
        "electricity_access": (89.5, 2022), "water_access": (87.7, 2022), "secondary_enrollment": (77.7, 2022),
        "co2_per_capita": (0.6, 2020), "gini": (43.5, 2016),
    },
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _fetch_json(url: str, timeout: int = 9) -> Any:
    request = Request(url, headers={"User-Agent": f"Sustainable-Catalyst-Site-Intelligence/{VERSION}"})
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").split())


def _normalize_country(code: str, metadata: dict[str, Any]) -> dict[str, Any]:
    source_name = _clean_text(metadata.get("source_name") or metadata.get("name") or code)
    display_name = DISPLAY_NAMES.get(source_name, source_name)
    region = _clean_text(metadata.get("region")) or "Unclassified"
    aliases = []
    if source_name and source_name != display_name:
        aliases.append(source_name)
    aliases.extend(SEARCH_ALIASES.get(code, []))
    aliases = sorted({item for item in aliases if item and item != display_name})
    return {
        **metadata,
        "name": display_name,
        "display_name": display_name,
        "source_name": source_name,
        "region": region,
        "source_region": _clean_text(metadata.get("source_region") or metadata.get("region")) or None,
        "capital": _clean_text(metadata.get("capital")) or None,
        "alternate_names": aliases,
        "entity_type": "territory" if code in TERRITORY_CODES else "country-or-territory",
    }


def _catalog_from_world_bank() -> dict[str, dict[str, Any]]:
    url = "https://api.worldbank.org/v2/country?format=json&per_page=400"
    payload = _fetch_json(url, timeout=10)
    if not isinstance(payload, list) or len(payload) < 2 or not isinstance(payload[1], list):
        return {}
    catalog: dict[str, dict[str, Any]] = {}
    for row in payload[1]:
        iso3 = str(row.get("id") or "").upper()
        iso2 = str(row.get("iso2Code") or "").upper()
        region = row.get("region") or {}
        region_id = str(region.get("id") or "")
        region_name = _clean_text(region.get("value"))
        if len(iso3) != 3 or len(iso2) != 2 or region_id == "NA" or not region_name:
            continue
        try:
            longitude = float(row.get("longitude")) if row.get("longitude") not in (None, "") else None
            latitude = float(row.get("latitude")) if row.get("latitude") not in (None, "") else None
        except (TypeError, ValueError):
            longitude = None
            latitude = None
        catalog[iso3] = _normalize_country(iso3, {
            "name": row.get("name") or iso3,
            "iso2": iso2,
            "region": region_name,
            "income_level": _clean_text((row.get("incomeLevel") or {}).get("value")) or None,
            "lending_type": _clean_text((row.get("lendingType") or {}).get("value")) or None,
            "capital": row.get("capitalCity") or None,
            "longitude": longitude,
            "latitude": latitude,
            "source": "World Bank Country API",
        })
    return catalog


def _normalized_static_catalog() -> dict[str, dict[str, Any]]:
    merged = {**FALLBACK_COUNTRY_CATALOG, **COUNTRIES}
    return {code: _normalize_country(code, metadata) for code, metadata in merged.items()}


def country_catalog(force_refresh: bool = False) -> dict[str, Any]:
    global _COUNTRY_CATALOG_CACHE, _COUNTRY_CATALOG_FETCHED_AT, _COUNTRY_CATALOG_STATE, _COUNTRY_CATALOG_TIMING_MS
    if _COUNTRY_CATALOG_CACHE is None or force_refresh:
        started = perf_counter()
        live: dict[str, dict[str, Any]] = {}
        if not force_refresh:
            cached = country_cache.get(f"v{VERSION}:country-catalog", fresh_seconds=21600, stale_seconds=604800)
            if cached and isinstance(cached.value, dict):
                _COUNTRY_CATALOG_CACHE = cached.value
                _COUNTRY_CATALOG_FETCHED_AT = cached.stored_at
                _COUNTRY_CATALOG_STATE = cached.state
        if _COUNTRY_CATALOG_CACHE is None or force_refresh:
            try:
                live = _catalog_from_world_bank()
            except Exception:
                live = {}
            if live:
                live = {code: _normalize_country(code, metadata) for code, metadata in live.items()}
                merged = {**_normalized_static_catalog(), **live}
                _COUNTRY_CATALOG_CACHE = merged
                _COUNTRY_CATALOG_FETCHED_AT = country_cache.set(f"v{VERSION}:country-catalog", merged)
                _COUNTRY_CATALOG_STATE = "live"
            else:
                cached = country_cache.get(f"v{VERSION}:country-catalog", fresh_seconds=0, stale_seconds=604800)
                if cached and isinstance(cached.value, dict):
                    _COUNTRY_CATALOG_CACHE = cached.value
                    _COUNTRY_CATALOG_FETCHED_AT = cached.stored_at
                    _COUNTRY_CATALOG_STATE = "stale" if cached.stale else "cached"
                else:
                    _COUNTRY_CATALOG_CACHE = _normalized_static_catalog()
                    _COUNTRY_CATALOG_FETCHED_AT = _now()
                    _COUNTRY_CATALOG_STATE = "fallback-catalog"
        _COUNTRY_CATALOG_TIMING_MS = round((perf_counter() - started) * 1000, 2)
    countries = [
        {"code": code, **metadata}
        for code, metadata in sorted((_COUNTRY_CATALOG_CACHE or {}).items(), key=lambda item: item[1].get("name", item[0]))
    ]
    return {
        "ok": True,
        "version": VERSION,
        "generated_at": _now(),
        "catalog_fetched_at": _COUNTRY_CATALOG_FETCHED_AT,
        "data_state": _COUNTRY_CATALOG_STATE,
        "stale": _COUNTRY_CATALOG_STATE == "stale",
        "country_count": len(countries),
        "countries": countries,
        "cache": {"state": _COUNTRY_CATALOG_STATE, "retrieved_at": _COUNTRY_CATALOG_FETCHED_AT},
    }


def search_countries(query: str = "", region: str = "", limit: int = 50) -> dict[str, Any]:
    payload = country_catalog()
    q = _clean_text(query).lower()
    region_filter = _clean_text(region).lower()
    results = []
    for item in payload["countries"]:
        haystack = " ".join([
            item.get("name", ""), item.get("source_name", ""), item.get("code", ""), item.get("iso2", ""),
            " ".join(item.get("alternate_names") or []),
        ]).lower()
        if q and q not in haystack:
            continue
        if region_filter and region_filter not in str(item.get("region") or "").lower():
            continue
        results.append(item)
    results = results[:max(1, min(int(limit), 300))]
    return {
        "ok": True, "version": VERSION, "generated_at": _now(), "data_state": payload["data_state"],
        "query": query, "region": region, "count": len(results), "countries": results,
    }


def country_regions() -> dict[str, Any]:
    payload = country_catalog()
    counts: dict[str, int] = {}
    for item in payload["countries"]:
        name = _clean_text(item.get("region")) or "Unclassified"
        counts[name] = counts.get(name, 0) + 1
    return {
        "ok": True, "version": VERSION, "generated_at": _now(), "data_state": payload["data_state"],
        "regions": [{"name": name, "country_count": count} for name, count in sorted(counts.items())],
    }


def _country(code: str) -> tuple[str, dict[str, Any]]:
    normalized = _clean_text(code).upper()
    payload = country_catalog()
    match = next((item for item in payload["countries"] if item["code"] == normalized or item.get("iso2") == normalized), None)
    if not match:
        raise ValueError("unsupported_country")
    metadata = dict(match)
    normalized = metadata.pop("code")
    return normalized, metadata


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
            year = int(row.get("date"))
        except (TypeError, ValueError):
            continue
        records.append({"year": year, "value": numeric, "unit": row.get("unit") or "", "source_note": (row.get("indicator") or {}).get("value") or indicator_id})
    records.sort(key=lambda item: item["year"])
    return records


def _series_cache_key(iso2: str, indicator_id: str) -> str:
    return f"v{VERSION}:indicator:{iso2}:{indicator_id}"


def _indicator_series(iso2: str, indicator_id: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    key = _series_cache_key(iso2, indicator_id)
    fresh = country_cache.get(key, fresh_seconds=21600, stale_seconds=604800, allow_stale=False)
    if fresh and isinstance(fresh.value, list):
        return fresh.value, {"state": "cached", "retrieved_at": fresh.stored_at, "stale": False, "timing_ms": 0.0}
    started = perf_counter()
    try:
        series = _world_bank_series(iso2, indicator_id)
    except Exception:
        series = []
    timing = round((perf_counter() - started) * 1000, 2)
    if series:
        stored_at = country_cache.set(key, series)
        return series, {"state": "live", "retrieved_at": stored_at, "stale": False, "timing_ms": timing}
    stale = country_cache.get(key, fresh_seconds=0, stale_seconds=604800, allow_stale=True)
    if stale and isinstance(stale.value, list):
        return stale.value, {"state": "stale" if stale.stale else "cached", "retrieved_at": stale.stored_at, "stale": stale.stale, "timing_ms": timing}
    return [], {"state": "unavailable", "retrieved_at": None, "stale": False, "timing_ms": timing}


@lru_cache(maxsize=512)
def _live_indicator_bundle(code: str) -> tuple[dict[str, Any], ...]:
    normalized, country = _country(code)
    results = []
    diagnostics = {"indicator_timings_ms": {}, "cache_states": {}, "requested_at": _now()}
    for definition in INDICATORS:
        series, cache_meta = _indicator_series(country["iso2"], definition["id"])
        latest = series[-1] if series else None
        diagnostics["indicator_timings_ms"][definition["id"]] = cache_meta["timing_ms"]
        diagnostics["cache_states"][definition["id"]] = cache_meta["state"]
        results.append({
            **definition,
            "latest": latest,
            "series": series[-12:],
            "source_id": definition["id"],
            "source": "World Bank Open Data",
            "source_url": f"https://data.worldbank.org/indicator/{definition['id']}?locations={country['iso2']}",
            "data_state": cache_meta["state"] if latest else "unavailable",
            "cache_state": cache_meta["state"],
            "retrieved_at": cache_meta["retrieved_at"],
            "stale": cache_meta["stale"],
        })
    _COUNTRY_DIAGNOSTICS[normalized] = diagnostics
    return tuple(results)


def _attach_platform_core_lineage(code: str, country: dict[str, Any], definition: dict[str, str], record: dict[str, Any]) -> dict[str, Any]:
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
        country_code=code, country_name=country["name"], indicator_id=definition["id"], indicator_key=definition["key"],
        indicator_label=definition["label"], canonical_url=raw["canonical_url"], retrieved_at=raw["retrieved_at"],
        raw_payload=raw["payload"], latest=latest, series=record.get("series") or [], source_name=record.get("source") or "World Bank Open Data",
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
        "source_id": definition["id"],
        "source": "World Bank reference snapshot",
        "source_url": f"https://data.worldbank.org/indicator/{definition['id']}",
        "data_state": "reference-snapshot",
        "cache_state": "reference-snapshot",
        "retrieved_at": None,
        "stale": False,
    }


def country_indicators(code: str) -> dict[str, Any]:
    normalized, country = _country(code)
    live = list(_live_indicator_bundle(normalized))
    merged = []
    counts = {"live": 0, "cached": 0, "stale": 0, "reference-snapshot": 0, "unavailable": 0}
    for definition, record in zip(INDICATORS, live):
        if record.get("latest"):
            state = record.get("data_state") or "live"
            counts[state] = counts.get(state, 0) + 1
            merged.append(_attach_platform_core_lineage(normalized, country, definition, record))
        else:
            fallback = _fallback_indicator(normalized, definition) or record
            counts[fallback.get("data_state", "unavailable")] = counts.get(fallback.get("data_state", "unavailable"), 0) + 1
            fallback["lineage"] = {
                "platform_core_enabled": PlatformCoreClient().settings.enabled,
                "platform_core_state": "not-recorded",
                "reason": "Reference snapshots and unavailable records are not published as live evidence.",
            }
            merged.append(fallback)
    available = [item for item in merged if item.get("latest")]
    if counts["live"] == len(INDICATORS):
        state = "live"
    elif counts["live"] > 0:
        state = "partial-live"
    elif counts["cached"] > 0:
        state = "cached"
    elif counts["stale"] > 0:
        state = "stale"
    elif available:
        state = "reference-snapshot"
    else:
        state = "unavailable"
    return {
        "ok": True, "version": VERSION, "generated_at": _now(), "country": {"code": normalized, **country},
        "data_state": state, "stale": counts["stale"] > 0,
        "live_indicator_count": counts["live"], "available_indicator_count": len(available), "indicator_count": len(merged),
        "missing_indicators": [item["id"] for item in merged if not item.get("latest")],
        "state_counts": counts, "indicators": merged,
        "methodology": [
            "Latest non-null World Bank observation is used for each indicator.",
            "Reporting years, units, source identifiers, and retrieval states remain visible.",
            "Fresh and stale last-known-good records are explicitly labeled.",
            "Reference snapshots are labeled and used only when no live or cached record is available.",
            "No missing value is silently imputed and zero remains distinct from unavailable.",
        ],
    }


def country_trends(code: str) -> dict[str, Any]:
    payload = country_indicators(code)
    return {
        "ok": True, "version": VERSION, "generated_at": payload["generated_at"], "country": payload["country"],
        "data_state": payload["data_state"], "stale": payload.get("stale", False),
        "trends": [
            {"id": item["id"], "key": item["key"], "label": item["label"], "unit": item["unit"], "format": item["format"],
             "source": item["source"], "source_url": item.get("source_url"), "data_state": item.get("data_state"),
             "retrieved_at": item.get("retrieved_at"), "stale": item.get("stale", False), "series": item["series"]}
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
                "id": item["id"], "key": item["key"], "label": item["label"], "value": item["latest"]["value"],
                "year": item["latest"]["year"], "unit": item["unit"], "format": item["format"],
                "source": item["source"], "source_id": item.get("source_id"), "source_url": item.get("source_url"),
                "data_state": item["data_state"], "cache_state": item.get("cache_state"), "retrieved_at": item.get("retrieved_at"),
                "stale": item.get("stale", False), "lineage": item.get("lineage", {}),
            })
    return {
        "ok": True, "version": VERSION, "generated_at": payload["generated_at"], "country": country,
        "data_state": payload["data_state"], "stale": payload.get("stale", False),
        "summary": f"{country['name']} country intelligence combines public development indicators, satellite context, and recent public event records.",
        "highlights": highlights, "missing_indicators": payload.get("missing_indicators", []), "state_counts": payload.get("state_counts", {}),
        "indicator_endpoint": f"/public/country/{country['code']}/indicators", "trends_endpoint": f"/public/country/{country['code']}/trends",
        "events_endpoint": f"/public/events?country_code={country['code']}",
        "briefing": {"population": latest.get("population"), "life_expectancy": latest.get("life_expectancy"), "gdp_per_capita": latest.get("gdp_per_capita"), "electricity_access": latest.get("electricity_access"), "water_access": latest.get("water_access")},
        "interpretation": [
            "Values are descriptive public indicators and do not constitute a national ranking.",
            "Indicators may refer to different reporting years and methodologies.",
            "Cached, stale, and reference records remain labeled.",
            "Country context does not establish causality, eligibility, liability, or legal responsibility.",
        ],
    }


def country_brief(code: str) -> dict[str, Any]:
    profile = country_profile(code)
    country = profile["country"]
    lines = [f"{item['label']}: {item['value']} {item['unit']} ({item['year']}, {item['source']}, {item['data_state']})." for item in profile["highlights"]]
    return {
        "ok": True, "version": VERSION, "generated_at": profile["generated_at"], "country": country,
        "title": f"{country['name']} — Live Country Intelligence Brief", "summary": profile["summary"],
        "evidence_lines": lines, "data_state": profile["data_state"],
        "boundary": "This brief organizes public evidence for orientation and research. Verify important findings against the linked source.",
    }


def global_country_overview(code: str) -> dict[str, Any]:
    profile = country_profile(code)
    country = profile["country"]
    return {
        "ok": True, "version": VERSION, "generated_at": profile["generated_at"], "country": country,
        "data_state": profile["data_state"], "stale": profile.get("stale", False),
        "headline": f"{country['name']} — Global Country Intelligence", "summary": profile["summary"],
        "map": {"latitude": country.get("latitude"), "longitude": country.get("longitude"), "default_zoom": 5 if country.get("latitude") is not None and country.get("longitude") is not None else 2},
        "highlights": profile["highlights"], "missing_indicators": profile.get("missing_indicators", []),
        "routes": {
            "indicators": f"/public/country/{country['code']}/indicators", "trends": f"/public/country/{country['code']}/trends",
            "events": f"/public/events?country_code={country['code']}", "brief": f"/public/country/{country['code']}/brief",
            "lineage": f"/public/country/{country['code']}/evidence-lineage", "diagnostics": f"/public/country/{country['code']}/diagnostics",
        },
        "boundaries": profile["interpretation"],
    }


def countries_diagnostics() -> dict[str, Any]:
    payload = country_catalog()
    missing_capitals = [item["code"] for item in payload["countries"] if not item.get("capital")]
    missing_coordinates = [item["code"] for item in payload["countries"] if item.get("latitude") is None or item.get("longitude") is None]
    return {
        "ok": True, "version": VERSION, "generated_at": _now(), "catalog_state": payload["data_state"],
        "country_count": payload["country_count"], "catalog_retrieved_at": payload.get("catalog_fetched_at"),
        "catalog_timing_ms": _COUNTRY_CATALOG_TIMING_MS, "missing_capital_count": len(missing_capitals),
        "missing_coordinate_count": len(missing_coordinates), "missing_capital_codes": missing_capitals[:25],
        "missing_coordinate_codes": missing_coordinates[:25], "cache": country_cache.diagnostics(),
    }


def country_diagnostics(code: str) -> dict[str, Any]:
    started = perf_counter()
    indicators = country_indicators(code)
    country = indicators["country"]
    event_count = 0
    event_state = "not-requested"
    event_timing_ms = None
    try:
        from .unified_live_events import unified_events
        event_started = perf_counter()
        events = unified_events(days=30, limit=50, country_code=country["code"], allow_fallback=False)
        event_timing_ms = round((perf_counter() - event_started) * 1000, 2)
        event_count = events.get("count", 0)
        event_state = events.get("data_state", "unavailable")
    except Exception:
        event_state = "unavailable"
    diagnostics = _COUNTRY_DIAGNOSTICS.get(country["code"], {})
    return {
        "ok": True, "version": VERSION, "generated_at": _now(), "country": country,
        "catalog_state": country_catalog()["data_state"], "metadata_state": "available",
        "indicator_success_count": indicators["available_indicator_count"], "live_indicator_count": indicators["live_indicator_count"],
        "missing_indicators": indicators["missing_indicators"], "trend_success_count": sum(1 for item in indicators["indicators"] if item.get("series")),
        "event_link_count": event_count, "event_state": event_state, "cache_state": indicators["data_state"],
        "stale": indicators.get("stale", False), "connector_timings_ms": diagnostics.get("indicator_timings_ms", {}),
        "indicator_cache_states": diagnostics.get("cache_states", {}), "event_timing_ms": event_timing_ms,
        "total_timing_ms": round((perf_counter() - started) * 1000, 2), "cache": country_cache.diagnostics(),
    }
