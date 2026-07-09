from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List


PUBLIC_TOPIC_DASHBOARDS: Dict[str, Dict[str, Any]] = {
    "climate-energy": {
        "slug": "climate-energy",
        "title": "Climate + Energy Public Dashboard",
        "eyebrow": "Climate and energy",
        "summary": "Public-safe source context for climate indicators, energy systems, emissions, and Earth-observation layers.",
        "shortcode": "[sc_public_climate_energy_dashboard]",
        "public_status": "public_candidate",
        "source_mode": "stable_snapshot",
        "page_slug": "/site-intelligence/climate-energy/",
        "signals": [
            {"label": "Climate indicators", "value": "Temperature, precipitation, wind, solar", "note": "Displayed as source-labeled context, not a forecast or climate-risk assessment."},
            {"label": "Energy context", "value": "Energy demand and emissions signals", "note": "Useful for public orientation and source-methodology discussion."},
            {"label": "Earth observation", "value": "Cloud, smoke, land, water, heat, and precipitation layers", "note": "Interpreted as visual/public context rather than operational monitoring."},
        ],
        "recommended_sections": [
            "Climate and energy source snapshot",
            "Emissions and energy-system context",
            "Earth-observation layer notes",
            "Public methodology and limitations",
        ],
    },
    "environmental-monitoring": {
        "slug": "environmental-monitoring",
        "title": "Environmental Monitoring Public Dashboard",
        "eyebrow": "Environmental monitoring",
        "summary": "Public-safe overview for air quality, land context, observation layers, monitoring readiness, and source limitations.",
        "shortcode": "[sc_public_environmental_monitoring_dashboard]",
        "public_status": "public_candidate",
        "source_mode": "fallback_aware",
        "page_slug": "/site-intelligence/environmental-monitoring/",
        "signals": [
            {"label": "Air quality", "value": "EPA/AQS-style context", "note": "Requires source health and location scope review before public interpretation."},
            {"label": "Land context", "value": "USGS-style land-cover signals", "note": "Useful for urban resilience, environmental exposure, and land-use framing."},
            {"label": "Observation layers", "value": "Remote-sensing visual context", "note": "Supports public explanation of source layers and monitoring boundaries."},
        ],
        "recommended_sections": [
            "Air-quality source context",
            "Land-cover and observation notes",
            "Monitoring readiness",
            "Source limitations and fallback behavior",
        ],
    },
    "biodiversity-land-use": {
        "slug": "biodiversity-land-use",
        "title": "Biodiversity + Land Use Public Dashboard",
        "eyebrow": "Biodiversity and land use",
        "summary": "Public-safe context for biodiversity occurrence data, land-use interpretation, ecological signals, and source caveats.",
        "shortcode": "[sc_public_biodiversity_land_use_dashboard]",
        "public_status": "public_candidate",
        "source_mode": "source_context",
        "page_slug": "/site-intelligence/biodiversity-land-use/",
        "signals": [
            {"label": "Biodiversity", "value": "GBIF-style occurrence context", "note": "Occurrence data is not a complete ecological inventory and requires careful interpretation."},
            {"label": "Land use", "value": "Land-cover and habitat context", "note": "Supports ecological framing and regional systems interpretation."},
            {"label": "Public caveats", "value": "Sampling bias and source limits", "note": "Public dashboards should explain data gaps and collection bias explicitly."},
        ],
        "recommended_sections": [
            "Biodiversity occurrence context",
            "Land-use and habitat signals",
            "Sampling-bias caveats",
            "Methodology notes",
        ],
    },
    "knowledge-system": {
        "slug": "knowledge-system",
        "title": "Knowledge-System Public Dashboard",
        "eyebrow": "Knowledge system",
        "summary": "Public-safe overview of Sustainable Catalyst article maps, topic areas, platform surfaces, registry coverage, and public knowledge pathways.",
        "shortcode": "[sc_public_knowledge_system_dashboard]",
        "public_status": "public_ready",
        "source_mode": "registry_summary",
        "page_slug": "/site-intelligence/knowledge-system/",
        "signals": [
            {"label": "Article maps", "value": "Connected topic architecture", "note": "Shows how knowledge areas, series, and platform modules relate."},
            {"label": "Registry", "value": "Public page and tool mapping", "note": "Public summaries can show coverage and structure without raw analytics."},
            {"label": "Pathways", "value": "Research, platform, publications, library", "note": "Helps visitors understand Sustainable Catalyst as a knowledge infrastructure project."},
        ],
        "recommended_sections": [
            "Knowledge-area overview",
            "Registry and article-map coverage",
            "Featured public surfaces",
            "Public knowledge pathways",
        ],
    },
    "search-discovery": {
        "slug": "search-discovery",
        "title": "Search + Discovery Public Dashboard",
        "eyebrow": "Search and discovery",
        "summary": "Public-safe interpretation of topic visibility, discovery pathways, search methodology, and knowledge-system findability.",
        "shortcode": "[sc_public_search_discovery_dashboard]",
        "public_status": "internal_review",
        "source_mode": "public_summary_only",
        "page_slug": "/site-intelligence/search-discovery/",
        "signals": [
            {"label": "Findability", "value": "Public topic discovery", "note": "Use themes and categories rather than raw query/report detail."},
            {"label": "Search visibility", "value": "Topic-level public explanation", "note": "Keep precise Search Console data internal unless manually reviewed."},
            {"label": "Internal pathways", "value": "Navigation and cross-link context", "note": "Supports public explanation of library and article-map discovery."},
        ],
        "recommended_sections": [
            "Topic visibility themes",
            "Knowledge-system discovery routes",
            "Public/internal boundary notes",
            "Search methodology caveats",
        ],
    },
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def topic_dashboard_directory() -> Dict[str, Any]:
    dashboards = []
    for key in ["climate-energy", "environmental-monitoring", "biodiversity-land-use", "knowledge-system", "search-discovery"]:
        item = PUBLIC_TOPIC_DASHBOARDS[key]
        dashboards.append({
            "slug": item["slug"],
            "title": item["title"],
            "eyebrow": item["eyebrow"],
            "summary": item["summary"],
            "shortcode": item["shortcode"],
            "public_status": item["public_status"],
            "source_mode": item["source_mode"],
            "page_slug": item["page_slug"],
        })
    return {
        "ok": True,
        "generated_at": _now(),
        "title": "Public Topic Dashboard Directory",
        "summary": "A public-safe directory of topic dashboards for Sustainable Catalyst Site Intelligence.",
        "public_status": "public_candidate",
        "dashboards": dashboards,
        "recommended_index_shortcode": "[sc_public_dashboard_directory]",
        "review_notes": [
            "Use topic dashboards as public orientation pages, not internal analytics consoles.",
            "Keep raw GA4, Search Console, diagnostics, and report exports private unless manually reviewed.",
            "Pair each topic dashboard with source-methodology notes and professional-advice boundaries.",
        ],
    }


def public_topic_dashboard(slug: str) -> Dict[str, Any]:
    item = PUBLIC_TOPIC_DASHBOARDS.get(slug)
    if not item:
        raise KeyError(slug)
    return {
        "ok": True,
        "generated_at": _now(),
        **item,
        "cards": item["signals"],
        "methodology": {
            "shown": [
                "Public-safe source summaries",
                "Topic-level context and methodology notes",
                "Curated readiness/status language",
                "Public dashboard placement guidance",
            ],
            "hidden": [
                "Raw analytics and query-level reports",
                "Credential, token, backend, or API configuration values",
                "Internal publishing queues and unreleased AI briefs",
                "Force-refresh diagnostics and source health internals",
            ],
        },
        "ctas": [
            {"label": "Open Site Intelligence", "url": "https://sustainablecatalyst.com/site-intelligence/"},
            {"label": "Research Library", "url": "https://sustainablecatalyst.com/research-library/"},
            {"label": "Workbench", "url": "https://sustainablecatalyst.com/workbench/"},
        ],
        "review_notes": [
            "This dashboard is public-safe by design and should remain methodology-forward.",
            "Treat external data as source context rather than professional advice or operational monitoring.",
            "Use private/admin dashboards for live connector diagnostics and raw report details.",
        ],
    }


def public_source_methodology() -> Dict[str, Any]:
    return {
        "ok": True,
        "generated_at": _now(),
        "title": "Public Source Methodology",
        "eyebrow": "Source methodology",
        "summary": "How Sustainable Catalyst Site Intelligence treats public data connectors, source health, fallback behavior, and public/private boundaries.",
        "public_status": "public_ready",
        "principles": [
            {"label": "Source context", "title": "Signals are interpretive", "detail": "External sources are presented as context for public learning and platform transparency, not as authoritative real-time operational data."},
            {"label": "Fallback-aware", "title": "Reliability before novelty", "detail": "Public dashboards may use cached, stable, or curated fallback summaries when live APIs are unavailable or unsuitable."},
            {"label": "Boundary-first", "title": "Private data stays private", "detail": "Public pages exclude raw analytics, credentials, diagnostics, internal reports, and unreleased strategy queues."},
            {"label": "Reviewable", "title": "Methodology travels with the display", "detail": "Every public topic dashboard should include source notes, limitations, and professional-advice boundaries."},
        ],
        "source_families": [
            {"family": "Climate and energy", "examples": "NASA POWER, Earth-observation layers, emissions context", "public_use": "Stable public summaries and source-labeled climate/energy context."},
            {"family": "Environmental monitoring", "examples": "Air quality, land cover, remote-sensing layers", "public_use": "Monitoring-oriented context with explicit caveats and fallback notes."},
            {"family": "Biodiversity and land use", "examples": "Occurrence records and land-use signals", "public_use": "Ecological context with sampling-bias and completeness caveats."},
            {"family": "Knowledge system", "examples": "Registry, article maps, public surfaces", "public_use": "Public explanation of Sustainable Catalyst as connected knowledge infrastructure."},
            {"family": "Search and discovery", "examples": "Topic visibility and discovery pathways", "public_use": "Theme-level findability explanation; raw query details remain private unless reviewed."},
        ],
        "recommended_shortcode": "[sc_public_source_methodology]",
    }
