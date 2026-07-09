from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from .config import Settings
from .registry import ContentRegistry


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_exists(path_value: str) -> bool:
    try:
        path = Path(path_value)
        if not path.is_absolute():
            candidates = [
                Path.cwd() / path,
                Path.cwd() / "backend" / path.name,
                Path.cwd() / "data" / path.name,
            ]
            return any(candidate.exists() for candidate in candidates)
        return path.exists()
    except Exception:
        return False


def _load_external_registry(settings: Settings) -> Dict[str, Any]:
    path = Path(settings.external_registry_path)
    candidates = [path] if path.is_absolute() else [Path.cwd() / path, Path.cwd() / "backend" / path.name, Path.cwd() / "data" / path.name]
    for candidate in candidates:
        if candidate.exists():
            try:
                return json.loads(candidate.read_text(encoding="utf-8"))
            except Exception as exc:  # noqa: BLE001
                return {"version": "unknown", "generated_at": _now(), "connectors": [], "error": str(exc)}
    return {"version": "unknown", "generated_at": _now(), "connectors": []}


def _shortcodes() -> List[Dict[str, Any]]:
    return [
        {"shortcode": "[sc_site_intelligence_dashboard]", "category": "core", "visibility": "private", "endpoint": "/intelligence/dashboard", "purpose": "Main private dashboard for analytics interpretation."},
        {"shortcode": "[sc_site_intelligence_page]", "category": "core", "visibility": "private", "endpoint": "/intelligence/page", "purpose": "Page-level intelligence for the current page."},
        {"shortcode": "[sc_site_intelligence_unmapped]", "category": "registry", "visibility": "private", "endpoint": "/intelligence/unmapped", "purpose": "Unmapped GA4 pages and registry suggestions."},
        {"shortcode": "[sc_site_intelligence_events]", "category": "events", "visibility": "private", "endpoint": "/intelligence/event-diagnostics", "purpose": "Custom event diagnostics and conversion readiness."},
        {"shortcode": "[sc_site_intelligence_opportunities]", "category": "events", "visibility": "private", "endpoint": "/intelligence/page-opportunities", "purpose": "Pages that need stronger calls to action or pathway structure."},
        {"shortcode": "[sc_external_data_health]", "category": "external sources", "visibility": "private", "endpoint": "/external/health", "purpose": "Pilot external connector health."},
        {"shortcode": "[sc_advanced_external_data_health]", "category": "external sources", "visibility": "private", "endpoint": "/external/advanced/health", "purpose": "Advanced external connector health."},
        {"shortcode": "[sc_climate_energy_intelligence]", "category": "dashboard", "visibility": "private", "endpoint": "/intelligence/dashboards/climate-energy", "purpose": "Private Climate + Energy Intelligence dashboard."},
        {"shortcode": "[sc_environmental_monitoring_intelligence]", "category": "dashboard", "visibility": "private", "endpoint": "/intelligence/dashboards/environmental-monitoring", "purpose": "Environmental monitoring dashboard."},
        {"shortcode": "[sc_urban_resilience_intelligence]", "category": "dashboard", "visibility": "private", "endpoint": "/intelligence/dashboards/urban-resilience", "purpose": "Urban resilience dashboard."},
        {"shortcode": "[sc_biodiversity_land_use_intelligence]", "category": "dashboard", "visibility": "private", "endpoint": "/intelligence/dashboards/biodiversity-land-use", "purpose": "Biodiversity and land-use dashboard."},
        {"shortcode": "[sc_energy_systems_intelligence]", "category": "dashboard", "visibility": "private", "endpoint": "/intelligence/dashboards/energy-systems", "purpose": "Energy systems dashboard."},
        {"shortcode": "[sc_search_intelligence]", "category": "search", "visibility": "private", "endpoint": "/intelligence/search", "purpose": "Search Console intelligence."},
        {"shortcode": "[sc_search_opportunities]", "category": "search", "visibility": "private", "endpoint": "/search/opportunities", "purpose": "Search opportunity queue."},
        {"shortcode": "[sc_metadata_intelligence]", "category": "seo", "visibility": "private", "endpoint": "/seo/metadata", "purpose": "Title and metadata review."},
        {"shortcode": "[sc_internal_link_intelligence]", "category": "seo", "visibility": "private", "endpoint": "/seo/internal-links", "purpose": "Internal-link recommendations."},
        {"shortcode": "[sc_seo_recommendations]", "category": "seo", "visibility": "private", "endpoint": "/seo/recommendations", "purpose": "Combined SEO recommendation queue."},
        {"shortcode": "[sc_indexing_intelligence]", "category": "indexing", "visibility": "private", "endpoint": "/intelligence/indexing", "purpose": "Sitemap, registry, search, and analytics coverage."},
        {"shortcode": "[sc_sitemap_coverage]", "category": "indexing", "visibility": "private", "endpoint": "/indexing/sitemap", "purpose": "Sitemap-to-registry coverage."},
        {"shortcode": "[sc_404_intelligence]", "category": "indexing", "visibility": "private", "endpoint": "/indexing/404s", "purpose": "404 and routing diagnostics."},
        {"shortcode": "[sc_site_intelligence_public_landing]", "category": "public", "visibility": "public", "endpoint": "/public/landing-page", "purpose": "Public Site Intelligence landing section."},
        {"shortcode": "[sc_site_intelligence_public_flagship]", "category": "public", "visibility": "public", "endpoint": "wordpress-local", "purpose": "Complete polished public dashboard page preset."},
        {"shortcode": "[sc_site_intelligence_public_page_builder]", "category": "public builder", "visibility": "private-review", "endpoint": "/public/page-builder", "purpose": "Public page-builder guidance, presets, and release checklist."},
        {"shortcode": "[sc_public_dashboard_shortcode_bundle]", "category": "public builder", "visibility": "private-review", "endpoint": "/public/page-builder/shortcodes", "purpose": "Copy-ready public dashboard shortcode bundles."},
        {"shortcode": "[sc_public_dashboard_visual_qa]", "category": "public builder", "visibility": "private-review", "endpoint": "/public/page-builder/visual-qa", "purpose": "Visual QA, copy polish, mobile review, and launch-readiness guidance for the public flagship dashboard."},
        {"shortcode": "[sc_public_site_intelligence]", "category": "public", "visibility": "public", "endpoint": "/public/dashboard", "purpose": "Sanitized public dashboard summary."},
        {"shortcode": "[sc_public_knowledge_overview]", "category": "public", "visibility": "public", "endpoint": "/public/knowledge-overview", "purpose": "Public knowledge architecture overview."},
        {"shortcode": "[sc_public_climate_energy_summary]", "category": "public", "visibility": "public", "endpoint": "/public/climate-energy-summary", "purpose": "Public-safe climate and energy snapshot."},
        {"shortcode": "[sc_public_methodology]", "category": "public", "visibility": "public", "endpoint": "/public/methodology", "purpose": "Public methodology and limitations."},
        {"shortcode": "[sc_public_dashboard_directory]", "category": "public topic", "visibility": "public", "endpoint": "/public/dashboards", "purpose": "Public Site Intelligence dashboard directory."},
        {"shortcode": "[sc_public_dashboard_navigation]", "category": "public topic", "visibility": "public", "endpoint": "/public/navigation", "purpose": "Reusable dashboard navigation for public topic pages."},
        {"shortcode": "[sc_public_climate_energy_dashboard]", "category": "public topic", "visibility": "public", "endpoint": "/public/dashboards/climate-energy", "purpose": "Public Climate + Energy topic dashboard."},
        {"shortcode": "[sc_public_environmental_monitoring_dashboard]", "category": "public topic", "visibility": "public", "endpoint": "/public/dashboards/environmental-monitoring", "purpose": "Public Environmental Monitoring topic dashboard."},
        {"shortcode": "[sc_public_biodiversity_land_use_dashboard]", "category": "public topic", "visibility": "public", "endpoint": "/public/dashboards/biodiversity-land-use", "purpose": "Public Biodiversity + Land Use topic dashboard."},
        {"shortcode": "[sc_public_knowledge_system_dashboard]", "category": "public topic", "visibility": "public", "endpoint": "/public/dashboards/knowledge-system", "purpose": "Public Knowledge System topic dashboard."},
        {"shortcode": "[sc_public_search_discovery_dashboard]", "category": "public topic", "visibility": "public", "endpoint": "/public/dashboards/search-discovery", "purpose": "Public Search + Discovery topic dashboard."},
        {"shortcode": "[sc_public_source_methodology]", "category": "public topic", "visibility": "public", "endpoint": "/public/source-methodology", "purpose": "Public source methodology and dashboard boundaries."},
        {"shortcode": "[sc_public_topic_page_templates]", "category": "public builder", "visibility": "private-review", "endpoint": "/public/page-templates", "purpose": "Copy-ready metadata and section guidance for public topic pages."},
        {"shortcode": "[sc_public_topic_page_visual_qa]", "category": "public builder", "visibility": "private-review", "endpoint": "/public/topic-page-visual-qa", "purpose": "Public topic page navigation and visual QA."},
        {"shortcode": "[sc_public_api_sources]", "category": "public sources", "visibility": "public", "endpoint": "/public/sources", "purpose": "Public-safe API source family overview for live/cached/fallback source expansion."},
        {"shortcode": "[sc_public_source_health]", "category": "public sources", "visibility": "public", "endpoint": "/public/sources/health", "purpose": "Public source-health summary with live/cached/fallback/planned status labels."},
        {"shortcode": "[sc_public_development_indicators]", "category": "public sources", "visibility": "public", "endpoint": "/public/sources/development-indicators", "purpose": "World Bank, OECD, and UN/SDG indicator context for public dashboards."},
        {"shortcode": "[sc_public_research_metadata]", "category": "public sources", "visibility": "public", "endpoint": "/public/sources/research-metadata", "purpose": "OpenAlex and Crossref research metadata context for public source discovery."},
        {"shortcode": "[sc_public_publication_metadata]", "category": "public sources", "visibility": "public", "endpoint": "/public/sources/publications", "purpose": "Publication and DOI metadata context for public bibliography/source panels."},
        {"shortcode": "[sc_public_repository_intelligence]", "category": "public sources", "visibility": "public", "endpoint": "/public/sources/repositories", "purpose": "GitHub repository intelligence for public code-infrastructure visibility."},
        {"shortcode": "[sc_public_indicator_overview]", "category": "public sources", "visibility": "public", "endpoint": "/public/indicators/overview", "purpose": "Public indicator overview across live/cached/fallback source families."},
        {"shortcode": "[sc_public_sustainability_indicators]", "category": "public sources", "visibility": "public", "endpoint": "/public/indicators/sustainability", "purpose": "Sustainability indicator context across environment, development, research, and repository layers."},
        {"shortcode": "[sc_public_dashboard_readiness]", "category": "public readiness", "visibility": "private", "endpoint": "/intelligence/public-readiness", "purpose": "Internal readiness checklist for public dashboards."},
        {"shortcode": "[sc_site_intelligence_report]", "category": "reports", "visibility": "private", "endpoint": "/reports/site-intelligence", "purpose": "Weekly Site Intelligence report."},
        {"shortcode": "[sc_search_intelligence_report]", "category": "reports", "visibility": "private", "endpoint": "/reports/search-intelligence", "purpose": "Search Intelligence report."},
        {"shortcode": "[sc_content_strategy_report]", "category": "reports", "visibility": "private", "endpoint": "/reports/content-strategy", "purpose": "Content strategy and publishing report."},
        {"shortcode": "[sc_external_sources_report]", "category": "reports", "visibility": "private", "endpoint": "/reports/external-sources", "purpose": "External data source report."},
        {"shortcode": "[sc_climate_energy_report]", "category": "reports", "visibility": "private", "endpoint": "/reports/climate-energy", "purpose": "Climate + Energy snapshot report."},
        {"shortcode": "[sc_indexing_report]", "category": "reports", "visibility": "private", "endpoint": "/reports/indexing", "purpose": "Registry and indexing report."},
        {"shortcode": "[sc_report_export_bundle]", "category": "reports", "visibility": "private", "endpoint": "/reports/export", "purpose": "Export manifest and optional report bundle."},
        {"shortcode": "[sc_ai_brief_status]", "category": "ai briefs", "visibility": "private", "endpoint": "/ai/status", "purpose": "AI provider status."},
        {"shortcode": "[sc_ai_site_intelligence_brief]", "category": "ai briefs", "visibility": "private", "endpoint": "/ai/briefs/site-intelligence", "purpose": "AI-assisted site brief."},
        {"shortcode": "[sc_ai_search_brief]", "category": "ai briefs", "visibility": "private", "endpoint": "/ai/briefs/search", "purpose": "AI-assisted search brief."},
        {"shortcode": "[sc_ai_publishing_brief]", "category": "ai briefs", "visibility": "private", "endpoint": "/ai/briefs/publishing", "purpose": "AI-assisted publishing brief."},
        {"shortcode": "[sc_ai_external_sources_brief]", "category": "ai briefs", "visibility": "private", "endpoint": "/ai/briefs/external-sources", "purpose": "AI-assisted external-sources brief."},
        {"shortcode": "[sc_ai_public_dashboard_brief]", "category": "ai briefs", "visibility": "public-review", "endpoint": "/ai/briefs/public-dashboard", "purpose": "Public dashboard brief; local fallback by default in WordPress."},
        {"shortcode": "[sc_site_intelligence_admin_overview]", "category": "admin", "visibility": "private", "endpoint": "/intelligence/admin", "purpose": "Admin overview for registry, modules, sources, and diagnostics."},
        {"shortcode": "[sc_site_intelligence_shortcode_catalog]", "category": "admin", "visibility": "private", "endpoint": "/admin/shortcodes", "purpose": "Shortcode catalog and placement guidance."},
        {"shortcode": "[sc_site_intelligence_module_status]", "category": "admin", "visibility": "private", "endpoint": "/admin/modules", "purpose": "Module and endpoint status matrix."},
        {"shortcode": "[sc_site_intelligence_diagnostic_summary]", "category": "admin", "visibility": "private", "endpoint": "/admin/diagnostic-summary", "purpose": "One-screen operational diagnostic summary."},
        {"shortcode": "[sc_site_intelligence_connection_check]", "category": "admin", "visibility": "private", "endpoint": "/admin/connection-check", "purpose": "Backend, token, registry, source, and public-readiness connection check."},
        {"shortcode": "[sc_site_intelligence_release_status]", "category": "release", "visibility": "private", "endpoint": "/release/status", "purpose": "v1.2.0 public flagship release status, checklist, smoke-test guidance, and launch metadata."},
    ]


def shortcode_catalog() -> Dict[str, Any]:
    rows = _shortcodes()
    category_counts = Counter(item["category"] for item in rows)
    visibility_counts = Counter(item["visibility"] for item in rows)
    return {
        "ok": True,
        "generated_at": _now(),
        "count": len(rows),
        "category_counts": dict(category_counts),
        "visibility_counts": dict(visibility_counts),
        "shortcodes": rows,
        "placement_notes": [
            "Keep private analytics, reports, AI briefs, registry tools, and diagnostics on authenticated/admin-only pages.",
            "Use only public shortcodes on public pages unless a module has been manually reviewed.",
            "Use the admin overview shortcode as the internal control-plane landing section.",
        ],
    }


def module_catalog(settings: Settings) -> List[Dict[str, Any]]:
    return [
        {"id": "core-dashboard", "name": "Core Site Intelligence", "status": "active", "visibility": "private", "shortcodes": ["[sc_site_intelligence_dashboard]", "[sc_site_intelligence_page]"], "endpoints": ["/intelligence/dashboard", "/intelligence/page"], "notes": "GA4-backed when configured; demo fallback otherwise."},
        {"id": "registry-manager", "name": "Registry Manager", "status": "active", "visibility": "private", "shortcodes": ["[sc_site_intelligence_admin_overview]"], "endpoints": ["/admin/registry", "/admin/registry/coverage"], "notes": "Read-only registry control plane in v0.9.0."},
        {"id": "event-diagnostics", "name": "Event and Conversion Diagnostics", "status": "active", "visibility": "private", "shortcodes": ["[sc_site_intelligence_events]", "[sc_site_intelligence_opportunities]"], "endpoints": ["/intelligence/event-diagnostics", "/intelligence/page-opportunities"], "notes": "Custom event and conversion-readiness checks."},
        {"id": "external-connectors", "name": "External Data Connectors", "status": "active", "visibility": "private", "shortcodes": ["[sc_external_data_health]", "[sc_advanced_external_data_health]"], "endpoints": ["/external/health", "/external/advanced/health"], "notes": "External sources use cache/fallback behavior."},
        {"id": "public-dashboard", "name": "Public Dashboard Framework", "status": "active" if settings.public_dashboards_enabled else "disabled", "visibility": "public", "shortcodes": ["[sc_site_intelligence_public_flagship]", "[sc_site_intelligence_public_landing]", "[sc_public_site_intelligence]", "[sc_public_knowledge_overview]", "[sc_public_climate_energy_summary]", "[sc_public_methodology]"], "endpoints": ["/public/page-builder", "/public/landing-page", "/public/dashboard", "/public/knowledge-overview", "/public/climate-energy-summary", "/public/methodology"], "notes": "Sanitized public output and flagship page-builder presets."},
        {"id": "public-topic-dashboards", "name": "Public Topic Dashboards", "status": "active" if settings.public_dashboards_enabled else "disabled", "visibility": "public", "shortcodes": ["[sc_public_dashboard_directory]", "[sc_public_dashboard_navigation]", "[sc_public_climate_energy_dashboard]", "[sc_public_environmental_monitoring_dashboard]", "[sc_public_biodiversity_land_use_dashboard]", "[sc_public_knowledge_system_dashboard]", "[sc_public_search_discovery_dashboard]", "[sc_public_source_methodology]"], "endpoints": ["/public/dashboards", "/public/navigation", "/public/page-templates", "/public/topic-page-visual-qa", "/public/source-methodology"], "notes": "v1.2.0 public topic page system with canonical /platform/site-intelligence/ paths, reusable navigation, templates, and QA."},
        {"id": "public-api-source-layer", "name": "Public API Source Layer", "status": "active" if settings.public_dashboards_enabled else "disabled", "visibility": "public", "shortcodes": ["[sc_public_api_sources]", "[sc_public_source_health]", "[sc_public_development_indicators]", "[sc_public_research_metadata]", "[sc_public_publication_metadata]", "[sc_public_repository_intelligence]", "[sc_public_indicator_overview]", "[sc_public_sustainability_indicators]"], "endpoints": ["/public/sources", "/public/sources/health", "/public/sources/development-indicators", "/public/sources/research-metadata", "/public/sources/publications", "/public/sources/repositories", "/public/indicators/overview", "/public/indicators/sustainability"], "notes": "v1.2.0 public API source expansion with source-health, development indicators, research/publication metadata, repository intelligence, and live/cached/fallback labels."},
        {"id": "public-release-qa", "name": "Public Release QA", "status": "active", "visibility": "private-review", "shortcodes": ["[sc_site_intelligence_public_page_builder]", "[sc_public_dashboard_shortcode_bundle]", "[sc_public_dashboard_visual_qa]"], "endpoints": ["/public/page-builder", "/public/page-builder/shortcodes", "/public/page-builder/visual-qa"], "notes": "Private review layer for visual QA, copy polish, shortcode bundles, and launch readiness."},
        {"id": "search-seo", "name": "Search and SEO Intelligence", "status": "active", "visibility": "private", "shortcodes": ["[sc_search_intelligence]", "[sc_metadata_intelligence]", "[sc_internal_link_intelligence]", "[sc_seo_recommendations]"], "endpoints": ["/intelligence/search", "/seo/metadata", "/seo/internal-links", "/seo/recommendations"], "notes": "Search Console live mode depends on property access."},
        {"id": "indexing", "name": "Sitemap and Indexing Intelligence", "status": "active", "visibility": "private", "shortcodes": ["[sc_indexing_intelligence]", "[sc_sitemap_coverage]", "[sc_404_intelligence]"], "endpoints": ["/intelligence/indexing", "/indexing/sitemap", "/indexing/404s"], "notes": "Compares sitemap, registry, analytics, and search-visible pages."},
        {"id": "publishing", "name": "Publishing Strategy Intelligence", "status": "active", "visibility": "private", "shortcodes": ["[sc_content_strategy_intelligence]", "[sc_topic_momentum]", "[sc_update_priorities]", "[sc_publishing_opportunities]"], "endpoints": ["/publishing/content-strategy", "/publishing/topic-momentum", "/publishing/update-priorities", "/publishing/promotion-opportunities"], "notes": "Turns analytics/search into update and promotion queues."},
        {"id": "reports", "name": "Report Generator", "status": "active", "visibility": "private", "shortcodes": ["[sc_site_intelligence_report]", "[sc_search_intelligence_report]", "[sc_report_export_bundle]"], "endpoints": ["/reports/site-intelligence", "/reports/search-intelligence", "/reports/export"], "notes": "JSON, Markdown, and CSV export support."},
        {"id": "ai-briefs", "name": "AI-Assisted Briefs", "status": "active", "visibility": "private", "shortcodes": ["[sc_ai_brief_status]", "[sc_ai_site_intelligence_brief]", "[sc_ai_search_brief]", "[sc_ai_publishing_brief]", "[sc_ai_external_sources_brief]"], "endpoints": ["/ai/status", "/ai/briefs/site-intelligence", "/ai/briefs/search", "/ai/briefs/publishing", "/ai/briefs/external-sources"], "notes": f"Provider: {settings.ai_provider}; deterministic fallback remains available."},
        {"id": "release-status", "name": "Public Flagship Release", "status": "active", "visibility": "private", "shortcodes": ["[sc_site_intelligence_release_status]", "[sc_site_intelligence_public_flagship]"], "endpoints": ["/release/status", "/release/checklist", "/release/smoke-test", "/release/public-summary"], "notes": "v1.2.0 release-hardening layer for public launch readiness, smoke tests, and final page metadata."},
        {"id": "admin-control", "name": "Admin Control Plane", "status": "active", "visibility": "private", "shortcodes": ["[sc_site_intelligence_admin_overview]", "[sc_site_intelligence_shortcode_catalog]", "[sc_site_intelligence_module_status]"], "endpoints": ["/intelligence/admin", "/admin/modules", "/admin/shortcodes", "/admin/diagnostics"], "notes": "v0.9.x control-plane layer for registry, source, module, and shortcode visibility."},
    ]


def module_manager(settings: Settings) -> Dict[str, Any]:
    modules = module_catalog(settings)
    status_counts = Counter(item["status"] for item in modules)
    visibility_counts = Counter(item["visibility"] for item in modules)
    return {"ok": True, "generated_at": _now(), "version": settings.version, "count": len(modules), "status_counts": dict(status_counts), "visibility_counts": dict(visibility_counts), "modules": modules}


def registry_manager(registry: ContentRegistry) -> Dict[str, Any]:
    items = registry.registry.items
    by_hub: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    hub_counts = Counter()
    type_counts = Counter()
    article_map_counts = Counter()
    missing_repository = 0
    missing_workbench = 0
    missing_next_paths = 0
    for item in items:
        hub_counts[item.hub] += 1
        type_counts[item.content_type] += 1
        if item.article_map:
            article_map_counts[item.article_map] += 1
        if not item.repository_url:
            missing_repository += 1
        if not item.workbench_tool_ids:
            missing_workbench += 1
        if not item.intended_next_paths:
            missing_next_paths += 1
        by_hub[item.hub].append({
            "id": item.id,
            "title": item.title,
            "url_path": item.url_path,
            "content_type": item.content_type,
            "article_map": item.article_map,
            "discipline": item.discipline,
            "repository_url": item.repository_url,
            "workbench_tool_ids": item.workbench_tool_ids,
            "intended_next_paths": item.intended_next_paths,
            "tags": item.tags,
        })
    return {
        "ok": True,
        "generated_at": _now(),
        "registry_version": registry.registry.version,
        "site": registry.registry.site,
        "base_url": registry.registry.base_url,
        "registry_path": str(registry.registry_path),
        "registry_file_exists": registry.registry_path.exists(),
        "counts": {
            "items": len(items),
            "hubs": len(hub_counts),
            "article_maps": len(article_map_counts),
            "content_types": len(type_counts),
            "missing_repository_url": missing_repository,
            "missing_workbench_tools": missing_workbench,
            "missing_next_paths": missing_next_paths,
        },
        "hub_counts": dict(hub_counts),
        "content_type_counts": dict(type_counts),
        "top_article_maps": dict(article_map_counts.most_common(20)),
        "groups": [{"hub": hub, "count": len(rows), "items": rows[:20]} for hub, rows in sorted(by_hub.items())],
        "recommendations": [
            "Review unmapped GA4/Search Console pages before editing the seed registry.",
            "Add repository URLs and Workbench tool IDs where a page has a platform artifact or calculator surface.",
            "Keep registry edits in Git so Render and WordPress dashboards remain auditable.",
        ],
    }


def registry_coverage(registry: ContentRegistry) -> Dict[str, Any]:
    base = registry_manager(registry)
    counts = base["counts"]
    total = max(1, counts["items"])
    return {
        "ok": True,
        "generated_at": _now(),
        "registry_version": base["registry_version"],
        "coverage": {
            "repository_url_rate": round(100 * (total - counts["missing_repository_url"]) / total, 1),
            "workbench_tool_rate": round(100 * (total - counts["missing_workbench_tools"]) / total, 1),
            "next_path_rate": round(100 * (total - counts["missing_next_paths"]) / total, 1),
            "article_map_count": counts["article_maps"],
            "hub_count": counts["hubs"],
        },
        "gaps": {k: counts[k] for k in ["missing_repository_url", "missing_workbench_tools", "missing_next_paths"]},
        "recommendations": base["recommendations"],
    }


def source_manager(settings: Settings) -> Dict[str, Any]:
    external = _load_external_registry(settings)
    connectors = external.get("connectors", []) or []
    auth_required = [item for item in connectors if item.get("auth_required")]
    status_counts = Counter(item.get("status", "unknown") for item in connectors)
    type_counts = Counter(item.get("connector_type", "unknown") for item in connectors)
    return {
        "ok": True,
        "generated_at": _now(),
        "version": settings.version,
        "source_files": [
            {"id": "content_registry", "path": settings.registry_path, "exists": _safe_exists(settings.registry_path), "purpose": "Content map, hubs, article maps, pathways, repositories, and Workbench links."},
            {"id": "external_connectors", "path": settings.external_registry_path, "exists": _safe_exists(settings.external_registry_path), "purpose": "External source metadata and dashboard associations."},
        ],
        "configuration": {
            "external_live": settings.external_live,
            "external_cache_enabled": settings.external_cache_enabled,
            "external_cache_ttl_seconds": settings.external_cache_ttl_seconds,
            "search_console_live": settings.search_console_live,
            "sitemap_live": settings.sitemap_live,
            "public_dashboards_enabled": settings.public_dashboards_enabled,
            "ai_provider": settings.ai_provider,
            "eia_api_key_configured": bool(settings.eia_api_key),
            "epa_aqs_configured": bool(settings.epa_aqs_email and settings.epa_aqs_key),
            "gemini_configured": bool(settings.gemini_api_key),
        },
        "connector_registry": {
            "version": external.get("version"),
            "generated_at": external.get("generated_at"),
            "count": len(connectors),
            "auth_required_count": len(auth_required),
            "status_counts": dict(status_counts),
            "type_counts": dict(type_counts),
            "connectors": connectors,
        },
        "recommendations": [
            "Keep optional API keys in Render environment variables, never in repo files.",
            "Prefer cached/fallback public summaries on public pages; use live connector checks on private pages.",
            "Review source status before promoting dashboard claims publicly.",
        ],
    }


def visibility_matrix(settings: Settings) -> Dict[str, Any]:
    rows = []
    for module in module_catalog(settings):
        rows.append({
            "module_id": module["id"],
            "name": module["name"],
            "visibility": module["visibility"],
            "public_safe": module["visibility"] == "public",
            "requires_review": module["visibility"] in {"public-review", "private"},
            "shortcodes": module.get("shortcodes", []),
            "notes": module.get("notes", ""),
        })
    return {
        "ok": True,
        "generated_at": _now(),
        "public_dashboards_enabled": settings.public_dashboards_enabled,
        "rows": rows,
        "policy": {
            "public_allowed": ["public-dashboard"],
            "private_only": ["core-dashboard", "registry-manager", "event-diagnostics", "search-seo", "indexing", "publishing", "reports", "ai-briefs", "admin-control"],
            "review_required": "Any dashboard that includes raw analytics, conversion diagnostics, internal reports, AI drafts, source diagnostics, or registry management details should remain private unless manually reviewed and sanitized.",
        },
    }


def source_control_tools(settings: Settings) -> Dict[str, Any]:
    return {
        "ok": True,
        "generated_at": _now(),
        "write_enabled": False,
        "mode": "read-only-audit",
        "managed_files": [
            {"path": "backend/data/site_registry.seed.json", "purpose": "Site/content registry seed", "editable_in_v090": False},
            {"path": "backend/data/external_connectors.seed.json", "purpose": "External connector registry seed", "editable_in_v090": False},
            {"path": "backend/app/main.py", "purpose": "Backend endpoint router", "editable_in_v090": False},
            {"path": "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php", "purpose": "WordPress plugin routes and shortcodes", "editable_in_v090": False},
        ],
        "recommended_git_workflow": [
            "Edit registry/source files locally or through a future write-enabled admin editor.",
            "Run backend tests and WordPress syntax checks.",
            "Commit changes to Content-Catalyst-LLC/sustainable-catalyst-site-intelligence.",
            "Redeploy Render from the latest main branch.",
            "Upload the matching WordPress plugin ZIP when plugin files change.",
        ],
        "guardrails": [
            "Do not store Google service account JSON, API tokens, Gemini keys, EIA keys, or EPA AQS credentials in the repository.",
            "Keep public/private visibility decisions explicit before exposing dashboards publicly.",
            "Use GitHub history as the audit trail for registry and source-control changes.",
        ],
        "settings_snapshot": {
            "version": settings.version,
            "environment": settings.environment,
            "registry_path": settings.registry_path,
            "external_registry_path": settings.external_registry_path,
        },
    }


def diagnostics(settings: Settings, registry: ContentRegistry) -> Dict[str, Any]:
    checks = [
        {"id": "backend_version", "label": "Backend version", "status": "healthy", "value": settings.version},
        {"id": "registry_file", "label": "Content registry file", "status": "healthy" if registry.registry_path.exists() else "warning", "value": str(registry.registry_path)},
        {"id": "external_registry_file", "label": "External connector registry file", "status": "healthy" if _safe_exists(settings.external_registry_path) else "warning", "value": settings.external_registry_path},
        {"id": "api_token", "label": "API token configured", "status": "healthy" if bool(settings.api_token) else "warning", "value": bool(settings.api_token)},
        {"id": "ga4", "label": "GA4 live mode", "status": "healthy" if settings.ga4_enabled else "fallback", "value": settings.ga4_enabled},
        {"id": "search_console", "label": "Search Console live mode", "status": "healthy" if settings.search_console_live else "fallback", "value": settings.search_console_live},
        {"id": "public_dashboards", "label": "Public dashboards enabled", "status": "healthy" if settings.public_dashboards_enabled else "disabled", "value": settings.public_dashboards_enabled},
        {"id": "ai_provider", "label": "AI provider", "status": "healthy" if settings.ai_provider != "disabled" else "fallback", "value": settings.ai_provider},
    ]
    warnings = [item for item in checks if item["status"] in {"warning", "disabled"}]
    return {
        "ok": True,
        "generated_at": _now(),
        "version": settings.version,
        "environment": settings.environment,
        "checks": checks,
        "warnings": warnings,
        "endpoint_groups": [
            {"group": "admin", "paths": ["/intelligence/admin", "/admin/registry", "/admin/sources", "/admin/modules", "/admin/shortcodes", "/admin/diagnostics", "/admin/visibility", "/admin/source-control"]},
            {"group": "public", "paths": ["/public/landing-page", "/public/dashboard", "/public/knowledge-overview", "/public/climate-energy-summary", "/public/methodology"]},
            {"group": "reports", "paths": ["/reports/site-intelligence", "/reports/search-intelligence", "/reports/content-strategy", "/reports/external-sources", "/reports/climate-energy", "/reports/indexing", "/reports/export"]},
            {"group": "ai", "paths": ["/ai/status", "/ai/briefs/site-intelligence", "/ai/briefs/search", "/ai/briefs/publishing", "/ai/briefs/external-sources", "/ai/briefs/public-dashboard"]},
        ],
        "recommendations": [
            "Use the admin overview page after each deploy to confirm module visibility and registry/source status.",
            "Treat fallback status as acceptable for demos, but document source limitations before public use.",
            "Rotate exposed API tokens and keep all secrets in Render/WordPress settings rather than Git.",
        ],
    }



def admin_status(settings: Settings, registry: ContentRegistry) -> Dict[str, Any]:
    """Small, fast admin status payload for WordPress settings screens."""
    diag = diagnostics(settings, registry)
    warning_count = len(diag.get("warnings", []))
    return {
        "ok": True,
        "generated_at": _now(),
        "version": settings.version,
        "environment": settings.environment,
        "overall_status": "needs_review" if warning_count else "healthy",
        "warning_count": warning_count,
        "checks": diag.get("checks", []),
        "connection": {
            "backend": True,
            "api_token_configured": bool(settings.api_token),
            "registry_file_exists": registry.registry_path.exists(),
            "external_registry_file_exists": _safe_exists(settings.external_registry_path),
        },
        "admin_notes": [
            "Use this panel after each GitHub push and Render deploy to confirm the backend and WordPress plugin are aligned.",
            "If WordPress reports a token or gateway error, test the direct Render root endpoint and then the relevant protected endpoint.",
        ],
    }


def connection_check(settings: Settings, registry: ContentRegistry) -> Dict[str, Any]:
    checks = [
        {"id": "backend_root", "label": "Backend process", "status": "healthy", "message": f"{settings.app_name} {settings.version} is responding."},
        {"id": "environment", "label": "Environment", "status": "healthy" if settings.environment in {"production", "development"} else "warning", "message": settings.environment},
        {"id": "api_token", "label": "Protected endpoint token", "status": "healthy" if bool(settings.api_token) else "warning", "message": "configured" if settings.api_token else "missing or disabled"},
        {"id": "registry", "label": "Content registry", "status": "healthy" if registry.registry_path.exists() else "warning", "message": str(registry.registry_path)},
        {"id": "external_registry", "label": "External source registry", "status": "healthy" if _safe_exists(settings.external_registry_path) else "warning", "message": settings.external_registry_path},
        {"id": "public_dashboards", "label": "Public dashboards", "status": "healthy" if settings.public_dashboards_enabled else "disabled", "message": str(settings.public_dashboards_enabled)},
        {"id": "search_console", "label": "Search Console live mode", "status": "healthy" if settings.search_console_live else "fallback", "message": str(settings.search_console_live)},
        {"id": "ai_provider", "label": "AI provider", "status": "healthy" if settings.ai_provider != "disabled" else "fallback", "message": settings.ai_provider},
    ]
    status_counts = Counter(item["status"] for item in checks)
    return {
        "ok": True,
        "generated_at": _now(),
        "version": settings.version,
        "overall_status": "warning" if status_counts.get("warning") else "healthy",
        "status_counts": dict(status_counts),
        "checks": checks,
        "troubleshooting": [
            "Confirm the Render root endpoint returns the same version as the WordPress plugin.",
            "If a WordPress panel fails but Render works, check API token mismatch, WordPress cache, Cloudflare cache, and shortcode placement.",
            "If Render is stale, push the update package and use Manual Deploy → Deploy latest commit.",
        ],
    }


def public_readiness_check(settings: Settings) -> Dict[str, Any]:
    visibility = visibility_matrix(settings)
    public_rows = [row for row in visibility.get("rows", []) if row.get("visibility") == "public"]
    review_rows = [row for row in visibility.get("rows", []) if row.get("requires_review")]
    return {
        "ok": True,
        "generated_at": _now(),
        "version": settings.version,
        "public_dashboards_enabled": settings.public_dashboards_enabled,
        "public_safe_modules": public_rows,
        "requires_review_count": len(review_rows),
        "warnings": [
            "Keep admin, report, AI brief, Search Console, GA4, conversion, and operational diagnostics on private pages.",
            "Use public dashboard endpoints and public shortcodes only after reviewing page copy and methodology language.",
        ],
        "recommended_public_stack": [
            "[sc_site_intelligence_public_landing]",
            "[sc_public_site_intelligence]",
            "[sc_public_knowledge_overview]",
            "[sc_public_climate_energy_summary]",
            "[sc_public_methodology]",
        ],
    }


def diagnostic_summary(settings: Settings, registry: ContentRegistry) -> Dict[str, Any]:
    diag = diagnostics(settings, registry)
    sources = source_manager(settings)
    modules = module_manager(settings)
    shortcodes = shortcode_catalog()
    connection = connection_check(settings, registry)
    warnings = diag.get("warnings", [])
    return {
        "ok": True,
        "generated_at": _now(),
        "version": settings.version,
        "overall_status": "needs_review" if warnings else "healthy",
        "summary": "One-click operational diagnostic summary for backend, registry, source connectors, modules, shortcodes, visibility, and public/private boundaries.",
        "counts": {
            "diagnostic_checks": len(diag.get("checks", [])),
            "warnings": len(warnings),
            "modules": modules.get("count", 0),
            "shortcodes": shortcodes.get("count", 0),
            "external_connectors": sources.get("connector_registry", {}).get("count", 0),
        },
        "connection": connection,
        "warnings": warnings,
        "recommended_next_actions": [
            "Confirm Render and WordPress plugin versions match after each release.",
            "Use the Shortcode Catalog before adding a panel to a public page.",
            "Review public dashboard copy before publishing AI-assisted or external-source summaries.",
            "Keep registry/source changes in Git until a write-enabled editor is added with authentication and rollback support.",
        ],
    }

def admin_overview(settings: Settings, registry: ContentRegistry) -> Dict[str, Any]:
    registry_report = registry_manager(registry)
    sources = source_manager(settings)
    modules = module_manager(settings)
    shortcodes = shortcode_catalog()
    diag = diagnostics(settings, registry)
    return {
        "ok": True,
        "generated_at": _now(),
        "version": settings.version,
        "title": "Site Intelligence Admin Control Plane",
        "summary": "Registry, source, module, shortcode, visibility, and diagnostic control-plane overview for Sustainable Catalyst Site Intelligence.",
        "totals": {
            "registry_items": registry_report["counts"]["items"],
            "hubs": registry_report["counts"]["hubs"],
            "external_connectors": sources["connector_registry"]["count"],
            "modules": modules["count"],
            "shortcodes": shortcodes["count"],
            "warnings": len(diag["warnings"]),
        },
        "registry": {"counts": registry_report["counts"], "hub_counts": registry_report["hub_counts"], "registry_path": registry_report["registry_path"]},
        "sources": {"configuration": sources["configuration"], "connector_registry": {k: v for k, v in sources["connector_registry"].items() if k != "connectors"}},
        "modules": modules["modules"],
        "shortcodes": {"category_counts": shortcodes["category_counts"], "visibility_counts": shortcodes["visibility_counts"], "featured": shortcodes["shortcodes"][-3:]},
        "diagnostics": {"checks": diag["checks"], "warnings": diag["warnings"]},
        "next_actions": [
            "Use the shortcode catalog to confirm which panels belong on private/admin pages versus public pages.",
            "Use Registry Manager before adding more dashboards so article maps, repositories, Workbench IDs, and next paths remain aligned.",
            "Use Source Manager before publishing claims that depend on external data connectors.",
            "Keep source-control writes in Git until a future authenticated registry editor is added.",
        ],
    }
