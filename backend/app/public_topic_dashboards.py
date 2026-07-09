from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

PUBLIC_BASE_PATH = "/platform/site-intelligence/"
PUBLIC_BASE_URL = "https://sustainablecatalyst.com/platform/site-intelligence/"

PUBLIC_TOPIC_ORDER: List[str] = [
    "climate-energy",
    "environmental-monitoring",
    "biodiversity-land-use",
    "knowledge-system",
    "search-discovery",
]

PUBLIC_NAVIGATION: List[Dict[str, str]] = [
    {"slug": "site-intelligence", "label": "Site Intelligence", "path": PUBLIC_BASE_PATH, "kind": "hub"},
    {"slug": "dashboards", "label": "Dashboard Directory", "path": PUBLIC_BASE_PATH + "dashboards/", "kind": "directory"},
    {"slug": "climate-energy", "label": "Climate + Energy", "path": PUBLIC_BASE_PATH + "climate-energy/", "kind": "topic"},
    {"slug": "environmental-monitoring", "label": "Environmental Monitoring", "path": PUBLIC_BASE_PATH + "environmental-monitoring/", "kind": "topic"},
    {"slug": "biodiversity-land-use", "label": "Biodiversity + Land Use", "path": PUBLIC_BASE_PATH + "biodiversity-land-use/", "kind": "topic"},
    {"slug": "knowledge-system", "label": "Knowledge System", "path": PUBLIC_BASE_PATH + "knowledge-system/", "kind": "topic"},
    {"slug": "search-discovery", "label": "Search + Discovery", "path": PUBLIC_BASE_PATH + "search-discovery/", "kind": "topic"},
    {"slug": "source-methodology", "label": "Source Methodology", "path": PUBLIC_BASE_PATH + "source-methodology/", "kind": "methodology"},
]

PUBLIC_TOPIC_DASHBOARDS: Dict[str, Dict[str, Any]] = {
    "climate-energy": {
        "slug": "climate-energy",
        "title": "Climate + Energy Public Dashboard",
        "eyebrow": "Climate and energy",
        "summary": "Public-safe source context for climate indicators, energy systems, emissions, and Earth-observation layers.",
        "shortcode": "[sc_public_climate_energy_dashboard]",
        "public_status": "public_candidate",
        "source_mode": "stable_snapshot",
        "page_slug": PUBLIC_BASE_PATH + "climate-energy/",
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
        "excerpt": "A public-safe climate and energy dashboard for source-labeled climate, energy, emissions, Earth observation, and methodology context within Site Intelligence.",
        "meta_description": "Climate + Energy is a public-safe Site Intelligence dashboard for source-labeled climate, energy, emissions, Earth observation, and methodology context across Sustainable Catalyst.",
    },
    "environmental-monitoring": {
        "slug": "environmental-monitoring",
        "title": "Environmental Monitoring Public Dashboard",
        "eyebrow": "Environmental monitoring",
        "summary": "Public-safe overview for air quality, land context, observation layers, monitoring readiness, and source limitations.",
        "shortcode": "[sc_public_environmental_monitoring_dashboard]",
        "public_status": "public_candidate",
        "source_mode": "fallback_aware",
        "page_slug": PUBLIC_BASE_PATH + "environmental-monitoring/",
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
        "excerpt": "A public-safe environmental monitoring dashboard for air, land, water, observation systems, source status, and monitoring methodology across Site Intelligence.",
        "meta_description": "Environmental Monitoring is a public-safe Site Intelligence dashboard for air, land, water, observation systems, source status, QA/QC context, and environmental monitoring methodology.",
    },
    "biodiversity-land-use": {
        "slug": "biodiversity-land-use",
        "title": "Biodiversity + Land Use Public Dashboard",
        "eyebrow": "Biodiversity and land use",
        "summary": "Public-safe context for biodiversity occurrence data, land-use interpretation, ecological signals, and source caveats.",
        "shortcode": "[sc_public_biodiversity_land_use_dashboard]",
        "public_status": "public_candidate",
        "source_mode": "source_context",
        "page_slug": PUBLIC_BASE_PATH + "biodiversity-land-use/",
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
        "excerpt": "A public-safe dashboard for biodiversity, land cover, land use, ecological source context, and environmental systems interpretation across Sustainable Catalyst.",
        "meta_description": "Biodiversity + Land Use is a public-safe Site Intelligence dashboard for biodiversity, land cover, land use, ecological source context, and environmental systems interpretation.",
    },
    "knowledge-system": {
        "slug": "knowledge-system",
        "title": "Knowledge System Public Dashboard",
        "eyebrow": "Knowledge system",
        "summary": "Public-safe overview of Sustainable Catalyst article maps, topic areas, platform surfaces, registry coverage, and public knowledge pathways.",
        "shortcode": "[sc_public_knowledge_system_dashboard]",
        "public_status": "public_ready",
        "source_mode": "registry_summary",
        "page_slug": PUBLIC_BASE_PATH + "knowledge-system/",
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
        "excerpt": "A public-safe dashboard for Sustainable Catalyst’s article maps, research pathways, platform tools, repositories, public dashboards, and knowledge-system structure.",
        "meta_description": "Knowledge System is a public-safe Site Intelligence dashboard for article maps, research pathways, platform tools, repositories, dashboards, and Sustainable Catalyst’s public knowledge structure.",
    },
    "search-discovery": {
        "slug": "search-discovery",
        "title": "Search + Discovery Public Dashboard",
        "eyebrow": "Search and discovery",
        "summary": "Public-safe interpretation of topic visibility, discovery pathways, search methodology, and knowledge-system findability.",
        "shortcode": "[sc_public_search_discovery_dashboard]",
        "public_status": "internal_review",
        "source_mode": "public_summary_only",
        "page_slug": PUBLIC_BASE_PATH + "search-discovery/",
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
        "excerpt": "A public-safe dashboard for search visibility, discovery pathways, metadata structure, internal linking, topic navigation, and knowledge-system findability across Sustainable Catalyst.",
        "meta_description": "Search + Discovery is a public-safe Site Intelligence dashboard for search visibility, discovery pathways, metadata structure, internal linking, topic navigation, and findability.",
    },
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _absolute_url(path: str) -> str:
    return "https://sustainablecatalyst.com" + path if path.startswith("/") else path


def _active_navigation(current_slug: str = "") -> List[Dict[str, Any]]:
    current = (current_slug or "").strip("/")
    items = []
    for item in PUBLIC_NAVIGATION:
        copy = dict(item)
        copy["url"] = _absolute_url(copy["path"])
        copy["active"] = copy["slug"] == current
        items.append(copy)
    return items


def public_dashboard_navigation(current_slug: str = "") -> Dict[str, Any]:
    return {
        "ok": True,
        "generated_at": _now(),
        "title": "Site Intelligence Dashboard Navigation",
        "summary": "Public navigation for Site Intelligence hub, dashboard directory, topic dashboards, and source methodology.",
        "current_slug": current_slug,
        "items": _active_navigation(current_slug),
        "recommended_shortcode": "[sc_public_dashboard_navigation]",
    }


def _template_for(item: Dict[str, Any]) -> Dict[str, Any]:
    slug = item["slug"]
    return {
        "slug": slug,
        "title": item["title"].replace(" Public Dashboard", ""),
        "canonical_path": item["page_slug"],
        "canonical_url": _absolute_url(item["page_slug"]),
        "shortcode": item["shortcode"],
        "excerpt": item.get("excerpt", item["summary"]),
        "meta_description": item.get("meta_description", item["summary"]),
        "hero_kicker": "Site Intelligence",
        "primary_anchor": "#dashboard",
        "page_classes": f"cc-platform-v5 ccp-site-intelligence-public ccp-si-topic-page ccp-si-{slug}",
        "required_sections": [
            "Hero with dashboard navigation buttons",
            "Dashboard navigation block",
            "Live shortcode module",
            "What it shows",
            "Source layer or knowledge architecture",
            "Methodology pipeline",
            "Related dashboards",
            "Boundaries and footer links",
        ],
    }


def public_topic_page_templates(slug: str | None = None) -> Dict[str, Any]:
    templates = [_template_for(PUBLIC_TOPIC_DASHBOARDS[key]) for key in PUBLIC_TOPIC_ORDER]
    templates.append({
        "slug": "source-methodology",
        "title": "Source Methodology",
        "canonical_path": PUBLIC_BASE_PATH + "source-methodology/",
        "canonical_url": _absolute_url(PUBLIC_BASE_PATH + "source-methodology/"),
        "shortcode": "[sc_public_source_methodology]",
        "excerpt": "A public-safe methodology page for source health, connector assumptions, public/private boundaries, fallback behavior, dashboard limits, and responsible interpretation across Site Intelligence.",
        "meta_description": "Source Methodology explains source health, connector assumptions, public/private boundaries, fallback behavior, dashboard limits, and responsible interpretation across Site Intelligence.",
        "hero_kicker": "Site Intelligence",
        "primary_anchor": "#methodology-dashboard",
        "page_classes": "cc-platform-v5 ccp-site-intelligence-public ccp-si-topic-page ccp-si-source-methodology",
        "required_sections": [
            "Hero with dashboard navigation buttons",
            "Dashboard navigation block",
            "Live methodology shortcode module",
            "What it explains",
            "Source rules",
            "Interpretation framework",
            "Public/private boundaries",
            "Related dashboards and footer links",
        ],
    })
    templates.append({
        "slug": "dashboards",
        "title": "Dashboard Directory",
        "canonical_path": PUBLIC_BASE_PATH + "dashboards/",
        "canonical_url": _absolute_url(PUBLIC_BASE_PATH + "dashboards/"),
        "shortcode": "[sc_public_dashboard_directory]",
        "excerpt": "A public directory of Site Intelligence dashboards for climate and energy, environmental monitoring, biodiversity and land use, knowledge-system structure, search and discovery, and source methodology.",
        "meta_description": "The Site Intelligence Dashboard Directory organizes public dashboards for environmental context, knowledge architecture, discovery, and source methodology across Sustainable Catalyst.",
        "hero_kicker": "Site Intelligence",
        "primary_anchor": "#dashboard-directory",
        "page_classes": "cc-platform-v5 ccp-site-intelligence-public ccp-si-topic-page ccp-si-dashboard-directory",
        "required_sections": [
            "Hero with dashboard navigation buttons",
            "Dashboard navigation block",
            "Live directory shortcode module",
            "What it organizes",
            "Dashboard catalog",
            "Directory methodology",
            "Recommended paths",
            "Boundaries and footer links",
        ],
    })
    if slug:
        match = [item for item in templates if item["slug"] == slug]
        if not match:
            raise KeyError(slug)
        templates = match
    return {
        "ok": True,
        "generated_at": _now(),
        "title": "Public Topic Page Templates",
        "summary": "Copy-ready metadata, shortcode, and section guidance for Site Intelligence public topic pages.",
        "templates": templates,
        "recommended_shortcode": "[sc_public_topic_page_templates]",
    }


def topic_page_visual_qa() -> Dict[str, Any]:
    checks = [
        {"id": "canonical_paths", "label": "Canonical paths", "status": "pass", "detail": "All topic pages use /platform/site-intelligence/ child paths."},
        {"id": "navigation", "label": "Dashboard navigation", "status": "pass", "detail": "Every page should link to the hub, directory, five topic dashboards, and source methodology."},
        {"id": "shortcodes", "label": "Public shortcodes only", "status": "pass", "detail": "Topic pages use public-safe shortcodes and avoid private/admin shortcodes."},
        {"id": "active_state", "label": "Active page state", "status": "pass", "detail": "WordPress JavaScript marks matching dashboard links with an active class for visual consistency."},
        {"id": "copy_boundaries", "label": "Boundary language", "status": "pass", "detail": "Pages keep professional-advice, source-limit, and public/private boundaries visible."},
        {"id": "mobile_wrapping", "label": "Text wrapping", "status": "review", "detail": "Use nowrap utilities only around short product names; avoid forcing full paragraphs or whole headings onto one line."},
    ]
    return {
        "ok": True,
        "generated_at": _now(),
        "title": "Site Intelligence Public Topic Page Visual QA",
        "summary": "QA checks for the public Site Intelligence page system and navigation polish.",
        "score": 94,
        "status": "ready_for_public_review",
        "checks": checks,
        "recommended_public_pages": [item["path"] for item in PUBLIC_NAVIGATION],
        "review_notes": [
            "Keep the custom ccp page shell and the public shortcodes separate; do not nest the flagship shortcode inside the custom shell.",
            "Clear WordPress, Cloudflare, and browser cache after plugin CSS or JavaScript updates.",
            "Use short button labels on mobile and nowrap spans only for names such as Site Intelligence and Knowledge Library.",
        ],
    }


def topic_dashboard_directory() -> Dict[str, Any]:
    dashboards = []
    for key in PUBLIC_TOPIC_ORDER:
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
            "url": _absolute_url(item["page_slug"]),
        })
    return {
        "ok": True,
        "generated_at": _now(),
        "title": "Public Topic Dashboard Directory",
        "summary": "A public-safe directory of topic dashboards for Sustainable Catalyst Site Intelligence.",
        "public_status": "public_candidate",
        "base_path": PUBLIC_BASE_PATH,
        "dashboards": dashboards,
        "navigation": _active_navigation("dashboards"),
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
        "url": _absolute_url(item["page_slug"]),
        "navigation": _active_navigation(slug),
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
            {"label": "Site Intelligence", "url": _absolute_url(PUBLIC_BASE_PATH)},
            {"label": "Dashboard Directory", "url": _absolute_url(PUBLIC_BASE_PATH + "dashboards/")},
            {"label": "Source Methodology", "url": _absolute_url(PUBLIC_BASE_PATH + "source-methodology/")},
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
        "page_slug": PUBLIC_BASE_PATH + "source-methodology/",
        "url": _absolute_url(PUBLIC_BASE_PATH + "source-methodology/"),
        "navigation": _active_navigation("source-methodology"),
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
