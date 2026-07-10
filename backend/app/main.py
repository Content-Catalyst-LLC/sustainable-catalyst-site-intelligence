from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from .config import Settings, get_settings
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
app = FastAPI(title=settings.app_name, version=settings.version)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


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


@app.get("/public/country-intelligence/{country_code}")
def public_country_intelligence(country_code: str):
    result = build_country_intelligence(country_code)
    if not result.get("ok"):
        raise HTTPException(status_code=422, detail=result)
    return result


@app.get("/public/cross-domain-comparison")
def public_cross_domain_comparison(country: str = "", compare: str = ""):
    return build_cross_domain_comparison(country, compare)


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
def public_sources_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    return build_public_sources()


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
def public_dashboard_methodology():
    return public_methodology()




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

