from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List

from .models import GA4ReportRow, PageMetric, RegistrySuggestion
from .registry import ContentRegistry


REPOSITORY_EVENTS = {"sc_repository_click", "github_click", "repository_click"}
WORKBENCH_EVENTS = {"sc_workbench_open", "workbench_open", "tool_open", "calculator_open"}
RESEARCH_LIBRARIAN_EVENTS = {"sc_research_librarian_open", "research_librarian_open", "ai_librarian_query"}
PATHWAY_EVENTS = {"sc_pathway_continue", "pathway_continue", "article_map_nav", "sc_library_nav"}
DECISION_STUDIO_EVENTS = {"sc_decision_studio_open", "decision_studio_open"}


def safe_div(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def normalize_score(value: float, ceiling: float) -> float:
    if ceiling <= 0:
        return 0.0
    return round(max(0.0, min(100.0, (value / ceiling) * 100.0)), 2)


def event_counts_by_path(event_rows: Iterable[GA4ReportRow]) -> Dict[str, Dict[str, float]]:
    counts: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for row in event_rows:
        path = row.dimensions.get("pagePath") or row.dimensions.get("unifiedPagePathScreen") or "/"
        event_name = row.dimensions.get("eventName", "")
        count = row.metrics.get("eventCount", 0.0)
        if event_name in REPOSITORY_EVENTS:
            counts[path]["repository_clicks"] += count
        if event_name in WORKBENCH_EVENTS:
            counts[path]["workbench_events"] += count
        if event_name in RESEARCH_LIBRARIAN_EVENTS:
            counts[path]["research_librarian_events"] += count
        if event_name in PATHWAY_EVENTS:
            counts[path]["pathway_events"] += count
        if event_name in DECISION_STUDIO_EVENTS:
            counts[path]["decision_studio_events"] += count
    return counts


def page_metric_from_rows(
    page_row: GA4ReportRow,
    event_counts: Dict[str, Dict[str, float]],
    registry: ContentRegistry,
) -> PageMetric:
    path = page_row.dimensions.get("pagePath") or page_row.dimensions.get("unifiedPagePathScreen") or "/"
    title = page_row.dimensions.get("pageTitle", "")
    match = registry.resolve(path, title)
    item = match.item
    metric = PageMetric(
        path=path,
        title=title or (item.title if item else ""),
        hub=item.hub if item else "Unmapped",
        article_map=item.article_map if item else None,
        discipline=item.discipline if item else None,
        content_type=item.content_type if item else "unknown",
        mapping_status=match.status,
        mapping_confidence=match.confidence,
        mapping_reason=match.reason,
        screen_page_views=page_row.metrics.get("screenPageViews", 0.0),
        active_users=page_row.metrics.get("activeUsers", 0.0),
        event_count=page_row.metrics.get("eventCount", 0.0),
        engagement_rate=page_row.metrics.get("engagementRate", 0.0),
        average_session_duration=page_row.metrics.get("averageSessionDuration", 0.0),
    )
    e = event_counts.get(path, {})
    metric.repository_clicks = e.get("repository_clicks", 0.0)
    metric.workbench_events = e.get("workbench_events", 0.0)
    metric.research_librarian_events = e.get("research_librarian_events", 0.0)
    metric.pathway_events = e.get("pathway_events", 0.0)
    metric.decision_studio_events = e.get("decision_studio_events", 0.0)
    metric.institutional_depth_score = institutional_depth_score(metric)
    metric.authority_surface_score = authority_surface_score(metric, has_repository=bool(item and item.repository_url))
    metric.hub_efficiency_score = hub_efficiency_score(metric)
    metric.recommendations = page_recommendations(
        metric,
        has_repository=bool(item and item.repository_url),
        has_tool=bool(item and item.workbench_tool_ids),
    )
    return metric


def institutional_depth_score(metric: PageMetric) -> float:
    engagement_component = metric.engagement_rate * 35.0
    duration_component = normalize_score(metric.average_session_duration, 240.0) * 0.25
    pathway_component = min(20.0, safe_div(metric.pathway_events, max(metric.active_users, 1.0)) * 100.0)
    tool_component = min(20.0, safe_div(metric.workbench_events + metric.research_librarian_events + metric.decision_studio_events, max(metric.active_users, 1.0)) * 100.0)
    mapping_component = 0.0
    if metric.mapping_status == "explicit":
        mapping_component = 4.0
    elif metric.mapping_status == "inferred":
        mapping_component = 2.0
    return round(min(100.0, engagement_component + duration_component + pathway_component + tool_component + mapping_component), 2)


def authority_surface_score(metric: PageMetric, has_repository: bool) -> float:
    traffic_component = normalize_score(metric.screen_page_views, 1000.0) * 0.25
    engagement_component = metric.engagement_rate * 25.0
    repository_component = min(25.0, safe_div(metric.repository_clicks, max(metric.active_users, 1.0)) * 100.0)
    structure_component = 15.0 if metric.article_map else 0.0
    repo_presence_component = 10.0 if has_repository else 0.0
    mapping_component = 5.0 if metric.mapping_status == "explicit" else 2.5 if metric.mapping_status == "inferred" else 0.0
    return round(min(100.0, traffic_component + engagement_component + repository_component + structure_component + repo_presence_component + mapping_component), 2)


def hub_efficiency_score(metric: PageMetric) -> float:
    continuation_rate = safe_div(metric.pathway_events, max(metric.active_users, 1.0))
    event_density = safe_div(metric.event_count, max(metric.screen_page_views, 1.0))
    return round(min(100.0, continuation_rate * 55.0 + event_density * 10.0 + metric.engagement_rate * 35.0), 2)


def page_recommendations(metric: PageMetric, has_repository: bool, has_tool: bool) -> List[str]:
    recommendations: List[str] = []
    if metric.mapping_status == "unmapped":
        recommendations.append("Add this page to the Sustainable Catalyst registry so custom metrics can classify it accurately.")
    elif metric.mapping_status == "inferred":
        recommendations.append("Confirm this inferred registry mapping and promote it to an explicit registry entry.")
    if metric.screen_page_views >= 250 and metric.pathway_events < max(10, metric.active_users * 0.10):
        recommendations.append("Strengthen article-map navigation and next-step links on this page.")
    if metric.engagement_rate >= 0.55 and has_repository and metric.repository_clicks < max(5, metric.active_users * 0.08):
        recommendations.append("Make the GitHub repository CTA more visible or contextual.")
    if metric.engagement_rate >= 0.55 and has_tool and metric.workbench_events < max(5, metric.active_users * 0.06):
        recommendations.append("Add a stronger Workbench prompt near the section where readers slow down.")
    if metric.average_session_duration < 70 and metric.screen_page_views >= 200:
        recommendations.append("Review the opening section and table of contents for faster reader orientation.")
    if not recommendations:
        recommendations.append("Maintain current structure; monitor trend and compare against related pages.")
    return recommendations[:4]


def build_page_metrics(
    page_rows: Iterable[GA4ReportRow],
    event_rows: Iterable[GA4ReportRow],
    registry: ContentRegistry,
) -> List[PageMetric]:
    counts = event_counts_by_path(event_rows)
    metrics = [page_metric_from_rows(row, counts, registry) for row in page_rows]
    return sorted(metrics, key=lambda item: item.institutional_depth_score, reverse=True)


def mapping_coverage(metrics: Iterable[PageMetric]) -> Dict[str, float]:
    items = list(metrics)
    total = len(items)
    explicit = sum(1 for item in items if item.mapping_status == "explicit")
    inferred = sum(1 for item in items if item.mapping_status == "inferred")
    unmapped = sum(1 for item in items if item.mapping_status == "unmapped")
    excluded = sum(1 for item in items if item.mapping_status == "excluded")
    return {
        "total_pages": total,
        "explicit_pages": explicit,
        "inferred_pages": inferred,
        "unmapped_pages": unmapped,
        "excluded_pages": excluded,
        "mapped_pages": explicit + inferred,
        "mapping_coverage_rate": round(safe_div(explicit + inferred, max(total - excluded, 1)) * 100.0, 2),
        "explicit_coverage_rate": round(safe_div(explicit, max(total - excluded, 1)) * 100.0, 2),
    }


def unmapped_suggestions(metrics: Iterable[PageMetric], registry: ContentRegistry, limit: int = 20) -> List[RegistrySuggestion]:
    candidates = [item for item in metrics if item.mapping_status in {"unmapped", "inferred"}]
    candidates = sorted(candidates, key=lambda item: (item.mapping_status == "unmapped", item.screen_page_views), reverse=True)
    return [registry.suggestion_for_metric(item) for item in candidates[:limit]]


def dashboard_totals(metrics: Iterable[PageMetric]) -> Dict[str, float]:
    items = list(metrics)
    totals = {
        "screen_page_views": sum(item.screen_page_views for item in items),
        "active_users": sum(item.active_users for item in items),
        "event_count": sum(item.event_count for item in items),
        "repository_clicks": sum(item.repository_clicks for item in items),
        "workbench_events": sum(item.workbench_events for item in items),
        "research_librarian_events": sum(item.research_librarian_events for item in items),
        "pathway_events": sum(item.pathway_events for item in items),
        "decision_studio_events": sum(item.decision_studio_events for item in items),
    }
    totals["avg_institutional_depth_score"] = round(
        safe_div(sum(item.institutional_depth_score for item in items), len(items)), 2
    )
    totals["avg_authority_surface_score"] = round(
        safe_div(sum(item.authority_surface_score for item in items), len(items)), 2
    )
    totals.update(mapping_coverage(items))
    return totals


def hub_summary(metrics: Iterable[PageMetric]) -> List[Dict[str, float | str]]:
    grouped: Dict[str, List[PageMetric]] = defaultdict(list)
    for metric in metrics:
        if metric.mapping_status == "excluded":
            continue
        grouped[metric.hub].append(metric)
    summary = []
    for hub, items in grouped.items():
        summary.append(
            {
                "hub": hub,
                "pages": len(items),
                "screen_page_views": sum(item.screen_page_views for item in items),
                "active_users": sum(item.active_users for item in items),
                "avg_institutional_depth_score": round(safe_div(sum(item.institutional_depth_score for item in items), len(items)), 2),
                "repository_clicks": sum(item.repository_clicks for item in items),
                "workbench_events": sum(item.workbench_events for item in items),
                "pathway_events": sum(item.pathway_events for item in items),
        "decision_studio_events": sum(item.decision_studio_events for item in items),
                "inferred_pages": sum(1 for item in items if item.mapping_status == "inferred"),
                "unmapped_pages": sum(1 for item in items if item.mapping_status == "unmapped"),
            }
        )
    return sorted(summary, key=lambda row: row["avg_institutional_depth_score"], reverse=True)
