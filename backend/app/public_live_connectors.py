from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from .config import Settings

PUBLIC_CONNECTOR_STATUS = {
    "live_ready": "Connector can perform public-safe live checks when backend access is enabled and upstream service is reachable.",
    "cached_ready": "Connector has cache/fallback behavior suitable for stable public display.",
    "fallback_ready": "Connector has stable public fallback summaries when live data is unavailable.",
    "planned": "Connector is documented for public methodology and future live integration.",
}

CONNECTORS: List[Dict[str, Any]] = [
    {
        "slug": "world-bank",
        "label": "World Bank",
        "family": "Development indicators",
        "endpoint": "/public/connectors/world-bank",
        "status": "live_ready",
        "source_mode": "public_api_live_cached_fallback",
        "cache_ttl_seconds": 21600,
        "freshness_window": "daily to periodic depending on indicator",
        "public_use": "Development, economy, environment, energy-access, and country/context indicators.",
        "safe_display": "Curated indicator groups with source labels, timestamps, and interpretation boundaries.",
        "fallback_reason": "Use curated public context if API availability, indicator mapping, or country scope is incomplete.",
        "requires_credentials": False,
        "private_exclusions": ["raw debug payloads", "unreviewed country rankings", "policy prescriptions"],
    },
    {
        "slug": "openalex",
        "label": "OpenAlex",
        "family": "Research metadata",
        "endpoint": "/public/connectors/openalex",
        "status": "live_ready",
        "source_mode": "public_api_live_cached_fallback",
        "cache_ttl_seconds": 21600,
        "freshness_window": "daily to weekly metadata refresh",
        "public_use": "Research graph metadata for works, concepts, authors, institutions, and open-access context.",
        "safe_display": "Metadata summaries and source-discovery context without automated authority scoring.",
        "fallback_reason": "Use planned metadata panels when API rate limits or query scope make public display unreliable.",
        "requires_credentials": False,
        "private_exclusions": ["copyrighted full text", "private notes", "unreviewed bibliographic authority claims"],
    },
    {
        "slug": "crossref",
        "label": "Crossref",
        "family": "Publication metadata",
        "endpoint": "/public/connectors/crossref",
        "status": "live_ready",
        "source_mode": "public_api_live_cached_fallback",
        "cache_ttl_seconds": 21600,
        "freshness_window": "daily to weekly DOI metadata refresh",
        "public_use": "DOI, publisher, publication-date, citation metadata, and bibliography provenance context.",
        "safe_display": "Publication metadata summaries with DOI/source labels and copyright boundaries.",
        "fallback_reason": "Use citation methodology notes when records are missing, ambiguous, or unsuitable for public display.",
        "requires_credentials": False,
        "private_exclusions": ["copyrighted full text", "unreviewed citation scoring", "private bibliography drafts"],
    },
    {
        "slug": "github",
        "label": "GitHub",
        "family": "Repository intelligence",
        "endpoint": "/public/connectors/github",
        "status": "live_ready",
        "source_mode": "public_api_live_cached_fallback",
        "cache_ttl_seconds": 3600,
        "freshness_window": "hourly public repository snapshot",
        "public_use": "Repository inventory, releases, README/docs presence, licenses, and public project-health context.",
        "safe_display": "Public repository metadata without tokens, private issues, local paths, or security-sensitive details.",
        "fallback_reason": "Use static repository summaries when API rate limits or GitHub availability interfere with public display.",
        "requires_credentials": False,
        "private_exclusions": ["tokens", "private issues", "local environment paths", "secret scan details"],
    },
    {
        "slug": "environmental",
        "label": "Environmental connectors",
        "family": "Climate, energy, monitoring, biodiversity, and land use",
        "endpoint": "/public/connectors/environmental",
        "status": "cached_ready",
        "source_mode": "mixed_live_cached_fallback",
        "cache_ttl_seconds": 1800,
        "freshness_window": "hourly to daily depending on source",
        "public_use": "NASA, NOAA/NWS, EPA, EIA, USGS, GBIF, and Climate TRACE context for environmental dashboards.",
        "safe_display": "Public-safe source status, cached summaries, fallback labels, and methodology caveats.",
        "fallback_reason": "Some sources require credentials, have rate limits, or may be delayed; public dashboards should remain stable.",
        "requires_credentials": "some_sources",
        "private_exclusions": ["API keys", "raw station payloads", "force-refresh logs", "professional compliance determinations"],
    },
]

ENVIRONMENTAL_SUBCONNECTORS: List[Dict[str, Any]] = [
    {"label": "NASA POWER", "status": "cached_ready", "public_use": "Climate and solar/weather-context indicators.", "credential_required": False},
    {"label": "NASA GIBS", "status": "cached_ready", "public_use": "Earth observation layer context.", "credential_required": False},
    {"label": "NOAA / NWS", "status": "cached_ready", "public_use": "Weather and environmental monitoring context.", "credential_required": False},
    {"label": "EPA AQS", "status": "cached_ready", "public_use": "Air-quality monitoring context.", "credential_required": "optional"},
    {"label": "EIA", "status": "cached_ready", "public_use": "Energy-system context.", "credential_required": "optional"},
    {"label": "USGS", "status": "cached_ready", "public_use": "Land, water, and geospatial context.", "credential_required": False},
    {"label": "GBIF", "status": "cached_ready", "public_use": "Biodiversity occurrence context.", "credential_required": False},
    {"label": "Climate TRACE", "status": "fallback_ready", "public_use": "Emissions-source context with conservative public language.", "credential_required": False},
]


def _now_dt() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _with_runtime(connector: Dict[str, Any], settings: Settings) -> Dict[str, Any]:
    now = _now_dt()
    ttl = int(connector.get("cache_ttl_seconds", settings.external_cache_ttl_seconds))
    # Public status is a conservative readiness label; it is not a raw upstream diagnostic.
    runtime_status = connector.get("status", "planned")
    live_possible = bool(settings.external_live) and runtime_status in {"live_ready", "cached_ready"}
    return {
        **connector,
        "runtime": {
            "public_status": runtime_status,
            "live_checks_enabled": bool(settings.external_live),
            "cache_enabled": bool(settings.external_cache_enabled),
            "live_possible": live_possible,
            "last_checked_at": _iso(now),
            "cache_ttl_seconds": ttl,
            "stale_ttl_seconds": settings.external_stale_ttl_seconds,
            "next_refresh_after": _iso(now + timedelta(seconds=ttl)),
            "display_mode": "live_or_cached" if live_possible and settings.external_cache_enabled else "fallback_summary",
            "public_safe": True,
        },
    }


def _connectors_with_runtime(settings: Settings) -> List[Dict[str, Any]]:
    return [_with_runtime(item, settings) for item in CONNECTORS]


def _counts(connectors: List[Dict[str, Any]]) -> Dict[str, int]:
    counts: Dict[str, int] = {"live_ready": 0, "cached_ready": 0, "fallback_ready": 0, "planned": 0}
    for item in connectors:
        status = item.get("status", "planned")
        counts[status] = counts.get(status, 0) + 1
    return counts


def public_connector_status(settings: Settings) -> Dict[str, Any]:
    connectors = _connectors_with_runtime(settings)
    counts = _counts(connectors)
    total = max(len(connectors), 1)
    ready_count = counts.get("live_ready", 0) + counts.get("cached_ready", 0) + counts.get("fallback_ready", 0)
    return {
        "ok": True,
        "generated_at": _iso(_now_dt()),
        "title": "Public Connector Status",
        "summary": "Public-safe live/cached/fallback status for Site Intelligence API connector families.",
        "version_scope": "v1.3.0",
        "public_status": "public_candidate",
        "score": int(round((ready_count / total) * 100)),
        "counts": counts,
        "connectors": connectors,
        "status_definitions": PUBLIC_CONNECTOR_STATUS,
        "recommended_shortcode": "[sc_public_connector_status]",
        "review_notes": [
            "Status labels are public readiness summaries, not raw uptime guarantees.",
            "Live checks must remain cache-safe and fallback-safe before appearing on public pages.",
            "Never expose API credentials, raw payloads, backend logs, or private diagnostics through public connector panels.",
        ],
    }


def public_cache_status(settings: Settings) -> Dict[str, Any]:
    connectors = _connectors_with_runtime(settings)
    now = _now_dt()
    policies = [
        {
            "label": item["label"],
            "slug": item["slug"],
            "cache_ttl_seconds": item["runtime"]["cache_ttl_seconds"],
            "stale_ttl_seconds": item["runtime"]["stale_ttl_seconds"],
            "last_checked_at": item["runtime"]["last_checked_at"],
            "next_refresh_after": item["runtime"]["next_refresh_after"],
            "display_mode": item["runtime"]["display_mode"],
        }
        for item in connectors
    ]
    return {
        "ok": True,
        "generated_at": _iso(now),
        "title": "Public Cache Status",
        "summary": "Cache and stale-safe display policy for public Site Intelligence connector panels.",
        "public_status": "public_candidate",
        "cache_enabled": settings.external_cache_enabled,
        "default_cache_ttl_seconds": settings.external_cache_ttl_seconds,
        "default_stale_ttl_seconds": settings.external_stale_ttl_seconds,
        "policies": policies,
        "recommended_shortcode": "[sc_public_cache_status]",
        "methodology": [
            "Public dashboards prefer stable cached summaries over raw live failure messages.",
            "Cached/stale labels should be visible when live source status is uncertain.",
            "Fallback summaries keep public pages readable without implying live accuracy.",
        ],
    }


def public_source_freshness(settings: Settings) -> Dict[str, Any]:
    connectors = _connectors_with_runtime(settings)
    freshness = []
    for item in connectors:
        freshness.append({
            "label": item["label"],
            "slug": item["slug"],
            "freshness_window": item["freshness_window"],
            "status": item["status"],
            "last_checked_at": item["runtime"]["last_checked_at"],
            "next_refresh_after": item["runtime"]["next_refresh_after"],
            "public_note": "Freshness is a public display label, not a certified real-time data-quality statement.",
        })
    return {
        "ok": True,
        "generated_at": _iso(_now_dt()),
        "title": "Public Source Freshness",
        "summary": "Public freshness labels for live, cached, fallback, and planned source families.",
        "public_status": "public_candidate",
        "freshness": freshness,
        "recommended_shortcode": "[sc_public_source_freshness]",
        "review_notes": [
            "Display source freshness as an interpretive label, not as a guarantee of completeness.",
            "Some upstream datasets update intermittently or have source-specific delay patterns.",
        ],
    }


def public_connector_detail(slug: str, settings: Settings) -> Dict[str, Any]:
    allowed = {item["slug"]: item for item in CONNECTORS}
    if slug not in allowed:
        raise KeyError(slug)
    connector = _with_runtime(allowed[slug], settings)
    payload: Dict[str, Any] = {
        "ok": True,
        "generated_at": _iso(_now_dt()),
        "title": f"{connector['label']} Connector",
        "summary": f"Public-safe connector status, cache policy, freshness, fallback behavior, and methodology notes for {connector['label']}.",
        "public_status": connector["status"],
        "connector": connector,
        "recommended_shortcode": f"[sc_public_{slug.replace('-', '_')}_connector]" if slug != "environmental" else "[sc_public_environmental_connectors]",
        "methodology": [
            "Use connector output as public source context, not professional advice or certification.",
            "Expose status labels, freshness labels, fallback reasons, and safe-display notes rather than raw payloads.",
            "Review all claims before using connector-derived summaries in formal publications or decision-critical settings.",
        ],
    }
    if slug == "environmental":
        payload["subconnectors"] = ENVIRONMENTAL_SUBCONNECTORS
    return payload


def public_environmental_connectors(settings: Settings) -> Dict[str, Any]:
    return public_connector_detail("environmental", settings)


def admin_connector_diagnostics(settings: Settings) -> Dict[str, Any]:
    # Admin-safe metadata only. No credentials or raw payloads are returned.
    connectors = _connectors_with_runtime(settings)
    optional_credentials = {
        "eia_api_key_configured": bool(settings.eia_api_key),
        "epa_aqs_credentials_configured": bool(settings.epa_aqs_email and settings.epa_aqs_key),
        "ga4_configured": bool(settings.ga4_property_id),
        "search_console_site_url_configured": bool(settings.search_console_site_url),
    }
    return {
        "ok": True,
        "generated_at": _iso(_now_dt()),
        "title": "Admin Connector Diagnostics",
        "summary": "Admin-safe connector configuration and public-readiness diagnostics. Secrets and raw payloads are intentionally excluded.",
        "version_scope": "v1.3.0",
        "environment": settings.environment,
        "external_live": settings.external_live,
        "external_cache_enabled": settings.external_cache_enabled,
        "external_cache_ttl_seconds": settings.external_cache_ttl_seconds,
        "external_stale_ttl_seconds": settings.external_stale_ttl_seconds,
        "optional_credentials": optional_credentials,
        "connectors": connectors,
        "hidden": [
            "API key values",
            "service account JSON",
            "raw upstream payloads",
            "backend logs",
            "private analytics",
        ],
    }
