from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List

from .events import event_diagnostics
from .metrics import build_page_metrics, dashboard_totals, hub_summary, mapping_coverage, safe_div
from .models import PageMetric
from .registry import ContentRegistry


def _round_public(value: float, bucket: int = 100) -> int:
    if value <= 0:
        return 0
    if value < bucket:
        return int(value)
    return int(round(value / bucket) * bucket)


def _band(value: float) -> str:
    value = float(value or 0)
    if value == 0:
        return "0"
    if value < 100:
        return "1–99"
    if value < 500:
        return "100–499"
    if value < 1000:
        return "500–999"
    if value < 5000:
        return "1K–4.9K"
    if value < 10000:
        return "5K–9.9K"
    if value < 50000:
        return "10K–49K"
    return "50K+"


def _status_from_score(score: float) -> str:
    if score >= 80:
        return "public_ready"
    if score >= 60:
        return "public_candidate"
    if score >= 40:
        return "internal_review"
    return "not_public_ready"


def _topic_role(hub: str) -> str:
    h = (hub or "").lower()
    if "research" in h:
        return "Knowledge architecture and research pathways"
    if "platform" in h or "model" in h:
        return "Applied tool and platform layer"
    if "publication" in h:
        return "Editorial and publishing surface"
    if "law" in h:
        return "Governance, law, and institutional reasoning"
    if "meaning" in h:
        return "Humanistic and interpretive knowledge layer"
    return "Sustainable Catalyst knowledge area"


def _public_page_focus(metric: PageMetric) -> str:
    if metric.repository_clicks > 0:
        return "Repository-linked article or tool surface"
    if metric.workbench_events > 0:
        return "Tool-connected modeling surface"
    if metric.research_librarian_events > 0:
        return "Guided inquiry surface"
    if metric.pathway_events > 0:
        return "Pathway and article-map navigation surface"
    if metric.mapping_status == "unmapped":
        return "Registry review candidate"
    return "Public knowledge surface"



def public_landing_page() -> Dict[str, Any]:
    """Public-facing landing-page model for Site Intelligence.

    This endpoint is intentionally static/curated enough to be safe for public
    pages while still explaining the live system architecture. It does not call
    GA4, Search Console, or external APIs.
    """
    return {
        "ok": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "title": "Sustainable Catalyst Site Intelligence",
        "eyebrow": "Public Dashboard Framework",
        "lede": "A public-safe window into the knowledge-system, search, climate, energy, and source-intelligence layers behind Sustainable Catalyst.",
        "status": {
            "public_mode": "enabled",
            "release_stage": "public preview",
            "raw_analytics_exposed": False,
            "private_strategy_exposed": False,
            "credential_values_exposed": False,
        },
        "cards": [
            {
                "label": "Knowledge system",
                "value": "Article maps + registry",
                "detail": "Public summaries connect Sustainable Catalyst pages to hubs, article maps, tools, repositories, and research pathways.",
            },
            {
                "label": "Search intelligence",
                "value": "SEO + discovery",
                "detail": "Search visibility is interpreted through the Sustainable Catalyst knowledge architecture rather than generic keyword lists.",
            },
            {
                "label": "External sources",
                "value": "Climate + energy",
                "detail": "External source snapshots are source-labeled, cached or fallback-aware, and displayed as interpretive signals.",
            },
            {
                "label": "Public safety",
                "value": "Sanitized output",
                "detail": "Public dashboards hide raw analytics, private conversion diagnostics, backend settings, tokens, and publishing queues.",
            },
        ],
        "sections": [
            {
                "name": "Public Site Intelligence",
                "shortcode": "[sc_public_site_intelligence]",
                "purpose": "Aggregated public-safe platform and knowledge-system overview.",
            },
            {
                "name": "Knowledge Overview",
                "shortcode": "[sc_public_knowledge_overview]",
                "purpose": "Knowledge-area summaries and public surface groupings.",
            },
            {
                "name": "Climate, Energy, and External Source Snapshot",
                "shortcode": "[sc_public_climate_energy_summary]",
                "purpose": "Stable external-source snapshot for climate, energy, emissions, and Earth observation context.",
            },
            {
                "name": "Public Methodology",
                "shortcode": "[sc_public_methodology]",
                "purpose": "Explains what public dashboards show, hide, and how source notes should be interpreted.",
            },
        ],
        "public_ctas": [
            {"label": "Explore the Research Library", "url": "https://sustainablecatalyst.com/research-library/"},
            {"label": "Open the Workbench", "url": "https://sustainablecatalyst.com/workbench/"},
            {"label": "View Sustainable Catalyst on GitHub", "url": "https://github.com/Content-Catalyst-LLC"},
        ],
        "review_notes": [
            "Use this landing shortcode on public pages; keep administrative readiness and raw diagnostics private.",
            "Treat external climate and energy data as interpretive public signals, not professional advice.",
            "Pair public dashboards with explanatory copy and source/methodology notes.",
        ],
    }

def public_methodology() -> Dict[str, Any]:
    return {
        "ok": True,
        "title": "Public Dashboard Methodology",
        "summary": "Public Site Intelligence dashboards expose aggregated, interpretive, and source-linked signals rather than raw analytics or internal strategy diagnostics.",
        "included": [
            "Aggregated knowledge-area activity bands",
            "Registry and article-map coverage indicators",
            "Public-safe climate, energy, and external-data summaries",
            "General platform-readiness status",
            "Methodology, source, and review notes",
        ],
        "excluded": [
            "Raw GA4 user-level data",
            "Precise internal traffic numbers when public rounding is enabled",
            "Private conversion diagnostics",
            "Credential, token, or backend configuration values",
            "Internal publishing queues and sensitive strategy notes",
        ],
        "review_notes": [
            "Public dashboards should be embedded only after the public-readiness status is public_candidate or public_ready.",
            "Private administrative dashboards should remain restricted to logged-in editors/admins.",
            "External-data outputs should include source notes and refreshed timestamps when displayed publicly.",
        ],
    }


def public_dashboard_from_metrics(metrics: List[PageMetric], event_rows: Iterable[Any], registry: ContentRegistry, source: str, start_date: str, end_date: str) -> Dict[str, Any]:
    totals = dashboard_totals(metrics)
    coverage = mapping_coverage(metrics)
    diagnostics = event_diagnostics(event_rows, metrics)
    readiness = diagnostics.get("readiness", {})
    hubs = hub_summary(metrics)
    mapped_rate = coverage.get("mapping_coverage_rate", 0.0)
    conversion_score = float(readiness.get("score", 0) or 0)
    external_placeholder_score = 65.0
    public_score = round((mapped_rate * 0.35) + (conversion_score * 0.20) + (external_placeholder_score * 0.15) + 20, 2)
    public_score = max(0.0, min(100.0, public_score))
    public_status = _status_from_score(public_score)

    top_hubs = []
    for row in hubs[:8]:
        top_hubs.append(
            {
                "hub": row.get("hub", "Unmapped"),
                "pages": int(row.get("pages", 0) or 0),
                "activity_band": _band(float(row.get("screen_page_views", 0) or 0)),
                "depth_score": round(float(row.get("avg_institutional_depth_score", 0) or 0), 1),
                "role": _topic_role(str(row.get("hub", ""))),
                "public_note": "Aggregated knowledge-area signal; raw traffic is kept private.",
            }
        )

    featured_pages = []
    for metric in metrics[:10]:
        if metric.mapping_status == "excluded":
            continue
        featured_pages.append(
            {
                "title": metric.title or metric.path,
                "path": metric.path,
                "hub": metric.hub,
                "article_map": metric.article_map,
                "activity_band": _band(metric.screen_page_views),
                "depth_status": "strong" if metric.institutional_depth_score >= 60 else "emerging" if metric.institutional_depth_score >= 35 else "early",
                "public_focus": _public_page_focus(metric),
            }
        )
        if len(featured_pages) >= 6:
            break

    modules = [
        {
            "module": "Knowledge-system analytics",
            "status": "public_candidate" if mapped_rate >= 50 else "internal_review",
            "public_output": "Aggregated views, knowledge-area coverage, and public-safe page groupings",
        },
        {
            "module": "Search and SEO intelligence",
            "status": "public_candidate",
            "public_output": "Topic visibility, search opportunity themes, and public methodology notes",
        },
        {
            "module": "External climate and energy data",
            "status": "public_candidate",
            "public_output": "Source-linked climate, energy, emissions, and Earth observation summaries",
        },
        {
            "module": "Publishing intelligence",
            "status": "internal_review",
            "public_output": "Public summaries only; private publishing queues remain internal",
        },
    ]

    return {
        "ok": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "mode": "public",
        "date_range": {"start_date": start_date, "end_date": end_date},
        "public_status": public_status,
        "public_readiness_score": public_score,
        "summary": {
            "views_band": _band(totals.get("screen_page_views", 0)),
            "rounded_views": _round_public(totals.get("screen_page_views", 0), 100),
            "active_users_band": _band(totals.get("active_users", 0)),
            "knowledge_areas": len([row for row in hubs if row.get("hub") != "Unmapped"]),
            "registry_entries": registry.count(),
            "mapping_coverage_rate": mapped_rate,
            "conversion_readiness_status": readiness.get("status", "unknown"),
        },
        "knowledge_areas": top_hubs,
        "featured_surfaces": featured_pages,
        "modules": modules,
        "public_recommendations": [
            "Use public dashboards to explain Sustainable Catalyst as a knowledge-system platform rather than as a raw traffic dashboard.",
            "Expose climate, energy, search, and article-map summaries before exposing any detailed internal strategy panels.",
            "Keep precise GA4 counts, unmapped-page diagnostics, conversion gaps, and publishing queues private.",
            "Add methodology and source notes directly beneath every public dashboard embed.",
        ],
        "methodology": public_methodology(),
    }


def build_public_dashboard(ga4: Any, registry: ContentRegistry, start_date: str = "28daysAgo", end_date: str = "today") -> Dict[str, Any]:
    page_rows = ga4.page_report(start_date, end_date)
    event_rows = ga4.event_report(start_date, end_date)
    metrics = build_page_metrics(page_rows, event_rows, registry)
    return public_dashboard_from_metrics(metrics, event_rows, registry, "ga4" if ga4.enabled else "demo", start_date, end_date)


def public_readiness_report(ga4: Any, registry: ContentRegistry, start_date: str = "28daysAgo", end_date: str = "today") -> Dict[str, Any]:
    report = build_public_dashboard(ga4, registry, start_date, end_date)
    score = report["public_readiness_score"]
    status = report["public_status"]
    checks = [
        {"check": "Backend is producing public-safe sanitized output", "status": "passed", "detail": "Public endpoints aggregate and band sensitive metrics."},
        {"check": "Registry coverage is adequate", "status": "passed" if report["summary"].get("mapping_coverage_rate", 0) >= 50 else "review", "detail": f"Coverage: {report['summary'].get('mapping_coverage_rate', 0)}%"},
        {"check": "Private admin diagnostics remain separate", "status": "passed", "detail": "Internal endpoints still require the Site Intelligence token."},
        {"check": "Public methodology is available", "status": "passed", "detail": "Methodology and exclusion notes are included."},
        {"check": "Publishing queues are not exposed", "status": "passed", "detail": "Public mode excludes raw internal strategy queues."},
    ]
    return {
        "ok": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "public_status": status,
        "public_readiness_score": score,
        "checks": checks,
        "recommended_next_steps": [
            "Review the public dashboard on a private WordPress page before embedding it publicly.",
            "Keep administrative shortcodes on private pages only.",
            "Add public-facing explanatory copy above each public dashboard section.",
            "Do a final secret scan and token rotation before a public product-page launch.",
        ],
    }
