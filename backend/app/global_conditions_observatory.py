"""Global Conditions and Live Map Observatory for Site Intelligence v2.1.0.

This module is a public-safe, server-side read bridge to Sustainable Catalyst
Core v2.8.0. It never sends Core credentials to the browser and degrades to a
clear local-fallback state when Core is not configured or temporarily offline.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
import threading
import time
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen

RELEASE_SCHEMA = "sc-site-intelligence-global-conditions/1.0"
FEATURE_SCHEMA = "sc-site-intelligence-global-feature-collection/1.0"
MAX_FEATURES = 500
MAX_SIGNALS = 100
_SAFE_LAYER_TYPES = {
    "geojson", "vector", "raster", "wms", "wmts", "stac", "cog", "pmtiles"
}
_CACHE: dict[str, tuple[float, Any]] = {}
_CACHE_LOCK = threading.Lock()


@dataclass(frozen=True)
class CoreReadConfig:
    enabled: bool
    base_url: str
    api_key: str
    timeout_seconds: float
    cache_ttl_seconds: int

    @property
    def configured(self) -> bool:
        return bool(self.enabled and self.base_url)


def _as_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on", "enabled"}


def _setting(settings: Any, attribute: str, env_name: str, default: Any = "") -> Any:
    value = getattr(settings, attribute, None) if settings is not None else None
    if value not in (None, ""):
        return value
    return os.getenv(env_name, default)


def core_read_config(settings: Any = None) -> CoreReadConfig:
    enabled = _as_bool(
        _setting(settings, "platform_core_enabled", "SC_SI_PLATFORM_CORE_ENABLED", False)
    ) and _as_bool(os.getenv("SC_SI_GLOBAL_CONDITIONS_ENABLED", "true"), True)
    base_url = str(
        _setting(settings, "platform_core_url", "SC_SI_PLATFORM_CORE_URL", "")
    ).strip().rstrip("/")
    api_key = str(
        _setting(
            settings,
            "platform_core_public_api_key",
            "SC_SI_PLATFORM_CORE_PUBLIC_API_KEY",
            "",
        )
    ).strip()
    timeout = float(os.getenv("SC_SI_GLOBAL_CONDITIONS_TIMEOUT_SECONDS", "9"))
    ttl = int(os.getenv("SC_SI_GLOBAL_CONDITIONS_CACHE_TTL_SECONDS", "90"))
    return CoreReadConfig(
        enabled=enabled,
        base_url=base_url,
        api_key=api_key,
        timeout_seconds=max(2.0, min(timeout, 30.0)),
        cache_ttl_seconds=max(15, min(ttl, 900)),
    )


def _cache_get(key: str) -> Any | None:
    with _CACHE_LOCK:
        record = _CACHE.get(key)
        if not record:
            return None
        expires_at, value = record
        if expires_at <= time.monotonic():
            _CACHE.pop(key, None)
            return None
        return value


def _cache_set(key: str, value: Any, ttl: int) -> None:
    with _CACHE_LOCK:
        _CACHE[key] = (time.monotonic() + ttl, value)


def _public_headers(config: CoreReadConfig) -> dict[str, str]:
    headers = {
        "Accept": "application/json",
        "User-Agent": "Sustainable-Catalyst-Site-Intelligence/2.1.0",
    }
    if config.api_key:
        headers["X-API-Key"] = config.api_key
        headers["Authorization"] = f"Bearer {config.api_key}"
    return headers


def _core_json(
    config: CoreReadConfig,
    path: str,
    query: Mapping[str, Any] | None = None,
    *,
    cache_key: str | None = None,
) -> Any:
    if not config.configured:
        raise RuntimeError("Platform Core public reading is not configured.")
    query_items = {
        key: value
        for key, value in (query or {}).items()
        if value not in (None, "", [], ())
    }
    suffix = f"?{urlencode(query_items, doseq=True)}" if query_items else ""
    url = urljoin(config.base_url + "/", path.lstrip("/")) + suffix
    key = cache_key or url
    cached = _cache_get(key)
    if cached is not None:
        return cached
    request = Request(url, headers=_public_headers(config), method="GET")
    try:
        with urlopen(request, timeout=config.timeout_seconds) as response:  # noqa: S310
            if response.status < 200 or response.status >= 300:
                raise RuntimeError(f"Core returned HTTP {response.status}.")
            body = response.read(4_000_000)
    except HTTPError as exc:
        raise RuntimeError(f"Core returned HTTP {exc.code}.") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise RuntimeError("Platform Core could not be reached.") from exc
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("Core returned an invalid JSON response.") from exc
    _cache_set(key, payload, config.cache_ttl_seconds)
    return payload


def _items(payload: Any, *keys: str) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    for key in keys:
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    data = payload.get("data")
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        for key in keys:
            value = data.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    return []


def _safe_text(value: Any, limit: int = 500) -> str:
    text = str(value or "").strip()
    return text[:limit]


def _safe_url(value: Any) -> str:
    value = _safe_text(value, 1600)
    return value if value.startswith(("https://", "http://")) else ""


def _safe_properties(properties: Mapping[str, Any] | None) -> dict[str, Any]:
    allowed = {
        "id", "title", "name", "description", "domain", "category", "metric",
        "value", "unit", "observed_at", "published_at", "retrieved_at",
        "freshness_status", "quality_status", "source_id", "connector_id",
        "source_name", "attribution", "license", "record_type", "severity",
        "country_code", "place", "event_type", "layer_id", "canonical_url",
    }
    output: dict[str, Any] = {}
    for key, value in (properties or {}).items():
        if key not in allowed:
            continue
        if isinstance(value, (str, int, float, bool)) or value is None:
            output[key] = _safe_text(value, 1200) if isinstance(value, str) else value
    if "canonical_url" in output:
        output["canonical_url"] = _safe_url(output["canonical_url"])
    return output


def _valid_geometry(geometry: Any) -> dict[str, Any] | None:
    if not isinstance(geometry, dict):
        return None
    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates")
    if geometry_type not in {
        "Point", "MultiPoint", "LineString", "MultiLineString", "Polygon", "MultiPolygon"
    }:
        return None
    if not isinstance(coordinates, list):
        return None
    return {"type": geometry_type, "coordinates": coordinates}


def _validate_bbox(value: str) -> str:
    if not value:
        return ""
    parts = value.split(",")
    if len(parts) != 4:
        raise ValueError("bbox must contain west,south,east,north.")
    numbers = [float(part.strip()) for part in parts]
    west, south, east, north = numbers
    if not (-180 <= west <= 180 and -180 <= east <= 180):
        raise ValueError("bbox longitude is outside the valid range.")
    if not (-90 <= south <= 90 and -90 <= north <= 90):
        raise ValueError("bbox latitude is outside the valid range.")
    if west > east or south > north:
        raise ValueError("bbox minimums must not exceed maximums.")
    return ",".join(f"{number:.6f}" for number in numbers)


def _state_payload(config: CoreReadConfig, state: str, message: str) -> dict[str, Any]:
    return {
        "configured": config.configured,
        "enabled": config.enabled,
        "state": state,
        "message": message,
        "credential_exposed": False,
    }


def build_global_conditions_overview(settings: Any = None) -> dict[str, Any]:
    config = core_read_config(settings)
    generated_at = datetime.now(timezone.utc).isoformat()
    if not config.configured:
        return {
            "ok": True,
            "schema": RELEASE_SCHEMA,
            "version": "2.1.0",
            "release_name": "Global Conditions and Live Map Observatory",
            "generated_at": generated_at,
            "integration": _state_payload(
                config,
                "local-fallback",
                "Platform Core is optional and is not configured; existing Site Intelligence feeds remain available.",
            ),
            "capabilities": {
                "core_features": False,
                "core_layers": False,
                "core_signals": False,
                "local_events": True,
                "earth_observation": True,
                "paid_provider_required": False,
            },
        }
    try:
        capabilities = _core_json(
            config,
            "/api/v1/fabric/capabilities",
            cache_key="global-conditions:capabilities",
        )
        return {
            "ok": True,
            "schema": RELEASE_SCHEMA,
            "version": "2.1.0",
            "release_name": "Global Conditions and Live Map Observatory",
            "generated_at": generated_at,
            "integration": _state_payload(config, "connected", "Platform Core public data fabric is connected."),
            "capabilities": capabilities if isinstance(capabilities, dict) else {},
        }
    except RuntimeError as exc:
        return {
            "ok": True,
            "schema": RELEASE_SCHEMA,
            "version": "2.1.0",
            "release_name": "Global Conditions and Live Map Observatory",
            "generated_at": generated_at,
            "integration": _state_payload(config, "degraded", str(exc)),
            "capabilities": {
                "core_features": False,
                "core_layers": False,
                "core_signals": False,
                "local_events": True,
                "earth_observation": True,
                "paid_provider_required": False,
            },
        }


def build_global_conditions_layers(settings: Any = None, limit: int = 100) -> dict[str, Any]:
    config = core_read_config(settings)
    bounded_limit = max(1, min(int(limit), 200))
    if not config.configured:
        return {
            "ok": True,
            "schema": RELEASE_SCHEMA,
            "state": "local-fallback",
            "count": 0,
            "layers": [],
        }
    try:
        payload = _core_json(
            config,
            "/api/v1/fabric/map-layers",
            {"limit": bounded_limit},
            cache_key=f"global-conditions:layers:{bounded_limit}",
        )
        layers = []
        for item in _items(payload, "layers", "items", "records")[:bounded_limit]:
            layer_type = _safe_text(item.get("layer_type") or item.get("type") or "geojson", 40).lower()
            if layer_type not in _SAFE_LAYER_TYPES:
                layer_type = "geojson"
            layers.append({
                "id": _safe_text(item.get("id") or item.get("layer_id"), 160),
                "title": _safe_text(item.get("title") or item.get("name") or "Map layer", 240),
                "description": _safe_text(item.get("description"), 1200),
                "layer_type": layer_type,
                "source_id": _safe_text(item.get("source_id"), 160),
                "connector_id": _safe_text(item.get("connector_id"), 160),
                "attribution": _safe_text(item.get("attribution"), 800),
                "license": _safe_text(item.get("license"), 240),
                "freshness_status": _safe_text(item.get("freshness_status"), 80),
                "public_url": _safe_url(item.get("public_url") or item.get("url")),
            })
        return {
            "ok": True,
            "schema": RELEASE_SCHEMA,
            "state": "connected",
            "count": len(layers),
            "layers": layers,
        }
    except RuntimeError as exc:
        return {
            "ok": True,
            "schema": RELEASE_SCHEMA,
            "state": "degraded",
            "message": str(exc),
            "count": 0,
            "layers": [],
        }


def build_global_conditions_features(
    settings: Any = None,
    *,
    bbox: str = "",
    domain: str = "",
    source_id: str = "",
    connector_id: str = "",
    observed_after: str = "",
    limit: int = 300,
) -> dict[str, Any]:
    config = core_read_config(settings)
    bounded_limit = max(1, min(int(limit), MAX_FEATURES))
    normalized_bbox = _validate_bbox(bbox)
    if not config.configured:
        return {
            "type": "FeatureCollection",
            "schema": FEATURE_SCHEMA,
            "state": "local-fallback",
            "features": [],
            "count": 0,
        }
    query = {
        "bbox": normalized_bbox,
        "domain": _safe_text(domain, 80),
        "source_id": _safe_text(source_id, 160),
        "connector_id": _safe_text(connector_id, 160),
        "observed_after": _safe_text(observed_after, 40),
        "limit": bounded_limit,
    }
    try:
        payload = _core_json(config, "/api/v1/fabric/features.geojson", query)
        raw_features = payload.get("features", []) if isinstance(payload, dict) else []
        features = []
        for raw in raw_features[:bounded_limit]:
            if not isinstance(raw, dict):
                continue
            geometry = _valid_geometry(raw.get("geometry"))
            if geometry is None:
                continue
            features.append({
                "type": "Feature",
                "id": _safe_text(raw.get("id"), 180),
                "geometry": geometry,
                "properties": _safe_properties(raw.get("properties")),
            })
        return {
            "type": "FeatureCollection",
            "schema": FEATURE_SCHEMA,
            "state": "connected",
            "features": features,
            "count": len(features),
        }
    except RuntimeError as exc:
        return {
            "type": "FeatureCollection",
            "schema": FEATURE_SCHEMA,
            "state": "degraded",
            "message": str(exc),
            "features": [],
            "count": 0,
        }


def build_global_conditions_signals(settings: Any = None, limit: int = 50) -> dict[str, Any]:
    config = core_read_config(settings)
    bounded_limit = max(1, min(int(limit), MAX_SIGNALS))
    if not config.configured:
        return {
            "ok": True,
            "schema": RELEASE_SCHEMA,
            "state": "local-fallback",
            "count": 0,
            "signals": [],
        }
    try:
        payload = _core_json(
            config,
            "/api/v1/live/observations/latest",
            {"limit": bounded_limit},
        )
        signals = []
        for item in _items(payload, "observations", "items", "records")[:bounded_limit]:
            signals.append({
                "id": _safe_text(item.get("id") or item.get("observation_id"), 180),
                "domain": _safe_text(item.get("domain"), 80),
                "metric": _safe_text(item.get("metric"), 180),
                "value": item.get("value"),
                "unit": _safe_text(item.get("unit"), 80),
                "observed_at": _safe_text(item.get("observed_at"), 64),
                "freshness_status": _safe_text(item.get("freshness_status"), 80),
                "quality_status": _safe_text(item.get("quality_status"), 80),
                "source_id": _safe_text(item.get("source_id"), 160),
                "connector_id": _safe_text(item.get("connector_id"), 160),
                "attribution": _safe_text(item.get("attribution"), 800),
            })
        return {
            "ok": True,
            "schema": RELEASE_SCHEMA,
            "state": "connected",
            "count": len(signals),
            "signals": signals,
        }
    except RuntimeError as exc:
        return {
            "ok": True,
            "schema": RELEASE_SCHEMA,
            "state": "degraded",
            "message": str(exc),
            "count": 0,
            "signals": [],
        }


def build_global_conditions_diagnostics(settings: Any = None) -> dict[str, Any]:
    config = core_read_config(settings)
    return {
        "ok": True,
        "schema": RELEASE_SCHEMA,
        "version": "2.1.0",
        "integration": _state_payload(
            config,
            "configured" if config.configured else "local-fallback",
            "Core credentials remain server-side and are never returned by this endpoint.",
        ),
        "limits": {
            "maximum_features_per_request": MAX_FEATURES,
            "maximum_signals_per_request": MAX_SIGNALS,
            "timeout_seconds": config.timeout_seconds,
            "cache_ttl_seconds": config.cache_ttl_seconds,
        },
        "boundaries": [
            "The observatory is public evidence infrastructure, not an emergency-response system.",
            "Mapped proximity does not establish causation.",
            "Satellite observations are not direct field verification.",
            "Freshness, quality, source, and attribution labels must remain visible.",
            "No paid provider is required by this release.",
        ],
    }
