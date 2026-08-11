from __future__ import annotations

"""Site Intelligence v4.35.5 authoritative connector expansion III.

Adds five authoritative machine interfaces on top of Expansion II:
USFWS National Wetlands Inventory REST, EPA ECHO facility web services,
NASA FIRMS active-fire area API (MAP_KEY gated), USDA NASS Quick Stats
(API-key gated), and NASA CMR GraphQL discovery.

Retrieval remains bounded and provenance-preserving. Credential-gated sources
are never represented as live when their server-side credential is absent.
"""

from datetime import date, datetime, timezone
import csv
import io
import json
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from .version import APP_VERSION
from . import authoritative_connectors_v4354 as expansion_ii

VERSION = APP_VERSION
CONTRACT = "authoritative-connector-expansion-iii"
USER_AGENT = f"SustainableCatalyst-SiteIntelligence/{VERSION} (+https://sustainablecatalyst.com)"
MAX_RESPONSE_BYTES = 4 * 1024 * 1024

NEW_CONNECTORS: tuple[dict[str, Any], ...] = (
    {
        "id": "usfws-nwi-rest",
        "title": "USFWS National Wetlands Inventory REST",
        "organization": "U.S. Fish & Wildlife Service",
        "workspace": "Wetlands & Inland Waters",
        "mode": "LIVE",
        "protocol": "ArcGIS REST / GeoJSON",
        "base_url_setting": "usfws_nwi_query_url",
        "authentication": "Public web mapping/query service.",
        "boundary": "NWI polygons are inventory/cartographic evidence, not a jurisdictional wetland determination, site delineation, permitting decision, or proof of absence.",
    },
    {
        "id": "epa-echo-facility-web-services",
        "title": "EPA ECHO Facility Web Services",
        "organization": "U.S. Environmental Protection Agency",
        "workspace": "Water / Waste / Industrial Regulatory Context",
        "mode": "LIVE",
        "protocol": "REST-like / JSON",
        "base_url_setting": "epa_echo_base_url",
        "authentication": "Public query-only web services.",
        "boundary": "ECHO records are regulatory/administrative evidence from EPA source systems. They do not create a new violation finding, legal conclusion, exposure finding, or current operating-status determination.",
    },
    {
        "id": "nasa-firms-area-api",
        "title": "NASA LANCE FIRMS Area API",
        "organization": "NASA LANCE / FIRMS",
        "workspace": "Terrestrial Ecosystems & Wildfire",
        "mode": "AUTH_REQUIRED",
        "protocol": "REST / CSV",
        "base_url_setting": "nasa_firms_base_url",
        "credential_setting": "nasa_firms_map_key",
        "credential_environment": "SC_SI_NASA_FIRMS_MAP_KEY",
        "authentication": "Free FIRMS MAP_KEY required server-side.",
        "boundary": "Thermal anomaly detections are satellite observations, not complete wildfire incidents, perimeters, containment estimates, ignition causes, evacuation orders, or burned-area estimates.",
    },
    {
        "id": "usda-nass-quick-stats",
        "title": "USDA NASS Quick Stats API",
        "organization": "USDA National Agricultural Statistics Service",
        "workspace": "Agriculture, Crops & Food Systems",
        "mode": "AUTH_REQUIRED",
        "protocol": "REST / JSON",
        "base_url_setting": "usda_nass_quickstats_url",
        "credential_setting": "usda_nass_api_key",
        "credential_environment": "SC_SI_USDA_NASS_API_KEY",
        "authentication": "NASS API key required server-side.",
        "boundary": "NASS values are official survey/census statistical estimates with aggregation, revision, suppression and methodology context; they are not exact field-by-field observations.",
    },
    {
        "id": "nasa-cmr-graphql",
        "title": "NASA CMR GraphQL",
        "organization": "NASA EOSDIS Common Metadata Repository",
        "workspace": "Earth / Science / Space Discovery",
        "mode": "DISCOVERY",
        "protocol": "GraphQL",
        "base_url_setting": "nasa_cmr_graphql_url",
        "authentication": "Public metadata search; optional Earthdata Login token for authorized concepts.",
        "boundary": "CMR GraphQL returns metadata/discovery records. It does not itself establish an observation value from the underlying scientific data product.",
    },
)

CONNECTORS: tuple[dict[str, Any], ...] = tuple(expansion_ii.CONNECTORS) + NEW_CONNECTORS


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _setting(settings: Any, name: str, default: str = "") -> str:
    value = str(getattr(settings, name, "") or "").strip() if settings is not None else ""
    return value or default


def _timeout(settings: Any) -> int:
    return int(getattr(settings, "external_request_timeout_seconds", 8)) if settings is not None else 8


def _default_base(connector_id: str) -> str:
    return {
        "usfws-nwi-rest": "https://fwspublicservices.wim.usgs.gov/wetlandsmapservice/rest/services/Wetlands/MapServer/0/query",
        "epa-echo-facility-web-services": "https://echodata.epa.gov/echo",
        "nasa-firms-area-api": "https://firms.modaps.eosdis.nasa.gov/api/area/csv",
        "usda-nass-quick-stats": "https://quickstats.nass.usda.gov/api/api_GET/",
        "nasa-cmr-graphql": "https://graphql.earthdata.nasa.gov/api",
    }[connector_id]


def _configured(connector: dict[str, Any], settings: Any) -> bool:
    credential = str(connector.get("credential_setting") or "")
    if credential:
        return bool(_setting(settings, credential))
    return True


def connector_catalog(settings: Any = None) -> dict[str, Any]:
    prior = expansion_ii.connector_catalog(settings)
    rows = [dict(row) for row in prior["connectors"]]
    for connector in NEW_CONNECTORS:
        row = dict(connector)
        row["configured_base_url"] = _setting(settings, connector["base_url_setting"], _default_base(connector["id"]))
        row["credential_configured"] = _configured(connector, settings)
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
        "expansion_iii_connector_count": len(NEW_CONNECTORS),
        "connectors": rows,
        "principles": prior.get("principles", []) + [
            "Credential-gated authoritative sources remain AUTH_REQUIRED until their server-side credential is configured.",
            "Discovery interfaces return metadata/capabilities, not observation values from underlying products.",
        ],
        "generated_at": _now(),
    }


def connector_readiness(settings: Any = None) -> dict[str, Any]:
    catalog = connector_catalog(settings)
    ids = {row["id"] for row in catalog["connectors"]}
    expected_new = {row["id"] for row in NEW_CONNECTORS}
    checks = {
        "fifteen_authoritative_interfaces_registered": catalog["connector_count"] == 15,
        "eleven_public_live_connectors": catalog["live_connector_count"] == 11,
        "two_discovery_connectors": catalog["discovery_connector_count"] == 2,
        "two_credential_gated_connectors": catalog["auth_required_connector_count"] == 2,
        "expansion_iii_five_connector_ids_present": expected_new.issubset(ids) and len(expected_new) == 5,
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


def _request_json(url: str, *, timeout: int = 8, headers: dict[str, str] | None = None, max_bytes: int = MAX_RESPONSE_BYTES) -> Any:
    request_headers = {"Accept": "application/json", "User-Agent": USER_AGENT}
    request_headers.update(headers or {})
    req = Request(url, headers=request_headers, method="GET")
    try:
        with urlopen(req, timeout=timeout) as response:
            raw = response.read(max_bytes + 1)
            if len(raw) > max_bytes:
                raise ValueError("Authoritative API response exceeded the public connector size limit.")
            return json.loads(raw.decode(response.headers.get_content_charset() or "utf-8"))
    except HTTPError as exc:
        raise RuntimeError(f"Authoritative API returned HTTP {exc.code}.") from exc
    except URLError as exc:
        raise RuntimeError("Authoritative API could not be reached.") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError("Authoritative API returned invalid JSON.") from exc


def _post_json(url: str, payload: dict[str, Any], *, timeout: int = 8, headers: dict[str, str] | None = None, max_bytes: int = MAX_RESPONSE_BYTES) -> Any:
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    request_headers = {"Accept": "application/json", "Content-Type": "application/json", "User-Agent": USER_AGENT}
    request_headers.update(headers or {})
    req = Request(url, data=body, headers=request_headers, method="POST")
    try:
        with urlopen(req, timeout=timeout) as response:
            raw = response.read(max_bytes + 1)
            if len(raw) > max_bytes:
                raise ValueError("Authoritative API response exceeded the public connector size limit.")
            return json.loads(raw.decode(response.headers.get_content_charset() or "utf-8"))
    except HTTPError as exc:
        raise RuntimeError(f"Authoritative API returned HTTP {exc.code}.") from exc
    except URLError as exc:
        raise RuntimeError("Authoritative API could not be reached.") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError("Authoritative API returned invalid JSON.") from exc


def _request_csv(url: str, *, timeout: int = 8, max_bytes: int = MAX_RESPONSE_BYTES) -> list[dict[str, Any]]:
    req = Request(url, headers={"Accept": "text/csv", "User-Agent": USER_AGENT}, method="GET")
    try:
        with urlopen(req, timeout=timeout) as response:
            raw = response.read(max_bytes + 1)
            if len(raw) > max_bytes:
                raise ValueError("Authoritative API response exceeded the public connector size limit.")
            text = raw.decode(response.headers.get_content_charset() or "utf-8-sig")
    except HTTPError as exc:
        raise RuntimeError(f"Authoritative API returned HTTP {exc.code}.") from exc
    except URLError as exc:
        raise RuntimeError("Authoritative API could not be reached.") from exc
    return [dict(row) for row in csv.DictReader(io.StringIO(text))]


def _parse_bbox(value: str, *, max_width: float = 30.0, max_height: float = 30.0) -> tuple[float, float, float, float]:
    try:
        west, south, east, north = [float(part.strip()) for part in value.split(",")]
    except Exception as exc:
        raise ValueError("bbox must be west,south,east,north") from exc
    if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
        raise ValueError("bbox coordinates are outside valid longitude/latitude bounds")
    if east - west > max_width or north - south > max_height:
        raise ValueError(f"bbox is too large; maximum span is {max_width:g}° longitude by {max_height:g}° latitude")
    return west, south, east, north


def usfws_nwi_wetlands(
    settings: Any,
    *,
    latitude: float | None = None,
    longitude: float | None = None,
    bbox: str = "",
    limit: int = 50,
    return_geometry: bool = True,
) -> dict[str, Any]:
    limit = max(1, min(200, int(limit)))
    have_point = latitude is not None or longitude is not None
    have_bbox = bool((bbox or "").strip())
    if have_point and have_bbox:
        raise ValueError("provide either latitude/longitude or bbox, not both")
    if have_point:
        if latitude is None or longitude is None:
            raise ValueError("latitude and longitude must be supplied together")
        if not (-90 <= float(latitude) <= 90 and -180 <= float(longitude) <= 180):
            raise ValueError("latitude/longitude are outside valid bounds")
        geometry = f"{float(longitude):.6f},{float(latitude):.6f}"
        geometry_type = "esriGeometryPoint"
    elif have_bbox:
        west, south, east, north = _parse_bbox(bbox, max_width=5.0, max_height=5.0)
        geometry = f"{west},{south},{east},{north}"
        geometry_type = "esriGeometryEnvelope"
    else:
        raise ValueError("latitude/longitude or bbox is required")
    params = {
        "where": "1=1",
        "geometry": geometry,
        "geometryType": geometry_type,
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "ATTRIBUTE,WETLAND_TYPE,ACRES,GLOBALID",
        "returnGeometry": "true" if return_geometry else "false",
        "outSR": "4326",
        "resultRecordCount": str(limit),
        "f": "geojson",
    }
    base = _setting(settings, "usfws_nwi_query_url", _default_base("usfws-nwi-rest"))
    data = _request_json(base + "?" + urlencode(params), timeout=_timeout(settings))
    features = data.get("features", []) if isinstance(data, dict) else []
    return {
        "ok": True,
        "version": VERSION,
        "connector_id": "usfws-nwi-rest",
        "source": "USFWS National Wetlands Inventory REST",
        "mode": "LIVE",
        "record_count": len(features) if isinstance(features, list) else 0,
        "data": data,
        "interpretation_boundary": "Inventory polygons are not a site-specific jurisdictional wetland determination and no returned feature does not prove wetland absence.",
        "retrieved_at": _now(),
    }


_ECHO_MEDIA = {
    "all": "echo_rest_services.get_facilities",
    "cwa": "cwa_rest_services.get_facilities",
    "rcra": "rcra_rest_services.get_facilities",
}


def epa_echo_facilities(
    settings: Any,
    *,
    media: str = "all",
    state: str = "",
    registry_id: str = "",
    latitude: float | None = None,
    longitude: float | None = None,
    radius_miles: float = 5.0,
    limit: int = 100,
) -> dict[str, Any]:
    media_id = (media or "all").strip().lower()
    if media_id not in _ECHO_MEDIA:
        raise ValueError("media must be one of: all, cwa, rcra")
    params: dict[str, str] = {"output": "JSON"}
    filters = 0
    st = re.sub(r"[^A-Za-z]", "", state or "").upper()
    if st:
        if len(st) != 2:
            raise ValueError("state must be a two-letter U.S. postal code")
        params["p_st"] = st
        filters += 1
    rid = re.sub(r"[^A-Za-z0-9-]", "", registry_id or "")[:24]
    if registry_id and not rid:
        raise ValueError("registry_id contains no valid identifier characters")
    if rid:
        params["p_id"] = rid
        filters += 1
    if latitude is not None or longitude is not None:
        if latitude is None or longitude is None:
            raise ValueError("latitude and longitude must be supplied together")
        if not (-90 <= float(latitude) <= 90 and -180 <= float(longitude) <= 180):
            raise ValueError("latitude/longitude are outside valid bounds")
        radius = float(radius_miles)
        if not 0 < radius <= 50:
            raise ValueError("radius_miles must be greater than 0 and no more than 50")
        params.update({"p_lat": f"{float(latitude):.6f}", "p_long": f"{float(longitude):.6f}", "p_radius": f"{radius:g}"})
        filters += 1
    if filters == 0:
        raise ValueError("at least one bounded facility filter is required")
    params["responseset"] = str(max(1, min(500, int(limit))))
    base = _setting(settings, "epa_echo_base_url", _default_base("epa-echo-facility-web-services")).rstrip("/")
    url = f"{base}/{_ECHO_MEDIA[media_id]}?{urlencode(params)}"
    data = _request_json(url, timeout=_timeout(settings))
    return {
        "ok": True,
        "version": VERSION,
        "connector_id": "epa-echo-facility-web-services",
        "source": "EPA ECHO Facility Web Services",
        "mode": "LIVE",
        "media": media_id,
        "data": data,
        "interpretation_boundary": "ECHO is regulatory/administrative evidence. Site Intelligence does not convert it into a new compliance, legal, exposure, or operating-status determination.",
        "retrieved_at": _now(),
    }


_FIRMS_SOURCES = {
    "LANDSAT_NRT", "MODIS_NRT", "MODIS_SP", "VIIRS_NOAA20_NRT", "VIIRS_NOAA20_SP",
    "VIIRS_NOAA21_NRT", "VIIRS_SNPP_NRT", "VIIRS_SNPP_SP",
}


def nasa_firms_area(
    settings: Any,
    *,
    source: str = "VIIRS_NOAA20_NRT",
    bbox: str,
    day_range: int = 1,
    date_value: str = "",
) -> dict[str, Any]:
    map_key = _setting(settings, "nasa_firms_map_key")
    if not map_key:
        raise PermissionError("NASA FIRMS MAP_KEY is not configured (SC_SI_NASA_FIRMS_MAP_KEY).")
    if not re.fullmatch(r"[A-Za-z0-9_-]{8,128}", map_key):
        raise ValueError("configured NASA FIRMS MAP_KEY has an invalid format")
    source_id = (source or "VIIRS_NOAA20_NRT").strip().upper()
    if source_id not in _FIRMS_SOURCES:
        raise ValueError("unsupported NASA FIRMS source")
    west, south, east, north = _parse_bbox(bbox, max_width=30.0, max_height=30.0)
    days = int(day_range)
    if not 1 <= days <= 5:
        raise ValueError("day_range must be between 1 and 5")
    date_part = ""
    if date_value:
        try:
            parsed = date.fromisoformat(date_value)
        except ValueError as exc:
            raise ValueError("date must be YYYY-MM-DD") from exc
        date_part = f"/{parsed.isoformat()}"
    base = _setting(settings, "nasa_firms_base_url", _default_base("nasa-firms-area-api")).rstrip("/")
    area = f"{west:g},{south:g},{east:g},{north:g}"
    url = f"{base}/{quote(map_key, safe='')}/{quote(source_id, safe='')}/{quote(area, safe=',.-')}/{days}{date_part}"
    records = _request_csv(url, timeout=_timeout(settings))
    return {
        "ok": True,
        "version": VERSION,
        "connector_id": "nasa-firms-area-api",
        "source": "NASA LANCE FIRMS Area API",
        "mode": "LIVE",
        "configured": True,
        "sensor_source": source_id,
        "record_count": len(records),
        "records": records,
        "interpretation_boundary": "FIRMS records are satellite thermal-anomaly detections. They are not complete wildfire incident, perimeter, containment, cause, evacuation, or burned-area records.",
        "retrieved_at": _now(),
    }


_NASS_ALLOWED_FILTERS = {
    "source_desc", "sector_desc", "group_desc", "commodity_desc", "class_desc", "prodn_practice_desc",
    "util_practice_desc", "statisticcat_desc", "unit_desc", "short_desc", "domain_desc", "agg_level_desc",
    "state_alpha", "state_name", "county_name", "region_desc", "zip_5", "watershed_code", "year",
    "freq_desc", "begin_code", "end_code", "reference_period_desc", "week_ending", "load_time",
}


def usda_nass_quickstats(settings: Any, *, filters: list[str], limit: int = 100) -> dict[str, Any]:
    api_key = _setting(settings, "usda_nass_api_key")
    if not api_key:
        raise PermissionError("USDA NASS API key is not configured (SC_SI_USDA_NASS_API_KEY).")
    if not re.fullmatch(r"[A-Za-z0-9_-]{8,128}", api_key):
        raise ValueError("configured USDA NASS API key has an invalid format")
    if not filters or len(filters) > 12:
        raise ValueError("between 1 and 12 Quick Stats filters are required")
    params: dict[str, str] = {"key": api_key, "format": "JSON"}
    substantive = False
    for item in filters:
        if "=" not in item:
            raise ValueError("Quick Stats filters must use name=value")
        key, value = item.split("=", 1)
        key = key.strip().lower()
        value = value.strip()
        if key not in _NASS_ALLOWED_FILTERS:
            raise ValueError(f"unsupported Quick Stats filter: {key}")
        if not value or len(value) > 160 or any(ch in value for ch in "\r\n"):
            raise ValueError(f"invalid Quick Stats filter value for {key}")
        params[key] = value
        if key in {"commodity_desc", "sector_desc", "group_desc", "state_alpha", "state_name", "county_name", "year", "agg_level_desc"}:
            substantive = True
    if not substantive:
        raise ValueError("Quick Stats query requires at least one commodity/sector/geography/year/aggregation filter")
    limit_n = max(1, min(500, int(limit)))
    base = _setting(settings, "usda_nass_quickstats_url", _default_base("usda-nass-quick-stats"))
    # Quick Stats documents get_counts as the authoritative preflight for result size.
    # Use it before api_GET so Site Intelligence never proxies a potentially 50,000-row query.
    count_base = re.sub(r"/api_GET/?$", "/get_counts/", base.rstrip("/"))
    count_payload = _request_json(count_base + "?" + urlencode({k: v for k, v in params.items() if k != "format"}), timeout=_timeout(settings))
    try:
        upstream_count = int(str((count_payload or {}).get("count", "0")).replace(",", "")) if isinstance(count_payload, dict) else 0
    except ValueError:
        raise RuntimeError("USDA NASS Quick Stats returned an invalid count preflight.")
    if upstream_count > limit_n:
        raise ValueError(f"Quick Stats query matches {upstream_count} records; narrow filters to {limit_n} or fewer")
    data = _request_json(base + "?" + urlencode(params), timeout=_timeout(settings))
    rows = data.get("data", []) if isinstance(data, dict) else []
    return {
        "ok": True,
        "version": VERSION,
        "connector_id": "usda-nass-quick-stats",
        "source": "USDA NASS Quick Stats API",
        "mode": "LIVE",
        "configured": True,
        "record_count": len(rows) if isinstance(rows, list) else 0,
        "upstream_count": upstream_count,
        "data": data,
        "interpretation_boundary": "Quick Stats values are official survey/census statistical estimates; aggregation, revision, suppression and methodology context remain source evidence.",
        "retrieved_at": _now(),
    }


def nasa_cmr_graphql_collections(
    settings: Any,
    *,
    keyword: str = "",
    short_name: str = "",
    provider: str = "",
    bounding_box: str = "",
    temporal: str = "",
    limit: int = 20,
) -> dict[str, Any]:
    if not any((keyword.strip(), short_name.strip(), provider.strip(), bounding_box.strip(), temporal.strip())):
        raise ValueError("at least one CMR GraphQL collection filter is required")
    limit_n = max(1, min(100, int(limit)))
    params: dict[str, Any] = {"limit": limit_n}
    if keyword:
        params["keyword"] = keyword.strip()[:160]
    if short_name:
        params["shortName"] = short_name.strip()[:120]
    if provider:
        params["provider"] = provider.strip()[:80]
    if bounding_box:
        west, south, east, north = _parse_bbox(bounding_box, max_width=360.0, max_height=180.0)
        params["boundingBox"] = [f"{west:g},{south:g},{east:g},{north:g}"]
    if temporal:
        if len(temporal) > 100 or "," not in temporal:
            raise ValueError("temporal must be a bounded CMR temporal range")
        params["temporal"] = temporal.strip()
    query = """query Collections($params: CollectionsInput) { collections(params: $params) { count cursor items { conceptId shortName title provider version timeStart timeEnd hasGranules cloudHosted } } }"""
    payload = {"query": query, "variables": {"params": params}}
    headers: dict[str, str] = {}
    token = _setting(settings, "nasa_earthdata_token")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    base = _setting(settings, "nasa_cmr_graphql_url", _default_base("nasa-cmr-graphql"))
    data = _post_json(base, payload, timeout=_timeout(settings), headers=headers)
    if isinstance(data, dict) and data.get("errors"):
        raise RuntimeError("NASA CMR GraphQL returned a query error.")
    collections = (((data or {}).get("data") or {}).get("collections") or {}) if isinstance(data, dict) else {}
    items = collections.get("items", []) if isinstance(collections, dict) else []
    return {
        "ok": True,
        "version": VERSION,
        "connector_id": "nasa-cmr-graphql",
        "source": "NASA CMR GraphQL",
        "mode": "DISCOVERY",
        "record_count": len(items) if isinstance(items, list) else 0,
        "upstream_count": collections.get("count") if isinstance(collections, dict) else None,
        "collections": items,
        "data": data,
        "interpretation_boundary": "CMR GraphQL results are authoritative metadata/discovery records, not underlying scientific observation values.",
        "retrieved_at": _now(),
    }

# Preserve Expansion I/II callable surface for the application router.
usgs_water_latest = expansion_ii.usgs_water_latest
noaa_erddap_search = expansion_ii.noaa_erddap_search
noaa_erddap_tabledap = expansion_ii.noaa_erddap_tabledap
nasa_exoplanet_planets = expansion_ii.nasa_exoplanet_planets
unhcr_population = expansion_ii.unhcr_population
nasa_cmr_collections = expansion_ii.nasa_cmr_collections
noaa_coops_data = expansion_ii.noaa_coops_data
ncei_access_data = expansion_ii.ncei_access_data
obis_occurrences = expansion_ii.obis_occurrences
eurostat_statistics = expansion_ii.eurostat_statistics
usda_soil_mapunits = expansion_ii.usda_soil_mapunits
