from __future__ import annotations

"""Site Intelligence v4.35.4 authoritative connector expansion II.

Adds five public authoritative machine interfaces while preserving the Expansion I
connectors.  Retrieval is bounded, source metadata remains visible, and missing
source values remain missing.  No connector health call is required by release
verification.
"""

from datetime import date, datetime, timezone
import json
import math
import re
from typing import Any, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .version import APP_VERSION
from .external_resilience_v43517 import request_json as resilient_request_json
from . import authoritative_connectors_v4353 as expansion_i

VERSION = APP_VERSION
CONTRACT = "authoritative-connector-expansion-ii"
USER_AGENT = f"SustainableCatalyst-SiteIntelligence/{VERSION} (+https://sustainablecatalyst.com)"
MAX_RESPONSE_BYTES = 4 * 1024 * 1024

NEW_CONNECTORS: tuple[dict[str, Any], ...] = (
    {
        "id": "noaa-coops-data-api",
        "title": "NOAA CO-OPS Data API",
        "organization": "NOAA Center for Operational Oceanographic Products and Services",
        "workspace": "Coastal Change, Sea Level & Blue Carbon",
        "mode": "LIVE",
        "protocol": "REST / JSON",
        "base_url_setting": "noaa_coops_base_url",
        "authentication": "Public web service; station/product/range constraints apply.",
        "boundary": "Station observations are local and datum-dependent. Tide predictions are predictions, not total-water-level forecasts.",
    },
    {
        "id": "noaa-ncei-access-data-v1",
        "title": "NOAA NCEI Access Data Service",
        "organization": "NOAA National Centers for Environmental Information",
        "workspace": "Climate / NCEI data access",
        "mode": "LIVE",
        "protocol": "REST / JSON",
        "base_url_setting": "ncei_access_base_url",
        "authentication": "Public Access Data Service; individual datasets retain their own constraints.",
        "boundary": "Returned records retain dataset, station, time, datatype and quality context. Climate observations are not forecasts.",
    },
    {
        "id": "obis-api-v3",
        "title": "Ocean Biodiversity Information System API v3",
        "organization": "IOC-UNESCO / OBIS",
        "workspace": "Marine Biodiversity & Biodiversity Conservation",
        "mode": "LIVE",
        "protocol": "REST / JSON / Darwin Core",
        "base_url_setting": "obis_base_url",
        "authentication": "Public API.",
        "boundary": "Occurrence records are reported evidence, not a census or proof of present occupancy; zero results do not establish absence.",
    },
    {
        "id": "eurostat-statistics-api",
        "title": "Eurostat Statistics API",
        "organization": "Eurostat / European Commission",
        "workspace": "Solid Waste & Circular Materials / European statistics",
        "mode": "LIVE",
        "protocol": "REST / JSON-stat 2.0",
        "base_url_setting": "eurostat_base_url",
        "authentication": "Free public programmatic access.",
        "boundary": "Eurostat values remain official statistical series with dataset dimensions, units, time and reporting definitions intact.",
    },
    {
        "id": "usda-nrcs-soil-data-access",
        "title": "USDA-NRCS Soil Data Access",
        "organization": "USDA Natural Resources Conservation Service",
        "workspace": "Soils & Land Degradation",
        "mode": "LIVE",
        "protocol": "REST/POST / JSON",
        "base_url_setting": "usda_soil_data_access_url",
        "authentication": "Public Soil Data Access web service.",
        "boundary": "SSURGO mapunit/component records are generalized soil-survey information, not parcel boundaries or site-specific engineering determinations.",
    },
)

CONNECTORS: tuple[dict[str, Any], ...] = tuple(expansion_i.CONNECTORS) + NEW_CONNECTORS


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _setting(settings: Any, name: str, default: str) -> str:
    value = str(getattr(settings, name, "") or "").strip() if settings is not None else ""
    return value or default


def _timeout(settings: Any) -> int:
    return int(getattr(settings, "external_request_timeout_seconds", 8)) if settings is not None else 8


def _clamp_int(value: int, low: int, high: int) -> int:
    return max(low, min(high, int(value)))


def _request_json(url: str, *, timeout: int = 8, headers: dict[str, str] | None = None, max_bytes: int = MAX_RESPONSE_BYTES) -> Any:
    return resilient_request_json(url, headers=headers, timeout=timeout, max_bytes=max_bytes, cache=True, stale_if_error=False)


def _post_json(url: str, payload: dict[str, Any], *, timeout: int = 8, max_bytes: int = MAX_RESPONSE_BYTES) -> Any:
    return resilient_request_json(url, payload=payload, timeout=timeout, max_bytes=max_bytes, cache=True, stale_if_error=False, retry_safe=True)


def _default_base(connector_id: str) -> str:
    return {
        "noaa-coops-data-api": "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter",
        "noaa-ncei-access-data-v1": "https://www.ncei.noaa.gov/access/services/data/v1",
        "obis-api-v3": "https://api.obis.org/v3",
        "eurostat-statistics-api": "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data",
        "usda-nrcs-soil-data-access": "https://SDMDataAccess.sc.egov.usda.gov/Tabular/post.rest",
    }[connector_id]


def connector_catalog(settings: Any = None) -> dict[str, Any]:
    prior = expansion_i.connector_catalog(settings)
    rows = [dict(row) for row in prior["connectors"]]
    for connector in NEW_CONNECTORS:
        row = dict(connector)
        row["configured_base_url"] = _setting(settings, connector["base_url_setting"], _default_base(connector["id"]))
        row["network_check_performed"] = False
        rows.append(row)
    return {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "connector_count": len(rows),
        "live_connector_count": sum(1 for row in rows if row["mode"] == "LIVE"),
        "discovery_connector_count": sum(1 for row in rows if row["mode"] == "DISCOVERY"),
        "expansion_i_connector_count": prior["connector_count"],
        "expansion_ii_connector_count": len(NEW_CONNECTORS),
        "connectors": rows,
        "principles": prior.get("principles", []) + [
            "Bound public queries before calling upstream services; do not proxy arbitrary SQL, URLs, or unbounded dataset requests.",
            "Release verification remains independent of transient upstream source health.",
        ],
        "generated_at": _now(),
    }


def connector_readiness(settings: Any = None) -> dict[str, Any]:
    catalog = connector_catalog(settings)
    ids = {row["id"] for row in catalog["connectors"]}
    expected_new = {row["id"] for row in NEW_CONNECTORS}
    checks = {
        "ten_authoritative_interfaces_implemented": catalog["connector_count"] == 10,
        "nine_live_capable_connectors": catalog["live_connector_count"] == 9,
        "nasa_cmr_discovery_remains_distinct": catalog["discovery_connector_count"] == 1,
        "expansion_ii_five_connector_ids_present": expected_new.issubset(ids) and len(expected_new) == 5,
        "network_checks_not_required_for_deterministic_readiness": True,
        "release_gate_does_not_depend_on_upstream_health": True,
    }
    return {
        "ok": all(checks.values()),
        "version": VERSION,
        "contract": CONTRACT,
        "network_calls_performed": False,
        "checks": checks,
        "generated_at": _now(),
    }


_COOPS_PRODUCTS = {
    "water_level", "hourly_height", "high_low", "daily_mean", "monthly_mean",
    "one_minute_water_level", "predictions", "air_temperature", "water_temperature",
    "wind", "air_pressure", "conductivity", "visibility", "humidity", "salinity",
    "currents", "currents_predictions", "currents_header", "ofs_water_level",
}


def noaa_coops_data(
    settings: Any,
    *,
    station: str,
    product: str = "water_level",
    date_value: str = "latest",
    begin_date: str = "",
    end_date: str = "",
    datum: str = "MSL",
    units: str = "metric",
    time_zone: str = "gmt",
    interval: str = "",
) -> dict[str, Any]:
    station_id = re.sub(r"[^A-Za-z0-9]", "", station or "")[:20]
    if not station_id:
        raise ValueError("station is required")
    product_id = (product or "water_level").strip().lower()
    if product_id not in _COOPS_PRODUCTS:
        raise ValueError("unsupported NOAA CO-OPS product")
    if units not in {"metric", "english"}:
        raise ValueError("units must be metric or english")
    if time_zone not in {"gmt", "lst", "lst_ldt"}:
        raise ValueError("time_zone must be gmt, lst, or lst_ldt")
    params: dict[str, str] = {
        "product": product_id,
        "application": "sustainable-catalyst-site-intelligence",
        "station": station_id,
        "units": units,
        "time_zone": time_zone,
        "format": "json",
    }
    if product_id in {"water_level", "hourly_height", "high_low", "daily_mean", "monthly_mean", "one_minute_water_level", "predictions", "ofs_water_level"}:
        params["datum"] = re.sub(r"[^A-Za-z0-9]", "", datum or "MSL").upper()[:8]
    if begin_date or end_date:
        if not (begin_date and end_date):
            raise ValueError("begin_date and end_date must be provided together")
        parsed_range = []
        for label, value in (("begin_date", begin_date), ("end_date", end_date)):
            if not re.fullmatch(r"\d{8}(?: \d{2}:\d{2})?", value):
                raise ValueError(f"{label} must use YYYYMMDD or YYYYMMDD HH:MM")
            fmt = "%Y%m%d %H:%M" if " " in value else "%Y%m%d"
            parsed_range.append(datetime.strptime(value, fmt))
        if parsed_range[1] < parsed_range[0] or (parsed_range[1] - parsed_range[0]).days > 31:
            raise ValueError("NOAA CO-OPS explicit date ranges must be ordered and no more than 31 days")
        params["begin_date"] = begin_date
        params["end_date"] = end_date
    else:
        if date_value not in {"latest", "recent", "today"} and not re.fullmatch(r"\d{8}", date_value or ""):
            raise ValueError("date must be latest, recent, today, or YYYYMMDD")
        params["date"] = date_value or "latest"
    if interval:
        if not re.fullmatch(r"[A-Za-z0-9_]{1,16}", interval):
            raise ValueError("interval contains unsupported characters")
        params["interval"] = interval
    base = _setting(settings, "noaa_coops_base_url", _default_base("noaa-coops-data-api"))
    url = f"{base}?{urlencode(params)}"
    payload = _request_json(url, timeout=_timeout(settings))
    if isinstance(payload, dict) and payload.get("error"):
        message = payload.get("error", {}).get("message") if isinstance(payload.get("error"), dict) else str(payload.get("error"))
        raise RuntimeError(f"NOAA CO-OPS returned an error: {message or 'unknown error'}")
    records = []
    if isinstance(payload, dict):
        for key in ("data", "predictions"):
            if isinstance(payload.get(key), list):
                records = [row for row in payload[key] if isinstance(row, dict)]
                break
    return {
        "ok": True, "version": VERSION, "contract": CONTRACT,
        "connector_id": "noaa-coops-data-api", "source": "NOAA CO-OPS Data API",
        "query": params, "metadata": payload.get("metadata") if isinstance(payload, dict) else None,
        "record_count": len(records), "records": records, "retrieved_at": _now(), "source_url": url,
        "boundary": "CO-OPS observations are station- and datum-specific. Source flags/quality fields remain attached; predictions are not observations or total-water-level forecasts.",
    }


def _iso_date(value: str, name: str) -> date:
    try:
        return date.fromisoformat(value)
    except Exception as exc:
        raise ValueError(f"{name} must use YYYY-MM-DD") from exc


def ncei_access_data(
    settings: Any,
    *,
    dataset: str,
    start_date: str,
    end_date: str,
    stations: Iterable[str] = (),
    data_types: Iterable[str] = (),
    units: str = "metric",
) -> dict[str, Any]:
    dataset_id = (dataset or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9_.-]{2,100}", dataset_id):
        raise ValueError("dataset contains unsupported characters")
    start, end = _iso_date(start_date, "start_date"), _iso_date(end_date, "end_date")
    if end < start or (end - start).days > 366:
        raise ValueError("NCEI date range must be ordered and no more than 366 days")
    if units not in {"metric", "standard"}:
        raise ValueError("units must be metric or standard")
    station_rows = [re.sub(r"[^A-Za-z0-9:_-]", "", str(x))[:40] for x in stations if str(x).strip()]
    type_rows = [re.sub(r"[^A-Za-z0-9_-]", "", str(x))[:40] for x in data_types if str(x).strip()]
    if len(station_rows) > 20 or len(type_rows) > 30:
        raise ValueError("too many NCEI station or datatype filters")
    params: dict[str, str] = {
        "dataset": dataset_id, "startDate": start.isoformat(), "endDate": end.isoformat(),
        "format": "json", "units": units, "includeAttributes": "true", "includeStationLocation": "true",
    }
    if station_rows:
        params["stations"] = ",".join(station_rows)
    if type_rows:
        params["dataTypes"] = ",".join(type_rows)
    base = _setting(settings, "ncei_access_base_url", _default_base("noaa-ncei-access-data-v1"))
    url = f"{base}?{urlencode(params)}"
    payload = _request_json(url, timeout=_timeout(settings))
    records = [row for row in payload if isinstance(row, dict)] if isinstance(payload, list) else []
    return {
        "ok": True, "version": VERSION, "contract": CONTRACT,
        "connector_id": "noaa-ncei-access-data-v1", "source": "NOAA NCEI Access Data Service",
        "query": params, "record_count": len(records), "records": records,
        "retrieved_at": _now(), "source_url": url,
        "boundary": "NCEI records preserve station, time, datatype, units and source attributes. A historical climate observation is not a forecast or attribution finding.",
    }


def obis_occurrences(
    settings: Any,
    *,
    scientific_name: str = "",
    aphia_id: int | None = None,
    geometry: str = "",
    start_date: str = "",
    end_date: str = "",
    size: int = 50,
) -> dict[str, Any]:
    size = _clamp_int(size, 1, 200)
    params: dict[str, str] = {"size": str(size)}
    if scientific_name.strip():
        params["scientificname"] = scientific_name.strip()[:160]
    if aphia_id is not None:
        if int(aphia_id) <= 0:
            raise ValueError("aphia_id must be positive")
        params["taxonid"] = str(int(aphia_id))
    if geometry.strip():
        geom = geometry.strip()
        if len(geom) > 1500 or not re.match(r"^(POINT|POLYGON|MULTIPOLYGON)\s*\(", geom, flags=re.I):
            raise ValueError("geometry must be bounded WKT POINT/POLYGON/MULTIPOLYGON")
        params["geometry"] = geom
    if start_date:
        params["startdate"] = _iso_date(start_date, "start_date").isoformat()
    if end_date:
        params["enddate"] = _iso_date(end_date, "end_date").isoformat()
    if start_date and end_date and params["enddate"] < params["startdate"]:
        raise ValueError("end_date must not precede start_date")
    if len(params) == 1:
        raise ValueError("at least one OBIS occurrence filter is required")
    base = _setting(settings, "obis_base_url", _default_base("obis-api-v3")).rstrip("/")
    url = f"{base}/occurrence?{urlencode(params)}"
    payload = _request_json(url, timeout=_timeout(settings))
    records: list[dict[str, Any]] = []
    total = None
    if isinstance(payload, dict):
        total = payload.get("total")
        for key in ("results", "data"):
            if isinstance(payload.get(key), list):
                records = [row for row in payload[key] if isinstance(row, dict)]
                break
    return {
        "ok": True, "version": VERSION, "contract": CONTRACT,
        "connector_id": "obis-api-v3", "source": "IOC-UNESCO Ocean Biodiversity Information System",
        "query": params, "record_count": len(records), "upstream_total": total, "records": records,
        "retrieved_at": _now(), "source_url": url,
        "boundary": "OBIS occurrence records retain dataset provenance and QC fields. They are reported occurrences, not population estimates; zero returned records do not establish absence.",
    }


_DATASET_CODE = re.compile(r"^[A-Za-z0-9_.-]{2,80}$")
_DIMENSION = re.compile(r"^[A-Za-z0-9_]{1,40}$")


def eurostat_statistics(
    settings: Any,
    *,
    dataset_code: str = "env_wasmun",
    geo: str = "",
    time: str = "",
    filters: Iterable[str] = (),
) -> dict[str, Any]:
    code = (dataset_code or "").strip()
    if not _DATASET_CODE.fullmatch(code):
        raise ValueError("dataset_code contains unsupported characters")
    pairs: list[tuple[str, str]] = [("format", "JSON"), ("lang", "EN")]
    if geo.strip():
        pairs.append(("geo", geo.strip()[:16]))
    if time.strip():
        if not re.fullmatch(r"[0-9A-Za-z_.-]{1,20}", time.strip()):
            raise ValueError("time contains unsupported characters")
        pairs.append(("time", time.strip()))
    extra_count = 0
    for item in filters:
        text = str(item).strip()
        if not text:
            continue
        if "=" not in text:
            raise ValueError("Eurostat filters must use dimension=value")
        name, value = text.split("=", 1)
        if not _DIMENSION.fullmatch(name.strip()) or not re.fullmatch(r"[0-9A-Za-z_.:@+\-]{1,80}", value.strip()):
            raise ValueError("Eurostat filter contains unsupported characters")
        pairs.append((name.strip(), value.strip()))
        extra_count += 1
    if not geo.strip() and not time.strip() and extra_count == 0:
        raise ValueError("at least one Eurostat dimension filter is required")
    if extra_count > 12:
        raise ValueError("too many Eurostat dimension filters")
    base = _setting(settings, "eurostat_base_url", _default_base("eurostat-statistics-api")).rstrip("/")
    url = f"{base}/{code}?{urlencode(pairs)}"
    payload = _request_json(url, timeout=_timeout(settings))
    if not isinstance(payload, dict):
        payload = {}
    return {
        "ok": True, "version": VERSION, "contract": CONTRACT,
        "connector_id": "eurostat-statistics-api", "source": "Eurostat Statistics API",
        "dataset_code": code, "query": dict(pairs),
        "jsonstat_id": payload.get("id"), "jsonstat_size": payload.get("size"),
        "value_count": len(payload.get("value", {})) if isinstance(payload.get("value"), dict) else (len(payload.get("value", [])) if isinstance(payload.get("value"), list) else 0),
        "data": payload, "retrieved_at": _now(), "source_url": url,
        "boundary": "Eurostat data retain their JSON-stat dimensions, units, geography, time and status metadata. Values are not silently converted across definitions or reporting systems.",
    }


def _soil_table(payload: Any) -> tuple[list[str], list[dict[str, Any]]]:
    if isinstance(payload, dict):
        table = payload.get("Table") or payload.get("table") or payload.get("data")
    else:
        table = payload
    if not isinstance(table, list) or not table:
        return [], []
    if isinstance(table[0], list):
        columns = [str(x) for x in table[0]]
        rows = [
            {columns[i]: (raw[i] if i < len(raw) else None) for i in range(len(columns))}
            for raw in table[1:] if isinstance(raw, list)
        ]
        return columns, rows
    if all(isinstance(row, dict) for row in table):
        rows = [dict(row) for row in table]
        columns = list(rows[0].keys()) if rows else []
        return columns, rows
    return [], []


def usda_soil_mapunits(
    settings: Any,
    *,
    mukey: str = "",
    area_symbol: str = "",
    limit: int = 50,
) -> dict[str, Any]:
    limit = _clamp_int(limit, 1, 200)
    mukey_value = (mukey or "").strip()
    area_value = (area_symbol or "").strip().upper()
    if mukey_value and not re.fullmatch(r"[0-9]{1,30}", mukey_value):
        raise ValueError("mukey must contain digits only")
    if area_value and not re.fullmatch(r"[A-Z0-9]{1,10}", area_value):
        raise ValueError("area_symbol must contain letters and digits only")
    clean_mukey = mukey_value
    clean_area = area_value
    if bool(clean_mukey) == bool(clean_area):
        raise ValueError("provide exactly one of mukey or area_symbol")
    if clean_mukey:
        query = f"SELECT TOP {limit} mukey, musym, muname, lkey FROM mapunit WHERE mukey = '{clean_mukey}' ORDER BY musym"
        query_desc = {"mukey": clean_mukey}
    else:
        query = (
            f"SELECT TOP {limit} mu.mukey, mu.musym, mu.muname, l.areasymbol "
            f"FROM mapunit mu INNER JOIN legend l ON mu.lkey = l.lkey "
            f"WHERE l.areasymbol = '{clean_area}' ORDER BY mu.musym"
        )
        query_desc = {"area_symbol": clean_area}
    url = _setting(settings, "usda_soil_data_access_url", _default_base("usda-nrcs-soil-data-access"))
    payload = _post_json(url, {"query": query, "format": "JSON+COLUMNNAME"}, timeout=_timeout(settings))
    columns, records = _soil_table(payload)
    return {
        "ok": True, "version": VERSION, "contract": CONTRACT,
        "connector_id": "usda-nrcs-soil-data-access", "source": "USDA-NRCS Soil Data Access",
        "query": query_desc, "record_count": len(records), "columns": columns, "records": records,
        "retrieved_at": _now(), "source_url": url,
        "boundary": "Soil Data Access returns official soil-survey mapunit/tabular records. These records are generalized survey information and are not site-specific field sampling or engineering conclusions.",
    }

# Preserve Expansion I function names for the public router and downstream users.
usgs_water_latest = expansion_i.usgs_water_latest
noaa_erddap_search = expansion_i.noaa_erddap_search
noaa_erddap_tabledap = expansion_i.noaa_erddap_tabledap
nasa_exoplanet_planets = expansion_i.nasa_exoplanet_planets
unhcr_population = expansion_i.unhcr_population
nasa_cmr_collections = expansion_i.nasa_cmr_collections
