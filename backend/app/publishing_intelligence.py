from __future__ import annotations

import math
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Tuple

from .ga4_client import GA4Client
from .metrics import build_page_metrics, dashboard_totals, hub_summary, safe_div
from .registry import ContentRegistry
from .search_console import SearchConsoleClient
from .seo_intelligence import seo_recommendations


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _norm(path: str) -> str:
    return ContentRegistry._norm(path or "/")


def _metric_map(metrics: Iterable[Any]) -> Dict[str, Any]:
    return {_norm(item.path): item for item in metrics}


def _search_page_map(pages: Iterable[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {_norm(item.get("page", "/")): item for item in pages}


def _series_key(hub: str | None, article_map: str | None) -> str:
    if article_map:
        return article_map
    if hub:
        return hub
    return "Unmapped"


def _growth_rate(current: float, prior: float) -> float:
    if prior <= 0 and current > 0:
        return 100.0
    if prior <= 0:
        return 0.0
    return round(((current - prior) / prior) * 100.0, 2)


def _log_component(value: float, scale: float = 12.0, cap: float = 40.0) -> float:
    return min(cap, math.log10(max(1.0, value)) * scale)


def _page_strategy_score(current_metric: Any, prior_metric: Any | None, search_item: Dict[str, Any] | None) -> float:
    views = float(getattr(current_metric, "screen_page_views", 0) or 0)
    users = float(getattr(current_metric, "active_users", 0) or 0)
    depth = float(getattr(current_metric, "institutional_depth_score", 0) or 0)
    authority = float(getattr(current_metric, "authority_surface_score", 0) or 0)
    prior_views = float(getattr(prior_metric, "screen_page_views", 0) or 0) if prior_metric else 0.0
    search_impressions = float((search_item or {}).get("impressions", 0) or 0)
    search_ctr = float((search_item or {}).get("ctr", 0) or 0)  # percent
    search_position = float((search_item or {}).get("position", 0) or 0)
    growth = _growth_rate(views, prior_views)

    score = 0.0
    score += _log_component(views + users, scale=10, cap=30)
    score += min(20.0, depth / 5.0)
    score += min(15.0, authority / 6.0)
    score += _log_component(search_impressions, scale=8, cap=20)
    if search_impressions >= 250 and search_ctr < 4:
        score += 8
    if 6 <= search_position <= 20:
        score += 8
    if growth >= 25:
        score += 6
    elif growth <= -35 and prior_views >= 100:
        score += 7
    return round(min(100.0, score), 2)


def _page_actions(metric: Any, prior_metric: Any | None, search_item: Dict[str, Any] | None) -> List[str]:
    actions: List[str] = []
    views = float(getattr(metric, "screen_page_views", 0) or 0)
    prior_views = float(getattr(prior_metric, "screen_page_views", 0) or 0) if prior_metric else 0.0
    growth = _growth_rate(views, prior_views)
    impressions = float((search_item or {}).get("impressions", 0) or 0)
    ctr = float((search_item or {}).get("ctr", 0) or 0)
    position = float((search_item or {}).get("position", 0) or 0)
    repo_clicks = float(getattr(metric, "repository_clicks", 0) or 0)
    workbench_events = float(getattr(metric, "workbench_events", 0) or 0)
    librarian_events = float(getattr(metric, "research_librarian_events", 0) or 0)
    pathway_events = float(getattr(metric, "pathway_events", 0) or 0)
    users = max(1.0, float(getattr(metric, "active_users", 0) or 0))
    mapping_status = getattr(metric, "mapping_status", "unmapped")

    if growth <= -35 and prior_views >= 100:
        actions.append("Refresh this page; traffic has declined materially against the prior comparison window.")
    if growth >= 35 and views >= 100:
        actions.append("Promote this rising page through LinkedIn, Substack, and related article-map navigation.")
    if impressions >= 250 and ctr < 4:
        actions.append("Review SEO title and meta description; search visibility is meaningful but CTR is weak.")
    if 6 <= position <= 20:
        actions.append("Add internal links from related hubs and article maps; this page is within striking distance in search.")
    if repo_clicks < users * 0.04 and getattr(metric, "authority_surface_score", 0) >= 35:
        actions.append("Add or strengthen contextual GitHub CTA placement near applied examples and repositories.")
    if workbench_events < users * 0.04 and (getattr(metric, "content_type", "") in {"article", "article_map", "hub"}):
        actions.append("Add a Workbench prompt if the page contains applied modeling, calculators, or technical examples.")
    if librarian_events < users * 0.03 and views >= 150:
        actions.append("Cross-link Research Librarian as a guided inquiry assistant for deeper reading.")
    if pathway_events < users * 0.08 and views >= 150:
        actions.append("Strengthen next-step pathways to adjacent articles, maps, tools, and repositories.")
    if mapping_status in {"unmapped", "inferred"}:
        actions.append("Confirm the registry mapping so publishing intelligence can classify this page accurately.")
    if not actions:
        actions.append("Monitor this page; current signals do not require immediate intervention.")
    return actions[:5]


def page_strategy_rows(
    current_metrics: Iterable[Any],
    prior_metrics: Iterable[Any],
    current_search_pages: Iterable[Dict[str, Any]],
    prior_search_pages: Iterable[Dict[str, Any]],
    limit: int = 25,
) -> List[Dict[str, Any]]:
    prior_by_path = _metric_map(prior_metrics)
    search_by_path = _search_page_map(current_search_pages)
    prior_search_by_path = _search_page_map(prior_search_pages)
    rows: List[Dict[str, Any]] = []
    for metric in current_metrics:
        path = _norm(metric.path)
        prior_metric = prior_by_path.get(path)
        search_item = search_by_path.get(path, {})
        prior_search = prior_search_by_path.get(path, {})
        current_views = float(metric.screen_page_views or 0)
        prior_views = float(getattr(prior_metric, "screen_page_views", 0) or 0) if prior_metric else 0.0
        current_impressions = float(search_item.get("impressions", 0) or 0)
        prior_impressions = float(prior_search.get("impressions", 0) or 0)
        score = _page_strategy_score(metric, prior_metric, search_item)
        status = "maintain"
        if current_views >= 150 and _growth_rate(current_views, prior_views) >= 35:
            status = "rising"
        if prior_views >= 100 and _growth_rate(current_views, prior_views) <= -35:
            status = "decay"
        if current_impressions >= 250 and float(search_item.get("ctr", 0) or 0) < 4:
            status = "search_opportunity"
        if metric.mapping_status in {"unmapped", "inferred"}:
            status = "mapping_review"
        rows.append({
            "path": path,
            "title": metric.title or path,
            "hub": metric.hub,
            "article_map": metric.article_map,
            "discipline": metric.discipline,
            "content_type": metric.content_type,
            "mapping_status": metric.mapping_status,
            "status": status,
            "strategy_score": score,
            "current_views": round(current_views, 2),
            "prior_views": round(prior_views, 2),
            "views_growth_rate": _growth_rate(current_views, prior_views),
            "active_users": round(float(metric.active_users or 0), 2),
            "depth_score": metric.institutional_depth_score,
            "authority_score": metric.authority_surface_score,
            "repository_clicks": metric.repository_clicks,
            "workbench_events": metric.workbench_events,
            "research_librarian_events": metric.research_librarian_events,
            "pathway_events": metric.pathway_events,
            "search_impressions": round(current_impressions, 2),
            "prior_search_impressions": round(prior_impressions, 2),
            "search_impression_growth_rate": _growth_rate(current_impressions, prior_impressions),
            "search_ctr": search_item.get("ctr", 0),
            "search_position": search_item.get("position", 0),
            "top_queries": search_item.get("top_queries", [])[:5],
            "actions": _page_actions(metric, prior_metric, search_item),
        })
    return sorted(rows, key=lambda row: row["strategy_score"], reverse=True)[:limit]


def article_map_performance(rows: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        key = _series_key(row.get("hub"), row.get("article_map"))
        if key not in grouped:
            grouped[key] = {
                "name": key,
                "hub": row.get("hub") or "Unmapped",
                "pages": 0,
                "current_views": 0.0,
                "prior_views": 0.0,
                "search_impressions": 0.0,
                "repository_clicks": 0.0,
                "workbench_events": 0.0,
                "research_librarian_events": 0.0,
                "pathway_events": 0.0,
                "strategy_scores": [],
                "priority_pages": [],
            }
        item = grouped[key]
        item["pages"] += 1
        for field in ["current_views", "prior_views", "search_impressions", "repository_clicks", "workbench_events", "research_librarian_events", "pathway_events"]:
            item[field] += float(row.get(field, 0) or 0)
        item["strategy_scores"].append(float(row.get("strategy_score", 0) or 0))
        if row.get("strategy_score", 0) >= 45:
            item["priority_pages"].append({"title": row.get("title"), "path": row.get("path"), "score": row.get("strategy_score"), "status": row.get("status")})
    output = []
    for item in grouped.values():
        avg_score = sum(item["strategy_scores"]) / max(1, len(item["strategy_scores"]))
        item["avg_strategy_score"] = round(avg_score, 2)
        item["views_growth_rate"] = _growth_rate(item["current_views"], item["prior_views"])
        item["priority_pages"] = sorted(item["priority_pages"], key=lambda row: row["score"], reverse=True)[:5]
        item.pop("strategy_scores", None)
        output.append(item)
    return sorted(output, key=lambda row: (row["avg_strategy_score"], row["search_impressions"] + row["current_views"]), reverse=True)


def content_decay(rows: Iterable[Dict[str, Any]], limit: int = 20) -> List[Dict[str, Any]]:
    candidates = [row for row in rows if row.get("prior_views", 0) >= 80 and row.get("views_growth_rate", 0) <= -25]
    for row in candidates:
        row["decay_score"] = round(min(100.0, abs(row.get("views_growth_rate", 0)) + _log_component(row.get("prior_views", 0), scale=8, cap=30)), 2)
    return sorted(candidates, key=lambda row: row.get("decay_score", 0), reverse=True)[:limit]


def rising_pages(rows: Iterable[Dict[str, Any]], limit: int = 20) -> List[Dict[str, Any]]:
    candidates = [row for row in rows if row.get("current_views", 0) >= 80 and row.get("views_growth_rate", 0) >= 25]
    return sorted(candidates, key=lambda row: (row.get("views_growth_rate", 0), row.get("current_views", 0)), reverse=True)[:limit]


def publishing_queue(rows: Iterable[Dict[str, Any]], limit: int = 25) -> List[Dict[str, Any]]:
    queue = []
    for row in rows:
        suggested_surface = "site_update"
        status = row.get("status")
        if status == "rising":
            suggested_surface = "linkedin_substack_promotion"
        elif status == "search_opportunity":
            suggested_surface = "seo_metadata_refresh"
        elif status == "decay":
            suggested_surface = "content_refresh"
        elif row.get("workbench_events", 0) == 0 and row.get("current_views", 0) >= 150:
            suggested_surface = "workbench_prompt"
        queue.append({
            "title": row.get("title"),
            "path": row.get("path"),
            "hub": row.get("hub"),
            "article_map": row.get("article_map"),
            "status": status,
            "priority_score": row.get("strategy_score"),
            "suggested_surface": suggested_surface,
            "signals": {
                "current_views": row.get("current_views"),
                "views_growth_rate": row.get("views_growth_rate"),
                "search_impressions": row.get("search_impressions"),
                "search_ctr": row.get("search_ctr"),
                "search_position": row.get("search_position"),
            },
            "actions": row.get("actions", [])[:4],
        })
    return sorted(queue, key=lambda item: item["priority_score"], reverse=True)[:limit]


def newsletter_candidates(rows: Iterable[Dict[str, Any]], limit: int = 12) -> List[Dict[str, Any]]:
    candidates = []
    for row in rows:
        score = 0.0
        if row.get("status") == "rising":
            score += 30
        if row.get("search_impressions", 0) >= 250:
            score += 20
        if row.get("depth_score", 0) >= 45:
            score += 15
        if row.get("authority_score", 0) >= 35:
            score += 15
        if row.get("article_map"):
            score += 10
        if row.get("workbench_events", 0) or row.get("repository_clicks", 0):
            score += 10
        if score <= 0:
            continue
        candidates.append({
            "title": row.get("title"),
            "path": row.get("path"),
            "hub": row.get("hub"),
            "article_map": row.get("article_map"),
            "newsletter_score": round(min(100.0, score), 2),
            "angle": _newsletter_angle(row),
            "signals": {
                "views": row.get("current_views"),
                "growth": row.get("views_growth_rate"),
                "search_impressions": row.get("search_impressions"),
                "authority_score": row.get("authority_score"),
            },
        })
    return sorted(candidates, key=lambda item: item["newsletter_score"], reverse=True)[:limit]


def _newsletter_angle(row: Dict[str, Any]) -> str:
    title = row.get("title") or row.get("path") or "this topic"
    if row.get("article_map"):
        return f"Use {title} as an entry point into the {row.get('article_map')} article map."
    if row.get("hub") in {"Sustainability", "Research", "Platform"}:
        return f"Frame {title} as part of the Sustainable Catalyst platform and public-interest knowledge system."
    return f"Turn {title} into a short update that connects the page to related Sustainable Catalyst pathways."


def promotion_opportunities(rows: Iterable[Dict[str, Any]], limit: int = 20) -> List[Dict[str, Any]]:
    output = []
    for row in rows:
        surfaces: List[str] = []
        if row.get("views_growth_rate", 0) >= 25 or row.get("search_impressions", 0) >= 250:
            surfaces.extend(["LinkedIn", "Substack"])
        if row.get("authority_score", 0) >= 35 and row.get("repository_clicks", 0) < 5:
            surfaces.append("GitHub CTA")
        if row.get("workbench_events", 0) < 5 and row.get("current_views", 0) >= 120:
            surfaces.append("Workbench prompt")
        if row.get("research_librarian_events", 0) < 5 and row.get("current_views", 0) >= 120:
            surfaces.append("Research Librarian cross-link")
        if not surfaces:
            continue
        output.append({
            "title": row.get("title"),
            "path": row.get("path"),
            "hub": row.get("hub"),
            "article_map": row.get("article_map"),
            "promotion_score": row.get("strategy_score"),
            "surfaces": sorted(set(surfaces)),
            "actions": row.get("actions", [])[:4],
            "signals": {
                "views": row.get("current_views"),
                "growth": row.get("views_growth_rate"),
                "search_impressions": row.get("search_impressions"),
                "authority_score": row.get("authority_score"),
            },
        })
    return sorted(output, key=lambda item: item["promotion_score"], reverse=True)[:limit]


def topic_momentum_report(article_maps: Iterable[Dict[str, Any]], search_topics: Iterable[Dict[str, Any]], limit: int = 20) -> Dict[str, Any]:
    output = []
    for item in article_maps:
        output.append({
            "topic": item.get("name"),
            "hub": item.get("hub"),
            "source": "article_map_performance",
            "momentum_score": round(min(100.0, item.get("avg_strategy_score", 0) + min(25, item.get("views_growth_rate", 0) / 2)), 2),
            "views": round(item.get("current_views", 0), 2),
            "views_growth_rate": item.get("views_growth_rate", 0),
            "search_impressions": round(item.get("search_impressions", 0), 2),
            "priority_pages": item.get("priority_pages", []),
        })
    for topic in search_topics:
        output.append({
            "topic": topic.get("topic"),
            "hub": topic.get("discipline"),
            "source": "search_console_topic",
            "momentum_score": topic.get("momentum_score", 0),
            "views": 0,
            "views_growth_rate": 0,
            "search_impressions": topic.get("impressions", 0),
            "clicks": topic.get("clicks", 0),
            "ctr": topic.get("ctr", 0),
            "avg_position": topic.get("avg_position", 0),
            "priority_pages": [],
        })
    dedup: Dict[str, Dict[str, Any]] = {}
    for item in output:
        key = item.get("topic") or "Unclassified"
        if key not in dedup or item.get("momentum_score", 0) > dedup[key].get("momentum_score", 0):
            dedup[key] = item
    rows = sorted(dedup.values(), key=lambda row: row.get("momentum_score", 0), reverse=True)[:limit]
    return {
        "ok": True,
        "generated_at": utc_now(),
        "topics": rows,
        "recommendations": [
            "Prioritize topics that combine search impressions, rising GA4 visibility, and existing article-map structure.",
            "Use topic momentum to plan updates, newsletters, LinkedIn posts, and Workbench expansion prompts.",
        ],
    }


def publishing_recommendations(rows: List[Dict[str, Any]], article_maps: List[Dict[str, Any]], decay_rows: List[Dict[str, Any]]) -> List[str]:
    recs: List[str] = []
    if rows:
        recs.append(f"Highest publishing priority: {rows[0]['title']} ({rows[0]['status']}, score {rows[0]['strategy_score']}).")
    if article_maps:
        recs.append(f"Strongest article-map opportunity: {article_maps[0]['name']} with {round(article_maps[0]['current_views'], 1)} current views and {round(article_maps[0]['search_impressions'], 1)} search impressions.")
    if decay_rows:
        recs.append(f"Refresh {len(decay_rows)} pages showing material decline against the prior comparison window.")
    search_opps = [row for row in rows if row.get("status") == "search_opportunity"]
    if search_opps:
        recs.append(f"Review metadata and internal links for {len(search_opps)} high-impression search opportunity pages.")
    rising = [row for row in rows if row.get("status") == "rising"]
    if rising:
        recs.append(f"Promote {len(rising)} rising pages through LinkedIn/Substack and related series navigation.")
    if not recs:
        recs.append("Publishing signals are stable; continue monitoring GA4, Search Console, event, and registry movement.")
    return recs[:8]


def publishing_intelligence(
    ga4: GA4Client,
    search_client: SearchConsoleClient,
    registry: ContentRegistry,
    start_date: str = "28daysAgo",
    end_date: str = "yesterday",
    prior_start_date: str = "56daysAgo",
    prior_end_date: str = "29daysAgo",
    limit: int = 25,
) -> Dict[str, Any]:
    current_metrics = build_page_metrics(ga4.page_report(start_date, end_date), ga4.event_report(start_date, end_date), registry)
    prior_metrics = build_page_metrics(ga4.page_report(prior_start_date, prior_end_date), ga4.event_report(prior_start_date, prior_end_date), registry)
    current_search_pages = search_client.page_summary(registry, start_date=start_date, end_date=end_date)
    prior_search_pages = search_client.page_summary(registry, start_date=prior_start_date, end_date=prior_end_date)
    search_topics = search_client.topic_momentum(start_date=start_date, end_date=end_date)

    rows = page_strategy_rows(current_metrics, prior_metrics, current_search_pages, prior_search_pages, limit=max(limit, 50))
    article_maps = article_map_performance(rows)
    decay_rows = content_decay(rows, limit=limit)
    rising = rising_pages(rows, limit=limit)
    queue = publishing_queue(rows, limit=limit)
    newsletters = newsletter_candidates(rows, limit=12)
    promotions = promotion_opportunities(rows, limit=limit)
    topic_report = topic_momentum_report(article_maps, search_topics, limit=limit)

    current_totals = dashboard_totals(current_metrics)
    prior_totals = dashboard_totals(prior_metrics)
    totals = {
        "current_views": current_totals.get("screen_page_views", 0),
        "prior_views": prior_totals.get("screen_page_views", 0),
        "views_growth_rate": _growth_rate(current_totals.get("screen_page_views", 0), prior_totals.get("screen_page_views", 0)),
        "current_active_users": current_totals.get("active_users", 0),
        "current_repository_clicks": current_totals.get("repository_clicks", 0),
        "current_workbench_events": current_totals.get("workbench_events", 0),
        "current_research_librarian_events": current_totals.get("research_librarian_events", 0),
        "priority_pages": len([row for row in rows if row.get("strategy_score", 0) >= 45]),
        "decay_pages": len(decay_rows),
        "rising_pages": len(rising),
        "promotion_opportunities": len(promotions),
        "article_maps_reviewed": len(article_maps),
    }
    return {
        "ok": True,
        "generated_at": utc_now(),
        "source": {
            "ga4": "ga4" if ga4.enabled else "sample-ga4",
            "search": "search-console" if search_client.enabled else "sample-search",
        },
        "date_range": {"start_date": start_date, "end_date": end_date},
        "comparison_range": {"start_date": prior_start_date, "end_date": prior_end_date},
        "totals": totals,
        "top_pages": rows[:limit],
        "article_map_performance": article_maps[:limit],
        "topic_momentum": topic_report.get("topics", [])[:limit],
        "content_decay": decay_rows,
        "rising_pages": rising,
        "publishing_queue": queue,
        "newsletter_candidates": newsletters,
        "promotion_opportunities": promotions,
        "recommendations": publishing_recommendations(rows, article_maps, decay_rows),
        "methodology": {
            "summary": "Publishing Intelligence combines GA4 page behavior, Search Console visibility, custom conversion events, and the Sustainable Catalyst registry to prioritize updates, promotion, internal links, and platform/tool placement.",
            "score_note": "Publishing priority scores are directional planning metrics; they are not official GA4, Search Console, or Google ranking metrics.",
            "review_note": "Use this internally to plan updates, newsletters, LinkedIn posts, Workbench prompts, and article-map improvements before making public dashboards available.",
        },
    }
