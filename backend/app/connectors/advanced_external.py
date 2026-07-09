
from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from ..config import Settings
from ..models import ExternalHealthItem
from .external_data import ExternalDataHub, EXTERNAL_CACHE, utc_now

ADVANCED_CONNECTOR_VERSION = "0.6.0"

SAMPLE_NOAA = {
    "source": "sample",
    "live": False,
    "summary": "NOAA/NWS fallback weather and climate-hazard context for Chicago-area defaults.",
    "indicators": [
        {"label": "Forecast temperature context", "value": 24.0, "unit": "°C", "interpretation": "Temperature context for heat, energy demand, and urban resilience review."},
        {"label": "Short-term precipitation signal", "value": 2.5, "unit": "mm", "interpretation": "Precipitation context for stormwater, monitoring, and infrastructure stress."},
        {"label": "Weather alert count", "value": 0, "unit": "alerts", "interpretation": "Hazard-alert signal for environmental monitoring and public resilience review."},
    ],
}

SAMPLE_EIA = {
    "source": "sample",
    "live": False,
    "summary": "EIA fallback electricity and energy-system context.",
    "indicators": [
        {"label": "Electricity system focus", "value": None, "unit": "", "interpretation": "Use EIA data for production, consumption, price, and fuel-mix intelligence when an API key is configured."},
        {"label": "Energy transition relevance", "value": 1, "unit": "signal", "interpretation": "Energy data links climate, infrastructure, economics, and emissions pathways."},
    ],
}

SAMPLE_EPA = {
    "source": "sample",
    "live": False,
    "summary": "EPA AQS fallback air-quality context.",
    "indicators": [
        {"label": "PM2.5 monitoring relevance", "value": 1, "unit": "signal", "interpretation": "Fine particulate matter is a core air-quality and public-health monitoring signal."},
        {"label": "Ozone monitoring relevance", "value": 1, "unit": "signal", "interpretation": "Ground-level ozone connects heat, emissions, air chemistry, and public health."},
    ],
}

SAMPLE_CENSUS = {
    "source": "sample",
    "live": False,
    "summary": "Census fallback place-context indicators for urban resilience.",
    "indicators": [
        {"label": "Population context", "value": 2746388, "unit": "people", "interpretation": "Population scale shapes exposure, infrastructure demand, and public-service resilience."},
        {"label": "Place context", "value": None, "unit": "", "interpretation": "Use Census data to contextualize climate, air quality, energy, and infrastructure signals."},
    ],
}

SAMPLE_USGS = {
    "source": "sample",
    "live": False,
    "summary": "USGS land-cover fallback context for land use and biodiversity dashboards.",
    "land_cover_context": [
        {"class": "developed", "share_estimate": 0.62, "interpretation": "Developed land cover can amplify heat, stormwater runoff, habitat fragmentation, and infrastructure exposure."},
        {"class": "open_space / vegetation", "share_estimate": 0.22, "interpretation": "Open/vegetated cover supports cooling, infiltration, habitat, and urban resilience."},
        {"class": "water / wetlands", "share_estimate": 0.05, "interpretation": "Water and wetland context matters for flooding, hydrology, biodiversity, and climate adaptation."},
    ],
}

SAMPLE_GBIF = {
    "source": "sample",
    "live": False,
    "summary": "GBIF fallback biodiversity context.",
    "indicators": [
        {"label": "Species occurrence relevance", "value": 1, "unit": "signal", "interpretation": "Occurrence data can support biodiversity, habitat, conservation, and land-use dashboards."},
        {"label": "Biodiversity observation caution", "value": 1, "unit": "note", "interpretation": "Occurrence data are not absence data; interpret records as observation signals, not complete ecological inventories."},
    ],
}


def _http_json(url: str, timeout: int, headers: Optional[Dict[str, str]] = None) -> Tuple[Dict[str, Any], float]:
    start = time.perf_counter()
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "SustainableCatalystSiteIntelligence/0.6.0"})
    with urllib.request.urlopen(req, timeout=timeout) as response:  # noqa: S310 - intentional public API request.
        data = json.loads(response.read().decode("utf-8"))
    elapsed = (time.perf_counter() - start) * 1000
    return data, round(elapsed, 1)


def _cache_meta(status: str, key: str, source_id: str) -> Dict[str, Any]:
    return {"status": status, "cache_key": key, "source": source_id, "version": ADVANCED_CONNECTOR_VERSION}


class AdvancedExternalDataHub:
    """Advanced external-data connector layer for v0.6.0.

    The layer prioritizes dashboard reliability: each connector returns a stable,
    source-labeled fallback if an API key is not configured or an upstream API is
    unavailable. This keeps public and private dashboards usable while still
    allowing live connector checks when credentials are added.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.core = ExternalDataHub(settings)

    def _ttl(self, source_id: str) -> int:
        if source_id in {"noaa_weather_climate"}:
            return max(900, int(self.settings.external_cache_ttl_seconds))
        if source_id in {"eia_energy", "epa_aqs_air_quality", "gbif_biodiversity"}:
            return max(3600, int(self.settings.external_cache_ttl_seconds) * 2)
        return max(86400, int(self.settings.external_cache_ttl_seconds) * 4)

    def _cached(self, key: str, source_id: str, fetcher, fallback: Dict[str, Any], force_refresh: bool = False) -> Dict[str, Any]:
        if self.settings.external_cache_enabled and not force_refresh:
            entry = EXTERNAL_CACHE.get(key)
            if entry:
                payload = dict(entry.value)
                payload["cache"] = entry.metadata("hit")
                return payload
        if not self.settings.external_live:
            payload = dict(fallback)
            payload["cache"] = _cache_meta("disabled", key, source_id)
            payload["message"] = "External live mode is disabled; using stable fallback data."
            return payload
        try:
            payload = fetcher()
            payload = dict(payload)
            if payload.get("live") and self.settings.external_cache_enabled:
                entry = EXTERNAL_CACHE.set(key, payload, self._ttl(source_id), source_id)
                payload["cache"] = entry.metadata("miss")
            else:
                payload["cache"] = _cache_meta("fallback", key, source_id)
            return payload
        except Exception as exc:  # noqa: BLE001
            stale = EXTERNAL_CACHE.get_stale(key, self.settings.external_stale_ttl_seconds) if self.settings.external_cache_enabled else None
            if stale:
                stale.last_error = f"{exc.__class__.__name__}: {exc}"
                payload = dict(stale.value)
                payload["live"] = False
                payload["message"] = f"Using stale cached {source_id} data after upstream failure: {exc.__class__.__name__}: {exc}"
                payload["cache"] = stale.metadata("stale")
                return payload
            payload = dict(fallback)
            payload["cache"] = _cache_meta("fallback", key, source_id)
            payload["message"] = f"{source_id} fallback used: {exc.__class__.__name__}: {exc}"
            return payload

    def noaa_weather_climate(self, latitude: Optional[float] = None, longitude: Optional[float] = None, force_refresh: bool = False) -> Dict[str, Any]:
        lat = self.settings.external_default_latitude if latitude is None else latitude
        lon = self.settings.external_default_longitude if longitude is None else longitude
        key = f"noaa_weather_climate:{lat}:{lon}"
        base = self.settings.noaa_weather_base_url.rstrip("/")

        def fetcher() -> Dict[str, Any]:
            points_url = f"{base}/points/{lat},{lon}"
            points, latency_1 = _http_json(points_url, self.settings.external_request_timeout_seconds)
            forecast_url = (points.get("properties") or {}).get("forecast")
            alerts_url = f"{base}/alerts/active?" + urllib.parse.urlencode({"point": f"{lat},{lon}"})
            periods = []
            latency_2 = 0.0
            if forecast_url:
                forecast, latency_2 = _http_json(forecast_url, self.settings.external_request_timeout_seconds)
                periods = (forecast.get("properties") or {}).get("periods", [])[:4]
            alerts, latency_3 = _http_json(alerts_url, self.settings.external_request_timeout_seconds)
            alert_count = len(alerts.get("features", []) or [])
            temps = []
            for p in periods:
                try:
                    val = float(p.get("temperature"))
                    if (p.get("temperatureUnit") or "F") == "F":
                        val = (val - 32) * 5 / 9
                    temps.append(val)
                except (TypeError, ValueError):
                    pass
            avg_temp = round(sum(temps) / len(temps), 2) if temps else None
            return {
                "source": "NOAA / National Weather Service",
                "live": True,
                "latency_ms": round(latency_1 + latency_2 + latency_3, 1),
                "location": {"latitude": lat, "longitude": lon},
                "summary": "NOAA/NWS live forecast and alert context.",
                "forecast_periods": periods,
                "indicators": [
                    {"label": "Forecast temperature context", "value": avg_temp, "unit": "°C", "interpretation": "Short-term temperature context for climate, energy demand, heat exposure, and resilience."},
                    {"label": "Active weather alerts", "value": alert_count, "unit": "alerts", "interpretation": "Hazard-alert signal for environmental monitoring and public resilience review."},
                ],
            }
        return self._cached(key, "noaa_weather_climate", fetcher, {**SAMPLE_NOAA, "location": {"latitude": lat, "longitude": lon}}, force_refresh)

    def eia_energy(self, state: str = "IL", force_refresh: bool = False) -> Dict[str, Any]:
        state = (state or "IL").upper()
        key = f"eia_energy:{state}"
        api_key = self.settings.eia_api_key.strip()
        if not api_key:
            payload = {**SAMPLE_EIA, "state": state, "message": "Set SC_SI_EIA_API_KEY to enable live EIA calls."}
            payload["cache"] = _cache_meta("missing_key", key, "eia_energy")
            return payload
        base = self.settings.eia_base_url.rstrip("/")

        def fetcher() -> Dict[str, Any]:
            url = base + "/electricity/retail-sales/data/?" + urllib.parse.urlencode({
                "api_key": api_key,
                "frequency": "monthly",
                "data[0]": "price",
                "facets[stateid][]": state,
                "sort[0][column]": "period",
                "sort[0][direction]": "desc",
                "length": "12",
            })
            data, latency = _http_json(url, self.settings.external_request_timeout_seconds)
            rows = (data.get("response") or {}).get("data", []) if isinstance(data, dict) else []
            prices = []
            for r in rows:
                try:
                    prices.append(float(r.get("price")))
                except (TypeError, ValueError):
                    pass
            avg_price = round(sum(prices) / len(prices), 3) if prices else None
            return {
                "source": "EIA Open Data",
                "live": True,
                "latency_ms": latency,
                "state": state,
                "summary": "EIA live electricity price context.",
                "latest_rows": rows[:6],
                "indicators": [
                    {"label": "Average recent retail electricity price", "value": avg_price, "unit": "cents/kWh", "interpretation": "Electricity price context for energy systems, economics, and resilience analysis."},
                    {"label": "Rows returned", "value": len(rows), "unit": "records", "interpretation": "Live EIA response depth for this state/query."},
                ],
            }
        return self._cached(key, "eia_energy", fetcher, {**SAMPLE_EIA, "state": state}, force_refresh)

    def epa_air_quality(self, state: str = "17", county: str = "031", force_refresh: bool = False) -> Dict[str, Any]:
        key = f"epa_aqs_air_quality:{state}:{county}"
        email = self.settings.epa_aqs_email.strip()
        api_key = self.settings.epa_aqs_key.strip()
        if not email or not api_key:
            payload = {**SAMPLE_EPA, "state": state, "county": county, "message": "Set SC_SI_EPA_AQS_EMAIL and SC_SI_EPA_AQS_KEY to enable live EPA AQS calls."}
            payload["cache"] = _cache_meta("missing_key", key, "epa_aqs_air_quality")
            return payload
        base = self.settings.epa_aqs_base_url.rstrip("/")

        def fetcher() -> Dict[str, Any]:
            url = base + "/monitors/byCounty?" + urllib.parse.urlencode({
                "email": email,
                "key": api_key,
                "param": "88101",
                "bdate": "20240101",
                "edate": "20241231",
                "state": state,
                "county": county,
            })
            data, latency = _http_json(url, self.settings.external_request_timeout_seconds)
            rows = data.get("Data", []) if isinstance(data, dict) else []
            return {
                "source": "EPA AQS",
                "live": True,
                "latency_ms": latency,
                "state": state,
                "county": county,
                "summary": "EPA AQS live monitor metadata context.",
                "monitor_count": len(rows),
                "indicators": [
                    {"label": "PM2.5 monitor count", "value": len(rows), "unit": "monitors", "interpretation": "Monitor coverage is a quality signal for environmental monitoring and QA/QC interpretation."},
                ],
            }
        return self._cached(key, "epa_aqs_air_quality", fetcher, {**SAMPLE_EPA, "state": state, "county": county}, force_refresh)

    def census_context(self, state: str = "17", county: str = "031", force_refresh: bool = False) -> Dict[str, Any]:
        key = f"census_context:{state}:{county}"
        base = self.settings.census_base_url.rstrip("/")

        def fetcher() -> Dict[str, Any]:
            url = base + "/data/2023/acs/acs5?" + urllib.parse.urlencode({
                "get": "NAME,B01003_001E",
                "for": f"county:{county}",
                "in": f"state:{state}",
            })
            data, latency = _http_json(url, self.settings.external_request_timeout_seconds)
            row = data[1] if isinstance(data, list) and len(data) > 1 else []
            name = row[0] if len(row) > 0 else "Selected county"
            population = None
            if len(row) > 1:
                try: population = float(row[1])
                except (TypeError, ValueError): population = None
            return {
                "source": "U.S. Census ACS",
                "live": True,
                "latency_ms": latency,
                "state": state,
                "county": county,
                "summary": "Census live population context.",
                "place_name": name,
                "indicators": [
                    {"label": "Population context", "value": population, "unit": "people", "interpretation": "Population scale shapes exposure, infrastructure demand, and public-service resilience."},
                ],
            }
        return self._cached(key, "census_context", fetcher, {**SAMPLE_CENSUS, "state": state, "county": county}, force_refresh)

    def usgs_land_cover(self, latitude: Optional[float] = None, longitude: Optional[float] = None, force_refresh: bool = False) -> Dict[str, Any]:
        lat = self.settings.external_default_latitude if latitude is None else latitude
        lon = self.settings.external_default_longitude if longitude is None else longitude
        # v0.6.0 treats USGS/NLCD as a registry-context source first; many NLCD
        # services are geospatial/raster-oriented and should be connected through
        # a dedicated map tile/STAC layer later.
        key = f"usgs_land_cover:{lat}:{lon}"
        payload = {**SAMPLE_USGS, "location": {"latitude": lat, "longitude": lon}, "cache": _cache_meta("registry_context", key, "usgs_land_cover")}
        return payload

    def gbif_biodiversity(self, country: str = "US", limit: int = 20, force_refresh: bool = False) -> Dict[str, Any]:
        country = (country or "US").upper()
        key = f"gbif_biodiversity:{country}:{limit}"
        base = self.settings.gbif_base_url.rstrip("/")

        def fetcher() -> Dict[str, Any]:
            url = base + "/v1/occurrence/search?" + urllib.parse.urlencode({"country": country, "limit": str(limit), "hasCoordinate": "true"})
            data, latency = _http_json(url, self.settings.external_request_timeout_seconds)
            count = data.get("count") if isinstance(data, dict) else None
            results = data.get("results", [])[:limit] if isinstance(data, dict) else []
            top = []
            for r in results[:8]:
                top.append({"scientificName": r.get("scientificName"), "basisOfRecord": r.get("basisOfRecord"), "countryCode": r.get("countryCode")})
            return {
                "source": "GBIF",
                "live": True,
                "latency_ms": latency,
                "country": country,
                "summary": "GBIF live species occurrence context.",
                "occurrence_count": count,
                "sample_occurrences": top,
                "indicators": [
                    {"label": "GBIF occurrence count", "value": count, "unit": "records", "interpretation": "Occurrence-count signal for biodiversity observation density, not complete species presence/absence."},
                    {"label": "Sample records returned", "value": len(results), "unit": "records", "interpretation": "Returned records provide observation examples for biodiversity and land-use interpretation."},
                ],
            }
        return self._cached(key, "gbif_biodiversity", fetcher, {**SAMPLE_GBIF, "country": country}, force_refresh)

    def health(self, force_refresh: bool = False) -> List[ExternalHealthItem]:
        payloads = [
            ("noaa_weather_climate", "NOAA / NWS", self.noaa_weather_climate(force_refresh=force_refresh)),
            ("eia_energy", "EIA Energy", self.eia_energy(force_refresh=force_refresh)),
            ("epa_aqs_air_quality", "EPA AQS", self.epa_air_quality(force_refresh=force_refresh)),
            ("census_context", "U.S. Census", self.census_context(force_refresh=force_refresh)),
            ("usgs_land_cover", "USGS Land Cover", self.usgs_land_cover(force_refresh=force_refresh)),
            ("gbif_biodiversity", "GBIF Biodiversity", self.gbif_biodiversity(force_refresh=force_refresh)),
        ]
        out: List[ExternalHealthItem] = []
        for connector_id, name, payload in payloads:
            cache = payload.get("cache") or {}
            cache_status = cache.get("status") or "none"
            if payload.get("live"):
                status = "healthy"
            elif cache_status == "missing_key":
                status = "needs_key"
            elif cache_status == "registry_context":
                status = "registry_context"
            else:
                status = "fallback"
            out.append(ExternalHealthItem(
                connector_id=connector_id,
                name=name,
                status=status,
                live=bool(payload.get("live")),
                message=payload.get("message") or payload.get("summary") or "Connector returned data.",
                last_checked=utc_now(),
                latency_ms=payload.get("latency_ms"),
                cache_status=cache_status,
                cached=cache_status in {"hit", "miss", "stale"},
                age_seconds=cache.get("age_seconds"),
                cached_at=cache.get("cached_at"),
                expires_at=cache.get("expires_at"),
            ))
        return out

    def environmental_monitoring_dashboard(self, latitude: Optional[float] = None, longitude: Optional[float] = None, state: str = "17", county: str = "031", force_refresh: bool = False) -> Dict[str, Any]:
        noaa = self.noaa_weather_climate(latitude, longitude, force_refresh=force_refresh)
        epa = self.epa_air_quality(state, county, force_refresh=force_refresh)
        gibs = self.core.nasa_gibs_layers(limit=6, force_refresh=False)
        return _dashboard(
            "environmental_monitoring",
            "Environmental Monitoring Intelligence",
            [noaa, epa, gibs],
            ["Environmental Monitoring", "Earth Science", "Climate Change", "Public Health"],
            ["environmental-monitoring-qaqc-tool", "environmental-science-calculator"],
            "Weather, alert, air-quality, and Earth observation signals for monitoring strategy and QA/QC review.",
        )

    def urban_resilience_dashboard(self, latitude: Optional[float] = None, longitude: Optional[float] = None, country: str = "USA", state: str = "17", county: str = "031", force_refresh: bool = False) -> Dict[str, Any]:
        noaa = self.noaa_weather_climate(latitude, longitude, force_refresh=force_refresh)
        epa = self.epa_air_quality(state, county, force_refresh=force_refresh)
        census = self.census_context(state, county, force_refresh=force_refresh)
        trace = self.core.climate_trace_emissions(country=country, force_refresh=False)
        return _dashboard(
            "urban_resilience",
            "Urban Resilience Intelligence",
            [noaa, epa, census, trace],
            ["Urban Resilience", "Climate Change", "Environmental Monitoring", "Infrastructure"],
            ["risk-resilience-scorecard", "climate-change-scenario-tool"],
            "Hazard, air-quality, population, and emissions context for urban resilience planning and public systems analysis.",
        )

    def biodiversity_land_use_dashboard(self, latitude: Optional[float] = None, longitude: Optional[float] = None, country: str = "US", force_refresh: bool = False) -> Dict[str, Any]:
        usgs = self.usgs_land_cover(latitude, longitude, force_refresh=force_refresh)
        gbif = self.gbif_biodiversity(country=country, force_refresh=force_refresh)
        gibs = self.core.nasa_gibs_layers(limit=6, force_refresh=False)
        return _dashboard(
            "biodiversity_land_use",
            "Biodiversity and Land Use Intelligence",
            [usgs, gbif, gibs],
            ["Biodiversity", "Land Use", "Environmental Science", "Earth Science"],
            ["environmental-science-calculator", "environmental-monitoring-qaqc-tool"],
            "Land-cover, species-occurrence, and Earth observation context for biodiversity and ecological pressure review.",
        )

    def energy_systems_dashboard(self, latitude: Optional[float] = None, longitude: Optional[float] = None, country: str = "USA", state: str = "IL", start: str = "20260101", end: str = "20260105", force_refresh: bool = False) -> Dict[str, Any]:
        eia = self.eia_energy(state=state, force_refresh=force_refresh)
        power = self.core.nasa_power_timeseries(latitude=latitude, longitude=longitude, start=start, end=end, force_refresh=False)
        trace = self.core.climate_trace_emissions(country=country, force_refresh=False)
        return _dashboard(
            "energy_systems",
            "Energy Systems Data Intelligence",
            [eia, power, trace],
            ["Energy Systems", "Climate Change", "Economics", "Infrastructure"],
            ["energy-systems-calculator", "climate-change-scenario-tool", "economics-forecasting-and-scenario-tool"],
            "Energy price/system, solar/meteorological, and emissions context for energy systems intelligence.",
        )


def _collect_indicators(payloads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    indicators: List[Dict[str, Any]] = []
    for p in payloads:
        for item in p.get("indicators", []) or []:
            if isinstance(item, dict):
                indicators.append({**item, "source": p.get("source", item.get("source", "external"))})
        for item in p.get("land_cover_context", []) or []:
            if isinstance(item, dict):
                indicators.append({"label": item.get("class", "land cover"), "value": item.get("share_estimate"), "unit": "share", "interpretation": item.get("interpretation", ""), "source": p.get("source", "USGS")})
    return indicators[:16]


def _stability(payloads: List[Dict[str, Any]]) -> Dict[str, Any]:
    live = sum(1 for p in payloads if p.get("live"))
    needs_key = sum(1 for p in payloads if (p.get("cache") or {}).get("status") == "missing_key")
    fallback = len(payloads) - live
    score = max(20, min(100, 35 + live * 18 - needs_key * 6))
    if live >= max(1, len(payloads) - 1):
        status = "stable"
        public_status = "public_candidate"
    elif live >= 1:
        status = "mixed"
        public_status = "internal_review"
    else:
        status = "fallback"
        public_status = "internal_only"
    return {"status": status, "score": score, "live_sources": live, "fallback_sources": fallback, "needs_key_sources": needs_key, "public_status": public_status, "public_ready": public_status == "public_candidate"}


def _source_summaries(payloads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for p in payloads:
        rows.append({
            "source": p.get("source", "external"),
            "live": bool(p.get("live")),
            "summary": p.get("summary") or p.get("message") or "External connector returned context.",
            "message": p.get("message", ""),
            "cache": p.get("cache", {}),
            "latency_ms": p.get("latency_ms"),
        })
    return rows


def _dashboard(dashboard_id: str, title: str, payloads: List[Dict[str, Any]], article_maps: List[str], tools: List[str], summary: str) -> Dict[str, Any]:
    stability = _stability(payloads)
    recs = [
        f"Use {title} as an internal review dashboard until source health is stable.",
        "Cross-link this dashboard to relevant article maps, Workbench tools, and Research Librarian pathways.",
        "Treat external public datasets as interpretive context, not professional advice or regulatory/compliance determinations.",
    ]
    if stability.get("needs_key_sources"):
        recs.insert(0, "One or more connectors need optional API credentials before live data will be available.")
    return {
        "ok": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "version": ADVANCED_CONNECTOR_VERSION,
        "dashboard_id": dashboard_id,
        "title": title,
        "summary": summary,
        "source": "advanced-external-live" if stability["live_sources"] else "advanced-external-fallback",
        "stability": stability,
        "source_summaries": _source_summaries(payloads),
        "indicators": _collect_indicators(payloads),
        "linked_article_maps": article_maps,
        "linked_workbench_tools": tools,
        "recommendations": recs,
        "methodology": {
            "public_status": stability["public_status"],
            "summary": "Advanced external data connectors combine live API calls, cached results, registry context, and stable fallback data for dashboard reliability.",
            "review_note": "Use private dashboards to validate live connectors before publishing any data-dependent public interpretation.",
        },
    }
