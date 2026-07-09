from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List, Optional, Tuple

from ..config import Settings
from ..models import ExternalConnector, ExternalConnectorRegistry, ExternalDataPoint, ExternalHealthItem, ExternalLayer


DEFAULT_POWER_PARAMETERS = ["T2M", "T2M_MAX", "T2M_MIN", "PRECTOTCORR", "WS10M", "ALLSKY_SFC_SW_DWN"]
CACHE_VERSION = "0.3.1"

SAMPLE_POWER_DATA: Dict[str, Any] = {
    "source": "sample",
    "parameters": {
        "T2M": {"20260101": 2.3, "20260102": 1.1, "20260103": 3.4, "20260104": 4.0, "20260105": 2.8},
        "T2M_MAX": {"20260101": 5.0, "20260102": 3.8, "20260103": 6.2, "20260104": 7.1, "20260105": 5.9},
        "T2M_MIN": {"20260101": -1.2, "20260102": -2.1, "20260103": 0.3, "20260104": 1.0, "20260105": -0.4},
        "PRECTOTCORR": {"20260101": 0.0, "20260102": 1.8, "20260103": 0.0, "20260104": 3.4, "20260105": 0.2},
        "WS10M": {"20260101": 4.4, "20260102": 5.2, "20260103": 3.8, "20260104": 6.1, "20260105": 4.9},
        "ALLSKY_SFC_SW_DWN": {"20260101": 1.9, "20260102": 2.4, "20260103": 2.7, "20260104": 2.2, "20260105": 2.5},
    },
}

SAMPLE_GIBS_LAYERS = [
    ExternalLayer(layer_id="MODIS_Terra_CorrectedReflectance_TrueColor", title="MODIS Terra Corrected Reflectance True Color", category="earth_observation", interpretation="General visual context for clouds, smoke, snow, land, and water patterns."),
    ExternalLayer(layer_id="VIIRS_NOAA20_CorrectedReflectance_TrueColor", title="VIIRS NOAA-20 Corrected Reflectance True Color", category="earth_observation", interpretation="High-frequency visual monitoring for land, water, cloud, smoke, and storm context."),
    ExternalLayer(layer_id="MODIS_Terra_Land_Surface_Temp_Day", title="MODIS Terra Land Surface Temperature Day", category="climate_heat", interpretation="Surface-temperature signal useful for heat exposure, land-cover, and urban resilience context."),
    ExternalLayer(layer_id="IMERG_Precipitation_Rate", title="IMERG Precipitation Rate", category="hydrology", interpretation="Precipitation intensity layer useful for storm, flood, drought, and water-cycle monitoring."),
    ExternalLayer(layer_id="OMI_Nitrogen_Dioxide_Tropospheric_Column", title="OMI Tropospheric Nitrogen Dioxide Column", category="air_quality", interpretation="Atmospheric pollution proxy for energy, transportation, industrial, and urban monitoring."),
]

SAMPLE_TRACE = {
    "source": "sample",
    "year": 2024,
    "country": "USA",
    "total_emissions_tonnes_co2e": 6230000000,
    "sectors": [
        {"sector": "power", "emissions_tonnes_co2e": 1600000000},
        {"sector": "transportation", "emissions_tonnes_co2e": 1750000000},
        {"sector": "buildings", "emissions_tonnes_co2e": 750000000},
        {"sector": "manufacturing", "emissions_tonnes_co2e": 980000000},
        {"sector": "oil-and-gas", "emissions_tonnes_co2e": 520000000},
    ],
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _dt_from_ts(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


@dataclass
class CacheEntry:
    key: str
    value: Dict[str, Any]
    created_at: float
    ttl_seconds: int
    source: str
    last_error: str = ""

    def fresh(self) -> bool:
        return (time.time() - self.created_at) <= self.ttl_seconds

    def metadata(self, status: str) -> Dict[str, Any]:
        age = max(0, time.time() - self.created_at)
        expires_at = self.created_at + self.ttl_seconds
        return {
            "status": status,
            "cache_key": self.key,
            "cached_at": _dt_from_ts(self.created_at),
            "expires_at": _dt_from_ts(expires_at),
            "age_seconds": round(age, 1),
            "ttl_seconds": self.ttl_seconds,
            "source": self.source,
            "last_error": self.last_error,
        }


class ExternalMemoryCache:
    """Simple process-local cache for public external source responses.

    Render free instances and local development do not need a database for the
    first stabilization layer. This cache prevents repeated page loads from
    hammering NASA/Climate TRACE and lets the dashboard reuse the last successful
    response when an upstream API is slow or temporarily unavailable.
    """

    def __init__(self):
        self._items: Dict[str, CacheEntry] = {}
        self.hits = 0
        self.misses = 0
        self.stale_hits = 0
        self.bypasses = 0
        self.fallbacks = 0

    def get(self, key: str) -> Optional[CacheEntry]:
        entry = self._items.get(key)
        if entry and entry.fresh():
            self.hits += 1
            return entry
        self.misses += 1
        return None

    def get_stale(self, key: str, max_age_seconds: int) -> Optional[CacheEntry]:
        entry = self._items.get(key)
        if not entry:
            return None
        if (time.time() - entry.created_at) <= max_age_seconds:
            self.stale_hits += 1
            return entry
        return None

    def set(self, key: str, value: Dict[str, Any], ttl_seconds: int, source: str) -> CacheEntry:
        entry = CacheEntry(key=key, value=value, created_at=time.time(), ttl_seconds=ttl_seconds, source=source)
        self._items[key] = entry
        return entry

    def clear(self) -> int:
        count = len(self._items)
        self._items.clear()
        return count

    def stats(self) -> Dict[str, Any]:
        now = time.time()
        entries = []
        for key, entry in sorted(self._items.items()):
            entries.append({
                "cache_key": key,
                "source": entry.source,
                "cached_at": _dt_from_ts(entry.created_at),
                "age_seconds": round(max(0, now - entry.created_at), 1),
                "ttl_seconds": entry.ttl_seconds,
                "fresh": entry.fresh(),
                "last_error": entry.last_error,
            })
        return {
            "ok": True,
            "version": CACHE_VERSION,
            "entries_count": len(self._items),
            "hits": self.hits,
            "misses": self.misses,
            "stale_hits": self.stale_hits,
            "bypasses": self.bypasses,
            "fallbacks": self.fallbacks,
            "entries": entries,
        }


EXTERNAL_CACHE = ExternalMemoryCache()


def load_external_registry(settings: Settings) -> ExternalConnectorRegistry:
    path = Path(settings.external_registry_path)
    if not path.is_absolute():
        candidates = [
            Path.cwd() / path,
            Path.cwd() / path.name,
            Path.cwd() / "backend" / "data" / path.name,
            Path.cwd() / "data" / path.name,
            Path(__file__).resolve().parents[2] / "data" / path.name,
        ]
        for candidate in candidates:
            if candidate.exists():
                path = candidate
                break
    payload = json.loads(path.read_text(encoding="utf-8"))
    return ExternalConnectorRegistry(**payload)


def cache_status() -> Dict[str, Any]:
    return EXTERNAL_CACHE.stats()


def clear_cache() -> Dict[str, Any]:
    cleared = EXTERNAL_CACHE.clear()
    return {"ok": True, "cleared_entries": cleared, "cache": EXTERNAL_CACHE.stats()}


class ExternalDataHub:
    """Public-data hub for climate and energy intelligence.

    v0.2.1 stabilizes the pilot by adding response caching, stale-success reuse,
    per-source freshness metadata, and explicit dashboard-readiness signals.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.registry = load_external_registry(settings)

    def connectors(self) -> List[ExternalConnector]:
        return self.registry.connectors

    def _cache_ttl(self, source_id: str) -> int:
        source_overrides = {
            "nasa_power": max(300, self.settings.external_cache_ttl_seconds),
            "nasa_gibs": max(1800, self.settings.external_cache_ttl_seconds * 4),
            "climate_trace": max(1800, self.settings.external_cache_ttl_seconds * 4),
        }
        return int(source_overrides.get(source_id, self.settings.external_cache_ttl_seconds))

    def _http_json(self, url: str, headers: Optional[Dict[str, str]] = None) -> Tuple[Dict[str, Any], float]:
        start = time.perf_counter()
        req = urllib.request.Request(url, headers=headers or {"User-Agent": "SustainableCatalystSiteIntelligence/0.3.1"})
        with urllib.request.urlopen(req, timeout=self.settings.external_request_timeout_seconds) as response:  # noqa: S310 - intentional public API request.
            data = json.loads(response.read().decode("utf-8"))
        elapsed = (time.perf_counter() - start) * 1000
        return data, round(elapsed, 1)

    def _cached_or_fetch(self, key: str, source_id: str, fetcher, force_refresh: bool = False) -> Dict[str, Any]:
        ttl = self._cache_ttl(source_id)
        if self.settings.external_cache_enabled and not force_refresh:
            entry = EXTERNAL_CACHE.get(key)
            if entry:
                payload = dict(entry.value)
                payload["cache"] = entry.metadata("hit")
                return payload
        elif not self.settings.external_cache_enabled:
            EXTERNAL_CACHE.bypasses += 1

        try:
            payload = fetcher()
            if self.settings.external_cache_enabled and payload.get("live"):
                entry = EXTERNAL_CACHE.set(key, payload, ttl, source_id)
                payload = dict(payload)
                payload["cache"] = entry.metadata("miss")
            else:
                payload = dict(payload)
                payload["cache"] = {"status": "bypass" if not self.settings.external_cache_enabled else "fallback", "cache_key": key, "ttl_seconds": ttl}
            return payload
        except Exception as exc:  # noqa: BLE001 - stabilized external layer should preserve dashboard availability.
            if self.settings.external_cache_enabled:
                stale = EXTERNAL_CACHE.get_stale(key, self.settings.external_stale_ttl_seconds)
                if stale:
                    stale.last_error = f"{exc.__class__.__name__}: {exc}"
                    payload = dict(stale.value)
                    payload["live"] = False
                    payload["source"] = payload.get("source", source_id)
                    payload["message"] = f"Using stale cached {source_id} data after upstream failure: {exc.__class__.__name__}: {exc}"
                    payload["cache"] = stale.metadata("stale")
                    return payload
            EXTERNAL_CACHE.fallbacks += 1
            raise

    def nasa_power_timeseries(
        self,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        start: str = "20260101",
        end: str = "20260105",
        parameters: Optional[List[str]] = None,
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        lat = self.settings.external_default_latitude if latitude is None else latitude
        lon = self.settings.external_default_longitude if longitude is None else longitude
        params = parameters or DEFAULT_POWER_PARAMETERS
        query = {
            "parameters": ",".join(params),
            "community": "RE",
            "longitude": str(lon),
            "latitude": str(lat),
            "start": start,
            "end": end,
            "format": "JSON",
        }
        url = self.settings.nasa_power_base_url + "?" + urllib.parse.urlencode(query)
        key = "nasa_power:" + urllib.parse.urlencode({"lat": lat, "lon": lon, "start": start, "end": end, "parameters": ",".join(params)})
        if not self.settings.external_live:
            return {**SAMPLE_POWER_DATA, "url": url, "live": False, "cache": {"status": "disabled"}, "message": "External live mode is disabled."}

        def fetcher() -> Dict[str, Any]:
            payload, latency = self._http_json(url)
            properties = payload.get("properties", {}) if isinstance(payload, dict) else {}
            return {
                "source": "NASA POWER",
                "live": True,
                "latency_ms": latency,
                "url": url,
                "parameters": properties.get("parameter", {}),
                "raw_header": payload.get("header", {}) if isinstance(payload, dict) else {},
            }

        try:
            return self._cached_or_fetch(key, "nasa_power", fetcher, force_refresh=force_refresh)
        except Exception as exc:  # noqa: BLE001 - fall back with explicit note.
            return {**SAMPLE_POWER_DATA, "url": url, "live": False, "cache": {"status": "fallback", "cache_key": key}, "message": f"NASA POWER fallback used: {exc.__class__.__name__}: {exc}"}

    def nasa_gibs_layers(self, limit: int = 20, force_refresh: bool = False) -> Dict[str, Any]:
        key = f"nasa_gibs:layers:{limit}:{self.settings.nasa_gibs_wmts_capabilities_url}"
        if not self.settings.external_live:
            return {"source": "sample", "live": False, "cache": {"status": "disabled"}, "layers": [layer.model_dump() for layer in SAMPLE_GIBS_LAYERS[:limit]], "message": "External live mode is disabled."}

        def fetcher() -> Dict[str, Any]:
            start = time.perf_counter()
            req = urllib.request.Request(self.settings.nasa_gibs_wmts_capabilities_url, headers={"User-Agent": "SustainableCatalystSiteIntelligence/0.3.1"})
            with urllib.request.urlopen(req, timeout=self.settings.external_request_timeout_seconds) as response:  # noqa: S310
                xml_text = response.read().decode("utf-8", errors="replace")
            elapsed = round((time.perf_counter() - start) * 1000, 1)
            root = ET.fromstring(xml_text)
            ns = {"wmts": "http://www.opengis.net/wmts/1.0", "ows": "http://www.opengis.net/ows/1.1"}
            layers: List[ExternalLayer] = []
            for layer in root.findall(".//wmts:Layer", ns):
                identifier = layer.findtext("ows:Identifier", default="", namespaces=ns)
                title = layer.findtext("ows:Title", default=identifier, namespaces=ns)
                if not identifier:
                    continue
                lowered = identifier.lower()
                category = "earth_observation"
                if "temp" in lowered or "thermal" in lowered:
                    category = "climate_heat"
                elif "precip" in lowered or "rain" in lowered:
                    category = "hydrology"
                elif "aerosol" in lowered or "dioxide" in lowered or "ozone" in lowered:
                    category = "air_quality"
                layers.append(ExternalLayer(layer_id=identifier, title=title or identifier, category=category, endpoint_hint=self.settings.nasa_gibs_wmts_capabilities_url, interpretation=_layer_interpretation(identifier, category)))
                if len(layers) >= limit:
                    break
            if not layers:
                layers = SAMPLE_GIBS_LAYERS[:limit]
            return {"source": "NASA GIBS", "live": True, "latency_ms": elapsed, "layers": [layer.model_dump() for layer in layers]}

        try:
            return self._cached_or_fetch(key, "nasa_gibs", fetcher, force_refresh=force_refresh)
        except Exception as exc:  # noqa: BLE001
            return {"source": "sample", "live": False, "cache": {"status": "fallback", "cache_key": key}, "layers": [layer.model_dump() for layer in SAMPLE_GIBS_LAYERS[:limit]], "message": f"NASA GIBS fallback used: {exc.__class__.__name__}: {exc}"}

    def climate_trace_emissions(self, year: int = 2024, country: Optional[str] = None, force_refresh: bool = False) -> Dict[str, Any]:
        country_code = country or self.settings.external_default_country
        # Climate TRACE API versions have changed over time. This connector keeps
        # the endpoint configurable and falls back to sample data if the public beta
        # route changes or is temporarily unavailable.
        url = f"{self.settings.climate_trace_base_url.rstrip('/')}/country/emissions?" + urllib.parse.urlencode({"year": year, "country": country_code})
        key = "climate_trace:" + urllib.parse.urlencode({"year": year, "country": country_code, "base": self.settings.climate_trace_base_url})
        if not self.settings.external_live:
            return {**SAMPLE_TRACE, "live": False, "url": url, "cache": {"status": "disabled"}, "message": "External live mode is disabled."}

        def fetcher() -> Dict[str, Any]:
            payload, latency = self._http_json(url)
            sectors = _extract_trace_sectors(payload)
            total = sum(float(item.get("emissions_tonnes_co2e", 0) or 0) for item in sectors)
            return {
                "source": "Climate TRACE",
                "live": True,
                "latency_ms": latency,
                "url": url,
                "year": year,
                "country": country_code,
                "total_emissions_tonnes_co2e": total,
                "sectors": sectors[:12],
            }

        try:
            return self._cached_or_fetch(key, "climate_trace", fetcher, force_refresh=force_refresh)
        except Exception as exc:  # noqa: BLE001
            return {**SAMPLE_TRACE, "live": False, "url": url, "cache": {"status": "fallback", "cache_key": key}, "message": f"Climate TRACE fallback used: {exc.__class__.__name__}: {exc}"}

    def health(self, force_refresh: bool = False) -> List[ExternalHealthItem]:
        items: List[ExternalHealthItem] = []
        power = self.nasa_power_timeseries(start="20260101", end="20260102", force_refresh=force_refresh)
        items.append(_health_item("nasa_power", "NASA POWER", power, "POWER connector returned data."))
        gibs = self.nasa_gibs_layers(limit=3, force_refresh=force_refresh)
        items.append(_health_item("nasa_gibs", "NASA GIBS", gibs, "GIBS connector returned layer metadata."))
        trace = self.climate_trace_emissions(force_refresh=force_refresh)
        items.append(_health_item("climate_trace", "Climate TRACE", trace, "Climate TRACE connector returned emissions data."))
        return items

    def climate_energy_dashboard(
        self,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        country: Optional[str] = None,
        start: str = "20260101",
        end: str = "20260105",
        year: int = 2024,
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        lat = self.settings.external_default_latitude if latitude is None else latitude
        lon = self.settings.external_default_longitude if longitude is None else longitude
        country_code = country or self.settings.external_default_country
        power = self.nasa_power_timeseries(lat, lon, start, end, force_refresh=force_refresh)
        layers = self.nasa_gibs_layers(limit=8, force_refresh=force_refresh)
        trace = self.climate_trace_emissions(year=year, country=country_code, force_refresh=force_refresh)
        indicators = _power_indicators(power)
        top_sectors = sorted(trace.get("sectors", []), key=lambda x: float(x.get("emissions_tonnes_co2e", 0) or 0), reverse=True)[:6]
        emissions_summary = {
            "source": trace.get("source", "sample"),
            "live": bool(trace.get("live")),
            "year": trace.get("year", year),
            "country": trace.get("country", country_code),
            "total_emissions_tonnes_co2e": trace.get("total_emissions_tonnes_co2e", 0),
            "top_sectors": top_sectors,
            "message": trace.get("message", ""),
            "cache": trace.get("cache", {}),
        }
        notes = []
        for blob in [power, layers, trace]:
            if blob.get("message"):
                notes.append(str(blob["message"]))
        live_sources = sum(1 for blob in [power, layers, trace] if blob.get("live"))
        cached_sources = sum(1 for blob in [power, layers, trace] if (blob.get("cache") or {}).get("status") in {"hit", "miss", "stale"})
        stale_sources = sum(1 for blob in [power, layers, trace] if (blob.get("cache") or {}).get("status") == "stale")
        fallback_sources = 3 - live_sources
        stability = _stability_summary(live_sources, cached_sources, stale_sources, fallback_sources)
        source = "external-live" if live_sources == 3 else "external-mixed" if live_sources else "sample-fallback"
        return {
            "ok": True,
            "generated_at": utc_now(),
            "source": source,
            "version": CACHE_VERSION,
            "location": {"latitude": lat, "longitude": lon, "country": country_code, "start": start, "end": end, "emissions_year": year},
            "connector_health": [item.model_dump() for item in self.health(force_refresh=False)],
            "cache_summary": _cache_summary([power, layers, trace]),
            "stability": stability,
            "indicators": [item.model_dump() for item in indicators],
            "earth_observation_layers": layers.get("layers", []),
            "emissions_summary": emissions_summary,
            "linked_article_maps": ["Climate Change", "Energy Systems", "Environmental Science", "Earth Science", "Urban Resilience"],
            "linked_workbench_tools": ["energy-systems-calculator", "climate-change-scenario-tool", "environmental-monitoring-qaqc-tool"],
            "recommendations": _dashboard_recommendations(indicators, emissions_summary, live_sources, stability),
            "notes": notes,
            "methodology": {
                "public_status": stability["public_status"],
                "summary": "External connector outputs are cached, source-labeled, and treated as interpretive signals rather than professional advice.",
                "review_note": "Use public mode only after source health is stable and fallback notes are absent or clearly disclosed.",
            },
        }


def _health_item(connector_id: str, name: str, payload: Dict[str, Any], success_message: str) -> ExternalHealthItem:
    cache = payload.get("cache") or {}
    cache_status_value = cache.get("status") or "none"
    status = "healthy" if payload.get("live") and cache_status_value != "stale" else "stale" if cache_status_value == "stale" else "fallback"
    return ExternalHealthItem(
        connector_id=connector_id,
        name=name,
        status=status,
        live=bool(payload.get("live")),
        message=payload.get("message", success_message),
        last_checked=utc_now(),
        latency_ms=payload.get("latency_ms"),
        cache_status=cache_status_value,
        cached=cache_status_value in {"hit", "miss", "stale"},
        age_seconds=cache.get("age_seconds"),
        cached_at=cache.get("cached_at"),
        expires_at=cache.get("expires_at"),
    )


def _avg(values: Dict[str, Any]) -> Optional[float]:
    clean = []
    for val in (values or {}).values():
        try:
            clean.append(float(val))
        except (TypeError, ValueError):
            pass
    return round(mean(clean), 3) if clean else None


def _power_indicators(power: Dict[str, Any]) -> List[ExternalDataPoint]:
    params = power.get("parameters", {}) or {}
    mapping = [
        ("Mean 2m temperature", "T2M", "°C", "Temperature baseline for climate, energy demand, heat exposure, and resilience interpretation."),
        ("Maximum 2m temperature", "T2M_MAX", "°C", "Daily maximum heat signal; useful for heat-risk and cooling-demand context."),
        ("Minimum 2m temperature", "T2M_MIN", "°C", "Daily minimum temperature signal; useful for cold stress and diurnal range context."),
        ("Corrected precipitation", "PRECTOTCORR", "mm/day", "Precipitation signal for hydrology, flood/drought context, and infrastructure stress."),
        ("10m wind speed", "WS10M", "m/s", "Wind resource and exposure signal for energy systems and storm context."),
        ("All-sky surface solar irradiance", "ALLSKY_SFC_SW_DWN", "kWh/m²/day", "Solar resource signal for distributed energy, building loads, and siting context."),
    ]
    points: List[ExternalDataPoint] = []
    for label, key, unit, interpretation in mapping:
        points.append(ExternalDataPoint(label=label, value=_avg(params.get(key, {})), unit=unit, interpretation=interpretation, source=power.get("source", "NASA POWER")))
    return points


def _layer_interpretation(layer_id: str, category: str) -> str:
    if category == "climate_heat":
        return "Heat and surface-temperature context for climate, land-use, and urban resilience interpretation."
    if category == "hydrology":
        return "Water-cycle and precipitation context for storms, flooding, drought, and environmental monitoring."
    if category == "air_quality":
        return "Atmospheric composition context for emissions, air quality, and energy-system monitoring."
    if "TrueColor" in layer_id or "Reflectance" in layer_id:
        return "Visible imagery context for clouds, smoke, snow, land, water, and surface conditions."
    return "Earth observation layer available for map-based climate and environmental intelligence."


def _extract_trace_sectors(payload: Any) -> List[Dict[str, Any]]:
    # Accommodate multiple public-beta response shapes without binding the product
    # to a single unstable schema.
    if isinstance(payload, dict):
        candidates = payload.get("sectors") or payload.get("data") or payload.get("results") or payload.get("emissions") or []
    elif isinstance(payload, list):
        candidates = payload
    else:
        candidates = []
    sectors: Dict[str, float] = {}
    if isinstance(candidates, dict):
        candidates = list(candidates.values())
    for item in candidates if isinstance(candidates, list) else []:
        if not isinstance(item, dict):
            continue
        sector = item.get("sector") or item.get("sectorName") or item.get("sector_name") or item.get("name") or "unknown"
        val = item.get("emissions_tonnes_co2e") or item.get("emissions") or item.get("co2e") or item.get("total") or 0
        try:
            sectors[str(sector)] = sectors.get(str(sector), 0.0) + float(val)
        except (TypeError, ValueError):
            continue
    return [{"sector": sector, "emissions_tonnes_co2e": round(value, 3)} for sector, value in sectors.items()]


def _cache_summary(blobs: List[Dict[str, Any]]) -> Dict[str, Any]:
    statuses: Dict[str, int] = {}
    for blob in blobs:
        status = (blob.get("cache") or {}).get("status", "none")
        statuses[status] = statuses.get(status, 0) + 1
    return {
        "statuses": statuses,
        "cache_enabled": any((blob.get("cache") or {}).get("status") in {"hit", "miss", "stale"} for blob in blobs),
        "oldest_age_seconds": max([(blob.get("cache") or {}).get("age_seconds", 0) or 0 for blob in blobs] or [0]),
        "items": [blob.get("cache") or {} for blob in blobs],
    }


def _stability_summary(live_sources: int, cached_sources: int, stale_sources: int, fallback_sources: int) -> Dict[str, Any]:
    if live_sources == 3 and stale_sources == 0:
        status = "stable"
        score = 100
        public_status = "public_candidate"
    elif live_sources >= 2:
        status = "mixed"
        score = 75 - (stale_sources * 10)
        public_status = "internal_review"
    elif cached_sources and stale_sources:
        status = "stale_cached"
        score = 55
        public_status = "internal_review"
    else:
        status = "fallback"
        score = 35
        public_status = "internal_only"
    return {
        "status": status,
        "score": max(0, score),
        "live_sources": live_sources,
        "cached_sources": cached_sources,
        "stale_sources": stale_sources,
        "fallback_sources": fallback_sources,
        "public_ready": public_status == "public_candidate",
        "public_status": public_status,
    }


def _dashboard_recommendations(indicators: List[ExternalDataPoint], emissions: Dict[str, Any], live_sources: int, stability: Dict[str, Any]) -> List[str]:
    recs = []
    solar = next((item.value for item in indicators if item.label.startswith("All-sky")), None)
    temp_max = next((item.value for item in indicators if item.label.startswith("Maximum")), None)
    precip = next((item.value for item in indicators if item.label.startswith("Corrected")), None)
    if solar is not None and solar >= 4:
        recs.append("Prioritize Energy Systems content and Workbench prompts around distributed solar potential for this location.")
    elif solar is not None:
        recs.append("Use NASA POWER solar values as context, but frame solar potential cautiously for this date range/location.")
    if temp_max is not None and temp_max >= 30:
        recs.append("Add Urban Resilience and heat-risk pathways where high-temperature signals appear in the data.")
    if precip is not None and precip > 5:
        recs.append("Connect precipitation signals to Environmental Monitoring, infrastructure stress, and flood/drought article pathways.")
    sectors = emissions.get("top_sectors", [])
    if sectors:
        recs.append("Use Climate TRACE sector rankings to connect emissions discussion with Energy Systems, economics, and policy tools.")
    if live_sources < 3:
        recs.append("One or more external connectors used fallback or stale cached data; check /external/health before publishing public dashboard interpretations.")
    if not stability.get("public_ready"):
        recs.append("Keep this dashboard internal until source health is stable and cache/fallback notes are suitable for public display.")
    recs.append("Cross-link this dashboard from Climate Change, Energy Systems, Environmental Science, and NASA Earth Observation pages once reviewed.")
    return recs
