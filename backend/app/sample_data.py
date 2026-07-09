from __future__ import annotations

from typing import List

from .models import GA4ReportRow


def sample_page_rows() -> List[GA4ReportRow]:
    """Demo-mode page metrics for local testing before GA4 is connected."""
    raw = [
        ("/research-library/", "Research Library", 980, 612, 3310, 0.64, 142),
        ("/workbench/", "Sustainable Catalyst Workbench", 640, 391, 2040, 0.58, 119),
        ("/linear-algebra-for-systems-modeling/", "Linear Algebra for Systems Modeling", 520, 311, 1760, 0.69, 186),
        ("/algorithms-computational-reasoning/", "Algorithms and Computational Reasoning", 470, 284, 1440, 0.61, 154),
        ("/research-librarian-ai/", "Research Librarian AI", 430, 271, 1210, 0.55, 96),
        ("/international-law/", "International Law", 390, 225, 1122, 0.59, 131),
        ("/decision-studio/", "Decision Studio", 310, 190, 870, 0.51, 84),
        ("/meaning/", "Meaning", 290, 181, 920, 0.62, 148),
        ("/calculus-for-systems-modeling/", "Calculus for Systems Modeling", 260, 156, 811, 0.66, 177),
        ("/channel/", "Channel", 205, 139, 490, 0.42, 61),
    ]
    return [
        GA4ReportRow(
            dimensions={"pagePath": path, "pageTitle": title},
            metrics={
                "screenPageViews": views,
                "activeUsers": users,
                "eventCount": events,
                "engagementRate": engagement,
                "averageSessionDuration": duration,
            },
        )
        for path, title, views, users, events, engagement, duration in raw
    ]


def sample_event_rows() -> List[GA4ReportRow]:
    raw = [
        ("/research-library/", "sc_library_nav", 220),
        ("/workbench/", "sc_workbench_open", 164),
        ("/linear-algebra-for-systems-modeling/", "sc_repository_click", 52),
        ("/linear-algebra-for-systems-modeling/", "sc_pathway_continue", 88),
        ("/algorithms-computational-reasoning/", "sc_repository_click", 37),
        ("/research-librarian-ai/", "sc_research_librarian_open", 97),
        ("/decision-studio/", "sc_decision_studio_open", 61),
        ("/research-library/", "sc_scroll_depth", 310),
        ("/calculus-for-systems-modeling/", "sc_workbench_open", 43),
        ("/international-law/", "sc_pathway_continue", 72),
        ("/meaning/", "sc_pathway_continue", 58),
    ]
    return [
        GA4ReportRow(
            dimensions={"pagePath": path, "eventName": event},
            metrics={"eventCount": count},
        )
        for path, event, count in raw
    ]
