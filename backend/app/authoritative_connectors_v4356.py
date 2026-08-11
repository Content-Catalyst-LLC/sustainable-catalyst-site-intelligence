from __future__ import annotations

"""Site Intelligence v4.35.6 national statistical & domain-authority connectors.

Adds five first-party statistical authorities on top of Expansion III:
Palestinian Central Bureau of Statistics (PxWeb), Statistics Canada WDS,
UK Office for National Statistics, Australian Bureau of Statistics SDMX,
and U.S. Bureau of Labor Statistics Public Data API.

All public routes are bounded. Missing values, status flags, revision metadata,
footnotes, and source payloads are preserved rather than silently coerced.
"""

from datetime import datetime, timezone
import math
import re
from typing import Any
from urllib.parse import quote, urlencode

from .version import APP_VERSION
from . import authoritative_connectors_v4355 as expansion_iii

VERSION = APP_VERSION
CONTRACT = "national-statistical-domain-authority-connector-expansion"

NEW_CONNECTORS: tuple[dict[str, Any], ...] = (
    {
        "id": "pcbs-pxweb-sdgs",
        "title": "Palestinian Central Bureau of Statistics PxWeb",
        "organization": "Palestinian Central Bureau of Statistics",
        "workspace": "Country / Human Development / Energy / SDG Statistics",
        "mode": "LIVE",
        "protocol": "PxWeb API v1 / JSON-stat",
        "base_url_setting": "pcbs_pxweb_base_url",
        "authentication": "Public statistical service.",
        "boundary": "PCBS statistical observations retain their published period, unit, disaggregation and metadata. Structural access indicators must not be presented as current service continuity or operational availability.",
    },
    {
        "id": "statistics-canada-wds",
        "title": "Statistics Canada Web Data Service",
        "organization": "Statistics Canada",
        "workspace": "Country / Economics / Population / Society",
        "mode": "LIVE",
        "protocol": "REST / JSON",
        "base_url_setting": "statcan_wds_base_url",
        "authentication": "Public Web Data Service.",
        "boundary": "Statistics Canada vectors may carry scalar factors, status codes, symbols, revisions and release timestamps; Site Intelligence preserves those fields instead of treating the numeric value alone as sufficient evidence.",
    },
    {
        "id": "uk-ons-api",
        "title": "UK Office for National Statistics API",
        "organization": "Office for National Statistics",
        "workspace": "Country / Economics / Population / Society",
        "mode": "LIVE",
        "protocol": "REST / JSON",
        "base_url_setting": "ons_api_base_url",
        "authentication": "Open and unrestricted public API.",
        "boundary": "ONS dataset editions and versions are explicit. Site Intelligence does not silently substitute a different release, geography, dimension option or wildcard scope.",
    },
    {
        "id": "australian-bureau-statistics-sdmx",
        "title": "Australian Bureau of Statistics Data API",
        "organization": "Australian Bureau of Statistics",
        "workspace": "Country / Economics / Population / Society",
        "mode": "LIVE",
        "protocol": "SDMX 2.1 / CSV",
        "base_url_setting": "abs_data_api_base_url",
        "authentication": "Freely accessible without an API key.",
        "boundary": "ABS Data API is a beta statistical dissemination service. Dataflow, SDMX key, time filters, labels and observation attributes remain part of the evidence record.",
    },
    {
        "id": "us-bls-public-data-api",
        "title": "U.S. Bureau of Labor Statistics Public Data API",
        "organization": "U.S. Bureau of Labor Statistics",
        "workspace": "Economics / Labor / Prices",
        "mode": "LIVE",
        "protocol": "REST / JSON",
        "base_url_setting": "bls_public_api_base_url",
        "authentication": "Version 1 public access requires no registration; bounded Site Intelligence requests use the public service.",
        "boundary": "BLS time-series values retain series identifiers, periods and footnotes such as preliminary status. A revised or preliminary value is not silently normalized into a final observation.",
    },
)

CONNECTORS: tuple[dict[str, Any], ...] = tuple(expansion_iii.CONNECTORS) + NEW_CONNECTORS

# Preserve the complete public connector surface from Expansion III.
usgs_water_latest = expansion_iii.usgs_water_latest
noaa_erddap_search = expansion_iii.noaa_erddap_search
noaa_erddap_tabledap = expansion_iii.noaa_erddap_tabledap
nasa_exoplanet_planets = expansion_iii.nasa_exoplanet_planets
unhcr_population = expansion_iii.unhcr_population
nasa_cmr_collections = expansion_iii.nasa_cmr_collections
noaa_coops_data = expansion_iii.noaa_coops_data
ncei_access_data = expansion_iii.ncei_access_data
obis_occurrences = expansion_iii.obis_occurrences
eurostat_statistics = expansion_iii.eurostat_statistics
usda_soil_mapunits = expansion_iii.usda_soil_mapunits
usfws_nwi_wetlands = expansion_iii.usfws_nwi_wetlands
epa_echo_facilities = expansion_iii.epa_echo_facilities
nasa_firms_area = expansion_iii.nasa_firms_area
usda_nass_quickstats = expansion_iii.usda_nass_quickstats
nasa_cmr_graphql_collections = expansion_iii.nasa_cmr_graphql_collections


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _setting(settings: Any, name: str, default: str = "") -> str:
    value = str(getattr(settings, name, "") or "").strip() if settings is not None else ""
    return value or default


def _timeout(settings: Any) -> int:
    return int(getattr(settings, "external_request_timeout_seconds", 8)) if settings is not None else 8


def _default_base(connector_id: str) -> str:
    return {
        "pcbs-pxweb-sdgs": "https://pcbs.gov.ps/SDGsIndicators/api/v1/en",
        "statistics-canada-wds": "https://www150.statcan.gc.ca/t1/wds/rest",
        "uk-ons-api": "https://api.beta.ons.gov.uk/v1",
        "australian-bureau-statistics-sdmx": "https://data.api.abs.gov.au/rest",
        "us-bls-public-data-api": "https://api.bls.gov/publicAPI/v1",
    }[connector_id]


def connector_catalog(settings: Any = None) -> dict[str, Any]:
    prior = expansion_iii.connector_catalog(settings)
    rows = [dict(row) for row in prior["connectors"]]
    for connector in NEW_CONNECTORS:
        row = dict(connector)
        row["configured_base_url"] = _setting(settings, connector["base_url_setting"], _default_base(connector["id"]))
        row["credential_configured"] = True
        row["network_check_performed"] = False
        rows.append(row)
    return {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "connector_count": len(rows),
        "live_connector_count": sum(1 for row in rows if row["mode"] == "LIVE"),
        "discovery_connector_count": sum(1 for row in rows if row["mode"] == "DISCOVERY"),
        "auth_required_connector_count": sum(1 for row in rows if row["mode"] == "AUTH_REQUIRED"),
        "configured_auth_required_connector_count": sum(1 for row in rows if row["mode"] == "AUTH_REQUIRED" and row.get("credential_configured")),
        "expansion_i_connector_count": prior.get("expansion_i_connector_count", 5),
        "expansion_ii_connector_count": prior.get("expansion_ii_connector_count", 5),
        "expansion_iii_connector_count": prior.get("expansion_iii_connector_count", 5),
        "expansion_vi_connector_count": len(NEW_CONNECTORS),
        "connectors": rows,
        "principles": prior.get("principles", []) + [
            "National statistical offices are preferred for country-specific official statistics when their metric is the relevant concept.",
            "International harmonized statistics remain useful for comparison but must not silently override a national authority's differently defined measure.",
            "Observation period, release/version, units, status flags and footnotes remain attached to the retrieved evidence.",
        ],
        "generated_at": _now(),
    }


def connector_readiness(settings: Any = None) -> dict[str, Any]:
    catalog = connector_catalog(settings)
    ids = {row["id"] for row in catalog["connectors"]}
    expected_new = {row["id"] for row in NEW_CONNECTORS}
    checks = {
        "twenty_authoritative_interfaces_registered": catalog["connector_count"] == 20,
        "sixteen_public_live_connectors": catalog["live_connector_count"] == 16,
        "two_discovery_connectors": catalog["discovery_connector_count"] == 2,
        "two_credential_gated_connectors": catalog["auth_required_connector_count"] == 2,
        "national_statistics_five_connector_ids_present": expected_new.issubset(ids) and len(expected_new) == 5,
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


def _safe_pxweb_path(table_path: str) -> str:
    path = (table_path or "").strip().strip("/")
    if not path or len(path) > 240 or ".." in path or not re.fullmatch(r"[A-Za-z0-9_./-]+", path):
        raise ValueError("table_path must be a bounded PCBS PxWeb table path")
    return path


def pcbs_pxweb_metadata(settings: Any, *, table_path: str) -> dict[str, Any]:
    path = _safe_pxweb_path(table_path)
    base = _setting(settings, "pcbs_pxweb_base_url", _default_base("pcbs-pxweb-sdgs")).rstrip("/")
    data = expansion_iii._request_json(f"{base}/{path}", timeout=_timeout(settings))
    return {
        "ok": True,
        "version": VERSION,
        "connector_id": "pcbs-pxweb-sdgs",
        "mode": "LIVE",
        "table_path": path,
        "metadata": data,
        "provenance": {"organization": "Palestinian Central Bureau of Statistics", "retrieved_at": _now(), "endpoint": f"{base}/{path}"},
        "boundary": NEW_CONNECTORS[0]["boundary"],
    }


def _pxweb_selections(values: list[str]) -> tuple[list[dict[str, Any]], int]:
    if not values or len(values) > 8:
        raise ValueError("selection must contain between 1 and 8 dimension selections")
    query: list[dict[str, Any]] = []
    cell_count = 1
    seen: set[str] = set()
    for item in values:
        if "=" not in item:
            raise ValueError("each selection must use DIMENSION=value1,value2 syntax")
        code, raw_values = item.split("=", 1)
        code = code.strip()
        selected = [part.strip() for part in raw_values.split(",") if part.strip()]
        if not re.fullmatch(r"[A-Za-z0-9_ -]{1,80}", code) or code in seen:
            raise ValueError("selection dimension code is invalid or duplicated")
        if not selected or len(selected) > 20:
            raise ValueError("each selection must contain between 1 and 20 explicit values")
        if any(value in {"*", "all", "ALL"} or len(value) > 120 for value in selected):
            raise ValueError("wildcard/all selections are not allowed on the public PCBS connector")
        seen.add(code)
        cell_count *= len(selected)
        if cell_count > 5000:
            raise ValueError("PCBS request exceeds the 5,000-cell Site Intelligence public bound")
        query.append({"code": code, "selection": {"filter": "item", "values": selected}})
    return query, cell_count


def pcbs_pxweb_data(settings: Any, *, table_path: str, selections: list[str]) -> dict[str, Any]:
    path = _safe_pxweb_path(table_path)
    query, requested_cells = _pxweb_selections(selections)
    base = _setting(settings, "pcbs_pxweb_base_url", _default_base("pcbs-pxweb-sdgs")).rstrip("/")
    endpoint = f"{base}/{path}"
    payload = {"query": query, "response": {"format": "json-stat2"}}
    data = expansion_iii._post_json(endpoint, payload, timeout=_timeout(settings), headers={"Accept": "application/json"})
    return {
        "ok": True,
        "version": VERSION,
        "connector_id": "pcbs-pxweb-sdgs",
        "mode": "LIVE",
        "table_path": path,
        "requested_cell_upper_bound": requested_cells,
        "data": data,
        "provenance": {"organization": "Palestinian Central Bureau of Statistics", "retrieved_at": _now(), "endpoint": endpoint, "request": payload},
        "boundary": NEW_CONNECTORS[0]["boundary"],
    }


def statcan_vectors(settings: Any, *, vector_ids: list[int], latest_n: int = 3) -> dict[str, Any]:
    ids = [int(value) for value in vector_ids]
    if not ids or len(ids) > 10 or any(value <= 0 for value in ids):
        raise ValueError("vector_id must contain between 1 and 10 positive Statistics Canada vector IDs")
    if not 1 <= int(latest_n) <= 24:
        raise ValueError("latest_n must be between 1 and 24")
    base = _setting(settings, "statcan_wds_base_url", _default_base("statistics-canada-wds")).rstrip("/")
    endpoint = f"{base}/getDataFromVectorsAndLatestNPeriods"
    payload = [{"vectorId": value, "latestN": int(latest_n)} for value in ids]
    data = expansion_iii._post_json(endpoint, payload, timeout=_timeout(settings))
    return {
        "ok": True,
        "version": VERSION,
        "connector_id": "statistics-canada-wds",
        "mode": "LIVE",
        "vector_count": len(ids),
        "latest_n": int(latest_n),
        "data": data,
        "provenance": {"organization": "Statistics Canada", "retrieved_at": _now(), "endpoint": endpoint, "request": payload},
        "boundary": NEW_CONNECTORS[1]["boundary"],
    }


def _safe_slug(value: str, *, name: str, max_length: int = 100) -> str:
    text = (value or "").strip()
    if not text or len(text) > max_length or not re.fullmatch(r"[A-Za-z0-9._-]+", text):
        raise ValueError(f"{name} is invalid")
    return text


def _ons_filters(filters: list[str]) -> dict[str, str]:
    if not filters or len(filters) > 8:
        raise ValueError("filter must contain between 1 and 8 ONS dimension selections")
    output: dict[str, str] = {}
    wildcard_count = 0
    for item in filters:
        if "=" not in item:
            raise ValueError("each ONS filter must use dimension=value syntax")
        key, value = item.split("=", 1)
        key, value = key.strip(), value.strip()
        if not re.fullmatch(r"[A-Za-z0-9._-]{1,80}", key) or not value or len(value) > 120:
            raise ValueError("ONS dimension filter is invalid")
        if key in output:
            raise ValueError("ONS dimension filters must not duplicate a dimension")
        if value == "*":
            wildcard_count += 1
        output[key] = value
    if wildcard_count > 1:
        raise ValueError("ONS public connector permits at most one wildcard dimension")
    if wildcard_count == 1 and len(output) < 2:
        raise ValueError("an ONS wildcard request must include at least one additional fixed dimension")
    return output


def ons_observations(settings: Any, *, dataset_id: str, edition: str, version: int, filters: list[str]) -> dict[str, Any]:
    dataset = _safe_slug(dataset_id, name="dataset_id")
    edition_value = _safe_slug(edition, name="edition")
    version_value = int(version)
    if version_value <= 0:
        raise ValueError("version must be positive")
    params = _ons_filters(filters)
    base = _setting(settings, "ons_api_base_url", _default_base("uk-ons-api")).rstrip("/")
    endpoint = f"{base}/datasets/{quote(dataset)}/editions/{quote(edition_value)}/versions/{version_value}/observations?{urlencode(params)}"
    data = expansion_iii._request_json(endpoint, timeout=_timeout(settings))
    return {
        "ok": True,
        "version": VERSION,
        "connector_id": "uk-ons-api",
        "mode": "LIVE",
        "dataset_id": dataset,
        "edition": edition_value,
        "dataset_version": version_value,
        "filters": params,
        "data": data,
        "provenance": {"organization": "Office for National Statistics", "retrieved_at": _now(), "endpoint": endpoint},
        "boundary": NEW_CONNECTORS[2]["boundary"],
    }


def _period_year(value: str) -> int:
    match = re.match(r"^(\d{4})", value or "")
    if not match:
        raise ValueError("period must begin with a four-digit year")
    return int(match.group(1))


def abs_sdmx_data(
    settings: Any,
    *,
    dataflow: str,
    data_key: str,
    start_period: str,
    end_period: str,
    limit: int = 200,
) -> dict[str, Any]:
    flow = (dataflow or "").strip()
    key = (data_key or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9_,.-]{2,120}", flow):
        raise ValueError("dataflow is invalid")
    if not key or len(key) > 240 or not re.fullmatch(r"[A-Za-z0-9_+.-]+", key):
        raise ValueError("data_key is invalid")
    if key.lower() == "all" or "*" in key:
        raise ValueError("ABS public connector requires an explicit SDMX data key")
    start_year, end_year = _period_year(start_period), _period_year(end_period)
    if end_year < start_year or end_year - start_year > 10:
        raise ValueError("ABS public requests must cover no more than 10 years")
    limit_value = max(1, min(1000, int(limit)))
    base = _setting(settings, "abs_data_api_base_url", _default_base("australian-bureau-statistics-sdmx")).rstrip("/")
    params = {
        "startPeriod": start_period,
        "endPeriod": end_period,
        "format": "csv",
        "labels": "both",
        "firstNObservations": limit_value,
    }
    endpoint = f"{base}/data/{quote(flow, safe=',')}/{quote(key, safe='.+')}?{urlencode(params)}"
    rows = expansion_iii._request_csv(endpoint, timeout=_timeout(settings))
    return {
        "ok": True,
        "version": VERSION,
        "connector_id": "australian-bureau-statistics-sdmx",
        "mode": "LIVE",
        "dataflow": flow,
        "data_key": key,
        "start_period": start_period,
        "end_period": end_period,
        "record_count": len(rows),
        "records": rows[:limit_value],
        "provenance": {"organization": "Australian Bureau of Statistics", "retrieved_at": _now(), "endpoint": endpoint},
        "boundary": NEW_CONNECTORS[3]["boundary"],
    }


def bls_timeseries(
    settings: Any,
    *,
    series_ids: list[str],
    start_year: int | None = None,
    end_year: int | None = None,
) -> dict[str, Any]:
    ids = [str(value).strip().upper() for value in series_ids if str(value).strip()]
    if not ids or len(ids) > 10 or any(not re.fullmatch(r"[A-Z0-9_#-]{4,60}", value) for value in ids):
        raise ValueError("series_id must contain between 1 and 10 valid BLS series IDs")
    payload: dict[str, Any] = {"seriesid": ids}
    if (start_year is None) != (end_year is None):
        raise ValueError("start_year and end_year must be supplied together")
    if start_year is not None and end_year is not None:
        start, end = int(start_year), int(end_year)
        current = datetime.now(timezone.utc).year
        if start < 1900 or end > current + 1 or end < start or end - start > 9:
            raise ValueError("BLS public v1 requests must cover a valid range of no more than 10 years")
        payload.update({"startyear": str(start), "endyear": str(end)})
    base = _setting(settings, "bls_public_api_base_url", _default_base("us-bls-public-data-api")).rstrip("/")
    endpoint = f"{base}/timeseries/data/"
    data = expansion_iii._post_json(endpoint, payload, timeout=_timeout(settings))
    return {
        "ok": True,
        "version": VERSION,
        "connector_id": "us-bls-public-data-api",
        "mode": "LIVE",
        "series_count": len(ids),
        "data": data,
        "provenance": {"organization": "U.S. Bureau of Labor Statistics", "retrieved_at": _now(), "endpoint": endpoint, "request": payload},
        "boundary": NEW_CONNECTORS[4]["boundary"],
    }
