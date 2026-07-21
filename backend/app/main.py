from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import Body, Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import PlainTextResponse, FileResponse, Response, HTMLResponse

from .config import Settings, get_settings
from .version import APP_VERSION
from .build_info import public_build_info as build_public_build_info
from .platform_core_integration import PlatformCoreClient, platform_core_status as build_platform_core_status
from .ga4_client import GA4Client, get_ga4_client
from .metrics import build_page_metrics, dashboard_totals, hub_summary, mapping_coverage, unmapped_suggestions
from .events import event_diagnostics, event_setup_recommendations, page_opportunities
from .models import CollectedEvent, DashboardResponse, EventAck
from .connectors.external_data import ExternalDataHub, SAMPLE_POWER_DATA, SAMPLE_GIBS_LAYERS, SAMPLE_TRACE, _power_indicators, cache_status, clear_cache
from .connectors.advanced_external import AdvancedExternalDataHub
from .recommendations import site_recommendations
from .registry import ContentRegistry
from .search_console import SearchConsoleClient
from .seo_intelligence import internal_link_review, metadata_review, seo_recommendations
from .indexing_intelligence import (
    SitemapFetcher,
    four_oh_four_report,
    indexing_intelligence,
    indexing_recommendations,
    orphan_candidates,
    sitemap_report,
)
from .publishing_intelligence import publishing_intelligence, topic_momentum_report
from .public_dashboard import build_public_dashboard, public_landing_page, public_methodology, public_readiness_report
from .public_page_builder import public_dashboard_visual_qa, public_page_builder, public_page_builder_readiness, public_shortcode_bundles
from .release import release_checklist, release_public_summary, release_status as build_release_status, smoke_test as release_smoke_test
from .public_topic_dashboards import (
    public_dashboard_navigation,
    public_topic_dashboard,
    public_source_methodology,
    public_topic_page_templates,
    topic_dashboard_directory,
    topic_page_visual_qa,
)
from .public_api_sources import (
    public_sources as build_public_sources,
    public_source_health as build_public_source_health,
    public_development_indicators as build_public_development_indicators,
    public_research_metadata as build_public_research_metadata,
    public_publication_metadata as build_public_publication_metadata,
    public_repository_intelligence as build_public_repository_intelligence,
    public_indicator_overview as build_public_indicator_overview,
    public_sustainability_indicators as build_public_sustainability_indicators,
)
from .connector_operations_v2130 import ConnectorOperationsCenter
from .historical_archive_v2140 import HistoricalArchiveCenter
from .spatial_evidence_v2150 import SpatialEvidenceStudio
from .statistical_harmonization_v2160 import StatisticalHarmonizationEngine
from .model_forecast_early_warning_v2170 import ModelForecastEarlyWarningCenter
from .evidence_synthesis_v2180 import EvidenceSynthesisCenter
from .knowledge_graph_v2190 import KnowledgeGraphExplorer
from .intelligence_publishing_v2200 import IntelligencePublishingStudio
from .scheduled_monitoring_v2210 import ScheduledMonitoringCenter
from .institutional_workspaces_v2220 import InstitutionalWorkspaceCenter
from .cross_platform_workflows_v2230 import CrossPlatformWorkflowCenter
from .federation_exchange_v2240 import InstitutionalDataExchange
from .production_governance_v2250 import ProductionGovernanceCenter, SlidingWindowRateLimiter
from .connected_public_intelligence_v300 import ConnectedPublicIntelligencePlatform
from .live_intelligence_v314 import build_live_intelligence, live_intelligence_status, live_intelligence_ranking_policy
from .live_intelligence_source_operations_v320 import LiveIntelligenceSourceOperations
from .live_intelligence_context_v340 import (
    build_signal_context, build_signal_evidence, context_policy as live_signal_context_policy,
    render_signal_context_html,
)
from .public_live_connectors import (
    public_connector_status as build_public_connector_status,
    public_cache_status as build_public_cache_status,
    public_source_freshness as build_public_source_freshness,
    public_connector_detail as build_public_connector_detail,
    public_environmental_connectors as build_public_environmental_connectors,
    public_connector_reliability as build_public_connector_reliability,
    public_connector_status_polish as build_public_connector_status_polish,
    admin_connector_diagnostics as build_admin_connector_diagnostics,
)
from .public_indicator_charts import (
    public_indicator_dashboard_directory as build_public_indicator_dashboard_directory,
    public_indicator_dashboard as build_public_indicator_dashboard,
    public_indicator_chart_gallery as build_public_indicator_chart_gallery,
    public_indicator_chart_visual_qa as build_public_indicator_chart_visual_qa,
)
from .public_source_briefs_exports import (
    public_source_aware_brief_directory as build_public_source_aware_brief_directory,
    public_source_aware_brief as build_public_source_aware_brief,
    public_dashboard_export_manifest as build_public_dashboard_export_manifest,
    public_dashboard_export as build_public_dashboard_export,
    public_dashboard_export_visual_qa as build_public_dashboard_export_visual_qa,
)
from .public_export_reliability import (
    export_validation as build_export_validation,
    download_states as build_export_download_states,
    reliability as build_export_reliability,
    brief_polish as build_brief_polish,
    brief_fallbacks as build_brief_fallbacks,
)
from .sustainable_development_connectors import (
    source_registry as build_sustainable_development_source_registry,
    source_families as build_sustainable_development_source_families,
    planetary_boundary_registry as build_planetary_boundary_registry,
    connector_health as build_sustainable_development_connector_health,
    methodology as build_sustainable_development_methodology,
    connector_reliability as build_sustainable_development_connector_reliability,
    freshness_policy as build_sustainable_development_freshness_policy,
    schema_validation_report as build_sustainable_development_schema_validation,
    connector_cache_status as build_sustainable_development_cache_status,
)
from .planetary_boundaries_observatory import (
    overview as build_planetary_boundaries_overview,
    boundary_detail as build_planetary_boundary_detail,
    boundary_trend as build_planetary_boundary_trend,
    boundary_sources as build_planetary_boundary_sources,
    methodology as build_planetary_boundaries_methodology,
    export_manifest as build_planetary_boundaries_export,
)

from .humanitarian_intelligence import (
    source_registry as build_humanitarian_source_registry,
    overview as build_humanitarian_overview,
    crisis_map as build_humanitarian_crisis_map,
    displacement_context as build_displacement_context,
    humanitarian_reports as build_humanitarian_reports,
    methodology as build_humanitarian_methodology,
    export_manifest as build_humanitarian_export,
)
from .public_dashboard_launch_polish import (
    launch_manifest as build_dashboard_launch_manifest,
    launch_readiness as build_dashboard_launch_readiness,
    public_navigation as build_dashboard_public_navigation,
)
from .cross_domain_dashboard_studio import (
    dashboard_directory as build_cross_domain_dashboard_directory,
    dashboard_manifest as build_cross_domain_dashboard_manifest,
    get_dashboard as build_cross_domain_dashboard,
    dashboard_data as build_cross_domain_dashboard_data,
    dashboard_sources as build_cross_domain_dashboard_sources,
    dashboard_brief as build_cross_domain_dashboard_brief,
    dashboard_export as build_cross_domain_dashboard_export,
    country_intelligence as build_country_intelligence,
    cross_domain_comparison as build_cross_domain_comparison,
    rendering_diagnostics as build_cross_domain_rendering_diagnostics,
)
from .conflict_human_security import (
    overview as build_human_security_overview,
    source_registry as build_human_security_source_registry,
    monitor_detail as build_human_security_monitor_detail,
    event_stream as build_human_security_events,
    displacement_flows as build_human_security_displacement,
    modeled_risk as build_human_security_modeled_risk,
    methodology as build_human_security_methodology,
    export_manifest as build_human_security_export,
)
from .international_law_governance import (
    source_registry as build_international_law_source_registry,
    overview as build_international_law_overview,
    monitor_detail as build_international_law_monitor_detail,
    sanctions_monitor as build_international_law_sanctions_monitor,
    legal_events as build_international_law_events,
    methodology as build_international_law_methodology,
    export_manifest as build_international_law_export,
)
from .human_development_intelligence import (
    source_registry as build_human_development_source_registry,
    overview as build_human_development_overview,
    domain_detail as build_human_development_domain_detail,
    country_profile as build_human_development_country_profile,
    inequality_dimensions as build_human_development_inequality_dimensions,
    methodology as build_human_development_methodology,
    export_manifest as build_human_development_export,
)
from .live_country_intelligence import (
    country_profile as build_live_country_profile,
    country_indicators as build_live_country_indicators,
    country_trends as build_live_country_trends,
    country_brief as build_live_country_brief,
    country_catalog as build_country_catalog,
    search_countries as build_country_search,
    country_regions as build_country_regions,
    global_country_overview as build_global_country_overview,
    countries_diagnostics as build_countries_diagnostics,
    country_diagnostics as build_country_diagnostics,
)
from .unified_live_events import (
    unified_events as build_unified_events,
    categories_summary as build_event_categories,
    sources_summary as build_event_sources,
    event_detail as build_event_detail,
    timeline as build_event_timeline,
    summary as build_event_summary,
)
from .comparative_intelligence import (
    compare_countries as build_comparative_intelligence,
    compare_indicators as build_comparative_indicators,
    compare_trends as build_comparative_trends,
    compare_events as build_comparative_events,
    comparison_brief as build_comparison_brief,
    comparison_export as build_comparison_export,
    comparison_diagnostics as build_comparison_diagnostics,
)
from .public_briefing_export_studio import (
    briefing_directory as build_briefing_directory,
    build_brief as build_public_brief,
    briefing_export as build_public_brief_export,
    briefing_diagnostics as build_briefing_diagnostics,
)
from .thematic_intelligence_dashboards import (
    dashboard_directory as build_thematic_dashboard_directory,
    build_dashboard as build_thematic_dashboard,
    dashboard_indicators as build_thematic_dashboard_indicators,
    dashboard_trends as build_thematic_dashboard_trends,
    dashboard_events as build_thematic_dashboard_events,
    dashboard_brief as build_thematic_dashboard_brief,
    dashboard_export as build_thematic_dashboard_export,
    dashboard_diagnostics as build_thematic_dashboard_diagnostics,
    ThematicDashboardError,
)
from .source_methodology_studio import (
    source_directory as build_source_methodology_directory,
    source_detail as build_source_detail,
    source_status as build_source_status,
    source_coverage as build_source_coverage,
    methodology_directory as build_methodology_directory,
    methodology_detail as build_methodology_detail,
    studio_diagnostics as build_source_methodology_diagnostics,
    studio_export as build_source_methodology_export,
    SourceMethodologyError,
)
from .saved_views import (
    schema_manifest as build_saved_views_schema,
    validate_manifest as validate_saved_view_manifest,
    migrations_manifest as build_saved_views_migrations,
    diagnostics as build_saved_views_diagnostics,
)
from .experience_quality import (
    experience_profile as build_experience_profile,
    experience_checklist as build_experience_checklist,
    experience_diagnostics as build_experience_diagnostics,
)
from .public_launch_portfolio import (
    launch_profile as build_launch_profile,
    launch_checklist as build_launch_checklist,
    launch_materials as build_launch_materials,
    launch_diagnostics as build_launch_diagnostics,
    portfolio_manifest as build_portfolio_manifest,
    portfolio_markdown as build_portfolio_markdown,
)
from .auditable_public_observatory import (
    observatory_profile as build_observatory_profile,
    audit_catalog as build_observatory_catalog,
    audit_record as build_observatory_audit_record,
    lineage_graph as build_observatory_lineage,
    verification_contract as build_observatory_verification,
    verify_payload as verify_observatory_payload,
    release_ledger as build_observatory_release_ledger,
    audit_packet as build_observatory_audit_packet,
    audit_packet_markdown as build_observatory_audit_packet_markdown,
    observatory_diagnostics as build_observatory_diagnostics,
    ObservatoryError,
)
from .earth_observation_studio import (
    overview as build_earth_observation_overview,
    layers as build_earth_observation_layers,
    comparison as build_earth_observation_comparison,
    timeline as build_earth_observation_timeline,
    presets as build_earth_observation_presets,
    export_manifest as build_earth_observation_export_manifest,
    diagnostics as build_earth_observation_diagnostics,
)
from .geospatial_intelligence import (
    overview as build_geospatial_overview,
    layer_manifest as build_geospatial_layers,
    live_events as build_geospatial_events,
    heatmap as build_geospatial_heatmap,
    satellite_manifest as build_geospatial_satellite,
    timeline as build_geospatial_timeline,
    accessibility_table as build_geospatial_accessibility,
    diagnostics as build_geospatial_diagnostics,
)

from .public_source_pages import (
    public_source_page_directory as build_public_source_page_directory,
    public_source_navigation as build_public_source_navigation,
    public_source_page_templates as build_public_source_page_templates,
    public_source_page_visual_qa as build_public_source_page_visual_qa,
)
from .report_generator import (
    bundle_manifest_report,
    bundle_report,
    climate_energy_report,
    content_strategy_report,
    external_sources_report,
    indexing_report,
    search_intelligence_report,
    site_intelligence_report,
    to_csv,
    to_markdown,
)
from .ai_briefs import ai_status, build_ai_brief
from .admin_control import (
    admin_overview,
    admin_status,
    connection_check,
    diagnostic_summary,
    diagnostics as admin_diagnostics,
    module_manager,
    public_readiness_check,
    registry_coverage,
    registry_manager,
    shortcode_catalog,
    source_control_tools,
    source_manager,
    visibility_matrix,
)


def require_token(
    settings: Settings = Depends(get_settings),
    x_sc_intelligence_token: Optional[str] = Header(default=None),
):
    if settings.environment == "production" and settings.api_token:
        if x_sc_intelligence_token != settings.api_token:
            raise HTTPException(status_code=401, detail="Invalid or missing Site Intelligence API token.")


def get_registry(settings: Settings = Depends(get_settings)) -> ContentRegistry:
    return ContentRegistry(settings.registry_path)


settings = get_settings()
_production_rate_limiter = SlidingWindowRateLimiter(settings.production_admin_rate_limit, settings.production_admin_rate_window_seconds)
app = FastAPI(title=settings.app_name, version=settings.version)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1024, compresslevel=6)


@app.middleware("http")
async def public_experience_headers(request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
    response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    response.headers.setdefault("Vary", "Accept-Encoding")

    path = request.url.path
    response.headers.setdefault("X-SC-Site-Intelligence-Version", APP_VERSION)
    if path == "/app/service-worker.js":
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        response.headers.setdefault("Service-Worker-Allowed", "/app/")
        response.headers.setdefault("X-SC-Cache-Generation", f"scsi-v{APP_VERSION}")
    elif path in {"/app/manifest.webmanifest", "/app/offline.html"}:
        response.headers["Cache-Control"] = "no-cache, max-age=0, must-revalidate"
    elif path.startswith("/app/assets/"):
        response.headers.setdefault("Cache-Control", "public, max-age=3600, stale-while-revalidate=86400, stale-if-error=604800")
    elif path == "/app" or path.startswith("/app/"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        if settings.public_embeds_enabled:
            frame_ancestors = ["'self'"] + [origin for origin in settings.public_embed_allowed_origins.split(",") if origin.strip()]
            response.headers.setdefault("Content-Security-Policy", "frame-ancestors " + (" ".join(item.strip() for item in frame_ancestors) if len(frame_ancestors) > 1 else "*"))
        else:
            response.headers.setdefault("Content-Security-Policy", "frame-ancestors 'self'")
    elif path.startswith("/public/experience-profile") or path.startswith("/public/launch-profile") or path.startswith("/public/observatory"):
        response.headers.setdefault("Cache-Control", "public, max-age=300")
    return response


@app.get("/")
def root(settings: Settings = Depends(get_settings)):
    return {
        "ok": True,
        "name": settings.app_name,
        "version": settings.version,
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health(settings: Settings = Depends(get_settings), ga4: GA4Client = Depends(get_ga4_client)):
    return {
        "ok": True,
        "service": settings.app_name,
        "version": settings.version,
        "environment": settings.environment,
        "demo_mode": settings.demo_mode,
        "ga4_enabled": ga4.enabled,
        "time": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/public/build-info")
def public_build_info():
    return build_public_build_info()


@app.get("/diagnostics/ga4")
def ga4_diagnostics(ga4: GA4Client = Depends(get_ga4_client), _: None = Depends(require_token)):
    return {"ok": True, "ga4": ga4.diagnostics()}


@app.get("/registry")
def registry(registry: ContentRegistry = Depends(get_registry), _: None = Depends(require_token)):
    return registry.registry.model_dump()


@app.get("/analytics/pages")
def analytics_pages(
    start_date: str = Query("28daysAgo"),
    end_date: str = Query("today"),
    ga4: GA4Client = Depends(get_ga4_client),
    _: None = Depends(require_token),
):
    return {
        "ok": True,
        "source": "ga4" if ga4.enabled else "demo",
        "rows": [row.model_dump() for row in ga4.page_report(start_date, end_date)],
    }


@app.get("/analytics/events")
def analytics_events(
    start_date: str = Query("28daysAgo"),
    end_date: str = Query("today"),
    ga4: GA4Client = Depends(get_ga4_client),
    _: None = Depends(require_token),
):
    return {
        "ok": True,
        "source": "ga4" if ga4.enabled else "demo",
        "rows": [row.model_dump() for row in ga4.event_report(start_date, end_date)],
    }


@app.get("/intelligence/dashboard", response_model=DashboardResponse)
def intelligence_dashboard(
    start_date: str = Query("28daysAgo"),
    end_date: str = Query("today"),
    ga4: GA4Client = Depends(get_ga4_client),
    registry: ContentRegistry = Depends(get_registry),
    _: None = Depends(require_token),
):
    try:
        page_rows = ga4.page_report(start_date, end_date)
        event_rows = ga4.event_report(start_date, end_date)
        metrics = build_page_metrics(page_rows, event_rows, registry)
    except Exception as exc:  # noqa: BLE001 - return a useful setup error to WordPress instead of a plain 500.
        raise HTTPException(
            status_code=502,
            detail={
                "message": "GA4 report request failed.",
                "error_type": exc.__class__.__name__,
                "error_message": str(exc),
                "hint": "Check SC_SI_GA4_PROPERTY_ID, service account Viewer access, Google Analytics Data API activation, and SC_SI_GOOGLE_APPLICATION_CREDENTIALS_JSON.",
            },
        ) from exc
    return DashboardResponse(
        generated_at=datetime.now(timezone.utc).isoformat(),
        source="ga4" if ga4.enabled else "demo",
        date_range={"start_date": start_date, "end_date": end_date},
        totals=dashboard_totals(metrics),
        top_pages=metrics[:25],
        hub_summary=hub_summary(metrics),
        recommendations=site_recommendations(metrics) + event_setup_recommendations(event_diagnostics(event_rows, metrics)),
        registry_count=registry.count(),
        unmapped_pages=unmapped_suggestions(metrics, registry, limit=12),
        mapping_coverage=mapping_coverage(metrics),
        event_diagnostics=event_diagnostics(event_rows, metrics),
        conversion_readiness=event_diagnostics(event_rows, metrics).get("readiness", {}),
    )


@app.get("/intelligence/page")
def intelligence_page(
    path: str = Query(...),
    start_date: str = Query("28daysAgo"),
    end_date: str = Query("today"),
    ga4: GA4Client = Depends(get_ga4_client),
    registry: ContentRegistry = Depends(get_registry),
    _: None = Depends(require_token),
):
    try:
        page_rows = ga4.page_report(start_date, end_date)
        event_rows = ga4.event_report(start_date, end_date)
        metrics = build_page_metrics(page_rows, event_rows, registry)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=502,
            detail={
                "message": "GA4 page request failed.",
                "error_type": exc.__class__.__name__,
                "error_message": str(exc),
                "hint": "Check GA4 credentials, property ID, and service account access.",
            },
        ) from exc
    normalized = ContentRegistry._norm(path)
    for metric in metrics:
        if ContentRegistry._norm(metric.path) == normalized:
            return {"ok": True, "source": "ga4" if ga4.enabled else "demo", "page": metric.model_dump()}
    item = registry.find(path)
    return {
        "ok": True,
        "source": "ga4" if ga4.enabled else "demo",
        "page": None,
        "registry_match": item.model_dump() if item else None,
        "message": "No GA4 row was returned for this path in the selected date range.",
    }


@app.get("/intelligence/unmapped")
def intelligence_unmapped(
    start_date: str = Query("28daysAgo"),
    end_date: str = Query("today"),
    limit: int = Query(25, ge=1, le=100),
    ga4: GA4Client = Depends(get_ga4_client),
    registry: ContentRegistry = Depends(get_registry),
    _: None = Depends(require_token),
):
    try:
        page_rows = ga4.page_report(start_date, end_date)
        event_rows = ga4.event_report(start_date, end_date)
        metrics = build_page_metrics(page_rows, event_rows, registry)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=502,
            detail={
                "message": "GA4 unmapped-pages request failed.",
                "error_type": exc.__class__.__name__,
                "error_message": str(exc),
                "hint": "Check GA4 credentials, property ID, and service account access.",
            },
        ) from exc
    return {
        "ok": True,
        "source": "ga4" if ga4.enabled else "demo",
        "date_range": {"start_date": start_date, "end_date": end_date},
        "mapping_coverage": mapping_coverage(metrics),
        "suggestions": [item.model_dump() for item in unmapped_suggestions(metrics, registry, limit=limit)],
    }


@app.get("/registry/resolve")
def registry_resolve(
    path: str = Query(...),
    title: str = Query(""),
    registry: ContentRegistry = Depends(get_registry),
    _: None = Depends(require_token),
):
    match = registry.resolve(path, title)
    return {
        "ok": True,
        "path": ContentRegistry._norm(path),
        "status": match.status,
        "confidence": match.confidence,
        "reason": match.reason,
        "item": match.item.model_dump() if match.item else None,
    }



@app.get("/public/dashboards")
def public_topic_dashboard_directory_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    return topic_dashboard_directory()


@app.get("/public/navigation")
def public_dashboard_navigation_endpoint(current: str = Query(""), settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    return public_dashboard_navigation(current)


@app.get("/public/page-templates")
def public_topic_page_templates_endpoint(slug: str = Query(""), settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    try:
        return public_topic_page_templates(slug or None)
    except KeyError:
        raise HTTPException(status_code=404, detail="Unknown public Site Intelligence page template.")


@app.get("/public/topic-page-visual-qa")
def public_topic_page_visual_qa_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    return topic_page_visual_qa()



@app.get("/public/connectors/status")
def public_connector_status_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    return build_public_connector_status(settings)


@app.get("/public/connectors/cache")
def public_connector_cache_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    return build_public_cache_status(settings)


@app.get("/public/connectors/freshness")
def public_connector_freshness_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    return build_public_source_freshness(settings)


@app.get("/public/connectors/world-bank")
def public_world_bank_connector_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    return build_public_connector_detail("world-bank", settings)


@app.get("/public/connectors/openalex")
def public_openalex_connector_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    return build_public_connector_detail("openalex", settings)


@app.get("/public/connectors/crossref")
def public_crossref_connector_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    return build_public_connector_detail("crossref", settings)


@app.get("/public/connectors/github")
def public_github_connector_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    return build_public_connector_detail("github", settings)


@app.get("/public/connectors/environmental")
def public_environmental_connectors_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    return build_public_environmental_connectors(settings)



@app.get("/public/connectors/reliability")
def public_connector_reliability_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    return build_public_connector_reliability(settings)


@app.get("/public/connectors/status-polish")
def public_connector_status_polish_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    return build_public_connector_status_polish(settings)


@app.get("/public/dashboard-exports/validation")
def dashboard_export_validation_endpoint(): return build_export_validation()

@app.get("/public/dashboard-exports/download-states")
def dashboard_export_download_states_endpoint(): return build_export_download_states()

@app.get("/public/dashboard-exports/reliability")
def dashboard_export_reliability_endpoint(): return build_export_reliability()

@app.get("/public/source-aware-briefs/polish")
def source_aware_brief_polish_endpoint(): return build_brief_polish()

@app.get("/public/source-aware-briefs/fallbacks")
def source_aware_brief_fallbacks_endpoint(): return build_brief_fallbacks()


@app.get("/public/sustainable-development/sources")
def sustainable_development_source_registry_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled or not settings.sustainable_development_connectors_enabled:
        raise HTTPException(status_code=403, detail="Sustainable development connectors are disabled.")
    return build_sustainable_development_source_registry(settings)

@app.get("/public/sustainable-development/families")
def sustainable_development_source_families_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled or not settings.sustainable_development_connectors_enabled:
        raise HTTPException(status_code=403, detail="Sustainable development connectors are disabled.")
    return build_sustainable_development_source_families()

@app.get("/public/sustainable-development/planetary-boundaries")
def planetary_boundary_registry_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled or not settings.sustainable_development_connectors_enabled:
        raise HTTPException(status_code=403, detail="Sustainable development connectors are disabled.")
    return build_planetary_boundary_registry()

@app.get("/public/sustainable-development/health")
def sustainable_development_connector_health_endpoint(live: bool = Query(False), settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled or not settings.sustainable_development_connectors_enabled:
        raise HTTPException(status_code=403, detail="Sustainable development connectors are disabled.")
    return build_sustainable_development_connector_health(settings, live=bool(live and settings.sustainable_development_live_checks))

@app.get("/public/sustainable-development/methodology")
def sustainable_development_methodology_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled or not settings.sustainable_development_connectors_enabled:
        raise HTTPException(status_code=403, detail="Sustainable development connectors are disabled.")
    return build_sustainable_development_methodology()

@app.get("/public/sustainable-development/reliability")
def sustainable_development_connector_reliability_endpoint(live: bool = Query(False), force: bool = Query(False), settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled or not settings.sustainable_development_connectors_enabled:
        raise HTTPException(status_code=403, detail="Sustainable development connectors are disabled.")
    return build_sustainable_development_connector_reliability(settings, live=bool(live), force=bool(force))

@app.get("/public/sustainable-development/freshness")
def sustainable_development_freshness_policy_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled or not settings.sustainable_development_connectors_enabled:
        raise HTTPException(status_code=403, detail="Sustainable development connectors are disabled.")
    return build_sustainable_development_freshness_policy()

@app.get("/public/sustainable-development/schema-validation")
def sustainable_development_schema_validation_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled or not settings.sustainable_development_connectors_enabled:
        raise HTTPException(status_code=403, detail="Sustainable development connectors are disabled.")
    return build_sustainable_development_schema_validation()

@app.get("/public/sustainable-development/cache")
def sustainable_development_cache_status_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled or not settings.sustainable_development_connectors_enabled:
        raise HTTPException(status_code=403, detail="Sustainable development connectors are disabled.")
    return build_sustainable_development_cache_status()


@app.get("/public/humanitarian-intelligence")
def public_humanitarian_intelligence():
    return build_humanitarian_overview()

@app.get("/public/humanitarian-intelligence/sources")
def public_humanitarian_sources():
    return build_humanitarian_source_registry()

@app.get("/public/humanitarian-intelligence/crisis-map")
def public_humanitarian_crisis_map():
    return build_humanitarian_crisis_map()

@app.get("/public/humanitarian-intelligence/displacement")
def public_displacement_context():
    return build_displacement_context()

@app.get("/public/humanitarian-intelligence/reports")
def public_humanitarian_reports():
    return build_humanitarian_reports()

@app.get("/public/humanitarian-intelligence/methodology")
def public_humanitarian_methodology():
    return build_humanitarian_methodology()

@app.get("/public/humanitarian-intelligence/export")
def public_humanitarian_export():
    return build_humanitarian_export()










@app.get("/public/events")
def public_unified_events(
    days: int = Query(default=14, ge=1, le=90),
    limit: int = Query(default=300, ge=1, le=1000),
    category: list[str] = Query(default=[]),
    source: list[str] = Query(default=[]),
    country_code: str | None = Query(default=None),
):
    return build_unified_events(
        days=days,
        limit=limit,
        categories=category,
        sources=source,
        country_code=country_code,
    )


@app.get("/public/events/categories")
def public_event_categories(days: int = Query(default=14, ge=1, le=90)):
    return build_event_categories(days=days)


@app.get("/public/events/sources")
def public_event_sources(days: int = Query(default=14, ge=1, le=90)):
    return build_event_sources(days=days)


@app.get("/public/events/timeline")
def public_event_timeline(
    days: int = Query(default=14, ge=1, le=90),
    interval_hours: int = Query(default=24, ge=1, le=168),
):
    return build_event_timeline(days=days, interval_hours=interval_hours)


@app.get("/public/events/summary")
def public_event_summary(days: int = Query(default=14, ge=1, le=90)):
    return build_event_summary(days=days)


@app.get("/public/events/{event_id}")
def public_event_detail(event_id: str):
    payload = build_event_detail(event_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="Event record not found.")
    return payload


@app.get("/public/earth-observation")
def public_earth_observation_overview():
    return build_earth_observation_overview()


@app.get("/public/earth-observation/layers")
def public_earth_observation_layers():
    return build_earth_observation_layers()


@app.get("/public/earth-observation/compare")
def public_earth_observation_compare(
    layer: str = Query(default="true-color"),
    date_a: str = Query(default=""),
    date_b: str = Query(default=""),
):
    return build_earth_observation_comparison(layer, date_a, date_b)


@app.get("/public/earth-observation/timeline")
def public_earth_observation_timeline(
    layer: str = Query(default="true-color"),
    end_date: str = Query(default=""),
    days: int = Query(default=14, ge=2, le=31),
):
    return build_earth_observation_timeline(layer, end_date, days)


@app.get("/public/earth-observation/presets")
def public_earth_observation_presets():
    return build_earth_observation_presets()



@app.get("/public/earth-observation/diagnostics")
def public_earth_observation_diagnostics():
    return build_earth_observation_diagnostics()


@app.get("/public/earth-observation/export-manifest")
def public_earth_observation_export_manifest(
    layer: str = Query(default="true-color"),
    date_a: str = Query(default=""),
    date_b: str = Query(default=""),
    latitude: float = Query(default=12.0, ge=-90, le=90),
    longitude: float = Query(default=20.0, ge=-180, le=180),
    zoom: int = Query(default=2, ge=1, le=12),
    opacity: float = Query(default=0.72, ge=0.1, le=1.0),
):
    return build_earth_observation_export_manifest(layer, date_a, date_b, latitude, longitude, zoom, opacity)


@app.get("/public/geospatial")
def public_geospatial_overview():
    return build_geospatial_overview()

@app.get("/public/geospatial/layers")
def public_geospatial_layers():
    return build_geospatial_layers()

@app.get("/public/geospatial/events")
def public_geospatial_events(category: str = "all"):
    return build_geospatial_events(category)

@app.get("/public/geospatial/heatmap")
def public_geospatial_heatmap():
    return build_geospatial_heatmap()

@app.get("/public/geospatial/satellite")
def public_geospatial_satellite(date: str = ""):
    return build_geospatial_satellite(date)

@app.get("/public/geospatial/timeline")
def public_geospatial_timeline():
    return build_geospatial_timeline()

@app.get("/public/geospatial/accessibility")
def public_geospatial_accessibility():
    return build_geospatial_accessibility()

@app.get("/public/geospatial/diagnostics")
def public_geospatial_diagnostics():
    return build_geospatial_diagnostics()


@app.get("/public/dashboard-studio/launch-manifest")
def public_dashboard_launch_manifest():
    return build_dashboard_launch_manifest()


@app.get("/public/dashboard-studio/launch-readiness")
def public_dashboard_launch_readiness():
    return build_dashboard_launch_readiness()


@app.get("/public/dashboard-studio/navigation")
def public_dashboard_public_navigation():
    return build_dashboard_public_navigation()

@app.get("/public/dashboard-studio")
def public_cross_domain_dashboards():
    return build_cross_domain_dashboard_directory()


@app.get("/public/dashboard-studio/manifest")
def public_cross_domain_dashboard_manifest():
    return build_cross_domain_dashboard_manifest()


@app.get("/public/dashboard-studio/{dashboard_id}")
def public_cross_domain_dashboard(dashboard_id: str):
    result = build_cross_domain_dashboard(dashboard_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result)
    return result


@app.get("/public/dashboard-studio/{dashboard_id}/data")
def public_cross_domain_dashboard_data(dashboard_id: str, country: str = "", region: str = "", start: str = "", end: str = "", compare: str = ""):
    result = build_cross_domain_dashboard_data(dashboard_id, country, region, start, end, compare)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result)
    return result


@app.get("/public/dashboard-studio/{dashboard_id}/sources")
def public_cross_domain_dashboard_sources(dashboard_id: str):
    result = build_cross_domain_dashboard_sources(dashboard_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result)
    return result


@app.get("/public/dashboard-studio/{dashboard_id}/brief")
def public_cross_domain_dashboard_brief(dashboard_id: str, country: str = ""):
    result = build_cross_domain_dashboard_brief(dashboard_id, country)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result)
    return result


@app.get("/public/dashboard-studio/{dashboard_id}/export")
def public_cross_domain_dashboard_export(dashboard_id: str, country: str = ""):
    result = build_cross_domain_dashboard_export(dashboard_id, country)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result)
    return result





@app.get("/public/launch-status")
def public_launch_status():
    return {
        "ok": True,
        "version": APP_VERSION,
        "release_channel": "public-beta",
        "standalone_app": "/app/",
        "platform_core_optional": True,
        "platform_core_required_for_public_app": False,
        "launch_checks": {
            "standalone_app": "ready",
            "satellite_layers": "ready",
            "earth_observation_studio": "flagship-visual-beta",
            "public_events": "unified-live-event-intelligence",
            "country_intelligence": "global-searchable-live-intelligence",
            "responsive_embed": "ready",
            "accessibility_states": "ready",
            "platform_core": "optional",
        },
    }

@app.get("/public/platform-core/status")
def public_platform_core_status():
    """Public-safe integration status. Never returns API keys."""
    return build_platform_core_status()


@app.post("/admin/platform-core/replay-queue")
def replay_platform_core_queue(
    limit: int = Query(default=100, ge=1, le=1000),
    _: None = Depends(require_token),
):
    return PlatformCoreClient().replay_queue(limit=limit)


@app.get("/public/country/{country_code}/evidence-lineage")
def public_country_evidence_lineage(country_code: str):
    try:
        payload = build_live_country_indicators(country_code)
    except ValueError:
        raise HTTPException(status_code=404, detail="Unsupported country code.")
    items = []
    for indicator in payload.get("indicators", []):
        latest = indicator.get("latest")
        lineage = indicator.get("lineage") or {}
        if not latest:
            continue
        items.append({
            "indicator_id": indicator.get("id"),
            "indicator_key": indicator.get("key"),
            "label": indicator.get("label"),
            "value": latest.get("value"),
            "unit": indicator.get("unit"),
            "reporting_year": latest.get("year"),
            "source": indicator.get("source"),
            "source_url": indicator.get("source_url"),
            "data_state": indicator.get("data_state"),
            "evidence_id": lineage.get("evidence_id"),
            "source_snapshot_id": lineage.get("source_snapshot_id"),
            "provenance_activity_id": lineage.get("provenance_activity_id"),
            "verification_url": lineage.get("verification_url"),
            "platform_core_state": lineage.get("platform_core_state", "not-recorded"),
            "methodology": "Latest non-null observation; reporting year and unit preserved; no imputation.",
        })
    return {
        "ok": True,
        "version": APP_VERSION,
        "country": payload.get("country"),
        "platform_core": build_platform_core_status(),
        "items": items,
    }



@app.get("/public/countries")
def public_country_catalog(force_refresh: bool = Query(default=False)):
    return build_country_catalog(force_refresh=force_refresh)


@app.get("/public/countries/search")
def public_country_search(
    q: str = Query(default=""),
    region: str = Query(default=""),
    limit: int = Query(default=50, ge=1, le=300),
):
    return build_country_search(query=q, region=region, limit=limit)


@app.get("/public/countries/regions")
def public_country_regions():
    return build_country_regions()


@app.get("/public/countries/diagnostics")
def public_countries_diagnostics():
    return build_countries_diagnostics()


@app.get("/public/country/{country_code}/diagnostics")
def public_country_diagnostics(country_code: str):
    try:
        return build_country_diagnostics(country_code)
    except ValueError:
        raise HTTPException(status_code=404, detail={
            "code": "unsupported_country",
            "message": "Unsupported country code.",
            "fallback_country": "KEN",
        })


@app.get("/public/country/{country_code}/overview")
def public_global_country_overview(country_code: str):
    try:
        return build_global_country_overview(country_code)
    except ValueError:
        raise HTTPException(status_code=404, detail="Unsupported country code.")


@app.get("/public/country/{country_code}")
def public_live_country_profile(country_code: str):
    try:
        return build_live_country_profile(country_code)
    except ValueError:
        raise HTTPException(status_code=404, detail="Unsupported country code.")

@app.get("/public/country/{country_code}/indicators")
def public_live_country_indicators(country_code: str):
    try:
        return build_live_country_indicators(country_code)
    except ValueError:
        raise HTTPException(status_code=404, detail="Unsupported country code.")

@app.get("/public/country/{country_code}/trends")
def public_live_country_trends(country_code: str):
    try:
        return build_live_country_trends(country_code)
    except ValueError:
        raise HTTPException(status_code=404, detail="Unsupported country code.")

@app.get("/public/country/{country_code}/brief")
def public_live_country_brief(country_code: str):
    try:
        return build_live_country_brief(country_code)
    except ValueError:
        raise HTTPException(status_code=404, detail="Unsupported country code.")

@app.get("/public/country-intelligence/{country_code}")
def public_country_intelligence(country_code: str):
    result = build_country_intelligence(country_code)
    if not result.get("ok"):
        raise HTTPException(status_code=422, detail=result)
    return result


@app.get("/public/cross-domain-comparison")
def public_cross_domain_comparison(country: str = "", compare: str = ""):
    return build_cross_domain_comparison(country, compare)


@app.get("/public/compare")
def public_comparative_intelligence(
    country: str = Query("KEN"),
    compare: str = Query("GHA"),
    include_events: bool = Query(True),
    include_brief: bool = Query(False),
    days: int = Query(30, ge=1, le=90),
    limit: int = Query(20, ge=1, le=100),
):
    try:
        return build_comparative_intelligence(
            country,
            compare,
            include_events=include_events,
            include_brief=include_brief,
            days=days,
            limit=limit,
        )
    except ValueError as exc:
        detail = str(exc)
        status = 422 if detail in {"duplicate_country", "unsupported_indicator"} else 404
        raise HTTPException(status_code=status, detail=detail)


@app.get("/public/compare/indicators")
def public_comparative_indicators(country: str = Query("KEN"), compare: str = Query("GHA")):
    try:
        return build_comparative_indicators(country, compare)
    except ValueError as exc:
        detail = str(exc)
        status = 422 if detail == "duplicate_country" else 404
        raise HTTPException(status_code=status, detail=detail)


@app.get("/public/compare/trends")
def public_comparative_trends(country: str = Query("KEN"), compare: str = Query("GHA")):
    try:
        return build_comparative_trends(country, compare)
    except ValueError as exc:
        detail = str(exc)
        status = 422 if detail == "duplicate_country" else 404
        raise HTTPException(status_code=status, detail=detail)


@app.get("/public/compare/events")
def public_comparative_events(country: str = Query("KEN"), compare: str = Query("GHA"), days: int = Query(30, ge=1, le=90), limit: int = Query(20, ge=1, le=100)):
    try:
        return build_comparative_events(country, compare, days=days, limit=limit)
    except ValueError as exc:
        detail = str(exc)
        status = 422 if detail == "duplicate_country" else 404
        raise HTTPException(status_code=status, detail=detail)


@app.get("/public/compare/brief")
def public_comparison_brief(
    country: str = Query("KEN"),
    compare: str = Query("GHA"),
    indicator: Optional[str] = Query(None),
):
    try:
        return build_comparison_brief(country, compare, indicator=indicator)
    except ValueError as exc:
        detail = str(exc)
        status = 422 if detail in {"duplicate_country", "unsupported_indicator"} else 404
        raise HTTPException(status_code=status, detail=detail)


@app.get("/public/compare/export")
def public_comparison_export(
    country: str = Query("KEN"),
    compare: str = Query("GHA"),
    format: str = Query("json"),
    indicator: Optional[str] = Query(None),
):
    try:
        body, media_type, filename = build_comparison_export(
            country,
            compare,
            export_format=format,
            indicator=indicator,
        )
    except ValueError as exc:
        detail = str(exc)
        if detail in {"unsupported_export_format", "unsupported_indicator", "duplicate_country"}:
            raise HTTPException(status_code=422, detail=detail)
        raise HTTPException(status_code=404, detail=detail)
    return Response(
        content=body,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


@app.get("/public/compare/diagnostics")
def public_comparison_diagnostics(
    country: str = Query("KEN"),
    compare: str = Query("GHA"),
):
    try:
        return build_comparison_diagnostics(country, compare)
    except ValueError as exc:
        detail = str(exc)
        status = 422 if detail == "duplicate_country" else 404
        raise HTTPException(status_code=status, detail=detail)


@app.get("/public/briefing-studio")
def public_briefing_studio_directory():
    return build_briefing_directory()


@app.get("/public/briefing-studio/brief")
def public_briefing_studio_brief(
    brief_type: str = Query("country", alias="type"),
    country: str = Query("KEN"),
    compare: str = Query("GHA"),
    event_id: Optional[str] = Query(None),
    days: int = Query(14, ge=1, le=90),
    category: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    layer_id: str = Query("true-color"),
    date_a: str = Query(""),
    date_b: str = Query(""),
    latitude: float = Query(12.0, ge=-90.0, le=90.0),
    longitude: float = Query(20.0, ge=-180.0, le=180.0),
    zoom: int = Query(2, ge=1, le=12),
    opacity: float = Query(0.72, ge=0.1, le=1.0),
    dashboard_id: str = Query("climate-human-vulnerability"),
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
    indicator: Optional[str] = Query(None),
    include_events: bool = Query(True),
):
    try:
        return build_public_brief(
            brief_type,
            country=country,
            compare=compare,
            event_id=event_id,
            days=days,
            category=category,
            source=source,
            layer_id=layer_id,
            date_a=date_a,
            date_b=date_b,
            latitude=latitude,
            longitude=longitude,
            zoom=zoom,
            opacity=opacity,
            dashboard_id=dashboard_id,
            start=start,
            end=end,
            indicator=indicator,
            include_events=include_events,
        )
    except ValueError as exc:
        detail = str(exc)
        status = 404 if detail in {"unsupported_country", "event_not_found", "dashboard_not_found"} else 422
        raise HTTPException(status_code=status, detail=detail)


@app.get("/public/briefing-studio/export")
def public_briefing_studio_export(
    brief_type: str = Query("country", alias="type"),
    format: str = Query("json"),
    country: str = Query("KEN"),
    compare: str = Query("GHA"),
    event_id: Optional[str] = Query(None),
    days: int = Query(14, ge=1, le=90),
    category: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    layer_id: str = Query("true-color"),
    date_a: str = Query(""),
    date_b: str = Query(""),
    latitude: float = Query(12.0, ge=-90.0, le=90.0),
    longitude: float = Query(20.0, ge=-180.0, le=180.0),
    zoom: int = Query(2, ge=1, le=12),
    opacity: float = Query(0.72, ge=0.1, le=1.0),
    dashboard_id: str = Query("climate-human-vulnerability"),
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
    indicator: Optional[str] = Query(None),
    include_events: bool = Query(True),
):
    try:
        body, media_type, filename = build_public_brief_export(
            brief_type,
            export_format=format,
            country=country,
            compare=compare,
            event_id=event_id,
            days=days,
            category=category,
            source=source,
            layer_id=layer_id,
            date_a=date_a,
            date_b=date_b,
            latitude=latitude,
            longitude=longitude,
            zoom=zoom,
            opacity=opacity,
            dashboard_id=dashboard_id,
            start=start,
            end=end,
            indicator=indicator,
            include_events=include_events,
        )
    except ValueError as exc:
        detail = str(exc)
        status = 404 if detail in {"unsupported_country", "event_not_found", "dashboard_not_found"} else 422
        raise HTTPException(status_code=status, detail=detail)
    return Response(
        content=body,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


@app.get("/public/briefing-studio/diagnostics")
def public_briefing_studio_diagnostics():
    return build_briefing_diagnostics()


@app.get("/public/thematic-dashboards")
def public_thematic_dashboard_directory():
    return build_thematic_dashboard_directory()


@app.get("/public/thematic-dashboard/{dashboard_id}")
def public_thematic_dashboard(
    dashboard_id: str,
    country: str = Query("KEN"),
    days: int = Query(30, ge=1, le=90),
    include_events: bool = Query(True),
):
    try:
        return build_thematic_dashboard(dashboard_id, country, days=days, include_events=include_events)
    except ThematicDashboardError as exc:
        detail = str(exc)
        status = 404 if detail in {"unknown_dashboard", "unsupported_country"} else 422
        raise HTTPException(status_code=status, detail=detail)


@app.get("/public/thematic-dashboard/{dashboard_id}/indicators")
def public_thematic_dashboard_indicators(dashboard_id: str, country: str = Query("KEN")):
    try:
        return build_thematic_dashboard_indicators(dashboard_id, country)
    except ThematicDashboardError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.get("/public/thematic-dashboard/{dashboard_id}/trends")
def public_thematic_dashboard_trends(dashboard_id: str, country: str = Query("KEN")):
    try:
        return build_thematic_dashboard_trends(dashboard_id, country)
    except ThematicDashboardError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.get("/public/thematic-dashboard/{dashboard_id}/events")
def public_thematic_dashboard_events(
    dashboard_id: str,
    country: str = Query("KEN"),
    days: int = Query(30, ge=1, le=90),
    limit: int = Query(40, ge=1, le=100),
):
    try:
        return build_thematic_dashboard_events(dashboard_id, country, days=days, limit=limit)
    except ThematicDashboardError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.get("/public/thematic-dashboard/{dashboard_id}/brief")
def public_thematic_dashboard_brief(
    dashboard_id: str,
    country: str = Query("KEN"),
    days: int = Query(30, ge=1, le=90),
):
    try:
        return build_thematic_dashboard_brief(dashboard_id, country, days=days)
    except ThematicDashboardError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.get("/public/thematic-dashboard/{dashboard_id}/export")
def public_thematic_dashboard_export(
    dashboard_id: str,
    country: str = Query("KEN"),
    days: int = Query(30, ge=1, le=90),
    format: str = Query("json"),
):
    try:
        body, media_type, filename = build_thematic_dashboard_export(
            dashboard_id, country, days=days, export_format=format
        )
    except ThematicDashboardError as exc:
        detail = str(exc)
        status = 422 if detail == "unsupported_export_format" else 404
        raise HTTPException(status_code=status, detail=detail)
    return Response(
        content=body,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


@app.get("/public/thematic-dashboard/{dashboard_id}/diagnostics")
def public_thematic_dashboard_diagnostics(
    dashboard_id: str,
    country: str = Query("KEN"),
    days: int = Query(30, ge=1, le=90),
):
    try:
        return build_thematic_dashboard_diagnostics(dashboard_id, country, days=days)
    except ThematicDashboardError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.get("/public/dashboard-studio/rendering-diagnostics")
def public_cross_domain_rendering_diagnostics():
    return build_cross_domain_rendering_diagnostics()


@app.get("/public/human-security")
def public_human_security():
    return build_human_security_overview()

@app.get("/public/human-security/sources")
def public_human_security_sources():
    return build_human_security_source_registry()

@app.get("/public/human-security/events")
def public_human_security_events(record_type: Optional[str] = Query(None), country: Optional[str] = Query(None)):
    return build_human_security_events(record_type=record_type, country=country)

@app.get("/public/human-security/displacement")
def public_human_security_displacement():
    return build_human_security_displacement()

@app.get("/public/human-security/modeled-risk")
def public_human_security_modeled_risk():
    return build_human_security_modeled_risk()

@app.get("/public/human-security/methodology")
def public_human_security_methodology():
    return build_human_security_methodology()

@app.get("/public/human-security/export")
def public_human_security_export():
    return build_human_security_export()

@app.get("/public/human-security/monitors/{monitor_id}")
def public_human_security_monitor(monitor_id: str):
    try:
        return build_human_security_monitor_detail(monitor_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Human-security monitor not found.")

@app.get("/public/international-law")
def public_international_law():
    return build_international_law_overview()

@app.get("/public/international-law/sources")
def public_international_law_sources():
    return build_international_law_source_registry()

@app.get("/public/international-law/sanctions")
def public_international_law_sanctions():
    return build_international_law_sanctions_monitor()

@app.get("/public/international-law/events")
def public_international_law_events(event_type: Optional[str] = Query(None), jurisdiction: Optional[str] = Query(None)):
    return build_international_law_events(event_type=event_type, jurisdiction=jurisdiction)

@app.get("/public/international-law/methodology")
def public_international_law_methodology():
    return build_international_law_methodology()

@app.get("/public/international-law/export")
def public_international_law_export():
    return build_international_law_export()

@app.get("/public/international-law/monitors/{monitor_id}")
def public_international_law_monitor(monitor_id: str):
    try:
        return build_international_law_monitor_detail(monitor_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="International-law monitor not found.")

@app.get("/public/human-development")
def public_human_development():
    return build_human_development_overview()

@app.get("/public/human-development/sources")
def public_human_development_sources():
    return build_human_development_source_registry()

@app.get("/public/human-development/country-profile")
def public_human_development_country_profile(country: Optional[str] = Query(None)):
    return build_human_development_country_profile(country)

@app.get("/public/human-development/inequalities")
def public_human_development_inequalities():
    return build_human_development_inequality_dimensions()

@app.get("/public/human-development/methodology")
def public_human_development_methodology():
    return build_human_development_methodology()

@app.get("/public/human-development/export")
def public_human_development_export():
    return build_human_development_export()

@app.get("/public/human-development/domains/{domain_id}")
def public_human_development_domain(domain_id: str):
    try:
        return build_human_development_domain_detail(domain_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Human-development domain not found.")


@app.get("/public/planetary-boundaries")
def planetary_boundaries_overview_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled or not settings.sustainable_development_connectors_enabled:
        raise HTTPException(status_code=403, detail="Planetary Boundaries Observatory is disabled.")
    return build_planetary_boundaries_overview()

@app.get("/public/planetary-boundaries/overview")
def planetary_boundaries_overview_alias_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled or not settings.sustainable_development_connectors_enabled:
        raise HTTPException(status_code=403, detail="Planetary Boundaries Observatory is disabled.")
    return build_planetary_boundaries_overview()

@app.get("/public/planetary-boundaries/methodology")
def planetary_boundaries_methodology_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled or not settings.sustainable_development_connectors_enabled:
        raise HTTPException(status_code=403, detail="Planetary Boundaries Observatory is disabled.")
    return build_planetary_boundaries_methodology()

@app.get("/public/planetary-boundaries/sources")
def planetary_boundaries_sources_endpoint(boundary_id: Optional[str] = Query(None), settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled or not settings.sustainable_development_connectors_enabled:
        raise HTTPException(status_code=403, detail="Planetary Boundaries Observatory is disabled.")
    try:
        return build_planetary_boundary_sources(boundary_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Planetary boundary not found.")

@app.get("/public/planetary-boundaries/export")
def planetary_boundaries_export_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled or not settings.sustainable_development_connectors_enabled:
        raise HTTPException(status_code=403, detail="Planetary Boundaries Observatory is disabled.")
    return build_planetary_boundaries_export()

@app.get("/public/planetary-boundaries/{boundary_id}/trend")
def planetary_boundary_trend_endpoint(boundary_id: str, settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled or not settings.sustainable_development_connectors_enabled:
        raise HTTPException(status_code=403, detail="Planetary Boundaries Observatory is disabled.")
    try:
        return build_planetary_boundary_trend(boundary_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Planetary boundary not found.")

@app.get("/public/planetary-boundaries/{boundary_id}/sources")
def planetary_boundary_sources_endpoint(boundary_id: str, settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled or not settings.sustainable_development_connectors_enabled:
        raise HTTPException(status_code=403, detail="Planetary Boundaries Observatory is disabled.")
    try:
        return build_planetary_boundary_sources(boundary_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Planetary boundary not found.")

@app.get("/public/planetary-boundaries/{boundary_id}")
def planetary_boundary_detail_endpoint(boundary_id: str, settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled or not settings.sustainable_development_connectors_enabled:
        raise HTTPException(status_code=403, detail="Planetary Boundaries Observatory is disabled.")
    try:
        return build_planetary_boundary_detail(boundary_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Planetary boundary not found.")


@app.get("/public/indicator-dashboards")
def public_indicator_dashboard_directory_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    return build_public_indicator_dashboard_directory(settings)


@app.get("/public/indicator-dashboards/sustainability")
def public_sustainability_indicator_dashboard_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    return build_public_indicator_dashboard("sustainability", settings)


@app.get("/public/indicator-dashboards/development")
def public_development_indicator_dashboard_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    return build_public_indicator_dashboard("development", settings)


@app.get("/public/indicator-dashboards/source-health")
def public_source_health_chart_dashboard_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    return build_public_indicator_dashboard("source-health", settings)


@app.get("/public/indicator-dashboards/research")
def public_research_metadata_chart_dashboard_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    return build_public_indicator_dashboard("research", settings)


@app.get("/public/indicator-dashboards/repository")
def public_repository_chart_dashboard_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    return build_public_indicator_dashboard("repository", settings)


@app.get("/public/indicator-dashboards/charts")
def public_indicator_chart_gallery_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    return build_public_indicator_chart_gallery(settings)


@app.get("/public/indicator-dashboards/visual-qa")
def public_indicator_chart_visual_qa_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    return build_public_indicator_chart_visual_qa(settings)



@app.get("/public/source-aware-briefs")
def public_source_aware_brief_directory_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    return build_public_source_aware_brief_directory(settings)


@app.get("/public/source-aware-briefs/site-intelligence")
def public_site_intelligence_source_aware_brief_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    return build_public_source_aware_brief("site-intelligence", settings)


@app.get("/public/source-aware-briefs/indicator")
def public_indicator_source_aware_brief_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    return build_public_source_aware_brief("indicator", settings)


@app.get("/public/source-aware-briefs/source-health")
def public_source_health_source_aware_brief_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    return build_public_source_aware_brief("source-health", settings)


@app.get("/public/dashboard-exports")
def public_dashboard_export_manifest_alias_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    return build_public_dashboard_export_manifest(settings)


@app.get("/public/dashboard-exports/manifest")
def public_dashboard_export_manifest_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    return build_public_dashboard_export_manifest(settings)


@app.get("/public/dashboard-exports/site-intelligence")
def public_site_intelligence_dashboard_export_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    return build_public_dashboard_export("site-intelligence", settings)


@app.get("/public/dashboard-exports/indicator")
def public_indicator_dashboard_export_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    return build_public_dashboard_export("indicator", settings)


@app.get("/public/dashboard-exports/source-health")
def public_source_health_dashboard_export_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    return build_public_dashboard_export("source-health", settings)


@app.get("/public/dashboard-exports/visual-qa")
def public_dashboard_export_visual_qa_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    return build_public_dashboard_export_visual_qa(settings)

@app.get("/admin/connectors/diagnostics")
def admin_connector_diagnostics_endpoint(settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    return build_admin_connector_diagnostics(settings)


def _connector_operations(settings: Settings) -> ConnectorOperationsCenter:
    if not settings.connector_operations_enabled:
        raise HTTPException(status_code=403, detail="Connector operations are disabled.")
    try:
        return ConnectorOperationsCenter(settings)
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/public/connectors/operations")
def public_connector_operations_endpoint(settings: Settings = Depends(get_settings)):
    return _connector_operations(settings).public_status()


@app.get("/admin/connectors/control-center")
def admin_connector_control_center_endpoint(settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    return _connector_operations(settings).control_center()


@app.get("/admin/connectors/registry")
def admin_connector_registry_endpoint(settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    return _connector_operations(settings).registry(public=False)


@app.get("/admin/connectors/jobs")
def admin_connector_jobs_endpoint(settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    return _connector_operations(settings).jobs()


@app.get("/admin/connectors/jobs/due")
def admin_connector_due_jobs_endpoint(settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    return _connector_operations(settings).due_jobs()


@app.post("/admin/connectors/jobs/run-due")
def admin_connector_run_due_jobs_endpoint(
    request: dict = Body(default={}),
    settings: Settings = Depends(get_settings),
    _: None = Depends(require_token),
):
    return _connector_operations(settings).run_due_jobs(
        dry_run=bool(request.get("dry_run", True)),
        force=bool(request.get("force", False)),
        limit=int(request.get("limit", 25)),
    )


@app.post("/admin/connectors/jobs/{job_id}/run")
def admin_connector_run_job_endpoint(
    job_id: str,
    request: Dict[str, Any] = Body(default={}),
    settings: Settings = Depends(get_settings),
    _: None = Depends(require_token),
):
    center = _connector_operations(settings)
    supplied = request.get("payload")
    if supplied is not None and not isinstance(supplied, dict):
        raise HTTPException(status_code=422, detail="payload must be a JSON object.")
    try:
        return center.run_job(
            job_id,
            trigger=str(request.get("trigger") or "manual"),
            dry_run=bool(request.get("dry_run", True)),
            supplied_payload=supplied,
            force=bool(request.get("force", False)),
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown connector job: {job_id}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/admin/connectors/executions")
def admin_connector_executions_endpoint(
    limit: int = Query(default=100, ge=1, le=5000),
    connector_id: str = Query(default=""),
    status: str = Query(default=""),
    settings: Settings = Depends(get_settings),
    _: None = Depends(require_token),
):
    return _connector_operations(settings).executions(limit=limit, connector_id=connector_id, status=status)


@app.get("/admin/connectors/quarantine")
def admin_connector_quarantine_endpoint(
    limit: int = Query(default=100, ge=1, le=5000),
    status: str = Query(default="open"),
    settings: Settings = Depends(get_settings),
    _: None = Depends(require_token),
):
    return _connector_operations(settings).quarantine(limit=limit, status=status)


@app.post("/admin/connectors/quarantine/{quarantine_id}/resolve")
def admin_connector_quarantine_resolve_endpoint(
    quarantine_id: str,
    request: Dict[str, Any] = Body(default={}),
    settings: Settings = Depends(get_settings),
    _: None = Depends(require_token),
):
    try:
        return _connector_operations(settings).resolve_quarantine(
            quarantine_id,
            action=str(request.get("action") or ""),
            note=str(request.get("note") or ""),
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown quarantine item: {quarantine_id}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/admin/connectors/datasets")
def admin_connector_datasets_endpoint(settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    return _connector_operations(settings).datasets()


# Site Intelligence v2.14.0 — Historical Archive and Temporal Change Intelligence.
def _historical_archive(settings: Settings) -> HistoricalArchiveCenter:
    if not settings.historical_archive_enabled:
        raise HTTPException(status_code=403, detail="Historical archive is disabled.")
    try:
        return HistoricalArchiveCenter(settings)
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/public/history")
def public_history_summary_endpoint(settings: Settings = Depends(get_settings)):
    return _historical_archive(settings).public_summary()


@app.get("/public/history/datasets")
def public_history_datasets_endpoint(settings: Settings = Depends(get_settings)):
    return _historical_archive(settings).datasets(public=True)


@app.get("/public/history/datasets/{dataset_id}/series")
def public_history_series_endpoint(
    dataset_id: str,
    metric: str = Query(default="", max_length=240),
    limit: int = Query(default=120, ge=1, le=1000),
    settings: Settings = Depends(get_settings),
):
    return _historical_archive(settings).series(dataset_id, metric=metric, limit=limit)


@app.get("/public/history/changes")
def public_history_changes_endpoint(
    dataset_id: str = Query(default="", max_length=180),
    material_only: bool = Query(default=False),
    limit: int = Query(default=100, ge=1, le=1000),
    settings: Settings = Depends(get_settings),
):
    return _historical_archive(settings).changes(dataset_id=dataset_id, material_only=material_only, limit=limit)


@app.get("/public/history/revisions")
def public_history_revisions_endpoint(
    dataset_id: str = Query(default="", max_length=180),
    limit: int = Query(default=100, ge=1, le=1000),
    settings: Settings = Depends(get_settings),
):
    return _historical_archive(settings).revisions(dataset_id=dataset_id, limit=limit)


@app.get("/admin/history/control-center")
def admin_history_control_center_endpoint(settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    return _historical_archive(settings).control_center()


@app.get("/admin/history/snapshots")
def admin_history_snapshots_endpoint(
    dataset_id: str = Query(default="", max_length=180),
    connector_id: str = Query(default="", max_length=180),
    limit: int = Query(default=100, ge=1, le=1000),
    settings: Settings = Depends(get_settings),
    _: None = Depends(require_token),
):
    return _historical_archive(settings).snapshots(dataset_id=dataset_id, connector_id=connector_id, limit=limit, public=False)


@app.post("/admin/history/snapshots/capture")
def admin_history_capture_endpoint(
    request: dict = Body(default={}),
    settings: Settings = Depends(get_settings),
    _: None = Depends(require_token),
):
    payload = request.get("payload")
    if not isinstance(payload, dict):
        raise HTTPException(status_code=422, detail="payload must be a JSON object.")
    try:
        return _historical_archive(settings).capture_snapshot(
            dataset_id=str(request.get("dataset_id") or ""),
            connector_id=str(request.get("connector_id") or "manual"),
            payload=payload,
            execution_id=str(request.get("execution_id") or ""),
            schema_version=str(request.get("schema_version") or "1.0"),
            source_timestamp=str(request.get("source_timestamp") or ""),
            source_revision_id=str(request.get("source_revision_id") or ""),
            note=str(request.get("note") or ""),
            force=bool(request.get("force", False)),
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/admin/history/snapshots/{snapshot_id}")
def admin_history_snapshot_endpoint(snapshot_id: str, settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _historical_archive(settings).snapshot(snapshot_id, include_payload=True)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown historical snapshot: {snapshot_id}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.get("/admin/history/compare")
def admin_history_compare_endpoint(
    previous_snapshot_id: str = Query(..., min_length=5, max_length=100),
    current_snapshot_id: str = Query(..., min_length=5, max_length=100),
    settings: Settings = Depends(get_settings),
    _: None = Depends(require_token),
):
    try:
        return _historical_archive(settings).compare_snapshots(previous_snapshot_id, current_snapshot_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown historical snapshot: {exc.args[0]}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/admin/history/export/{dataset_id}")
def admin_history_export_endpoint(
    dataset_id: str,
    include_payloads: bool = Query(default=False),
    limit: int = Query(default=500, ge=1, le=1000),
    settings: Settings = Depends(get_settings),
    _: None = Depends(require_token),
):
    return _historical_archive(settings).export_bundle(dataset_id, include_payloads=include_payloads, limit=limit)


@app.get("/admin/history/restore-preview/{snapshot_id}")
def admin_history_restore_preview_endpoint(snapshot_id: str, settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _historical_archive(settings).restore_preview(snapshot_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown historical snapshot: {snapshot_id}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.get("/admin/history/retention")
def admin_history_retention_preview_endpoint(
    dataset_id: str = Query(default="", max_length=180),
    retention_days: int = Query(default=3650, ge=1, le=36500),
    max_snapshots: int = Query(default=3650, ge=2, le=50000),
    settings: Settings = Depends(get_settings),
    _: None = Depends(require_token),
):
    return _historical_archive(settings).retention(
        dry_run=True, dataset_id=dataset_id, retention_days=retention_days, max_snapshots=max_snapshots
    )


@app.post("/admin/history/retention/apply")
def admin_history_retention_apply_endpoint(
    request: dict = Body(default={}),
    settings: Settings = Depends(get_settings),
    _: None = Depends(require_token),
):
    return _historical_archive(settings).retention(
        dry_run=bool(request.get("dry_run", True)),
        dataset_id=str(request.get("dataset_id") or ""),
        retention_days=int(request.get("retention_days") or settings.historical_archive_default_retention_days),
        max_snapshots=int(request.get("max_snapshots") or settings.historical_archive_max_snapshots_per_dataset),
    )


# Site Intelligence v2.15.0 — Geospatial Analysis and Spatial Evidence Studio.
def _spatial_evidence(settings: Settings) -> SpatialEvidenceStudio:
    if not settings.spatial_evidence_enabled:
        raise HTTPException(status_code=403, detail="Spatial evidence studio is disabled.")
    try:
        return SpatialEvidenceStudio(settings)
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/public/spatial")
def public_spatial_summary_endpoint(settings: Settings = Depends(get_settings)):
    return _spatial_evidence(settings).public_summary()


@app.get("/public/spatial/layers")
def public_spatial_layers_endpoint(settings: Settings = Depends(get_settings)):
    return _spatial_evidence(settings).layers()


@app.get("/public/spatial/methodology")
def public_spatial_methodology_endpoint(settings: Settings = Depends(get_settings)):
    return _spatial_evidence(settings).methodology()


@app.get("/public/spatial/areas")
def public_spatial_areas_endpoint(settings: Settings = Depends(get_settings)):
    return _spatial_evidence(settings).areas(public=True)


@app.get("/public/spatial/datasets")
def public_spatial_datasets_endpoint(settings: Settings = Depends(get_settings)):
    return _spatial_evidence(settings).datasets(public=True)


@app.get("/public/spatial/evidence")
def public_spatial_evidence_endpoint(
    area_id: str = Query(..., min_length=2, max_length=120),
    dataset_id: str = Query(..., min_length=2, max_length=120),
    version_id: str = Query(default="", max_length=180),
    settings: Settings = Depends(get_settings),
):
    try:
        return _spatial_evidence(settings).export_evidence(area_id, dataset_id, version_id=version_id, public=True)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown or non-public spatial record: {exc.args[0]}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.get("/admin/spatial/control-center")
def admin_spatial_control_center_endpoint(settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    return _spatial_evidence(settings).control_center()


@app.get("/admin/spatial/areas")
def admin_spatial_areas_endpoint(settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    return _spatial_evidence(settings).areas()


@app.post("/admin/spatial/areas")
def admin_spatial_create_area_endpoint(
    request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)
):
    try:
        return _spatial_evidence(settings).create_area(request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/admin/spatial/datasets")
def admin_spatial_datasets_endpoint(
    latest_only: bool = Query(default=True), settings: Settings = Depends(get_settings), _: None = Depends(require_token)
):
    return _spatial_evidence(settings).datasets(latest_only=latest_only)


@app.post("/admin/spatial/datasets/register")
def admin_spatial_register_dataset_endpoint(
    request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)
):
    try:
        return _spatial_evidence(settings).register_dataset(request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/admin/spatial/analyze/intersection")
def admin_spatial_intersection_endpoint(
    request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)
):
    try:
        return _spatial_evidence(settings).intersection(
            str(request.get("area_id") or ""), str(request.get("dataset_id") or ""), str(request.get("version_id") or "")
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown spatial record: {exc.args[0]}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/admin/spatial/analyze/proximity")
def admin_spatial_proximity_endpoint(
    request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)
):
    try:
        return _spatial_evidence(settings).proximity(
            str(request.get("dataset_id") or ""),
            float(request.get("longitude")),
            float(request.get("latitude")),
            float(request.get("max_distance_km") or 100),
            str(request.get("version_id") or ""),
        )
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown spatial dataset: {exc.args[0]}") from exc


@app.post("/admin/spatial/analyze/aggregate")
def admin_spatial_aggregate_endpoint(
    request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)
):
    try:
        return _spatial_evidence(settings).aggregate(
            str(request.get("area_id") or ""),
            str(request.get("dataset_id") or ""),
            str(request.get("metric") or ""),
            str(request.get("version_id") or ""),
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown spatial record: {exc.args[0]}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/admin/spatial/analyze/compare")
def admin_spatial_compare_endpoint(
    request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)
):
    try:
        return _spatial_evidence(settings).compare(
            str(request.get("dataset_id") or ""),
            str(request.get("previous_version_id") or ""),
            str(request.get("current_version_id") or ""),
            str(request.get("metric") or ""),
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown spatial dataset version: {exc.args[0]}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/admin/spatial/analyses")
def admin_spatial_analyses_endpoint(
    limit: int = Query(default=100, ge=1, le=1000), settings: Settings = Depends(get_settings), _: None = Depends(require_token)
):
    return _spatial_evidence(settings).analyses(limit=limit)


@app.get("/admin/spatial/export")
def admin_spatial_export_endpoint(
    area_id: str = Query(..., min_length=2, max_length=120),
    dataset_id: str = Query(..., min_length=2, max_length=120),
    version_id: str = Query(default="", max_length=180),
    settings: Settings = Depends(get_settings),
    _: None = Depends(require_token),
):
    try:
        return _spatial_evidence(settings).export_evidence(area_id, dataset_id, version_id=version_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown spatial record: {exc.args[0]}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


# Site Intelligence v3.4.0 — Statistical Harmonization and Comparable-Series Engine.
def _harmonization(settings: Settings) -> StatisticalHarmonizationEngine:
    if not settings.statistical_harmonization_enabled:
        raise HTTPException(status_code=403, detail="Statistical harmonization is disabled.")
    return StatisticalHarmonizationEngine(settings)


@app.get("/public/harmonization")
def public_harmonization_summary_endpoint(settings: Settings = Depends(get_settings)):
    return _harmonization(settings).public_summary()


@app.get("/public/harmonization/standards")
def public_harmonization_standards_endpoint(settings: Settings = Depends(get_settings)):
    return _harmonization(settings).standards()


@app.get("/public/harmonization/methodology")
def public_harmonization_methodology_endpoint(settings: Settings = Depends(get_settings)):
    return _harmonization(settings).methodology()


@app.get("/public/harmonization/series")
def public_harmonization_series_endpoint(settings: Settings = Depends(get_settings)):
    return _harmonization(settings).series(public=True)


@app.get("/public/harmonization/series/{series_id}")
def public_harmonization_series_detail_endpoint(
    series_id: str, version_id: str = Query(default="", max_length=180), settings: Settings = Depends(get_settings)
):
    try:
        return _harmonization(settings).series_detail(series_id, version_id, public=True)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown or non-public comparable series: {exc.args[0]}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/public/harmonization/compare")
def public_harmonization_compare_endpoint(request: dict = Body(default={}), settings: Settings = Depends(get_settings)):
    try:
        return _harmonization(settings).compare(request, public=True)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown or non-public comparable series: {exc.args[0]}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/public/harmonization/export")
def public_harmonization_export_endpoint(
    series_id: str = Query(..., min_length=2, max_length=120),
    version_id: str = Query(default="", max_length=180),
    settings: Settings = Depends(get_settings),
):
    try:
        return _harmonization(settings).export(series_id, version_id, public=True)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown or non-public comparable series: {exc.args[0]}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.get("/public/harmonization/diagnostics")
def public_harmonization_diagnostics_endpoint(settings: Settings = Depends(get_settings)):
    return _harmonization(settings).diagnostics(public=True)


@app.get("/admin/harmonization/control-center")
def admin_harmonization_control_center_endpoint(settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    return _harmonization(settings).control_center()


@app.get("/admin/harmonization/series")
def admin_harmonization_series_endpoint(
    latest_only: bool = Query(default=True), settings: Settings = Depends(get_settings), _: None = Depends(require_token)
):
    return _harmonization(settings).series(latest_only=latest_only)


@app.post("/admin/harmonization/series/register")
def admin_harmonization_register_endpoint(
    request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)
):
    try:
        return _harmonization(settings).register_series(request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/admin/harmonization/transform")
def admin_harmonization_transform_endpoint(
    request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)
):
    try:
        return _harmonization(settings).transform(request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown comparable series: {exc.args[0]}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/admin/harmonization/compare")
def admin_harmonization_compare_endpoint(
    request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)
):
    try:
        return _harmonization(settings).compare(request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown comparable series: {exc.args[0]}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/admin/harmonization/export")
def admin_harmonization_export_endpoint(
    series_id: str = Query(..., min_length=2, max_length=120),
    version_id: str = Query(default="", max_length=180),
    settings: Settings = Depends(get_settings),
    _: None = Depends(require_token),
):
    try:
        return _harmonization(settings).export(series_id, version_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown comparable series: {exc.args[0]}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.get("/admin/harmonization/workbench-handoff")
def admin_harmonization_workbench_handoff_endpoint(
    series_id: str = Query(..., min_length=2, max_length=120),
    version_id: str = Query(default="", max_length=180),
    settings: Settings = Depends(get_settings),
    _: None = Depends(require_token),
):
    try:
        return _harmonization(settings).workbench_handoff(series_id, version_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown comparable series: {exc.args[0]}") from exc


# Site Intelligence v3.4.0 — Model Registry, Forecast Evaluation, and Early-Warning Indicators.
def _model_governance(settings: Settings) -> ModelForecastEarlyWarningCenter:
    if not settings.model_governance_enabled:
        raise HTTPException(status_code=403, detail="Model governance is disabled.")
    return ModelForecastEarlyWarningCenter(settings)


@app.get("/public/model-governance")
def public_model_governance_summary_endpoint(settings: Settings = Depends(get_settings)):
    return _model_governance(settings).public_summary()


@app.get("/public/model-governance/methodology")
def public_model_governance_methodology_endpoint(settings: Settings = Depends(get_settings)):
    return _model_governance(settings).methodology()


@app.get("/public/model-governance/diagnostics")
def public_model_governance_diagnostics_endpoint(settings: Settings = Depends(get_settings)):
    return _model_governance(settings).diagnostics(public=True)


@app.get("/public/models")
def public_models_endpoint(settings: Settings = Depends(get_settings)):
    return _model_governance(settings).models(public=True)


@app.get("/public/models/{model_id}")
def public_model_detail_endpoint(model_id: str, model_version: str = Query(default="", max_length=120), settings: Settings = Depends(get_settings)):
    try:
        return _model_governance(settings).model_detail(model_id, model_version, public=True)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown or non-public model: {exc.args[0]}") from exc


@app.get("/public/forecasts")
def public_forecasts_endpoint(model_id: str = Query(default="", max_length=140), limit: int = Query(default=100, ge=1, le=1000), settings: Settings = Depends(get_settings)):
    return _model_governance(settings).forecasts(public=True, model_id=model_id, limit=limit)


@app.get("/public/forecast-evaluations")
def public_forecast_evaluations_endpoint(model_id: str = Query(default="", max_length=140), limit: int = Query(default=100, ge=1, le=1000), settings: Settings = Depends(get_settings)):
    return _model_governance(settings).evaluations(public=True, model_id=model_id, limit=limit)


@app.get("/public/early-warning")
def public_early_warning_endpoint(limit: int = Query(default=100, ge=1, le=1000), settings: Settings = Depends(get_settings)):
    return _model_governance(settings).warning_summary(public=True, limit=limit)


@app.get("/public/model-governance/export")
def public_model_governance_export_endpoint(model_id: str = Query(..., min_length=2, max_length=140), model_version: str = Query(default="", max_length=120), settings: Settings = Depends(get_settings)):
    try:
        return _model_governance(settings).export_governance_packet(model_id, model_version, public=True)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown or non-public model: {exc.args[0]}") from exc


@app.get("/admin/model-governance/control-center")
def admin_model_governance_control_center_endpoint(settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    return _model_governance(settings).control_center()


@app.post("/admin/model-governance/models/register")
def admin_model_register_endpoint(request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _model_governance(settings).register_model(request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/admin/model-governance/forecasts/ingest")
def admin_forecast_ingest_endpoint(request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _model_governance(settings).ingest_forecast(request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown model: {exc.args[0]}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/admin/model-governance/evaluations/run")
def admin_forecast_evaluation_endpoint(request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _model_governance(settings).evaluate_forecast(request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown forecast: {exc.args[0]}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/admin/model-governance/warnings/register")
def admin_warning_register_endpoint(request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _model_governance(settings).register_warning_rule(request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/admin/model-governance/warnings/evaluate")
def admin_warning_evaluate_endpoint(request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _model_governance(settings).evaluate_warning(request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown warning rule: {exc.args[0]}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/admin/model-governance/export")
def admin_model_governance_export_endpoint(model_id: str = Query(..., min_length=2, max_length=140), model_version: str = Query(default="", max_length=120), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _model_governance(settings).export_governance_packet(model_id, model_version)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown model: {exc.args[0]}") from exc


# Site Intelligence v3.4.0 — Evidence Synthesis, Claims, and Contradiction Review.
def _evidence_synthesis(settings: Settings) -> EvidenceSynthesisCenter:
    if not settings.evidence_synthesis_enabled:
        raise HTTPException(status_code=403, detail="Evidence synthesis is disabled.")
    return EvidenceSynthesisCenter(settings)


@app.get("/public/evidence-synthesis")
def public_evidence_synthesis_summary_endpoint(settings: Settings = Depends(get_settings)):
    return _evidence_synthesis(settings).public_summary()


@app.get("/public/evidence-synthesis/methodology")
def public_evidence_synthesis_methodology_endpoint(settings: Settings = Depends(get_settings)):
    return _evidence_synthesis(settings).methodology()


@app.get("/public/evidence-synthesis/diagnostics")
def public_evidence_synthesis_diagnostics_endpoint(settings: Settings = Depends(get_settings)):
    return _evidence_synthesis(settings).diagnostics(public=True)


@app.get("/public/claims")
def public_claims_endpoint(settings: Settings = Depends(get_settings)):
    return _evidence_synthesis(settings).claims(public=True)


@app.get("/public/claims/{claim_id}")
def public_claim_detail_endpoint(claim_id: str, settings: Settings = Depends(get_settings)):
    try:
        return _evidence_synthesis(settings).claim_detail(claim_id, public=True)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown or non-public claim: {exc.args[0]}") from exc


@app.get("/public/claims/{claim_id}/contradictions")
def public_claim_contradictions_endpoint(claim_id: str, settings: Settings = Depends(get_settings)):
    try:
        return _evidence_synthesis(settings).contradiction_review(claim_id, public=True)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown or non-public claim: {exc.args[0]}") from exc


@app.get("/public/evidence-synthesis/export")
def public_evidence_synthesis_export_endpoint(claim_id: str = Query(..., min_length=2, max_length=140), settings: Settings = Depends(get_settings)):
    try:
        return _evidence_synthesis(settings).export_packet(claim_id, public=True)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown or non-public claim: {exc.args[0]}") from exc


@app.get("/admin/evidence-synthesis/control-center")
def admin_evidence_synthesis_control_center_endpoint(settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    return _evidence_synthesis(settings).control_center()


@app.post("/admin/evidence-synthesis/claims/register")
def admin_evidence_claim_register_endpoint(request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _evidence_synthesis(settings).register_claim(request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/admin/evidence-synthesis/evidence/add")
def admin_evidence_add_endpoint(request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _evidence_synthesis(settings).add_evidence(request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown claim: {exc.args[0]}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/admin/evidence-synthesis/uncertainty/record")
def admin_evidence_uncertainty_endpoint(request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _evidence_synthesis(settings).record_uncertainty(request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown claim: {exc.args[0]}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/admin/evidence-synthesis/claims/review")
def admin_evidence_claim_review_endpoint(request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _evidence_synthesis(settings).review_claim(request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown claim: {exc.args[0]}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/admin/evidence-synthesis/synthesize")
def admin_evidence_synthesize_endpoint(request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _evidence_synthesis(settings).synthesize(request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown claim: {exc.args[0]}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/admin/evidence-synthesis/export")
def admin_evidence_synthesis_export_endpoint(claim_id: str = Query(..., min_length=2, max_length=140), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _evidence_synthesis(settings).export_packet(claim_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown claim: {exc.args[0]}") from exc


@app.get("/admin/evidence-synthesis/handoff")
def admin_evidence_synthesis_handoff_endpoint(claim_id: str = Query(..., min_length=2, max_length=140), destination: str = Query(...), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _evidence_synthesis(settings).handoff(claim_id, destination)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown claim: {exc.args[0]}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


# Site Intelligence v3.4.0 — Intelligence Publishing and Story Map Studio.
def _knowledge_graph(settings: Settings) -> KnowledgeGraphExplorer:
    if not settings.knowledge_graph_enabled:
        raise HTTPException(status_code=403, detail="Knowledge graph is disabled.")
    return KnowledgeGraphExplorer(settings)


@app.get("/public/knowledge-graph")
def public_knowledge_graph_summary_endpoint(settings: Settings = Depends(get_settings)):
    return _knowledge_graph(settings).public_summary()


@app.get("/public/knowledge-graph/methodology")
def public_knowledge_graph_methodology_endpoint(settings: Settings = Depends(get_settings)):
    return _knowledge_graph(settings).methodology()


@app.get("/public/knowledge-graph/diagnostics")
def public_knowledge_graph_diagnostics_endpoint(settings: Settings = Depends(get_settings)):
    return _knowledge_graph(settings).diagnostics(public=True)


@app.get("/public/knowledge-graph/entities")
def public_knowledge_graph_entities_endpoint(entity_type: str = Query(default="", max_length=120), q: str = Query(default="", max_length=500), limit: int = Query(default=100, ge=1, le=1000), settings: Settings = Depends(get_settings)):
    return _knowledge_graph(settings).entities(public=True, entity_type=entity_type, query=q, limit=limit)


@app.get("/public/knowledge-graph/entities/{entity_id}")
def public_knowledge_graph_entity_endpoint(entity_id: str, as_of: str = Query(default="", max_length=120), settings: Settings = Depends(get_settings)):
    try:
        return _knowledge_graph(settings).entity_detail(entity_id, public=True, as_of=as_of)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown or non-public entity: {exc.args[0]}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/public/knowledge-graph/relationships")
def public_knowledge_graph_relationships_endpoint(relationship_type: str = Query(default="", max_length=120), entity_id: str = Query(default="", max_length=180), as_of: str = Query(default="", max_length=120), limit: int = Query(default=200, ge=1, le=1000), settings: Settings = Depends(get_settings)):
    try:
        return _knowledge_graph(settings).relationships(public=True, relationship_type=relationship_type, entity_id=entity_id, as_of=as_of, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/public/knowledge-graph/resolve")
def public_knowledge_graph_resolve_endpoint(q: str = Query(..., min_length=1, max_length=500), namespace: str = Query(default="", max_length=120), settings: Settings = Depends(get_settings)):
    return _knowledge_graph(settings).resolve(q, public=True, namespace=namespace)


@app.get("/public/knowledge-graph/traverse")
def public_knowledge_graph_traverse_endpoint(entity_id: str = Query(..., min_length=1, max_length=180), depth: int = Query(default=2, ge=0, le=12), direction: str = Query(default="both"), relationship_type: list[str] = Query(default=[]), as_of: str = Query(default="", max_length=120), settings: Settings = Depends(get_settings)):
    try:
        return _knowledge_graph(settings).traverse(entity_id, public=True, depth=depth, direction=direction, relationship_types=relationship_type, as_of=as_of)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown or non-public entity: {exc.args[0]}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/public/knowledge-graph/path")
def public_knowledge_graph_path_endpoint(source_id: str = Query(..., min_length=1, max_length=180), target_id: str = Query(..., min_length=1, max_length=180), max_depth: int = Query(default=4, ge=1, le=12), relationship_type: list[str] = Query(default=[]), as_of: str = Query(default="", max_length=120), settings: Settings = Depends(get_settings)):
    try:
        return _knowledge_graph(settings).shortest_path(source_id, target_id, public=True, max_depth=max_depth, relationship_types=relationship_type, as_of=as_of)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown or non-public entity: {exc.args[0]}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/public/knowledge-graph/export")
def public_knowledge_graph_export_endpoint(entity_id: str = Query(..., min_length=1, max_length=180), depth: int = Query(default=2, ge=0, le=12), as_of: str = Query(default="", max_length=120), settings: Settings = Depends(get_settings)):
    try:
        return _knowledge_graph(settings).export_subgraph(entity_id, public=True, depth=depth, as_of=as_of)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown or non-public entity: {exc.args[0]}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/admin/knowledge-graph/control-center")
def admin_knowledge_graph_control_center_endpoint(settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    return _knowledge_graph(settings).control_center()


@app.post("/admin/knowledge-graph/entities/register")
def admin_knowledge_graph_entity_register_endpoint(request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _knowledge_graph(settings).register_entity(request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/admin/knowledge-graph/aliases/register")
def admin_knowledge_graph_alias_register_endpoint(request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _knowledge_graph(settings).register_alias(request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown entity: {exc.args[0]}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/admin/knowledge-graph/relationships/register")
def admin_knowledge_graph_relationship_register_endpoint(request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _knowledge_graph(settings).register_relationship(request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown entity: {exc.args[0]}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/admin/knowledge-graph/reconcile/preview")
def admin_knowledge_graph_reconciliation_endpoint(request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    return _knowledge_graph(settings).preview_reconciliation(request)


@app.get("/admin/knowledge-graph/export")
def admin_knowledge_graph_export_endpoint(entity_id: str = Query(..., min_length=1, max_length=180), depth: int = Query(default=2, ge=0, le=12), as_of: str = Query(default="", max_length=120), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _knowledge_graph(settings).export_subgraph(entity_id, depth=depth, as_of=as_of)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown entity: {exc.args[0]}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/admin/knowledge-graph/platform-core-handoff")
def admin_knowledge_graph_core_handoff_endpoint(entity_id: str = Query(..., min_length=1, max_length=180), depth: int = Query(default=2, ge=0, le=12), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _knowledge_graph(settings).platform_core_handoff(entity_id, depth=depth)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown entity: {exc.args[0]}") from exc


# Site Intelligence v3.4.0 — Intelligence Publishing and Story Map Studio.
def _intelligence_publishing(settings: Settings) -> IntelligencePublishingStudio:
    if not settings.intelligence_publishing_enabled:
        raise HTTPException(status_code=403, detail="Intelligence publishing is disabled.")
    return IntelligencePublishingStudio(settings)


@app.get("/public/intelligence-publishing")
def public_intelligence_publishing_summary_endpoint(settings: Settings = Depends(get_settings)):
    return _intelligence_publishing(settings).public_summary()


@app.get("/public/intelligence-publishing/methodology")
def public_intelligence_publishing_methodology_endpoint(settings: Settings = Depends(get_settings)):
    return _intelligence_publishing(settings).methodology()


@app.get("/public/intelligence-publishing/diagnostics")
def public_intelligence_publishing_diagnostics_endpoint(settings: Settings = Depends(get_settings)):
    return _intelligence_publishing(settings).diagnostics(public=True)


@app.get("/public/intelligence-publications")
def public_intelligence_publications_endpoint(limit: int = Query(default=100, ge=1, le=1000), settings: Settings = Depends(get_settings)):
    return _intelligence_publishing(settings).public_publications(limit=limit)


@app.get("/public/intelligence-publications/{publication_id}")
def public_intelligence_publication_detail_endpoint(publication_id: str, settings: Settings = Depends(get_settings)):
    try:
        return _intelligence_publishing(settings).publication_detail(publication_id, public=True)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown or non-public publication: {exc.args[0]}") from exc


@app.get("/public/intelligence-publications/{publication_id}/story-map")
def public_intelligence_story_map_endpoint(publication_id: str, settings: Settings = Depends(get_settings)):
    try:
        return _intelligence_publishing(settings).story_map(publication_id, public=True)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown or non-public publication: {exc.args[0]}") from exc


@app.get("/public/intelligence-publications/{publication_id}/versions")
def public_intelligence_publication_versions_endpoint(publication_id: str, settings: Settings = Depends(get_settings)):
    try:
        return _intelligence_publishing(settings).version_history(publication_id, public=True)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown or non-public publication: {exc.args[0]}") from exc


@app.get("/public/intelligence-publications/{publication_id}/export")
def public_intelligence_publication_export_endpoint(publication_id: str, settings: Settings = Depends(get_settings)):
    try:
        return _intelligence_publishing(settings).export_publication(publication_id, public=True)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown or non-public publication: {exc.args[0]}") from exc


@app.get("/admin/intelligence-publishing/control-center")
def admin_intelligence_publishing_control_center_endpoint(settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    return _intelligence_publishing(settings).control_center()


@app.post("/admin/intelligence-publishing/projects")
def admin_intelligence_publishing_project_endpoint(request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _intelligence_publishing(settings).create_project(request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/admin/intelligence-publishing/projects/{project_id}/blocks")
def admin_intelligence_publishing_block_endpoint(project_id: str, request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _intelligence_publishing(settings).add_block(project_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown publication project: {exc.args[0]}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/admin/intelligence-publishing/projects/{project_id}/review/submit")
def admin_intelligence_publishing_review_submit_endpoint(project_id: str, request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _intelligence_publishing(settings).submit_review(project_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown publication project: {exc.args[0]}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/admin/intelligence-publishing/projects/{project_id}/review/decide")
def admin_intelligence_publishing_review_decide_endpoint(project_id: str, request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _intelligence_publishing(settings).decide_review(project_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown publication project: {exc.args[0]}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/admin/intelligence-publishing/projects/{project_id}/publish")
def admin_intelligence_publishing_publish_endpoint(project_id: str, request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _intelligence_publishing(settings).publish_project(project_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown publication project: {exc.args[0]}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/admin/intelligence-publishing/projects/{project_id}/export")
def admin_intelligence_publishing_export_endpoint(project_id: str, settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _intelligence_publishing(settings).export_publication(project_id, public=False)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown publication project: {exc.args[0]}") from exc


@app.get("/admin/intelligence-publishing/projects/{project_id}/wordpress-handoff")
def admin_intelligence_publishing_wordpress_handoff_endpoint(project_id: str, settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _intelligence_publishing(settings).wordpress_handoff(project_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown publication project: {exc.args[0]}") from exc


def _scheduled_monitoring(settings: Settings) -> ScheduledMonitoringCenter:
    if not settings.scheduled_monitoring_enabled:
        raise HTTPException(status_code=503, detail="Scheduled monitoring is disabled.")
    return ScheduledMonitoringCenter(settings)


@app.get("/public/scheduled-monitoring")
def public_scheduled_monitoring_summary_endpoint(settings: Settings = Depends(get_settings)):
    return _scheduled_monitoring(settings).public_summary()


@app.get("/public/scheduled-monitoring/diagnostics")
def public_scheduled_monitoring_diagnostics_endpoint(settings: Settings = Depends(get_settings)):
    return _scheduled_monitoring(settings).diagnostics(public=True)


@app.get("/public/intelligence-digests")
def public_intelligence_digests_endpoint(limit: int = Query(default=50, ge=1, le=500), settings: Settings = Depends(get_settings)):
    return {"ok": True, "version": APP_VERSION, "digests": _scheduled_monitoring(settings).digests(public=True, limit=limit)}


@app.get("/public/intelligence-digests/{digest_id}")
def public_intelligence_digest_endpoint(digest_id: str, settings: Settings = Depends(get_settings)):
    digest = next((x for x in _scheduled_monitoring(settings).digests(public=True, limit=1000) if x.get("digest_id") == digest_id), None)
    if not digest:
        raise HTTPException(status_code=404, detail="Published digest not found.")
    return {"ok": True, "version": APP_VERSION, "digest": digest}


@app.get("/public/intelligence-feeds")
def public_intelligence_feeds_endpoint(settings: Settings = Depends(get_settings)):
    return {"ok": True, "version": APP_VERSION, "feeds": _scheduled_monitoring(settings).feeds(public=True)}


@app.get("/public/intelligence-feeds/{feed_id}")
def public_intelligence_feed_endpoint(feed_id: str, format: str = Query(default="json", pattern="^(json|rss|atom)$"), settings: Settings = Depends(get_settings)):
    try:
        media_type, body = _scheduled_monitoring(settings).feed_payload(feed_id, format)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Feed not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return Response(content=body, media_type=media_type, headers={"X-SC-Site-Intelligence-Version": APP_VERSION})


@app.get("/admin/scheduled-monitoring/control-center")
def admin_scheduled_monitoring_control_center_endpoint(settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    return _scheduled_monitoring(settings).control_center()


@app.post("/admin/scheduled-monitoring/monitors")
def admin_scheduled_monitoring_monitor_endpoint(request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _scheduled_monitoring(settings).save_monitor(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/scheduled-monitoring/monitors/{monitor_id}/check")
def admin_scheduled_monitoring_check_endpoint(monitor_id: str, request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _scheduled_monitoring(settings).check_monitor(monitor_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Monitor not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/scheduled-monitoring/run-due")
def admin_scheduled_monitoring_run_due_endpoint(dry_run: bool = Query(default=True), limit: int = Query(default=100, ge=1, le=500), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    return _scheduled_monitoring(settings).run_due(dry_run=dry_run, limit=limit)


@app.post("/admin/scheduled-monitoring/digests")
def admin_scheduled_monitoring_digest_endpoint(request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _scheduled_monitoring(settings).generate_digest(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/scheduled-monitoring/digests/{digest_id}/review")
def admin_scheduled_monitoring_digest_review_endpoint(digest_id: str, request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _scheduled_monitoring(settings).approve_digest(digest_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Digest not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/scheduled-monitoring/digests/{digest_id}/deliver")
def admin_scheduled_monitoring_digest_delivery_endpoint(digest_id: str, request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _scheduled_monitoring(settings).deliver_digest(digest_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Digest not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/scheduled-monitoring/feeds")
def admin_scheduled_monitoring_feed_endpoint(request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _scheduled_monitoring(settings).save_feed(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc



def _institutional_workspaces(settings: Settings) -> InstitutionalWorkspaceCenter:
    if not settings.institutional_workspaces_enabled:
        raise HTTPException(status_code=503, detail="Institutional workspaces are disabled.")
    return InstitutionalWorkspaceCenter(settings)


def _workspace_actor(request: dict[str, Any]) -> tuple[str, str]:
    return str(request.get("actor_role") or "administrator"), str(request.get("actor_id") or "system")


@app.get("/public/institutional-workspaces")
def public_institutional_workspaces_endpoint(settings: Settings = Depends(get_settings)):
    return _institutional_workspaces(settings).public_summary()


@app.get("/public/institutional-workspaces/diagnostics")
def public_institutional_workspaces_diagnostics_endpoint(settings: Settings = Depends(get_settings)):
    return _institutional_workspaces(settings).diagnostics(public=True)


@app.get("/public/institutional-workspaces/{workspace_id}")
def public_institutional_workspace_endpoint(workspace_id: str, settings: Settings = Depends(get_settings)):
    try:
        return {"ok": True, "version": APP_VERSION, "workspace": _institutional_workspaces(settings).workspace_detail(workspace_id, public=True)}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Published public workspace not found.") from exc


@app.get("/admin/institutional-workspaces/control-center")
def admin_institutional_workspaces_control_center_endpoint(settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    return _institutional_workspaces(settings).control_center()


@app.get("/admin/institutional-workspaces/{workspace_id}")
def admin_institutional_workspace_endpoint(workspace_id: str, settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _institutional_workspaces(settings).workspace_detail(workspace_id, public=False)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Workspace not found.") from exc


@app.post("/admin/institutional-workspaces")
def admin_institutional_workspace_create_endpoint(request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    role, actor = _workspace_actor(request)
    try:
        return _institutional_workspaces(settings).create_workspace(request, role, actor)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/institutional-workspaces/{workspace_id}")
def admin_institutional_workspace_update_endpoint(workspace_id: str, request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    role, actor = _workspace_actor(request)
    try:
        return _institutional_workspaces(settings).update_workspace(workspace_id, request, role, actor)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Workspace not found.") from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/institutional-workspaces/{workspace_id}/members")
def admin_institutional_workspace_member_endpoint(workspace_id: str, request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    role, actor = _workspace_actor(request)
    try:
        return _institutional_workspaces(settings).add_member(workspace_id, request, role, actor)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Workspace not found.") from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/institutional-workspaces/{workspace_id}/assignments")
def admin_institutional_workspace_assignment_endpoint(workspace_id: str, request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    role, actor = _workspace_actor(request)
    try:
        return _institutional_workspaces(settings).save_assignment(workspace_id, request, role, actor)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Workspace not found.") from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/institutional-workspaces/{workspace_id}/comments")
def admin_institutional_workspace_comment_endpoint(workspace_id: str, request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    role, actor = _workspace_actor(request)
    try:
        return _institutional_workspaces(settings).add_comment(workspace_id, request, role, actor)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Workspace not found.") from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/institutional-workspaces/{workspace_id}/evidence-reviews")
def admin_institutional_workspace_review_endpoint(workspace_id: str, request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    role, actor = _workspace_actor(request)
    try:
        return _institutional_workspaces(settings).review_evidence(workspace_id, request, role, actor)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Workspace not found.") from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/institutional-workspaces/{workspace_id}/source-collections")
def admin_institutional_workspace_collection_endpoint(workspace_id: str, request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    role, actor = _workspace_actor(request)
    try:
        return _institutional_workspaces(settings).save_collection(workspace_id, request, role, actor)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Workspace not found.") from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/admin/institutional-workspaces/{workspace_id}/retention-preview")
def admin_institutional_workspace_retention_preview_endpoint(workspace_id: str, cutoff_days: int | None = Query(default=None, ge=30, le=3650), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _institutional_workspaces(settings).retention_preview(workspace_id, cutoff_days)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Workspace not found.") from exc


@app.post("/admin/institutional-workspaces/{workspace_id}/retention")
def admin_institutional_workspace_retention_endpoint(workspace_id: str, request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    role, actor = _workspace_actor(request)
    try:
        return _institutional_workspaces(settings).apply_retention(workspace_id, request, role, actor)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Workspace not found.") from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/admin/institutional-workspaces/{workspace_id}/export")
def admin_institutional_workspace_export_endpoint(workspace_id: str, format: str = Query(default="json", pattern="^(json|zip)$"), actor_role: str = Query(default="publisher"), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        media_type, body = _institutional_workspaces(settings).export_workspace(workspace_id, actor_role, format)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Workspace not found.") from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    suffix = "zip" if format == "zip" else "json"
    return Response(content=body, media_type=media_type, headers={"Content-Disposition": f'attachment; filename="institutional-workspace-{workspace_id}.{suffix}"', "X-SC-Site-Intelligence-Version": APP_VERSION})


@app.get("/public/source-pages")
def public_source_pages(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=404, detail="Public dashboards are disabled.")
    return build_public_source_page_directory()


@app.get("/public/source-pages/navigation")
def public_source_page_navigation(current: str = Query(""), settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=404, detail="Public dashboards are disabled.")
    return build_public_source_navigation(current)


@app.get("/public/source-pages/templates")
def public_source_page_templates(slug: str | None = Query(default=None), settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=404, detail="Public dashboards are disabled.")
    try:
        return build_public_source_page_templates(slug)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown public source page slug: {slug}") from exc


@app.get("/public/source-pages/visual-qa")
def public_source_page_visual_qa(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=404, detail="Public dashboards are disabled.")
    return build_public_source_page_visual_qa()

@app.get("/public/sources")
def public_sources_endpoint(
    domain: str = Query(""),
    state: str = Query(""),
    feature: str = Query(""),
    query: str = Query(""),
    country: str = Query(""),
    include_health: bool = Query(False),
    settings: Settings = Depends(get_settings),
):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    return build_source_methodology_directory(
        domain=domain,
        state=state,
        feature=feature,
        query=query,
        country=country,
        include_health=include_health,
    )


@app.get("/public/sources/health")
def public_source_health_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    return build_public_source_health()


@app.get("/public/sources/development-indicators")
def public_development_indicators_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    return build_public_development_indicators()


@app.get("/public/sources/research-metadata")
def public_research_metadata_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    return build_public_research_metadata()


@app.get("/public/sources/publications")
def public_publication_metadata_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    return build_public_publication_metadata()


@app.get("/public/sources/repositories")
def public_repository_intelligence_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    return build_public_repository_intelligence()


@app.get("/public/sources/{source_id}/status")
def public_source_status_record(source_id: str, settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    try:
        return build_source_status(source_id)
    except SourceMethodologyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/public/sources/{source_id}/coverage")
def public_source_coverage_record(source_id: str, settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    try:
        return build_source_coverage(source_id)
    except SourceMethodologyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/public/sources/{source_id}")
def public_source_detail_record(
    source_id: str,
    include_health: bool = Query(False),
    settings: Settings = Depends(get_settings),
):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    try:
        return build_source_detail(source_id, include_health=include_health)
    except SourceMethodologyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/public/indicators/overview")
def public_indicator_overview_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    return build_public_indicator_overview()


@app.get("/public/indicators/sustainability")
def public_sustainability_indicators_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    return build_public_sustainability_indicators()


@app.get("/public/dashboards/climate-energy")
def public_climate_energy_dashboard_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    return public_topic_dashboard("climate-energy")


@app.get("/public/dashboards/environmental-monitoring")
def public_environmental_monitoring_dashboard_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    return public_topic_dashboard("environmental-monitoring")


@app.get("/public/dashboards/biodiversity-land-use")
def public_biodiversity_land_use_dashboard_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    return public_topic_dashboard("biodiversity-land-use")


@app.get("/public/dashboards/knowledge-system")
def public_knowledge_system_dashboard_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    return public_topic_dashboard("knowledge-system")


@app.get("/public/dashboards/search-discovery")
def public_search_discovery_dashboard_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    return public_topic_dashboard("search-discovery")


@app.get("/public/source-methodology")
def public_source_methodology_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    return public_source_methodology()


@app.get("/intelligence/public-topic-dashboards")
def intelligence_public_topic_dashboards(_: None = Depends(require_token)):
    return topic_dashboard_directory()


@app.get("/intelligence/public-topic-page-templates")
def intelligence_public_topic_page_templates(_: None = Depends(require_token)):
    return public_topic_page_templates()


@app.get("/intelligence/public-topic-page-visual-qa")
def intelligence_public_topic_page_visual_qa(_: None = Depends(require_token)):
    return topic_page_visual_qa()


@app.get("/intelligence/public-api-sources")
def intelligence_public_api_sources(_: None = Depends(require_token)):
    return build_public_sources()


@app.get("/intelligence/public-source-health")
def intelligence_public_source_health(_: None = Depends(require_token)):
    return build_public_source_health()

@app.get("/public/landing-page")
def public_landing_page_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public Site Intelligence dashboards are disabled.")
    return public_landing_page()

@app.get("/public/status")
def public_status(settings: Settings = Depends(get_settings)):
    return {
        "ok": True,
        "enabled": settings.public_dashboards_enabled,
        "mode": settings.public_default_mode,
        "version": settings.version,
        "safe_output": True,
        "exposes_raw_ga4": False,
        "exposes_private_strategy": False,
    }


@app.get("/public/methodology")
def public_dashboard_methodology(feature: str = Query(""), query: str = Query("")):
    return build_methodology_directory(feature=feature, query=query)


@app.get("/public/methodology/{method_id}")
def public_methodology_detail_record(method_id: str):
    try:
        return build_methodology_detail(method_id)
    except SourceMethodologyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/public/source-methodology/diagnostics")
def public_source_methodology_diagnostics():
    return build_source_methodology_diagnostics()


@app.get("/public/source-methodology/export")
def public_source_methodology_export(format: str = Query("json"), include_health: bool = Query(True)):
    try:
        body, media_type, filename = build_source_methodology_export(format, include_health=include_health)
    except SourceMethodologyError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return Response(
        content=body,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )




@app.get("/public/saved-views/schema")
def public_saved_views_schema():
    return build_saved_views_schema()


@app.post("/public/saved-views/validate")
def public_saved_views_validate(manifest: dict[str, Any]):
    return validate_saved_view_manifest(manifest)


@app.get("/public/saved-views/migrations")
def public_saved_views_migrations():
    return build_saved_views_migrations()


@app.get("/public/saved-views/diagnostics")
def public_saved_views_diagnostics():
    return build_saved_views_diagnostics()


@app.get("/public/experience-profile")
def public_experience_profile():
    return build_experience_profile()


@app.get("/public/experience-profile/checklist")
def public_experience_checklist():
    return build_experience_checklist()


@app.get("/public/experience-profile/diagnostics")
def public_experience_diagnostics():
    return build_experience_diagnostics()


@app.get("/public/launch-profile")
def public_launch_profile():
    return build_launch_profile()


@app.get("/public/launch-profile/checklist")
def public_launch_checklist():
    return build_launch_checklist()


@app.get("/public/launch-profile/materials")
def public_launch_materials():
    return build_launch_materials()


@app.get("/public/launch-profile/diagnostics")
def public_launch_diagnostics():
    return build_launch_diagnostics()


@app.get("/public/launch-profile/portfolio")
def public_launch_portfolio(format: str = Query("json")):
    normalized = str(format).strip().lower()
    if normalized == "json":
        return build_portfolio_manifest()
    if normalized in {"md", "markdown"}:
        return PlainTextResponse(
            build_portfolio_markdown(),
            media_type="text/markdown; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="site-intelligence-portfolio.md"'},
        )
    raise HTTPException(status_code=422, detail="Supported portfolio formats are json and markdown.")


@app.get("/public/observatory")
def public_observatory_profile():
    return build_observatory_profile()


@app.get("/public/observatory/catalog")
def public_observatory_catalog():
    return build_observatory_catalog()


@app.get("/public/observatory/audit/{artifact_id}")
def public_observatory_audit_record(artifact_id: str):
    try:
        return build_observatory_audit_record(artifact_id)
    except ObservatoryError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/public/observatory/lineage")
def public_observatory_lineage():
    return build_observatory_lineage()


@app.get("/public/observatory/verification")
def public_observatory_verification():
    return build_observatory_verification()


@app.post("/public/observatory/verify")
def public_observatory_verify(request: dict[str, Any]):
    payload = request.get("payload")
    if "payload" not in request:
        raise HTTPException(status_code=422, detail="Verification request must contain payload.")
    try:
        return verify_observatory_payload(payload, request.get("expected_digest"))
    except ObservatoryError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/public/observatory/release-ledger")
def public_observatory_release_ledger():
    return build_observatory_release_ledger()


@app.get("/public/observatory/diagnostics")
def public_observatory_diagnostics():
    return build_observatory_diagnostics()


@app.get("/public/observatory/export")
def public_observatory_export(format: str = Query("json")):
    normalized = str(format).strip().lower()
    if normalized == "json":
        return build_observatory_audit_packet()
    if normalized in {"md", "markdown"}:
        return PlainTextResponse(
            build_observatory_audit_packet_markdown(),
            media_type="text/markdown; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="site-intelligence-audit-packet.md"'},
        )
    raise HTTPException(status_code=422, detail="Supported observatory export formats are json and markdown.")


@app.get("/public/page-builder")
def public_page_builder_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    return public_page_builder(settings)


@app.get("/public/page-builder/shortcodes")
def public_page_builder_shortcodes_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    return public_shortcode_bundles()


@app.get("/public/page-builder/readiness")
def public_page_builder_readiness_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    return public_page_builder_readiness(settings)


@app.get("/public/page-builder/visual-qa")
def public_page_builder_visual_qa_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    return public_dashboard_visual_qa(settings)


@app.get("/intelligence/public-page-builder")
def public_page_builder_private_endpoint(settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    return public_page_builder(settings)

@app.get("/release/public-summary")
def release_public_summary_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public Site Intelligence dashboards are disabled.")
    return release_public_summary(settings)


@app.get("/release/status")
def release_status_endpoint(settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    return build_release_status(settings)


@app.get("/release/checklist")
def release_checklist_endpoint(settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    return release_checklist(settings)


@app.get("/release/smoke-test")
def release_smoke_test_endpoint(settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    return release_smoke_test(settings)


@app.get("/public/dashboard")
def public_dashboard(
    start_date: str = Query("28daysAgo"),
    end_date: str = Query("today"),
    settings: Settings = Depends(get_settings),
    ga4: GA4Client = Depends(get_ga4_client),
    registry: ContentRegistry = Depends(get_registry),
):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public Site Intelligence dashboards are disabled.")
    try:
        return build_public_dashboard(ga4, registry, start_date=start_date, end_date=end_date)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=502,
            detail={
                "message": "Public dashboard request failed.",
                "error_type": exc.__class__.__name__,
                "error_message": str(exc),
                "hint": "Check GA4/demo mode, registry path, and public dashboard settings.",
            },
        ) from exc


@app.get("/public/knowledge-overview")
def public_knowledge_overview(
    start_date: str = Query("28daysAgo"),
    end_date: str = Query("today"),
    ga4: GA4Client = Depends(get_ga4_client),
    registry: ContentRegistry = Depends(get_registry),
):
    report = build_public_dashboard(ga4, registry, start_date=start_date, end_date=end_date)
    return {
        "ok": True,
        "generated_at": report.get("generated_at"),
        "source": report.get("source"),
        "summary": report.get("summary", {}),
        "knowledge_areas": report.get("knowledge_areas", []),
        "featured_surfaces": report.get("featured_surfaces", []),
        "methodology": report.get("methodology", {}),
    }


@app.get("/public/climate-energy-summary")
def public_climate_energy_summary(
    latitude: Optional[float] = Query(default=None),
    longitude: Optional[float] = Query(default=None),
    country: Optional[str] = Query(default=None),
    start: str = Query("20260101"),
    end: str = Query("20260105"),
    year: int = Query(2024, ge=2021, le=2100),
    live: bool = Query(False),
    settings: Settings = Depends(get_settings),
):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public Site Intelligence dashboards are disabled.")

    def _dump_items(items):
        dumped = []
        for item in (items or [])[:6]:
            if hasattr(item, "model_dump"):
                dumped.append(item.model_dump())
            elif isinstance(item, dict):
                dumped.append(item)
            else:
                dumped.append({"value": str(item)})
        return dumped

    # Public pages should not block on slow upstream APIs. By default, return a
    # stable source-labeled snapshot using the pilot fallback dataset. Editors can
    # test live connector output by calling ?live=true or shortcode live="true".
    if not live:
        lat = settings.external_default_latitude if latitude is None else latitude
        lon = settings.external_default_longitude if longitude is None else longitude
        country_code = country or settings.external_default_country
        power = {**SAMPLE_POWER_DATA, "live": False, "source": "public-stable-snapshot"}
        indicators = _power_indicators(power)
        return {
            "ok": True,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source": "public-stable-snapshot",
            "location": {"latitude": lat, "longitude": lon, "country": country_code, "start": start, "end": end, "emissions_year": year},
            "stability": {
                "status": "stable",
                "public_status": "public_ready",
                "live_sources": 0,
                "fallback_sources": 3,
                "cached_sources": 0,
                "stale_sources": 0,
                "message": "Public snapshot mode is using stable fallback data so the page loads quickly.",
            },
            "indicators": _dump_items(indicators),
            "earth_observation_layers": _dump_items(SAMPLE_GIBS_LAYERS),
            "emissions_summary": {
                **SAMPLE_TRACE,
                "live": False,
                "year": year,
                "country": country_code,
                "top_sectors": SAMPLE_TRACE.get("sectors", [])[:6],
                "message": "Public snapshot mode; live connector checks remain available on private/internal dashboards.",
                "cache": {"status": "public_snapshot"},
            },
            "linked_article_maps": ["Climate Change", "Energy Systems", "Environmental Science", "Earth Science", "Urban Resilience"],
            "linked_workbench_tools": ["energy-systems-calculator", "climate-change-scenario-tool", "environmental-monitoring-qaqc-tool"],
            "notes": [
                "This public section is optimized for reliability and uses source-labeled fallback data by default.",
                "Use private/internal dashboards for live connector diagnostics, cache status, and force-refresh checks.",
            ],
            "methodology": {
                "public_status": "public_ready",
                "summary": "Public climate and energy summaries are stable, source-labeled, and intended as interpretive signals rather than professional advice.",
                "review_note": "Live external API calls can be tested with live=true, but public pages should prefer stable snapshot mode.",
            },
        }

    hub = ExternalDataHub(settings)
    try:
        dashboard = hub.climate_energy_dashboard(
            latitude=latitude,
            longitude=longitude,
            country=country,
            start=start,
            end=end,
            year=year,
            force_refresh=False,
        )
        return {
            "ok": True,
            "generated_at": dashboard.get("generated_at"),
            "source": dashboard.get("source"),
            "location": dashboard.get("location", {}),
            "stability": dashboard.get("stability", {}),
            "indicators": _dump_items(dashboard.get("indicators", [])),
            "earth_observation_layers": _dump_items(dashboard.get("earth_observation_layers", [])),
            "emissions_summary": dashboard.get("emissions_summary", {}),
            "linked_article_maps": dashboard.get("linked_article_maps", []),
            "linked_workbench_tools": dashboard.get("linked_workbench_tools", []),
            "notes": dashboard.get("notes", []),
            "methodology": dashboard.get("methodology", {}),
        }
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=502,
            detail={
                "message": "Public climate and energy live summary failed.",
                "error_type": exc.__class__.__name__,
                "error_message": str(exc),
                "hint": "Use default snapshot mode for public pages or check external connector settings.",
            },
        ) from exc


@app.get("/intelligence/public-readiness")
def intelligence_public_readiness(
    start_date: str = Query("28daysAgo"),
    end_date: str = Query("today"),
    ga4: GA4Client = Depends(get_ga4_client),
    registry: ContentRegistry = Depends(get_registry),
    _: None = Depends(require_token),
):
    try:
        return public_readiness_report(ga4, registry, start_date=start_date, end_date=end_date)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail={"message": "Public readiness request failed.", "error_type": exc.__class__.__name__, "error_message": str(exc)}) from exc


@app.get("/intelligence/event-diagnostics")
def intelligence_event_diagnostics(
    start_date: str = Query("28daysAgo"),
    end_date: str = Query("today"),
    ga4: GA4Client = Depends(get_ga4_client),
    registry: ContentRegistry = Depends(get_registry),
    _: None = Depends(require_token),
):
    try:
        page_rows = ga4.page_report(start_date, end_date)
        event_rows = ga4.event_report(start_date, end_date)
        metrics = build_page_metrics(page_rows, event_rows, registry)
        diagnostics = event_diagnostics(event_rows, metrics)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=502,
            detail={
                "message": "GA4 event-diagnostics request failed.",
                "error_type": exc.__class__.__name__,
                "error_message": str(exc),
                "hint": "Check GA4 credentials and whether Sustainable Catalyst custom events are visible in GA4.",
            },
        ) from exc
    return {
        "ok": True,
        "source": "ga4" if ga4.enabled else "demo",
        "date_range": {"start_date": start_date, "end_date": end_date},
        "diagnostics": diagnostics,
        "recommendations": event_setup_recommendations(diagnostics),
    }


@app.get("/intelligence/conversions")
def intelligence_conversions(
    start_date: str = Query("28daysAgo"),
    end_date: str = Query("today"),
    ga4: GA4Client = Depends(get_ga4_client),
    registry: ContentRegistry = Depends(get_registry),
    _: None = Depends(require_token),
):
    try:
        page_rows = ga4.page_report(start_date, end_date)
        event_rows = ga4.event_report(start_date, end_date)
        metrics = build_page_metrics(page_rows, event_rows, registry)
        diagnostics = event_diagnostics(event_rows, metrics)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=502,
            detail={
                "message": "GA4 conversion-readiness request failed.",
                "error_type": exc.__class__.__name__,
                "error_message": str(exc),
                "hint": "Check GA4 event visibility and event bridge configuration.",
            },
        ) from exc
    return {
        "ok": True,
        "source": "ga4" if ga4.enabled else "demo",
        "date_range": {"start_date": start_date, "end_date": end_date},
        "readiness": diagnostics.get("readiness", {}),
        "events": diagnostics.get("events", []),
    }


@app.get("/intelligence/page-opportunities")
def intelligence_page_opportunities(
    start_date: str = Query("28daysAgo"),
    end_date: str = Query("today"),
    limit: int = Query(25, ge=1, le=100),
    ga4: GA4Client = Depends(get_ga4_client),
    registry: ContentRegistry = Depends(get_registry),
    _: None = Depends(require_token),
):
    try:
        page_rows = ga4.page_report(start_date, end_date)
        event_rows = ga4.event_report(start_date, end_date)
        metrics = build_page_metrics(page_rows, event_rows, registry)
        opportunities = page_opportunities(metrics, limit=limit)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=502,
            detail={
                "message": "GA4 page-opportunities request failed.",
                "error_type": exc.__class__.__name__,
                "error_message": str(exc),
                "hint": "Check GA4 event visibility and page registry mapping.",
            },
        ) from exc
    return {
        "ok": True,
        "source": "ga4" if ga4.enabled else "demo",
        "date_range": {"start_date": start_date, "end_date": end_date},
        "opportunities": opportunities,
    }


@app.get("/intelligence/events")
def intelligence_events_alias(
    start_date: str = Query("28daysAgo"),
    end_date: str = Query("today"),
    ga4: GA4Client = Depends(get_ga4_client),
    registry: ContentRegistry = Depends(get_registry),
    _: None = Depends(require_token),
):
    return intelligence_event_diagnostics(start_date, end_date, ga4, registry, _)


@app.get("/external/connectors")
def external_connectors(settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    hub = ExternalDataHub(settings)
    return {
        "ok": True,
        "version": settings.version,
        "registry": hub.registry.model_dump(),
    }


@app.get("/external/cache")
def external_cache_status(_: None = Depends(require_token)):
    return cache_status()


@app.post("/external/cache/clear")
def external_cache_clear(_: None = Depends(require_token)):
    return clear_cache()


@app.get("/external/health")
def external_health(
    force_refresh: bool = Query(False),
    settings: Settings = Depends(get_settings),
    _: None = Depends(require_token),
):
    hub = ExternalDataHub(settings)
    return {
        "ok": True,
        "source": "external-live" if settings.external_live else "sample-fallback",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "cache": cache_status(),
        "connectors": [item.model_dump() for item in hub.health(force_refresh=force_refresh)],
    }


@app.get("/external/nasa-power/timeseries")
def external_nasa_power_timeseries(
    latitude: Optional[float] = Query(default=None),
    longitude: Optional[float] = Query(default=None),
    start: str = Query("20260101"),
    end: str = Query("20260105"),
    parameters: str = Query("T2M,T2M_MAX,T2M_MIN,PRECTOTCORR,WS10M,ALLSKY_SFC_SW_DWN"),
    force_refresh: bool = Query(False),
    settings: Settings = Depends(get_settings),
    _: None = Depends(require_token),
):
    hub = ExternalDataHub(settings)
    params = [part.strip() for part in parameters.split(",") if part.strip()]
    return {"ok": True, "data": hub.nasa_power_timeseries(latitude, longitude, start, end, params, force_refresh=force_refresh)}


@app.get("/external/nasa-gibs/layers")
def external_nasa_gibs_layers(
    limit: int = Query(12, ge=1, le=100),
    force_refresh: bool = Query(False),
    settings: Settings = Depends(get_settings),
    _: None = Depends(require_token),
):
    hub = ExternalDataHub(settings)
    return {"ok": True, "data": hub.nasa_gibs_layers(limit=limit, force_refresh=force_refresh)}


@app.get("/external/climate-trace/emissions")
def external_climate_trace_emissions(
    year: int = Query(2024, ge=2021, le=2100),
    country: Optional[str] = Query(default=None),
    force_refresh: bool = Query(False),
    settings: Settings = Depends(get_settings),
    _: None = Depends(require_token),
):
    hub = ExternalDataHub(settings)
    return {"ok": True, "data": hub.climate_trace_emissions(year=year, country=country, force_refresh=force_refresh)}


@app.get("/intelligence/dashboards/climate-energy")
def climate_energy_dashboard(
    latitude: Optional[float] = Query(default=None),
    longitude: Optional[float] = Query(default=None),
    country: Optional[str] = Query(default=None),
    start: str = Query("20260101"),
    end: str = Query("20260105"),
    year: int = Query(2024, ge=2021, le=2100),
    force_refresh: bool = Query(False),
    settings: Settings = Depends(get_settings),
    _: None = Depends(require_token),
):
    try:
        hub = ExternalDataHub(settings)
        return hub.climate_energy_dashboard(latitude=latitude, longitude=longitude, country=country, start=start, end=end, year=year, force_refresh=force_refresh)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=502,
            detail={
                "message": "Climate + Energy Intelligence request failed.",
                "error_type": exc.__class__.__name__,
                "error_message": str(exc),
                "hint": "Check external registry path, live connector settings, and upstream API availability.",
            },
        ) from exc


@app.get("/external/advanced/health")
def external_advanced_health(
    force_refresh: bool = Query(False),
    settings: Settings = Depends(get_settings),
    _: None = Depends(require_token),
):
    hub = AdvancedExternalDataHub(settings)
    return {
        "ok": True,
        "version": settings.version,
        "source": "advanced-external-live" if settings.external_live else "advanced-external-fallback",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "connectors": [item.model_dump() for item in hub.health(force_refresh=force_refresh)],
    }


@app.get("/external/noaa/climate")
def external_noaa_climate(
    latitude: Optional[float] = Query(default=None),
    longitude: Optional[float] = Query(default=None),
    force_refresh: bool = Query(False),
    settings: Settings = Depends(get_settings),
    _: None = Depends(require_token),
):
    return {"ok": True, "data": AdvancedExternalDataHub(settings).noaa_weather_climate(latitude, longitude, force_refresh=force_refresh)}


@app.get("/external/eia/energy")
def external_eia_energy(
    state: str = Query("IL"),
    force_refresh: bool = Query(False),
    settings: Settings = Depends(get_settings),
    _: None = Depends(require_token),
):
    return {"ok": True, "data": AdvancedExternalDataHub(settings).eia_energy(state=state, force_refresh=force_refresh)}


@app.get("/external/epa/air-quality")
def external_epa_air_quality(
    state: str = Query("17"),
    county: str = Query("031"),
    force_refresh: bool = Query(False),
    settings: Settings = Depends(get_settings),
    _: None = Depends(require_token),
):
    return {"ok": True, "data": AdvancedExternalDataHub(settings).epa_air_quality(state=state, county=county, force_refresh=force_refresh)}


@app.get("/external/census/context")
def external_census_context(
    state: str = Query("17"),
    county: str = Query("031"),
    force_refresh: bool = Query(False),
    settings: Settings = Depends(get_settings),
    _: None = Depends(require_token),
):
    return {"ok": True, "data": AdvancedExternalDataHub(settings).census_context(state=state, county=county, force_refresh=force_refresh)}


@app.get("/external/usgs/land-cover")
def external_usgs_land_cover(
    latitude: Optional[float] = Query(default=None),
    longitude: Optional[float] = Query(default=None),
    force_refresh: bool = Query(False),
    settings: Settings = Depends(get_settings),
    _: None = Depends(require_token),
):
    return {"ok": True, "data": AdvancedExternalDataHub(settings).usgs_land_cover(latitude, longitude, force_refresh=force_refresh)}


@app.get("/external/gbif/biodiversity")
def external_gbif_biodiversity(
    country: str = Query("US"),
    limit: int = Query(20, ge=1, le=100),
    force_refresh: bool = Query(False),
    settings: Settings = Depends(get_settings),
    _: None = Depends(require_token),
):
    return {"ok": True, "data": AdvancedExternalDataHub(settings).gbif_biodiversity(country=country, limit=limit, force_refresh=force_refresh)}


@app.get("/intelligence/dashboards/environmental-monitoring")
def environmental_monitoring_dashboard(
    latitude: Optional[float] = Query(default=None),
    longitude: Optional[float] = Query(default=None),
    state: str = Query("17"),
    county: str = Query("031"),
    force_refresh: bool = Query(False),
    settings: Settings = Depends(get_settings),
    _: None = Depends(require_token),
):
    return AdvancedExternalDataHub(settings).environmental_monitoring_dashboard(latitude, longitude, state=state, county=county, force_refresh=force_refresh)


@app.get("/intelligence/dashboards/urban-resilience")
def urban_resilience_dashboard(
    latitude: Optional[float] = Query(default=None),
    longitude: Optional[float] = Query(default=None),
    country: str = Query("USA"),
    state: str = Query("17"),
    county: str = Query("031"),
    force_refresh: bool = Query(False),
    settings: Settings = Depends(get_settings),
    _: None = Depends(require_token),
):
    return AdvancedExternalDataHub(settings).urban_resilience_dashboard(latitude, longitude, country=country, state=state, county=county, force_refresh=force_refresh)


@app.get("/intelligence/dashboards/biodiversity-land-use")
def biodiversity_land_use_dashboard(
    latitude: Optional[float] = Query(default=None),
    longitude: Optional[float] = Query(default=None),
    country: str = Query("US"),
    force_refresh: bool = Query(False),
    settings: Settings = Depends(get_settings),
    _: None = Depends(require_token),
):
    return AdvancedExternalDataHub(settings).biodiversity_land_use_dashboard(latitude, longitude, country=country, force_refresh=force_refresh)


@app.get("/intelligence/dashboards/energy-systems")
def energy_systems_dashboard(
    latitude: Optional[float] = Query(default=None),
    longitude: Optional[float] = Query(default=None),
    country: str = Query("USA"),
    state: str = Query("IL"),
    start: str = Query("20260101"),
    end: str = Query("20260105"),
    force_refresh: bool = Query(False),
    settings: Settings = Depends(get_settings),
    _: None = Depends(require_token),
):
    return AdvancedExternalDataHub(settings).energy_systems_dashboard(latitude, longitude, country=country, state=state, start=start, end=end, force_refresh=force_refresh)


@app.get("/search/health")
def search_health(
    settings: Settings = Depends(get_settings),
    _: None = Depends(require_token),
):
    client = SearchConsoleClient(settings)
    return {"ok": True, "search_console": client.diagnostics()}


@app.get("/search/performance")
def search_performance(
    start_date: str = Query("28daysAgo"),
    end_date: str = Query("yesterday"),
    dimensions: str = Query("query,page"),
    row_limit: int = Query(250, ge=1, le=25000),
    settings: Settings = Depends(get_settings),
    _: None = Depends(require_token),
):
    try:
        client = SearchConsoleClient(settings)
        dims = [item.strip() for item in dimensions.split(",") if item.strip()]
        return {
            "ok": True,
            "source": "search-console" if client.enabled else "sample-search",
            "rows": client.performance(start_date=start_date, end_date=end_date, dimensions=dims, row_limit=row_limit),
        }
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=502,
            detail={
                "message": "Search Console performance request failed.",
                "error_type": exc.__class__.__name__,
                "error_message": str(exc),
                "hint": "Check Search Console property access, Google service account access, and SC_SI_SEARCH_CONSOLE_SITE_URL.",
            },
        ) from exc


@app.get("/search/pages")
def search_pages(
    start_date: str = Query("28daysAgo"),
    end_date: str = Query("yesterday"),
    settings: Settings = Depends(get_settings),
    registry: ContentRegistry = Depends(get_registry),
    _: None = Depends(require_token),
):
    try:
        client = SearchConsoleClient(settings)
        return {
            "ok": True,
            "source": "search-console" if client.enabled else "sample-search",
            "pages": client.page_summary(registry, start_date=start_date, end_date=end_date),
        }
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail={"message": "Search page summary request failed.", "error_type": exc.__class__.__name__, "error_message": str(exc)}) from exc


@app.get("/search/queries")
def search_queries(
    start_date: str = Query("28daysAgo"),
    end_date: str = Query("yesterday"),
    settings: Settings = Depends(get_settings),
    _: None = Depends(require_token),
):
    try:
        client = SearchConsoleClient(settings)
        return {
            "ok": True,
            "source": "search-console" if client.enabled else "sample-search",
            "queries": client.query_summary(start_date=start_date, end_date=end_date),
            "topic_momentum": client.topic_momentum(start_date=start_date, end_date=end_date),
        }
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail={"message": "Search query summary request failed.", "error_type": exc.__class__.__name__, "error_message": str(exc)}) from exc


@app.get("/search/opportunities")
def search_opportunities(
    start_date: str = Query("28daysAgo"),
    end_date: str = Query("yesterday"),
    limit: int = Query(25, ge=1, le=100),
    settings: Settings = Depends(get_settings),
    registry: ContentRegistry = Depends(get_registry),
    _: None = Depends(require_token),
):
    try:
        client = SearchConsoleClient(settings)
        pages = client.page_summary(registry, start_date=start_date, end_date=end_date)
        return {
            "ok": True,
            "source": "search-console" if client.enabled else "sample-search",
            "date_range": {"start_date": start_date, "end_date": end_date},
            "opportunities": pages[:limit],
        }
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail={"message": "Search opportunities request failed.", "error_type": exc.__class__.__name__, "error_message": str(exc)}) from exc


@app.get("/intelligence/search")
def search_intelligence(
    start_date: str = Query("28daysAgo"),
    end_date: str = Query("yesterday"),
    settings: Settings = Depends(get_settings),
    registry: ContentRegistry = Depends(get_registry),
    _: None = Depends(require_token),
):
    try:
        client = SearchConsoleClient(settings)
        return client.search_intelligence(registry, start_date=start_date, end_date=end_date)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=502,
            detail={
                "message": "Search Intelligence request failed.",
                "error_type": exc.__class__.__name__,
                "error_message": str(exc),
                "hint": "Add the service account to Search Console, verify the site URL, and confirm Google Search Console API access.",
            },
        ) from exc


@app.get("/seo/metadata")
def seo_metadata(
    start_date: str = Query("28daysAgo"),
    end_date: str = Query("yesterday"),
    limit: int = Query(25, ge=1, le=100),
    settings: Settings = Depends(get_settings),
    registry: ContentRegistry = Depends(get_registry),
    _: None = Depends(require_token),
):
    try:
        client = SearchConsoleClient(settings)
        return metadata_review(client, registry, start_date=start_date, end_date=end_date, limit=limit)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=502,
            detail={
                "message": "Metadata Intelligence request failed.",
                "error_type": exc.__class__.__name__,
                "error_message": str(exc),
                "hint": "Check Search Console access and registry mapping before running metadata/title review.",
            },
        ) from exc


@app.get("/seo/internal-links")
def seo_internal_links(
    start_date: str = Query("28daysAgo"),
    end_date: str = Query("yesterday"),
    limit: int = Query(25, ge=1, le=100),
    settings: Settings = Depends(get_settings),
    registry: ContentRegistry = Depends(get_registry),
    _: None = Depends(require_token),
):
    try:
        client = SearchConsoleClient(settings)
        return internal_link_review(client, registry, start_date=start_date, end_date=end_date, limit=limit)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=502,
            detail={
                "message": "Internal Link Intelligence request failed.",
                "error_type": exc.__class__.__name__,
                "error_message": str(exc),
                "hint": "Check Search Console access, registry mapping, and page summary availability.",
            },
        ) from exc


@app.get("/seo/recommendations")
def seo_recommendation_report(
    start_date: str = Query("28daysAgo"),
    end_date: str = Query("yesterday"),
    limit: int = Query(25, ge=1, le=100),
    settings: Settings = Depends(get_settings),
    registry: ContentRegistry = Depends(get_registry),
    _: None = Depends(require_token),
):
    try:
        client = SearchConsoleClient(settings)
        return seo_recommendations(client, registry, start_date=start_date, end_date=end_date, limit=limit)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=502,
            detail={
                "message": "SEO Recommendation Intelligence request failed.",
                "error_type": exc.__class__.__name__,
                "error_message": str(exc),
                "hint": "Check Search Console access and registry mapping.",
            },
        ) from exc


@app.get("/intelligence/seo")
def seo_intelligence_report(
    start_date: str = Query("28daysAgo"),
    end_date: str = Query("yesterday"),
    limit: int = Query(25, ge=1, le=100),
    settings: Settings = Depends(get_settings),
    registry: ContentRegistry = Depends(get_registry),
    _: None = Depends(require_token),
):
    try:
        client = SearchConsoleClient(settings)
        return {
            "ok": True,
            "source": "search-console" if client.enabled else "sample-search",
            "metadata": metadata_review(client, registry, start_date=start_date, end_date=end_date, limit=limit),
            "internal_links": internal_link_review(client, registry, start_date=start_date, end_date=end_date, limit=limit),
            "recommendations": seo_recommendations(client, registry, start_date=start_date, end_date=end_date, limit=limit),
        }
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=502,
            detail={
                "message": "Combined SEO Intelligence request failed.",
                "error_type": exc.__class__.__name__,
                "error_message": str(exc),
                "hint": "Check Search Console access and registry mapping.",
            },
        ) from exc


@app.get("/indexing/sitemap")
def indexing_sitemap(
    settings: Settings = Depends(get_settings),
    registry: ContentRegistry = Depends(get_registry),
    _: None = Depends(require_token),
):
    try:
        return sitemap_report(settings, registry)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=502,
            detail={
                "message": "Sitemap coverage request failed.",
                "error_type": exc.__class__.__name__,
                "error_message": str(exc),
                "hint": "Check SC_SI_SITEMAP_URL, sitemap availability, and registry path.",
            },
        ) from exc


@app.get("/indexing/coverage")
def indexing_coverage(
    start_date: str = Query("28daysAgo"),
    end_date: str = Query("yesterday"),
    settings: Settings = Depends(get_settings),
    registry: ContentRegistry = Depends(get_registry),
    ga4: GA4Client = Depends(get_ga4_client),
    _: None = Depends(require_token),
):
    try:
        return indexing_intelligence(settings, registry, ga4, SearchConsoleClient(settings), start_date=start_date, end_date=end_date)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=502,
            detail={
                "message": "Indexing coverage request failed.",
                "error_type": exc.__class__.__name__,
                "error_message": str(exc),
                "hint": "Check sitemap fetch settings, GA4/Search Console access, and registry mapping.",
            },
        ) from exc


@app.get("/indexing/orphans")
def indexing_orphans(
    start_date: str = Query("28daysAgo"),
    end_date: str = Query("yesterday"),
    limit: int = Query(25, ge=1, le=100),
    settings: Settings = Depends(get_settings),
    registry: ContentRegistry = Depends(get_registry),
    ga4: GA4Client = Depends(get_ga4_client),
    _: None = Depends(require_token),
):
    try:
        intel = indexing_intelligence(settings, registry, ga4, SearchConsoleClient(settings), start_date=start_date, end_date=end_date)
        return orphan_candidates(intel, limit=limit)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail={"message": "Orphan candidate request failed.", "error_type": exc.__class__.__name__, "error_message": str(exc)}) from exc


@app.get("/indexing/404s")
def indexing_404s(
    start_date: str = Query("28daysAgo"),
    end_date: str = Query("yesterday"),
    limit: int = Query(25, ge=1, le=100),
    settings: Settings = Depends(get_settings),
    registry: ContentRegistry = Depends(get_registry),
    ga4: GA4Client = Depends(get_ga4_client),
    _: None = Depends(require_token),
):
    try:
        intel = indexing_intelligence(settings, registry, ga4, SearchConsoleClient(settings), start_date=start_date, end_date=end_date)
        return four_oh_four_report(intel, limit=limit)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail={"message": "404 intelligence request failed.", "error_type": exc.__class__.__name__, "error_message": str(exc)}) from exc


@app.get("/indexing/recommendations")
def indexing_recommendation_report(
    start_date: str = Query("28daysAgo"),
    end_date: str = Query("yesterday"),
    limit: int = Query(25, ge=1, le=100),
    settings: Settings = Depends(get_settings),
    registry: ContentRegistry = Depends(get_registry),
    ga4: GA4Client = Depends(get_ga4_client),
    _: None = Depends(require_token),
):
    try:
        intel = indexing_intelligence(settings, registry, ga4, SearchConsoleClient(settings), start_date=start_date, end_date=end_date)
        return indexing_recommendations(intel, limit=limit)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail={"message": "Indexing recommendation request failed.", "error_type": exc.__class__.__name__, "error_message": str(exc)}) from exc


@app.get("/intelligence/indexing")
def indexing_intelligence_report(
    start_date: str = Query("28daysAgo"),
    end_date: str = Query("yesterday"),
    settings: Settings = Depends(get_settings),
    registry: ContentRegistry = Depends(get_registry),
    ga4: GA4Client = Depends(get_ga4_client),
    _: None = Depends(require_token),
):
    try:
        return indexing_intelligence(settings, registry, ga4, SearchConsoleClient(settings), start_date=start_date, end_date=end_date)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=502,
            detail={
                "message": "Combined Indexing Intelligence request failed.",
                "error_type": exc.__class__.__name__,
                "error_message": str(exc),
                "hint": "Check sitemap, GA4, Search Console, and registry configuration.",
            },
        ) from exc



# ---------------------------------------------------------------------------
# Report Generator and Export Intelligence (v0.7.0)
# ---------------------------------------------------------------------------

REPORT_FORMATS = {"json", "markdown", "md", "csv"}


def _format_report_response(report: dict, export_format: str = "json", filename: str = "site-intelligence-report"):
    fmt = (export_format or "json").lower().strip()
    if fmt not in REPORT_FORMATS:
        raise HTTPException(status_code=400, detail="Unsupported report format. Use json, markdown, or csv.")
    if fmt in {"markdown", "md"}:
        return PlainTextResponse(
            to_markdown(report),
            media_type="text/markdown; charset=utf-8",
            headers={"Content-Disposition": f'inline; filename="{filename}.md"'},
        )
    if fmt == "csv":
        return PlainTextResponse(
            to_csv(report),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'inline; filename="{filename}.csv"'},
        )
    return report


def _site_report_data(ga4: GA4Client, registry: ContentRegistry, start_date: str, end_date: str) -> dict:
    page_rows = ga4.page_report(start_date, end_date)
    event_rows = ga4.event_report(start_date, end_date)
    metrics = build_page_metrics(page_rows, event_rows, registry)
    diagnostics = event_diagnostics(event_rows, metrics)
    dashboard = DashboardResponse(
        generated_at=datetime.now(timezone.utc).isoformat(),
        source="ga4" if ga4.enabled else "demo",
        date_range={"start_date": start_date, "end_date": end_date},
        totals=dashboard_totals(metrics),
        top_pages=metrics[:25],
        hub_summary=hub_summary(metrics),
        recommendations=site_recommendations(metrics) + event_setup_recommendations(diagnostics),
        registry_count=registry.count(),
        unmapped_pages=unmapped_suggestions(metrics, registry, limit=12),
        mapping_coverage=mapping_coverage(metrics),
        event_diagnostics=diagnostics,
        conversion_readiness=diagnostics.get("readiness", {}),
    ).model_dump()
    return site_intelligence_report(dashboard)


def _search_report_data(settings: Settings, registry: ContentRegistry, start_date: str, end_date: str) -> dict:
    search = SearchConsoleClient(settings).search_intelligence(registry, start_date=start_date, end_date=end_date)
    return search_intelligence_report(search)


def _content_report_data(ga4: GA4Client, settings: Settings, registry: ContentRegistry, start_date: str, end_date: str, prior_start_date: str, prior_end_date: str, limit: int) -> dict:
    search_client = SearchConsoleClient(settings)
    publishing = publishing_intelligence(
        ga4,
        search_client,
        registry,
        start_date=start_date,
        end_date=end_date,
        prior_start_date=prior_start_date,
        prior_end_date=prior_end_date,
        limit=limit,
    )
    return content_strategy_report(publishing)


def _indexing_report_data(settings: Settings, registry: ContentRegistry, ga4: GA4Client, start_date: str, end_date: str) -> dict:
    search_client = SearchConsoleClient(settings)
    intel = indexing_intelligence(settings, registry, ga4, search_client, start_date=start_date, end_date=end_date)
    return indexing_report(intel)


def _external_sources_report_data(settings: Settings) -> dict:
    base_hub = ExternalDataHub(settings)
    advanced_hub = AdvancedExternalDataHub(settings)
    base_health = {
        "ok": True,
        "source": "external-live" if settings.external_live else "external-fallback",
        "connectors": [item.model_dump() for item in base_hub.health()],
        "source_notes": [
            "NASA POWER, NASA GIBS, and Climate TRACE support the first climate/energy pilot layer.",
            "Public dashboards should use cached or snapshot mode unless live API latency is acceptable.",
        ],
    }
    advanced_health = {
        "ok": True,
        "source": "advanced-external-live" if settings.external_live else "advanced-external-fallback",
        "connectors": [item.model_dump() for item in advanced_hub.health()],
    }
    return external_sources_report(base_health, advanced_health)


def _climate_energy_report_data(settings: Settings, latitude: Optional[float], longitude: Optional[float], country: Optional[str], start: str, end: str, year: int, live: bool) -> dict:
    if live:
        summary = ExternalDataHub(settings).climate_energy_dashboard(latitude=latitude, longitude=longitude, country=country, start=start, end=end, year=year, force_refresh=False)
    else:
        summary = public_climate_energy_summary(latitude=latitude, longitude=longitude, country=country, start=start, end=end, year=year, live=False, settings=settings)
    return climate_energy_report(summary)


@app.get("/reports/site-intelligence")
def reports_site_intelligence(
    start_date: str = Query("28daysAgo"),
    end_date: str = Query("today"),
    format: str = Query("json"),
    ga4: GA4Client = Depends(get_ga4_client),
    registry: ContentRegistry = Depends(get_registry),
    _: None = Depends(require_token),
):
    try:
        return _format_report_response(_site_report_data(ga4, registry, start_date, end_date), format, "site-intelligence-report")
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail={"message": "Site Intelligence report generation failed.", "error_type": exc.__class__.__name__, "error_message": str(exc)}) from exc


@app.get("/reports/search-intelligence")
def reports_search_intelligence(
    start_date: str = Query("28daysAgo"),
    end_date: str = Query("yesterday"),
    format: str = Query("json"),
    settings: Settings = Depends(get_settings),
    registry: ContentRegistry = Depends(get_registry),
    _: None = Depends(require_token),
):
    try:
        return _format_report_response(_search_report_data(settings, registry, start_date, end_date), format, "search-intelligence-report")
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail={"message": "Search Intelligence report generation failed.", "error_type": exc.__class__.__name__, "error_message": str(exc)}) from exc


@app.get("/reports/content-strategy")
def reports_content_strategy(
    start_date: str = Query("28daysAgo"),
    end_date: str = Query("today"),
    prior_start_date: str = Query("56daysAgo"),
    prior_end_date: str = Query("29daysAgo"),
    limit: int = Query(25, ge=1, le=100),
    format: str = Query("json"),
    ga4: GA4Client = Depends(get_ga4_client),
    settings: Settings = Depends(get_settings),
    registry: ContentRegistry = Depends(get_registry),
    _: None = Depends(require_token),
):
    try:
        report = _content_report_data(ga4, settings, registry, start_date, end_date, prior_start_date, prior_end_date, limit)
        return _format_report_response(report, format, "content-strategy-report")
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail={"message": "Content Strategy report generation failed.", "error_type": exc.__class__.__name__, "error_message": str(exc)}) from exc


@app.get("/reports/external-sources")
def reports_external_sources(
    format: str = Query("json"),
    settings: Settings = Depends(get_settings),
    _: None = Depends(require_token),
):
    try:
        return _format_report_response(_external_sources_report_data(settings), format, "external-sources-report")
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail={"message": "External Sources report generation failed.", "error_type": exc.__class__.__name__, "error_message": str(exc)}) from exc


@app.get("/reports/climate-energy")
def reports_climate_energy(
    latitude: Optional[float] = Query(default=None),
    longitude: Optional[float] = Query(default=None),
    country: Optional[str] = Query(default=None),
    start: str = Query("20260101"),
    end: str = Query("20260105"),
    year: int = Query(2024, ge=2021, le=2100),
    live: bool = Query(False),
    format: str = Query("json"),
    settings: Settings = Depends(get_settings),
    _: None = Depends(require_token),
):
    try:
        return _format_report_response(_climate_energy_report_data(settings, latitude, longitude, country, start, end, year, live), format, "climate-energy-report")
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail={"message": "Climate + Energy report generation failed.", "error_type": exc.__class__.__name__, "error_message": str(exc)}) from exc


@app.get("/reports/indexing")
def reports_indexing(
    start_date: str = Query("28daysAgo"),
    end_date: str = Query("yesterday"),
    format: str = Query("json"),
    settings: Settings = Depends(get_settings),
    registry: ContentRegistry = Depends(get_registry),
    ga4: GA4Client = Depends(get_ga4_client),
    _: None = Depends(require_token),
):
    try:
        return _format_report_response(_indexing_report_data(settings, registry, ga4, start_date, end_date), format, "indexing-coverage-report")
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail={"message": "Indexing report generation failed.", "error_type": exc.__class__.__name__, "error_message": str(exc)}) from exc


def _report_export_catalog() -> list[dict[str, Any]]:
    return [
        {"id": "site-intelligence", "title": "Weekly Site Intelligence Report", "endpoint": "/reports/site-intelligence", "formats": ["json", "markdown", "csv"], "cost": "medium"},
        {"id": "search-intelligence", "title": "Search Intelligence Report", "endpoint": "/reports/search-intelligence", "formats": ["json", "markdown", "csv"], "cost": "medium"},
        {"id": "content-strategy", "title": "Content Strategy and Publishing Report", "endpoint": "/reports/content-strategy", "formats": ["json", "markdown", "csv"], "cost": "high"},
        {"id": "external-sources", "title": "External Data Sources Report", "endpoint": "/reports/external-sources", "formats": ["json", "markdown", "csv"], "cost": "low"},
        {"id": "climate-energy", "title": "Climate + Energy Snapshot Report", "endpoint": "/reports/climate-energy", "formats": ["json", "markdown", "csv"], "cost": "low"},
        {"id": "indexing", "title": "Registry and Indexing Coverage Report", "endpoint": "/reports/indexing", "formats": ["json", "markdown", "csv"], "cost": "high"},
    ]


@app.get("/reports/export")
def reports_export_bundle(
    report: str = Query("all"),
    start_date: str = Query("28daysAgo"),
    end_date: str = Query("today"),
    format: str = Query("json"),
    full: bool = Query(False),
    ga4: GA4Client = Depends(get_ga4_client),
    settings: Settings = Depends(get_settings),
    registry: ContentRegistry = Depends(get_registry),
    _: None = Depends(require_token),
):
    try:
        requested = {item.strip() for item in report.split(",") if item.strip()} if report != "all" else {"site", "search", "content", "external", "climate", "indexing"}
        if not full:
            manifest = bundle_manifest_report(_report_export_catalog(), sorted(requested))
            manifest["full_bundle_endpoint"] = "/reports/export?full=true"
            manifest["timeout_note"] = "The default export endpoint returns this lightweight manifest so WordPress pages do not wait on every upstream report. Use full=true for direct internal exports."
            return _format_report_response(manifest, format, "site-intelligence-export-bundle")

        reports = []
        if "site" in requested or "site-intelligence" in requested:
            reports.append(_site_report_data(ga4, registry, start_date, end_date))
        if "search" in requested or "search-intelligence" in requested:
            reports.append(_search_report_data(settings, registry, start_date, "yesterday" if end_date == "today" else end_date))
        if "content" in requested or "content-strategy" in requested:
            reports.append(_content_report_data(ga4, settings, registry, start_date, end_date, "56daysAgo", "29daysAgo", 20))
        if "external" in requested or "external-sources" in requested:
            reports.append(_external_sources_report_data(settings))
        if "climate" in requested or "climate-energy" in requested:
            reports.append(_climate_energy_report_data(settings, None, None, None, "20260101", "20260105", 2024, False))
        if "indexing" in requested:
            reports.append(_indexing_report_data(settings, registry, ga4, start_date, "yesterday" if end_date == "today" else end_date))
        return _format_report_response(bundle_report(reports), format, "site-intelligence-export-bundle")
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail={"message": "Report export bundle generation failed.", "error_type": exc.__class__.__name__, "error_message": str(exc)}) from exc


@app.get("/intelligence/reports")
def intelligence_reports_summary(_: None = Depends(require_token)):
    return {
        "ok": True,
        "version": settings.version,
        "reports": _report_export_catalog() + [{"id": "export-bundle", "title": "Site Intelligence Export Bundle", "endpoint": "/reports/export", "formats": ["json", "markdown", "csv"], "cost": "manifest"}],
        "notes": [
            "Markdown exports are suitable for planning notes, GitHub documentation, or editorial drafts.",
            "CSV exports flatten highlights, recommendations, section metrics, and section rows for spreadsheet review.",
            "Use public dashboard endpoints for public pages; report endpoints are intended for internal planning unless manually reviewed.",
        ],
    }



def _public_dashboard_brief_report(settings: Settings, registry: ContentRegistry) -> dict:
    """Build a fast public-safe source report for the AI Public Dashboard Brief.

    This intentionally avoids the live GA4-backed public dashboard builder. The
    public-dashboard brief is meant to summarize public presentation readiness,
    not to pull raw analytics or call external origins during a WordPress page
    render. Keeping this report synthetic prevents Bluehost/Cloudflare 5xx pages
    from leaking into the shortcode output when an upstream origin is slow.
    """
    landing = public_landing_page()
    methodology = public_methodology()
    registry_entries = getattr(registry, "entries", []) or []
    checklist = [
        {"check": "Public landing-page shortcode is available", "status": "passed", "detail": "The public landing page uses curated public-safe copy."},
        {"check": "Public methodology notes are available", "status": "passed", "detail": "The methodology section explains included and excluded data."},
        {"check": "Raw analytics remain private", "status": "passed", "detail": "This brief does not call GA4 or expose raw report details."},
        {"check": "Registry-backed knowledge architecture is present", "status": "passed" if len(registry_entries) else "review", "detail": f"Registry entries available: {len(registry_entries)}."},
    ]
    readiness = {"status": "public_preview", "score": 90 if len(registry_entries) else 75, "checklist": checklist}
    landing_cards = landing.get("cards", []) or []
    public_modules = [card.get("title") for card in landing_cards if isinstance(card, dict) and card.get("title")]
    recommendations = [
        "Keep public dashboards aggregated, source-labeled, and manually reviewed before publication.",
        "Use the public methodology section beside public dashboard modules.",
        "Keep raw analytics, conversion diagnostics, token-protected reports, and operational queues private.",
        "Use fast public-safe snapshots on public pages; reserve live connector calls for private testing.",
    ]
    return {
        "ok": True,
        "report_id": "public-dashboard",
        "title": "Public Dashboard Readiness Report",
        "summary": "A public-safe report summarizing the Sustainable Catalyst public dashboard presentation layer, methodology notes, and release-readiness signals.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": {"dashboard": "public-safe-snapshot", "mode": "public-safe", "live_analytics": False},
        "date_range": {},
        "highlights": [
            landing.get("lede", "Public Site Intelligence presents sanitized, source-labeled dashboard summaries."),
            f"Public dashboard modules available: {len(landing_cards)}.",
            f"Readiness status: {readiness.get('status', 'review')}; checklist items: {len(checklist)}.",
        ],
        "recommendations": recommendations,
        "sections": [
            {
                "section_id": "public_cards",
                "title": "Public dashboard cards",
                "summary": "Public-safe dashboard modules available for landing pages.",
                "metrics": {"module_count": len(landing_cards)},
                "rows": landing_cards,
            },
            {
                "section_id": "public_modules",
                "title": "Public module inventory",
                "summary": "Named public-facing Site Intelligence modules suitable for reviewed pages.",
                "metrics": {},
                "rows": public_modules,
            },
            {
                "section_id": "methodology",
                "title": "Methodology notes",
                "summary": methodology.get("summary", "Public methodology and source-boundary notes."),
                "metrics": {},
                "rows": (methodology.get("included", []) or []) + (methodology.get("excluded", []) or []) + (methodology.get("review_notes", []) or []),
            },
            {
                "section_id": "readiness",
                "title": "Public readiness checklist",
                "summary": "Checklist items for public dashboard review.",
                "metrics": {"score": readiness.get("score", 0), "status": readiness.get("status", "review")},
                "rows": checklist,
            },
        ],
        "export_formats": ["json"],
        "methodology": {
            "summary": "Public dashboard briefs use public-safe landing, methodology, and readiness data only.",
            "privacy_note": "This brief intentionally avoids raw GA4 rows, private conversion queues, external live calls, and backend configuration values.",
        },
    }


@app.get("/ai/status")
def ai_brief_status(settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    return ai_status(settings)


def _format_ai_brief_response(brief: dict, format: str, filename: str):
    normalized = (format or "json").lower()
    if normalized == "markdown":
        lines = [f"# {brief.get('title', 'Site Intelligence Brief')}", "", brief.get("executive_summary", "")]
        for title, key in [
            ("Key findings", "key_findings"),
            ("Recommended actions", "recommended_actions"),
            ("Content and platform opportunities", "content_opportunities"),
            ("Risk and uncertainty notes", "risk_notes"),
            ("Public-safe summary", "public_safe_summary"),
        ]:
            value = brief.get(key)
            if not value:
                continue
            lines.extend(["", f"## {title}"])
            if isinstance(value, list):
                lines.extend([f"- {item}" for item in value])
            else:
                lines.extend(["", str(value)])
        return PlainTextResponse("\n".join(lines).strip() + "\n", media_type="text/markdown", headers={"Content-Disposition": f"inline; filename={filename}.md"})
    return brief


@app.get("/ai/briefs/site-intelligence")
def ai_site_intelligence_brief(
    start_date: str = Query("28daysAgo"),
    end_date: str = Query("today"),
    mode: str = Query("private"),
    use_ai: bool = Query(True),
    format: str = Query("json"),
    ga4: GA4Client = Depends(get_ga4_client),
    settings: Settings = Depends(get_settings),
    registry: ContentRegistry = Depends(get_registry),
    _: None = Depends(require_token),
):
    try:
        report = _site_report_data(ga4, registry, start_date, end_date)
        return _format_ai_brief_response(build_ai_brief(report, "site-intelligence", settings, mode=mode, use_ai=use_ai), format, "ai-site-intelligence-brief")
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail={"message": "AI Site Intelligence brief generation failed.", "error_type": exc.__class__.__name__, "error_message": str(exc)}) from exc


@app.get("/ai/briefs/search")
def ai_search_brief(
    start_date: str = Query("28daysAgo"),
    end_date: str = Query("yesterday"),
    mode: str = Query("private"),
    use_ai: bool = Query(True),
    format: str = Query("json"),
    settings: Settings = Depends(get_settings),
    registry: ContentRegistry = Depends(get_registry),
    _: None = Depends(require_token),
):
    try:
        report = _search_report_data(settings, registry, start_date, end_date)
        return _format_ai_brief_response(build_ai_brief(report, "search", settings, mode=mode, use_ai=use_ai), format, "ai-search-brief")
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail={"message": "AI Search brief generation failed.", "error_type": exc.__class__.__name__, "error_message": str(exc)}) from exc


@app.get("/ai/briefs/publishing")
def ai_publishing_brief(
    start_date: str = Query("28daysAgo"),
    end_date: str = Query("today"),
    prior_start_date: str = Query("56daysAgo"),
    prior_end_date: str = Query("29daysAgo"),
    limit: int = Query(25, ge=1, le=100),
    mode: str = Query("private"),
    use_ai: bool = Query(True),
    format: str = Query("json"),
    ga4: GA4Client = Depends(get_ga4_client),
    settings: Settings = Depends(get_settings),
    registry: ContentRegistry = Depends(get_registry),
    _: None = Depends(require_token),
):
    try:
        report = _content_report_data(ga4, settings, registry, start_date, end_date, prior_start_date, prior_end_date, limit)
        return _format_ai_brief_response(build_ai_brief(report, "publishing", settings, mode=mode, use_ai=use_ai), format, "ai-publishing-brief")
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail={"message": "AI Publishing brief generation failed.", "error_type": exc.__class__.__name__, "error_message": str(exc)}) from exc


@app.get("/ai/briefs/external-sources")
def ai_external_sources_brief(
    mode: str = Query("private"),
    use_ai: bool = Query(True),
    format: str = Query("json"),
    settings: Settings = Depends(get_settings),
    _: None = Depends(require_token),
):
    try:
        report = _external_sources_report_data(settings)
        return _format_ai_brief_response(build_ai_brief(report, "external-sources", settings, mode=mode, use_ai=use_ai), format, "ai-external-sources-brief")
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail={"message": "AI External Sources brief generation failed.", "error_type": exc.__class__.__name__, "error_message": str(exc)}) from exc


@app.get("/ai/briefs/public-dashboard")
def ai_public_dashboard_brief(
    mode: str = Query("public"),
    use_ai: bool = Query(False),
    format: str = Query("json"),
    settings: Settings = Depends(get_settings),
    registry: ContentRegistry = Depends(get_registry),
    _: None = Depends(require_token),
):
    try:
        report = _public_dashboard_brief_report(settings, registry)
        return _format_ai_brief_response(build_ai_brief(report, "public-dashboard", settings, mode=mode, use_ai=use_ai), format, "ai-public-dashboard-brief")
    except Exception as exc:  # noqa: BLE001
        fallback_report = {
            "ok": True,
            "report_id": "public-dashboard",
            "title": "Public Dashboard Readiness Report",
            "summary": "A public-safe fallback report summarizing Site Intelligence public dashboard readiness without calling live analytics or external connectors.",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source": {"dashboard": "local-public-safe-fallback", "mode": "public-safe", "live_analytics": False},
            "date_range": {},
            "highlights": [
                "Public Site Intelligence should present sanitized, source-labeled dashboard summaries.",
                "Public dashboard language should be manually reviewed before publication.",
                "Raw analytics, conversion diagnostics, and operational queues should remain private.",
            ],
            "recommendations": [
                "Use the public landing, public knowledge overview, climate/energy summary, and methodology shortcodes for public pages.",
                "Keep the Public Dashboard Brief deterministic unless testing the backend route directly.",
                "Reserve live connector and AI-provider calls for private review pages.",
            ],
            "sections": [],
            "methodology": {
                "summary": "Fallback brief generated locally because public-dashboard brief assembly failed.",
                "privacy_note": "No raw analytics, private report details, or external API results are exposed.",
                "error_type": exc.__class__.__name__,
            },
        }
        return _format_ai_brief_response(build_ai_brief(fallback_report, "public-dashboard", settings, mode=mode, use_ai=False), format, "ai-public-dashboard-brief")


@app.get("/intelligence/ai-briefs")
def intelligence_ai_briefs(settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    return {
        "ok": True,
        "version": settings.version,
        "ai_status": ai_status(settings),
        "briefs": [
            {"id": "site-intelligence", "title": "AI-Assisted Weekly Site Intelligence Brief", "endpoint": "/ai/briefs/site-intelligence", "shortcode": "[sc_ai_site_intelligence_brief]"},
            {"id": "search", "title": "AI-Assisted Search Intelligence Brief", "endpoint": "/ai/briefs/search", "shortcode": "[sc_ai_search_brief]"},
            {"id": "publishing", "title": "AI-Assisted Publishing Strategy Brief", "endpoint": "/ai/briefs/publishing", "shortcode": "[sc_ai_publishing_brief]"},
            {"id": "external-sources", "title": "AI-Assisted External Data Sources Brief", "endpoint": "/ai/briefs/external-sources", "shortcode": "[sc_ai_external_sources_brief]"},
            {"id": "public-dashboard", "title": "AI-Assisted Public Dashboard Brief", "endpoint": "/ai/briefs/public-dashboard", "shortcode": "[sc_ai_public_dashboard_brief]"},
        ],
        "notes": [
            "AI briefs fall back to deterministic interpretation when SC_SI_AI_PROVIDER is disabled or not configured.",
            "Use mode=public only for public-safe summaries and review all public copy before publication.",
            "Gemini can be enabled with SC_SI_AI_PROVIDER=gemini and SC_SI_GEMINI_API_KEY in Render.",
        ],
    }



@app.get("/admin/registry")
def admin_registry_endpoint(registry: ContentRegistry = Depends(get_registry), _: None = Depends(require_token)):
    return registry_manager(registry)


@app.get("/admin/registry/coverage")
def admin_registry_coverage_endpoint(registry: ContentRegistry = Depends(get_registry), _: None = Depends(require_token)):
    return registry_coverage(registry)


@app.get("/admin/sources")
def admin_sources_endpoint(settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    return source_manager(settings)


@app.get("/admin/modules")
def admin_modules_endpoint(settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    return module_manager(settings)


@app.get("/admin/shortcodes")
def admin_shortcodes_endpoint(_: None = Depends(require_token)):
    return shortcode_catalog()


@app.get("/admin/diagnostics")
def admin_diagnostics_endpoint(settings: Settings = Depends(get_settings), registry: ContentRegistry = Depends(get_registry), _: None = Depends(require_token)):
    return admin_diagnostics(settings, registry)


@app.get("/admin/visibility")
def admin_visibility_endpoint(settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    return visibility_matrix(settings)


@app.get("/admin/source-control")
def admin_source_control_endpoint(settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    return source_control_tools(settings)


@app.get("/admin/status")
def admin_status_endpoint(settings: Settings = Depends(get_settings), registry: ContentRegistry = Depends(get_registry), _: None = Depends(require_token)):
    return admin_status(settings, registry)


@app.get("/admin/connection-check")
def admin_connection_check_endpoint(settings: Settings = Depends(get_settings), registry: ContentRegistry = Depends(get_registry), _: None = Depends(require_token)):
    return connection_check(settings, registry)


@app.get("/admin/public-readiness-check")
def admin_public_readiness_check_endpoint(settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    return public_readiness_check(settings)


@app.get("/admin/diagnostic-summary")
def admin_diagnostic_summary_endpoint(settings: Settings = Depends(get_settings), registry: ContentRegistry = Depends(get_registry), _: None = Depends(require_token)):
    return diagnostic_summary(settings, registry)


@app.get("/intelligence/admin")
def intelligence_admin_endpoint(settings: Settings = Depends(get_settings), registry: ContentRegistry = Depends(get_registry), _: None = Depends(require_token)):
    return admin_overview(settings, registry)


@app.post("/collect/event", response_model=EventAck)
def collect_event(event: CollectedEvent, _: None = Depends(require_token)):
    # v0.1.0 acknowledges events without storing them. The next version can add
    # SQLite/Postgres persistence or Measurement Protocol forwarding.
    return EventAck(
        ok=True,
        stored=False,
        event_name=event.event_name,
        message="Event accepted. Persistence is disabled in v0.3.2; use GA4/dataLayer as the primary event store.",
    )

@app.get("/publishing/content-strategy")
def publishing_content_strategy(
    start_date: str = Query("28daysAgo"),
    end_date: str = Query("yesterday"),
    prior_start_date: str = Query("56daysAgo"),
    prior_end_date: str = Query("29daysAgo"),
    limit: int = Query(25, ge=1, le=100),
    ga4: GA4Client = Depends(get_ga4_client),
    settings: Settings = Depends(get_settings),
    registry: ContentRegistry = Depends(get_registry),
    _: None = Depends(require_token),
):
    try:
        return publishing_intelligence(
            ga4,
            SearchConsoleClient(settings),
            registry,
            start_date=start_date,
            end_date=end_date,
            prior_start_date=prior_start_date,
            prior_end_date=prior_end_date,
            limit=limit,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=502,
            detail={
                "message": "Content Strategy Intelligence request failed.",
                "error_type": exc.__class__.__name__,
                "error_message": str(exc),
                "hint": "Check GA4, Search Console, and registry access before running publishing strategy reports.",
            },
        ) from exc


@app.get("/publishing/topic-momentum")
def publishing_topic_momentum(
    start_date: str = Query("28daysAgo"),
    end_date: str = Query("yesterday"),
    prior_start_date: str = Query("56daysAgo"),
    prior_end_date: str = Query("29daysAgo"),
    limit: int = Query(25, ge=1, le=100),
    ga4: GA4Client = Depends(get_ga4_client),
    settings: Settings = Depends(get_settings),
    registry: ContentRegistry = Depends(get_registry),
    _: None = Depends(require_token),
):
    report = publishing_intelligence(
        ga4,
        SearchConsoleClient(settings),
        registry,
        start_date=start_date,
        end_date=end_date,
        prior_start_date=prior_start_date,
        prior_end_date=prior_end_date,
        limit=limit,
    )
    return {
        "ok": True,
        "generated_at": report.get("generated_at"),
        "source": report.get("source", {}),
        "date_range": report.get("date_range", {}),
        "comparison_range": report.get("comparison_range", {}),
        "topics": report.get("topic_momentum", []),
        "article_map_performance": report.get("article_map_performance", []),
        "recommendations": [
            "Use topic momentum to choose article updates, newsletter angles, LinkedIn posts, and Workbench prompts.",
            "Prioritize topics that combine search visibility, GA4 engagement, and clear Sustainable Catalyst article-map structure.",
        ],
    }


@app.get("/publishing/update-priorities")
def publishing_update_priorities(
    start_date: str = Query("28daysAgo"),
    end_date: str = Query("yesterday"),
    prior_start_date: str = Query("56daysAgo"),
    prior_end_date: str = Query("29daysAgo"),
    limit: int = Query(25, ge=1, le=100),
    ga4: GA4Client = Depends(get_ga4_client),
    settings: Settings = Depends(get_settings),
    registry: ContentRegistry = Depends(get_registry),
    _: None = Depends(require_token),
):
    report = publishing_intelligence(
        ga4,
        SearchConsoleClient(settings),
        registry,
        start_date=start_date,
        end_date=end_date,
        prior_start_date=prior_start_date,
        prior_end_date=prior_end_date,
        limit=limit,
    )
    return {
        "ok": True,
        "generated_at": report.get("generated_at"),
        "source": report.get("source", {}),
        "date_range": report.get("date_range", {}),
        "comparison_range": report.get("comparison_range", {}),
        "content_decay": report.get("content_decay", []),
        "rising_pages": report.get("rising_pages", []),
        "publishing_queue": report.get("publishing_queue", []),
        "newsletter_candidates": report.get("newsletter_candidates", []),
        "recommendations": report.get("recommendations", []),
    }


@app.get("/publishing/promotion-opportunities")
def publishing_promotion_opportunities(
    start_date: str = Query("28daysAgo"),
    end_date: str = Query("yesterday"),
    prior_start_date: str = Query("56daysAgo"),
    prior_end_date: str = Query("29daysAgo"),
    limit: int = Query(25, ge=1, le=100),
    ga4: GA4Client = Depends(get_ga4_client),
    settings: Settings = Depends(get_settings),
    registry: ContentRegistry = Depends(get_registry),
    _: None = Depends(require_token),
):
    report = publishing_intelligence(
        ga4,
        SearchConsoleClient(settings),
        registry,
        start_date=start_date,
        end_date=end_date,
        prior_start_date=prior_start_date,
        prior_end_date=prior_end_date,
        limit=limit,
    )
    return {
        "ok": True,
        "generated_at": report.get("generated_at"),
        "source": report.get("source", {}),
        "date_range": report.get("date_range", {}),
        "promotion_opportunities": report.get("promotion_opportunities", []),
        "newsletter_candidates": report.get("newsletter_candidates", []),
        "recommendations": [
            "Use promotion opportunities to decide which pages should become LinkedIn updates, Substack topics, GitHub CTA improvements, or Workbench prompts.",
            "Keep raw conversion gaps internal until public dashboard mode is available.",
        ],
    }


@app.get("/intelligence/publishing")
def publishing_intelligence_report(
    start_date: str = Query("28daysAgo"),
    end_date: str = Query("yesterday"),
    prior_start_date: str = Query("56daysAgo"),
    prior_end_date: str = Query("29daysAgo"),
    limit: int = Query(25, ge=1, le=100),
    ga4: GA4Client = Depends(get_ga4_client),
    settings: Settings = Depends(get_settings),
    registry: ContentRegistry = Depends(get_registry),
    _: None = Depends(require_token),
):
    return publishing_content_strategy(start_date, end_date, prior_start_date, prior_end_date, limit, ga4, settings, registry, _)





# Site Intelligence v2.1.0 — Global Conditions and Live Map Observatory
@app.get("/public/global-conditions")
def public_global_conditions_endpoint(settings: Settings = Depends(get_settings)):
    from .global_conditions_observatory import build_global_conditions_overview
    return build_global_conditions_overview(settings)


@app.get("/public/global-conditions/layers")
def public_global_conditions_layers_endpoint(
    limit: int = Query(default=100, ge=1, le=200),
    settings: Settings = Depends(get_settings),
):
    from .global_conditions_observatory import build_global_conditions_layers
    return build_global_conditions_layers(settings, limit=limit)


@app.get("/public/global-conditions/features")
def public_global_conditions_features_endpoint(
    bbox: str = Query(default="", max_length=120),
    domain: str = Query(default="", max_length=80),
    source_id: str = Query(default="", max_length=160),
    connector_id: str = Query(default="", max_length=160),
    observed_after: str = Query(default="", max_length=40),
    limit: int = Query(default=300, ge=1, le=500),
    settings: Settings = Depends(get_settings),
):
    from .global_conditions_observatory import build_global_conditions_features
    try:
        return build_global_conditions_features(
            settings,
            bbox=bbox,
            domain=domain,
            source_id=source_id,
            connector_id=connector_id,
            observed_after=observed_after,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/public/global-conditions/signals")
def public_global_conditions_signals_endpoint(
    limit: int = Query(default=50, ge=1, le=100),
    settings: Settings = Depends(get_settings),
):
    from .global_conditions_observatory import build_global_conditions_signals
    return build_global_conditions_signals(settings, limit=limit)


@app.get("/public/global-conditions/diagnostics")
def public_global_conditions_diagnostics_endpoint(settings: Settings = Depends(get_settings)):
    from .global_conditions_observatory import build_global_conditions_diagnostics
    return build_global_conditions_diagnostics(settings)




# Site Intelligence v2.2.0 — Economics, Markets, and Sustainability Signals
@app.get("/public/economics-sustainability")
def public_economics_sustainability_overview(settings: Settings = Depends(get_settings)):
    from .economics_markets_sustainability import build_economics_overview
    return build_economics_overview(settings)


@app.get("/public/economics-sustainability/records")
def public_economics_sustainability_records(
    family: str = Query(default="", max_length=80),
    record_type: str = Query(default="", max_length=80),
    subject: str = Query(default="", max_length=160),
    source_id: str = Query(default="", max_length=160),
    indicator_code: str = Query(default="", max_length=180),
    geography_code: str = Query(default="", max_length=20),
    frequency: str = Query(default="", max_length=40),
    query: str = Query(default="", max_length=240),
    start: str = Query(default="", max_length=50),
    end: str = Query(default="", max_length=50),
    limit: int = Query(default=100, ge=1, le=300),
    offset: int = Query(default=0, ge=0),
    settings: Settings = Depends(get_settings),
):
    from .economics_markets_sustainability import build_economic_records
    return build_economic_records(
        settings, family=family, record_type=record_type, subject=subject,
        source_id=source_id, indicator_code=indicator_code,
        geography_code=geography_code, frequency=frequency, query=query,
        start=start, end=end, limit=limit, offset=offset,
    )


@app.get("/public/economics-sustainability/facets")
def public_economics_sustainability_facets(
    geography_code: str = Query(default="", max_length=20),
    settings: Settings = Depends(get_settings),
):
    from .economics_markets_sustainability import build_economic_facets
    return build_economic_facets(settings, geography_code=geography_code)


@app.get("/public/economics-sustainability/series")
def public_economics_sustainability_series(
    indicator_code: str = Query(..., min_length=1, max_length=180),
    geography_code: str = Query(default="", max_length=20),
    source_id: str = Query(default="", max_length=160),
    limit: int = Query(default=120, ge=1, le=240),
    settings: Settings = Depends(get_settings),
):
    from .economics_markets_sustainability import build_economic_series
    try:
        return build_economic_series(
            settings, indicator_code=indicator_code, geography_code=geography_code,
            source_id=source_id, limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/public/economics-sustainability/compare")
def public_economics_sustainability_compare(
    indicator_code: str = Query(..., min_length=1, max_length=180),
    geography_a: str = Query(..., min_length=2, max_length=20),
    geography_b: str = Query(..., min_length=2, max_length=20),
    limit: int = Query(default=120, ge=1, le=240),
    settings: Settings = Depends(get_settings),
):
    from .economics_markets_sustainability import build_economic_comparison
    try:
        return build_economic_comparison(
            settings, indicator_code=indicator_code, geography_a=geography_a,
            geography_b=geography_b, limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/public/economics-sustainability/brief")
def public_economics_sustainability_brief(
    geography_code: str = Query(default="", max_length=20),
    family: str = Query(default="", max_length=80),
    limit: int = Query(default=80, ge=1, le=150),
    settings: Settings = Depends(get_settings),
):
    from .economics_markets_sustainability import build_economics_brief
    return build_economics_brief(settings, geography_code=geography_code, family=family, limit=limit)


@app.get("/public/economics-sustainability/diagnostics")
def public_economics_sustainability_diagnostics(settings: Settings = Depends(get_settings)):
    from .economics_markets_sustainability import build_economics_diagnostics
    return build_economics_diagnostics(settings)


# Site Intelligence v2.3.0 — International Law and Global Governance Observatory
@app.get("/public/international-law-observatory")
def public_international_law_observatory_overview(settings: Settings = Depends(get_settings)):
    from .international_law_observatory import build_law_overview
    return build_law_overview(settings)


@app.get("/public/international-law-observatory/records")
def public_international_law_observatory_records(
    record_type: str = Query(default="", max_length=100),
    authority_level: str = Query(default="", max_length=100),
    legal_body: str = Query(default="", max_length=260),
    country: str = Query(default="", max_length=120),
    subject: str = Query(default="", max_length=180),
    official_symbol: str = Query(default="", max_length=180),
    query: str = Query(default="", max_length=240),
    start: str = Query(default="", max_length=50),
    end: str = Query(default="", max_length=50),
    limit: int = Query(default=100, ge=1, le=300),
    offset: int = Query(default=0, ge=0),
    settings: Settings = Depends(get_settings),
):
    from .international_law_observatory import build_law_records
    return build_law_records(
        settings, record_type=record_type, authority_level=authority_level,
        legal_body=legal_body, country=country, subject=subject,
        official_symbol=official_symbol, query=query, start=start, end=end,
        limit=limit, offset=offset,
    )


@app.get("/public/international-law-observatory/facets")
def public_international_law_observatory_facets(settings: Settings = Depends(get_settings)):
    from .international_law_observatory import build_law_facets
    return build_law_facets(settings)


@app.get("/public/international-law-observatory/timeline")
def public_international_law_observatory_timeline(
    country: str = Query(default="", max_length=120),
    authority_level: str = Query(default="", max_length=100),
    record_type: str = Query(default="", max_length=100),
    limit: int = Query(default=160, ge=1, le=240),
    settings: Settings = Depends(get_settings),
):
    from .international_law_observatory import build_law_timeline
    return build_law_timeline(settings, country=country, authority_level=authority_level, record_type=record_type, limit=limit)


@app.get("/public/international-law-observatory/country-profile")
def public_international_law_observatory_country_profile(
    country: str = Query(..., min_length=2, max_length=120),
    limit: int = Query(default=160, ge=1, le=300),
    settings: Settings = Depends(get_settings),
):
    from .international_law_observatory import build_country_legal_profile
    try:
        return build_country_legal_profile(settings, country=country, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/public/international-law-observatory/authority-matrix")
def public_international_law_observatory_authority_matrix(
    country: str = Query(default="", max_length=120),
    limit: int = Query(default=300, ge=1, le=300),
    settings: Settings = Depends(get_settings),
):
    from .international_law_observatory import build_authority_matrix
    return build_authority_matrix(settings, country=country, limit=limit)


@app.get("/public/international-law-observatory/brief")
def public_international_law_observatory_brief(
    country: str = Query(default="", max_length=120),
    authority_level: str = Query(default="", max_length=100),
    record_type: str = Query(default="", max_length=100),
    limit: int = Query(default=100, ge=1, le=150),
    settings: Settings = Depends(get_settings),
):
    from .international_law_observatory import build_law_brief
    return build_law_brief(settings, country=country, authority_level=authority_level, record_type=record_type, limit=limit)


@app.get("/public/international-law-observatory/diagnostics")
def public_international_law_observatory_diagnostics(settings: Settings = Depends(get_settings)):
    from .international_law_observatory import build_law_diagnostics
    return build_law_diagnostics(settings)


# Site Intelligence v2.4.0 — Scientific and Earth Systems Observatory
@app.get("/public/scientific-earth-systems")
def public_scientific_earth_systems_overview(settings: Settings = Depends(get_settings)):
    from .scientific_earth_systems_observatory import build_science_overview
    return build_science_overview(settings)


@app.get("/public/scientific-earth-systems/records")
def public_scientific_earth_systems_records(
    record_type: str = Query(default="", max_length=100),
    discipline: str = Query(default="", max_length=160),
    source_id: str = Query(default="", max_length=160),
    collection: str = Query(default="", max_length=300),
    mission: str = Query(default="", max_length=240),
    instrument: str = Query(default="", max_length=240),
    target: str = Query(default="", max_length=300),
    dataset_id: str = Query(default="", max_length=240),
    query: str = Query(default="", max_length=240),
    start: str = Query(default="", max_length=50),
    end: str = Query(default="", max_length=50),
    limit: int = Query(default=100, ge=1, le=300),
    offset: int = Query(default=0, ge=0),
    settings: Settings = Depends(get_settings),
):
    from .scientific_earth_systems_observatory import build_science_records
    return build_science_records(settings, record_type=record_type, discipline=discipline, source_id=source_id, collection=collection, mission=mission, instrument=instrument, target=target, dataset_id=dataset_id, query=query, start=start, end=end, limit=limit, offset=offset)


@app.get("/public/scientific-earth-systems/facets")
def public_scientific_earth_systems_facets(settings: Settings = Depends(get_settings)):
    from .scientific_earth_systems_observatory import build_science_facets
    return build_science_facets(settings)


@app.get("/public/scientific-earth-systems/assets")
def public_scientific_earth_systems_assets(
    source_id: str = Query(default="", max_length=160),
    scientific_record_id: str = Query(default="", max_length=180),
    dataset_id: str = Query(default="", max_length=240),
    format: str = Query(default="", max_length=80),
    asset_role: str = Query(default="", max_length=100),
    limit: int = Query(default=100, ge=1, le=250),
    offset: int = Query(default=0, ge=0),
    settings: Settings = Depends(get_settings),
):
    from .scientific_earth_systems_observatory import build_science_assets
    return build_science_assets(settings, source_id=source_id, scientific_record_id=scientific_record_id, dataset_id=dataset_id, format=format, asset_role=asset_role, limit=limit, offset=offset)


@app.get("/public/scientific-earth-systems/map-layers")
def public_scientific_earth_systems_layers(
    source_id: str = Query(default="", max_length=160),
    layer_type: str = Query(default="", max_length=80),
    limit: int = Query(default=100, ge=1, le=160),
    offset: int = Query(default=0, ge=0),
    settings: Settings = Depends(get_settings),
):
    from .scientific_earth_systems_observatory import build_science_layers
    return build_science_layers(settings, source_id=source_id, layer_type=layer_type, limit=limit, offset=offset)


@app.get("/public/scientific-earth-systems/stac")
def public_scientific_earth_systems_stac(
    collections: str = Query(default="", max_length=500),
    bbox: str = Query(default="", max_length=120),
    start: str = Query(default="", max_length=50),
    end: str = Query(default="", max_length=50),
    query: str = Query(default="", max_length=240),
    limit: int = Query(default=100, ge=1, le=300),
    offset: int = Query(default=0, ge=0),
    settings: Settings = Depends(get_settings),
):
    from .scientific_earth_systems_observatory import build_science_stac
    try:
        return build_science_stac(settings, collections=collections, bbox=bbox, start=start, end=end, query=query, limit=limit, offset=offset)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/public/scientific-earth-systems/timeseries")
def public_scientific_earth_systems_timeseries(
    source_id: str = Query(default="", max_length=160),
    metric: str = Query(default="", max_length=240),
    domain: str = Query(default="", max_length=160),
    dataset_id: str = Query(default="", max_length=240),
    geography_code: str = Query(default="", max_length=40),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    settings: Settings = Depends(get_settings),
):
    from .scientific_earth_systems_observatory import build_science_series
    return build_science_series(settings, source_id=source_id, metric=metric, domain=domain, dataset_id=dataset_id, geography_code=geography_code, limit=limit, offset=offset)


@app.get("/public/scientific-earth-systems/timeseries/{series_id}/points")
def public_scientific_earth_systems_timeseries_points(
    series_id: str,
    start: str = Query(default="", max_length=50),
    end: str = Query(default="", max_length=50),
    limit: int = Query(default=300, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    settings: Settings = Depends(get_settings),
):
    from .scientific_earth_systems_observatory import build_science_series_points
    try:
        return build_science_series_points(settings, series_id=series_id, start=start, end=end, limit=limit, offset=offset)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/public/scientific-earth-systems/brief")
def public_scientific_earth_systems_brief(
    family: str = Query(default="", max_length=100),
    discipline: str = Query(default="", max_length=160),
    source_id: str = Query(default="", max_length=160),
    query: str = Query(default="", max_length=240),
    limit: int = Query(default=80, ge=1, le=150),
    settings: Settings = Depends(get_settings),
):
    from .scientific_earth_systems_observatory import build_science_brief
    return build_science_brief(settings, family=family, discipline=discipline, source_id=source_id, query=query, limit=limit)


@app.get("/public/scientific-earth-systems/diagnostics")
def public_scientific_earth_systems_diagnostics(settings: Settings = Depends(get_settings)):
    from .scientific_earth_systems_observatory import build_science_diagnostics
    return build_science_diagnostics(settings)


# Site Intelligence v2.5.0 — Humanitarian, Conflict, and Displacement Observatory
@app.get("/public/humanitarian-conflict-displacement")
def public_humanitarian_conflict_displacement_overview(settings: Settings = Depends(get_settings)):
    from .humanitarian_conflict_displacement_observatory import build_overview
    return build_overview(settings)

@app.get("/public/humanitarian-conflict-displacement/records")
def public_humanitarian_conflict_displacement_records(
    country: str = Query(default="", max_length=120), category: str = Query(default="", max_length=100),
    source_id: str = Query(default="", max_length=160), query: str = Query(default="", max_length=240),
    days: int = Query(default=30, ge=1, le=90), include_hazards: bool = Query(default=True),
    limit: int = Query(default=150, ge=1, le=300), offset: int = Query(default=0, ge=0),
    settings: Settings = Depends(get_settings),
):
    from .humanitarian_conflict_displacement_observatory import build_records
    return build_records(settings,country=country,category=category,source_id=source_id,query=query,days=days,include_hazards=include_hazards,limit=limit,offset=offset)

@app.get("/public/humanitarian-conflict-displacement/facets")
def public_humanitarian_conflict_displacement_facets(settings: Settings = Depends(get_settings)):
    from .humanitarian_conflict_displacement_observatory import build_facets
    return build_facets(settings)

@app.get("/public/humanitarian-conflict-displacement/timeline")
def public_humanitarian_conflict_displacement_timeline(
    country: str = Query(default="", max_length=120), category: str = Query(default="", max_length=100),
    query: str = Query(default="", max_length=240), days: int = Query(default=30, ge=1, le=90),
    settings: Settings = Depends(get_settings),
):
    from .humanitarian_conflict_displacement_observatory import build_timeline
    return build_timeline(settings,country=country,category=category,query=query,days=days)

@app.get("/public/humanitarian-conflict-displacement/displacement")
def public_humanitarian_conflict_displacement_displacement(country: str = Query(default="", max_length=120), limit: int = Query(default=200, ge=1, le=300), settings: Settings = Depends(get_settings)):
    from .humanitarian_conflict_displacement_observatory import build_displacement
    return build_displacement(settings,country=country,limit=limit)

@app.get("/public/humanitarian-conflict-displacement/country-profile")
def public_humanitarian_conflict_displacement_country_profile(country: str = Query(..., max_length=120), limit: int = Query(default=250, ge=1, le=300), settings: Settings = Depends(get_settings)):
    from .humanitarian_conflict_displacement_observatory import build_country_profile
    try: return build_country_profile(settings,country=country,limit=limit)
    except ValueError as exc: raise HTTPException(status_code=422,detail=str(exc)) from exc

@app.get("/public/humanitarian-conflict-displacement/access")
def public_humanitarian_conflict_displacement_access(country: str = Query(default="", max_length=120), limit: int = Query(default=200, ge=1, le=300), settings: Settings = Depends(get_settings)):
    from .humanitarian_conflict_displacement_observatory import build_access_snapshot
    return build_access_snapshot(settings,country=country,limit=limit)

@app.get("/public/humanitarian-conflict-displacement/brief")
def public_humanitarian_conflict_displacement_brief(country: str = Query(default="", max_length=120), category: str = Query(default="", max_length=100), query: str = Query(default="", max_length=240), limit: int = Query(default=100, ge=1, le=150), settings: Settings = Depends(get_settings)):
    from .humanitarian_conflict_displacement_observatory import build_brief
    return build_brief(settings,country=country,category=category,query=query,limit=limit)

@app.get("/public/humanitarian-conflict-displacement/diagnostics")
def public_humanitarian_conflict_displacement_diagnostics(settings: Settings = Depends(get_settings)):
    from .humanitarian_conflict_displacement_observatory import build_diagnostics
    return build_diagnostics(settings)



# Site Intelligence v2.6.0 — Trade, Energy, and Resource Security Observatory
@app.get("/public/trade-energy-resources")
def public_trade_energy_resources_overview(settings: Settings = Depends(get_settings)):
    from .trade_energy_resource_security_observatory import build_overview
    return build_overview(settings)

@app.get("/public/trade-energy-resources/records")
def public_trade_energy_resources_records(family: str = Query(default="", max_length=100), source_id: str = Query(default="", max_length=160), geography_code: str = Query(default="", max_length=20), counterpart_code: str = Query(default="", max_length=20), indicator_code: str = Query(default="", max_length=180), frequency: str = Query(default="", max_length=40), query: str = Query(default="", max_length=240), start: str = Query(default="", max_length=50), end: str = Query(default="", max_length=50), limit: int = Query(default=150, ge=1, le=300), offset: int = Query(default=0, ge=0), settings: Settings = Depends(get_settings)):
    from .trade_energy_resource_security_observatory import build_records
    return build_records(settings,family=family,source_id=source_id,geography_code=geography_code,counterpart_code=counterpart_code,indicator_code=indicator_code,frequency=frequency,query=query,start=start,end=end,limit=limit,offset=offset)

@app.get("/public/trade-energy-resources/facets")
def public_trade_energy_resources_facets(geography_code: str = Query(default="", max_length=20), settings: Settings = Depends(get_settings)):
    from .trade_energy_resource_security_observatory import build_facets
    return build_facets(settings,geography_code=geography_code)

@app.get("/public/trade-energy-resources/trade")
def public_trade_energy_resources_trade(geography_code: str = Query(default="", max_length=20), query: str = Query(default="", max_length=240), limit: int = Query(default=250, ge=1, le=300), settings: Settings = Depends(get_settings)):
    from .trade_energy_resource_security_observatory import build_trade
    return build_trade(settings,geography_code=geography_code,query=query,limit=limit)

@app.get("/public/trade-energy-resources/energy")
def public_trade_energy_resources_energy(geography_code: str = Query(default="", max_length=20), query: str = Query(default="", max_length=240), limit: int = Query(default=250, ge=1, le=300), settings: Settings = Depends(get_settings)):
    from .trade_energy_resource_security_observatory import build_energy
    return build_energy(settings,geography_code=geography_code,query=query,limit=limit)

@app.get("/public/trade-energy-resources/resources")
def public_trade_energy_resources_resource_records(geography_code: str = Query(default="", max_length=20), query: str = Query(default="", max_length=240), limit: int = Query(default=250, ge=1, le=300), settings: Settings = Depends(get_settings)):
    from .trade_energy_resource_security_observatory import build_resources
    return build_resources(settings,geography_code=geography_code,query=query,limit=limit)

@app.get("/public/trade-energy-resources/dependencies")
def public_trade_energy_resources_dependencies(geography_code: str = Query(default="", max_length=20), family: str = Query(default="trade", max_length=100), limit: int = Query(default=250, ge=1, le=300), settings: Settings = Depends(get_settings)):
    from .trade_energy_resource_security_observatory import build_dependencies
    return build_dependencies(settings,geography_code=geography_code,family=family,limit=limit)

@app.get("/public/trade-energy-resources/country-profile")
def public_trade_energy_resources_country_profile(country: str = Query(..., min_length=2, max_length=20), limit: int = Query(default=300, ge=1, le=300), settings: Settings = Depends(get_settings)):
    from .trade_energy_resource_security_observatory import build_country_profile
    try:return build_country_profile(settings,country=country,limit=limit)
    except ValueError as exc:raise HTTPException(status_code=422,detail=str(exc)) from exc

@app.get("/public/trade-energy-resources/brief")
def public_trade_energy_resources_brief(geography_code: str = Query(default="", max_length=20), family: str = Query(default="", max_length=100), query: str = Query(default="", max_length=240), limit: int = Query(default=100, ge=1, le=150), settings: Settings = Depends(get_settings)):
    from .trade_energy_resource_security_observatory import build_brief
    return build_brief(settings,geography_code=geography_code,family=family,query=query,limit=limit)

@app.get("/public/trade-energy-resources/diagnostics")
def public_trade_energy_resources_diagnostics(settings: Settings = Depends(get_settings)):
    from .trade_energy_resource_security_observatory import build_diagnostics
    return build_diagnostics(settings)

# Site Intelligence v2.7.0 — Unified Country and Regional Intelligence Dossiers
@app.get("/public/intelligence-dossiers")
def public_intelligence_dossiers_overview(settings: Settings = Depends(get_settings)):
    from .unified_country_regional_dossiers import build_dossier_overview
    return build_dossier_overview(settings)

@app.get("/public/intelligence-dossiers/facets")
def public_intelligence_dossiers_facets(settings: Settings = Depends(get_settings)):
    from .unified_country_regional_dossiers import build_dossier_facets
    return build_dossier_facets(settings)

@app.get("/public/intelligence-dossiers/country")
def public_intelligence_dossiers_country(country: str = Query(..., min_length=2, max_length=20), limit_per_domain: int = Query(default=40, ge=5, le=60), settings: Settings = Depends(get_settings)):
    from .unified_country_regional_dossiers import build_country_dossier
    try:
        return build_country_dossier(settings, country=country, limit_per_domain=limit_per_domain)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

@app.get("/public/intelligence-dossiers/region")
def public_intelligence_dossiers_region(region: str = Query(..., min_length=2, max_length=160), limit_per_domain: int = Query(default=40, ge=5, le=60), settings: Settings = Depends(get_settings)):
    from .unified_country_regional_dossiers import build_regional_dossier
    try:
        return build_regional_dossier(settings, region=region, limit_per_domain=limit_per_domain)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

@app.get("/public/intelligence-dossiers/compare")
def public_intelligence_dossiers_compare(country_a: str = Query(..., min_length=2, max_length=20), country_b: str = Query(..., min_length=2, max_length=20), limit_per_domain: int = Query(default=12, ge=5, le=30), settings: Settings = Depends(get_settings)):
    from .unified_country_regional_dossiers import build_dossier_comparison
    try:
        return build_dossier_comparison(settings, country_a=country_a, country_b=country_b, limit_per_domain=limit_per_domain)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

@app.get("/public/intelligence-dossiers/brief")
def public_intelligence_dossiers_brief(country: str = Query(default="", max_length=20), region: str = Query(default="", max_length=160), limit_per_domain: int = Query(default=10, ge=5, le=30), settings: Settings = Depends(get_settings)):
    from .unified_country_regional_dossiers import build_dossier_brief
    try:
        return build_dossier_brief(settings, country=country, region=region, limit_per_domain=limit_per_domain)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

@app.get("/public/intelligence-dossiers/diagnostics")
def public_intelligence_dossiers_diagnostics(settings: Settings = Depends(get_settings)):
    from .unified_country_regional_dossiers import build_dossier_diagnostics
    return build_dossier_diagnostics(settings)

# Site Intelligence v2.8.0 — Alerts, Monitoring, and Live Intelligence Streams
@app.get("/public/alerts-monitoring")
def public_alerts_monitoring_overview(settings: Settings = Depends(get_settings)):
    from .alerts_monitoring_live_streams import build_monitoring_overview
    return build_monitoring_overview(settings)

@app.get("/public/live-intelligence-stream")
def public_live_intelligence_stream(
    families: str = Query(default="", max_length=240),
    country: str = Query(default="", max_length=20),
    query: str = Query(default="", max_length=240),
    source_id: str = Query(default="", max_length=180),
    freshness: str = Query(default="", max_length=80),
    limit: int = Query(default=180, ge=1, le=400),
    settings: Settings = Depends(get_settings),
):
    from .alerts_monitoring_live_streams import build_stream_snapshot
    return build_stream_snapshot(settings, families=families, country=country, query=query, source_id=source_id, freshness=freshness, limit=limit)

@app.get("/public/live-intelligence-stream/events")
def public_live_intelligence_stream_events(
    families: str = Query(default="", max_length=240),
    country: str = Query(default="", max_length=20),
    query: str = Query(default="", max_length=240),
    source_id: str = Query(default="", max_length=180),
    freshness: str = Query(default="", max_length=80),
    limit: int = Query(default=120, ge=1, le=300),
    settings: Settings = Depends(get_settings),
):
    from .alerts_monitoring_live_streams import build_sse_snapshot
    payload = build_sse_snapshot(settings, families=families, country=country, query=query, source_id=source_id, freshness=freshness, limit=limit)
    return Response(payload, media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

@app.get("/public/alerts-monitoring/facets")
def public_alerts_monitoring_facets(limit: int = Query(default=240, ge=20, le=400), settings: Settings = Depends(get_settings)):
    from .alerts_monitoring_live_streams import build_monitoring_facets
    return build_monitoring_facets(settings, limit=limit)

@app.post("/public/alerts-monitoring/evaluate")
def public_alerts_monitoring_evaluate(payload: dict[str, Any] = Body(default_factory=dict), settings: Settings = Depends(get_settings)):
    from .alerts_monitoring_live_streams import evaluate_alert_rules
    rules = payload.get("rules") if isinstance(payload, dict) else []
    if rules is not None and not isinstance(rules, list):
        raise HTTPException(status_code=422, detail="rules must be a list")
    return evaluate_alert_rules(settings, rules=rules or [])

@app.get("/public/alerts-monitoring/sources")
def public_alerts_monitoring_sources(limit: int = Query(default=240, ge=20, le=400), settings: Settings = Depends(get_settings)):
    from .alerts_monitoring_live_streams import build_source_watch
    return build_source_watch(settings, limit=limit)

@app.post("/public/alerts-monitoring/digest")
def public_alerts_monitoring_digest(payload: dict[str, Any] = Body(default_factory=dict), settings: Settings = Depends(get_settings)):
    from .alerts_monitoring_live_streams import build_monitoring_digest
    rules = payload.get("rules") if isinstance(payload, dict) else []
    if rules is not None and not isinstance(rules, list):
        raise HTTPException(status_code=422, detail="rules must be a list")
    return build_monitoring_digest(
        settings,
        rules=rules or [],
        country=str(payload.get("country") or ""),
        families=payload.get("families") or None,
        limit=max(1, min(int(payload.get("limit") or 120), 300)),
    )

@app.get("/public/alerts-monitoring/diagnostics")
def public_alerts_monitoring_diagnostics(settings: Settings = Depends(get_settings)):
    from .alerts_monitoring_live_streams import build_monitoring_diagnostics
    return build_monitoring_diagnostics(settings)

# Site Intelligence v2.9.0 — Comparative Intelligence and Scenario Studio
@app.get("/public/comparative-scenario-studio")
def public_comparative_scenario_studio(settings: Settings = Depends(get_settings)):
    from .comparative_scenario_studio_v290 import build_studio_overview
    return build_studio_overview(settings)

@app.get("/public/comparative-scenario-studio/facets")
def public_comparative_scenario_facets(limit: int = Query(default=400, ge=20, le=500), settings: Settings = Depends(get_settings)):
    from .comparative_scenario_studio_v290 import build_studio_facets
    return build_studio_facets(settings, limit=limit)

@app.post("/public/comparative-scenario-studio/compare")
def public_comparative_scenario_compare(payload: dict[str, Any] = Body(default_factory=dict), settings: Settings = Depends(get_settings)):
    from .comparative_scenario_studio_v290 import build_comparison_matrix
    try:
        return build_comparison_matrix(settings, geographies=payload.get("geographies"), indicators=payload.get("indicators"), domains=payload.get("domains"), start=str(payload.get("start") or ""), end=str(payload.get("end") or ""), limit=max(50, min(int(payload.get("limit") or 400), 500)))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

@app.get("/public/comparative-scenario-studio/peers")
def public_comparative_scenario_peers(geography: str = Query(..., min_length=2, max_length=20), region: str = Query(default="", max_length=160), settings: Settings = Depends(get_settings)):
    from .comparative_scenario_studio_v290 import build_peer_group
    try:
        return build_peer_group(settings, geography=geography, region=region)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

@app.post("/public/comparative-scenario-studio/scenario")
def public_comparative_scenario_transform(payload: dict[str, Any] = Body(default_factory=dict), settings: Settings = Depends(get_settings)):
    from .comparative_scenario_studio_v290 import build_transparent_scenario
    try:
        return build_transparent_scenario(settings, geographies=payload.get("geographies"), indicators=payload.get("indicators"), domains=payload.get("domains"), adjustments=payload.get("adjustments"), start=str(payload.get("start") or ""), end=str(payload.get("end") or ""))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

@app.post("/public/comparative-scenario-studio/correlation")
def public_comparative_scenario_correlation(payload: dict[str, Any] = Body(default_factory=dict), settings: Settings = Depends(get_settings)):
    from .comparative_scenario_studio_v290 import build_correlation_review
    try:
        return build_correlation_review(settings, geography=str(payload.get("geography") or ""), indicator_x=str(payload.get("indicator_x") or ""), indicator_y=str(payload.get("indicator_y") or ""), limit=max(3, min(int(payload.get("limit") or 200), 300)))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

@app.post("/public/comparative-scenario-studio/packet")
def public_comparative_scenario_packet(payload: dict[str, Any] = Body(default_factory=dict), settings: Settings = Depends(get_settings)):
    from .comparative_scenario_studio_v290 import build_comparison_packet
    try:
        return build_comparison_packet(settings, payload=payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

@app.get("/public/comparative-scenario-studio/diagnostics")
def public_comparative_scenario_diagnostics(settings: Settings = Depends(get_settings)):
    from .comparative_scenario_studio_v290 import build_studio_diagnostics
    return build_studio_diagnostics(settings)

# Site Intelligence v2.10.0 — Research Paths, Saved Investigations, and Briefing Workflows
@app.get("/public/research-workflows")
def public_research_workflows(settings: Settings = Depends(get_settings)):
    from .research_paths_investigations_v2100 import build_workflow_overview
    return build_workflow_overview(settings)

@app.get("/public/research-workflows/schema")
def public_research_workflow_schema(settings: Settings = Depends(get_settings)):
    from .research_paths_investigations_v2100 import build_workflow_schema
    return build_workflow_schema(settings)

@app.post("/public/research-workflows/validate")
def public_research_workflow_validate(payload: dict[str, Any] = Body(default_factory=dict), settings: Settings = Depends(get_settings)):
    from .research_paths_investigations_v2100 import validate_investigation
    try:
        return validate_investigation(payload, settings)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

@app.post("/public/research-workflows/evidence-set")
def public_research_workflow_evidence_set(payload: dict[str, Any] = Body(default_factory=dict), settings: Settings = Depends(get_settings)):
    from .research_paths_investigations_v2100 import build_evidence_set
    try:
        return build_evidence_set(payload, settings)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

@app.post("/public/research-workflows/briefing")
def public_research_workflow_briefing(payload: dict[str, Any] = Body(default_factory=dict), settings: Settings = Depends(get_settings)):
    from .research_paths_investigations_v2100 import build_briefing_packet
    try:
        return build_briefing_packet(payload, settings)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

@app.post("/public/research-workflows/handoff/{target}")
def public_research_workflow_handoff(target: str, payload: dict[str, Any] = Body(default_factory=dict), settings: Settings = Depends(get_settings)):
    from .research_paths_investigations_v2100 import build_product_handoff
    try:
        return build_product_handoff(payload, target, settings)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

@app.get("/public/research-workflows/diagnostics")
def public_research_workflow_diagnostics(settings: Settings = Depends(get_settings)):
    from .research_paths_investigations_v2100 import build_workflow_diagnostics
    return build_workflow_diagnostics(settings)

# Site Intelligence v2.11.0 — Public Data API, Embeds, and Institutional Integration
@app.get("/public/public-data-api-integration")
def public_data_api_integration(settings: Settings = Depends(get_settings)):
    from .public_data_api_embeds_v2110 import build_overview
    return build_overview(settings)

@app.get("/api/public/v1")
def public_data_api_root(settings: Settings = Depends(get_settings)):
    from .public_data_api_embeds_v2110 import build_overview
    return build_overview(settings)

@app.get("/api/public/v1/catalog")
def public_data_api_catalog(settings: Settings = Depends(get_settings)):
    from .public_data_api_embeds_v2110 import build_catalog
    return build_catalog(settings)


# Site Intelligence v3.4.0 — Typed Cross-Platform Intelligence Workflows.
def _cross_platform_workflows(settings: Settings) -> CrossPlatformWorkflowCenter:
    if not settings.cross_platform_workflows_enabled:
        raise HTTPException(status_code=503, detail="Cross-platform workflows are disabled.")
    return CrossPlatformWorkflowCenter(settings)


def _workflow_actor(request: dict[str, Any]) -> tuple[str, str]:
    return str(request.get("actor_role") or "administrator"), str(request.get("actor_id") or "system")


@app.get("/public/cross-platform-workflows")
def public_cross_platform_workflows_endpoint(settings: Settings = Depends(get_settings)):
    return _cross_platform_workflows(settings).public_summary()


@app.get("/public/cross-platform-workflows/diagnostics")
def public_cross_platform_workflows_diagnostics_endpoint(settings: Settings = Depends(get_settings)):
    return _cross_platform_workflows(settings).diagnostics(public=True)


@app.get("/admin/cross-platform-workflows/control-center")
def admin_cross_platform_workflows_control_center_endpoint(settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    return _cross_platform_workflows(settings).control_center()


@app.post("/admin/cross-platform-workflows/packets")
def admin_cross_platform_workflow_create_endpoint(request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    role, actor = _workflow_actor(request)
    try:
        return _cross_platform_workflows(settings).create_packet(request, role, actor)
    except (ValueError, PermissionError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/cross-platform-workflows/incoming")
def admin_cross_platform_workflow_incoming_endpoint(request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    role, actor = _workflow_actor(request)
    try:
        return _cross_platform_workflows(settings).ingest_incoming(request, role, actor)
    except (ValueError, PermissionError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/admin/cross-platform-workflows/packets/{packet_id}/validate")
def admin_cross_platform_workflow_validate_endpoint(packet_id: str, settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _cross_platform_workflows(settings).validate_packet(packet_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Packet not found.") from exc


@app.get("/admin/cross-platform-workflows/packets/{packet_id}/dispatch-preview")
def admin_cross_platform_workflow_dispatch_preview_endpoint(packet_id: str, settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _cross_platform_workflows(settings).dispatch_preview(packet_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Packet not found.") from exc


@app.post("/admin/cross-platform-workflows/packets/{packet_id}/queue")
def admin_cross_platform_workflow_queue_endpoint(packet_id: str, request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _cross_platform_workflows(settings).queue_packet(packet_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Packet not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/cross-platform-workflows/packets/{packet_id}/receipts")
def admin_cross_platform_workflow_receipt_endpoint(packet_id: str, request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _cross_platform_workflows(settings).record_receipt(packet_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Packet not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/admin/cross-platform-workflows/packets/{packet_id}/retry-preview")
def admin_cross_platform_workflow_retry_preview_endpoint(packet_id: str, settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _cross_platform_workflows(settings).retry_preview(packet_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Packet not found.") from exc


@app.post("/admin/cross-platform-workflows/packets/{packet_id}/retry")
def admin_cross_platform_workflow_retry_endpoint(packet_id: str, request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _cross_platform_workflows(settings).retry_failed(packet_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Packet not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/cross-platform-workflows/packets/{packet_id}/linkbacks")
def admin_cross_platform_workflow_linkback_endpoint(packet_id: str, request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _cross_platform_workflows(settings).add_linkback(packet_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Packet not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/admin/cross-platform-workflows/packets/{packet_id}/export")
def admin_cross_platform_workflow_export_endpoint(packet_id: str, settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        body = _cross_platform_workflows(settings).export_packet(packet_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Packet not found.") from exc
    return Response(content=body, media_type="application/json", headers={"Content-Disposition": f'attachment; filename="cross-platform-packet-{packet_id}.json"', "X-SC-Site-Intelligence-Version": APP_VERSION})

@app.get("/api/public/v1/workspaces")
def public_data_api_workspaces(settings: Settings = Depends(get_settings)):
    from .public_data_api_embeds_v2110 import build_catalog
    return build_catalog(settings)

@app.get("/api/public/v1/workspaces/{workspace_id}")
def public_data_api_workspace(workspace_id: str, settings: Settings = Depends(get_settings)):
    from .public_data_api_embeds_v2110 import build_workspace_manifest
    try:
        return build_workspace_manifest(workspace_id, settings)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

@app.get("/api/public/v1/workspaces/{workspace_id}/records")
def public_data_api_workspace_records(
    workspace_id: str,
    country: str = Query(default="", max_length=20),
    geography_code: str = Query(default="", max_length=20),
    source_id: str = Query(default="", max_length=180),
    query: str = Query(default="", max_length=240),
    family: str = Query(default="", max_length=100),
    domain: str = Query(default="", max_length=100),
    category: str = Query(default="", max_length=100),
    discipline: str = Query(default="", max_length=100),
    authority_level: str = Query(default="", max_length=100),
    record_type: str = Query(default="", max_length=100),
    indicator_code: str = Query(default="", max_length=160),
    bbox: str = Query(default="", max_length=120),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    settings: Settings = Depends(get_settings),
):
    from .public_data_api_embeds_v2110 import build_workspace_records
    try:
        return build_workspace_records(workspace_id, settings, country=country, geography_code=geography_code, source_id=source_id, query=query, family=family, domain=domain, category=category, discipline=discipline, authority_level=authority_level, record_type=record_type, indicator_code=indicator_code, bbox=bbox, limit=limit, offset=offset)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

@app.get("/api/public/v1/workspaces/{workspace_id}/records.csv")
def public_data_api_workspace_records_csv(
    workspace_id: str,
    country: str = Query(default="", max_length=20),
    source_id: str = Query(default="", max_length=180),
    query: str = Query(default="", max_length=240),
    family: str = Query(default="", max_length=100),
    limit: int = Query(default=100, ge=1, le=500),
    settings: Settings = Depends(get_settings),
):
    from .public_data_api_embeds_v2110 import build_workspace_csv
    try:
        content = build_workspace_csv(workspace_id, settings, country=country, source_id=source_id, query=query, family=family, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return Response(content=content, media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="site-intelligence-{workspace_id}-records.csv"'})

@app.get("/api/public/v1/embed")
def public_data_api_embed(
    view: str = Query(default="overview", max_length=80),
    theme: str = Query(default="system", max_length=20),
    chrome: str = Query(default="compact", max_length=20),
    height: int = Query(default=900, ge=420, le=2200),
    institution: str = Query(default="", max_length=120),
    settings: Settings = Depends(get_settings),
):
    from .public_data_api_embeds_v2110 import build_embed_manifest
    try:
        return build_embed_manifest(view, theme=theme, chrome=chrome, height=height, institution=institution, settings=settings)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

@app.get("/api/public/v1/institution")
def public_data_api_institution(settings: Settings = Depends(get_settings)):
    from .public_data_api_embeds_v2110 import build_institution_profile
    return build_institution_profile(settings)

@app.get("/api/public/v1/openapi-summary")
def public_data_api_openapi_summary(settings: Settings = Depends(get_settings)):
    from .public_data_api_embeds_v2110 import build_openapi_summary
    return build_openapi_summary(settings)

@app.get("/api/public/v1/diagnostics")
def public_data_api_diagnostics(settings: Settings = Depends(get_settings)):
    from .public_data_api_embeds_v2110 import build_diagnostics
    return build_diagnostics(settings)


# Site Intelligence v2.13.0 — Connector Operations and Data Ingestion Control Center.
@app.get("/public/offline-experience")
def offline_experience(settings: Settings = Depends(get_settings)):
    from .offline_mobile_accessibility_performance_v2120 import build_overview
    return build_overview(settings)

@app.get("/public/offline-experience/cache-plan")
def offline_experience_cache_plan(settings: Settings = Depends(get_settings)):
    from .offline_mobile_accessibility_performance_v2120 import build_cache_plan
    return build_cache_plan(settings)

@app.get("/public/offline-experience/accessibility")
def offline_experience_accessibility(settings: Settings = Depends(get_settings)):
    from .offline_mobile_accessibility_performance_v2120 import build_accessibility
    return build_accessibility(settings)

@app.get("/public/offline-experience/performance")
def offline_experience_performance(settings: Settings = Depends(get_settings)):
    from .offline_mobile_accessibility_performance_v2120 import build_performance
    return build_performance(settings)

@app.get("/public/offline-experience/diagnostics")
def offline_experience_diagnostics(settings: Settings = Depends(get_settings)):
    from .offline_mobile_accessibility_performance_v2120 import build_diagnostics
    return build_diagnostics(settings)

@app.get("/public/offline-experience/reliability")
def offline_experience_reliability(settings: Settings = Depends(get_settings)):
    from .offline_mobile_accessibility_performance_v2120 import build_reliability
    return build_reliability(settings)


# Site Intelligence v3.4.0 — Open Standards, Federation, and Institutional Data Exchange.
def _federation_exchange(settings: Settings) -> InstitutionalDataExchange:
    if not settings.federation_exchange_enabled:
        raise HTTPException(status_code=503, detail="Institutional data exchange is disabled.")
    return InstitutionalDataExchange(settings)


@app.get("/public/institutional-data-exchange")
def public_institutional_data_exchange_endpoint(settings: Settings = Depends(get_settings)):
    return _federation_exchange(settings).public_summary()


@app.get("/public/institutional-data-exchange/diagnostics")
def public_institutional_data_exchange_diagnostics_endpoint(settings: Settings = Depends(get_settings)):
    return _federation_exchange(settings).diagnostics(public=True)


@app.get("/public/institutional-data-exchange/catalog")
def public_institutional_catalog_export_endpoint(format: str = Query(default="jsonld", pattern="^(json|jsonld|dcat|geojson|csv)$"), settings: Settings = Depends(get_settings)):
    try:
        body = _federation_exchange(settings).export_catalog(format, public_only=True)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    media = "application/ld+json" if format in {"json", "jsonld", "dcat"} else ("application/geo+json" if format == "geojson" else "text/csv")
    return Response(content=body, media_type=media, headers={"Content-Disposition": f'attachment; filename="site-intelligence-catalog-v2240.{"jsonld" if format in {"json","jsonld","dcat"} else format}"'})


@app.get("/admin/institutional-data-exchange/control-center")
def admin_institutional_data_exchange_control_center_endpoint(settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    return _federation_exchange(settings).control_center()


@app.post("/admin/institutional-data-exchange/institutions")
def admin_federation_register_institution_endpoint(request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _federation_exchange(settings).register_institution(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/institutional-data-exchange/records")
def admin_federation_register_record_endpoint(request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _federation_exchange(settings).register_record(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/institutional-data-exchange/trust/{institution_id}")
def admin_federation_set_trust_endpoint(institution_id: str, request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _federation_exchange(settings).set_trust_policy(institution_id, request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/institutional-data-exchange/manifests/{institution_id}")
def admin_federation_build_manifest_endpoint(institution_id: str, request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _federation_exchange(settings).build_manifest(institution_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Institution not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/institutional-data-exchange/manifests/{manifest_id}/publish")
def admin_federation_publish_manifest_endpoint(manifest_id: str, request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _federation_exchange(settings).publish_manifest(manifest_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Manifest not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/institutional-data-exchange/import-preview")
def admin_federation_import_preview_endpoint(request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    manifest = request.get("manifest")
    return _federation_exchange(settings).import_preview(manifest, request.get("institution_id"), request.get("verification_key"))


@app.post("/admin/institutional-data-exchange/imports")
def admin_federation_accept_import_endpoint(request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _federation_exchange(settings).accept_import(request.get("manifest"), request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# Site Intelligence v3.4.0 — Security, Privacy, Governance, and Production Scale.
def _production_governance(settings: Settings) -> ProductionGovernanceCenter:
    if not settings.production_governance_enabled:
        raise HTTPException(status_code=503, detail="Production governance is disabled.")
    return ProductionGovernanceCenter(settings)


def require_governance_scope(
    required_scope: str,
    settings: Settings,
    x_sc_api_key: Optional[str],
    x_sc_intelligence_token: Optional[str],
):
    if settings.environment != "production":
        return {"valid": True, "actor": "development", "scopes": [required_scope]}
    if settings.api_token and x_sc_intelligence_token == settings.api_token:
        return {"valid": True, "actor": "legacy-admin-token", "scopes": ["*"]}
    result = _production_governance(settings).verify_api_key(x_sc_api_key or "", required_scope)
    if not result.get("valid"):
        raise HTTPException(status_code=401 if result.get("reason") == "unknown_key" else 403, detail=f"Governance authorization failed: {result.get('reason')}")
    return result


@app.get("/public/production-governance")
def public_production_governance_endpoint(settings: Settings = Depends(get_settings)):
    return _production_governance(settings).public_summary()


@app.get("/public/production-governance/diagnostics")
def public_production_governance_diagnostics_endpoint(settings: Settings = Depends(get_settings)):
    return _production_governance(settings).diagnostics(public=True)


@app.get("/admin/production-governance/control-center")
def admin_production_governance_control_center_endpoint(settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    return _production_governance(settings).control_center()


@app.post("/admin/production-governance/migrations")
def admin_production_governance_migrations_endpoint(settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    return _production_governance(settings).apply_migrations()


@app.post("/admin/production-governance/api-keys")
def admin_production_governance_create_api_key_endpoint(request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _production_governance(settings).create_api_key(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/production-governance/api-keys/{key_id}/revoke")
def admin_production_governance_revoke_api_key_endpoint(key_id: str, settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _production_governance(settings).revoke_api_key(key_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="API key not found.") from exc


@app.get("/admin/production-governance/audit")
def admin_production_governance_audit_endpoint(limit: int = Query(default=100, ge=1, le=1000), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    center = _production_governance(settings)
    return {"events": center.audit_events(limit), "verification": center.verify_audit_chain()}


@app.post("/admin/production-governance/privacy-requests")
def admin_production_governance_privacy_request_endpoint(request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _production_governance(settings).create_privacy_request(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/production-governance/privacy-requests/{request_id}")
def admin_production_governance_privacy_update_endpoint(request_id: str, request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _production_governance(settings).update_privacy_request(request_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Privacy request not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/production-governance/retention/preview")
def admin_production_governance_retention_preview_endpoint(request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _production_governance(settings).retention_preview(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/production-governance/retention/apply")
def admin_production_governance_retention_apply_endpoint(request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _production_governance(settings).apply_retention(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/production-governance/backups")
def admin_production_governance_backup_endpoint(request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    return _production_governance(settings).create_backup(request)


@app.get("/admin/production-governance/backups/{backup_id}/verify")
def admin_production_governance_verify_backup_endpoint(backup_id: str, settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _production_governance(settings).verify_backup(backup_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Backup not found.") from exc


@app.get("/admin/production-governance/backups/{backup_id}/restore-preview")
def admin_production_governance_restore_preview_endpoint(backup_id: str, settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _production_governance(settings).restore_preview(backup_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Backup not found.") from exc


@app.post("/admin/production-governance/jobs")
def admin_production_governance_enqueue_job_endpoint(request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    return _production_governance(settings).enqueue_job(request)


@app.post("/admin/production-governance/jobs/lease")
def admin_production_governance_lease_job_endpoint(request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    return _production_governance(settings).lease_job(request.get("worker_id") or "worker", request.get("lease_seconds") or 60)


@app.post("/admin/production-governance/jobs/{job_id}/complete")
def admin_production_governance_complete_job_endpoint(job_id: str, request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _production_governance(settings).complete_job(job_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Job not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/production-governance/deployments")
def admin_production_governance_deployment_endpoint(request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    return _production_governance(settings).record_deployment(request)


@app.get("/admin/production-governance/load-probe")
def admin_production_governance_load_probe_endpoint(requests: int = Query(default=250, ge=1, le=5000), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    return _production_governance(settings).load_probe(requests)

# Site Intelligence v3.4.0 — Signal Context and Drill-Down.
def _connected_platform(settings: Settings) -> ConnectedPublicIntelligencePlatform:
    if not settings.connected_platform_enabled:
        raise HTTPException(status_code=404, detail="Connected platform is disabled.")
    return ConnectedPublicIntelligencePlatform(settings)


@app.get("/public/live-intelligence")
def public_live_intelligence_endpoint(
    category: str = Query(default="", max_length=80),
    limit: int = Query(default=16, ge=1, le=24),
    feeds: str = Query(default="", max_length=320),
    exclude: str = Query(default="", max_length=320),
    max_per_source: int = Query(default=2, ge=1, le=5),
    settings: Settings = Depends(get_settings),
):
    return build_live_intelligence(
        settings,
        category=category,
        limit=limit,
        feeds=feeds,
        exclude=exclude,
        max_per_source=max_per_source,
    )


@app.get("/public/live-intelligence/status")
def public_live_intelligence_status_endpoint(settings: Settings = Depends(get_settings)):
    return live_intelligence_status(settings)


@app.get("/public/live-intelligence/ranking-policy")
def public_live_intelligence_ranking_policy_endpoint():
    return live_intelligence_ranking_policy()


@app.get("/public/live-intelligence/context-policy")
def public_live_intelligence_context_policy_endpoint():
    return live_signal_context_policy()


@app.get("/public/live-intelligence/signals/{signal_id}")
def public_live_intelligence_signal_context_endpoint(signal_id: str, settings: Settings = Depends(get_settings)):
    if not settings.live_intelligence_context_enabled:
        raise HTTPException(status_code=404, detail="Live Intelligence signal context is disabled.")
    try:
        return build_signal_context(settings, signal_id, build_live_intelligence)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Live Intelligence signal not found in the current feed.") from exc


@app.get("/public/live-intelligence/signals/{signal_id}/evidence")
def public_live_intelligence_signal_evidence_endpoint(signal_id: str, settings: Settings = Depends(get_settings)):
    if not settings.live_intelligence_context_enabled:
        raise HTTPException(status_code=404, detail="Live Intelligence signal context is disabled.")
    try:
        return build_signal_evidence(settings, signal_id, build_live_intelligence)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Live Intelligence signal not found in the current feed.") from exc


@app.get("/public/live-intelligence/signals/{signal_id}/view", response_class=HTMLResponse)
def public_live_intelligence_signal_context_view_endpoint(signal_id: str, settings: Settings = Depends(get_settings)):
    if not settings.live_intelligence_context_enabled:
        raise HTTPException(status_code=404, detail="Live Intelligence signal context is disabled.")
    try:
        context = build_signal_context(settings, signal_id, build_live_intelligence)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Live Intelligence signal not found in the current feed.") from exc
    return HTMLResponse(
        render_signal_context_html(context),
        headers={"Cache-Control": "public, max-age=120, stale-while-revalidate=600"},
    )


def _live_source_operations(settings: Settings) -> LiveIntelligenceSourceOperations:
    if not settings.live_source_operations_enabled:
        raise HTTPException(status_code=403, detail="Live Intelligence source operations are disabled.")
    try:
        return LiveIntelligenceSourceOperations(settings)
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/public/live-intelligence/sources")
def public_live_intelligence_sources_endpoint(settings: Settings = Depends(get_settings)):
    return _live_source_operations(settings).registry(public=True)


@app.get("/public/live-intelligence/sources/{feed_id}")
def public_live_intelligence_source_endpoint(feed_id: str, settings: Settings = Depends(get_settings)):
    try:
        return _live_source_operations(settings).source(feed_id, public=True)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Live Intelligence source not found.") from exc


@app.get("/admin/live-intelligence/sources/control-center")
def admin_live_intelligence_sources_control_center_endpoint(settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    return _live_source_operations(settings).control_center()


@app.get("/admin/live-intelligence/sources/history")
def admin_live_intelligence_sources_history_endpoint(
    feed_id: str = Query(default="", max_length=80),
    limit: int = Query(default=100, ge=1, le=500),
    settings: Settings = Depends(get_settings),
    _: None = Depends(require_token),
):
    try:
        return _live_source_operations(settings).history(feed_id=feed_id, limit=limit)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Live Intelligence source not found.") from exc


@app.patch("/admin/live-intelligence/sources/{feed_id}")
def admin_live_intelligence_source_update_endpoint(
    feed_id: str,
    request: dict = Body(default={}),
    settings: Settings = Depends(get_settings),
    _: None = Depends(require_token),
):
    try:
        return _live_source_operations(settings).update_source(feed_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Live Intelligence source not found.") from exc


@app.post("/admin/live-intelligence/sources/{feed_id}/test")
def admin_live_intelligence_source_test_endpoint(
    feed_id: str,
    request: dict = Body(default={}),
    settings: Settings = Depends(get_settings),
    _: None = Depends(require_token),
):
    live = bool(request.get("live", False))
    runner = None
    if live:
        runner = lambda source_id: build_live_intelligence(
            settings, feeds=[source_id], limit=6, max_per_source=5, record_operations=False
        )
    try:
        return _live_source_operations(settings).manual_test(feed_id, live=live, test_runner=runner)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Live Intelligence source not found.") from exc


@app.get("/public/connected-intelligence")
def public_connected_intelligence_endpoint(settings: Settings = Depends(get_settings)):
    return _connected_platform(settings).overview()


@app.get("/public/connected-intelligence/search")
def public_connected_intelligence_search_endpoint(q: str = Query(default="", max_length=240), record_type: str = Query(default="", max_length=80), limit: int = Query(default=25, ge=1, le=100), settings: Settings = Depends(get_settings)):
    return _connected_platform(settings).search(q, record_type=record_type, limit=limit)


@app.get("/public/connected-intelligence/context/{record_id:path}")
def public_connected_intelligence_context_endpoint(record_id: str, settings: Settings = Depends(get_settings)):
    try:
        return _connected_platform(settings).context(record_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Connected intelligence record not found.") from exc


@app.get("/public/connected-intelligence/provenance/{record_id:path}")
def public_connected_intelligence_provenance_endpoint(record_id: str, settings: Settings = Depends(get_settings)):
    try:
        return _connected_platform(settings).provenance(record_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Connected intelligence record not found.") from exc


@app.get("/public/connected-intelligence/lifecycle")
def public_connected_intelligence_lifecycle_endpoint(settings: Settings = Depends(get_settings)):
    return _connected_platform(settings).lifecycle()


@app.get("/public/connected-intelligence/diagnostics")
def public_connected_intelligence_diagnostics_endpoint(settings: Settings = Depends(get_settings)):
    return _connected_platform(settings).diagnostics()


@app.get("/public/connected-intelligence/export")
def public_connected_intelligence_export_endpoint(q: str = Query(default="", max_length=240), format: str = Query(default="json", pattern="^(json|csv)$"), limit: int = Query(default=100, ge=1, le=100), settings: Settings = Depends(get_settings)):
    body, media_type = _connected_platform(settings).export(q, format_name=format, limit=limit)
    suffix = "csv" if format == "csv" else "json"
    return Response(content=body, media_type=media_type, headers={"Content-Disposition": f'attachment; filename="connected-intelligence-{APP_VERSION}.{suffix}"', "X-SC-Site-Intelligence-Version": APP_VERSION})


@app.get("/admin/connected-intelligence/control-center")
def admin_connected_intelligence_control_center_endpoint(settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    return _connected_platform(settings).control_center()


@app.post("/admin/connected-intelligence/reindex-preview")
def admin_connected_intelligence_reindex_preview_endpoint(settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    center = _connected_platform(settings)
    return {"ok": True, "version": APP_VERSION, "preview": True, "write_performed": False, "record_count": len(center.records()), "diagnostics": center.diagnostics()}

# Site Intelligence standalone public application.
from pathlib import Path as _Path
PUBLIC_APP_DIR = _Path(__file__).resolve().parent.parent / "public_app"
if PUBLIC_APP_DIR.exists():
    app.mount("/app/assets", StaticFiles(directory=str(PUBLIC_APP_DIR / "assets")), name="site-intelligence-app-assets")

    @app.get("/app/manifest.webmanifest", include_in_schema=False)
    def standalone_manifest():
        return FileResponse(str(PUBLIC_APP_DIR / "manifest.webmanifest"), media_type="application/manifest+json")

    @app.get("/app/service-worker.js", include_in_schema=False)
    def standalone_service_worker():
        return FileResponse(str(PUBLIC_APP_DIR / "service-worker.js"), media_type="application/javascript")

    @app.get("/app/offline.html", include_in_schema=False)
    def standalone_offline_page():
        return FileResponse(str(PUBLIC_APP_DIR / "offline.html"), media_type="text/html")

    @app.get("/app", include_in_schema=False)
    @app.get("/app/", include_in_schema=False)
    @app.get("/app/{route:path}", include_in_schema=False)
    def standalone_public_app(route: str = ""):
        return FileResponse(str(PUBLIC_APP_DIR / "index.html"))
