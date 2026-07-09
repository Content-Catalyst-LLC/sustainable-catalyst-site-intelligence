from __future__ import annotations

from typing import List

from .metrics import safe_div
from .models import PageMetric


def site_recommendations(metrics: List[PageMetric]) -> List[str]:
    if not metrics:
        return ["Connect GA4 or load a registry with page analytics to generate recommendations."]

    recs: List[str] = []
    operational = [item for item in metrics if item.mapping_status != "excluded"]
    total_users = sum(item.active_users for item in operational)
    total_repo = sum(item.repository_clicks for item in operational)
    total_workbench = sum(item.workbench_events for item in operational)
    total_librarian = sum(item.research_librarian_events for item in operational)
    total_pathway = sum(item.pathway_events for item in operational)

    repo_rate = safe_div(total_repo, max(total_users, 1.0))
    workbench_rate = safe_div(total_workbench, max(total_users, 1.0))
    librarian_rate = safe_div(total_librarian, max(total_users, 1.0))
    pathway_rate = safe_div(total_pathway, max(total_users, 1.0))

    unmapped = [item for item in operational if item.mapping_status == "unmapped"]
    inferred = [item for item in operational if item.mapping_status == "inferred"]
    if unmapped:
        recs.append("Registry mapping still has gaps; add explicit entries for the highest-traffic unmapped pages first.")
    elif inferred:
        recs.append("Most pages are now interpreted; promote high-traffic inferred mappings into explicit registry entries.")
    else:
        recs.append("Registry coverage is strong; use the dashboard to optimize pathways, tools, and repository conversion.")

    if pathway_rate < 0.25:
        recs.append("Increase visible article-map pathways from hubs into deeper series pages.")
    else:
        recs.append("Article-pathway movement is becoming a strength; feature the best-performing pathways on the Research Library page.")

    if repo_rate < 0.08:
        recs.append("Repository conversion is low relative to readership; add contextual GitHub CTAs near applied examples and tool sections.")
    else:
        recs.append("Repository clicks are meaningful; consider highlighting GitHub-backed articles in LinkedIn and Substack posts.")

    if workbench_rate < 0.10:
        recs.append("Workbench activation is still emerging; add short inline prompts from high-engagement articles into relevant tools.")
    else:
        recs.append("Workbench usage is strong enough to justify a dedicated Platform Demos pathway.")

    if librarian_rate < 0.07:
        recs.append("Research Librarian should be cross-linked from article maps and long articles as a guided inquiry assistant.")

    high_engagement_low_conversion = [
        item for item in operational
        if item.engagement_rate >= 0.60 and item.screen_page_views >= 200 and item.repository_clicks + item.workbench_events < 20
    ]
    if high_engagement_low_conversion:
        title = high_engagement_low_conversion[0].title or high_engagement_low_conversion[0].path
        recs.append(f"Prioritize conversion improvements on high-engagement page: {title}.")

    system_404 = [item for item in metrics if item.content_type == "system" and item.screen_page_views >= 100]
    if system_404:
        recs.append("404 traffic is visible in GA4; review broken links, redirects, and article-map navigation that may be sending users to missing pages.")

    return recs[:7]
