from __future__ import annotations

import csv
import io
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping, Sequence


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def as_number(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def compact_text(value: Any, limit: int = 220) -> str:
    text = str(value or "").replace("\n", " ").strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def report_shell(report_id: str, title: str, summary: str, source: Any, date_range: Mapping[str, Any] | None = None) -> Dict[str, Any]:
    return {
        "ok": True,
        "report_id": report_id,
        "title": title,
        "summary": summary,
        "generated_at": utc_now(),
        "source": source,
        "date_range": dict(date_range or {}),
        "highlights": [],
        "recommendations": [],
        "sections": [],
        "export_formats": ["json", "markdown", "csv"],
        "methodology": {
            "summary": "Report Generator combines Site Intelligence modules into structured, exportable briefs. Scores and priorities are directional planning aids, not official Google, NASA, NOAA, EPA, or other source metrics.",
            "privacy_note": "Public pages should use public dashboard endpoints. Reports are intended for internal planning unless manually reviewed before publication.",
        },
    }


def add_section(report: Dict[str, Any], section_id: str, title: str, summary: str, rows: Iterable[Any] | None = None, metrics: Mapping[str, Any] | None = None) -> None:
    report.setdefault("sections", []).append({
        "section_id": section_id,
        "title": title,
        "summary": summary,
        "metrics": dict(metrics or {}),
        "rows": list(rows or []),
    })


def site_intelligence_report(dashboard: Mapping[str, Any]) -> Dict[str, Any]:
    totals = dict(dashboard.get("totals") or {})
    coverage = dict(dashboard.get("mapping_coverage") or {})
    date_range = dashboard.get("date_range") or {}
    report = report_shell(
        "site-intelligence",
        "Weekly Site Intelligence Report",
        "A planning report combining GA4 engagement, registry mapping, custom events, and Sustainable Catalyst recommendations.",
        dashboard.get("source", "unknown"),
        date_range,
    )
    views = as_number(totals.get("screen_page_views"))
    users = as_number(totals.get("active_users"))
    report["highlights"] = [
        f"{int(views):,} page views and {int(users):,} active users in the reviewed period.",
        f"Average institutional depth score: {totals.get('avg_institutional_depth_score', 0)}.",
        f"Mapping coverage: {coverage.get('mapping_coverage_rate', totals.get('mapping_coverage_rate', 0))}%.",
    ]
    report["recommendations"] = list(dashboard.get("recommendations") or [])[:8]
    add_section(report, "totals", "Core metrics", "Top-level behavior and mapping totals.", metrics=totals)
    add_section(report, "top_pages", "Top interpreted pages", "High-visibility pages with Sustainable Catalyst interpretation.", rows=dashboard.get("top_pages", [])[:12])
    add_section(report, "unmapped", "Unmapped page candidates", "Pages that should be reviewed for registry coverage.", rows=dashboard.get("unmapped_pages", [])[:12])
    add_section(report, "events", "Event diagnostics", "Repository, Workbench, Research Librarian, and pathway event readiness.", metrics=dashboard.get("event_diagnostics", {}))
    return report


def search_intelligence_report(search: Mapping[str, Any]) -> Dict[str, Any]:
    totals = dict(search.get("totals") or {})
    report = report_shell(
        "search-intelligence",
        "Search Intelligence Report",
        "A report on Google Search Console visibility, query/page performance, search opportunity, and article-map momentum.",
        search.get("source", "unknown"),
        search.get("date_range", {}),
    )
    report["highlights"] = [
        f"{int(as_number(totals.get('impressions'))):,} impressions and {int(as_number(totals.get('clicks'))):,} clicks.",
        f"Average CTR: {totals.get('ctr', 0)}%; average position: {totals.get('avg_position', 0)}.",
        f"Search opportunities detected: {totals.get('opportunities', 0)}.",
    ]
    report["recommendations"] = list(search.get("recommendations") or [])[:8]
    add_section(report, "top_pages", "Search-visible pages", "Pages with search visibility and opportunity scores.", rows=search.get("top_pages", [])[:15])
    add_section(report, "top_queries", "Top query opportunities", "Queries grouped into Sustainable Catalyst topics.", rows=search.get("top_queries", [])[:15])
    add_section(report, "topic_momentum", "Article-map search momentum", "Topic clusters gaining or holding search visibility.", rows=search.get("topic_momentum", [])[:15])
    return report


def content_strategy_report(publishing: Mapping[str, Any]) -> Dict[str, Any]:
    totals = dict(publishing.get("totals") or {})
    report = report_shell(
        "content-strategy",
        "Content Strategy and Publishing Report",
        "A report translating analytics, search, and registry signals into update priorities, promotion ideas, and publishing actions.",
        publishing.get("source", "unknown"),
        publishing.get("date_range", {}),
    )
    report["highlights"] = [
        f"Priority pages: {totals.get('priority_pages', 0)}; rising pages: {totals.get('rising_pages', 0)}; decay pages: {totals.get('decay_pages', 0)}.",
        f"Promotion opportunities: {totals.get('promotion_opportunities', 0)}.",
        f"Article maps reviewed: {totals.get('article_maps_reviewed', 0)}.",
    ]
    report["recommendations"] = list(publishing.get("recommendations") or [])[:8]
    add_section(report, "publishing_queue", "Publishing action queue", "Highest-priority pages and actions.", rows=publishing.get("publishing_queue", [])[:15])
    add_section(report, "newsletter", "Newsletter / Substack candidates", "Pages with strong story potential for external promotion.", rows=publishing.get("newsletter_candidates", [])[:12])
    add_section(report, "promotion", "Promotion opportunities", "Pages suited for LinkedIn, GitHub, Substack, or article-map promotion.", rows=publishing.get("promotion_opportunities", [])[:12])
    add_section(report, "article_maps", "Article-map performance", "Article maps and hubs with publishing-strategy signals.", rows=publishing.get("article_map_performance", [])[:12])
    return report


def external_sources_report(health: Mapping[str, Any], advanced_health: Mapping[str, Any] | None = None) -> Dict[str, Any]:
    connectors = list(health.get("connectors") or [])
    advanced = list((advanced_health or {}).get("connectors") or [])
    all_connectors = connectors + advanced
    report = report_shell(
        "external-sources",
        "External Data Sources Report",
        "A report on public data connectors, source health, fallback behavior, cache status, and dashboard readiness.",
        {"base": health.get("source", "external"), "advanced": (advanced_health or {}).get("source", "advanced-external")},
        {},
    )
    online = [item for item in all_connectors if str(item.get("status", item.get("public_status", ""))).lower() in {"ok", "available", "online", "public_ready"}]
    report["highlights"] = [
        f"{len(all_connectors)} external connectors reviewed.",
        f"{len(online)} connectors reported as available/public-ready or healthy.",
        "Fallback and cache behavior should remain enabled for public pages.",
    ]
    report["recommendations"] = [
        "Keep public dashboards on cached or public-safe snapshot mode unless live source latency is acceptable.",
        "Add optional EIA/EPA credentials only through Render environment variables when live source coverage is needed.",
        "Review source notes before using external data summaries in public-facing pages or reports.",
    ]
    add_section(report, "connector_health", "Connector health", "Base and advanced external source status.", rows=all_connectors)
    add_section(report, "source_notes", "Source notes", "Notes from the connector layer.", rows=health.get("source_notes", []) or health.get("notes", []))
    return report


def climate_energy_report(summary: Mapping[str, Any]) -> Dict[str, Any]:
    indicators = summary.get("indicators") or summary.get("public_indicators") or {}
    report = report_shell(
        "climate-energy",
        "Climate + Energy Snapshot Report",
        "A source-labeled report summarizing climate, energy, emissions, and Earth-observation signals for Sustainable Catalyst dashboards.",
        summary.get("source", "climate-energy"),
        summary.get("date_range", {}),
    )
    report["highlights"] = [
        f"Public status: {summary.get('public_status', summary.get('status', 'review'))}.",
        f"Dashboard mode: {summary.get('mode', summary.get('source', 'snapshot'))}.",
        "Climate/energy summaries are directional and should include source notes when published.",
    ]
    report["recommendations"] = list(summary.get("recommendations") or summary.get("review_notes") or [])[:8]
    add_section(report, "indicators", "Climate and energy indicators", "Public-safe climate/energy signal summary.", metrics=indicators if isinstance(indicators, Mapping) else {})
    add_section(report, "sources", "External source status", "Source-specific data and cache/fallback notes.", rows=summary.get("sources", []) or summary.get("source_notes", []))
    add_section(report, "linked_resources", "Linked Sustainable Catalyst resources", "Article maps, tools, and dashboard resources connected to this topic.", rows=summary.get("linked_resources", []) or summary.get("linked_tools", []))
    return report


def indexing_report(indexing: Mapping[str, Any]) -> Dict[str, Any]:
    totals = dict(indexing.get("totals") or {})
    report = report_shell(
        "indexing",
        "Registry and Indexing Coverage Report",
        "A structural integrity report comparing sitemap, registry, GA4 visibility, Search Console visibility, 404s, and orphan candidates.",
        indexing.get("source", "indexing"),
        indexing.get("date_range", {}),
    )
    report["highlights"] = [
        f"Total reviewed paths: {totals.get('total_paths', 0)}.",
        f"Coverage rate: {totals.get('coverage_rate', 0)}%; registry/sitemap alignment: {totals.get('registry_sitemap_alignment_rate', 0)}%.",
        f"Diagnostic 404 pages: {totals.get('diagnostic_404_pages', 0)}.",
    ]
    report["recommendations"] = list(indexing.get("recommendations") or [])[:8]
    add_section(report, "coverage", "Coverage rows", "High-priority sitemap, search, GA4, and registry coverage findings.", rows=indexing.get("rows", [])[:20])
    add_section(report, "orphans", "Orphan candidates", "Potential orphan or weakly connected pages.", rows=indexing.get("orphan_candidates", [])[:12])
    add_section(report, "404s", "404 diagnostics", "Not-found pages receiving traffic or search visibility.", rows=indexing.get("four_oh_four", [])[:12])
    return report


def bundle_report(reports: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    return {
        "ok": True,
        "report_id": "site-intelligence-export-bundle",
        "title": "Site Intelligence Export Bundle",
        "summary": "Combined report bundle for Sustainable Catalyst planning, review, and export.",
        "generated_at": utc_now(),
        "reports": list(reports),
        "export_formats": ["json", "markdown", "csv"],
    }


def bundle_manifest_report(available_reports: Sequence[Mapping[str, Any]] | None = None, requested: Sequence[str] | None = None) -> Dict[str, Any]:
    reports = list(available_reports or [])
    requested_list = list(requested or [])
    report = report_shell(
        "site-intelligence-export-bundle",
        "Site Intelligence Export Bundle",
        "A lightweight export manifest for Sustainable Catalyst planning reports. Use individual report endpoints, or request full=true for a complete combined bundle when running outside the WordPress timeout window.",
        {"source": "manifest", "mode": "lightweight"},
        {},
    )
    report["highlights"] = [
        f"{len(reports)} exportable report endpoints are available.",
        "The WordPress shortcode loads a lightweight manifest to avoid proxy timeouts.",
        "Full JSON, Markdown, or CSV exports remain available through individual protected backend report endpoints.",
    ]
    report["recommendations"] = [
        "Use individual report shortcodes for review pages and the export manifest as the navigation/index card.",
        "For large exports, call /reports/export?full=true directly from Terminal or an internal workflow rather than through the WordPress page proxy.",
        "Keep report pages private/internal unless manually reviewed for public release.",
    ]
    add_section(
        report,
        "available_reports",
        "Available report exports",
        "Protected backend report endpoints and supported export formats.",
        rows=reports,
    )
    add_section(
        report,
        "export_modes",
        "Export modes",
        "How to use the export bundle without blocking WordPress page loads.",
        rows=[
            {"name": "Lightweight manifest", "endpoint": "/reports/export", "use": "Default WordPress-safe summary."},
            {"name": "Full bundle", "endpoint": "/reports/export?full=true", "use": "Complete combined payload for Terminal/internal use."},
            {"name": "Markdown", "endpoint": "/reports/export?full=true&format=markdown", "use": "Planning brief or GitHub/Markdown draft."},
            {"name": "CSV", "endpoint": "/reports/export?full=true&format=csv", "use": "Spreadsheet-friendly flattened rows."},
        ],
    )
    report["requested_reports"] = requested_list
    return report


def flatten_rows(report: Mapping[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for key, value in (report.get("date_range") or {}).items():
        rows.append({"section": "date_range", "key": key, "value": value, "detail": ""})
    for index, item in enumerate(report.get("highlights") or [], start=1):
        rows.append({"section": "highlight", "key": str(index), "value": compact_text(item, 500), "detail": ""})
    for index, item in enumerate(report.get("recommendations") or [], start=1):
        rows.append({"section": "recommendation", "key": str(index), "value": compact_text(item, 500), "detail": ""})
    for section in report.get("sections") or []:
        sid = section.get("section_id") or section.get("title") or "section"
        for key, value in (section.get("metrics") or {}).items():
            rows.append({"section": sid, "key": key, "value": compact_text(value, 500), "detail": "metric"})
        for idx, item in enumerate(section.get("rows") or [], start=1):
            if isinstance(item, Mapping):
                title = item.get("title") or item.get("name") or item.get("path") or item.get("query") or item.get("connector_id") or str(idx)
                detail = item.get("status") or item.get("summary") or item.get("recommendations") or item.get("source") or ""
                rows.append({"section": sid, "key": compact_text(title, 160), "value": compact_text(item, 800), "detail": compact_text(detail, 300)})
            else:
                rows.append({"section": sid, "key": str(idx), "value": compact_text(item, 800), "detail": ""})
    return rows


def to_markdown(report: Mapping[str, Any]) -> str:
    if report.get("reports"):
        parts = [f"# {report.get('title', 'Site Intelligence Export Bundle')}", "", compact_text(report.get("summary", ""), 1000), ""]
        for sub in report.get("reports") or []:
            parts.append(to_markdown(sub))
            parts.append("\n---\n")
        return "\n".join(parts).strip() + "\n"

    parts = [f"# {report.get('title', 'Site Intelligence Report')}", "", compact_text(report.get("summary", ""), 1000), ""]
    if report.get("date_range"):
        dr = report.get("date_range") or {}
        parts += [f"**Date range:** {dr.get('start_date', '')} to {dr.get('end_date', '')}", ""]
    if report.get("highlights"):
        parts += ["## Highlights"] + [f"- {compact_text(item, 600)}" for item in report.get("highlights") or []] + [""]
    if report.get("recommendations"):
        parts += ["## Recommendations"] + [f"- {compact_text(item, 600)}" for item in report.get("recommendations") or []] + [""]
    for section in report.get("sections") or []:
        parts += [f"## {section.get('title', 'Section')}", "", compact_text(section.get("summary", ""), 1000), ""]
        for key, value in (section.get("metrics") or {}).items():
            parts.append(f"- **{key}:** {compact_text(value, 400)}")
        if section.get("metrics"):
            parts.append("")
        for item in (section.get("rows") or [])[:15]:
            if isinstance(item, Mapping):
                label = item.get("title") or item.get("name") or item.get("path") or item.get("query") or item.get("connector_id") or "Item"
                parts.append(f"- **{compact_text(label, 180)}** — {compact_text(item, 600)}")
            else:
                parts.append(f"- {compact_text(item, 600)}")
        parts.append("")
    methodology = report.get("methodology") or {}
    if methodology:
        parts += ["## Methodology", "", compact_text(methodology.get("summary", ""), 1000), "", compact_text(methodology.get("privacy_note", ""), 1000), ""]
    return "\n".join(parts).strip() + "\n"


def to_csv(report: Mapping[str, Any]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["report_id", "title", "section", "key", "value", "detail"])
    writer.writeheader()
    if report.get("reports"):
        for sub in report.get("reports") or []:
            for row in flatten_rows(sub):
                writer.writerow({"report_id": sub.get("report_id", ""), "title": sub.get("title", ""), **row})
    else:
        for row in flatten_rows(report):
            writer.writerow({"report_id": report.get("report_id", ""), "title": report.get("title", ""), **row})
    return output.getvalue()
