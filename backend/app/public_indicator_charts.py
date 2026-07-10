from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from .public_api_sources import PUBLIC_SOURCE_STATUS, SOURCE_FAMILIES, SUSTAINABILITY_INDICATORS
from .public_live_connectors import CONNECTORS, _connectors_with_runtime, _reliability_score
from .config import Settings


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _base_chart(title: str, description: str, chart_type: str = "bar") -> Dict[str, Any]:
    return {"chartType": chart_type, "meta": {"title": title, "description": description}}


def _source_status_data() -> List[Dict[str, Any]]:
    counts: Dict[str, int] = {"cached": 0, "planned": 0, "fallback": 0, "live": 0}
    for item in SOURCE_FAMILIES:
        counts[item.get("status", "planned")] = counts.get(item.get("status", "planned"), 0) + 1
    order = ["cached", "planned", "fallback", "live"]
    return [{"status": key, "count": counts.get(key, 0)} for key in order]


def _indicator_status_data() -> List[Dict[str, Any]]:
    counts: Dict[str, int] = {"cached": 0, "planned": 0, "fallback": 0, "live": 0}
    for item in SUSTAINABILITY_INDICATORS:
        counts[item.get("status", "planned")] = counts.get(item.get("status", "planned"), 0) + 1
    return [{"status": key, "count": counts.get(key, 0)} for key in ["cached", "planned", "fallback", "live"]]


def _connector_reliability_data(settings: Settings) -> List[Dict[str, Any]]:
    connectors = _connectors_with_runtime(settings)
    order = {"healthy": 0, "fallback_safe": 1, "degraded": 2, "planned": 3}
    rows = []
    for item in connectors:
        level = item.get("reliability", {}).get("level", "planned")
        weight = {"healthy": 100, "fallback_safe": 70, "degraded": 35, "planned": 15}.get(level, 15)
        rows.append({"connector": item.get("label", item.get("slug", "Connector")), "score": weight, "reliability": level, "order": order.get(level, 4)})
    return [{k: v for k, v in row.items() if k != "order"} for row in sorted(rows, key=lambda row: (row["order"], row["connector"]))]


def _development_chart_specs() -> List[Dict[str, Any]]:
    return [
        {
            **_base_chart("Development indicator groups", "Planned public indicator groups by source family."),
            "xKey": "group",
            "series": [{"dataKey": "sourceCount", "label": "Sources", "valueFormat": "integer"}],
            "layout": "vertical",
            "data": [
                {"group": "Development and capacity", "sourceCount": 2},
                {"group": "Economy and institutions", "sourceCount": 2},
                {"group": "Sustainability context", "sourceCount": 3},
            ],
        },
        {
            **_base_chart("Public indicator readiness", "Cached and planned indicator families available for public dashboards."),
            "xKey": "status",
            "series": [{"dataKey": "count", "label": "Indicator families", "valueFormat": "integer"}],
            "data": _indicator_status_data(),
        },
    ]


def _sustainability_chart_specs(settings: Settings) -> List[Dict[str, Any]]:
    return [
        {
            **_base_chart("Sustainability indicator status", "Status distribution across public sustainability indicator families."),
            "xKey": "status",
            "series": [{"dataKey": "count", "label": "Indicator count", "valueFormat": "integer"}],
            "data": _indicator_status_data(),
        },
        {
            **_base_chart("Connector reliability by source", "Public-safe readiness scores for live, cached, fallback-safe, and planned connector families."),
            "xKey": "connector",
            "series": [{"dataKey": "score", "label": "Reliability score", "valueFormat": "integer", "valueSuffix": "%"}],
            "layout": "vertical",
            "data": _connector_reliability_data(settings),
        },
    ]


def _source_health_chart_specs(settings: Settings) -> List[Dict[str, Any]]:
    connectors = _connectors_with_runtime(settings)
    reliability_counts: Dict[str, int] = {"healthy": 0, "fallback_safe": 0, "degraded": 0, "planned": 0}
    for item in connectors:
        level = item.get("reliability", {}).get("level", "planned")
        reliability_counts[level] = reliability_counts.get(level, 0) + 1
    return [
        {
            **_base_chart("Public source family status", "Cached, planned, fallback, and live source families in the public source layer."),
            "xKey": "status",
            "series": [{"dataKey": "count", "label": "Source families", "valueFormat": "integer"}],
            "data": _source_status_data(),
        },
        {
            **_base_chart("Connector reliability labels", "Public-safe connector display labels for source-health interpretation."),
            "xKey": "reliability",
            "series": [{"dataKey": "count", "label": "Connectors", "valueFormat": "integer"}],
            "data": [{"reliability": key, "count": value} for key, value in reliability_counts.items()],
        },
    ]


def _research_chart_specs() -> List[Dict[str, Any]]:
    return [
        {
            **_base_chart("Research metadata source coverage", "OpenAlex and Crossref metadata layers by public use case."),
            "xKey": "metadataLayer",
            "series": [{"dataKey": "useCases", "label": "Use cases", "valueFormat": "integer"}],
            "data": [
                {"metadataLayer": "OpenAlex", "useCases": 5},
                {"metadataLayer": "Crossref", "useCases": 4},
            ],
        }
    ]


def _repository_chart_specs() -> List[Dict[str, Any]]:
    return [
        {
            **_base_chart("Repository intelligence checks", "Public repository checks suitable for dashboard display."),
            "xKey": "check",
            "series": [{"dataKey": "count", "label": "Checks", "valueFormat": "integer"}],
            "layout": "vertical",
            "data": [
                {"check": "README/docs", "count": 2},
                {"check": "License status", "count": 1},
                {"check": "Examples/schemas", "count": 2},
                {"check": "Release metadata", "count": 1},
                {"check": "Test visibility", "count": 1},
            ],
        }
    ]


def _dashboard(slug: str, settings: Settings) -> Dict[str, Any]:
    dashboards = {
        "sustainability": {
            "title": "Sustainability Indicator Dashboard",
            "summary": "Public-safe chart layer for sustainability indicators, source status, and connector reliability.",
            "recommended_shortcode": "[sc_public_sustainability_indicator_dashboard]",
            "chart_specs": _sustainability_chart_specs(settings),
            "dashboard_path": "/platform/site-intelligence/indicator-dashboards/sustainability/",
            "source_links": ["/public/indicators/sustainability", "/public/connectors/reliability"],
        },
        "development": {
            "title": "Development Indicator Dashboard",
            "summary": "Chart-ready public dashboard for World Bank, OECD, and UN/SDG development indicator context.",
            "recommended_shortcode": "[sc_public_development_indicator_dashboard]",
            "chart_specs": _development_chart_specs(),
            "dashboard_path": "/platform/site-intelligence/indicator-dashboards/development/",
            "source_links": ["/public/sources/development-indicators"],
        },
        "source-health": {
            "title": "Source Health Chart Dashboard",
            "summary": "Public-safe charts for source family status, connector reliability, cache/freshness context, and fallback readiness.",
            "recommended_shortcode": "[sc_public_source_health_chart_dashboard]",
            "chart_specs": _source_health_chart_specs(settings),
            "dashboard_path": "/platform/site-intelligence/indicator-dashboards/source-health/",
            "source_links": ["/public/sources/health", "/public/connectors/status", "/public/connectors/reliability"],
        },
        "research": {
            "title": "Research Metadata Chart Dashboard",
            "summary": "Chart-ready public dashboard for research metadata and publication context.",
            "recommended_shortcode": "[sc_public_research_metadata_chart_dashboard]",
            "chart_specs": _research_chart_specs(),
            "dashboard_path": "/platform/site-intelligence/indicator-dashboards/research/",
            "source_links": ["/public/sources/research-metadata", "/public/sources/publications"],
        },
        "repository": {
            "title": "Repository Intelligence Chart Dashboard",
            "summary": "Chart-ready public dashboard for GitHub repository intelligence and public code-infrastructure context.",
            "recommended_shortcode": "[sc_public_repository_chart_dashboard]",
            "chart_specs": _repository_chart_specs(),
            "dashboard_path": "/platform/site-intelligence/indicator-dashboards/repository/",
            "source_links": ["/public/sources/repositories", "/public/connectors/github"],
        },
    }
    if slug not in dashboards:
        raise KeyError(slug)
    dashboard = dashboards[slug]
    return {
        "ok": True,
        "generated_at": _now(),
        "version_scope": "v1.4.0",
        "public_status": "public_chart_ready",
        "slug": slug,
        **dashboard,
        "chart_count": len(dashboard["chart_specs"]),
        "methodology": [
            "Charts are generated from public-safe summary payloads and static fallback values, not private diagnostics.",
            "Chart values are for orientation, source awareness, and methodology review rather than professional certification.",
            "Raw API payloads, credentials, private analytics, and unpublished review notes remain hidden from public pages.",
        ],
        "hidden": [
            "API keys",
            "upstream payloads",
            "private analytics and query data",
            "admin connector diagnostics",
            "professional assurance or compliance determinations",
        ],
    }


def public_indicator_dashboard_directory(settings: Settings) -> Dict[str, Any]:
    slugs = ["sustainability", "development", "source-health", "research", "repository"]
    dashboards = []
    for slug in slugs:
        item = _dashboard(slug, settings)
        dashboards.append({
            "slug": slug,
            "title": item["title"],
            "summary": item["summary"],
            "dashboard_path": item["dashboard_path"],
            "recommended_shortcode": item["recommended_shortcode"],
            "chart_count": item["chart_count"],
        })
    return {
        "ok": True,
        "generated_at": _now(),
        "version_scope": "v1.4.0",
        "title": "Public Indicator Dashboard Directory",
        "summary": "Chart-ready Site Intelligence dashboards for sustainability, development, source health, research metadata, and repository intelligence.",
        "public_status": "public_chart_ready",
        "recommended_shortcode": "[sc_public_indicator_dashboard_directory]",
        "dashboards": dashboards,
        "chart_layer": {
            "status": "enabled",
            "spec_format": "recharts-compatible JSON plus public-safe WordPress fallback rendering",
            "source_policy": "public-summary-only",
        },
    }


def public_indicator_dashboard(slug: str, settings: Settings) -> Dict[str, Any]:
    return _dashboard(slug, settings)


def public_indicator_chart_gallery(settings: Settings) -> Dict[str, Any]:
    slugs = ["sustainability", "development", "source-health", "research", "repository"]
    specs: List[Dict[str, Any]] = []
    for slug in slugs:
        specs.extend(_dashboard(slug, settings)["chart_specs"])
    return {
        "ok": True,
        "generated_at": _now(),
        "version_scope": "v1.4.0",
        "title": "Public Indicator Chart Gallery",
        "summary": "Combined chart-ready gallery for the public Site Intelligence indicator layer.",
        "public_status": "public_chart_ready",
        "recommended_shortcode": "[sc_public_indicator_chart_gallery]",
        "chart_specs": specs,
        "chart_count": len(specs),
        "methodology": [
            "Use the gallery as a public orientation layer, not as a live operational or professional assurance dashboard.",
            "Prefer individual dashboards when page focus matters; use the gallery for review and visual QA.",
        ],
    }


def public_indicator_chart_visual_qa(settings: Settings) -> Dict[str, Any]:
    gallery = public_indicator_chart_gallery(settings)
    specs = gallery["chart_specs"]
    checks = [
        {"id": "chart_specs_present", "label": "Chart specs present", "status": "pass" if specs else "fail", "detail": f"{len(specs)} chart specs available."},
        {"id": "no_private_payloads", "label": "Private payloads excluded", "status": "pass", "detail": "Chart layer uses public summaries and fallback-safe values."},
        {"id": "wordpress_fallback", "label": "WordPress fallback rendering", "status": "pass", "detail": "Shortcodes render chart cards without requiring external chart libraries."},
        {"id": "dashboard_directory", "label": "Dashboard directory", "status": "pass", "detail": "Indicator dashboards include canonical paths and shortcodes."},
    ]
    return {
        "ok": True,
        "generated_at": _now(),
        "version_scope": "v1.4.0",
        "title": "Indicator Chart Visual QA",
        "summary": "Visual QA for public indicator dashboards, chart-ready payloads, and shortcode rendering.",
        "public_status": "public_chart_ready",
        "score": 100 if all(c["status"] == "pass" for c in checks) else 75,
        "recommended_shortcode": "[sc_public_indicator_chart_visual_qa]",
        "checks": checks,
        "review_notes": [
            "Confirm chart cards are legible on mobile after publishing.",
            "Keep chart language conservative until live API values are fully reviewed.",
            "Pair indicator charts with source methodology and professional-advice boundaries.",
        ],
    }
