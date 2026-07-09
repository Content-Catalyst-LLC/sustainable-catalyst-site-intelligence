from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, Iterable, List, Tuple

from .metrics import (
    PATHWAY_EVENTS,
    REPOSITORY_EVENTS,
    RESEARCH_LIBRARIAN_EVENTS,
    WORKBENCH_EVENTS,
    safe_div,
)
from .models import GA4ReportRow, PageMetric

DECISION_STUDIO_EVENTS = {"sc_decision_studio_open", "decision_studio_open"}
SCROLL_DEPTH_EVENTS = {"sc_scroll_depth", "scroll_depth"}
LIBRARY_NAV_EVENTS = {"sc_library_nav", "library_nav", "research_library_nav"}

EVENT_CATALOG: List[Dict[str, Any]] = [
    {
        "event_name": "sc_repository_click",
        "label": "Repository CTA tracking",
        "category": "repository",
        "priority": "high",
        "aliases": sorted(REPOSITORY_EVENTS),
        "why_it_matters": "Measures whether readers move from articles into GitHub repositories and applied artifacts.",
    },
    {
        "event_name": "sc_workbench_open",
        "label": "Workbench activation tracking",
        "category": "workbench",
        "priority": "high",
        "aliases": sorted(WORKBENCH_EVENTS),
        "why_it_matters": "Measures whether readers move from content into calculators, models, and applied tools.",
    },
    {
        "event_name": "sc_research_librarian_open",
        "label": "Research Librarian tracking",
        "category": "research_librarian",
        "priority": "high",
        "aliases": sorted(RESEARCH_LIBRARIAN_EVENTS),
        "why_it_matters": "Measures whether readers use the guided inquiry assistant from article maps and long pages.",
    },
    {
        "event_name": "sc_decision_studio_open",
        "label": "Decision Studio tracking",
        "category": "decision_studio",
        "priority": "medium",
        "aliases": sorted(DECISION_STUDIO_EVENTS),
        "why_it_matters": "Measures whether visitors move from research material into applied decision-brief workflows.",
    },
    {
        "event_name": "sc_pathway_continue",
        "label": "Article pathway tracking",
        "category": "pathway",
        "priority": "high",
        "aliases": sorted(PATHWAY_EVENTS),
        "why_it_matters": "Measures whether hub and article-map pages are creating deeper knowledge-system journeys.",
    },
    {
        "event_name": "sc_library_nav",
        "label": "Library navigation tracking",
        "category": "library_navigation",
        "priority": "medium",
        "aliases": sorted(LIBRARY_NAV_EVENTS),
        "why_it_matters": "Measures movement into the Research Library and related navigation surfaces.",
    },
    {
        "event_name": "sc_scroll_depth",
        "label": "Scroll-depth tracking",
        "category": "engagement_depth",
        "priority": "medium",
        "aliases": sorted(SCROLL_DEPTH_EVENTS),
        "why_it_matters": "Measures whether readers reach deeper sections of long Sustainable Catalyst pages.",
    },
]


def _event_name(row: GA4ReportRow) -> str:
    return row.dimensions.get("eventName", "")


def _event_path(row: GA4ReportRow) -> str:
    return row.dimensions.get("pagePath") or row.dimensions.get("unifiedPagePathScreen") or "/"


def _event_count(row: GA4ReportRow) -> float:
    return row.metrics.get("eventCount", 0.0)


def event_totals(event_rows: Iterable[GA4ReportRow]) -> Dict[str, float]:
    totals: Dict[str, float] = defaultdict(float)
    for row in event_rows:
        totals[_event_name(row)] += _event_count(row)
    return dict(sorted(totals.items(), key=lambda item: item[1], reverse=True))


def event_totals_by_path(event_rows: Iterable[GA4ReportRow]) -> Dict[Tuple[str, str], float]:
    totals: Dict[Tuple[str, str], float] = defaultdict(float)
    for row in event_rows:
        totals[(_event_path(row), _event_name(row))] += _event_count(row)
    return totals


def event_diagnostics(event_rows: Iterable[GA4ReportRow], page_metrics: Iterable[PageMetric]) -> Dict[str, Any]:
    rows = list(event_rows)
    metrics = list(page_metrics)
    totals = event_totals(rows)
    tracked_total = 0.0
    definitions = []
    active_high_priority = 0
    high_priority_total = 0
    active_all = 0

    for definition in EVENT_CATALOG:
        aliases = set(definition["aliases"])
        count = sum(count for event, count in totals.items() if event in aliases)
        tracked_total += count
        active = count > 0
        if active:
            active_all += 1
        if definition["priority"] == "high":
            high_priority_total += 1
            if active:
                active_high_priority += 1
        status = "active" if active else "missing"
        if active and count < 5:
            status = "low_volume"
        definitions.append({
            **definition,
            "event_count": count,
            "status": status,
            "ga4_visible": active,
            "matched_event_names": sorted([event for event in totals.keys() if event in aliases]),
            "next_action": _next_action(definition["category"], status),
        })

    unknown_sc_events = sorted([
        {"event_name": event, "event_count": count}
        for event, count in totals.items()
        if event.startswith("sc_") and not any(event in set(d["aliases"]) for d in EVENT_CATALOG)
    ], key=lambda item: item["event_count"], reverse=True)

    readiness = conversion_readiness(definitions, metrics)
    return {
        "event_catalog_version": "0.3.1",
        "tracked_event_total": tracked_total,
        "visible_ga4_event_names": len(totals),
        "tracked_events_active": active_all,
        "tracked_events_total": len(EVENT_CATALOG),
        "high_priority_active": active_high_priority,
        "high_priority_total": high_priority_total,
        "readiness": readiness,
        "events": definitions,
        "top_ga4_events": [{"event_name": event, "event_count": count} for event, count in list(totals.items())[:25]],
        "unknown_sc_events": unknown_sc_events[:20],
    }


def conversion_readiness(definitions: List[Dict[str, Any]], metrics: Iterable[PageMetric]) -> Dict[str, Any]:
    score = 0.0
    checks = []
    weights = {
        "repository": 18,
        "workbench": 18,
        "research_librarian": 16,
        "decision_studio": 10,
        "pathway": 18,
        "library_navigation": 10,
        "engagement_depth": 10,
    }
    for definition in definitions:
        weight = weights.get(definition["category"], 10)
        active = definition["status"] in {"active", "low_volume"}
        earned = weight if active else 0
        if definition["status"] == "low_volume":
            earned = weight * 0.65
        score += earned
        checks.append({
            "label": definition["label"],
            "category": definition["category"],
            "status": definition["status"],
            "weight": weight,
            "earned": round(earned, 2),
            "event_count": definition["event_count"],
        })

    total_views = sum(item.screen_page_views for item in metrics)
    total_users = sum(item.active_users for item in metrics)
    total_conversion_events = sum(
        item.repository_clicks + item.workbench_events + item.research_librarian_events + item.pathway_events
        for item in metrics
    )
    return {
        "score": round(min(100.0, score), 2),
        "status": "ready" if score >= 80 else "partial" if score >= 45 else "not_ready",
        "checks": checks,
        "total_views": total_views,
        "total_active_users": total_users,
        "total_conversion_events": total_conversion_events,
        "conversion_event_rate_per_active_user": round(safe_div(total_conversion_events, max(total_users, 1.0)) * 100.0, 2),
    }


def page_opportunities(metrics: Iterable[PageMetric], limit: int = 20) -> List[Dict[str, Any]]:
    opportunities: List[Dict[str, Any]] = []
    for page in metrics:
        if page.mapping_status == "excluded":
            continue
        user_base = max(page.active_users, 1.0)
        repository_rate = safe_div(page.repository_clicks, user_base)
        workbench_rate = safe_div(page.workbench_events, user_base)
        research_rate = safe_div(page.research_librarian_events, user_base)
        pathway_rate = safe_div(page.pathway_events, user_base)
        actions = []
        severity = 0
        if page.screen_page_views >= 200 and page.repository_clicks == 0 and page.authority_surface_score >= 20:
            actions.append("Validate GitHub CTA tracking and add a contextual repository link if one exists.")
            severity += 3
        elif page.screen_page_views >= 200 and repository_rate < 0.03:
            actions.append("Improve repository CTA placement or copy; current click rate is low for the traffic level.")
            severity += 2
        if page.screen_page_views >= 200 and page.workbench_events == 0 and (page.hub in {"Research", "Platform"} or page.discipline in {"Mathematics", "Economics", "Environmental Science", "Energy"}):
            actions.append("Add or validate Workbench entry points from this page.")
            severity += 3
        elif workbench_rate < 0.02 and page.screen_page_views >= 300:
            actions.append("Add a short inline Workbench prompt near applied examples.")
            severity += 1
        if page.average_session_duration >= 90 and page.research_librarian_events == 0:
            actions.append("Cross-link Research Librarian AI as a guided inquiry assistant for this long/high-engagement page.")
            severity += 2
        if page.screen_page_views >= 250 and pathway_rate < 0.06:
            actions.append("Strengthen article-map continuation links and related-pathway cards.")
            severity += 2
        if page.mapping_status != "explicit":
            actions.append("Confirm this page in the registry so conversion recommendations can use the right article map and tool relationships.")
            severity += 1
        if actions:
            opportunities.append({
                "path": page.path,
                "title": page.title,
                "hub": page.hub,
                "article_map": page.article_map,
                "mapping_status": page.mapping_status,
                "views": page.screen_page_views,
                "active_users": page.active_users,
                "repository_clicks": page.repository_clicks,
                "workbench_events": page.workbench_events,
                "research_librarian_events": page.research_librarian_events,
                "pathway_events": page.pathway_events,
                "repository_rate": round(repository_rate * 100.0, 2),
                "workbench_rate": round(workbench_rate * 100.0, 2),
                "research_librarian_rate": round(research_rate * 100.0, 2),
                "pathway_rate": round(pathway_rate * 100.0, 2),
                "priority_score": round(severity * 10 + min(page.screen_page_views / 100.0, 20), 2),
                "actions": actions[:5],
            })
    return sorted(opportunities, key=lambda item: item["priority_score"], reverse=True)[:limit]


def event_setup_recommendations(diagnostics: Dict[str, Any]) -> List[str]:
    recs: List[str] = []
    missing = [item for item in diagnostics.get("events", []) if item.get("status") == "missing"]
    if missing:
        labels = ", ".join(item["event_name"] for item in missing[:4])
        recs.append(f"Create or verify GA4/GTM event tags for missing Sustainable Catalyst events: {labels}.")
    if diagnostics.get("readiness", {}).get("score", 0) < 80:
        recs.append("Treat conversion reporting as partial until high-priority events are visible in GA4.")
    if diagnostics.get("tracked_event_total", 0) == 0:
        recs.append("Confirm the WordPress event bridge is enabled and that GTM custom-event triggers are publishing to GA4.")
    unknown = diagnostics.get("unknown_sc_events", [])
    if unknown:
        recs.append("Review unknown sc_* events and add aliases where they represent real Sustainable Catalyst interactions.")
    if not recs:
        recs.append("Event tracking is active; monitor conversion rates by article map and improve prompts on high-traffic pages.")
    return recs


def _next_action(category: str, status: str) -> str:
    if status == "active":
        return "Monitor volume and compare conversion rates across high-traffic pages."
    if status == "low_volume":
        return "Verify that the event fires on the expected pages and improve CTA visibility where appropriate."
    actions = {
        "repository": "Create a GTM custom-event trigger for sc_repository_click and verify GitHub links are detected.",
        "workbench": "Create a GTM custom-event trigger for sc_workbench_open and validate Workbench link/shortcode clicks.",
        "research_librarian": "Create a GTM custom-event trigger for sc_research_librarian_open and add visible Research Librarian links from long articles.",
        "decision_studio": "Create a GTM custom-event trigger for sc_decision_studio_open and validate Decision Studio entry links.",
        "pathway": "Create a GTM custom-event trigger for sc_pathway_continue and validate article-map/related-link navigation.",
        "library_navigation": "Create a GTM custom-event trigger for sc_library_nav and validate Research Library navigation links.",
        "engagement_depth": "Create a GTM custom-event trigger for sc_scroll_depth and confirm scroll-depth parameters are sent to GA4.",
    }
    return actions.get(category, "Create or verify the matching GTM custom-event trigger.")
