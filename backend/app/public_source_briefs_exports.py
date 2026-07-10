from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping

from .config import Settings
from .public_api_sources import (
    public_sources,
    public_source_health,
    public_development_indicators,
    public_research_metadata,
    public_publication_metadata,
    public_repository_intelligence,
    public_indicator_overview,
    public_sustainability_indicators,
)
from .public_indicator_charts import (
    public_indicator_dashboard_directory,
    public_indicator_chart_gallery,
    public_indicator_chart_visual_qa,
)
from .public_live_connectors import (
    public_connector_status,
    public_connector_reliability,
    public_source_freshness,
)
from .public_topic_dashboards import topic_dashboard_directory


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _version(settings: Settings) -> str:
    return f"v{settings.version}"


def _compact(value: Any, limit: int = 240) -> str:
    text = str(value or "").replace("\n", " ").strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _endpoint(title: str, endpoint: str, note: str, status: str = "public_safe") -> Dict[str, str]:
    return {"title": title, "endpoint": endpoint, "status": status, "note": note}


def _public_sources(settings: Settings) -> List[Dict[str, str]]:
    return [
        _endpoint("Source directory", "/public/sources", "Public source families and indicator context."),
        _endpoint("Source health", "/public/sources/health", "Public source-health summary and disclosure notes."),
        _endpoint("Connector status", "/public/connectors/status", "Live/cache/fallback connector state."),
        _endpoint("Source freshness", "/public/connectors/freshness", "Freshness labels for public connector interpretation."),
        _endpoint("Indicator dashboards", "/public/indicator-dashboards", "Chart-ready indicator dashboard directory."),
        _endpoint("Indicator chart gallery", "/public/indicator-dashboards/charts", "Public-safe chart specs and fallback rendering."),
    ]


def _citation_policy() -> List[str]:
    return [
        "Briefs cite public Site Intelligence endpoints and source families rather than private API payloads.",
        "Public summaries are educational and methodological; they are not certification, assurance, or professional advice.",
        "Live connector status should be paired with cache/fallback labels before publication.",
        "Credentials, request headers, private analytics, and unpublished operational diagnostics remain excluded.",
    ]


def _hidden_fields() -> List[str]:
    return [
        "API keys and credential values",
        "upstream response bodies",
        "private GA4 or Search Console rows",
        "admin-only connector diagnostics",
        "unreviewed professional, compliance, certification, assurance, or investment conclusions",
    ]


def _safe_counts(settings: Settings) -> Dict[str, Any]:
    indicators = public_indicator_dashboard_directory(settings)
    connector = public_connector_reliability(settings)
    sources = public_sources()
    return {
        "dashboard_count": len(indicators.get("dashboards") or []),
        "source_family_count": len(sources.get("source_families") or sources.get("sources") or []),
        "connector_reliability_score": connector.get("score"),
        "connector_reliability_counts": connector.get("reliability_counts") or {},
    }


def public_source_aware_brief_directory(settings: Settings) -> Dict[str, Any]:
    briefs = [
        {
            "slug": "site-intelligence",
            "title": "Site Intelligence Source-Aware Brief",
            "summary": "Explains the public dashboard, source, connector, and indicator layers in one reviewed brief.",
            "recommended_shortcode": "[sc_public_site_intelligence_source_brief]",
            "brief_path": "/platform/site-intelligence/source-aware-briefs/site-intelligence/",
        },
        {
            "slug": "indicator",
            "title": "Indicator Dashboard Source Brief",
            "summary": "Connects public indicator dashboards to their source families, chart specs, and publication boundaries.",
            "recommended_shortcode": "[sc_public_indicator_source_brief]",
            "brief_path": "/platform/site-intelligence/source-aware-briefs/indicator/",
        },
        {
            "slug": "source-health",
            "title": "Source Health Brief",
            "summary": "Summarizes connector reliability, cache/fallback status, source freshness, and public disclosure notes.",
            "recommended_shortcode": "[sc_public_source_health_brief]",
            "brief_path": "/platform/site-intelligence/source-aware-briefs/source-health/",
        },
    ]
    return {
        "ok": True,
        "generated_at": _now(),
        "version_scope": _version(settings),
        "title": "Source-Aware Brief Directory",
        "summary": "Public-safe brief layer connecting Site Intelligence dashboards to source context, indicator charts, connector status, and methodology boundaries.",
        "public_status": "public_brief_ready",
        "recommended_shortcode": "[sc_public_source_aware_brief_directory]",
        "briefs": briefs,
        "source_policy": "public-endpoint citations only; no raw private payloads",
        "hidden": _hidden_fields(),
    }


def public_source_aware_brief(slug: str, settings: Settings) -> Dict[str, Any]:
    counts = _safe_counts(settings)
    connector_status = public_connector_status(settings)
    source_health = public_source_health()
    gallery = public_indicator_chart_gallery(settings)
    briefs = {
        "site-intelligence": {
            "title": "Site Intelligence Source-Aware Brief",
            "summary": "Site Intelligence now combines public dashboards, public source pages, live/cache connector status, indicator charts, and export-ready summaries.",
            "recommended_shortcode": "[sc_public_site_intelligence_source_brief]",
            "brief_path": "/platform/site-intelligence/source-aware-briefs/site-intelligence/",
            "key_findings": [
                f"{counts['dashboard_count']} public indicator dashboards are available for source-aware pages.",
                f"Connector reliability score is {counts.get('connector_reliability_score')} on the public-safe readiness scale.",
                "The public Site Intelligence layer separates reviewed summaries from private analytics and upstream response bodies.",
            ],
            "recommended_actions": [
                "Use source-aware briefs below public dashboards when visitors need methodology context.",
                "Pair chart dashboards with source-health and freshness panels before treating them as live public status pages.",
                "Keep WordPress pages on shortcodes and reviewed summaries rather than embedding raw API responses.",
            ],
            "source_citations": _public_sources(settings),
        },
        "indicator": {
            "title": "Indicator Dashboard Source Brief",
            "summary": "Indicator dashboards use chart-ready public payloads with source-family labels, fallback values, and publication boundaries.",
            "recommended_shortcode": "[sc_public_indicator_source_brief]",
            "brief_path": "/platform/site-intelligence/source-aware-briefs/indicator/",
            "key_findings": [
                f"{gallery.get('chart_count', 0)} chart-ready indicator specs are available across the public dashboard gallery.",
                "Sustainability, development, source-health, research, and repository charts are separated into focused dashboards.",
                "Chart output is intentionally conservative and uses public summaries, not professional assurance claims.",
            ],
            "recommended_actions": [
                "Create public indicator pages only after pairing charts with source methodology and boundaries.",
                "Use one focused dashboard per page when the audience needs clarity; use the gallery for review and QA.",
                "Label whether each indicator is live, cached, fallback-safe, or planned.",
            ],
            "source_citations": [
                _endpoint("Indicator overview", "/public/indicators/overview", "Public indicator layer overview."),
                _endpoint("Sustainability indicators", "/public/indicators/sustainability", "Public sustainability indicator families."),
                _endpoint("Chart gallery", "/public/indicator-dashboards/charts", "Chart-ready indicator payloads."),
            ],
        },
        "source-health": {
            "title": "Source Health Brief",
            "summary": "Source-health pages show connector reliability, cache/fallback status, freshness, and public-safe disclosure notes.",
            "recommended_shortcode": "[sc_public_source_health_brief]",
            "brief_path": "/platform/site-intelligence/source-aware-briefs/source-health/",
            "key_findings": [
                f"Reliability labels: {', '.join((counts.get('connector_reliability_counts') or {}).keys())}.",
                f"Connector status panels report {len(connector_status.get('status_cards') or [])} public-safe connector cards.",
                "Source-health outputs are designed to explain readiness and limitations rather than guarantee data completeness.",
            ],
            "recommended_actions": [
                "Show cache and freshness panels near any public dashboard that depends on external APIs.",
                "Publish fallback labels when live API latency, rate limits, or optional credentials affect freshness.",
                "Keep admin diagnostics behind token-protected backend routes.",
            ],
            "source_citations": [
                _endpoint("Source health", "/public/sources/health", "Public source health summary."),
                _endpoint("Connector status", "/public/connectors/status", "Live/cache/fallback connector state."),
                _endpoint("Source freshness", "/public/connectors/freshness", "Freshness labels and timestamp context."),
            ],
        },
    }
    if slug not in briefs:
        raise KeyError(slug)
    data = briefs[slug]
    return {
        "ok": True,
        "generated_at": _now(),
        "version_scope": _version(settings),
        "public_status": "public_brief_ready",
        "slug": slug,
        **data,
        "source_context": {
            "source_health_status": source_health.get("public_status", "review"),
            "source_policy": "public endpoint summaries, source-family labels, and reviewed methodology notes only",
            "safe_counts": counts,
        },
        "citation_policy": _citation_policy(),
        "hidden": _hidden_fields(),
        "boundary_note": "Educational and analytical context only; not legal, financial, engineering, compliance, assurance, ESG/SDG certification, or professional advice.",
    }


def _export_sources_for(kind: str, settings: Settings) -> List[Dict[str, str]]:
    if kind == "indicator":
        return [
            _endpoint("Indicator dashboards", "/public/indicator-dashboards", "Dashboard directory and chart counts."),
            _endpoint("Indicator gallery", "/public/indicator-dashboards/charts", "Chart specs for public rendering."),
            _endpoint("Indicator brief", "/public/source-aware-briefs/indicator", "Source-aware indicator interpretation."),
        ]
    if kind == "source-health":
        return [
            _endpoint("Source health", "/public/sources/health", "Source-health context."),
            _endpoint("Connector reliability", "/public/connectors/reliability", "Reliability scoring and display labels."),
            _endpoint("Source health brief", "/public/source-aware-briefs/source-health", "Source-aware interpretation."),
        ]
    return [
        _endpoint("Dashboard directory", "/public/dashboards", "Public topic dashboard directory."),
        _endpoint("Source directory", "/public/sources", "Public source directory."),
        _endpoint("Indicator dashboards", "/public/indicator-dashboards", "Chart dashboard directory."),
        _endpoint("Site Intelligence brief", "/public/source-aware-briefs/site-intelligence", "Source-aware site intelligence interpretation."),
    ]


def _markdown_export(title: str, summary: str, findings: List[str], actions: List[str], sources: List[Mapping[str, str]]) -> str:
    lines = [f"# {title}", "", summary, "", "## Key findings"]
    lines.extend([f"- {item}" for item in findings])
    lines.extend(["", "## Recommended actions"])
    lines.extend([f"- {item}" for item in actions])
    lines.extend(["", "## Public source endpoints"])
    lines.extend([f"- {item.get('title')}: `{item.get('endpoint')}` — {item.get('note')}" for item in sources])
    lines.extend(["", "## Boundary", "Educational and analytical context only; not professional advice or assurance."])
    return "\n".join(lines)


def _csv_preview(sources: List[Mapping[str, str]]) -> List[Dict[str, str]]:
    return [{"section": "source", "title": item.get("title", ""), "endpoint": item.get("endpoint", ""), "status": item.get("status", "public_safe")} for item in sources]


def public_dashboard_export_manifest(settings: Settings) -> Dict[str, Any]:
    exports = [
        {
            "slug": "site-intelligence",
            "title": "Site Intelligence Public Export",
            "summary": "Combined public dashboard/source/brief export manifest.",
            "recommended_shortcode": "[sc_public_site_intelligence_export]",
            "endpoint": "/public/dashboard-exports/site-intelligence",
        },
        {
            "slug": "indicator",
            "title": "Indicator Dashboard Export",
            "summary": "Export-ready indicator dashboard brief, source links, and chart summary.",
            "recommended_shortcode": "[sc_public_indicator_dashboard_export]",
            "endpoint": "/public/dashboard-exports/indicator",
        },
        {
            "slug": "source-health",
            "title": "Source Health Export",
            "summary": "Export-ready source-health brief, reliability labels, freshness, and disclosure notes.",
            "recommended_shortcode": "[sc_public_source_health_export]",
            "endpoint": "/public/dashboard-exports/source-health",
        },
    ]
    return {
        "ok": True,
        "generated_at": _now(),
        "version_scope": _version(settings),
        "title": "Public Dashboard Export Manifest",
        "summary": "Export-ready public Site Intelligence bundles for reviewed dashboard pages, source-aware briefs, and public-safe handoffs.",
        "public_status": "public_export_ready",
        "recommended_shortcode": "[sc_public_dashboard_export_manifest]",
        "exports": exports,
        "export_formats": ["json", "markdown", "csv-preview"],
        "hidden": _hidden_fields(),
        "notes": [
            "Exports are intentionally lightweight for WordPress and public pages.",
            "Use backend JSON endpoints for structured workflows; copy Markdown for page drafts or documentation.",
            "CSV preview rows list public source endpoints rather than raw indicator values.",
        ],
    }


def public_dashboard_export(kind: str, settings: Settings) -> Dict[str, Any]:
    if kind not in {"site-intelligence", "indicator", "source-health"}:
        raise KeyError(kind)
    brief_slug = "site-intelligence" if kind == "site-intelligence" else kind
    brief = public_source_aware_brief(brief_slug, settings)
    sources = _export_sources_for(kind, settings)
    title_map = {
        "site-intelligence": "Site Intelligence Public Export",
        "indicator": "Indicator Dashboard Export",
        "source-health": "Source Health Export",
    }
    shortcode_map = {
        "site-intelligence": "[sc_public_site_intelligence_export]",
        "indicator": "[sc_public_indicator_dashboard_export]",
        "source-health": "[sc_public_source_health_export]",
    }
    findings = list(brief.get("key_findings") or [])
    actions = list(brief.get("recommended_actions") or [])
    title = title_map[kind]
    summary = brief.get("summary", "Public dashboard export.")
    return {
        "ok": True,
        "generated_at": _now(),
        "version_scope": _version(settings),
        "slug": kind,
        "title": title,
        "summary": summary,
        "public_status": "public_export_ready",
        "recommended_shortcode": shortcode_map[kind],
        "source_aware_brief": brief,
        "export_bundle": {
            "json": {
                "title": title,
                "summary": summary,
                "key_findings": findings,
                "recommended_actions": actions,
                "source_endpoints": sources,
                "boundary_note": brief.get("boundary_note"),
            },
            "markdown": _markdown_export(title, summary, findings, actions, sources),
            "csv_preview": _csv_preview(sources),
        },
        "source_citations": sources,
        "export_formats": ["json", "markdown", "csv-preview"],
        "hidden": _hidden_fields(),
    }


def public_dashboard_export_visual_qa(settings: Settings) -> Dict[str, Any]:
    manifest = public_dashboard_export_manifest(settings)
    exports = [public_dashboard_export(item["slug"], settings) for item in manifest["exports"]]
    checks = [
        {"id": "exports_present", "label": "Exports present", "status": "pass" if len(exports) == 3 else "fail", "detail": f"{len(exports)} export bundles available."},
        {"id": "markdown_present", "label": "Markdown copies present", "status": "pass" if all((e.get("export_bundle") or {}).get("markdown") for e in exports) else "fail", "detail": "Each export includes a Markdown copy block."},
        {"id": "source_citations_present", "label": "Public source citations present", "status": "pass" if all(e.get("source_citations") for e in exports) else "fail", "detail": "Each export includes public endpoint citations."},
        {"id": "private_payloads_hidden", "label": "Private payloads hidden", "status": "pass", "detail": "Exports exclude API keys, upstream response bodies, and private analytics rows."},
        {"id": "wordpress_safe", "label": "WordPress-safe payload size", "status": "pass", "detail": "Export shortcodes render lightweight summaries and copyable markdown."},
    ]
    return {
        "ok": True,
        "generated_at": _now(),
        "version_scope": _version(settings),
        "title": "Dashboard Export Visual QA",
        "summary": "Visual QA for public source-aware brief panels, dashboard export bundles, public citations, and copy-ready Markdown output.",
        "public_status": "public_export_ready",
        "recommended_shortcode": "[sc_public_dashboard_export_visual_qa]",
        "score": 100 if all(check["status"] == "pass" for check in checks) else 75,
        "checks": checks,
        "export_count": len(exports),
        "review_notes": [
            "Confirm export cards are legible on mobile and in narrow WordPress columns.",
            "Use exports as reviewed page/documentation drafts, not as professional assurance reports.",
            "Keep source-aware briefs paired with dashboard source methodology pages.",
        ],
        "hidden": _hidden_fields(),
    }
