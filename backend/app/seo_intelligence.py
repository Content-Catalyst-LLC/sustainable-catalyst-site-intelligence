from __future__ import annotations

import math
import re
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .registry import ContentRegistry
from .search_console import SearchConsoleClient, norm_page, opportunity_score, safe_div

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "how", "in", "into", "is", "it",
    "of", "on", "or", "the", "this", "to", "with", "your", "what", "why", "sustainable", "catalyst",
}

GENERIC_TITLE_MARKERS = [
    "page not found",
    "archives",
    "uncategorized",
    "author archives",
    "tag archives",
    "category archives",
]

TECHNICAL_HUBS = {
    "Research", "Mathematics", "Modeling", "Analytics", "Platform", "Sustainability", "Law", "Technology",
    "Environmental Science", "Energy", "International Law",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def tokenize(text: str) -> List[str]:
    return [token for token in re.findall(r"[a-z0-9]+", (text or "").lower()) if token not in STOPWORDS and len(token) > 2]


def overlap_ratio(title: str, query: str) -> float:
    q = set(tokenize(query))
    if not q:
        return 0.0
    t = set(tokenize(title))
    return round(len(q & t) / max(1, len(q)), 3)


def title_status(title: str) -> Dict[str, Any]:
    length = len(title or "")
    lower = (title or "").lower()
    issues: List[str] = []
    status = "healthy"
    if length < 35:
        issues.append("Title may be too short to communicate topic depth and search intent.")
    if length > 72:
        issues.append("Title may be too long for search-result display and should be reviewed for front-loaded clarity.")
    if any(marker in lower for marker in GENERIC_TITLE_MARKERS):
        issues.append("Title appears generic or archive-like; review whether this page should be indexed, redirected, or given a stronger title.")
    if "sustainable catalyst" not in lower:
        issues.append("Title does not include the Sustainable Catalyst brand; this may be fine for articles, but review priority pages for brand consistency.")
    if issues:
        status = "review"
    if any("generic" in issue.lower() or "archive" in issue.lower() for issue in issues):
        status = "priority"
    return {"length": length, "status": status, "issues": issues}


def metadata_score(page: Dict[str, Any]) -> float:
    impressions = float(page.get("impressions", 0))
    ctr = float(page.get("ctr", 0)) / 100.0
    position = float(page.get("position", 0))
    base = opportunity_score(impressions, ctr, position, mapped=page.get("mapping_status") in {"explicit", "inferred"})
    top_query = ""
    if page.get("top_queries"):
        top_query = page["top_queries"][0].get("query", "")
    title = page.get("title") or page.get("page") or ""
    overlap = overlap_ratio(title, top_query)
    if overlap < 0.25 and impressions >= 100:
        base += 10
    status = title_status(title)
    base += min(15, len(status["issues"]) * 4)
    return round(min(100.0, base), 2)


def link_priority(page: Dict[str, Any]) -> float:
    impressions = float(page.get("impressions", 0))
    position = float(page.get("position", 0))
    ctr = float(page.get("ctr", 0)) / 100.0
    component = min(40.0, math.log10(max(impressions, 1)) * 13.0)
    if 6 <= position <= 20:
        component += 30
    elif position <= 5:
        component += 15
    elif 20 < position <= 40:
        component += 18
    if ctr < 0.04 and impressions >= 100:
        component += 12
    if page.get("mapping_status") == "unmapped":
        component += 10
    return round(min(100.0, component), 2)


def build_anchor_suggestions(page: Dict[str, Any]) -> List[str]:
    suggestions: List[str] = []
    queries = page.get("top_queries") or []
    for query in queries[:3]:
        q = query.get("query")
        if q and q not in suggestions:
            suggestions.append(q)
    article_map = page.get("article_map")
    if article_map and article_map.lower() not in [s.lower() for s in suggestions]:
        suggestions.append(article_map)
    hub = page.get("hub")
    if hub and hub != "Unmapped" and hub.lower() not in [s.lower() for s in suggestions]:
        suggestions.append(hub)
    return suggestions[:5]


def metadata_review(client: SearchConsoleClient, registry: ContentRegistry, start_date: str = "28daysAgo", end_date: str = "yesterday", limit: int = 25) -> Dict[str, Any]:
    pages = client.page_summary(registry, start_date=start_date, end_date=end_date)
    reviews: List[Dict[str, Any]] = []
    for page in pages:
        title = page.get("title") or page.get("page") or ""
        top_query = page.get("top_queries", [{}])[0].get("query", "") if page.get("top_queries") else ""
        status = title_status(title)
        overlap = overlap_ratio(title, top_query)
        recommendations: List[str] = []
        if status["issues"]:
            recommendations.extend(status["issues"])
        if top_query and overlap < 0.25 and page.get("impressions", 0) >= 100:
            recommendations.append("Search intent/title alignment is weak; consider front-loading language closer to the strongest query without keyword stuffing.")
        if page.get("impressions", 0) >= 250 and page.get("ctr", 0) < 4:
            recommendations.append("High impressions with low CTR: rewrite title and meta description around the article's real promise and audience value.")
        if 6 <= page.get("position", 0) <= 20:
            recommendations.append("Near page-one opportunity: strengthen title specificity, intro clarity, internal links, and related-series context.")
        if page.get("mapping_status") == "unmapped":
            recommendations.append("Add this page to the registry so metadata recommendations can be tied to article maps, tools, and repositories.")
        if not recommendations:
            recommendations.append("Metadata looks acceptable from available Search Console and registry signals; monitor CTR and query drift.")
        reviews.append({
            "page": page.get("page"),
            "title": title,
            "hub": page.get("hub"),
            "article_map": page.get("article_map"),
            "mapping_status": page.get("mapping_status"),
            "clicks": page.get("clicks", 0),
            "impressions": page.get("impressions", 0),
            "ctr": page.get("ctr", 0),
            "position": page.get("position", 0),
            "top_query": top_query,
            "title_length": status["length"],
            "title_status": status["status"],
            "query_title_overlap": overlap,
            "metadata_priority_score": metadata_score(page),
            "recommendations": recommendations[:5],
        })
    priority = sorted(reviews, key=lambda item: item["metadata_priority_score"], reverse=True)
    return {
        "ok": True,
        "source": "search-console" if client.enabled else "sample-search",
        "generated_at": utc_now(),
        "date_range": {"start_date": start_date, "end_date": end_date},
        "summary": {
            "pages_reviewed": len(reviews),
            "priority_pages": len([item for item in reviews if item["metadata_priority_score"] >= 60]),
            "low_ctr_pages": len([item for item in reviews if item["impressions"] >= 250 and item["ctr"] < 4]),
            "generic_title_pages": len([item for item in reviews if item["title_status"] == "priority"]),
        },
        "metadata_reviews": priority[:limit],
        "recommendations": build_metadata_recommendations(priority),
        "methodology": {
            "summary": "Metadata Intelligence uses Search Console performance, query-title alignment, title length, generic-title detection, and registry mapping status to prioritize title and meta-description review.",
            "limitation": "The backend does not crawl the rendered HTML meta description in this build; recommendations identify pages worth reviewing rather than claiming exact meta-tag defects.",
        },
    }


def build_metadata_recommendations(reviews: List[Dict[str, Any]]) -> List[str]:
    recommendations: List[str] = []
    low_ctr = [item for item in reviews if item["impressions"] >= 250 and item["ctr"] < 4]
    if low_ctr:
        recommendations.append(f"Rewrite titles/meta descriptions for {len(low_ctr)} high-impression pages with CTR below 4%.")
    generic = [item for item in reviews if item["title_status"] == "priority"]
    if generic:
        recommendations.append(f"Review {len(generic)} generic/archive/error-style titles before exposing search dashboards publicly.")
    weak_alignment = [item for item in reviews if item["query_title_overlap"] < 0.25 and item["impressions"] >= 100]
    if weak_alignment:
        recommendations.append(f"Improve query-title alignment on {len(weak_alignment)} pages where search demand does not clearly match the title language.")
    near = [item for item in reviews if 6 <= item["position"] <= 20]
    if near:
        recommendations.append(f"Prioritize metadata and internal-link upgrades for {len(near)} pages ranking near positions 6–20.")
    if not recommendations:
        recommendations.append("Metadata signals look stable; continue monitoring CTR, query drift, and article-map search momentum.")
    return recommendations[:5]


def internal_link_review(client: SearchConsoleClient, registry: ContentRegistry, start_date: str = "28daysAgo", end_date: str = "yesterday", limit: int = 25) -> Dict[str, Any]:
    pages = client.page_summary(registry, start_date=start_date, end_date=end_date)
    by_map: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for page in pages:
        by_map[page.get("article_map") or page.get("hub") or "Unmapped"].append(page)

    opportunities: List[Dict[str, Any]] = []
    for page in pages:
        path = page.get("page") or "/"
        match = registry.resolve(path)
        item = match.item
        map_key = page.get("article_map") or page.get("hub") or "Unmapped"
        related = sorted(
            [candidate for candidate in by_map.get(map_key, []) if candidate.get("page") != path],
            key=lambda row: (row.get("impressions", 0), row.get("opportunity_score", 0)),
            reverse=True,
        )[:5]
        actions: List[str] = []
        if 6 <= page.get("position", 0) <= 20:
            actions.append("Add contextual internal links from the most relevant hub and adjacent article-map pages to push this near-page-one page upward.")
        if page.get("impressions", 0) >= 250 and page.get("ctr", 0) < 4:
            actions.append("Pair title/meta review with internal links using natural anchor text that matches the highest-intent queries.")
        if page.get("mapping_status") == "unmapped":
            actions.append("Map this page in the registry before assigning internal-link targets.")
        if item and item.intended_next_paths:
            actions.append("Verify intended-next links are visible in the article body and bottom pathway strip.")
        if item and item.repository_url:
            actions.append("Place the GitHub repository CTA near applied examples, code companions, or tool sections.")
        if item and item.workbench_tool_ids:
            actions.append("Add an inline Workbench prompt where search visitors are likely to need applied modeling support.")
        if page.get("hub") in TECHNICAL_HUBS and not (item and (item.repository_url or item.workbench_tool_ids)):
            actions.append("Review whether this technical/search-visible page should connect to a repository, Workbench tool, or Research Librarian pathway.")
        if not actions:
            actions.append("Maintain internal links to sibling pages and monitor whether search visibility converts into deeper article-map movement.")
        opportunities.append({
            "page": path,
            "title": page.get("title"),
            "hub": page.get("hub"),
            "article_map": page.get("article_map"),
            "mapping_status": page.get("mapping_status"),
            "clicks": page.get("clicks", 0),
            "impressions": page.get("impressions", 0),
            "ctr": page.get("ctr", 0),
            "position": page.get("position", 0),
            "internal_link_priority_score": link_priority(page),
            "anchor_suggestions": build_anchor_suggestions(page),
            "source_link_candidates": [
                {
                    "page": candidate.get("page"),
                    "title": candidate.get("title"),
                    "impressions": candidate.get("impressions", 0),
                    "opportunity_score": candidate.get("opportunity_score", 0),
                }
                for candidate in related
            ],
            "target_links": item.intended_next_paths if item else [],
            "repository_url": item.repository_url if item else None,
            "workbench_tool_ids": item.workbench_tool_ids if item else [],
            "actions": actions[:6],
        })
    ranked = sorted(opportunities, key=lambda item: item["internal_link_priority_score"], reverse=True)
    return {
        "ok": True,
        "source": "search-console" if client.enabled else "sample-search",
        "generated_at": utc_now(),
        "date_range": {"start_date": start_date, "end_date": end_date},
        "summary": {
            "pages_reviewed": len(opportunities),
            "priority_pages": len([item for item in opportunities if item["internal_link_priority_score"] >= 60]),
            "near_page_one_pages": len([item for item in opportunities if 6 <= item["position"] <= 20]),
            "unmapped_search_pages": len([item for item in opportunities if item["mapping_status"] == "unmapped"]),
        },
        "internal_link_opportunities": ranked[:limit],
        "recommendations": build_internal_link_recommendations(ranked),
        "methodology": {
            "summary": "Internal Link Intelligence combines Search Console opportunity signals with the registry's hubs, article maps, intended next paths, repositories, and Workbench tool IDs.",
            "limitation": "This build recommends link opportunities from registry/search data; it does not crawl every rendered page to verify existing internal-link placement.",
        },
    }


def build_internal_link_recommendations(items: List[Dict[str, Any]]) -> List[str]:
    recommendations: List[str] = []
    near = [item for item in items if 6 <= item["position"] <= 20]
    if near:
        recommendations.append(f"Add stronger contextual links into {len(near)} pages ranking near positions 6–20.")
    unmapped = [item for item in items if item["mapping_status"] == "unmapped"]
    if unmapped:
        recommendations.append(f"Resolve {len(unmapped)} search-visible unmapped pages before relying on automated internal-link recommendations.")
    workbench = [item for item in items if item.get("workbench_tool_ids")]
    if workbench:
        recommendations.append(f"Validate visible Workbench prompts on {len(workbench)} search-visible pages with associated tools.")
    repo = [item for item in items if item.get("repository_url")]
    if repo:
        recommendations.append(f"Validate contextual GitHub repository CTAs on {len(repo)} search-visible pages with repositories.")
    if not recommendations:
        recommendations.append("Internal-link opportunity signals are stable; continue comparing Search Console visibility with GA4 pathway continuation.")
    return recommendations[:5]


def seo_recommendations(client: SearchConsoleClient, registry: ContentRegistry, start_date: str = "28daysAgo", end_date: str = "yesterday", limit: int = 25) -> Dict[str, Any]:
    metadata = metadata_review(client, registry, start_date=start_date, end_date=end_date, limit=limit)
    links = internal_link_review(client, registry, start_date=start_date, end_date=end_date, limit=limit)
    combined: List[Dict[str, Any]] = []
    meta_by_page = {item["page"]: item for item in metadata["metadata_reviews"]}
    link_by_page = {item["page"]: item for item in links["internal_link_opportunities"]}
    for page in sorted(set(meta_by_page) | set(link_by_page)):
        meta = meta_by_page.get(page, {})
        link = link_by_page.get(page, {})
        score = round(max(float(meta.get("metadata_priority_score", 0)), float(link.get("internal_link_priority_score", 0))), 2)
        combined.append({
            "page": page,
            "title": meta.get("title") or link.get("title") or page,
            "hub": meta.get("hub") or link.get("hub"),
            "article_map": meta.get("article_map") or link.get("article_map"),
            "priority_score": score,
            "metadata_priority_score": meta.get("metadata_priority_score", 0),
            "internal_link_priority_score": link.get("internal_link_priority_score", 0),
            "recommendations": (meta.get("recommendations", [])[:3] + link.get("actions", [])[:3])[:6],
            "anchor_suggestions": link.get("anchor_suggestions", []),
        })
    combined = sorted(combined, key=lambda item: item["priority_score"], reverse=True)[:limit]
    return {
        "ok": True,
        "source": metadata.get("source"),
        "generated_at": utc_now(),
        "date_range": metadata.get("date_range", {}),
        "summary": {
            "metadata_priority_pages": metadata.get("summary", {}).get("priority_pages", 0),
            "internal_link_priority_pages": links.get("summary", {}).get("priority_pages", 0),
            "combined_priority_pages": len([item for item in combined if item["priority_score"] >= 60]),
        },
        "top_recommendations": combined,
        "recommendations": metadata.get("recommendations", []) + links.get("recommendations", []),
        "methodology": {
            "summary": "SEO Recommendation Intelligence merges metadata/title review with internal-link opportunity detection so updates can be prioritized by Search Console evidence and Sustainable Catalyst registry context.",
            "review_note": "Treat recommendations as editorial/workflow guidance; final SEO titles, descriptions, and links should be reviewed manually before publication.",
        },
    }
