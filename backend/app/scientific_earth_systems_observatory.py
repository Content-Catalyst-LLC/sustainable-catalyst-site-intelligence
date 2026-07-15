"""Scientific and Earth Systems Observatory for Site Intelligence v2.4.0.

This module provides a public-safe, server-side bridge to Sustainable Catalyst
Core v2.8.0 scientific records and data-fabric services. It preserves source,
license, attribution, observation time, mission, instrument, dataset, quality,
and file-format context. It never exposes Core credentials, performs no silent
scientific inference, and never fabricates records when Core is unavailable.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
import os
from typing import Any, Mapping
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .global_conditions_observatory import (
    CoreReadConfig,
    _core_json,
    _items,
    _safe_text,
    _safe_url,
    _validate_bbox,
    core_read_config,
)

RELEASE_SCHEMA = "sc-site-intelligence-scientific-earth-systems/1.0"
RECORDS_SCHEMA = "sc-site-intelligence-scientific-records/1.0"
ASSETS_SCHEMA = "sc-site-intelligence-scientific-assets/1.0"
LAYERS_SCHEMA = "sc-site-intelligence-scientific-layers/1.0"
SERIES_SCHEMA = "sc-site-intelligence-scientific-timeseries/1.0"
MAX_RECORDS = 300
MAX_ASSETS = 250
MAX_LAYERS = 160
MAX_SERIES = 200
MAX_POINTS = 500

_ALLOWED_RECORD_TYPES = {
    "earth_science_dataset",
    "astronomy_image",
    "environmental_observation",
    "forecast_field",
    "water_observation",
    "biomedical_database_record",
    "chemical_compound",
    "biodiversity_occurrence",
    "material",
    "telescope_observation",
    "astronomy_catalog_record",
}

_RECORD_TYPE_LABELS = {
    "earth_science_dataset": "Earth science dataset",
    "astronomy_image": "Astronomy image",
    "environmental_observation": "Environmental observation",
    "forecast_field": "Forecast field",
    "water_observation": "Water observation",
    "biomedical_database_record": "Biomedical database record",
    "chemical_compound": "Chemical compound",
    "biodiversity_occurrence": "Biodiversity occurrence",
    "material": "Materials science record",
    "telescope_observation": "Telescope observation",
    "astronomy_catalog_record": "Astronomy catalog record",
}

_FAMILY_LABELS = {
    "earth-systems": "Earth systems",
    "climate-atmosphere": "Climate and atmosphere",
    "water-hazards": "Water and hazards",
    "space-astronomy": "Space and astronomy",
    "biology-biodiversity": "Biology and biodiversity",
    "chemistry-materials": "Chemistry and materials",
    "scientific-infrastructure": "Scientific infrastructure",
    "other": "Other science",
}

_SAFE_FORMATS = {
    "geojson", "stac", "wms", "wmts", "cog", "geotiff", "pmtiles",
    "geoparquet", "netcdf", "zarr", "fits", "votable", "grib2", "sdmx",
    "tap", "adql", "json", "xml", "csv", "parquet", "image", "unknown",
}
_SAFE_LAYER_TYPES = {"geojson", "vector", "raster", "wms", "wmts", "stac", "cog", "pmtiles"}
_SENSITIVE_KEYS = {
    "api_key", "apikey", "key", "token", "authorization", "password", "secret",
    "credential", "write_api_key", "public_api_key", "raw_record_id",
}


@dataclass(frozen=True)
class ScienceObservatoryConfig:
    enabled: bool
    timeout_seconds: float
    cache_ttl_seconds: int


def _as_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on", "enabled"}


def science_observatory_config(settings: Any = None) -> ScienceObservatoryConfig:
    enabled = getattr(settings, "scientific_earth_systems_enabled", None)
    if enabled is None:
        enabled = os.getenv("SC_SI_SCIENTIFIC_EARTH_SYSTEMS_ENABLED", "true")
    timeout = getattr(settings, "scientific_earth_systems_timeout_seconds", None)
    if timeout is None:
        timeout = os.getenv("SC_SI_SCIENTIFIC_EARTH_SYSTEMS_TIMEOUT_SECONDS", "9")
    ttl = getattr(settings, "scientific_earth_systems_cache_ttl_seconds", None)
    if ttl is None:
        ttl = os.getenv("SC_SI_SCIENTIFIC_EARTH_SYSTEMS_CACHE_TTL_SECONDS", "120")
    return ScienceObservatoryConfig(
        enabled=_as_bool(enabled, True),
        timeout_seconds=max(2.0, min(float(timeout), 30.0)),
        cache_ttl_seconds=max(15, min(int(ttl), 1800)),
    )


def _core_config(settings: Any = None) -> CoreReadConfig:
    base = core_read_config(settings)
    local = science_observatory_config(settings)
    return CoreReadConfig(
        enabled=bool(base.enabled and local.enabled),
        base_url=base.base_url,
        api_key=base.api_key,
        timeout_seconds=local.timeout_seconds,
        cache_ttl_seconds=local.cache_ttl_seconds,
    )


def _sensitive_key(value: Any) -> bool:
    normalized = "".join(character for character in str(value or "").lower() if character.isalnum())
    return normalized in {"key", "rawrecordid"} or any(
        token in normalized for token in ("apikey", "token", "authorization", "password", "secret", "credential")
    )


def _public_url(value: Any) -> str:
    safe = _safe_url(value)
    if not safe:
        return ""
    parts = urlsplit(safe)
    query = [(key, item) for key, item in parse_qsl(parts.query, keep_blank_values=True) if not _sensitive_key(key)]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query, doseq=True), parts.fragment))


def _safe_list(value: Any, limit: int = 40, item_limit: int = 240) -> list[str]:
    if not isinstance(value, list):
        return []
    output: list[str] = []
    for item in value[:limit]:
        clean = _safe_text(item, item_limit)
        if clean and clean not in output:
            output.append(clean)
    return output


def _safe_mapping(value: Any, *, depth: int = 0) -> dict[str, Any]:
    if not isinstance(value, Mapping) or depth > 2:
        return {}
    output: dict[str, Any] = {}
    for raw_key, raw_value in value.items():
        key = _safe_text(raw_key, 80)
        if not key or key.lower() in _SENSITIVE_KEYS or _sensitive_key(key):
            continue
        if isinstance(raw_value, Mapping):
            nested = _safe_mapping(raw_value, depth=depth + 1)
            if nested:
                output[key] = nested
        elif isinstance(raw_value, list):
            clean = []
            for item in raw_value[:30]:
                if item is None or isinstance(item, (bool, int, float)):
                    clean.append(item)
                elif not isinstance(item, (dict, list)):
                    clean.append(_safe_text(item, 240))
            if clean:
                output[key] = clean
        elif raw_value is None or isinstance(raw_value, (bool, int, float)):
            output[key] = raw_value
        else:
            output[key] = _safe_text(raw_value, 500)
    return output


def _geometry(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, Mapping):
        return None
    geometry_type = value.get("type")
    coordinates = value.get("coordinates")
    if geometry_type not in {"Point", "MultiPoint", "LineString", "MultiLineString", "Polygon", "MultiPolygon"}:
        return None
    if not isinstance(coordinates, list):
        return None
    return {"type": geometry_type, "coordinates": coordinates}


def _family(record: Mapping[str, Any]) -> str:
    record_type = str(record.get("record_type") or "").lower()
    discipline = str(record.get("discipline") or "").lower()
    text = " ".join(str(record.get(field) or "").lower() for field in (
        "title", "summary", "collection", "mission", "instrument", "target", "dataset_id"
    ))
    if record_type in {"telescope_observation", "astronomy_catalog_record", "astronomy_image"} or any(
        term in f"{discipline} {text}" for term in ("astronomy", "astrophysics", "space", "telescope", "jwst", "hubble")
    ):
        return "space-astronomy"
    if record_type in {"biodiversity_occurrence", "biomedical_database_record"} or any(
        term in f"{discipline} {text}" for term in ("biology", "biodiversity", "species", "genomic", "protein", "biomedical")
    ):
        return "biology-biodiversity"
    if record_type in {"chemical_compound", "material"} or any(
        term in f"{discipline} {text}" for term in ("chemistry", "compound", "material", "crystal", "molecule")
    ):
        return "chemistry-materials"
    if record_type in {"earth_science_dataset", "environmental_observation"}:
        return "earth-systems"
    if record_type in {"water_observation"} or any(
        term in f"{discipline} {text}" for term in ("hydrology", "river", "streamflow", "earthquake", "hazard", "fire")
    ):
        return "water-hazards"
    if record_type in {"forecast_field"} or any(
        term in f"{discipline} {text}" for term in ("weather", "climate", "atmosphere", "forecast", "meteorolog")
    ):
        return "climate-atmosphere"
    if any(
        term in f"{discipline} {text}" for term in ("earth science", "ocean", "land", "satellite", "remote sensing", "environment")
    ):
        return "earth-systems"
    if any(term in f"{discipline} {text}" for term in ("archive", "catalog", "infrastructure", "database")):
        return "scientific-infrastructure"
    return "other"


def _quality_label(value: Any) -> str:
    text = _safe_text(value, 80).strip().lower().replace("_", " ").replace("-", " ")
    if not text:
        return "QUALITY NOT STATED"
    return text.upper()


def _date_value(record: Mapping[str, Any]) -> str:
    return _safe_text(record.get("observation_start") or record.get("published_at") or record.get("created_at"), 60)


def _public_record(record: Mapping[str, Any]) -> dict[str, Any]:
    record_type = _safe_text(record.get("record_type"), 100)
    if record_type not in _ALLOWED_RECORD_TYPES:
        record_type = "earth_science_dataset"
    output = {
        "id": _safe_text(record.get("id"), 180),
        "source_record_id": _safe_text(record.get("source_record_id"), 240),
        "source_id": _safe_text(record.get("source_id"), 160),
        "connector_id": _safe_text(record.get("connector_id"), 180),
        "record_type": record_type,
        "record_type_label": _RECORD_TYPE_LABELS.get(record_type, record_type.replace("_", " ").title()),
        "discipline": _safe_text(record.get("discipline"), 160),
        "family": "",
        "family_label": "",
        "title": _safe_text(record.get("title"), 600),
        "summary": _safe_text(record.get("summary"), 1800),
        "dataset_id": _safe_text(record.get("dataset_id"), 240),
        "collection": _safe_text(record.get("collection"), 300),
        "mission": _safe_text(record.get("mission"), 240),
        "instrument": _safe_text(record.get("instrument"), 240),
        "target": _safe_text(record.get("target"), 300),
        "doi": _safe_text(record.get("doi"), 220),
        "access_url": _public_url(record.get("access_url")),
        "landing_page_url": _public_url(record.get("landing_page_url")),
        "geometry": _geometry(record.get("geometry")),
        "observation_start": _safe_text(record.get("observation_start"), 60),
        "observation_end": _safe_text(record.get("observation_end"), 60),
        "published_at": _safe_text(record.get("published_at"), 60),
        "display_date": "",
        "identifiers": _safe_mapping(record.get("identifiers")),
        "keywords": _safe_list(record.get("keywords"), 50, 160),
        "variables": _safe_list(record.get("variables"), 50, 160),
        "file_formats": [item.lower() for item in _safe_list(record.get("file_formats"), 30, 80)],
        "quality_status": _safe_text(record.get("quality_status"), 80),
        "quality_label": _quality_label(record.get("quality_status")),
        "license_name": _safe_text(record.get("license_name"), 220),
        "attribution": _safe_text(record.get("attribution"), 500),
        "content_hash": _safe_text(record.get("content_hash"), 180),
        "metadata": _safe_mapping(record.get("metadata")),
    }
    output["family"] = _family(output)
    output["family_label"] = _FAMILY_LABELS[output["family"]]
    output["display_date"] = _date_value(output)
    return output


def _public_asset(asset: Mapping[str, Any]) -> dict[str, Any]:
    fmt = _safe_text(asset.get("format"), 80).lower() or "unknown"
    if fmt not in _SAFE_FORMATS:
        fmt = "unknown"
    return {
        "id": _safe_text(asset.get("id"), 180),
        "scientific_record_id": _safe_text(asset.get("scientific_record_id"), 180),
        "source_id": _safe_text(asset.get("source_id"), 160),
        "connector_id": _safe_text(asset.get("connector_id"), 180),
        "dataset_id": _safe_text(asset.get("dataset_id"), 240),
        "title": _safe_text(asset.get("title"), 500),
        "asset_role": _safe_text(asset.get("asset_role"), 100),
        "media_type": _safe_text(asset.get("media_type"), 160),
        "format": fmt,
        "href": _public_url(asset.get("href")),
        "storage_mode": _safe_text(asset.get("storage_mode"), 80),
        "size_bytes": asset.get("size_bytes") if isinstance(asset.get("size_bytes"), int) else None,
        "checksum": _safe_text(asset.get("checksum"), 180),
        "stac_roles": _safe_list(asset.get("stac_roles"), 20, 100),
        "variables": _safe_list(asset.get("variables"), 40, 160),
        "spatial_extent": asset.get("spatial_extent") if isinstance(asset.get("spatial_extent"), list) else [],
        "temporal_extent": asset.get("temporal_extent") if isinstance(asset.get("temporal_extent"), list) else [],
        "license_name": _safe_text(asset.get("license_name"), 220),
        "attribution": _safe_text(asset.get("attribution"), 500),
        "metadata": _safe_mapping(asset.get("metadata")),
    }


def _public_layer(layer: Mapping[str, Any]) -> dict[str, Any]:
    layer_type = _safe_text(layer.get("layer_type"), 80).lower()
    if layer_type not in _SAFE_LAYER_TYPES:
        layer_type = "raster"
    return {
        "id": _safe_text(layer.get("id"), 180),
        "source_id": _safe_text(layer.get("source_id"), 160),
        "connector_id": _safe_text(layer.get("connector_id"), 180),
        "external_layer_id": _safe_text(layer.get("external_layer_id"), 240),
        "title": _safe_text(layer.get("title"), 500),
        "description": _safe_text(layer.get("description"), 1200),
        "layer_type": layer_type,
        "endpoint_url": _public_url(layer.get("endpoint_url")),
        "tile_template": _public_url(layer.get("tile_template")),
        "style": _safe_mapping(layer.get("style")),
        "bounds": layer.get("bounds") if isinstance(layer.get("bounds"), list) else [],
        "min_zoom": layer.get("min_zoom") if isinstance(layer.get("min_zoom"), int) else None,
        "max_zoom": layer.get("max_zoom") if isinstance(layer.get("max_zoom"), int) else None,
        "time_enabled": bool(layer.get("time_enabled")),
        "license_name": _safe_text(layer.get("license_name"), 220),
        "attribution": _safe_text(layer.get("attribution"), 500),
        "status": _safe_text(layer.get("status"), 80),
        "metadata": _safe_mapping(layer.get("metadata")),
    }


def _public_series(series: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "id": _safe_text(series.get("id"), 180),
        "source_id": _safe_text(series.get("source_id"), 160),
        "connector_id": _safe_text(series.get("connector_id"), 180),
        "metric": _safe_text(series.get("metric"), 240),
        "title": _safe_text(series.get("title"), 500),
        "description": _safe_text(series.get("description"), 1000),
        "dataset_id": _safe_text(series.get("dataset_id"), 240),
        "domain": _safe_text(series.get("domain"), 160),
        "unit": _safe_text(series.get("unit"), 120),
        "frequency": _safe_text(series.get("frequency"), 80),
        "geography_code": _safe_text(series.get("geography_code"), 40),
        "dimensions": _safe_mapping(series.get("dimensions")),
        "license_name": _safe_text(series.get("license_name"), 220),
        "attribution": _safe_text(series.get("attribution"), 500),
    }


def _public_point(point: Mapping[str, Any]) -> dict[str, Any]:
    number = point.get("value_number")
    if not isinstance(number, (int, float)):
        number = None
    return {
        "id": _safe_text(point.get("id"), 180),
        "series_id": _safe_text(point.get("series_id"), 180),
        "observed_at": _safe_text(point.get("observed_at"), 60),
        "value_number": number,
        "value_text": _safe_text(point.get("value_text"), 500),
        "quality_status": _safe_text(point.get("quality_status"), 80),
        "freshness_status": _safe_text(point.get("freshness_status"), 80),
        "dimensions": _safe_mapping(point.get("dimensions")),
    }


def _integration_state(settings: Any = None, error: str = "") -> dict[str, Any]:
    config = _core_config(settings)
    if not science_observatory_config(settings).enabled:
        state, message = "disabled", "The Scientific and Earth Systems Observatory is disabled."
    elif not config.configured:
        state, message = "core-unconfigured", "Platform Core is not configured; no scientific records are fabricated locally."
    elif error:
        state, message = "degraded", error
    else:
        state, message = "connected", "Platform Core scientific records and data fabric are connected."
    return {
        "enabled": science_observatory_config(settings).enabled,
        "configured": config.configured,
        "state": state,
        "message": message,
        "credential_exposed": False,
    }


def _facet(items: list[dict[str, Any]], key: str, label_key: str | None = None, limit: int = 80) -> list[dict[str, Any]]:
    counter: Counter[str] = Counter()
    labels: dict[str, str] = {}
    for item in items:
        value = str(item.get(key) or "").strip()
        if not value:
            continue
        counter[value] += 1
        if label_key:
            labels[value] = str(item.get(label_key) or value)
    return [
        {"id": value, "label": labels.get(value, value.replace("_", " ").title()), "count": count}
        for value, count in counter.most_common(limit)
    ]


def _record_query(
    *, record_type: str = "", discipline: str = "", source_id: str = "", collection: str = "",
    mission: str = "", instrument: str = "", target: str = "", dataset_id: str = "", query: str = "",
    start: str = "", end: str = "", limit: int = 100, offset: int = 0,
) -> dict[str, Any]:
    return {
        "record_type": record_type,
        "discipline": discipline,
        "source_id": source_id,
        "collection": collection,
        "mission": mission,
        "instrument": instrument,
        "target": target,
        "dataset_id": dataset_id,
        "query": query,
        "start": start,
        "end": end,
        "limit": min(max(int(limit), 1), MAX_RECORDS),
        "offset": max(int(offset), 0),
    }


def build_science_records(settings: Any = None, **filters: Any) -> dict[str, Any]:
    config = _core_config(settings)
    generated_at = datetime.now(timezone.utc).isoformat()
    if not config.configured:
        return {"ok": True, "schema": RECORDS_SCHEMA, "version": "2.5.0", "generated_at": generated_at, "records": [], "total": 0, "integration": _integration_state(settings)}
    try:
        payload = _core_json(config, "/api/v1/science/records", _record_query(**filters))
        records = [_public_record(item) for item in _items(payload, "items", "records")]
        records = [item for item in records if item["id"] or item["source_record_id"]]
        meta = payload.get("meta", {}) if isinstance(payload, Mapping) else {}
        pagination = meta.get("pagination", {}) if isinstance(meta, Mapping) else {}
        return {
            "ok": True,
            "schema": RECORDS_SCHEMA,
            "version": "2.5.0",
            "generated_at": generated_at,
            "records": records,
            "total": int(pagination.get("total") or len(records)),
            "integration": _integration_state(settings),
        }
    except RuntimeError as exc:
        return {"ok": True, "schema": RECORDS_SCHEMA, "version": "2.5.0", "generated_at": generated_at, "records": [], "total": 0, "integration": _integration_state(settings, str(exc))}


def build_science_facets(settings: Any = None, limit: int = 300) -> dict[str, Any]:
    result = build_science_records(settings, limit=min(limit, MAX_RECORDS))
    records = result["records"]
    return {
        "ok": True,
        "schema": RELEASE_SCHEMA,
        "version": "2.5.0",
        "families": _facet(records, "family", "family_label"),
        "record_types": _facet(records, "record_type", "record_type_label"),
        "disciplines": _facet(records, "discipline"),
        "sources": _facet(records, "source_id"),
        "missions": _facet(records, "mission"),
        "instruments": _facet(records, "instrument"),
        "collections": _facet(records, "collection"),
        "formats": _facet([{"format": fmt} for item in records for fmt in item.get("file_formats", [])], "format"),
        "integration": result["integration"],
    }


def build_science_assets(
    settings: Any = None, *, source_id: str = "", scientific_record_id: str = "", dataset_id: str = "",
    format: str = "", asset_role: str = "", limit: int = 100, offset: int = 0,
) -> dict[str, Any]:
    config = _core_config(settings)
    generated_at = datetime.now(timezone.utc).isoformat()
    if not config.configured:
        return {"ok": True, "schema": ASSETS_SCHEMA, "version": "2.5.0", "generated_at": generated_at, "assets": [], "total": 0, "integration": _integration_state(settings)}
    try:
        payload = _core_json(config, "/api/v1/fabric/assets", {
            "source_id": source_id, "scientific_record_id": scientific_record_id, "dataset_id": dataset_id,
            "format": format, "asset_role": asset_role, "limit": min(max(limit, 1), MAX_ASSETS), "offset": max(offset, 0),
        })
        assets = [_public_asset(item) for item in _items(payload, "items", "assets")]
        assets = [item for item in assets if item["href"]]
        meta = payload.get("meta", {}) if isinstance(payload, Mapping) else {}
        pagination = meta.get("pagination", {}) if isinstance(meta, Mapping) else {}
        return {"ok": True, "schema": ASSETS_SCHEMA, "version": "2.5.0", "generated_at": generated_at, "assets": assets, "total": int(pagination.get("total") or len(assets)), "integration": _integration_state(settings)}
    except RuntimeError as exc:
        return {"ok": True, "schema": ASSETS_SCHEMA, "version": "2.5.0", "generated_at": generated_at, "assets": [], "total": 0, "integration": _integration_state(settings, str(exc))}


def build_science_layers(settings: Any = None, *, source_id: str = "", layer_type: str = "", limit: int = 100, offset: int = 0) -> dict[str, Any]:
    config = _core_config(settings)
    generated_at = datetime.now(timezone.utc).isoformat()
    if not config.configured:
        return {"ok": True, "schema": LAYERS_SCHEMA, "version": "2.5.0", "generated_at": generated_at, "layers": [], "total": 0, "integration": _integration_state(settings)}
    try:
        payload = _core_json(config, "/api/v1/fabric/map-layers", {"source_id": source_id, "layer_type": layer_type, "limit": min(max(limit, 1), MAX_LAYERS), "offset": max(offset, 0)})
        layers = [_public_layer(item) for item in _items(payload, "items", "layers")]
        meta = payload.get("meta", {}) if isinstance(payload, Mapping) else {}
        pagination = meta.get("pagination", {}) if isinstance(meta, Mapping) else {}
        return {"ok": True, "schema": LAYERS_SCHEMA, "version": "2.5.0", "generated_at": generated_at, "layers": layers, "total": int(pagination.get("total") or len(layers)), "integration": _integration_state(settings)}
    except RuntimeError as exc:
        return {"ok": True, "schema": LAYERS_SCHEMA, "version": "2.5.0", "generated_at": generated_at, "layers": [], "total": 0, "integration": _integration_state(settings, str(exc))}


def build_science_stac(
    settings: Any = None, *, collections: str = "", bbox: str = "", start: str = "", end: str = "",
    query: str = "", limit: int = 100, offset: int = 0,
) -> dict[str, Any]:
    config = _core_config(settings)
    generated_at = datetime.now(timezone.utc).isoformat()
    if bbox:
        bbox = _validate_bbox(bbox)
    if not config.configured:
        return {"ok": True, "schema": "sc-site-intelligence-stac/1.0", "version": "2.5.0", "generated_at": generated_at, "type": "FeatureCollection", "features": [], "numberMatched": 0, "numberReturned": 0, "integration": _integration_state(settings)}
    try:
        payload = _core_json(config, "/api/v1/stac/search", {"collections": collections, "bbox": bbox, "start": start, "end": end, "query": query, "limit": min(max(limit, 1), MAX_RECORDS), "offset": max(offset, 0)})
        features = []
        for feature in payload.get("features", []) if isinstance(payload, Mapping) else []:
            if not isinstance(feature, Mapping):
                continue
            properties = _safe_mapping(feature.get("properties"))
            assets = {}
            for key, asset in (feature.get("assets") or {}).items() if isinstance(feature.get("assets"), Mapping) else []:
                if not isinstance(asset, Mapping):
                    continue
                href = _public_url(asset.get("href"))
                if href:
                    assets[_safe_text(key, 80)] = {"href": href, "type": _safe_text(asset.get("type"), 160), "roles": _safe_list(asset.get("roles"), 12, 80), "title": _safe_text(asset.get("title"), 240)}
            features.append({
                "type": "Feature",
                "id": _safe_text(feature.get("id"), 180),
                "collection": _safe_text(feature.get("collection"), 180),
                "geometry": _geometry(feature.get("geometry")),
                "bbox": feature.get("bbox") if isinstance(feature.get("bbox"), list) else [],
                "properties": properties,
                "assets": assets,
            })
        return {"ok": True, "schema": "sc-site-intelligence-stac/1.0", "version": "2.5.0", "generated_at": generated_at, "type": "FeatureCollection", "features": features, "numberMatched": int(payload.get("numberMatched") or len(features)), "numberReturned": len(features), "integration": _integration_state(settings)}
    except RuntimeError as exc:
        return {"ok": True, "schema": "sc-site-intelligence-stac/1.0", "version": "2.5.0", "generated_at": generated_at, "type": "FeatureCollection", "features": [], "numberMatched": 0, "numberReturned": 0, "integration": _integration_state(settings, str(exc))}


def build_science_series(
    settings: Any = None, *, source_id: str = "", metric: str = "", domain: str = "", dataset_id: str = "",
    geography_code: str = "", limit: int = 100, offset: int = 0,
) -> dict[str, Any]:
    config = _core_config(settings)
    generated_at = datetime.now(timezone.utc).isoformat()
    if not config.configured:
        return {"ok": True, "schema": SERIES_SCHEMA, "version": "2.5.0", "generated_at": generated_at, "series": [], "total": 0, "integration": _integration_state(settings)}
    try:
        payload = _core_json(config, "/api/v1/fabric/timeseries", {"source_id": source_id, "metric": metric, "domain": domain, "dataset_id": dataset_id, "geography_code": geography_code, "limit": min(max(limit, 1), MAX_SERIES), "offset": max(offset, 0)})
        series = [_public_series(item) for item in _items(payload, "items", "series")]
        meta = payload.get("meta", {}) if isinstance(payload, Mapping) else {}
        pagination = meta.get("pagination", {}) if isinstance(meta, Mapping) else {}
        return {"ok": True, "schema": SERIES_SCHEMA, "version": "2.5.0", "generated_at": generated_at, "series": series, "total": int(pagination.get("total") or len(series)), "integration": _integration_state(settings)}
    except RuntimeError as exc:
        return {"ok": True, "schema": SERIES_SCHEMA, "version": "2.5.0", "generated_at": generated_at, "series": [], "total": 0, "integration": _integration_state(settings, str(exc))}


def build_science_series_points(settings: Any = None, *, series_id: str, start: str = "", end: str = "", limit: int = 300, offset: int = 0) -> dict[str, Any]:
    series_id = _safe_text(series_id, 180)
    if not series_id:
        raise ValueError("series_id is required.")
    config = _core_config(settings)
    generated_at = datetime.now(timezone.utc).isoformat()
    if not config.configured:
        return {"ok": True, "schema": SERIES_SCHEMA, "version": "2.5.0", "generated_at": generated_at, "series_id": series_id, "points": [], "total": 0, "integration": _integration_state(settings)}
    try:
        payload = _core_json(config, f"/api/v1/fabric/timeseries/{series_id}/points", {"start": start, "end": end, "limit": min(max(limit, 1), MAX_POINTS), "offset": max(offset, 0)})
        points = [_public_point(item) for item in _items(payload, "items", "points")]
        points.sort(key=lambda item: item["observed_at"])
        meta = payload.get("meta", {}) if isinstance(payload, Mapping) else {}
        pagination = meta.get("pagination", {}) if isinstance(meta, Mapping) else {}
        return {"ok": True, "schema": SERIES_SCHEMA, "version": "2.5.0", "generated_at": generated_at, "series_id": series_id, "points": points, "total": int(pagination.get("total") or len(points)), "integration": _integration_state(settings)}
    except RuntimeError as exc:
        return {"ok": True, "schema": SERIES_SCHEMA, "version": "2.5.0", "generated_at": generated_at, "series_id": series_id, "points": [], "total": 0, "integration": _integration_state(settings, str(exc))}


def build_science_overview(settings: Any = None) -> dict[str, Any]:
    generated_at = datetime.now(timezone.utc).isoformat()
    records = build_science_records(settings, limit=MAX_RECORDS)
    assets = build_science_assets(settings, limit=MAX_ASSETS)
    layers = build_science_layers(settings, limit=MAX_LAYERS)
    series = build_science_series(settings, limit=MAX_SERIES)
    record_items = records["records"]
    return {
        "ok": True,
        "schema": RELEASE_SCHEMA,
        "version": "2.5.0",
        "release_name": "Scientific and Earth Systems Observatory",
        "generated_at": generated_at,
        "integration": records["integration"],
        "counts": {
            "scientific_records": records["total"],
            "scientific_assets": assets["total"],
            "map_layers": layers["total"],
            "time_series": series["total"],
            "disciplines": len({item["discipline"] for item in record_items if item["discipline"]}),
            "missions": len({item["mission"] for item in record_items if item["mission"]}),
            "sources": len({item["source_id"] for item in record_items if item["source_id"]}),
        },
        "families": _facet(record_items, "family", "family_label"),
        "quality_policy": {
            "statement": "Source, observation time, dataset, mission, instrument, license, attribution, quality status, and file format remain visible. Missing records are not imputed.",
            "scientific_limits": [
                "Metadata discovery is not equivalent to scientific validation or peer review.",
                "Remote-sensing imagery and derived products require domain-specific interpretation and ground validation.",
                "Forecasts, observations, models, catalog records, and computed properties remain distinct record types.",
                "The observatory does not provide clinical diagnosis, treatment guidance, or automated scientific conclusions.",
            ],
        },
        "capabilities": {
            "scientific_records": True,
            "assets": True,
            "map_layers": True,
            "stac": True,
            "time_series": True,
            "paid_provider_required": False,
            "fabrication_fallback": False,
        },
    }


def build_science_brief(settings: Any = None, *, family: str = "", discipline: str = "", source_id: str = "", query: str = "", limit: int = 80) -> dict[str, Any]:
    records_payload = build_science_records(settings, discipline=discipline, source_id=source_id, query=query, limit=min(limit, 150))
    records = records_payload["records"]
    if family:
        records = [item for item in records if item["family"] == family]
    by_family = Counter(item["family_label"] for item in records)
    by_type = Counter(item["record_type_label"] for item in records)
    return {
        "ok": True,
        "schema": "sc-site-intelligence-science-brief/1.0",
        "version": "2.5.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "title": "Scientific and Earth Systems source brief",
        "scope": {"family": family, "discipline": discipline, "source_id": source_id, "query": query},
        "record_count": len(records),
        "summary": "This deterministic brief describes the visible source records and does not infer scientific conclusions from record counts or metadata alone.",
        "by_family": dict(by_family),
        "by_record_type": dict(by_type),
        "records": records[:30],
        "limitations": [
            "Coverage depends on free official sources configured and ingested through Platform Core.",
            "Record counts reflect discoverable metadata rather than scientific importance or evidentiary weight.",
            "Observation dates, publication dates, processing levels, and update frequencies can differ.",
        ],
        "integration": records_payload["integration"],
    }


def build_science_diagnostics(settings: Any = None) -> dict[str, Any]:
    config = _core_config(settings)
    payload: dict[str, Any] = {
        "ok": True,
        "schema": "sc-site-intelligence-science-diagnostics/1.0",
        "version": "2.5.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "integration": _integration_state(settings),
        "credential_exposed": False,
        "checks": [],
    }
    if not config.configured:
        payload["checks"].append({"id": "core", "status": "review", "detail": payload["integration"]["message"]})
        return payload
    for check_id, path in (
        ("science-records", "/api/v1/science/records"),
        ("fabric-capabilities", "/api/v1/fabric/capabilities"),
        ("fabric-assets", "/api/v1/fabric/assets"),
        ("fabric-layers", "/api/v1/fabric/map-layers"),
        ("stac", "/api/v1/stac"),
        ("timeseries", "/api/v1/fabric/timeseries"),
    ):
        try:
            _core_json(config, path, {"limit": 1} if path not in {"/api/v1/fabric/capabilities", "/api/v1/stac"} else None, cache_key=f"science-diagnostic:{check_id}")
            payload["checks"].append({"id": check_id, "status": "pass", "detail": "Public Core endpoint responded."})
        except RuntimeError as exc:
            payload["checks"].append({"id": check_id, "status": "review", "detail": str(exc)})
    if any(item["status"] != "pass" for item in payload["checks"]):
        payload["integration"] = _integration_state(settings, "One or more scientific data-fabric endpoints are unavailable.")
    return payload
