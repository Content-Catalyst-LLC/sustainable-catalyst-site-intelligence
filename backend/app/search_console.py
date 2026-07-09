from __future__ import annotations

import json
import math
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .config import Settings
from .registry import ContentRegistry

SEARCH_CONSOLE_SCOPE = "https://www.googleapis.com/auth/webmasters.readonly"
SEARCH_ANALYTICS_ENDPOINT = "https://searchconsole.googleapis.com/webmasters/v3/sites/{site_url}/searchAnalytics/query"

SAMPLE_SEARCH_ROWS: List[Dict[str, Any]] = [
    {"keys": ["sustainable catalyst", "https://sustainablecatalyst.com/publications/"], "clicks": 86, "impressions": 1320, "ctr": 0.0652, "position": 8.7},
    {"keys": ["linear algebra systems modeling", "https://sustainablecatalyst.com/linear-algebra-for-systems-modeling/"], "clicks": 31, "impressions": 920, "ctr": 0.0337, "position": 11.4},
    {"keys": ["war crimes crimes against humanity genocide", "https://sustainablecatalyst.com/war-crimes-crimes-against-humanity-genocide-and-the-architecture-of-international-criminal-law/"], "clicks": 18, "impressions": 760, "ctr": 0.0237, "position": 13.2},
    {"keys": ["mathematical modeling archives", "https://sustainablecatalyst.com/mathematical-modeling/"], "clicks": 24, "impressions": 540, "ctr": 0.0444, "position": 9.9},
    {"keys": ["research library knowledge architecture", "https://sustainablecatalyst.com/research-library/"], "clicks": 12, "impressions": 410, "ctr": 0.0293, "position": 16.1},
    {"keys": ["sustainable development indicator tool", "https://sustainablecatalyst.com/workbench/"], "clicks": 7, "impressions": 335, "ctr": 0.0209, "position": 18.6},
    {"keys": ["climate energy intelligence dashboard", "https://sustainablecatalyst.com/platform/"], "clicks": 5, "impressions": 220, "ctr": 0.0227, "position": 21.5},
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def resolve_date(value: str) -> str:
    """Resolve Search Console dates to YYYY-MM-DD.

    Supports `today`, `yesterday`, and GA-style relative values such as
    `28daysAgo`. Search Console usually has a delay, so default end dates use
    yesterday rather than today.
    """
    today = date.today()
    value = (value or "").strip()
    if not value:
        return (today - timedelta(days=2)).isoformat()
    if value == "today":
        return today.isoformat()
    if value == "yesterday":
        return (today - timedelta(days=1)).isoformat()
    if value.endswith("daysAgo"):
        try:
            days = int(value.replace("daysAgo", ""))
            return (today - timedelta(days=days)).isoformat()
        except ValueError:
            return (today - timedelta(days=28)).isoformat()
    return value


def norm_page(value: str) -> str:
    if not value:
        return "/"
    value = value.split("?", 1)[0].split("#", 1)[0]
    if value.startswith("http"):
        for host in ["https://sustainablecatalyst.com", "http://sustainablecatalyst.com"]:
            if value.startswith(host):
                value = value[len(host):] or "/"
                break
    if not value.startswith("/"):
        value = "/" + value
    if value != "/" and not value.endswith("/"):
        value += "/"
    return value


def safe_div(numerator: float, denominator: float) -> float:
    if not denominator:
        return 0.0
    return numerator / denominator


def weighted_position(rows: Iterable[Dict[str, Any]]) -> float:
    rows = list(rows)
    total_impressions = sum(float(row.get("impressions", 0)) for row in rows)
    if total_impressions <= 0:
        return 0.0
    return round(sum(float(row.get("position", 0)) * float(row.get("impressions", 0)) for row in rows) / total_impressions, 2)


def opportunity_score(impressions: float, ctr: float, position: float, mapped: bool = True) -> float:
    impression_component = min(45.0, math.log10(max(impressions, 1)) * 15.0)
    ctr_gap = max(0.0, 0.08 - ctr)
    ctr_component = min(30.0, ctr_gap / 0.08 * 30.0)
    if position <= 0:
        position_component = 8.0
    elif position <= 5:
        position_component = 10.0
    elif position <= 20:
        position_component = 20.0
    else:
        position_component = 12.0
    mapping_component = 5.0 if mapped else 10.0
    return round(min(100.0, impression_component + ctr_component + position_component + mapping_component), 2)


def query_topic(query: str) -> Dict[str, str]:
    text = (query or "").lower()
    rules = [
        ("Linear Algebra for Systems Modeling", "Mathematics", ["linear algebra", "matrix", "matrices", "eigen", "markov"]),
        ("Calculus for Systems Modeling", "Mathematics", ["calculus", "derivative", "integral", "limit"]),
        ("International Law", "Law", ["war crimes", "genocide", "crimes against humanity", "human rights", "international law"]),
        ("Climate + Energy Intelligence", "Sustainability", ["climate", "energy", "emissions", "solar", "environmental"]),
        ("Research Library", "Knowledge Systems", ["research library", "knowledge architecture", "learning architecture"]),
        ("Workbench", "Platform", ["workbench", "calculator", "scenario", "tool"]),
        ("Meaning", "Humanities", ["meaning", "myth", "symbol", "ritual", "aesthetic"]),
        ("Publications", "Publishing", ["sustainable catalyst", "publication", "article"]),
    ]
    for topic, discipline, needles in rules:
        if any(needle in text for needle in needles):
            return {"topic": topic, "discipline": discipline}
    return {"topic": "Unclassified Search Demand", "discipline": "Unmapped"}


class SearchConsoleClient:
    """Search Console connector and Sustainable Catalyst SEO interpretation layer."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._session: Optional[Any] = None

    @property
    def enabled(self) -> bool:
        return bool(self.settings.search_console_site_url) and self.settings.search_console_live and bool(
            self.settings.google_application_credentials_json or self.settings.google_application_credentials_file
        )

    def _credentials(self):
        from google.oauth2 import service_account
        if self.settings.google_application_credentials_json:
            info = json.loads(self.settings.google_application_credentials_json)
            return service_account.Credentials.from_service_account_info(info, scopes=[SEARCH_CONSOLE_SCOPE])
        if self.settings.google_application_credentials_file:
            return service_account.Credentials.from_service_account_file(
                self.settings.google_application_credentials_file,
                scopes=[SEARCH_CONSOLE_SCOPE],
            )
        raise RuntimeError("Search Console credentials are not configured.")

    def _build_session(self):
        from google.auth.transport.requests import AuthorizedSession
        if self._session is None:
            self._session = AuthorizedSession(self._credentials())
        return self._session

    def diagnostics(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "enabled": self.enabled,
            "site_url": self.settings.search_console_site_url,
            "credential_source": "json" if self.settings.google_application_credentials_json else "file" if self.settings.google_application_credentials_file else "none",
            "live_mode": self.settings.search_console_live,
            "request_ok": None,
            "error_type": None,
            "error_message": None,
        }
        if not self.enabled:
            result["request_ok"] = False
            result["message"] = "Search Console is using sample data or is not configured."
            return result
        try:
            rows = self.performance(start_date="7daysAgo", end_date="yesterday", dimensions=["query"], row_limit=1)
            result["request_ok"] = True
            result["sample_rows"] = len(rows)
        except Exception as exc:  # noqa: BLE001
            result["request_ok"] = False
            result["error_type"] = exc.__class__.__name__
            result["error_message"] = str(exc)
        return result

    def performance(
        self,
        start_date: str = "28daysAgo",
        end_date: str = "yesterday",
        dimensions: Optional[List[str]] = None,
        row_limit: int = 250,
    ) -> List[Dict[str, Any]]:
        dimensions = dimensions or ["query", "page"]
        if not self.enabled:
            return [dict(row) for row in SAMPLE_SEARCH_ROWS]

        site_url = self.settings.search_console_site_url
        endpoint = SEARCH_ANALYTICS_ENDPOINT.format(site_url=site_url.replace(":", "%3A").replace("/", "%2F"))
        payload = {
            "startDate": resolve_date(start_date),
            "endDate": resolve_date(end_date),
            "dimensions": dimensions,
            "rowLimit": min(row_limit, self.settings.search_console_max_rows),
            "startRow": 0,
        }
        response = self._build_session().post(endpoint, json=payload, timeout=self.settings.search_console_timeout_seconds)
        if not response.ok:
            raise RuntimeError(f"Search Console API error {response.status_code}: {response.text[:500]}")
        data = response.json()
        return data.get("rows", [])

    def page_summary(self, registry: ContentRegistry, start_date: str = "28daysAgo", end_date: str = "yesterday") -> List[Dict[str, Any]]:
        rows = self.performance(start_date=start_date, end_date=end_date, dimensions=["query", "page"], row_limit=self.settings.search_console_max_rows)
        grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for row in rows:
            keys = row.get("keys", [])
            if len(keys) >= 2:
                page = norm_page(keys[1])
            elif len(keys) == 1 and str(keys[0]).startswith("http"):
                page = norm_page(keys[0])
            else:
                page = "/"
            grouped[page].append(row)

        output = []
        for page, page_rows in grouped.items():
            clicks = sum(float(row.get("clicks", 0)) for row in page_rows)
            impressions = sum(float(row.get("impressions", 0)) for row in page_rows)
            ctr = safe_div(clicks, impressions)
            position = weighted_position(page_rows)
            match = registry.resolve(page)
            top_queries = sorted(
                [
                    {
                        "query": (row.get("keys", [""])[0] if row.get("keys") else ""),
                        "clicks": row.get("clicks", 0),
                        "impressions": row.get("impressions", 0),
                        "ctr": row.get("ctr", 0),
                        "position": row.get("position", 0),
                        **query_topic(row.get("keys", [""])[0] if row.get("keys") else ""),
                    }
                    for row in page_rows
                ],
                key=lambda item: item["impressions"],
                reverse=True,
            )[:5]
            score = opportunity_score(impressions, ctr, position, mapped=match.status in {"explicit", "inferred"})
            recs = []
            if impressions >= 250 and ctr < 0.04:
                recs.append("Review SEO title and meta description; this page has meaningful impressions but low CTR.")
            if 6 <= position <= 20:
                recs.append("Strengthen internal links and topical context; this page is near striking distance in search results.")
            if match.status == "unmapped":
                recs.append("Add this search-visible page to the Site Intelligence registry.")
            if match.item and match.item.repository_url:
                recs.append("Tie the search-visible page to its GitHub repository CTA where relevant.")
            if match.item and match.item.workbench_tool_ids:
                recs.append("Add a contextual Workbench prompt for search visitors who need applied analysis.")
            if not recs:
                recs.append("Monitor search momentum and compare against related article-map pages.")
            output.append({
                "page": page,
                "title": match.item.title if match.item else page,
                "hub": match.item.hub if match.item else "Unmapped",
                "article_map": match.item.article_map if match.item else None,
                "discipline": match.item.discipline if match.item else None,
                "mapping_status": match.status,
                "mapping_confidence": match.confidence,
                "clicks": round(clicks, 2),
                "impressions": round(impressions, 2),
                "ctr": round(ctr * 100, 2),
                "position": position,
                "opportunity_score": score,
                "top_queries": top_queries,
                "recommendations": recs[:4],
            })
        return sorted(output, key=lambda item: item["opportunity_score"], reverse=True)

    def query_summary(self, start_date: str = "28daysAgo", end_date: str = "yesterday") -> List[Dict[str, Any]]:
        rows = self.performance(start_date=start_date, end_date=end_date, dimensions=["query", "page"], row_limit=self.settings.search_console_max_rows)
        grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for row in rows:
            keys = row.get("keys", [])
            query = keys[0] if keys else ""
            grouped[query].append(row)
        output = []
        for query, qrows in grouped.items():
            clicks = sum(float(row.get("clicks", 0)) for row in qrows)
            impressions = sum(float(row.get("impressions", 0)) for row in qrows)
            ctr = safe_div(clicks, impressions)
            pos = weighted_position(qrows)
            pages = sorted({norm_page(row.get("keys", ["", ""])[1]) for row in qrows if len(row.get("keys", [])) >= 2})
            output.append({
                "query": query,
                **query_topic(query),
                "clicks": round(clicks, 2),
                "impressions": round(impressions, 2),
                "ctr": round(ctr * 100, 2),
                "position": pos,
                "pages": pages[:5],
                "opportunity_score": opportunity_score(impressions, ctr, pos, mapped=True),
            })
        return sorted(output, key=lambda item: item["opportunity_score"], reverse=True)

    def topic_momentum(self, start_date: str = "28daysAgo", end_date: str = "yesterday") -> List[Dict[str, Any]]:
        grouped: Dict[str, Dict[str, Any]] = {}
        for item in self.query_summary(start_date=start_date, end_date=end_date):
            topic = item["topic"]
            if topic not in grouped:
                grouped[topic] = {"topic": topic, "discipline": item["discipline"], "clicks": 0.0, "impressions": 0.0, "queries": 0, "positions": []}
            grouped[topic]["clicks"] += item["clicks"]
            grouped[topic]["impressions"] += item["impressions"]
            grouped[topic]["queries"] += 1
            grouped[topic]["positions"].append(item["position"])
        output = []
        for topic, item in grouped.items():
            item["ctr"] = round(safe_div(item["clicks"], item["impressions"]) * 100, 2)
            item["avg_position"] = round(sum(item["positions"]) / max(1, len(item["positions"])), 2)
            item["momentum_score"] = opportunity_score(item["impressions"], item["ctr"] / 100.0, item["avg_position"], mapped=True)
            item.pop("positions", None)
            output.append(item)
        return sorted(output, key=lambda row: row["momentum_score"], reverse=True)

    def search_intelligence(self, registry: ContentRegistry, start_date: str = "28daysAgo", end_date: str = "yesterday") -> Dict[str, Any]:
        pages = self.page_summary(registry, start_date=start_date, end_date=end_date)
        queries = self.query_summary(start_date=start_date, end_date=end_date)
        topics = self.topic_momentum(start_date=start_date, end_date=end_date)
        totals = {
            "clicks": round(sum(item["clicks"] for item in pages), 2),
            "impressions": round(sum(item["impressions"] for item in pages), 2),
        }
        totals["ctr"] = round(safe_div(totals["clicks"], totals["impressions"]) * 100, 2)
        totals["avg_position"] = round(sum(item["position"] for item in pages) / max(1, len(pages)), 2)
        totals["pages"] = len(pages)
        totals["queries"] = len(queries)
        totals["opportunities"] = len([item for item in pages if item["opportunity_score"] >= 55])
        recommendations = []
        low_ctr = [item for item in pages if item["impressions"] >= 250 and item["ctr"] < 4]
        if low_ctr:
            recommendations.append(f"Review titles/meta descriptions for {len(low_ctr)} high-impression pages with low CTR.")
        unmapped = [item for item in pages if item["mapping_status"] == "unmapped"]
        if unmapped:
            recommendations.append(f"Add {len(unmapped)} search-visible pages to the registry to improve SEO intelligence mapping.")
        striking = [item for item in pages if 6 <= item["position"] <= 20]
        if striking:
            recommendations.append(f"Strengthen internal links and article-map context for {len(striking)} pages ranking near positions 6–20.")
        if topics:
            recommendations.append(f"Highest search opportunity topic: {topics[0]['topic']}.")
        if not recommendations:
            recommendations.append("Search visibility is stable; monitor topic momentum and compare against GA4 engagement.")
        return {
            "ok": True,
            "source": "search-console" if self.enabled else "sample-search",
            "generated_at": utc_now(),
            "date_range": {"start_date": resolve_date(start_date), "end_date": resolve_date(end_date)},
            "site_url": self.settings.search_console_site_url or "https://sustainablecatalyst.com/",
            "totals": totals,
            "top_pages": pages[:25],
            "top_queries": queries[:25],
            "topic_momentum": topics,
            "opportunities": pages[:25],
            "recommendations": recommendations,
            "diagnostics": self.diagnostics(),
            "methodology": {
                "summary": "Search Intelligence combines Google Search Console performance data with the Sustainable Catalyst registry to map queries and pages into article maps, hubs, tools, and conversion opportunities.",
                "score_note": "Opportunity score weights impressions, CTR gap, average position, and registry mapping status. It is directional, not an official Google ranking metric.",
                "privacy_note": "Use internally until public dashboard mode hides operational details and raw administrative recommendations.",
            },
        }
