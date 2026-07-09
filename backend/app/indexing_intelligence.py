from __future__ import annotations

import math
import re
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple
from urllib.error import URLError, HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .config import Settings
from .ga4_client import GA4Client
from .metrics import build_page_metrics
from .registry import ContentRegistry
from .search_console import SearchConsoleClient, norm_page, safe_div

SAMPLE_SITEMAP_URLS = [
    "https://sustainablecatalyst.com/",
    "https://sustainablecatalyst.com/publications/",
    "https://sustainablecatalyst.com/research-library/",
    "https://sustainablecatalyst.com/workbench/",
    "https://sustainablecatalyst.com/research-librarian-ai/",
    "https://sustainablecatalyst.com/decision-studio/",
    "https://sustainablecatalyst.com/linear-algebra-for-systems-modeling/",
    "https://sustainablecatalyst.com/algorithms-computational-reasoning/",
    "https://sustainablecatalyst.com/international-law/",
    "https://sustainablecatalyst.com/meaning/",
    "https://sustainablecatalyst.com/channel/",
    "https://sustainablecatalyst.com/platform/",
]

SYSTEM_URL_PATTERNS = (
    "/wp-admin/",
    "/wp-json/",
    "/wp-content/",
    "/xmlrpc.php",
    "/feed/",
    "/comments/",
    "/author/",
    "?",
)

ARCHIVE_PATTERNS = (
    "/category/",
    "/tag/",
    "/author/",
    "/archives/",
)

NOT_FOUND_TITLE_PATTERNS = ("page not found", "404", "not found")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_url_to_path(value: str, base_url: str = "https://sustainablecatalyst.com") -> str:
    return norm_page(value or "/")


def is_system_path(path: str) -> bool:
    text = (path or "").lower()
    return any(pattern in text for pattern in SYSTEM_URL_PATTERNS)


def is_archive_path(path: str) -> bool:
    text = (path or "").lower()
    return any(pattern in text for pattern in ARCHIVE_PATTERNS)


def url_kind(path: str, title: str = "") -> str:
    lower_title = (title or "").lower()
    lower_path = (path or "").lower()
    if any(term in lower_title for term in NOT_FOUND_TITLE_PATTERNS) or "404" in lower_path:
        return "404"
    if is_system_path(path):
        return "system"
    if is_archive_path(path) or lower_path.endswith("/category/") or lower_path.endswith("/tag/"):
        return "archive"
    if lower_path == "/":
        return "home"
    return "content"


def _http_get_text(url: str, timeout: int) -> str:
    request = Request(url, headers={"User-Agent": "SustainableCatalystSiteIntelligence/0.3.2"})
    with urlopen(request, timeout=timeout) as response:  # noqa: S310 - configured URL, read-only fetch.
        return response.read().decode("utf-8", errors="replace")


def _xml_namespace(root: ET.Element) -> str:
    match = re.match(r"\{([^}]+)\}", root.tag)
    return match.group(1) if match else ""


def _find_all(root: ET.Element, local_name: str) -> List[ET.Element]:
    ns = _xml_namespace(root)
    if ns:
        return root.findall(f".//{{{ns}}}{local_name}")
    return root.findall(f".//{local_name}")


def parse_sitemap_xml(xml_text: str) -> Tuple[str, List[str]]:
    root = ET.fromstring(xml_text)
    tag = root.tag.split("}")[-1]
    locs = [node.text.strip() for node in _find_all(root, "loc") if node.text and node.text.strip()]
    if tag == "sitemapindex":
        return "sitemapindex", locs
    return "urlset", locs


class SitemapFetcher:
    def __init__(self, settings: Settings):
        self.settings = settings

    @property
    def enabled(self) -> bool:
        return bool(self.settings.sitemap_live and self.settings.sitemap_url)

    def diagnostics(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "sitemap_url": self.settings.sitemap_url,
            "max_urls": self.settings.sitemap_max_urls,
            "timeout_seconds": self.settings.sitemap_timeout_seconds,
        }

    def fetch(self, force_sample: bool = False) -> Dict[str, Any]:
        if force_sample or not self.enabled:
            return self._sample("Sitemap live mode is disabled or not configured.")
        try:
            urls = self._fetch_recursive(self.settings.sitemap_url, depth=0, seen=set())
            unique_urls = sorted(set(urls))[: self.settings.sitemap_max_urls]
            return self._from_urls(unique_urls, source="sitemap-live", message="Sitemap fetched successfully.")
        except Exception as exc:  # noqa: BLE001
            sample = self._sample(f"Live sitemap fetch failed; using sample fallback. {exc.__class__.__name__}: {str(exc)[:180]}")
            sample["diagnostics"]["last_error_type"] = exc.__class__.__name__
            sample["diagnostics"]["last_error_message"] = str(exc)[:500]
            return sample

    def _fetch_recursive(self, url: str, depth: int, seen: Set[str]) -> List[str]:
        if depth > 1 or url in seen:
            return []
        seen.add(url)
        xml_text = _http_get_text(url, timeout=self.settings.sitemap_timeout_seconds)
        kind, locs = parse_sitemap_xml(xml_text)
        if kind == "urlset":
            return locs
        output: List[str] = []
        for loc in locs[:30]:
            output.extend(self._fetch_recursive(loc, depth=depth + 1, seen=seen))
            if len(output) >= self.settings.sitemap_max_urls:
                break
        return output[: self.settings.sitemap_max_urls]

    def _sample(self, message: str) -> Dict[str, Any]:
        return self._from_urls(SAMPLE_SITEMAP_URLS, source="sample-sitemap", message=message)

    def _from_urls(self, urls: List[str], source: str, message: str) -> Dict[str, Any]:
        base = self.settings.site_base_url
        rows = []
        for url in urls:
            path = normalize_url_to_path(url, base)
            if is_system_path(path):
                continue
            rows.append({
                "url": url,
                "path": path,
                "kind": url_kind(path),
            })
        # Deduplicate by path while preserving first URL.
        seen_paths: Set[str] = set()
        unique_rows: List[Dict[str, Any]] = []
        for row in rows:
            if row["path"] in seen_paths:
                continue
            seen_paths.add(row["path"])
            unique_rows.append(row)
        kind_counts = Counter(row["kind"] for row in unique_rows)
        return {
            "ok": True,
            "source": source,
            "generated_at": utc_now(),
            "message": message,
            "sitemap_url": self.settings.sitemap_url,
            "total_urls": len(unique_rows),
            "kind_counts": dict(kind_counts),
            "urls": unique_rows,
            "diagnostics": self.diagnostics(),
        }


def _path_set_from_registry(registry: ContentRegistry) -> Set[str]:
    return {ContentRegistry._norm(item.url_path) for item in registry.all_items() if item.url_path}


def _path_map_from_ga4(ga4: GA4Client, registry: ContentRegistry, start_date: str, end_date: str) -> Dict[str, Dict[str, Any]]:
    metrics = build_page_metrics(ga4.page_report(start_date, end_date), ga4.event_report(start_date, end_date), registry)
    return {ContentRegistry._norm(metric.path): metric.model_dump() for metric in metrics}


def _path_map_from_search(client: SearchConsoleClient, registry: ContentRegistry, start_date: str, end_date: str) -> Dict[str, Dict[str, Any]]:
    return {ContentRegistry._norm(item.get("page", "/")): item for item in client.page_summary(registry, start_date=start_date, end_date=end_date)}


def coverage_score(in_sitemap: bool, in_registry: bool, in_ga4: bool, in_search: bool, kind: str = "content") -> float:
    score = 0.0
    if in_sitemap:
        score += 25
    if in_registry:
        score += 25
    if in_ga4:
        score += 20
    if in_search:
        score += 20
    if kind == "content":
        score += 10
    elif kind in {"404", "system"}:
        score -= 15
    return round(max(0.0, min(100.0, score)), 2)


def coverage_status(in_sitemap: bool, in_registry: bool, in_ga4: bool, in_search: bool, kind: str) -> str:
    if kind == "404":
        return "diagnostic"
    if in_sitemap and in_registry and (in_ga4 or in_search):
        return "covered"
    if in_search and not in_registry:
        return "search_visible_unmapped"
    if in_ga4 and not in_registry:
        return "traffic_unmapped"
    if in_sitemap and not in_registry:
        return "sitemap_unmapped"
    if in_registry and not in_sitemap:
        return "registry_not_in_sitemap"
    if in_registry and not in_ga4 and not in_search:
        return "registry_inactive"
    return "partial"


def recommendations_for_row(row: Dict[str, Any]) -> List[str]:
    recs: List[str] = []
    status = row["status"]
    kind = row["kind"]
    if kind == "404" or row.get("title", "").lower().find("page not found") >= 0:
        recs.append("Investigate this 404 signal; add redirects or repair internal links if the URL receives traffic or impressions.")
    if status in {"search_visible_unmapped", "traffic_unmapped", "sitemap_unmapped"}:
        recs.append("Add this page to the Site Intelligence registry or improve inference rules so custom metrics classify it correctly.")
    if status == "registry_not_in_sitemap":
        recs.append("Confirm whether this registered page should be included in the XML sitemap or intentionally excluded.")
    if status == "registry_inactive":
        recs.append("Review whether this registered page needs internal links, search optimization, or publication cleanup.")
    if row.get("search_impressions", 0) and not row.get("in_sitemap"):
        recs.append("Search-visible page is not in the fetched sitemap; check sitemap coverage and canonical URL settings.")
    if row.get("ga4_views", 0) and not row.get("in_sitemap"):
        recs.append("Traffic-visible page is not in the fetched sitemap; verify canonical routing and sitemap inclusion.")
    if row.get("in_sitemap") and not row.get("in_registry") and kind == "archive":
        recs.append("Archive URL appears in the sitemap/visibility layer; consider whether archives should be indexed or routed to curated hubs.")
    if not recs:
        recs.append("Coverage looks structurally acceptable; continue monitoring against Search Console and GA4.")
    return recs[:4]


def indexing_intelligence(
    settings: Settings,
    registry: ContentRegistry,
    ga4: GA4Client,
    search_client: SearchConsoleClient,
    start_date: str = "28daysAgo",
    end_date: str = "yesterday",
    sitemap_only: bool = False,
) -> Dict[str, Any]:
    sitemap = SitemapFetcher(settings).fetch()
    sitemap_paths = {row["path"]: row for row in sitemap.get("urls", [])}
    registry_paths = _path_set_from_registry(registry)
    ga4_pages = {} if sitemap_only else _path_map_from_ga4(ga4, registry, start_date, end_date)
    search_pages = {} if sitemap_only else _path_map_from_search(search_client, registry, start_date, end_date)
    all_paths = sorted(set(sitemap_paths) | registry_paths | set(ga4_pages) | set(search_pages))

    rows: List[Dict[str, Any]] = []
    for path in all_paths:
        ga4_item = ga4_pages.get(path, {})
        search_item = search_pages.get(path, {})
        registry_match = registry.resolve(path, ga4_item.get("title", "") or search_item.get("title", ""))
        kind = url_kind(path, ga4_item.get("title", "") or search_item.get("title", ""))
        in_sitemap = path in sitemap_paths
        in_registry = path in registry_paths or registry_match.status in {"explicit", "inferred"}
        in_ga4 = path in ga4_pages
        in_search = path in search_pages
        status = coverage_status(in_sitemap, in_registry, in_ga4, in_search, kind)
        row = {
            "path": path,
            "title": ga4_item.get("title") or search_item.get("title") or (registry_match.item.title if registry_match.item else path),
            "kind": kind,
            "hub": registry_match.item.hub if registry_match.item else "Unmapped",
            "article_map": registry_match.item.article_map if registry_match.item else None,
            "mapping_status": registry_match.status,
            "mapping_confidence": registry_match.confidence,
            "in_sitemap": in_sitemap,
            "in_registry": in_registry,
            "in_ga4": in_ga4,
            "in_search_console": in_search,
            "status": status,
            "coverage_score": coverage_score(in_sitemap, in_registry, in_ga4, in_search, kind),
            "ga4_views": ga4_item.get("screen_page_views", 0),
            "ga4_active_users": ga4_item.get("active_users", 0),
            "search_clicks": search_item.get("clicks", 0),
            "search_impressions": search_item.get("impressions", 0),
            "search_ctr": search_item.get("ctr", 0),
            "search_position": search_item.get("position", 0),
        }
        row["recommendations"] = recommendations_for_row(row)
        rows.append(row)

    rows_sorted = sorted(
        rows,
        key=lambda item: (
            item["kind"] == "404",
            item["status"] in {"search_visible_unmapped", "traffic_unmapped", "sitemap_unmapped"},
            item.get("search_impressions", 0) + item.get("ga4_views", 0),
            -item["coverage_score"],
        ),
        reverse=True,
    )
    status_counts = Counter(row["status"] for row in rows)
    kind_counts = Counter(row["kind"] for row in rows)
    totals = {
        "total_paths": len(rows),
        "sitemap_urls": len(sitemap_paths),
        "registry_urls": len(registry_paths),
        "ga4_pages": len(ga4_pages),
        "search_console_pages": len(search_pages),
        "covered_pages": status_counts.get("covered", 0),
        "unmapped_visible_pages": status_counts.get("search_visible_unmapped", 0) + status_counts.get("traffic_unmapped", 0),
        "sitemap_unmapped_pages": status_counts.get("sitemap_unmapped", 0),
        "registry_not_in_sitemap_pages": status_counts.get("registry_not_in_sitemap", 0),
        "diagnostic_404_pages": kind_counts.get("404", 0),
    }
    totals["coverage_rate"] = round(safe_div(totals["covered_pages"], max(1, totals["total_paths"])) * 100, 2)
    totals["registry_sitemap_alignment_rate"] = round(safe_div(len(registry_paths & set(sitemap_paths)), max(1, len(registry_paths | set(sitemap_paths)))) * 100, 2)
    recommendations: List[str] = []
    if totals["unmapped_visible_pages"]:
        recommendations.append(f"Map {totals['unmapped_visible_pages']} GA4/Search-visible pages into the registry or inference rules.")
    if totals["sitemap_unmapped_pages"]:
        recommendations.append(f"Review {totals['sitemap_unmapped_pages']} sitemap URLs that are not currently classified by the registry.")
    if totals["registry_not_in_sitemap_pages"]:
        recommendations.append(f"Check {totals['registry_not_in_sitemap_pages']} registry pages that were not found in the fetched sitemap.")
    if totals["diagnostic_404_pages"]:
        recommendations.append("Investigate 404 URLs receiving traffic or search visibility and repair redirects/internal links.")
    if not recommendations:
        recommendations.append("Sitemap, registry, GA4, and Search Console coverage are structurally aligned for the reviewed dataset.")

    return {
        "ok": True,
        "generated_at": utc_now(),
        "source": {
            "sitemap": sitemap.get("source"),
            "ga4": "ga4" if ga4.enabled else "sample-ga4",
            "search": "search-console" if search_client.enabled else "sample-search",
        },
        "date_range": {"start_date": start_date, "end_date": end_date},
        "sitemap": {k: v for k, v in sitemap.items() if k != "urls"},
        "totals": totals,
        "status_counts": dict(status_counts),
        "kind_counts": dict(kind_counts),
        "coverage_rows": rows_sorted,
        "recommendations": recommendations,
        "methodology": {
            "summary": "Indexing Intelligence compares XML sitemap URLs, Site Intelligence registry entries, GA4 page visibility, and Search Console search visibility.",
            "coverage_note": "Coverage scores are directional operating metrics, not Google ranking or index-status metrics.",
            "public_note": "Keep detailed 404, orphan, and registry diagnostics private until public dashboard mode is enabled.",
        },
    }


def sitemap_report(settings: Settings, registry: ContentRegistry) -> Dict[str, Any]:
    sitemap = SitemapFetcher(settings).fetch()
    registry_paths = _path_set_from_registry(registry)
    rows = []
    for item in sitemap.get("urls", []):
        path = item["path"]
        match = registry.resolve(path)
        row = dict(item)
        row.update({
            "in_registry": path in registry_paths or match.status in {"explicit", "inferred"},
            "mapping_status": match.status,
            "hub": match.item.hub if match.item else "Unmapped",
            "article_map": match.item.article_map if match.item else None,
        })
        rows.append(row)
    unmapped = [row for row in rows if not row["in_registry"]]
    return {
        "ok": True,
        "generated_at": utc_now(),
        "source": sitemap.get("source"),
        "sitemap_url": sitemap.get("sitemap_url"),
        "total_urls": len(rows),
        "mapped_urls": len(rows) - len(unmapped),
        "unmapped_urls": len(unmapped),
        "mapping_rate": round(safe_div(len(rows) - len(unmapped), max(1, len(rows))) * 100, 2),
        "kind_counts": sitemap.get("kind_counts", {}),
        "urls": rows[: settings.sitemap_max_urls],
        "unmapped": unmapped[:50],
        "diagnostics": sitemap.get("diagnostics", {}),
        "message": sitemap.get("message", ""),
    }


def orphan_candidates(intel: Dict[str, Any], limit: int = 25) -> Dict[str, Any]:
    candidates = []
    for row in intel.get("coverage_rows", []):
        if row["status"] in {"registry_not_in_sitemap", "registry_inactive", "partial"} and row.get("in_registry"):
            if not row.get("in_ga4") and not row.get("in_search_console"):
                candidate = dict(row)
                candidate["orphan_reason"] = "Registered page has no GA4 or Search Console visibility in the reviewed range."
                candidates.append(candidate)
            elif row.get("in_registry") and not row.get("in_sitemap"):
                candidate = dict(row)
                candidate["orphan_reason"] = "Registered page was not found in the fetched sitemap."
                candidates.append(candidate)
    return {
        "ok": True,
        "generated_at": utc_now(),
        "source": intel.get("source", {}),
        "date_range": intel.get("date_range", {}),
        "count": len(candidates),
        "candidates": candidates[:limit],
        "recommendations": [
            "Review orphan candidates before deleting or redirecting; some may be intentional private, draft, archive, or newly published pages.",
            "Use internal links, sitemap inclusion, or registry cleanup depending on whether each page should remain part of the public knowledge system.",
        ],
    }


def four_oh_four_report(intel: Dict[str, Any], limit: int = 25) -> Dict[str, Any]:
    rows = [row for row in intel.get("coverage_rows", []) if row.get("kind") == "404" or "not found" in (row.get("title") or "").lower()]
    rows = sorted(rows, key=lambda item: item.get("ga4_views", 0) + item.get("search_impressions", 0), reverse=True)
    return {
        "ok": True,
        "generated_at": utc_now(),
        "source": intel.get("source", {}),
        "date_range": intel.get("date_range", {}),
        "count": len(rows),
        "urls": rows[:limit],
        "recommendations": [
            "Repair or redirect 404 URLs that receive GA4 traffic or Search Console impressions.",
            "Check whether archive/category URLs are being surfaced instead of curated hubs.",
            "Use this report internally; do not expose 404 diagnostics on public dashboards.",
        ],
    }


def indexing_recommendations(intel: Dict[str, Any], limit: int = 25) -> Dict[str, Any]:
    rows = intel.get("coverage_rows", [])
    prioritized = sorted(
        rows,
        key=lambda row: (
            row.get("kind") == "404",
            row.get("status") in {"search_visible_unmapped", "traffic_unmapped", "sitemap_unmapped", "registry_not_in_sitemap"},
            row.get("search_impressions", 0) + row.get("ga4_views", 0),
        ),
        reverse=True,
    )[:limit]
    action_queue = []
    for row in prioritized:
        action_queue.append({
            "path": row["path"],
            "title": row.get("title", row["path"]),
            "status": row["status"],
            "kind": row["kind"],
            "priority_score": round((100 - row.get("coverage_score", 0)) + min(50, math.log10(max(1, row.get("search_impressions", 0) + row.get("ga4_views", 0))) * 15), 2),
            "signals": {
                "ga4_views": row.get("ga4_views", 0),
                "search_impressions": row.get("search_impressions", 0),
                "in_sitemap": row.get("in_sitemap"),
                "in_registry": row.get("in_registry"),
                "in_ga4": row.get("in_ga4"),
                "in_search_console": row.get("in_search_console"),
            },
            "actions": row.get("recommendations", []),
        })
    action_queue = sorted(action_queue, key=lambda item: item["priority_score"], reverse=True)
    return {
        "ok": True,
        "generated_at": utc_now(),
        "source": intel.get("source", {}),
        "summary": intel.get("totals", {}),
        "recommendations": intel.get("recommendations", []),
        "action_queue": action_queue,
        "methodology": intel.get("methodology", {}),
    }
