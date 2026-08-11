from __future__ import annotations

"""Site Intelligence v4.35.3.1 authoritative connector expansion I.

The connector layer deliberately keeps authoritative payloads and missing values
intact.  It normalizes only enough structure for the public workspaces to show
source, time, units, quality/status, and retrieval provenance.  It never turns a
missing value into zero and never treats discovery metadata as an observation.
"""

from datetime import datetime, timezone
import json
import math
import re
from typing import Any, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urljoin
from urllib.request import Request, urlopen

from .version import APP_VERSION

VERSION = APP_VERSION
CONTRACT = "authoritative-connector-expansion-i"
USER_AGENT = "SustainableCatalyst-SiteIntelligence/4.35.3.1 (+https://sustainablecatalyst.com)"
MAX_RESPONSE_BYTES = 4 * 1024 * 1024

CONNECTORS: tuple[dict[str, Any], ...] = (
    {
        "id": "usgs-water-ogc-v0",
        "title": "USGS Water Data OGC API",
        "organization": "U.S. Geological Survey",
        "workspace": "Hydrology, Rivers, Flood & Drought",
        "mode": "LIVE",
        "protocol": "OGC API Features / JSON",
        "base_url_setting": "usgs_water_base_url",
        "authentication": "Public read; optional API key can increase rate limits.",
        "boundary": "A monitoring-location observation is not a flood warning, water-rights determination, or guarantee of current site operation.",
    },
    {
        "id": "noaa-coastwatch-erddap",
        "title": "NOAA CoastWatch ERDDAP",
        "organization": "NOAA CoastWatch / OceanWatch",
        "workspace": "Ocean Surface",
        "mode": "LIVE",
        "protocol": "ERDDAP REST / tabledap",
        "base_url_setting": "noaa_erddap_base_url",
        "authentication": "No credentials required for public datasets.",
        "boundary": "Dataset variables, quality flags, temporal resolution, analysis/forecast status, and fill values remain dataset-specific.",
    },
    {
        "id": "nasa-exoplanet-tap",
        "title": "NASA Exoplanet Archive TAP",
        "organization": "NASA Exoplanet Science Institute / IPAC",
        "workspace": "Exoplanets, Habitability & Biosignatures",
        "mode": "LIVE",
        "protocol": "TAP / ADQL / JSON",
        "base_url_setting": "nasa_exoplanet_tap_url",
        "authentication": "Public query service.",
        "boundary": "Planetary parameters are published archive values with source-specific uncertainty; equilibrium temperature is not surface temperature or evidence of habitability.",
    },
    {
        "id": "unhcr-refugee-statistics-v1",
        "title": "UNHCR Refugee Statistics API",
        "organization": "UN High Commissioner for Refugees",
        "workspace": "Humanitarian Intelligence",
        "mode": "LIVE",
        "protocol": "REST / JSON",
        "base_url_setting": "unhcr_population_base_url",
        "authentication": "Public read API.",
        "boundary": "UNHCR statistics are official periodic population statistics, not a real-time movement tracker or legal-status determination for an individual.",
    },
    {
        "id": "nasa-cmr-search",
        "title": "NASA Common Metadata Repository Search",
        "organization": "NASA EOSDIS",
        "workspace": "Earth / Science / Space discovery",
        "mode": "DISCOVERY",
        "protocol": "REST / JSON / UMM / STAC discovery",
        "base_url_setting": "nasa_cmr_base_url",
        "authentication": "Guest collection search supported; restricted assets may require Earthdata authentication.",
        "boundary": "CMR collection metadata establishes discoverability and dataset context; it is not itself an Earth observation value.",
    },
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clamp_int(value: int, low: int, high: int) -> int:
    return max(low, min(high, int(value)))


def _finite(value: float, name: str, low: float, high: float) -> float:
    parsed = float(value)
    if not math.isfinite(parsed) or parsed < low or parsed > high:
        raise ValueError(f"{name} must be between {low:g} and {high:g}")
    return parsed


def _setting(settings: Any, name: str, default: str) -> str:
    value = str(getattr(settings, name, "") or "").strip() if settings is not None else ""
    return value or default


def _request_json(
    url: str,
    *,
    timeout: int = 8,
    headers: dict[str, str] | None = None,
    max_bytes: int = MAX_RESPONSE_BYTES,
) -> Any:
    request_headers = {"Accept": "application/json", "User-Agent": USER_AGENT}
    request_headers.update(headers or {})
    req = Request(url, headers=request_headers, method="GET")
    try:
        with urlopen(req, timeout=timeout) as response:
            raw = response.read(max_bytes + 1)
            if len(raw) > max_bytes:
                raise ValueError("Authoritative API response exceeded the public connector size limit.")
            charset = response.headers.get_content_charset() or "utf-8"
            return json.loads(raw.decode(charset))
    except HTTPError as exc:
        raise RuntimeError(f"Authoritative API returned HTTP {exc.code}.") from exc
    except URLError as exc:
        raise RuntimeError("Authoritative API could not be reached.") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError("Authoritative API returned invalid JSON.") from exc


def connector_catalog(settings: Any = None) -> dict[str, Any]:
    rows = []
    for connector in CONNECTORS:
        row = dict(connector)
        row["configured_base_url"] = _setting(settings, connector["base_url_setting"], _default_base(connector["id"]))
        row["network_check_performed"] = False
        if connector["id"] == "usgs-water-ogc-v0":
            row["optional_api_key_configured"] = bool(str(getattr(settings, "usgs_water_api_key", "") or "").strip()) if settings is not None else False
        rows.append(row)
    return {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "connector_count": len(rows),
        "live_connector_count": sum(1 for row in rows if row["mode"] == "LIVE"),
        "discovery_connector_count": sum(1 for row in rows if row["mode"] == "DISCOVERY"),
        "connectors": rows,
        "principles": [
            "Retrieve from the authoritative machine-readable service rather than substituting a sample value.",
            "Preserve source identifiers, observation dates, units, status/quality fields, and null values.",
            "Do not promote discovery metadata to an observation.",
            "A connector failure is an availability state, not evidence that the measured phenomenon is absent.",
        ],
        "generated_at": _now(),
    }


def connector_readiness(settings: Any = None) -> dict[str, Any]:
    catalog = connector_catalog(settings)
    checks = {
        "five_authoritative_interfaces_implemented": catalog["connector_count"] == 5,
        "four_observation_or_record_connectors_live_capable": catalog["live_connector_count"] == 4,
        "nasa_cmr_discovery_kept_distinct": catalog["discovery_connector_count"] == 1,
        "missing_values_preserved_by_contract": True,
        "network_checks_not_required_for_deterministic_readiness": True,
    }
    return {
        "ok": all(checks.values()),
        "version": VERSION,
        "contract": CONTRACT,
        "network_calls_performed": False,
        "checks": checks,
        "configuration": {
            "usgs_water_api_key_optional": "SC_SI_USGS_WATER_API_KEY",
            "connector_base_urls_have_safe_defaults": True,
        },
        "generated_at": _now(),
    }


def _default_base(connector_id: str) -> str:
    return {
        "usgs-water-ogc-v0": "https://api.waterdata.usgs.gov/ogcapi/v0",
        "noaa-coastwatch-erddap": "https://coastwatch.noaa.gov/erddap",
        "nasa-exoplanet-tap": "https://exoplanetarchive.ipac.caltech.edu/TAP/sync",
        "unhcr-refugee-statistics-v1": "https://api.unhcr.org/population/v1",
        "nasa-cmr-search": "https://cmr.earthdata.nasa.gov/search",
    }[connector_id]


def _numeric_or_none(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def usgs_water_latest(
    settings: Any,
    *,
    latitude: float,
    longitude: float,
    radius_degrees: float = 0.10,
    limit: int = 50,
    parameter_code: str = "",
) -> dict[str, Any]:
    lat = _finite(latitude, "latitude", -90, 90)
    lon = _finite(longitude, "longitude", -180, 180)
    radius = float(radius_degrees)
    if not math.isfinite(radius) or radius <= 0 or radius > 5:
        raise ValueError("radius_degrees must be greater than 0 and no more than 5")
    limit = _clamp_int(limit, 1, 250)
    south, north = max(-90.0, lat - radius), min(90.0, lat + radius)
    west, east = max(-180.0, lon - radius), min(180.0, lon + radius)
    params = {
        "f": "json",
        "bbox": f"{west:.6f},{south:.6f},{east:.6f},{north:.6f}",
        "limit": str(limit),
    }
    base = _setting(settings, "usgs_water_base_url", _default_base("usgs-water-ogc-v0")).rstrip("/")
    url = f"{base}/collections/latest-continuous/items?{urlencode(params)}"
    headers: dict[str, str] = {}
    api_key = str(getattr(settings, "usgs_water_api_key", "") or "").strip() if settings is not None else ""
    if api_key:
        headers["X-Api-Key"] = api_key
    payload = _request_json(url, timeout=int(getattr(settings, "external_request_timeout_seconds", 8)), headers=headers)
    features = payload.get("features", []) if isinstance(payload, dict) else []
    wanted = re.sub(r"[^0-9A-Za-z_-]", "", parameter_code or "").strip()
    observations: list[dict[str, Any]] = []
    for feature in features:
        if not isinstance(feature, dict):
            continue
        props = feature.get("properties") if isinstance(feature.get("properties"), dict) else {}
        pcode = str(props.get("parameter_code") or "")
        if wanted and pcode.lower() != wanted.lower():
            continue
        geometry = feature.get("geometry") if isinstance(feature.get("geometry"), dict) else {}
        coordinates = geometry.get("coordinates") if isinstance(geometry.get("coordinates"), list) else None
        raw_value = props.get("value")
        observations.append({
            "feature_id": feature.get("id"),
            "time_series_id": props.get("time_series_id"),
            "monitoring_location_id": props.get("monitoring_location_id"),
            "parameter_code": props.get("parameter_code"),
            "time": props.get("time"),
            "value": raw_value,
            "numeric_value": _numeric_or_none(raw_value),
            "unit_of_measure": props.get("unit_of_measure"),
            "approval_status": props.get("approval_status"),
            "qualifier": props.get("qualifier"),
            "last_modified": props.get("last_modified"),
            "coordinates": coordinates,
            "missing": raw_value in (None, ""),
        })
    return {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "connector_id": "usgs-water-ogc-v0",
        "source": "U.S. Geological Survey Water Data OGC API",
        "query": {"latitude": lat, "longitude": lon, "radius_degrees": radius, "parameter_code": wanted or None, "limit": limit},
        "observation_count": len(observations),
        "observations": observations,
        "upstream_number_matched": payload.get("numberMatched") if isinstance(payload, dict) else None,
        "upstream_number_returned": payload.get("numberReturned") if isinstance(payload, dict) else None,
        "retrieved_at": _now(),
        "source_url": url,
        "boundary": "USGS latest-continuous values retain approval/provisional status and qualifiers. Missing source values remain missing.",
    }


def _erddap_rows(payload: Any) -> tuple[list[str], list[dict[str, Any]]]:
    table = payload.get("table", {}) if isinstance(payload, dict) else {}
    names = table.get("columnNames", []) if isinstance(table, dict) else []
    rows = table.get("rows", []) if isinstance(table, dict) else []
    if not isinstance(names, list) or not isinstance(rows, list):
        return [], []
    columns = [str(name) for name in names]
    records: list[dict[str, Any]] = []
    for raw in rows:
        if not isinstance(raw, list):
            continue
        record = {columns[index]: (raw[index] if index < len(raw) else None) for index in range(len(columns))}
        records.append(record)
    return columns, records


def noaa_erddap_search(settings: Any, *, query: str, limit: int = 20) -> dict[str, Any]:
    text = (query or "").strip()
    if not text:
        raise ValueError("query is required")
    limit = _clamp_int(limit, 1, 100)
    base = _setting(settings, "noaa_erddap_base_url", _default_base("noaa-coastwatch-erddap")).rstrip("/")
    params = {"page": "1", "itemsPerPage": str(limit), "searchFor": text}
    url = f"{base}/search/index.json?{urlencode(params)}"
    payload = _request_json(url, timeout=int(getattr(settings, "external_request_timeout_seconds", 8)))
    columns, records = _erddap_rows(payload)
    return {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "connector_id": "noaa-coastwatch-erddap",
        "source": "NOAA CoastWatch ERDDAP",
        "query": text,
        "result_count": len(records),
        "columns": columns,
        "datasets": records,
        "retrieved_at": _now(),
        "source_url": url,
        "boundary": "ERDDAP search results are dataset discovery records; consult dataset metadata before interpreting variables or temporal coverage.",
    }


_DATASET_RE = re.compile(r"^[A-Za-z0-9_.-]{1,128}$")
_VARIABLE_RE = re.compile(r"^[A-Za-z0-9_]+$")
_CONSTRAINT_RE = re.compile(r"^[A-Za-z0-9_]+(?:<=|>=|!=|=|<|>)[A-Za-z0-9_.:+\-TZ'\"]+$")


def noaa_erddap_tabledap(
    settings: Any,
    *,
    dataset_id: str,
    variables: Iterable[str],
    constraints: Iterable[str] = (),
) -> dict[str, Any]:
    dataset = (dataset_id or "").strip()
    if not _DATASET_RE.fullmatch(dataset):
        raise ValueError("dataset_id contains unsupported characters")
    fields = [str(item).strip() for item in variables if str(item).strip()]
    if not fields or len(fields) > 20 or any(not _VARIABLE_RE.fullmatch(item) for item in fields):
        raise ValueError("variables must contain 1 to 20 ERDDAP variable names")
    clauses = [str(item).strip() for item in constraints if str(item).strip()]
    if dataset != "allDatasets" and not clauses:
        raise ValueError("At least one bounded ERDDAP constraint is required for dataset data retrieval")
    if len(clauses) > 12 or any(not _CONSTRAINT_RE.fullmatch(item) for item in clauses):
        raise ValueError("An ERDDAP constraint contains unsupported characters or syntax")
    base = _setting(settings, "noaa_erddap_base_url", _default_base("noaa-coastwatch-erddap")).rstrip("/")
    query_parts = [",".join(fields)]
    query_parts.extend(quote(clause, safe="=<>!:'\".+-_TZ") for clause in clauses)
    url = f"{base}/tabledap/{quote(dataset, safe='._-')}.json?" + "&".join(query_parts)
    payload = _request_json(url, timeout=int(getattr(settings, "external_request_timeout_seconds", 8)))
    columns, records = _erddap_rows(payload)
    return {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "connector_id": "noaa-coastwatch-erddap",
        "source": "NOAA CoastWatch ERDDAP tabledap",
        "dataset_id": dataset,
        "variables": fields,
        "constraints": clauses,
        "record_count": len(records),
        "columns": columns,
        "records": records,
        "retrieved_at": _now(),
        "source_url": url,
        "boundary": "Returned values retain the dataset's own variable semantics. Nulls remain null; fill-value handling and quality flags must be interpreted from dataset metadata.",
    }


def nasa_exoplanet_planets(settings: Any, *, target: str = "", limit: int = 25) -> dict[str, Any]:
    limit = _clamp_int(limit, 1, 200)
    columns = "pl_name,hostname,discoverymethod,disc_year,pl_orbper,pl_rade,pl_bmasse,pl_eqt,sy_dist"
    query = f"select top {limit} {columns} from pscomppars"
    target_text = (target or "").strip()
    if target_text:
        safe = target_text.lower().replace("'", "''")[:120]
        query += f" where lower(pl_name) like '%{safe}%' or lower(hostname) like '%{safe}%'"
    query += " order by pl_name"
    base = _setting(settings, "nasa_exoplanet_tap_url", _default_base("nasa-exoplanet-tap"))
    url = f"{base}?{urlencode({'query': query, 'format': 'json'})}"
    payload = _request_json(url, timeout=int(getattr(settings, "external_request_timeout_seconds", 8)))
    records = payload if isinstance(payload, list) else []
    normalized = []
    for row in records:
        if not isinstance(row, dict):
            continue
        normalized.append({
            "planet_name": row.get("pl_name"),
            "host_name": row.get("hostname"),
            "discovery_method": row.get("discoverymethod"),
            "discovery_year": row.get("disc_year"),
            "orbital_period_days": row.get("pl_orbper"),
            "planet_radius_earth": row.get("pl_rade"),
            "planet_mass_earth": row.get("pl_bmasse"),
            "equilibrium_temperature_k": row.get("pl_eqt"),
            "system_distance_pc": row.get("sy_dist"),
            "raw": row,
        })
    return {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "connector_id": "nasa-exoplanet-tap",
        "source": "NASA Exoplanet Archive TAP",
        "target": target_text or None,
        "record_count": len(normalized),
        "records": normalized,
        "units": {"orbital_period_days": "day", "planet_radius_earth": "Earth radii", "planet_mass_earth": "Earth masses", "equilibrium_temperature_k": "K", "system_distance_pc": "pc"},
        "retrieved_at": _now(),
        "source_url": url,
        "boundary": "Equilibrium temperature is an archive parameter, not a measured surface temperature or a habitability determination.",
    }


def _unhcr_rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("items", "data", "results"):
        value = payload.get(key)
        if isinstance(value, list):
            return [row for row in value if isinstance(row, dict)]
    return []


def unhcr_population(
    settings: Any,
    *,
    year: int | None = None,
    origin: str = "",
    asylum: str = "",
    limit: int = 100,
) -> dict[str, Any]:
    limit = _clamp_int(limit, 1, 200)
    params: dict[str, str] = {"limit": str(limit)}
    if year is not None:
        year_value = int(year)
        if year_value < 1951 or year_value > datetime.now(timezone.utc).year + 1:
            raise ValueError("year is outside the supported UNHCR statistical range")
        params["year"] = str(year_value)
    origin_code = re.sub(r"[^A-Za-z]", "", origin or "").upper()
    asylum_code = re.sub(r"[^A-Za-z]", "", asylum or "").upper()
    if origin and len(origin_code) != 3:
        raise ValueError("origin must be an ISO3 country code")
    if asylum and len(asylum_code) != 3:
        raise ValueError("asylum must be an ISO3 country code")
    if origin_code:
        params["coo"] = origin_code
    if asylum_code:
        params["coa"] = asylum_code
    if origin_code or asylum_code:
        params["cf_type"] = "ISO"
    base = _setting(settings, "unhcr_population_base_url", _default_base("unhcr-refugee-statistics-v1")).rstrip("/")
    url = f"{base}/population/?{urlencode(params)}"
    payload = _request_json(url, timeout=int(getattr(settings, "external_request_timeout_seconds", 8)))
    records = _unhcr_rows(payload)
    return {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "connector_id": "unhcr-refugee-statistics-v1",
        "source": "UNHCR Refugee Statistics API",
        "query": {"year": year, "origin": origin_code or None, "asylum": asylum_code or None, "limit": limit},
        "record_count": len(records),
        "records": records,
        "retrieved_at": _now(),
        "source_url": url,
        "boundary": "These are official periodic aggregate statistics. Preserve population category, reference year, origin/asylum geography, and footnotes before drawing conclusions.",
    }


def nasa_cmr_collections(
    settings: Any,
    *,
    query: str,
    limit: int = 20,
    provider: str = "",
    temporal: str = "",
    bounding_box: str = "",
) -> dict[str, Any]:
    text = (query or "").strip()
    if not text:
        raise ValueError("query is required")
    limit = _clamp_int(limit, 1, 200)
    params: list[tuple[str, str]] = [("keyword", text), ("page_size", str(limit)), ("include_granule_counts", "true")]
    if provider.strip():
        params.append(("provider", provider.strip()[:80]))
    if temporal.strip():
        params.append(("temporal", temporal.strip()[:120]))
    if bounding_box.strip():
        if not re.fullmatch(r"[-0-9., ]{7,100}", bounding_box.strip()):
            raise ValueError("bounding_box must contain four numeric comma-separated coordinates")
        params.append(("bounding_box", bounding_box.strip()))
    base = _setting(settings, "nasa_cmr_base_url", _default_base("nasa-cmr-search")).rstrip("/")
    url = f"{base}/collections.json?{urlencode(params)}"
    payload = _request_json(
        url,
        timeout=int(getattr(settings, "external_request_timeout_seconds", 8)),
        headers={"Client-Id": "sustainable-catalyst-site-intelligence"},
    )
    feed = payload.get("feed", {}) if isinstance(payload, dict) else {}
    entries = feed.get("entry", []) if isinstance(feed, dict) else []
    records = [row for row in entries if isinstance(row, dict)] if isinstance(entries, list) else []
    return {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "connector_id": "nasa-cmr-search",
        "source": "NASA EOSDIS Common Metadata Repository",
        "mode": "DISCOVERY",
        "query": {"keyword": text, "provider": provider.strip() or None, "temporal": temporal.strip() or None, "bounding_box": bounding_box.strip() or None, "limit": limit},
        "collection_count": len(records),
        "collections": records,
        "retrieved_at": _now(),
        "source_url": url,
        "boundary": "CMR results are collection metadata/discovery records, not observation values. Open the cited collection/data-service links to retrieve scientific data.",
    }
