from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import hmac
import time
from typing import Any, Mapping, Optional

from fastapi import Body, Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import PlainTextResponse, FileResponse, Response, HTMLResponse

from .config import Settings, get_settings
from .version import APP_VERSION
from .build_info import public_build_info as build_public_build_info, public_deployment_status as build_public_deployment_status
from .deployment_gate_v3226 import build_release_gate
from .deployment_receipt_v3226 import public_deployment_receipt as build_public_deployment_receipt
from .runtime_diagnostics_v3224 import build_runtime_health
from .runtime_recovery_v3224 import build_runtime_recovery_contract
from .production_truth_v3231 import public_production_truth as build_public_production_truth, public_production_truth_route as build_public_production_truth_route
from .cartographic_interaction_v3232 import public_map_interaction_contract as build_public_map_interaction_contract
from .data_truth_v32371 import (public_data_truth as build_public_data_truth, public_data_truth_source as build_public_data_truth_source, public_data_truth_countries as build_public_data_truth_countries, public_country_data_truth as build_public_country_data_truth, public_country_source_truth as build_public_country_source_truth, public_country_indicator_truth as build_public_country_indicator_truth, public_coverage_matrix as build_public_coverage_matrix)
from .record_provenance_v4358 import (public_indicator_record_truth as build_public_indicator_record_truth, public_country_record_truth as build_public_country_record_truth, public_map_layer_truth as build_public_map_layer_truth, public_normalized_record_truth as build_public_normalized_record_truth, public_record_truth_manifest as build_public_record_truth_manifest)
from .workspace_evidence_unification_v4358 import (overview as build_workspace_evidence_overview, readiness as build_workspace_evidence_readiness, canonical_country_observations as build_canonical_country_observations, canonical_country_indicator as build_canonical_country_indicator)
from .data_truth_control_plane_v3240 import (public_control_plane as build_public_control_plane, public_control_plane_sources as build_public_control_plane_sources, public_control_plane_source as build_public_control_plane_source, public_control_plane_history as build_public_control_plane_history, public_control_plane_schema_drift as build_public_control_plane_schema_drift, public_control_plane_outages as build_public_control_plane_outages, public_control_plane_coverage as build_public_control_plane_coverage, public_control_plane_workspaces as build_public_control_plane_workspaces, public_control_plane_export as build_public_control_plane_export)
from .analytical_workspaces_v3234 import public_analytical_workspaces as build_public_analytical_workspaces, public_analytical_workspace as build_public_analytical_workspace, public_analytical_snapshot as build_public_analytical_snapshot
from .unified_analytical_state_v3250 import (
    public_unified_analytical_state as build_public_unified_analytical_state,
    public_normalize_analytical_state as build_public_normalize_analytical_state,
    public_analytical_deep_link as build_public_analytical_deep_link,
    public_analytical_handoff as build_public_analytical_handoff,
)
from .comparative_model_assurance_v3260 import (
    public_assurance as build_public_assurance,
    public_comparison_assurance as build_public_comparison_assurance,
    public_scenario_assurance as build_public_scenario_assurance,
    public_model_assurance_review as build_public_model_assurance_review,
    public_assurance_model_cards as build_public_assurance_model_cards,
    public_assurance_package as build_public_assurance_package,
)
from .research_evidence_integration_v3270 import (
    public_research_integration as build_public_research_integration,
    public_research_context as build_public_research_context,
    public_research_manifest as build_public_research_manifest,
    public_research_citations as build_public_research_citations,
    public_research_claim_map as build_public_research_claim_map,
    public_knowledge_library_discovery as build_public_knowledge_library_discovery,
    public_research_handoff_preview as build_public_research_handoff_preview,
)
from .monitoring_early_warning_v3280 import (
    public_monitoring_operations as build_public_monitoring_operations,
    public_watchlist_preview as build_public_watchlist_preview,
    public_monitoring_evaluation as build_public_monitoring_evaluation,
    public_source_change_monitoring as build_public_source_change_monitoring,
    public_modeled_warning_preview as build_public_modeled_warning_preview,
    public_monitoring_digest_preview as build_public_monitoring_digest_preview,
    public_monitoring_feed_contract as build_public_monitoring_feed_contract,
)
from .briefing_publication_studio_v3290 import (
    public_briefing_publication_studio as build_public_briefing_publication_studio,
    public_frozen_evidence_manifest as build_public_frozen_evidence_manifest,
    public_briefing_preview as build_public_briefing_preview,
    public_story_map_preview as build_public_story_map_preview,
    public_publication_readiness as build_public_publication_readiness,
    public_publication_correction_preview as build_public_publication_correction_preview,
    public_publication_package as build_public_publication_package,
)
from .institutional_review_governance_v3300 import (
    public_institutional_governance as build_public_institutional_governance,
    public_workspace_governance_preview as build_public_workspace_governance_preview,
    public_review_queue_preview as build_public_review_queue_preview,
    public_annotation_governance_preview as build_public_annotation_governance_preview,
    public_review_decision_preview as build_public_review_decision_preview,
    public_workspace_audit_preview as build_public_workspace_audit_preview,
    public_workspace_package_export as build_public_workspace_package_export,
    public_workspace_package_import_preview as build_public_workspace_package_import_preview,
)
from .security_observability_assurance_v3310 import (
    public_security_observability_assurance as build_public_security_observability_assurance,
    public_security_posture as build_public_security_posture,
    public_observability_posture as build_public_observability_posture,
    public_performance_budget as build_public_performance_budget,
    public_rate_limit_preview as build_public_rate_limit_preview,
    public_supply_chain_posture as build_public_supply_chain_posture,
    public_post_deploy_smoke_preview as build_public_post_deploy_smoke_preview,
)
from .unified_public_intelligence_v4000 import (
    public_unified_platform as build_public_unified_platform,
    public_unified_navigation as build_public_unified_navigation,
    public_unified_contracts as build_public_unified_contracts,
    public_v4_readiness as build_public_v4_readiness,
    public_v4_configuration_readiness as build_public_v4_configuration_readiness,
)
from .orbital_earth_v4100 import (
    overview as build_orbital_earth_overview,
    catalog as build_orbital_earth_catalog,
    state as build_orbital_earth_state,
    export_manifest as build_orbital_earth_export_manifest,
    readiness as build_orbital_earth_readiness,
)
from .planetary_intelligence_v4200 import (
    overview as build_planetary_overview,
    catalog as build_planetary_catalog,
    body as build_planetary_body,
    state as build_planetary_state,
    export_manifest as build_planetary_export_manifest,
    readiness as build_planetary_readiness,
)
from .astronomical_observation_v4300 import (
    overview as build_astronomical_overview,
    catalog as build_astronomical_catalog,
    target as build_astronomical_target,
    state as build_astronomical_state,
    export_manifest as build_astronomical_export_manifest,
    readiness as build_astronomical_readiness,
)
from .seti_technosignatures_v43400 import (
    overview as build_seti_overview,
    catalog as build_seti_catalog,
    state as build_seti_state,
    normalize_observation as build_seti_normalize_observation,
    normalize_signal as build_seti_normalize_signal,
    normalize_candidate as build_seti_normalize_candidate,
    export_manifest as build_seti_export_manifest,
    readiness as build_seti_readiness,
)
from .exoplanet_habitability_v43500 import (
    overview as build_exoplanet_habitability_overview,
    catalog as build_exoplanet_habitability_catalog,
    state as build_exoplanet_habitability_state,
    normalize_planet as build_exoplanet_habitability_normalize_planet,
    normalize_spectrum as build_exoplanet_habitability_normalize_spectrum,
    normalize_biosignature as build_exoplanet_habitability_normalize_biosignature,
    export_manifest as build_exoplanet_habitability_export_manifest,
    readiness as build_exoplanet_habitability_readiness,
)
from .solar_system_navigation_v4400 import (
    overview as build_solar_system_overview,
    catalog as build_solar_system_catalog,
    body as build_solar_system_body,
    mission as build_solar_system_mission,
    state as build_solar_system_state,
    normalize_ephemeris as build_solar_system_normalize_ephemeris,
    export_manifest as build_solar_system_export_manifest,
    readiness as build_solar_system_readiness,
)
from .ocean_observation_marine_systems_v4360 import (
    overview as build_ocean_observation_overview,
    catalog as build_ocean_observation_catalog,
    workspace_manifest as build_ocean_observation_manifest,
    readiness as build_ocean_observation_readiness,
)
from .ocean_surface_v4500 import (
    overview as build_ocean_surface_overview,
    catalog as build_ocean_surface_catalog,
    source as build_ocean_surface_source,
    state as build_ocean_surface_state,
    normalize_observation as build_ocean_surface_normalize_observation,
    export_manifest as build_ocean_surface_export_manifest,
    readiness as build_ocean_surface_readiness,
)
from .water_column_v4600 import (
    overview as build_water_column_overview,
    catalog as build_water_column_catalog,
    state as build_water_column_state,
    normalize_profile as build_water_column_normalize_profile,
    resolve_depth as build_water_column_resolve_depth,
    export_manifest as build_water_column_export_manifest,
    readiness as build_water_column_readiness,
)
from .seafloor_bathymetry_v4700 import (
    overview as build_seafloor_overview,
    catalog as build_seafloor_catalog,
    state as build_seafloor_state,
    normalize_sample as build_seafloor_normalize_sample,
    normalize_footprint as build_seafloor_normalize_footprint,
    export_manifest as build_seafloor_export_manifest,
    readiness as build_seafloor_readiness,
)
from .underwater_observation_v4800 import (
    overview as build_underwater_overview,
    catalog as build_underwater_catalog,
    state as build_underwater_state,
    normalize_media as build_underwater_normalize_media,
    normalize_annotation as build_underwater_normalize_annotation,
    export_manifest as build_underwater_export_manifest,
    readiness as build_underwater_readiness,
)
from .live_underwater_media_v4370 import (
    provider_catalog as build_live_underwater_provider_catalog,
    search as build_live_underwater_search,
    readiness as build_live_underwater_readiness,
    fetch_onc_image as build_live_underwater_onc_image,
)
from .live_space_observation_v4380 import (
    provider_catalog as build_live_space_provider_catalog,
    search as build_live_space_search,
    readiness as build_live_space_readiness,
)
from .marine_biodiversity_v4900 import (
    overview as build_marine_biodiversity_overview,
    catalog as build_marine_biodiversity_catalog,
    state as build_marine_biodiversity_state,
    normalize_occurrence as build_marine_biodiversity_normalize_occurrence,
    normalize_taxonomy as build_marine_biodiversity_normalize_taxonomy,
    normalize_visual as build_marine_biodiversity_normalize_visual,
    normalize_acoustic as build_marine_biodiversity_normalize_acoustic,
    export_manifest as build_marine_biodiversity_export_manifest,
    readiness as build_marine_biodiversity_readiness,
)
from .ocean_missions_v41000 import (
    overview as build_ocean_missions_overview,
    catalog as build_ocean_missions_catalog,
    state as build_ocean_missions_state,
    normalize_platform as build_ocean_missions_normalize_platform,
    normalize_mission as build_ocean_missions_normalize_mission,
    normalize_track as build_ocean_missions_normalize_track,
    export_manifest as build_ocean_missions_export_manifest,
    readiness as build_ocean_missions_readiness,
)
from .ocean_events_v41100 import (
    overview as build_ocean_events_overview,
    catalog as build_ocean_events_catalog,
    state as build_ocean_events_state,
    normalize_condition as build_ocean_events_normalize_condition,
    threshold_preview as build_ocean_events_threshold_preview,
    normalize_event as build_ocean_events_normalize_event,
    export_manifest as build_ocean_events_export_manifest,
    readiness as build_ocean_events_readiness,
)
from .marine_human_activity_v41200 import (
    overview as build_marine_human_activity_overview,
    catalog as build_marine_human_activity_catalog,
    state as build_marine_human_activity_state,
    normalize_activity as build_marine_human_activity_normalize_activity,
    normalize_protected_area as build_marine_human_activity_normalize_protected_area,
    overlap_preview as build_marine_human_activity_overlap_preview,
    export_manifest as build_marine_human_activity_export_manifest,
    readiness as build_marine_human_activity_readiness,
)
from .marine_pollution_v41300 import (
    overview as build_marine_pollution_overview,
    catalog as build_marine_pollution_catalog,
    state as build_marine_pollution_state,
    normalize_measurement as build_marine_pollution_normalize_measurement,
    normalize_debris as build_marine_pollution_normalize_debris,
    threshold_preview as build_marine_pollution_threshold_preview,
    export_manifest as build_marine_pollution_export_manifest,
    readiness as build_marine_pollution_readiness,
)
from .coastal_change_v41400 import (
    overview as build_coastal_change_overview,
    catalog as build_coastal_change_catalog,
    state as build_coastal_change_state,
    normalize_water_level as build_coastal_change_normalize_water_level,
    normalize_shoreline as build_coastal_change_normalize_shoreline,
    normalize_habitat as build_coastal_change_normalize_habitat,
    scenario_preview as build_coastal_change_scenario_preview,
    export_manifest as build_coastal_change_export_manifest,
    readiness as build_coastal_change_readiness,
)
from .ocean_governance_v41500 import (
    overview as build_ocean_governance_overview,
    catalog as build_ocean_governance_catalog,
    state as build_ocean_governance_state,
    normalize_zone as build_ocean_governance_normalize_zone,
    normalize_management_area as build_ocean_governance_normalize_management_area,
    overlap_preview as build_ocean_governance_overlap_preview,
    export_manifest as build_ocean_governance_export_manifest,
    readiness as build_ocean_governance_readiness,
)
from .cryosphere_v41600 import (
    overview as build_cryosphere_overview,
    catalog as build_cryosphere_catalog,
    state as build_cryosphere_state,
    normalize_measurement as build_cryosphere_normalize_measurement,
    normalize_feature as build_cryosphere_normalize_feature,
    anomaly_preview as build_cryosphere_anomaly_preview,
    export_manifest as build_cryosphere_export_manifest,
    readiness as build_cryosphere_readiness,
)
from .atmosphere_v41700 import (
    overview as build_atmosphere_overview,
    catalog as build_atmosphere_catalog,
    state as build_atmosphere_state,
    normalize_measurement as build_atmosphere_normalize_measurement,
    normalize_forecast as build_atmosphere_normalize_forecast,
    threshold_preview as build_atmosphere_threshold_preview,
    export_manifest as build_atmosphere_export_manifest,
    readiness as build_atmosphere_readiness,
)
from .hydrology_v41800 import (
    overview as build_hydrology_overview,
    catalog as build_hydrology_catalog,
    state as build_hydrology_state,
    normalize_measurement as build_hydrology_normalize_measurement,
    normalize_forecast as build_hydrology_normalize_forecast,
    threshold_preview as build_hydrology_threshold_preview,
    export_manifest as build_hydrology_export_manifest,
    readiness as build_hydrology_readiness,
)
from .terrestrial_ecosystems_v41900 import (
    overview as build_terrestrial_overview,
    catalog as build_terrestrial_catalog,
    state as build_terrestrial_state,
    normalize_measurement as build_terrestrial_normalize_measurement,
    normalize_feature as build_terrestrial_normalize_feature,
    threshold_preview as build_terrestrial_threshold_preview,
    export_manifest as build_terrestrial_export_manifest,
    readiness as build_terrestrial_readiness,
)
from .geosphere_v42000 import (
    overview as build_geosphere_overview,
    catalog as build_geosphere_catalog,
    state as build_geosphere_state,
    normalize_measurement as build_geosphere_normalize_measurement,
    normalize_notice as build_geosphere_normalize_notice,
    threshold_preview as build_geosphere_threshold_preview,
    export_manifest as build_geosphere_export_manifest,
    readiness as build_geosphere_readiness,
)
from .soils_land_degradation_v42100 import (
    overview as build_soils_overview,
    catalog as build_soils_catalog,
    state as build_soils_state,
    normalize_measurement as build_soils_normalize_measurement,
    normalize_assessment as build_soils_normalize_assessment,
    threshold_preview as build_soils_threshold_preview,
    export_manifest as build_soils_export_manifest,
    readiness as build_soils_readiness,
)
from .climate_intelligence_v42200 import (
    overview as build_climate_overview,
    catalog as build_climate_catalog,
    state as build_climate_state,
    normalize_measurement as build_climate_normalize_measurement,
    normalize_extreme as build_climate_normalize_extreme,
    threshold_preview as build_climate_threshold_preview,
    export_manifest as build_climate_export_manifest,
    readiness as build_climate_readiness,
)
from .agriculture_food_systems_v42500 import (
    overview as build_agriculture_overview, catalog as build_agriculture_catalog, state as build_agriculture_state,
    normalize_measurement as build_agriculture_normalize_measurement, normalize_assessment as build_agriculture_normalize_assessment,
    threshold_preview as build_agriculture_threshold_preview, export_manifest as build_agriculture_export_manifest, readiness as build_agriculture_readiness,
)
from .human_settlements_v42600 import (
    overview as build_human_settlements_overview, catalog as build_human_settlements_catalog, state as build_human_settlements_state,
    normalize_measurement as build_human_settlements_normalize_measurement, normalize_feature as build_human_settlements_normalize_feature,
    threshold_preview as build_human_settlements_threshold_preview, export_manifest as build_human_settlements_export_manifest, readiness as build_human_settlements_readiness,
)
from .transportation_infrastructure_v42700 import (
    overview as build_transportation_overview, catalog as build_transportation_catalog, state as build_transportation_state,
    normalize_feature as build_transportation_normalize_feature, normalize_feed as build_transportation_normalize_feed,
    accessibility_preview as build_transportation_accessibility_preview, export_manifest as build_transportation_export_manifest, readiness as build_transportation_readiness,
)
from .energy_systems_v42800 import (
    overview as build_energy_systems_overview, catalog as build_energy_systems_catalog, state as build_energy_systems_state,
    normalize_feature as build_energy_systems_normalize_feature, normalize_series as build_energy_systems_normalize_series,
    threshold_preview as build_energy_systems_threshold_preview, export_manifest as build_energy_systems_export_manifest, readiness as build_energy_systems_readiness,
)
from .digital_connectivity_v42900 import (
    overview as build_digital_connectivity_overview, catalog as build_digital_connectivity_catalog, state as build_digital_connectivity_state,
    normalize_feature as build_digital_connectivity_normalize_feature, normalize_measurement as build_digital_connectivity_normalize_measurement,
    normalize_availability as build_digital_connectivity_normalize_availability, threshold_preview as build_digital_connectivity_threshold_preview,
    export_manifest as build_digital_connectivity_export_manifest, readiness as build_digital_connectivity_readiness,
)
from .industrial_manufacturing_trade_v43000 import (
    overview as build_industrial_manufacturing_overview, catalog as build_industrial_manufacturing_catalog, state as build_industrial_manufacturing_state,
    normalize_feature as build_industrial_manufacturing_normalize_feature, normalize_series as build_industrial_manufacturing_normalize_series,
    normalize_trade_flow as build_industrial_manufacturing_normalize_trade_flow, threshold_preview as build_industrial_manufacturing_threshold_preview,
    export_manifest as build_industrial_manufacturing_export_manifest, readiness as build_industrial_manufacturing_readiness,
)
from .mining_critical_materials_v43100 import (
    overview as build_mining_overview, catalog as build_mining_catalog, state as build_mining_state,
    normalize_feature as build_mining_normalize_feature, normalize_resource as build_mining_normalize_resource,
    normalize_series as build_mining_normalize_series, threshold_preview as build_mining_threshold_preview,
    export_manifest as build_mining_export_manifest, readiness as build_mining_readiness,
)
from .water_sanitation_infrastructure_v43200 import (
    overview as build_water_sanitation_overview, catalog as build_water_sanitation_catalog, state as build_water_sanitation_state,
    normalize_feature as build_water_sanitation_normalize_feature, normalize_system as build_water_sanitation_normalize_system,
    normalize_series as build_water_sanitation_normalize_series, threshold_preview as build_water_sanitation_threshold_preview,
    export_manifest as build_water_sanitation_export_manifest, readiness as build_water_sanitation_readiness,
)
from .solid_waste_circular_materials_v43300 import (
    overview as build_solid_waste_overview, catalog as build_solid_waste_catalog, state as build_solid_waste_state,
    normalize_feature as build_solid_waste_normalize_feature, normalize_regulatory as build_solid_waste_normalize_regulatory,
    normalize_series as build_solid_waste_normalize_series, threshold_preview as build_solid_waste_threshold_preview,
    export_manifest as build_solid_waste_export_manifest, readiness as build_solid_waste_readiness,
)
from .wetlands_inland_waters_v42400 import (
    overview as build_wetlands_overview, catalog as build_wetlands_catalog, state as build_wetlands_state,
    normalize_feature as build_wetlands_normalize_feature, normalize_measurement as build_wetlands_normalize_measurement,
    overlap_preview as build_wetlands_overlap_preview, export_manifest as build_wetlands_export_manifest, readiness as build_wetlands_readiness,
)
from .biodiversity_intelligence_v42300 import (
    overview as build_biodiversity_overview,
    catalog as build_biodiversity_catalog,
    state as build_biodiversity_state,
    normalize_occurrence as build_biodiversity_normalize_occurrence,
    normalize_conservation as build_biodiversity_normalize_conservation,
    overlap_preview as build_biodiversity_overlap_preview,
    export_manifest as build_biodiversity_export_manifest,
    readiness as build_biodiversity_readiness,
)
from .browser_reliability_v3235 import public_browser_reliability_contract as build_public_browser_reliability_contract
from .performance_offline_v3236 import public_performance_offline_contract as build_public_performance_offline_contract
from .bootstrap_recovery_v32361 import public_bootstrap_recovery_contract as build_public_bootstrap_recovery_contract
from .mutation_observer_recovery_v32362 import public_mutation_observer_recovery_contract as build_public_mutation_observer_recovery_contract
from .embed_isolation_v32363 import public_embed_isolation_contract as build_public_embed_isolation_contract
from .startup_stability_v32364 import public_startup_stability_contract as build_public_startup_stability_contract
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
from .live_intelligence_reliability_v361 import (
    build_live_intelligence, build_channel_feed, live_intelligence_status,
    live_intelligence_ranking_policy, channel_directory as live_intelligence_channel_directory,
    channel_definition as live_intelligence_channel_definition, channel_policy as live_intelligence_channel_policy,
)
from .live_intelligence_presentation_v362 import presentation_policy as live_intelligence_presentation_policy
from .live_intelligence_gateway_v370 import (
    apply_gateway_policy as apply_live_intelligence_gateway_policy,
    homepage_gateway_policy as live_intelligence_gateway_policy,
    DEFAULT_HOMEPAGE_SIGNAL_LIMIT, MAX_HOMEPAGE_SIGNAL_LIMIT,
)
from .homepage_summary_v4390 import build_homepage_summary
from .live_intelligence_rotation_v371 import (
    apply_rotation_policy as apply_live_intelligence_rotation_policy,
    rotation_policy as live_intelligence_rotation_policy,
    LiveIntelligenceRotationStore,
)
from .live_intelligence_analytics_v372 import (
    LiveIntelligenceAnalyticsStore, analytics_policy as live_intelligence_analytics_policy,
)
from .live_intelligence_surfaces_v380 import (
    apply_connected_surface_policy, embed_manifest as live_intelligence_embed_manifest,
    normalize_surface_id as normalize_live_intelligence_surface_id,
    surface_definition as live_intelligence_surface_definition,
    surface_directory as live_intelligence_surface_directory,
    surface_policy as live_intelligence_surface_policy,
)
from .live_intelligence_subscriptions_v390 import (
    LiveIntelligenceSubscriptionCenter, preference_manifest as live_intelligence_preference_manifest,
    subscription_policy as live_intelligence_subscription_policy,
)
from .live_intelligence_briefings_v3100 import (
    LiveIntelligenceBriefingCenter, briefing_policy as live_intelligence_briefing_policy,
    briefing_templates as live_intelligence_briefing_templates,
)
from .live_intelligence_editorial_workspace_v3110 import (
    LiveIntelligenceEditorialWorkspace, editorial_workspace_policy as live_intelligence_editorial_policy,
)
from .live_intelligence_publication_releases_v3120 import (
    LiveIntelligencePublicationReleaseCenter, adapter_catalog as live_intelligence_publication_adapter_catalog,
    publication_release_policy as live_intelligence_publication_release_policy,
)
from .live_intelligence_release_operations_v3130 import (
    LiveIntelligenceReleaseOperationsCenter, release_operations_policy as live_intelligence_release_operations_policy,
)
from .live_intelligence_change_history_v3140 import (
    LiveIntelligenceChangeHistoryCenter, change_history_policy as live_intelligence_change_history_policy,
)
from .live_intelligence_public_archive_v3150 import (
    LiveIntelligencePublicArchive, public_archive_policy as live_intelligence_public_archive_policy,
)
from .live_intelligence_archive_audits_v3160 import (
    LiveIntelligenceArchiveAuditCenter, archive_audit_policy as live_intelligence_archive_audit_policy,
)
from .live_intelligence_preservation_exchange_v3170 import (
    LiveIntelligencePreservationExchangeCenter,
    preservation_exchange_policy as live_intelligence_preservation_exchange_policy,
)
from .live_intelligence_federated_registry_v3180 import (
    LiveIntelligenceFederatedPreservationRegistry,
    federated_registry_policy as live_intelligence_federated_registry_policy,
)
from .live_intelligence_registry_governance_v3190 import (
    LiveIntelligenceRegistryGovernanceCenter,
    registry_governance_policy as live_intelligence_registry_governance_policy,
)
from .live_intelligence_registry_discovery_v3200 import (
    LiveIntelligenceRegistryDiscovery,
    registry_discovery_policy as live_intelligence_registry_discovery_policy,
)
from .live_intelligence_registry_collections_v3210 import (
    LiveIntelligenceRegistryCollectionsCenter,
    registry_collections_policy as live_intelligence_registry_collections_policy,
)
from .live_intelligence_registry_publications_v3220 import (
    LiveIntelligenceRegistryPublicationCenter,
    registry_publication_policy as live_intelligence_registry_publication_policy,
)
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
from .authoritative_api_production_audit_v43516 import (
    audit_overview as build_authoritative_api_audit,
    audit_catalog as build_authoritative_api_catalog,
    workspace_matrix as build_authoritative_api_workspace_matrix,
    audit_readiness as build_authoritative_api_readiness,
    production_audit as build_authoritative_api_production_audit,
    closure_ledger as build_authoritative_api_closure_ledger,
    production_readiness as build_authoritative_api_production_readiness,
)
from .authoritative_connectors_v43515 import (
    connector_catalog as build_authoritative_connector_catalog,
    connector_readiness as build_authoritative_connector_readiness,
    usgs_water_latest as build_usgs_water_latest,
    noaa_erddap_search as build_noaa_erddap_search,
    noaa_erddap_tabledap as build_noaa_erddap_tabledap,
    nasa_exoplanet_planets as build_nasa_exoplanet_planets,
    unhcr_population as build_unhcr_population,
    nasa_cmr_collections as build_nasa_cmr_collections,
    noaa_coops_data as build_noaa_coops_data,
    ncei_access_data as build_ncei_access_data,
    obis_occurrences as build_obis_occurrences,
    eurostat_statistics as build_eurostat_statistics,
    usda_soil_mapunits as build_usda_soil_mapunits,
    usfws_nwi_wetlands as build_usfws_nwi_wetlands,
    epa_echo_facilities as build_epa_echo_facilities,
    nasa_firms_area as build_nasa_firms_area,
    usda_nass_quickstats as build_usda_nass_quickstats,
    nasa_cmr_graphql_collections as build_nasa_cmr_graphql_collections,
    pcbs_pxweb_metadata as build_pcbs_pxweb_metadata,
    pcbs_pxweb_data as build_pcbs_pxweb_data,
    statcan_vectors as build_statcan_vectors,
    ons_observations as build_ons_observations,
    abs_sdmx_data as build_abs_sdmx_data,
    bls_timeseries as build_bls_timeseries,
    faostat_data as build_faostat_data,
    ilostat_indicator as build_ilostat_indicator,
    oecd_sdmx_data as build_oecd_sdmx_data,
    epa_frs_facilities as build_epa_frs_facilities,
    usgs_volcano_notices as build_usgs_volcano_notices,
    osm_power as build_osm_power,
    eia_electricity as build_eia_electricity_v43511,
    ember_electricity as build_ember_electricity,
    entsoe_data as build_entsoe_data,
    osm_telecom as build_osm_telecom,
    mlab_locate as build_mlab_locate,
    fcc_bdc_asofs as build_fcc_bdc_asofs,
    airnow_current as build_airnow_current_v43512,
    era5_catalogue as build_era5_catalogue_v43512,
    cams_catalogue as build_cams_catalogue_v43512,
    osm_water as build_osm_water_v43513,
    epa_sdwis as build_epa_sdwis_v43513,
    nidis_drought_file as build_nidis_drought_file_v43513,
    nasa_gpm_imerg_discovery as build_nasa_gpm_imerg_discovery_v43513,
    glofas_layers as build_glofas_layers_v43513,
    gdacs_events as build_gdacs_events_v43514,
    hdx_dataset_search as build_hdx_dataset_search_v43514,
    hdx_hapi as build_hdx_hapi_v43514,
    ipc_food_security as build_ipc_food_security_v43514,
    fews_net_data as build_fews_net_data_v43514,
    osm_mining as build_osm_mining_v43515,
    usgs_usmin_discovery as build_usgs_usmin_discovery_v43515,
    usgs_mcs_2026_discovery as build_usgs_mcs_2026_discovery_v43515,
    osm_industrial as build_osm_industrial_v43515,
    wits_trade_stats as build_wits_trade_stats_v43515,
)
from .authoritative_connectors_v43521 import palestine_open_data_search as build_palestine_open_data_search_v43521
from .evidence_intelligence_v4357 import (
    overview as build_evidence_intelligence_overview,
    metric_catalog as build_evidence_metric_catalog,
    precedence_catalog as build_evidence_precedence_catalog,
    freshness_policy as build_evidence_freshness_policy,
    freshness_assessment as build_evidence_freshness_assessment,
    indicator_semantics as build_evidence_indicator_semantics,
    select_evidence as build_evidence_selection,
    readiness as build_evidence_intelligence_readiness,
)
from .release_health_v4380 import (
    deployment_verification as build_deployment_verification_v4380,
    source_health_policy as build_source_health_policy_v4380,
)
from .workspace_browser_audit_v43518 import (
    workspace_browser_audit as build_workspace_browser_audit_v43518,
    workspace_browser_readiness as build_workspace_browser_readiness_v43518,
    workspace_route_detail as build_workspace_route_detail_v43518,
)
from .credential_configuration_v43516 import (
    credential_registry as build_credential_configuration_v43516,
    credential_readiness as build_credential_configuration_readiness_v43516,
    credential_workspaces as build_credential_configuration_workspaces_v43516,
)
from .external_resilience_v43517 import (
    resilience_overview as build_external_resilience_v43517,
    resilience_readiness as build_external_resilience_readiness_v43517,
    resilience_provider_states as build_external_resilience_provider_states_v43517,
)
from .production_soak_v43519 import (
    run_soak_suite as build_production_soak_v43519,
    readiness as build_production_soak_readiness_v43519,
)
from .evidence_presentation_v43519 import (
    readiness as build_evidence_presentation_readiness_v43519,
    classify_evidence as build_evidence_presentation_classification_v43519,
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
    request: Request,
    settings: Settings = Depends(get_settings),
    x_sc_intelligence_token: Optional[str] = Header(default=None),
):
    if settings.environment == "production":
        if not settings.api_token or settings.api_token == "dev-token-change-me":
            raise HTTPException(status_code=401, detail="Production Site Intelligence API token is not configured securely.")
        if not x_sc_intelligence_token or not hmac.compare_digest(x_sc_intelligence_token, settings.api_token):
            raise HTTPException(status_code=401, detail="Invalid or missing Site Intelligence API token.")
        limiter_key = hashlib.sha256(x_sc_intelligence_token.encode("utf-8")).hexdigest()[:24]
        rate = _production_rate_limiter.check(limiter_key)
        if not rate["allowed"]:
            raise HTTPException(status_code=429, detail="Site Intelligence administrative rate limit exceeded.", headers={"Retry-After": str(rate["retry_after_seconds"])})


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
    allow_headers=["Accept", "Content-Type", "Cache-Control", "Pragma", "X-SC-Intelligence-Token"],
)
app.add_middleware(GZipMiddleware, minimum_size=1024, compresslevel=6)


@app.middleware("http")
async def public_experience_headers(request, call_next):
    started = time.perf_counter()
    response = await call_next(request)
    response.headers.setdefault("Server-Timing", f"app;dur={(time.perf_counter()-started)*1000:.2f}")
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
    if settings.environment == "production":
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    response.headers.setdefault("Vary", "Accept-Encoding")

    path = request.url.path
    is_app_surface = path == "/app" or path.startswith("/app/")
    if not (is_app_surface and settings.public_embeds_enabled):
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    else:
        if "X-Frame-Options" in response.headers:
            del response.headers["X-Frame-Options"]
    response.headers.setdefault("X-SC-Site-Intelligence-Version", APP_VERSION)
    if path in {"/health", "/public/build-info", "/public/deployment-status", "/public/deployment-receipt", "/public/release-gate"}:
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        response.headers["X-SC-Release-Gate"] = f"v{APP_VERSION}"
    elif path == "/app/service-worker.js":
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        response.headers.setdefault("Service-Worker-Allowed", "/app/")
        response.headers.setdefault("X-SC-Cache-Generation", f"scsi-v{APP_VERSION}")
    elif path in {"/app/manifest.webmanifest", "/app/offline.html"}:
        response.headers["Cache-Control"] = "no-cache, max-age=0, must-revalidate"
    elif path.startswith("/app/assets/"):
        response.headers.setdefault("Cache-Control", "public, max-age=3600, stale-while-revalidate=86400, stale-if-error=604800")
    elif is_app_surface:
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        if settings.public_embeds_enabled:
            allowed_origins = [origin for origin in settings.cors_origin_list if origin.startswith(("http://", "https://"))]
            frame_ancestors = list(dict.fromkeys(["'self'", *allowed_origins]))
            response.headers["Content-Security-Policy"] = "; ".join([
                "default-src 'self'",
                "script-src 'self'",
                "style-src 'self' 'unsafe-inline'",
                "img-src 'self' data: blob: https:",
                "font-src 'self' data: https:",
                "connect-src 'self' https:",
                "worker-src 'self' blob:",
                "object-src 'none'",
                "base-uri 'self'",
                "form-action 'self'",
                "frame-ancestors " + " ".join(frame_ancestors),
            ])
            if "X-Frame-Options" in response.headers:
                del response.headers["X-Frame-Options"]
        else:
            response.headers["Content-Security-Policy"] = "frame-ancestors 'self'"
            response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
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


@app.get("/public/deployment-status")
def public_deployment_status():
    return build_public_deployment_status()


@app.get("/public/deployment-receipt")
def public_deployment_receipt():
    return build_public_deployment_receipt()


@app.get("/public/release-gate")
def public_release_gate(
    plugin_version: str | None = Query(default=None),
    expected_commit: str | None = Query(default=None),
    expected_release_id: str | None = Query(default=None),
):
    return build_release_gate(
        plugin_version=plugin_version,
        expected_commit=expected_commit,
        expected_release_id=expected_release_id,
    )


@app.get("/public/runtime-health")
def public_runtime_health(settings: Settings = Depends(get_settings)):
    return build_runtime_health(settings)


@app.get("/public/runtime-recovery")
def public_runtime_recovery(settings: Settings = Depends(get_settings)):
    return build_runtime_recovery_contract(settings)


@app.get("/public/maps/interaction")
def public_map_interaction():
    return build_public_map_interaction_contract()


@app.get("/public/data-truth")
def public_data_truth_endpoint(country: str | None = Query(default=None), settings: Settings = Depends(get_settings)):
    try:
        return build_public_data_truth(settings, country_code=country)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Country not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/public/data-truth/countries")
def public_data_truth_countries_endpoint(settings: Settings = Depends(get_settings)):
    return build_public_data_truth_countries(settings)


@app.get("/public/data-truth/coverage-matrix")
def public_data_truth_coverage_matrix_endpoint(
    countries: str = Query(default=""), region: str = Query(default=""), source: str = Query(default=""),
    state: str = Query(default=""), limit: int = Query(default=24, ge=1, le=60), offset: int = Query(default=0, ge=0),
    settings: Settings = Depends(get_settings),
):
    country_codes = [item.strip().upper() for item in countries.split(",") if item.strip()] or None
    return build_public_coverage_matrix(settings, countries=country_codes, region=region, source_id=source, state=state, limit=limit, offset=offset)


@app.get("/public/data-truth/country/{country_code}")
def public_country_data_truth_endpoint(country_code: str, settings: Settings = Depends(get_settings)):
    try:
        return build_public_country_data_truth(settings, country_code)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Country not found.") from exc


@app.get("/public/data-truth/country/{country_code}/sources")
def public_country_source_truth_endpoint(country_code: str, settings: Settings = Depends(get_settings)):
    try:
        return build_public_country_source_truth(settings, country_code)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Country not found.") from exc


@app.get("/public/data-truth/country/{country_code}/indicators")
def public_country_indicator_truth_endpoint(country_code: str, settings: Settings = Depends(get_settings)):
    try:
        return build_public_country_indicator_truth(settings, country_code)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Country not found.") from exc


@app.get("/public/data-truth/control-plane")
def public_data_truth_control_plane_endpoint(settings: Settings = Depends(get_settings)):
    return build_public_control_plane(settings)


@app.get("/public/data-truth/control-plane/sources")
def public_data_truth_control_plane_sources_endpoint(settings: Settings = Depends(get_settings)):
    return build_public_control_plane_sources(settings)


@app.get("/public/data-truth/control-plane/source/{feed_id}")
def public_data_truth_control_plane_source_endpoint(feed_id: str, settings: Settings = Depends(get_settings)):
    try:
        return build_public_control_plane_source(settings, feed_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Data source not found.") from exc


@app.get("/public/data-truth/control-plane/history")
def public_data_truth_control_plane_history_endpoint(
    source: str | None = Query(default=None), limit: int = Query(default=100, ge=1, le=500),
    settings: Settings = Depends(get_settings),
):
    try:
        return build_public_control_plane_history(settings, source, limit)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Data source not found.") from exc


@app.get("/public/data-truth/control-plane/schema-drift")
def public_data_truth_control_plane_schema_drift_endpoint(settings: Settings = Depends(get_settings)):
    return build_public_control_plane_schema_drift(settings)


@app.get("/public/data-truth/control-plane/outages")
def public_data_truth_control_plane_outages_endpoint(settings: Settings = Depends(get_settings)):
    return build_public_control_plane_outages(settings)


@app.get("/public/data-truth/control-plane/coverage")
def public_data_truth_control_plane_coverage_endpoint(
    countries: str = Query(default=""), settings: Settings = Depends(get_settings),
):
    country_codes = [item.strip().upper() for item in countries.split(",") if item.strip()] or None
    return build_public_control_plane_coverage(settings, country_codes)


@app.get("/public/data-truth/control-plane/workspaces")
def public_data_truth_control_plane_workspaces_endpoint(
    country: str = Query(default="KEN"), settings: Settings = Depends(get_settings),
):
    try:
        return build_public_control_plane_workspaces(settings, country)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Country not found.") from exc


@app.get("/public/data-truth/control-plane/export")
def public_data_truth_control_plane_export_endpoint(
    countries: str = Query(default=""), country: str = Query(default="KEN"), settings: Settings = Depends(get_settings),
):
    country_codes = [item.strip().upper() for item in countries.split(",") if item.strip()] or None
    try:
        return build_public_control_plane_export(settings, country_codes, country)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Country or source not found.") from exc


@app.get("/public/data-truth/{feed_id}")
def public_data_truth_source_endpoint(feed_id: str, settings: Settings = Depends(get_settings)):
    try:
        return build_public_data_truth_source(settings, feed_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Data source not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/public/workspace-evidence")
def public_workspace_evidence_endpoint():
    return build_workspace_evidence_overview()


@app.get("/public/workspace-evidence/readiness")
def public_workspace_evidence_readiness_endpoint():
    return build_workspace_evidence_readiness()


@app.get("/public/workspace-evidence/country/{country_code}")
def public_workspace_evidence_country_endpoint(country_code: str):
    try:
        return build_canonical_country_observations(country_code)
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=404, detail="Country not found.") from exc


@app.get("/public/workspace-evidence/country/{country_code}/indicator/{indicator_id}")
def public_workspace_evidence_indicator_endpoint(country_code: str, indicator_id: str):
    try:
        return build_canonical_country_indicator(country_code, indicator_id)
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=404, detail="Country or indicator not found.") from exc


@app.get("/public/record-truth/country/{country_code}")
def public_country_record_truth_endpoint(country_code: str, settings: Settings = Depends(get_settings)):
    try:
        return build_public_country_record_truth(settings, country_code)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Country not found.") from exc


@app.get("/public/record-truth/indicator/{country_code}/{indicator_id}")
def public_indicator_record_truth_endpoint(country_code: str, indicator_id: str, settings: Settings = Depends(get_settings)):
    try:
        return build_public_indicator_record_truth(settings, country_code, indicator_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Country or indicator not found.") from exc


@app.get("/public/record-truth/map-layer/{layer_id}")
def public_map_layer_truth_endpoint(layer_id: str, date: str | None = Query(default=None), settings: Settings = Depends(get_settings)):
    try:
        return build_public_map_layer_truth(settings, layer_id, date=date)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Map layer not found.") from exc


@app.post("/public/record-truth/resolve")
def public_normalized_record_truth_endpoint(record: dict[str, Any] = Body(...), settings: Settings = Depends(get_settings)):
    return build_public_normalized_record_truth(settings, record)


@app.get("/public/record-truth/manifest")
def public_record_truth_manifest_endpoint(country: str = Query(default="KEN"), settings: Settings = Depends(get_settings)):
    try:
        return build_public_record_truth_manifest(settings, country)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Country not found.") from exc


@app.get("/public/browser-reliability")
def public_browser_reliability_endpoint():
    try:
        return build_public_browser_reliability_contract()
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/public/performance-offline")
def public_performance_offline_endpoint():
    try:
        return build_public_performance_offline_contract()
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/public/bootstrap-recovery")
def public_bootstrap_recovery_endpoint():
    try:
        return build_public_bootstrap_recovery_contract()
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/public/mutation-observer-recovery")
def public_mutation_observer_recovery_endpoint():
    try:
        return build_public_mutation_observer_recovery_contract()
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/public/embed-isolation")
def public_embed_isolation_endpoint():
    try:
        return build_public_embed_isolation_contract()
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/public/startup-stability")
def public_startup_stability_endpoint():
    try:
        return build_public_startup_stability_contract()
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/public/workspaces/unified-state")
def public_unified_analytical_state_endpoint(settings: Settings = Depends(get_settings)):
    return build_public_unified_analytical_state(settings)


@app.post("/public/workspaces/unified-state/normalize")
def public_normalize_analytical_state_endpoint(
    state: dict[str, Any] = Body(default={}), settings: Settings = Depends(get_settings),
):
    return build_public_normalize_analytical_state(settings, state)


@app.post("/public/workspaces/unified-state/deep-link")
def public_analytical_deep_link_endpoint(
    state: dict[str, Any] = Body(default={}), target: str | None = Query(default=None),
    settings: Settings = Depends(get_settings),
):
    try:
        return build_public_analytical_deep_link(settings, state, target)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Analytical handoff target not found.") from exc


@app.post("/public/workspaces/unified-state/handoff/{target}")
def public_analytical_handoff_endpoint(
    target: str, state: dict[str, Any] = Body(default={}), settings: Settings = Depends(get_settings),
):
    try:
        return build_public_analytical_handoff(settings, target, state)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Analytical handoff target not found.") from exc


@app.get("/public/assurance")
def public_assurance_endpoint(settings: Settings = Depends(get_settings)):
    return build_public_assurance(settings)


@app.post("/public/assurance/comparison")
def public_comparison_assurance_endpoint(
    request: dict[str, Any] = Body(default={}), settings: Settings = Depends(get_settings),
):
    return build_public_comparison_assurance(settings, request)


@app.post("/public/assurance/scenario")
def public_scenario_assurance_endpoint(
    request: dict[str, Any] = Body(default={}), settings: Settings = Depends(get_settings),
):
    try:
        return build_public_scenario_assurance(settings, request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/public/assurance/model-review")
def public_model_assurance_review_endpoint(
    card: dict[str, Any] = Body(default={}), settings: Settings = Depends(get_settings),
):
    return build_public_model_assurance_review(settings, card)


@app.get("/public/assurance/model-cards")
def public_assurance_model_cards_endpoint(settings: Settings = Depends(get_settings)):
    return build_public_assurance_model_cards(settings)


@app.post("/public/assurance/package")
def public_assurance_package_endpoint(
    request: dict[str, Any] = Body(default={}), settings: Settings = Depends(get_settings),
):
    try:
        return build_public_assurance_package(settings, request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/public/research-integration")
def public_research_integration_endpoint(settings: Settings = Depends(get_settings)):
    return build_public_research_integration(settings)


@app.post("/public/research-integration/context")
def public_research_context_endpoint(
    request: dict[str, Any] = Body(default={}), settings: Settings = Depends(get_settings),
):
    try:
        return build_public_research_context(settings, request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/public/research-integration/evidence-manifest")
def public_research_manifest_endpoint(
    request: dict[str, Any] = Body(default={}), settings: Settings = Depends(get_settings),
):
    try:
        return build_public_research_manifest(settings, request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/public/research-integration/citations")
def public_research_citations_endpoint(
    request: dict[str, Any] = Body(default={}), settings: Settings = Depends(get_settings),
):
    try:
        return build_public_research_citations(settings, request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/public/research-integration/claim-map")
def public_research_claim_map_endpoint(
    request: dict[str, Any] = Body(default={}), settings: Settings = Depends(get_settings),
):
    try:
        return build_public_research_claim_map(settings, request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/public/research-integration/knowledge-library/discovery")
def public_knowledge_library_discovery_endpoint(
    request: dict[str, Any] = Body(default={}), settings: Settings = Depends(get_settings),
):
    try:
        return build_public_knowledge_library_discovery(settings, request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/public/research-integration/handoff/{target}/preview")
def public_research_handoff_preview_endpoint(
    target: str, request: dict[str, Any] = Body(default={}), settings: Settings = Depends(get_settings),
):
    try:
        return build_public_research_handoff_preview(settings, target, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Research handoff target not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/public/monitoring-operations")
def public_monitoring_operations_endpoint():
    return build_public_monitoring_operations()


@app.post("/public/monitoring-operations/watchlist/preview")
def public_monitoring_watchlist_preview_endpoint(request: dict[str, Any] = Body(default={})):
    try:
        return build_public_watchlist_preview(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/public/monitoring-operations/evaluate")
def public_monitoring_evaluation_endpoint(request: dict[str, Any] = Body(default={})):
    try:
        return build_public_monitoring_evaluation(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/public/monitoring-operations/source-changes")
def public_source_change_monitoring_endpoint(request: dict[str, Any] = Body(default={})):
    try:
        return build_public_source_change_monitoring(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/public/monitoring-operations/modeled-warning/preview")
def public_modeled_warning_preview_endpoint(request: dict[str, Any] = Body(default={})):
    try:
        return build_public_modeled_warning_preview(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/public/monitoring-operations/digest/preview")
def public_monitoring_digest_preview_endpoint(request: dict[str, Any] = Body(default={})):
    try:
        return build_public_monitoring_digest_preview(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/public/monitoring-operations/feed-contract")
def public_monitoring_feed_contract_endpoint():
    return build_public_monitoring_feed_contract()


@app.get("/public/publication-studio")
def public_briefing_publication_studio_endpoint():
    return build_public_briefing_publication_studio()


@app.post("/public/publication-studio/frozen-manifest")
def public_frozen_evidence_manifest_endpoint(request: dict[str, Any] = Body(default={})):
    try:
        return build_public_frozen_evidence_manifest(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/public/publication-studio/briefing/preview")
def public_briefing_preview_endpoint(request: dict[str, Any] = Body(default={})):
    try:
        return build_public_briefing_preview(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/public/publication-studio/story-map/preview")
def public_story_map_preview_endpoint(request: dict[str, Any] = Body(default={})):
    try:
        return build_public_story_map_preview(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/public/publication-studio/readiness")
def public_publication_readiness_endpoint(request: dict[str, Any] = Body(default={})):
    try:
        return build_public_publication_readiness(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/public/publication-studio/correction/preview")
def public_publication_correction_preview_endpoint(request: dict[str, Any] = Body(default={})):
    try:
        return build_public_publication_correction_preview(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/public/publication-studio/package")
def public_publication_package_endpoint(request: dict[str, Any] = Body(default={})):
    try:
        return build_public_publication_package(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/public/institutional-governance")
def public_institutional_governance_endpoint():
    return build_public_institutional_governance()


@app.post("/public/institutional-governance/workspace/preview")
def public_workspace_governance_preview_endpoint(request: dict[str, Any] = Body(default={})):
    try:
        return build_public_workspace_governance_preview(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/public/institutional-governance/review-queue")
def public_review_queue_preview_endpoint(request: dict[str, Any] = Body(default={})):
    try:
        return build_public_review_queue_preview(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/public/institutional-governance/annotation/preview")
def public_annotation_governance_preview_endpoint(request: dict[str, Any] = Body(default={})):
    try:
        return build_public_annotation_governance_preview(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/public/institutional-governance/decision/preview")
def public_review_decision_preview_endpoint(request: dict[str, Any] = Body(default={})):
    try:
        return build_public_review_decision_preview(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/public/institutional-governance/audit/preview")
def public_workspace_audit_preview_endpoint(request: dict[str, Any] = Body(default={})):
    try:
        return build_public_workspace_audit_preview(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/public/institutional-governance/package/export")
def public_workspace_package_export_endpoint(request: dict[str, Any] = Body(default={})):
    try:
        return build_public_workspace_package_export(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/public/institutional-governance/package/import-preview")
def public_workspace_package_import_preview_endpoint(request: dict[str, Any] = Body(default={})):
    try:
        return build_public_workspace_package_import_preview(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/public/v4")
def public_v4():
    return build_public_unified_platform()


@app.get("/public/v4/navigation")
def public_v4_navigation():
    return build_public_unified_navigation()


@app.get("/public/v4/contracts")
def public_v4_contracts():
    return build_public_unified_contracts()


@app.get("/public/v4/readiness")
def public_v4_readiness(settings: Settings = Depends(get_settings)):
    return build_public_v4_readiness(settings)


@app.get("/public/v4/configuration-readiness")
def public_v4_configuration_readiness(settings: Settings = Depends(get_settings)):
    return build_public_v4_configuration_readiness(settings)


@app.get("/public/orbital-earth")
def public_orbital_earth_overview():
    return build_orbital_earth_overview()


@app.get("/public/orbital-earth/catalog")
def public_orbital_earth_catalog():
    return build_orbital_earth_catalog()


@app.get("/public/orbital-earth/state")
def public_orbital_earth_state(
    layer: str = Query(default="true-color"),
    date: str = Query(default=""),
    latitude: float = Query(default=0.0, ge=-90, le=90),
    longitude: float = Query(default=20.0, ge=-180, le=180),
    altitude_km: float = Query(default=1200.0, ge=250, le=35786),
):
    return build_orbital_earth_state(layer, date, latitude, longitude, altitude_km)


@app.get("/public/orbital-earth/export-manifest")
def public_orbital_earth_export_manifest(
    layer: str = Query(default="true-color"),
    date: str = Query(default=""),
    latitude: float = Query(default=0.0, ge=-90, le=90),
    longitude: float = Query(default=20.0, ge=-180, le=180),
    altitude_km: float = Query(default=1200.0, ge=250, le=35786),
):
    return build_orbital_earth_export_manifest(layer, date, latitude, longitude, altitude_km)


@app.get("/public/orbital-earth/readiness")
def public_orbital_earth_readiness():
    return build_orbital_earth_readiness()


@app.get("/public/planetary-intelligence")
def public_planetary_intelligence():
    return build_planetary_overview()

@app.get("/public/planetary-intelligence/catalog")
def public_planetary_catalog():
    return build_planetary_catalog()

@app.get("/public/planetary-intelligence/body/{body_id}")
def public_planetary_body(body_id: str):
    return build_planetary_body(body_id)

@app.get("/public/planetary-intelligence/state")
def public_planetary_state(body: str = Query(default="moon"), product: str = Query(default=""), latitude: float = Query(default=0.0, ge=-90, le=90), longitude: float = Query(default=0.0, ge=-180, le=180), zoom: float = Query(default=2.0, ge=1, le=12)):
    return build_planetary_state(body, product, latitude, longitude, zoom)

@app.get("/public/planetary-intelligence/export-manifest")
def public_planetary_manifest(body: str = Query(default="moon"), product: str = Query(default=""), latitude: float = Query(default=0.0, ge=-90, le=90), longitude: float = Query(default=0.0, ge=-180, le=180), zoom: float = Query(default=2.0, ge=1, le=12)):
    return build_planetary_export_manifest(body, product, latitude, longitude, zoom)

@app.get("/public/planetary-intelligence/readiness")
def public_planetary_readiness():
    return build_planetary_readiness()

@app.get("/public/astronomical-observation")
def public_astronomical_observation():
    return build_astronomical_overview()

@app.get("/public/astronomical-observation/catalog")
def public_astronomical_catalog():
    return build_astronomical_catalog()

@app.get("/public/astronomical-observation/target/{target_id}")
def public_astronomical_target(target_id: str):
    return build_astronomical_target(target_id)

@app.get("/public/astronomical-observation/state")
def public_astronomical_state(target: str = Query(default="m31"), survey: str = Query(default="dss-optical"), ra: float | None = Query(default=None, ge=0, le=360), dec: float | None = Query(default=None, ge=-90, le=90), field: float = Query(default=0.25, ge=0.01, le=10)):
    return build_astronomical_state(target, survey, ra, dec, field)

@app.get("/public/astronomical-observation/export-manifest")
def public_astronomical_manifest(target: str = Query(default="m31"), survey: str = Query(default="dss-optical"), ra: float | None = Query(default=None, ge=0, le=360), dec: float | None = Query(default=None, ge=-90, le=90), field: float = Query(default=0.25, ge=0.01, le=10)):
    return build_astronomical_export_manifest(target, survey, ra, dec, field)

@app.get("/public/astronomical-observation/readiness")
def public_astronomical_readiness():
    return build_astronomical_readiness()


@app.get("/public/seti-technosignatures")
def public_seti_overview():
    return build_seti_overview()

@app.get("/public/seti-technosignatures/catalog")
def public_seti_catalog():
    return build_seti_catalog()

@app.get("/public/seti-technosignatures/state")
def public_seti_state(source: str = Query(default="breakthrough-listen-open-data"), indicator_type: str = Query(default="observation-metadata"), target: str = Query(default=""), telescope: str = Query(default=""), frequency_mhz: float | None = Query(default=None, ge=0), ra_deg: float | None = Query(default=None, ge=0, le=360), dec_deg: float | None = Query(default=None, ge=-90, le=90)):
    try:
        return build_seti_state(source, indicator_type, target, telescope, frequency_mhz, ra_deg, dec_deg)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.post("/public/seti-technosignatures/observation/normalize")
def public_seti_observation_normalize(request: dict[str, Any] = Body(default={})):
    try:
        return build_seti_normalize_observation(request)
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.post("/public/seti-technosignatures/signal/normalize")
def public_seti_signal_normalize(request: dict[str, Any] = Body(default={})):
    try:
        return build_seti_normalize_signal(request)
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.post("/public/seti-technosignatures/candidate/normalize")
def public_seti_candidate_normalize(request: dict[str, Any] = Body(default={})):
    try:
        return build_seti_normalize_candidate(request)
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.get("/public/seti-technosignatures/export-manifest")
def public_seti_manifest(source: str = Query(default="breakthrough-listen-open-data"), indicator_type: str = Query(default="observation-metadata"), target: str = Query(default=""), telescope: str = Query(default=""), frequency_mhz: float | None = Query(default=None, ge=0), ra_deg: float | None = Query(default=None, ge=0, le=360), dec_deg: float | None = Query(default=None, ge=-90, le=90)):
    try:
        return build_seti_export_manifest(source, indicator_type, target, telescope, frequency_mhz, ra_deg, dec_deg)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.get("/public/seti-technosignatures/readiness")
def public_seti_readiness():
    return build_seti_readiness()

@app.get("/public/exoplanet-habitability")
def public_exoplanet_habitability_overview():
    return build_exoplanet_habitability_overview()

@app.get("/public/exoplanet-habitability/catalog")
def public_exoplanet_habitability_catalog():
    return build_exoplanet_habitability_catalog()

@app.get("/public/exoplanet-habitability/state")
def public_exoplanet_habitability_state(source: str = Query(default="nasa-exoplanet-archive-systems"), indicator_type: str = Query(default="planetary-system"), target: str = Query(default=""), spectrum_type: str = Query(default=""), facility: str = Query(default=""), wavelength_um: float | None = Query(default=None, gt=0)):
    try:
        return build_exoplanet_habitability_state(source, indicator_type, target, spectrum_type, facility, wavelength_um)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.post("/public/exoplanet-habitability/planet/normalize")
def public_exoplanet_habitability_planet_normalize(request: dict[str, Any] = Body(default={})):
    try:
        return build_exoplanet_habitability_normalize_planet(request)
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.post("/public/exoplanet-habitability/spectrum/normalize")
def public_exoplanet_habitability_spectrum_normalize(request: dict[str, Any] = Body(default={})):
    try:
        return build_exoplanet_habitability_normalize_spectrum(request)
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.post("/public/exoplanet-habitability/biosignature/normalize")
def public_exoplanet_habitability_biosignature_normalize(request: dict[str, Any] = Body(default={})):
    try:
        return build_exoplanet_habitability_normalize_biosignature(request)
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.get("/public/exoplanet-habitability/export-manifest")
def public_exoplanet_habitability_manifest(source: str = Query(default="nasa-exoplanet-archive-systems"), indicator_type: str = Query(default="planetary-system"), target: str = Query(default=""), spectrum_type: str = Query(default=""), facility: str = Query(default=""), wavelength_um: float | None = Query(default=None, gt=0)):
    try:
        return build_exoplanet_habitability_export_manifest(source, indicator_type, target, spectrum_type, facility, wavelength_um)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.get("/public/exoplanet-habitability/readiness")
def public_exoplanet_habitability_readiness():
    return build_exoplanet_habitability_readiness()

@app.get("/public/solar-system-navigation")
def public_solar_system_navigation():
    return build_solar_system_overview()

@app.get("/public/solar-system-navigation/catalog")
def public_solar_system_catalog():
    return build_solar_system_catalog()

@app.get("/public/solar-system-navigation/body/{body_id}")
def public_solar_system_body(body_id: str):
    return build_solar_system_body(body_id)

@app.get("/public/solar-system-navigation/mission/{mission_id}")
def public_solar_system_mission(mission_id: str):
    return build_solar_system_mission(mission_id)

@app.get("/public/solar-system-navigation/state")
def public_solar_system_state(
    body: str = Query(default="earth"),
    mission: str = Query(default=""),
    epoch: str = Query(default=""),
    frame: str = Query(default="J2000"),
    observer: str = Query(default="solar-system-barycenter"),
):
    try:
        return build_solar_system_state(body, mission, epoch, frame, observer)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.post("/public/solar-system-navigation/ephemeris/normalize")
def public_solar_system_normalize_ephemeris(request: dict[str, Any] = Body(default={})):
    try:
        return build_solar_system_normalize_ephemeris(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.get("/public/solar-system-navigation/export-manifest")
def public_solar_system_manifest(
    body: str = Query(default="earth"),
    mission: str = Query(default=""),
    epoch: str = Query(default=""),
    frame: str = Query(default="J2000"),
    observer: str = Query(default="solar-system-barycenter"),
):
    try:
        return build_solar_system_export_manifest(body, mission, epoch, frame, observer)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.get("/public/solar-system-navigation/readiness")
def public_solar_system_readiness():
    return build_solar_system_readiness()


@app.get("/public/space-observation/providers")
def public_space_observation_providers():
    return build_live_space_provider_catalog(get_settings())

@app.get("/public/space-observation/readiness")
def public_space_observation_readiness():
    return build_live_space_readiness(get_settings())

@app.post("/public/space-observation/search")
def public_space_observation_search(request: dict[str, Any] = Body(default={})):
    try:
        return build_live_space_search(request, get_settings())
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/public/ocean-observation")
def public_ocean_observation_overview():
    return build_ocean_observation_overview()

@app.get("/public/ocean-observation/catalog")
def public_ocean_observation_catalog():
    return build_ocean_observation_catalog()

@app.get("/public/ocean-observation/manifest")
def public_ocean_observation_manifest():
    return build_ocean_observation_manifest()

@app.get("/public/ocean-observation/readiness")
def public_ocean_observation_readiness():
    return build_ocean_observation_readiness()


@app.get("/public/ocean-intelligence")
def public_ocean_surface_overview():
    return build_ocean_surface_overview()

@app.get("/public/ocean-intelligence/catalog")
def public_ocean_surface_catalog():
    return build_ocean_surface_catalog()

@app.get("/public/ocean-intelligence/source/{source_id}")
def public_ocean_surface_source(source_id: str):
    return build_ocean_surface_source(source_id)

@app.get("/public/ocean-intelligence/state")
def public_ocean_surface_state(variable: str = Query(default="sea-surface-temperature"), source: str = Query(default=""), latitude: float = Query(default=0.0), longitude: float = Query(default=0.0), date: str = Query(default="")):
    try: return build_ocean_surface_state(variable, source, latitude, longitude, date)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.post("/public/ocean-intelligence/observation/normalize")
def public_ocean_surface_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_ocean_surface_normalize_observation(request)
    except (ValueError, TypeError) as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.get("/public/ocean-intelligence/export-manifest")
def public_ocean_surface_manifest(variable: str = Query(default="sea-surface-temperature"), source: str = Query(default=""), latitude: float = Query(default=0.0), longitude: float = Query(default=0.0), date: str = Query(default="")):
    try: return build_ocean_surface_export_manifest(variable, source, latitude, longitude, date)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.get("/public/ocean-intelligence/readiness")
def public_ocean_surface_readiness():
    return build_ocean_surface_readiness()

@app.get("/public/water-column")
def public_water_column_overview():
    return build_water_column_overview()

@app.get("/public/water-column/catalog")
def public_water_column_catalog():
    return build_water_column_catalog()

@app.get("/public/water-column/state")
def public_water_column_state(variable: str = Query(default="temperature"), source: str = Query(default=""), latitude: float = Query(default=0.0), longitude: float = Query(default=0.0), date: str = Query(default=""), depth_m: float = Query(default=0.0)):
    try: return build_water_column_state(variable, source, latitude, longitude, date, depth_m)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.post("/public/water-column/profile/normalize")
def public_water_column_profile_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_water_column_normalize_profile(request)
    except (ValueError, TypeError) as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.post("/public/water-column/depth/resolve")
def public_water_column_depth_resolve(request: dict[str, Any] = Body(default={})):
    try: return build_water_column_resolve_depth(request)
    except (ValueError, TypeError) as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.get("/public/water-column/export-manifest")
def public_water_column_manifest(variable: str = Query(default="temperature"), source: str = Query(default=""), latitude: float = Query(default=0.0), longitude: float = Query(default=0.0), date: str = Query(default=""), depth_m: float = Query(default=0.0)):
    try: return build_water_column_export_manifest(variable, source, latitude, longitude, date, depth_m)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.get("/public/water-column/readiness")
def public_water_column_readiness():
    return build_water_column_readiness()

@app.get("/public/seafloor-intelligence")
def public_seafloor_overview():
    return build_seafloor_overview()

@app.get("/public/seafloor-intelligence/catalog")
def public_seafloor_catalog():
    return build_seafloor_catalog()

@app.get("/public/seafloor-intelligence/state")
def public_seafloor_state(layer: str = Query(default="bathymetric-elevation"), source: str = Query(default=""), latitude: float = Query(default=0.0), longitude: float = Query(default=0.0), date: str = Query(default="")):
    try: return build_seafloor_state(layer, source, latitude, longitude, date)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.post("/public/seafloor-intelligence/sample/normalize")
def public_seafloor_sample_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_seafloor_normalize_sample(request)
    except (ValueError, TypeError) as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.post("/public/seafloor-intelligence/footprint/normalize")
def public_seafloor_footprint_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_seafloor_normalize_footprint(request)
    except (ValueError, TypeError) as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.get("/public/seafloor-intelligence/export-manifest")
def public_seafloor_manifest(layer: str = Query(default="bathymetric-elevation"), source: str = Query(default=""), latitude: float = Query(default=0.0), longitude: float = Query(default=0.0), date: str = Query(default="")):
    try: return build_seafloor_export_manifest(layer, source, latitude, longitude, date)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.get("/public/seafloor-intelligence/readiness")
def public_seafloor_readiness():
    return build_seafloor_readiness()

@app.get("/public/underwater-observation")
def public_underwater_overview():
    return build_underwater_overview()

@app.get("/public/underwater-observation/catalog")
def public_underwater_catalog():
    return build_underwater_catalog()

@app.get("/public/underwater-observation/state")
def public_underwater_state(source: str = Query(default="onc-oceans-3"), media_type: str = Query(default="still-image"), latitude: float = Query(default=0.0), longitude: float = Query(default=0.0), date: str = Query(default=""), depth_m: float | None = Query(default=None), query: str = Query(default="")):
    try: return build_underwater_state(source, media_type, latitude, longitude, date, depth_m, query)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.post("/public/underwater-observation/media/normalize")
def public_underwater_media_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_underwater_normalize_media(request)
    except (ValueError, TypeError) as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.post("/public/underwater-observation/annotation/normalize")
def public_underwater_annotation_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_underwater_normalize_annotation(request)
    except (ValueError, TypeError) as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.get("/public/underwater-observation/export-manifest")
def public_underwater_manifest(source: str = Query(default="onc-oceans-3"), media_type: str = Query(default="still-image"), latitude: float = Query(default=0.0), longitude: float = Query(default=0.0), date: str = Query(default=""), depth_m: float | None = Query(default=None), query: str = Query(default="")):
    try: return build_underwater_export_manifest(source, media_type, latitude, longitude, date, depth_m, query)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.get("/public/underwater-observation/readiness")
def public_underwater_readiness():
    return build_underwater_readiness()

@app.get("/public/underwater-media/providers")
def public_underwater_media_providers():
    return build_live_underwater_provider_catalog(get_settings())

@app.get("/public/underwater-media/readiness")
def public_underwater_media_readiness():
    return build_live_underwater_readiness(get_settings())

@app.post("/public/underwater-media/search")
def public_underwater_media_search(request: dict[str, Any] = Body(default={})):
    try:
        return build_live_underwater_search(request, get_settings())
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.get("/public/underwater-media/onc/file")
def public_underwater_media_onc_file(filename: str = Query(..., min_length=1, max_length=500)):
    try:
        body, content_type = build_live_underwater_onc_image(filename, get_settings())
        return Response(content=body, media_type=content_type, headers={"Cache-Control": "public, max-age=300", "X-Content-Type-Options": "nosniff"})
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

@app.get("/public/marine-biodiversity")
def public_marine_biodiversity_overview():
    return build_marine_biodiversity_overview()

@app.get("/public/marine-biodiversity/catalog")
def public_marine_biodiversity_catalog():
    return build_marine_biodiversity_catalog()

@app.get("/public/marine-biodiversity/state")
def public_marine_biodiversity_state(source: str = Query(default="obis"), evidence_class: str = Query(default="occurrence-record"), scientific_name: str = Query(default=""), latitude: float | None = Query(default=None), longitude: float | None = Query(default=None), depth_m: float | None = Query(default=None), date: str = Query(default="")):
    try: return build_marine_biodiversity_state(source, evidence_class, scientific_name, latitude, longitude, depth_m, date)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.post("/public/marine-biodiversity/occurrence/normalize")
def public_marine_biodiversity_occurrence_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_marine_biodiversity_normalize_occurrence(request)
    except (ValueError, TypeError) as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.post("/public/marine-biodiversity/taxonomy/normalize")
def public_marine_biodiversity_taxonomy_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_marine_biodiversity_normalize_taxonomy(request)
    except (ValueError, TypeError) as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.post("/public/marine-biodiversity/visual/normalize")
def public_marine_biodiversity_visual_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_marine_biodiversity_normalize_visual(request)
    except (ValueError, TypeError) as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.post("/public/marine-biodiversity/acoustic/normalize")
def public_marine_biodiversity_acoustic_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_marine_biodiversity_normalize_acoustic(request)
    except (ValueError, TypeError) as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.get("/public/marine-biodiversity/export-manifest")
def public_marine_biodiversity_manifest(source: str = Query(default="obis"), evidence_class: str = Query(default="occurrence-record"), scientific_name: str = Query(default=""), latitude: float | None = Query(default=None), longitude: float | None = Query(default=None), depth_m: float | None = Query(default=None), date: str = Query(default="")):
    try: return build_marine_biodiversity_export_manifest(source, evidence_class, scientific_name, latitude, longitude, depth_m, date)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.get("/public/marine-biodiversity/readiness")
def public_marine_biodiversity_readiness():
    return build_marine_biodiversity_readiness()

@app.get("/public/ocean-missions")
def public_ocean_missions_overview():
    return build_ocean_missions_overview()

@app.get("/public/ocean-missions/catalog")
def public_ocean_missions_catalog():
    return build_ocean_missions_catalog()

@app.get("/public/ocean-missions/state")
def public_ocean_missions_state(source: str = Query(default="argo"), platform_type: str = Query(default="float"), platform_id: str = Query(default=""), latitude: float | None = Query(default=None), longitude: float | None = Query(default=None), date: str = Query(default="")):
    try: return build_ocean_missions_state(source, platform_type, platform_id, latitude, longitude, date)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.post("/public/ocean-missions/platform/normalize")
def public_ocean_missions_platform_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_ocean_missions_normalize_platform(request)
    except (ValueError, TypeError) as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.post("/public/ocean-missions/mission/normalize")
def public_ocean_missions_mission_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_ocean_missions_normalize_mission(request)
    except (ValueError, TypeError) as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.post("/public/ocean-missions/track/normalize")
def public_ocean_missions_track_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_ocean_missions_normalize_track(request)
    except (ValueError, TypeError) as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.get("/public/ocean-missions/export-manifest")
def public_ocean_missions_manifest(source: str = Query(default="argo"), platform_type: str = Query(default="float"), platform_id: str = Query(default=""), latitude: float | None = Query(default=None), longitude: float | None = Query(default=None), date: str = Query(default="")):
    try: return build_ocean_missions_export_manifest(source, platform_type, platform_id, latitude, longitude, date)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.get("/public/ocean-missions/readiness")
def public_ocean_missions_readiness():
    return build_ocean_missions_readiness()

@app.get("/public/ocean-events")
def public_ocean_events_overview():
    return build_ocean_events_overview()

@app.get("/public/ocean-events/catalog")
def public_ocean_events_catalog():
    return build_ocean_events_catalog()

@app.get("/public/ocean-events/state")
def public_ocean_events_state(source: str = Query(default="noaa-coral-reef-watch"), hazard_type: str = Query(default="marine-heatwave"), latitude: float | None = Query(default=None), longitude: float | None = Query(default=None), date: str = Query(default="")):
    try: return build_ocean_events_state(source, hazard_type, latitude, longitude, date)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.post("/public/ocean-events/condition/normalize")
def public_ocean_events_condition_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_ocean_events_normalize_condition(request)
    except (ValueError, TypeError) as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.post("/public/ocean-events/threshold/preview")
def public_ocean_events_threshold_preview(request: dict[str, Any] = Body(default={})):
    try: return build_ocean_events_threshold_preview(request)
    except (ValueError, TypeError) as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.post("/public/ocean-events/event/normalize")
def public_ocean_events_event_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_ocean_events_normalize_event(request)
    except (ValueError, TypeError) as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.get("/public/ocean-events/export-manifest")
def public_ocean_events_manifest(source: str = Query(default="noaa-coral-reef-watch"), hazard_type: str = Query(default="marine-heatwave"), latitude: float | None = Query(default=None), longitude: float | None = Query(default=None), date: str = Query(default="")):
    try: return build_ocean_events_export_manifest(source, hazard_type, latitude, longitude, date)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.get("/public/ocean-events/readiness")
def public_ocean_events_readiness():
    return build_ocean_events_readiness()

@app.get("/public/marine-human-activity")
def public_marine_human_activity_overview():
    return build_marine_human_activity_overview()

@app.get("/public/marine-human-activity/catalog")
def public_marine_human_activity_catalog():
    return build_marine_human_activity_catalog()

@app.get("/public/marine-human-activity/state")
def public_marine_human_activity_state(source: str = Query(default="noaa-marine-cadastre-ais"), activity_type: str = Query(default="vessel-traffic"), latitude: float | None = Query(default=None), longitude: float | None = Query(default=None), date: str = Query(default="")):
    try: return build_marine_human_activity_state(source, activity_type, latitude, longitude, date)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.post("/public/marine-human-activity/activity/normalize")
def public_marine_human_activity_activity_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_marine_human_activity_normalize_activity(request)
    except (ValueError, TypeError) as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.post("/public/marine-human-activity/protected-area/normalize")
def public_marine_human_activity_protected_area_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_marine_human_activity_normalize_protected_area(request)
    except (ValueError, TypeError) as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.post("/public/marine-human-activity/overlap/preview")
def public_marine_human_activity_overlap_preview(request: dict[str, Any] = Body(default={})):
    try: return build_marine_human_activity_overlap_preview(request)
    except (ValueError, TypeError) as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.get("/public/marine-human-activity/export-manifest")
def public_marine_human_activity_manifest(source: str = Query(default="noaa-marine-cadastre-ais"), activity_type: str = Query(default="vessel-traffic"), latitude: float | None = Query(default=None), longitude: float | None = Query(default=None), date: str = Query(default="")):
    try: return build_marine_human_activity_export_manifest(source, activity_type, latitude, longitude, date)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.get("/public/marine-human-activity/readiness")
def public_marine_human_activity_readiness():
    return build_marine_human_activity_readiness()

@app.get("/public/marine-pollution")
def public_marine_pollution_overview():
    return build_marine_pollution_overview()

@app.get("/public/marine-pollution/catalog")
def public_marine_pollution_catalog():
    return build_marine_pollution_catalog()

@app.get("/public/marine-pollution/state")
def public_marine_pollution_state(source: str = Query(default="noaa-ncei-marine-microplastics"), indicator_type: str = Query(default="microplastics"), latitude: float | None = Query(default=None), longitude: float | None = Query(default=None), date: str = Query(default="")):
    try: return build_marine_pollution_state(source, indicator_type, latitude, longitude, date)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.post("/public/marine-pollution/measurement/normalize")
def public_marine_pollution_measurement_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_marine_pollution_normalize_measurement(request)
    except (ValueError, TypeError, KeyError) as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.post("/public/marine-pollution/debris/normalize")
def public_marine_pollution_debris_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_marine_pollution_normalize_debris(request)
    except (ValueError, TypeError) as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.post("/public/marine-pollution/threshold/preview")
def public_marine_pollution_threshold_preview(request: dict[str, Any] = Body(default={})):
    try: return build_marine_pollution_threshold_preview(request)
    except (ValueError, TypeError, KeyError) as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.get("/public/marine-pollution/export-manifest")
def public_marine_pollution_manifest(source: str = Query(default="noaa-ncei-marine-microplastics"), indicator_type: str = Query(default="microplastics"), latitude: float | None = Query(default=None), longitude: float | None = Query(default=None), date: str = Query(default="")):
    try: return build_marine_pollution_export_manifest(source, indicator_type, latitude, longitude, date)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.get("/public/marine-pollution/readiness")
def public_marine_pollution_readiness():
    return build_marine_pollution_readiness()

@app.get("/public/coastal-change")
def public_coastal_change_overview():
    return build_coastal_change_overview()

@app.get("/public/coastal-change/catalog")
def public_coastal_change_catalog():
    return build_coastal_change_catalog()

@app.get("/public/coastal-change/state")
def public_coastal_change_state(source: str = Query(default="noaa-coops"), indicator_type: str = Query(default="observed-water-level"), latitude: float | None = Query(default=None), longitude: float | None = Query(default=None), date: str = Query(default="")):
    try: return build_coastal_change_state(source, indicator_type, latitude, longitude, date)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.post("/public/coastal-change/water-level/normalize")
def public_coastal_change_water_level_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_coastal_change_normalize_water_level(request)
    except (ValueError, TypeError, KeyError) as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.post("/public/coastal-change/shoreline/normalize")
def public_coastal_change_shoreline_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_coastal_change_normalize_shoreline(request)
    except (ValueError, TypeError, KeyError) as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.post("/public/coastal-change/habitat/normalize")
def public_coastal_change_habitat_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_coastal_change_normalize_habitat(request)
    except (ValueError, TypeError, KeyError) as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.post("/public/coastal-change/scenario/preview")
def public_coastal_change_scenario_preview(request: dict[str, Any] = Body(default={})):
    try: return build_coastal_change_scenario_preview(request)
    except (ValueError, TypeError, KeyError) as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.get("/public/coastal-change/export-manifest")
def public_coastal_change_manifest(source: str = Query(default="noaa-coops"), indicator_type: str = Query(default="observed-water-level"), latitude: float | None = Query(default=None), longitude: float | None = Query(default=None), date: str = Query(default="")):
    try: return build_coastal_change_export_manifest(source, indicator_type, latitude, longitude, date)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.get("/public/coastal-change/readiness")
def public_coastal_change_readiness():
    return build_coastal_change_readiness()

@app.get("/public/ocean-governance")
def public_ocean_governance_overview(): return build_ocean_governance_overview()

@app.get("/public/ocean-governance/catalog")
def public_ocean_governance_catalog(): return build_ocean_governance_catalog()

@app.get("/public/ocean-governance/state")
def public_ocean_governance_state(source: str = Query(default="marine-regions-vliz"), zone_type: str = Query(default="exclusive-economic-zone"), latitude: float | None = Query(default=None), longitude: float | None = Query(default=None), date: str = Query(default="")):
    try: return build_ocean_governance_state(source,zone_type,latitude,longitude,date)
    except ValueError as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc

@app.post("/public/ocean-governance/zone/normalize")
def public_ocean_governance_zone_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_ocean_governance_normalize_zone(request)
    except (ValueError,TypeError,KeyError) as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc

@app.post("/public/ocean-governance/management-area/normalize")
def public_ocean_governance_management_area_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_ocean_governance_normalize_management_area(request)
    except (ValueError,TypeError,KeyError) as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc

@app.post("/public/ocean-governance/overlap/preview")
def public_ocean_governance_overlap_preview(request: dict[str, Any] = Body(default={})):
    try: return build_ocean_governance_overlap_preview(request)
    except (ValueError,TypeError,KeyError) as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc

@app.get("/public/ocean-governance/export-manifest")
def public_ocean_governance_manifest(source: str = Query(default="marine-regions-vliz"), zone_type: str = Query(default="exclusive-economic-zone"), latitude: float | None = Query(default=None), longitude: float | None = Query(default=None), date: str = Query(default="")):
    try: return build_ocean_governance_export_manifest(source,zone_type,latitude,longitude,date)
    except ValueError as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc

@app.get("/public/ocean-governance/readiness")
def public_ocean_governance_readiness(): return build_ocean_governance_readiness()

@app.get("/public/cryosphere")
def public_cryosphere_overview(): return build_cryosphere_overview()

@app.get("/public/cryosphere/catalog")
def public_cryosphere_catalog(): return build_cryosphere_catalog()

@app.get("/public/cryosphere/state")
def public_cryosphere_state(source: str = Query(default="noaa-nsidc-sea-ice-index"), indicator_type: str = Query(default="sea-ice-extent"), latitude: float | None = Query(default=None), longitude: float | None = Query(default=None), date: str = Query(default="")):
    try: return build_cryosphere_state(source,indicator_type,latitude,longitude,date)
    except ValueError as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc

@app.post("/public/cryosphere/measurement/normalize")
def public_cryosphere_measurement_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_cryosphere_normalize_measurement(request)
    except (ValueError,TypeError,KeyError) as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc

@app.post("/public/cryosphere/feature/normalize")
def public_cryosphere_feature_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_cryosphere_normalize_feature(request)
    except (ValueError,TypeError,KeyError) as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc

@app.post("/public/cryosphere/anomaly/preview")
def public_cryosphere_anomaly_preview(request: dict[str, Any] = Body(default={})):
    try: return build_cryosphere_anomaly_preview(request)
    except (ValueError,TypeError,KeyError) as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc

@app.get("/public/cryosphere/export-manifest")
def public_cryosphere_manifest(source: str = Query(default="noaa-nsidc-sea-ice-index"), indicator_type: str = Query(default="sea-ice-extent"), latitude: float | None = Query(default=None), longitude: float | None = Query(default=None), date: str = Query(default="")):
    try: return build_cryosphere_export_manifest(source,indicator_type,latitude,longitude,date)
    except ValueError as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc

@app.get("/public/cryosphere/readiness")
def public_cryosphere_readiness(): return build_cryosphere_readiness()


@app.get("/public/atmosphere")
def public_atmosphere_overview(): return build_atmosphere_overview()

@app.get("/public/atmosphere/catalog")
def public_atmosphere_catalog(): return build_atmosphere_catalog()

@app.get("/public/atmosphere/state")
def public_atmosphere_state(source: str = Query(default="airnow"), indicator_type: str = Query(default="aqi"), latitude: float | None = Query(default=None), longitude: float | None = Query(default=None), date: str = Query(default="")):
    try: return build_atmosphere_state(source,indicator_type,latitude,longitude,date)
    except ValueError as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc

@app.post("/public/atmosphere/measurement/normalize")
def public_atmosphere_measurement_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_atmosphere_normalize_measurement(request)
    except (ValueError,TypeError,KeyError) as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc

@app.post("/public/atmosphere/forecast/normalize")
def public_atmosphere_forecast_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_atmosphere_normalize_forecast(request)
    except (ValueError,TypeError,KeyError) as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc

@app.post("/public/atmosphere/threshold/preview")
def public_atmosphere_threshold_preview(request: dict[str, Any] = Body(default={})):
    try: return build_atmosphere_threshold_preview(request)
    except (ValueError,TypeError,KeyError) as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc

@app.get("/public/atmosphere/export-manifest")
def public_atmosphere_manifest(source: str = Query(default="airnow"), indicator_type: str = Query(default="aqi"), latitude: float | None = Query(default=None), longitude: float | None = Query(default=None), date: str = Query(default="")):
    try: return build_atmosphere_export_manifest(source,indicator_type,latitude,longitude,date)
    except ValueError as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc

@app.get("/public/atmosphere/readiness")
def public_atmosphere_readiness(): return build_atmosphere_readiness()


@app.get("/public/hydrology")
def public_hydrology_overview(): return build_hydrology_overview()

@app.get("/public/hydrology/catalog")
def public_hydrology_catalog(): return build_hydrology_catalog()

@app.get("/public/hydrology/state")
def public_hydrology_state(source: str = Query(default="usgs-water-data"), indicator_type: str = Query(default="streamflow"), latitude: float | None = Query(default=None), longitude: float | None = Query(default=None), date: str = Query(default="")):
    try: return build_hydrology_state(source,indicator_type,latitude,longitude,date)
    except ValueError as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc

@app.post("/public/hydrology/measurement/normalize")
def public_hydrology_measurement_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_hydrology_normalize_measurement(request)
    except (ValueError,TypeError,KeyError) as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc

@app.post("/public/hydrology/forecast/normalize")
def public_hydrology_forecast_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_hydrology_normalize_forecast(request)
    except (ValueError,TypeError,KeyError) as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc

@app.post("/public/hydrology/threshold/preview")
def public_hydrology_threshold_preview(request: dict[str, Any] = Body(default={})):
    try: return build_hydrology_threshold_preview(request)
    except (ValueError,TypeError,KeyError) as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc

@app.get("/public/hydrology/export-manifest")
def public_hydrology_manifest(source: str = Query(default="usgs-water-data"), indicator_type: str = Query(default="streamflow"), latitude: float | None = Query(default=None), longitude: float | None = Query(default=None), date: str = Query(default="")):
    try: return build_hydrology_export_manifest(source,indicator_type,latitude,longitude,date)
    except ValueError as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc

@app.get("/public/hydrology/readiness")
def public_hydrology_readiness(): return build_hydrology_readiness()

@app.get("/public/terrestrial-ecosystems")
def public_terrestrial_overview(): return build_terrestrial_overview()

@app.get("/public/terrestrial-ecosystems/catalog")
def public_terrestrial_catalog(): return build_terrestrial_catalog()

@app.get("/public/terrestrial-ecosystems/state")
def public_terrestrial_state(source: str = Query(default="nasa-firms"), indicator_type: str = Query(default="active-fire-detection"), latitude: float | None = Query(default=None), longitude: float | None = Query(default=None), date: str = Query(default="")):
    try: return build_terrestrial_state(source,indicator_type,latitude,longitude,date)
    except ValueError as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc

@app.post("/public/terrestrial-ecosystems/measurement/normalize")
def public_terrestrial_measurement_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_terrestrial_normalize_measurement(request)
    except (ValueError,TypeError,KeyError) as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc

@app.post("/public/terrestrial-ecosystems/feature/normalize")
def public_terrestrial_feature_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_terrestrial_normalize_feature(request)
    except (ValueError,TypeError,KeyError) as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc

@app.post("/public/terrestrial-ecosystems/threshold/preview")
def public_terrestrial_threshold_preview(request: dict[str, Any] = Body(default={})):
    try: return build_terrestrial_threshold_preview(request)
    except (ValueError,TypeError,KeyError) as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc

@app.get("/public/terrestrial-ecosystems/export-manifest")
def public_terrestrial_manifest(source: str = Query(default="nasa-firms"), indicator_type: str = Query(default="active-fire-detection"), latitude: float | None = Query(default=None), longitude: float | None = Query(default=None), date: str = Query(default="")):
    try: return build_terrestrial_export_manifest(source,indicator_type,latitude,longitude,date)
    except ValueError as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc

@app.get("/public/terrestrial-ecosystems/readiness")
def public_terrestrial_readiness(): return build_terrestrial_readiness()

@app.get("/public/geosphere")
def public_geosphere_overview(): return build_geosphere_overview()

@app.get("/public/geosphere/catalog")
def public_geosphere_catalog(): return build_geosphere_catalog()

@app.get("/public/geosphere/state")
def public_geosphere_state(source: str = Query(default="usgs-earthquake-catalog"), indicator_type: str = Query(default="earthquake-event"), latitude: float | None = Query(default=None), longitude: float | None = Query(default=None), date: str = Query(default="")):
    try: return build_geosphere_state(source,indicator_type,latitude,longitude,date)
    except ValueError as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc

@app.post("/public/geosphere/measurement/normalize")
def public_geosphere_measurement_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_geosphere_normalize_measurement(request)
    except (ValueError,TypeError,KeyError) as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc

@app.post("/public/geosphere/notice/normalize")
def public_geosphere_notice_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_geosphere_normalize_notice(request)
    except (ValueError,TypeError,KeyError) as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc

@app.post("/public/geosphere/threshold/preview")
def public_geosphere_threshold_preview(request: dict[str, Any] = Body(default={})):
    try: return build_geosphere_threshold_preview(request)
    except (ValueError,TypeError,KeyError) as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc

@app.get("/public/geosphere/export-manifest")
def public_geosphere_manifest(source: str = Query(default="usgs-earthquake-catalog"), indicator_type: str = Query(default="earthquake-event"), latitude: float | None = Query(default=None), longitude: float | None = Query(default=None), date: str = Query(default="")):
    try: return build_geosphere_export_manifest(source,indicator_type,latitude,longitude,date)
    except ValueError as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc

@app.get("/public/geosphere/readiness")
def public_geosphere_readiness(): return build_geosphere_readiness()

@app.get("/public/soils-land")
def public_soils_overview(): return build_soils_overview()

@app.get("/public/soils-land/catalog")
def public_soils_catalog(): return build_soils_catalog()

@app.get("/public/soils-land/state")
def public_soils_state(source: str = Query(default="isric-soilgrids"), indicator_type: str = Query(default="soil-organic-carbon"), latitude: float | None = Query(default=None), longitude: float | None = Query(default=None), date: str = Query(default="")):
    try: return build_soils_state(source,indicator_type,latitude,longitude,date)
    except (TypeError,ValueError) as exc: raise HTTPException(status_code=400,detail=str(exc))

@app.post("/public/soils-land/measurement/normalize")
def public_soils_measurement_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_soils_normalize_measurement(request)
    except (TypeError,ValueError) as exc: raise HTTPException(status_code=400,detail=str(exc))

@app.post("/public/soils-land/assessment/normalize")
def public_soils_assessment_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_soils_normalize_assessment(request)
    except (TypeError,ValueError) as exc: raise HTTPException(status_code=400,detail=str(exc))

@app.post("/public/soils-land/threshold/preview")
def public_soils_threshold_preview(request: dict[str, Any] = Body(default={})):
    try: return build_soils_threshold_preview(request)
    except (TypeError,ValueError) as exc: raise HTTPException(status_code=400,detail=str(exc))

@app.get("/public/soils-land/export-manifest")
def public_soils_manifest(source: str = Query(default="isric-soilgrids"), indicator_type: str = Query(default="soil-organic-carbon"), latitude: float | None = Query(default=None), longitude: float | None = Query(default=None), date: str = Query(default="")):
    try: return build_soils_export_manifest(source,indicator_type,latitude,longitude,date)
    except (TypeError,ValueError) as exc: raise HTTPException(status_code=400,detail=str(exc))

@app.get("/public/soils-land/readiness")
def public_soils_readiness(): return build_soils_readiness()

@app.get("/public/climate")
def public_climate_overview(): return build_climate_overview()

@app.get("/public/climate/catalog")
def public_climate_catalog(): return build_climate_catalog()

@app.get("/public/climate/state")
def public_climate_state(source: str = Query(default="noaa-ncei-cdo"), indicator_type: str = Query(default="air-temperature"), latitude: float | None = Query(default=None), longitude: float | None = Query(default=None), date: str = Query(default="")):
    try: return build_climate_state(source,indicator_type,latitude,longitude,date)
    except (TypeError,ValueError) as exc: raise HTTPException(status_code=400,detail=str(exc))

@app.post("/public/climate/measurement/normalize")
def public_climate_measurement_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_climate_normalize_measurement(request)
    except (TypeError,ValueError) as exc: raise HTTPException(status_code=400,detail=str(exc))

@app.post("/public/climate/extreme/normalize")
def public_climate_extreme_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_climate_normalize_extreme(request)
    except (TypeError,ValueError) as exc: raise HTTPException(status_code=400,detail=str(exc))

@app.post("/public/climate/threshold/preview")
def public_climate_threshold_preview(request: dict[str, Any] = Body(default={})):
    try: return build_climate_threshold_preview(request)
    except (TypeError,ValueError) as exc: raise HTTPException(status_code=400,detail=str(exc))

@app.get("/public/climate/export-manifest")
def public_climate_manifest(source: str = Query(default="noaa-ncei-cdo"), indicator_type: str = Query(default="air-temperature"), latitude: float | None = Query(default=None), longitude: float | None = Query(default=None), date: str = Query(default="")):
    try: return build_climate_export_manifest(source,indicator_type,latitude,longitude,date)
    except (TypeError,ValueError) as exc: raise HTTPException(status_code=400,detail=str(exc))

@app.get("/public/climate/readiness")
def public_climate_readiness(): return build_climate_readiness()

@app.get("/public/biodiversity")
def public_biodiversity_overview(): return build_biodiversity_overview()

@app.get("/public/biodiversity/catalog")
def public_biodiversity_catalog(): return build_biodiversity_catalog()

@app.get("/public/biodiversity/state")
def public_biodiversity_state(source: str = Query(default="gbif-occurrence"), indicator_type: str = Query(default="species-occurrence"), scientific_name: str = Query(default=""), latitude: float | None = Query(default=None), longitude: float | None = Query(default=None), date: str = Query(default="")):
    try: return build_biodiversity_state(source,indicator_type,scientific_name,latitude,longitude,date)
    except (TypeError,ValueError) as exc: raise HTTPException(status_code=400,detail=str(exc))

@app.post("/public/biodiversity/occurrence/normalize")
def public_biodiversity_occurrence_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_biodiversity_normalize_occurrence(request)
    except (TypeError,ValueError) as exc: raise HTTPException(status_code=400,detail=str(exc))

@app.post("/public/biodiversity/conservation/normalize")
def public_biodiversity_conservation_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_biodiversity_normalize_conservation(request)
    except (TypeError,ValueError) as exc: raise HTTPException(status_code=400,detail=str(exc))

@app.post("/public/biodiversity/overlap/preview")
def public_biodiversity_overlap_preview(request: dict[str, Any] = Body(default={})):
    try: return build_biodiversity_overlap_preview(request)
    except (TypeError,ValueError) as exc: raise HTTPException(status_code=400,detail=str(exc))

@app.get("/public/biodiversity/export-manifest")
def public_biodiversity_manifest(source: str = Query(default="gbif-occurrence"), indicator_type: str = Query(default="species-occurrence"), scientific_name: str = Query(default=""), latitude: float | None = Query(default=None), longitude: float | None = Query(default=None), date: str = Query(default="")):
    try: return build_biodiversity_export_manifest(source,indicator_type,scientific_name,latitude,longitude,date)
    except (TypeError,ValueError) as exc: raise HTTPException(status_code=400,detail=str(exc))

@app.get("/public/biodiversity/readiness")
def public_biodiversity_readiness(): return build_biodiversity_readiness()

@app.get("/public/production-assurance")
def public_production_assurance_endpoint(settings: Settings = Depends(get_settings)):
    return build_public_security_observability_assurance(settings)

@app.get("/public/production-assurance/security")
def public_security_assurance_endpoint(settings: Settings = Depends(get_settings)):
    return build_public_security_posture(settings)

@app.get("/public/production-assurance/observability")
def public_observability_assurance_endpoint():
    return build_public_observability_posture()

@app.get("/public/production-assurance/performance")
def public_performance_assurance_endpoint():
    return build_public_performance_budget()

@app.post("/public/production-assurance/rate-limit/preview")
def public_rate_limit_assurance_preview_endpoint(request: dict[str, Any] = Body(default={}), settings: Settings = Depends(get_settings)):
    return build_public_rate_limit_preview(request, settings)

@app.get("/public/production-assurance/supply-chain")
def public_supply_chain_assurance_endpoint():
    return build_public_supply_chain_posture()

@app.post("/public/production-assurance/post-deploy/preview")
def public_post_deploy_assurance_preview_endpoint(request: dict[str, Any] = Body(default={})):
    return build_public_post_deploy_smoke_preview(request)


@app.get("/public/workflows/analytical")
def public_analytical_workflows_endpoint(settings: Settings = Depends(get_settings)):
    return build_public_analytical_workspaces(settings)


@app.get("/public/workflows/analytical/{workflow_id}")
def public_analytical_workflow_endpoint(workflow_id: str, settings: Settings = Depends(get_settings)):
    try:
        return build_public_analytical_workspace(settings, workflow_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Analytical workflow not found.") from exc


@app.get("/public/workflows/analytical/{workflow_id}/snapshot")
def public_analytical_workflow_snapshot_endpoint(
    workflow_id: str,
    country: str = Query(default="KEN"),
    compare: str = Query(default="GHA"),
    area_id: str = Query(default=""),
    dataset_id: str = Query(default=""),
    layer_id: str = Query(default="true-color"),
    date_a: str = Query(default=""),
    date_b: str = Query(default=""),
    settings: Settings = Depends(get_settings),
):
    try:
        return build_public_analytical_snapshot(settings, workflow_id, {"country":country,"compare":compare,"area_id":area_id,"dataset_id":dataset_id,"layer_id":layer_id,"date_a":date_a,"date_b":date_b})
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Analytical workflow not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/public/workspaces/production-truth")
def public_workspace_production_truth():
    return build_public_production_truth()


@app.get("/public/workspaces/production-truth/{route_id}")
def public_workspace_production_truth_route(route_id: str):
    payload = build_public_production_truth_route(route_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="Unknown public workspace route")
    return payload


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


@app.get("/public/country/{country_code}/linked-records")
def public_country_linked_records(
    country_code: str,
    days: int = Query(default=90, ge=1, le=90),
    limit: int = Query(default=24, ge=1, le=60),
    include_discovery: bool = Query(default=True),
    settings: Settings = Depends(get_settings),
):
    from .country_linked_records_v43520 import build_country_linked_records
    try:
        return build_country_linked_records(
            settings, country_code=country_code, days=days, limit=limit, include_discovery=include_discovery
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="Unsupported country code.")


@app.get("/public/country/{country_code}/data-federation")
def public_country_data_federation_v43521(
    country_code: str,
    query: str = Query(default="", max_length=160),
    limit: int = Query(default=12, ge=1, le=30),
    settings: Settings = Depends(get_settings),
):
    from .palestine_data_federation_v43521 import build_palestine_data_federation
    try:
        return build_palestine_data_federation(settings, country_code=country_code, query=query, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/public/country/{country_code}/knowledge-context")
def public_country_knowledge_context_v43521(
    country_code: str,
    language: str = Query(default="en", min_length=2, max_length=12),
    media_limit: int = Query(default=4, ge=1, le=8),
    pageview_days: int = Query(default=30, ge=1, le=90),
    settings: Settings = Depends(get_settings),
):
    from .wikimedia_knowledge_context_v43521 import country_knowledge_context
    try:
        return country_knowledge_context(
            settings, country_code=country_code, language=language, media_limit=media_limit, pageview_days=pageview_days
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/public/palestine-open-data/search")
def public_palestine_open_data_search_v43521(
    q: str = Query(default="", max_length=160),
    rows: int = Query(default=20, ge=1, le=50),
    settings: Settings = Depends(get_settings),
):
    try:
        return build_palestine_open_data_search_v43521(settings, query=q, rows=rows)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/public/knowledge-context/wikidata/search")
def public_wikidata_search_v43521(
    q: str = Query(..., min_length=1, max_length=180), language: str = Query("en", min_length=2, max_length=12),
    limit: int = Query(5, ge=1, le=20), settings: Settings = Depends(get_settings),
):
    from .wikimedia_knowledge_context_v43521 import wikidata_search
    try: return wikidata_search(settings, query=q, language=language, limit=limit)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/public/knowledge-context/wikidata/entity/{entity_id}")
def public_wikidata_entity_v43521(entity_id: str, language: str = Query("en", min_length=2, max_length=12), settings: Settings = Depends(get_settings)):
    from .wikimedia_knowledge_context_v43521 import wikidata_entity
    try: return wikidata_entity(settings, entity_id=entity_id, language=language)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/public/knowledge-context/wikipedia/page")
def public_wikipedia_context_v43521(title: str = Query(..., min_length=1, max_length=240), language: str = Query("en", min_length=2, max_length=12), settings: Settings = Depends(get_settings)):
    from .wikimedia_knowledge_context_v43521 import wikipedia_page_context
    try: return wikipedia_page_context(settings, title=title, language=language)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/public/knowledge-context/commons/search")
def public_commons_context_v43521(q: str = Query(..., min_length=1, max_length=180), limit: int = Query(6, ge=1, le=12), settings: Settings = Depends(get_settings)):
    from .wikimedia_knowledge_context_v43521 import commons_media_search
    try: return commons_media_search(settings, query=q, limit=limit)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/public/knowledge-context/pageviews")
def public_pageviews_context_v43521(article: str = Query(..., min_length=1, max_length=240), language: str = Query("en", min_length=2, max_length=12), days: int = Query(30, ge=1, le=90), settings: Settings = Depends(get_settings)):
    from .wikimedia_knowledge_context_v43521 import pageviews
    try: return pageviews(settings, article=article, language=language, days=days)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc


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


# Site Intelligence v4.35.23 — Statistical Harmonization and Comparable-Series Engine.
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


# Site Intelligence v4.35.23 — Model Registry, Forecast Evaluation, and Early-Warning Indicators.
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


# Site Intelligence v4.35.23 — Evidence Synthesis, Claims, and Contradiction Review.
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


# Site Intelligence v4.35.23 — Intelligence Publishing and Story Map Studio.
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


# Site Intelligence v4.35.23 — Intelligence Publishing and Story Map Studio.
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

@app.get("/public/authoritative-apis")
def public_authoritative_api_audit_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    return build_authoritative_api_audit(settings)


@app.get("/public/authoritative-apis/catalog")
def public_authoritative_api_catalog_endpoint(
    workspace: str = Query(""),
    access_class: str = Query(""),
    query: str = Query(""),
    settings: Settings = Depends(get_settings),
):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    try:
        return build_authoritative_api_catalog(settings, workspace=workspace, access_class=access_class, query=query)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/public/authoritative-apis/workspaces")
def public_authoritative_api_workspace_matrix_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    return build_authoritative_api_workspace_matrix(settings)


@app.get("/public/authoritative-apis/readiness")
def public_authoritative_api_readiness_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    return build_authoritative_api_readiness(settings)


@app.get("/public/authoritative-apis/production-audit")
def public_authoritative_api_production_audit_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    return build_authoritative_api_production_audit(settings)


@app.get("/public/authoritative-apis/closure-ledger")
def public_authoritative_api_closure_ledger_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    return build_authoritative_api_closure_ledger(settings)


@app.get("/public/authoritative-apis/production-readiness")
def public_authoritative_api_production_readiness_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    return build_authoritative_api_production_readiness(settings)


@app.get("/public/authoritative-connectors")
def public_authoritative_connectors_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    return build_authoritative_connector_catalog(settings)


@app.get("/public/authoritative-connectors/readiness")
def public_authoritative_connectors_readiness_endpoint(settings: Settings = Depends(get_settings)):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    return build_authoritative_connector_readiness(settings)


@app.get("/public/evidence-intelligence")
def public_evidence_intelligence_endpoint():
    return build_evidence_intelligence_overview()


@app.get("/public/evidence-intelligence/metrics")
def public_evidence_metrics_endpoint():
    return build_evidence_metric_catalog()


@app.get("/public/evidence-intelligence/precedence")
def public_evidence_precedence_endpoint(jurisdiction: str = Query(default=""), concept_id: str = Query(default="")):
    return build_evidence_precedence_catalog(jurisdiction=jurisdiction, concept_id=concept_id)


@app.get("/public/evidence-intelligence/freshness")
def public_evidence_freshness_endpoint(observed_at: str = Query(...), cadence: str = Query(default="unknown"), now: str | None = Query(default=None)):
    return build_evidence_freshness_assessment(observed_at=observed_at, cadence=cadence, now=now)


@app.get("/public/evidence-intelligence/indicator/{indicator_id}")
def public_evidence_indicator_semantics_endpoint(indicator_id: str, jurisdiction: str = Query(default="")):
    try:
        return build_evidence_indicator_semantics(indicator_id, jurisdiction=jurisdiction)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Indicator semantics not registered.") from exc


@app.post("/public/evidence-intelligence/select")
def public_evidence_select_endpoint(payload: dict[str, Any] = Body(...)):
    try:
        return build_evidence_selection(
            concept_id=str(payload.get("concept_id") or ""),
            jurisdiction=str(payload.get("jurisdiction") or ""),
            candidates=payload.get("candidates") or [],
            now=payload.get("now"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/public/evidence-intelligence/readiness")
def public_evidence_intelligence_readiness_endpoint():
    return build_evidence_intelligence_readiness()


@app.get("/public/deployment-verification")
def public_deployment_verification_v43531_endpoint(settings: Settings = Depends(get_settings)):
    return build_deployment_verification_v4380(settings)


@app.get("/public/source-health-policy")
def public_source_health_policy_v43531_endpoint(settings: Settings = Depends(get_settings)):
    return build_source_health_policy_v4380(settings)


@app.get("/public/workspace-browser-audit")
def public_workspace_browser_audit_v43518_endpoint():
    return build_workspace_browser_audit_v43518()

@app.get("/public/workspace-browser-audit/readiness")
def public_workspace_browser_readiness_v43518_endpoint():
    return build_workspace_browser_readiness_v43518()

@app.get("/public/workspace-browser-audit/route/{route_id}")
def public_workspace_browser_route_v43518_endpoint(route_id: str):
    try:
        return build_workspace_route_detail_v43518(route_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Workspace route is not registered.") from exc


@app.get("/public/authoritative-connectors/usgs-water/latest")
@app.get("/public/hydrology/live/usgs-water")
def public_usgs_water_latest_endpoint(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius_degrees: float = Query(0.10, gt=0, le=5),
    limit: int = Query(50, ge=1, le=250),
    parameter_code: str = Query(""),
    settings: Settings = Depends(get_settings),
):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    try:
        return build_usgs_water_latest(settings, latitude=latitude, longitude=longitude, radius_degrees=radius_degrees, limit=limit, parameter_code=parameter_code)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/public/authoritative-connectors/noaa-erddap/search")
@app.get("/public/ocean-intelligence/erddap/search")
def public_noaa_erddap_search_endpoint(
    query: str = Query(..., min_length=1, max_length=160),
    limit: int = Query(20, ge=1, le=100),
    settings: Settings = Depends(get_settings),
):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    try:
        return build_noaa_erddap_search(settings, query=query, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/public/authoritative-connectors/noaa-erddap/data")
@app.get("/public/ocean-intelligence/erddap/data")
def public_noaa_erddap_data_endpoint(
    dataset_id: str = Query(..., min_length=1, max_length=128),
    variables: str = Query(..., min_length=1, max_length=500),
    constraint: list[str] = Query(default=[]),
    settings: Settings = Depends(get_settings),
):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    try:
        fields = [item.strip() for item in variables.split(",") if item.strip()]
        return build_noaa_erddap_tabledap(settings, dataset_id=dataset_id, variables=fields, constraints=constraint)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/public/authoritative-connectors/nasa-exoplanets")
@app.get("/public/exoplanet-habitability/live")
def public_nasa_exoplanet_connector_endpoint(
    target: str = Query("", max_length=120),
    limit: int = Query(25, ge=1, le=200),
    settings: Settings = Depends(get_settings),
):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    try:
        return build_nasa_exoplanet_planets(settings, target=target, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/public/authoritative-connectors/unhcr-population")
@app.get("/public/humanitarian-intelligence/displacement/live")
def public_unhcr_population_connector_endpoint(
    year: int | None = Query(None, ge=1951, le=2200),
    origin: str = Query("", max_length=3),
    asylum: str = Query("", max_length=3),
    limit: int = Query(100, ge=1, le=200),
    settings: Settings = Depends(get_settings),
):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    try:
        return build_unhcr_population(settings, year=year, origin=origin, asylum=asylum, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/public/authoritative-connectors/nasa-cmr/collections")
@app.get("/public/science-discovery/nasa-cmr")
def public_nasa_cmr_connector_endpoint(
    query: str = Query(..., min_length=1, max_length=160),
    limit: int = Query(20, ge=1, le=200),
    provider: str = Query("", max_length=80),
    temporal: str = Query("", max_length=120),
    bounding_box: str = Query("", max_length=100),
    settings: Settings = Depends(get_settings),
):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    try:
        return build_nasa_cmr_collections(settings, query=query, limit=limit, provider=provider, temporal=temporal, bounding_box=bounding_box)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/public/authoritative-connectors/noaa-coops/data")
@app.get("/public/coastal-change/live/noaa-coops")
def public_noaa_coops_data_endpoint(
    station: str = Query(..., min_length=1, max_length=20),
    product: str = Query("water_level", max_length=40),
    date: str = Query("latest", max_length=20),
    begin_date: str = Query("", max_length=20),
    end_date: str = Query("", max_length=20),
    datum: str = Query("MSL", max_length=8),
    units: str = Query("metric", max_length=10),
    time_zone: str = Query("gmt", max_length=10),
    interval: str = Query("", max_length=16),
    settings: Settings = Depends(get_settings),
):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    try:
        return build_noaa_coops_data(settings, station=station, product=product, date_value=date, begin_date=begin_date, end_date=end_date, datum=datum, units=units, time_zone=time_zone, interval=interval)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/public/authoritative-connectors/noaa-ncei/data")
@app.get("/public/climate/live/noaa-ncei")
def public_ncei_access_data_endpoint(
    dataset: str = Query(..., min_length=2, max_length=100),
    start_date: str = Query(..., min_length=10, max_length=10),
    end_date: str = Query(..., min_length=10, max_length=10),
    station: list[str] = Query(default=[]),
    data_type: list[str] = Query(default=[]),
    units: str = Query("metric", max_length=10),
    settings: Settings = Depends(get_settings),
):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    try:
        return build_ncei_access_data(settings, dataset=dataset, start_date=start_date, end_date=end_date, stations=station, data_types=data_type, units=units)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/public/authoritative-connectors/obis/occurrences")
@app.get("/public/biodiversity/live/obis")
def public_obis_occurrences_endpoint(
    scientific_name: str = Query("", max_length=160),
    aphia_id: int | None = Query(None, ge=1),
    geometry: str = Query("", max_length=1500),
    start_date: str = Query("", max_length=10),
    end_date: str = Query("", max_length=10),
    size: int = Query(50, ge=1, le=200),
    settings: Settings = Depends(get_settings),
):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    try:
        return build_obis_occurrences(settings, scientific_name=scientific_name, aphia_id=aphia_id, geometry=geometry, start_date=start_date, end_date=end_date, size=size)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/public/authoritative-connectors/eurostat/statistics")
@app.get("/public/solid-waste-circular-materials/live/eurostat")
def public_eurostat_statistics_endpoint(
    dataset_code: str = Query("env_wasmun", min_length=2, max_length=80),
    geo: str = Query("", max_length=16),
    time: str = Query("", max_length=20),
    filter: list[str] = Query(default=[]),
    settings: Settings = Depends(get_settings),
):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    try:
        return build_eurostat_statistics(settings, dataset_code=dataset_code, geo=geo, time=time, filters=filter)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/public/authoritative-connectors/usda-soils/mapunits")
@app.get("/public/soils-land/live/usda-nrcs")
def public_usda_soil_mapunits_endpoint(
    mukey: str = Query("", max_length=30),
    area_symbol: str = Query("", max_length=10),
    limit: int = Query(50, ge=1, le=200),
    settings: Settings = Depends(get_settings),
):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    try:
        return build_usda_soil_mapunits(settings, mukey=mukey, area_symbol=area_symbol, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc



@app.get("/public/authoritative-connectors/usfws-nwi/wetlands")
@app.get("/public/wetlands-inland-water/live/usfws-nwi")
def public_usfws_nwi_wetlands_endpoint(
    latitude: float | None = Query(None, ge=-90, le=90),
    longitude: float | None = Query(None, ge=-180, le=180),
    bbox: str = Query("", max_length=120),
    limit: int = Query(50, ge=1, le=200),
    return_geometry: bool = Query(True),
    settings: Settings = Depends(get_settings),
):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    try:
        return build_usfws_nwi_wetlands(settings, latitude=latitude, longitude=longitude, bbox=bbox, limit=limit, return_geometry=return_geometry)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/public/authoritative-connectors/epa-echo/facilities")
@app.get("/public/industrial-manufacturing/live/epa-echo")
@app.get("/public/water-sanitation/live/epa-echo")
def public_epa_echo_facilities_endpoint(
    media: str = Query("all", max_length=8),
    state: str = Query("", max_length=2),
    registry_id: str = Query("", max_length=24),
    latitude: float | None = Query(None, ge=-90, le=90),
    longitude: float | None = Query(None, ge=-180, le=180),
    radius_miles: float = Query(5.0, gt=0, le=50),
    limit: int = Query(100, ge=1, le=500),
    settings: Settings = Depends(get_settings),
):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    try:
        return build_epa_echo_facilities(settings, media=media, state=state, registry_id=registry_id, latitude=latitude, longitude=longitude, radius_miles=radius_miles, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/public/authoritative-connectors/nasa-firms/area")
@app.get("/public/terrestrial-ecosystems/live/nasa-firms")
def public_nasa_firms_area_endpoint(
    source: str = Query("VIIRS_NOAA20_NRT", max_length=32),
    bbox: str = Query(..., min_length=7, max_length=120),
    day_range: int = Query(1, ge=1, le=5),
    date: str = Query("", max_length=10),
    settings: Settings = Depends(get_settings),
):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    try:
        return build_nasa_firms_area(settings, source=source, bbox=bbox, day_range=day_range, date_value=date)
    except PermissionError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/public/authoritative-connectors/usda-nass/quick-stats")
@app.get("/public/agriculture-food-systems/live/usda-nass")
def public_usda_nass_quickstats_endpoint(
    filter: list[str] = Query(default=[]),
    limit: int = Query(100, ge=1, le=500),
    settings: Settings = Depends(get_settings),
):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    try:
        return build_usda_nass_quickstats(settings, filters=filter, limit=limit)
    except PermissionError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/public/authoritative-connectors/nasa-cmr/graphql/collections")
@app.get("/public/science-discovery/nasa-cmr-graphql")
def public_nasa_cmr_graphql_endpoint(
    keyword: str = Query("", max_length=160),
    short_name: str = Query("", max_length=120),
    provider: str = Query("", max_length=80),
    bounding_box: str = Query("", max_length=120),
    temporal: str = Query("", max_length=100),
    limit: int = Query(20, ge=1, le=100),
    settings: Settings = Depends(get_settings),
):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    try:
        return build_nasa_cmr_graphql_collections(settings, keyword=keyword, short_name=short_name, provider=provider, bounding_box=bounding_box, temporal=temporal, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

@app.get("/public/authoritative-connectors/pcbs/pxweb/metadata")
@app.get("/public/country-statistics/palestine/pcbs/metadata")
def public_pcbs_pxweb_metadata_endpoint(
    table_path: str = Query(..., min_length=3, max_length=240),
    settings: Settings = Depends(get_settings),
):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    try:
        return build_pcbs_pxweb_metadata(settings, table_path=table_path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/public/authoritative-connectors/pcbs/pxweb/data")
@app.get("/public/country-statistics/palestine/pcbs/data")
def public_pcbs_pxweb_data_endpoint(
    table_path: str = Query(..., min_length=3, max_length=240),
    selection: list[str] = Query(default=[]),
    settings: Settings = Depends(get_settings),
):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    try:
        return build_pcbs_pxweb_data(settings, table_path=table_path, selections=selection)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/public/authoritative-connectors/statcan/vectors")
@app.get("/public/country-statistics/canada/statcan")
def public_statcan_vectors_endpoint(
    vector_id: list[int] = Query(default=[]),
    latest_n: int = Query(3, ge=1, le=24),
    settings: Settings = Depends(get_settings),
):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    try:
        return build_statcan_vectors(settings, vector_ids=vector_id, latest_n=latest_n)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/public/authoritative-connectors/ons/observations")
@app.get("/public/country-statistics/united-kingdom/ons")
def public_ons_observations_endpoint(
    dataset_id: str = Query(..., min_length=1, max_length=100),
    edition: str = Query(..., min_length=1, max_length=100),
    version: int = Query(..., ge=1),
    filter: list[str] = Query(default=[]),
    settings: Settings = Depends(get_settings),
):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    try:
        return build_ons_observations(settings, dataset_id=dataset_id, edition=edition, version=version, filters=filter)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/public/authoritative-connectors/abs/sdmx")
@app.get("/public/country-statistics/australia/abs")
def public_abs_sdmx_endpoint(
    dataflow: str = Query(..., min_length=2, max_length=120),
    data_key: str = Query(..., min_length=1, max_length=240),
    start_period: str = Query(..., min_length=4, max_length=20),
    end_period: str = Query(..., min_length=4, max_length=20),
    limit: int = Query(200, ge=1, le=1000),
    settings: Settings = Depends(get_settings),
):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    try:
        return build_abs_sdmx_data(settings, dataflow=dataflow, data_key=data_key, start_period=start_period, end_period=end_period, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/public/authoritative-connectors/bls/timeseries")
@app.get("/public/economics-labor/live/bls")
def public_bls_timeseries_endpoint(
    series_id: list[str] = Query(default=[]),
    start_year: int | None = Query(None, ge=1900, le=2200),
    end_year: int | None = Query(None, ge=1900, le=2200),
    settings: Settings = Depends(get_settings),
):
    if not settings.public_dashboards_enabled:
        raise HTTPException(status_code=403, detail="Public dashboards are disabled.")
    try:
        return build_bls_timeseries(settings, series_ids=series_id, start_year=start_year, end_year=end_year)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/public/authoritative-connectors/faostat/data")
@app.get("/public/agriculture-food/live/faostat")
def public_faostat_data_endpoint(
    domain: str = Query(..., min_length=1, max_length=12), area: str = Query("", max_length=300),
    item: str = Query("", max_length=300), element: str = Query("", max_length=300),
    year: str = Query("", max_length=300), limit: int = Query(250, ge=1, le=1000), settings: Settings = Depends(get_settings),
):
    try: return build_faostat_data(settings, domain=domain, area=area, item=item, element=element, year=year, limit=limit)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc: raise HTTPException(status_code=502, detail=str(exc)) from exc

@app.get("/public/authoritative-connectors/ilostat/indicator")
@app.get("/public/human-development/live/ilostat")
def public_ilostat_indicator_endpoint(
    indicator: str = Query(..., min_length=3, max_length=64), ref_area: str = Query(..., min_length=2, max_length=8),
    start_year: int | None = Query(None, ge=1950, le=2100), end_year: int | None = Query(None, ge=1950, le=2100), settings: Settings = Depends(get_settings),
):
    try: return build_ilostat_indicator(settings, indicator=indicator, ref_area=ref_area, start_year=start_year, end_year=end_year)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc: raise HTTPException(status_code=502, detail=str(exc)) from exc

@app.get("/public/authoritative-connectors/oecd/sdmx")
@app.get("/public/economics-development/live/oecd")
def public_oecd_sdmx_endpoint(
    agency: str = Query(..., min_length=2, max_length=80), dataflow: str = Query(..., min_length=2, max_length=120),
    version: str = Query("", max_length=32), key: str = Query(..., min_length=1, max_length=300),
    start_period: str = Query("", max_length=20), end_period: str = Query("", max_length=20), settings: Settings = Depends(get_settings),
):
    try: return build_oecd_sdmx_data(settings, agency=agency, dataflow=dataflow, version=version, key=key, start_period=start_period, end_period=end_period)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc: raise HTTPException(status_code=502, detail=str(exc)) from exc

@app.get("/public/authoritative-connectors/epa-frs/facilities")
@app.get("/public/industrial-manufacturing/live/epa-frs")
def public_epa_frs_facilities_endpoint(
    registry_id: str = Query("", max_length=20), facility_name: str = Query("", max_length=100), state_abbr: str = Query("", max_length=2),
    city_name: str = Query("", max_length=80), zip_code: str = Query("", max_length=10), program_acronym: str = Query("", max_length=24),
    latitude: float | None = Query(None, ge=-90, le=90), longitude: float | None = Query(None, ge=-180, le=180),
    search_radius: float | None = Query(None, gt=0, le=25), settings: Settings = Depends(get_settings),
):
    try: return build_epa_frs_facilities(settings, registry_id=registry_id, facility_name=facility_name, state_abbr=state_abbr, city_name=city_name, zip_code=zip_code, program_acronym=program_acronym, latitude=latitude, longitude=longitude, search_radius=search_radius)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc: raise HTTPException(status_code=502, detail=str(exc)) from exc

@app.get("/public/authoritative-connectors/usgs-volcano/notices")
@app.get("/public/geosphere/live/usgs-volcano")
def public_usgs_volcano_notices_endpoint(
    days: int = Query(3, ge=1, le=7), observatory: str = Query("", max_length=8), settings: Settings = Depends(get_settings),
):
    try: return build_usgs_volcano_notices(settings, days=days, observatory=observatory)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc: raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/public/energy-systems/live/osm-power")
def public_energy_osm_power(latitude: float=Query(...,ge=-90,le=90), longitude: float=Query(...,ge=-180,le=180), radius_km: float=Query(10,gt=0,le=50), settings: Settings=Depends(get_settings)):
    try: return build_osm_power(settings,latitude=latitude,longitude=longitude,radius_km=radius_km)
    except ValueError as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc
    except RuntimeError as exc: raise HTTPException(status_code=502,detail=str(exc)) from exc

@app.get("/public/energy-systems/live/eia")
def public_energy_eia(route: str=Query("electricity/rto/region-data",max_length=120), data_field: str=Query("value",max_length=40), facet_name: str=Query("",max_length=40), facet_value: str=Query("",max_length=80), frequency: str=Query("hourly",max_length=20), start: str=Query("",max_length=20), end: str=Query("",max_length=20), length: int=Query(100,ge=1,le=500), settings: Settings=Depends(get_settings)):
    try: return build_eia_electricity_v43511(settings,route=route,data_field=data_field,facet_name=facet_name,facet_value=facet_value,frequency=frequency,start=start,end=end,length=length)
    except ValueError as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc
    except RuntimeError as exc: raise HTTPException(status_code=502,detail=str(exc)) from exc

@app.get("/public/energy-systems/live/ember")
def public_energy_ember(entity_code: str=Query(...,min_length=2,max_length=12), dataset: str=Query("electricity-generation",max_length=40), resolution: str=Query("monthly",max_length=10), start_date: str=Query("",max_length=20), end_date: str=Query("",max_length=20), settings: Settings=Depends(get_settings)):
    try: return build_ember_electricity(settings,dataset=dataset,resolution=resolution,entity_code=entity_code,start_date=start_date,end_date=end_date)
    except ValueError as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc
    except RuntimeError as exc: raise HTTPException(status_code=502,detail=str(exc)) from exc

@app.get("/public/energy-systems/live/entsoe")
def public_energy_entsoe(document_type: str=Query(...,min_length=3,max_length=3), period_start: str=Query(...,min_length=12,max_length=12), period_end: str=Query(...,min_length=12,max_length=12), domain_param: str=Query(...,max_length=32), domain_code: str=Query(...,min_length=10,max_length=20), process_type: str=Query("",max_length=3), settings: Settings=Depends(get_settings)):
    try: return build_entsoe_data(settings,document_type=document_type,period_start=period_start,period_end=period_end,domain_param=domain_param,domain_code=domain_code,process_type=process_type)
    except ValueError as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc
    except RuntimeError as exc: raise HTTPException(status_code=502,detail=str(exc)) from exc

@app.get("/public/digital-connectivity/live/osm-telecom")
def public_digital_osm_telecom(latitude: float=Query(...,ge=-90,le=90), longitude: float=Query(...,ge=-180,le=180), radius_km: float=Query(10,gt=0,le=50), settings: Settings=Depends(get_settings)):
    try: return build_osm_telecom(settings,latitude=latitude,longitude=longitude,radius_km=radius_km)
    except ValueError as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc
    except RuntimeError as exc: raise HTTPException(status_code=502,detail=str(exc)) from exc

@app.get("/public/digital-connectivity/discovery/mlab")
def public_digital_mlab(settings: Settings=Depends(get_settings)):
    try: return build_mlab_locate(settings)
    except RuntimeError as exc: raise HTTPException(status_code=502,detail=str(exc)) from exc

@app.get("/public/digital-connectivity/discovery/fcc-bdc")
def public_digital_fcc_bdc(settings: Settings=Depends(get_settings)):
    try: return build_fcc_bdc_asofs(settings)
    except RuntimeError as exc: raise HTTPException(status_code=502,detail=str(exc)) from exc

@app.get("/public/authoritative-connectors/airnow/current")
@app.get("/public/atmosphere/live/airnow")
def public_atmosphere_airnow_current(latitude: float=Query(...,ge=-90,le=90), longitude: float=Query(...,ge=-180,le=180), distance_miles: int=Query(25,ge=1,le=250), settings: Settings=Depends(get_settings)):
    try: return build_airnow_current_v43512(settings,latitude=latitude,longitude=longitude,distance_miles=distance_miles)
    except ValueError as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc
    except RuntimeError as exc: raise HTTPException(status_code=502,detail=str(exc)) from exc

@app.get("/public/authoritative-connectors/copernicus-era5/catalogue")
@app.get("/public/climate/discovery/era5")
def public_climate_era5_catalogue(collection_id: str=Query("reanalysis-era5-single-levels",max_length=120), settings: Settings=Depends(get_settings)):
    try: return build_era5_catalogue_v43512(settings,collection_id=collection_id)
    except ValueError as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc
    except RuntimeError as exc: raise HTTPException(status_code=502,detail=str(exc)) from exc

@app.get("/public/authoritative-connectors/cams/catalogue")
@app.get("/public/atmosphere/discovery/cams")
def public_atmosphere_cams_catalogue(collection_id: str=Query("cams-global-atmospheric-composition-forecasts",max_length=120), settings: Settings=Depends(get_settings)):
    try: return build_cams_catalogue_v43512(settings,collection_id=collection_id)
    except ValueError as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc
    except RuntimeError as exc: raise HTTPException(status_code=502,detail=str(exc)) from exc


@app.get("/public/authoritative-connectors/osm-water")
@app.get("/public/water-sanitation/live/osm-water")
def public_water_osm_infrastructure(latitude: float=Query(...,ge=-90,le=90), longitude: float=Query(...,ge=-180,le=180), radius_km: float=Query(10,gt=0,le=50), settings: Settings=Depends(get_settings)):
    try: return build_osm_water_v43513(settings,latitude=latitude,longitude=longitude,radius_km=radius_km)
    except ValueError as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc
    except RuntimeError as exc: raise HTTPException(status_code=502,detail=str(exc)) from exc

@app.get("/public/authoritative-connectors/epa-sdwis")
@app.get("/public/water-sanitation/live/epa-sdwis")
def public_water_epa_sdwis(dataset: str=Query("county-served",max_length=40), filter_column: str=Query("",max_length=40), filter_value: str=Query("",max_length=80), limit: int=Query(100,ge=1,le=500), settings: Settings=Depends(get_settings)):
    try: return build_epa_sdwis_v43513(settings,dataset=dataset,filter_column=filter_column,filter_value=filter_value,limit=limit)
    except ValueError as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc
    except RuntimeError as exc: raise HTTPException(status_code=502,detail=str(exc)) from exc

@app.get("/public/authoritative-connectors/nidis-drought/file")
@app.get("/public/hydrology/live/drought-gov")
def public_hydrology_nidis_drought(relative_path: str=Query(...,min_length=5,max_length=220), settings: Settings=Depends(get_settings)):
    try: return build_nidis_drought_file_v43513(settings,relative_path=relative_path)
    except ValueError as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc
    except RuntimeError as exc: raise HTTPException(status_code=502,detail=str(exc)) from exc

@app.get("/public/authoritative-connectors/nasa-gpm/discovery")
@app.get("/public/hydrology/discovery/nasa-gpm")
def public_hydrology_nasa_gpm(limit: int=Query(20,ge=1,le=200), temporal: str=Query("",max_length=120), bounding_box: str=Query("",max_length=100), settings: Settings=Depends(get_settings)):
    try: return build_nasa_gpm_imerg_discovery_v43513(settings,limit=limit,temporal=temporal,bounding_box=bounding_box)
    except ValueError as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc
    except RuntimeError as exc: raise HTTPException(status_code=502,detail=str(exc)) from exc

@app.get("/public/authoritative-connectors/glofas/layers")
@app.get("/public/hydrology/discovery/glofas")
def public_hydrology_glofas_layers(settings: Settings=Depends(get_settings)):
    try: return build_glofas_layers_v43513(settings)
    except RuntimeError as exc: raise HTTPException(status_code=502,detail=str(exc)) from exc


@app.get("/public/authoritative-connectors/gdacs/events")
@app.get("/public/humanitarian/live/gdacs")
def public_humanitarian_gdacs_events(event_type: str=Query("",max_length=8), alert_level: str=Query("",max_length=8), limit: int=Query(50,ge=1,le=100), settings: Settings=Depends(get_settings)):
    try: return build_gdacs_events_v43514(settings,event_type=event_type,alert_level=alert_level,limit=limit)
    except ValueError as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc
    except RuntimeError as exc: raise HTTPException(status_code=502,detail=str(exc)) from exc

@app.get("/public/authoritative-connectors/hdx/datasets")
@app.get("/public/humanitarian/discovery/hdx")
def public_humanitarian_hdx_dataset_search(query: str=Query(...,min_length=1,max_length=120), rows: int=Query(20,ge=1,le=50), settings: Settings=Depends(get_settings)):
    try: return build_hdx_dataset_search_v43514(settings,query=query,rows=rows)
    except ValueError as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc
    except RuntimeError as exc: raise HTTPException(status_code=502,detail=str(exc)) from exc

@app.get("/public/authoritative-connectors/hdx-hapi")
@app.get("/public/food-security/live/hdx-hapi")
def public_food_security_hdx_hapi(dataset: str=Query("food-security",max_length=40), location_code: str=Query("",max_length=3), limit: int=Query(100,ge=1,le=500), offset: int=Query(0,ge=0,le=100000), settings: Settings=Depends(get_settings)):
    try: return build_hdx_hapi_v43514(settings,dataset=dataset,location_code=location_code,limit=limit,offset=offset)
    except ValueError as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc
    except RuntimeError as exc: raise HTTPException(status_code=502,detail=str(exc)) from exc

@app.get("/public/authoritative-connectors/ipc")
@app.get("/public/food-security/live/ipc")
def public_food_security_ipc(resource: str=Query("country",max_length=20), country: str=Query("",max_length=2), year: int|None=Query(None,ge=2000,le=2100), analysis_type: str=Query("",max_length=1), limit: int=Query(250,ge=1,le=1000), settings: Settings=Depends(get_settings)):
    try: return build_ipc_food_security_v43514(settings,resource=resource,country=country,year=year,analysis_type=analysis_type,limit=limit)
    except ValueError as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc
    except RuntimeError as exc: raise HTTPException(status_code=502,detail=str(exc)) from exc

@app.get("/public/authoritative-connectors/fews-net")
@app.get("/public/food-security/live/fews-net")
def public_food_security_fews_net(dataset: str=Query("food-security-phase",max_length=40), country_code: str=Query("",max_length=2), start_date: str=Query("",max_length=10), end_date: str=Query("",max_length=10), scenario: str=Query("",max_length=8), page_size: int=Query(100,ge=1,le=500), offset: int=Query(0,ge=0,le=100000), settings: Settings=Depends(get_settings)):
    try: return build_fews_net_data_v43514(settings,dataset=dataset,country_code=country_code,start_date=start_date,end_date=end_date,scenario=scenario,page_size=page_size,offset=offset)
    except ValueError as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc
    except RuntimeError as exc: raise HTTPException(status_code=502,detail=str(exc)) from exc


@app.get("/public/authoritative-connectors/osm-mining")
@app.get("/public/mining-critical-materials/live/osm-mining")
def public_mining_osm_features(latitude: float=Query(...,ge=-90,le=90), longitude: float=Query(...,ge=-180,le=180), radius_km: float=Query(10,gt=0,le=50), settings: Settings=Depends(get_settings)):
    try: return build_osm_mining_v43515(settings,latitude=latitude,longitude=longitude,radius_km=radius_km)
    except ValueError as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc
    except RuntimeError as exc: raise HTTPException(status_code=502,detail=str(exc)) from exc

@app.get("/public/authoritative-connectors/usgs-usmin/discovery")
@app.get("/public/mining-critical-materials/discovery/usgs-usmin")
def public_mining_usgs_usmin(record_id: str=Query("USGS:6464de5bd34ec179a83d9e6c",max_length=80), settings: Settings=Depends(get_settings)):
    try: return build_usgs_usmin_discovery_v43515(settings,record_id=record_id)
    except ValueError as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc
    except RuntimeError as exc: raise HTTPException(status_code=502,detail=str(exc)) from exc

@app.get("/public/authoritative-connectors/usgs-mcs-2026/discovery")
@app.get("/public/mining-critical-materials/discovery/usgs-mcs-2026")
def public_mining_usgs_mcs_2026(record_id: str=Query("USGS:69837e43b66b01367d7ec7c7",max_length=80), settings: Settings=Depends(get_settings)):
    try: return build_usgs_mcs_2026_discovery_v43515(settings,record_id=record_id)
    except ValueError as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc
    except RuntimeError as exc: raise HTTPException(status_code=502,detail=str(exc)) from exc

@app.get("/public/authoritative-connectors/osm-industrial")
@app.get("/public/industrial-manufacturing/live/osm-industrial")
def public_industrial_osm_features(latitude: float=Query(...,ge=-90,le=90), longitude: float=Query(...,ge=-180,le=180), radius_km: float=Query(10,gt=0,le=50), settings: Settings=Depends(get_settings)):
    try: return build_osm_industrial_v43515(settings,latitude=latitude,longitude=longitude,radius_km=radius_km)
    except ValueError as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc
    except RuntimeError as exc: raise HTTPException(status_code=502,detail=str(exc)) from exc

@app.get("/public/authoritative-connectors/wits/trade-stats")
@app.get("/public/industrial-manufacturing/live/wits")
def public_industrial_wits_trade_stats(reporter: str=Query(...,min_length=3,max_length=3), year: int=Query(...,ge=1988,le=2100), partner: str=Query("wld",max_length=3), product: str=Query("999999",max_length=20), indicator: str=Query("XPRT-TRD-VL",max_length=40), dataset: str=Query("tradestats-trade",max_length=40), settings: Settings=Depends(get_settings)):
    try: return build_wits_trade_stats_v43515(settings,reporter=reporter,year=year,partner=partner,product=product,indicator=indicator,dataset=dataset)
    except ValueError as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc
    except RuntimeError as exc: raise HTTPException(status_code=502,detail=str(exc)) from exc



@app.get("/public/external-resilience")
def public_external_resilience(settings: Settings=Depends(get_settings)):
    return build_external_resilience_v43517(settings)

@app.get("/public/external-resilience/readiness")
def public_external_resilience_readiness(settings: Settings=Depends(get_settings)):
    return build_external_resilience_readiness_v43517(settings)

@app.get("/public/external-resilience/providers")
def public_external_resilience_providers():
    return build_external_resilience_provider_states_v43517()


@app.get("/public/country-evidence-reconciliation/readiness")
def public_country_evidence_reconciliation_readiness_v43522():
    from .country_evidence_reconciliation_v43522 import readiness
    return readiness()


@app.get("/public/country-identity/readiness")
def public_country_identity_readiness_v43523():
    from .country_identity_v43523 import readiness
    return readiness()


@app.get("/public/country-navigation-integrity/readiness")
def public_country_navigation_integrity_readiness_v43524():
    from .country_navigation_integrity_v43524 import readiness
    return readiness()

@app.get("/public/country-evidence-presentation/readiness")
def public_country_evidence_presentation_readiness_v43525():
    from .country_evidence_presentation_v43525 import readiness
    return readiness()


@app.post("/public/country-evidence-reconciliation/reconcile")
def public_country_evidence_reconcile_v43522(payload: dict[str, Any] = Body(...)):
    from .country_evidence_reconciliation_v43522 import reconcile_evidence
    try:
        return reconcile_evidence(
            jurisdiction=payload.get("jurisdiction") or payload.get("country_code") or "",
            concept_id=payload.get("concept_id") or "",
            candidates=payload.get("candidates") or [],
            now=payload.get("now"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/public/country/{country_code}/evidence-reconciliation")
def public_country_evidence_reconciliation_snapshot_v43522(country_code: str):
    from .country_evidence_reconciliation_v43522 import country_reconciliation_snapshot
    try:
        return country_reconciliation_snapshot(country_code)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/public/country-linked-records/readiness")
def public_country_linked_records_readiness_v43520():
    from .country_linked_records_v43520 import readiness
    return readiness()


@app.get("/public/country-data-federation/readiness")
def public_country_data_federation_readiness_v43521():
    from .palestine_data_federation_v43521 import readiness
    return readiness()


@app.get("/public/knowledge-context/readiness")
def public_knowledge_context_readiness_v43521():
    from .wikimedia_knowledge_context_v43521 import readiness
    return readiness()


@app.get("/public/production-soak")
def public_production_soak_v43519(settings: Settings=Depends(get_settings)):
    return build_production_soak_v43519(settings)

@app.get("/public/production-soak/readiness")
def public_production_soak_readiness_v43519(settings: Settings=Depends(get_settings)):
    return build_production_soak_readiness_v43519(settings)

@app.get("/public/evidence-presentation/readiness")
def public_evidence_presentation_readiness_v43519():
    return build_evidence_presentation_readiness_v43519()

@app.get("/public/evidence-presentation/classify")
def public_evidence_presentation_classify_v43519(
    jurisdiction: str=Query(...,min_length=2,max_length=12),
    indicator_id: str=Query(...,min_length=2,max_length=80),
    source: str=Query(...,min_length=2,max_length=160),
    observation_year: int|None=Query(None,ge=1800,le=2200),
    data_state: str=Query("unavailable",max_length=40),
    value_available: bool=Query(True),
):
    return build_evidence_presentation_classification_v43519(
        jurisdiction=jurisdiction, indicator_id=indicator_id, source=source, observation_year=observation_year,
        data_state=data_state, value_available=value_available,
    )


@app.get("/public/credential-configuration")
def public_credential_configuration(settings: Settings=Depends(get_settings)):
    return build_credential_configuration_v43516(settings)

@app.get("/public/credential-configuration/readiness")
def public_credential_configuration_readiness(settings: Settings=Depends(get_settings)):
    return build_credential_configuration_readiness_v43516(settings)

@app.get("/public/credential-configuration/workspaces")
def public_credential_configuration_workspaces(settings: Settings=Depends(get_settings)):
    return build_credential_configuration_workspaces_v43516(settings)


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



@app.get("/public/agriculture-food")
def public_agriculture_overview(): return build_agriculture_overview()
@app.get("/public/agriculture-food/catalog")
def public_agriculture_catalog(): return build_agriculture_catalog()
@app.get("/public/agriculture-food/state")
def public_agriculture_state(source: str = Query(default="faostat"), indicator_type: str = Query(default="crop-production"), commodity: str = Query(default=""), area: str = Query(default=""), year: str = Query(default=""), latitude: float | None = Query(default=None), longitude: float | None = Query(default=None)):
    try: return build_agriculture_state(source,indicator_type,commodity,area,year,latitude,longitude)
    except (ValueError,TypeError) as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc
@app.post("/public/agriculture-food/measurement/normalize")
def public_agriculture_measurement_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_agriculture_normalize_measurement(request)
    except (ValueError,TypeError) as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc
@app.post("/public/agriculture-food/assessment/normalize")
def public_agriculture_assessment_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_agriculture_normalize_assessment(request)
    except (ValueError,TypeError) as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc
@app.post("/public/agriculture-food/threshold/preview")
def public_agriculture_threshold_preview(request: dict[str, Any] = Body(default={})):
    try: return build_agriculture_threshold_preview(request)
    except (ValueError,TypeError) as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc
@app.get("/public/agriculture-food/export-manifest")
def public_agriculture_manifest(source: str = Query(default="faostat"), indicator_type: str = Query(default="crop-production"), commodity: str = Query(default=""), area: str = Query(default=""), year: str = Query(default="")):
    try: return build_agriculture_export_manifest(source,indicator_type,commodity,area,year)
    except (ValueError,TypeError) as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc
@app.get("/public/agriculture-food/readiness")
def public_agriculture_readiness(): return build_agriculture_readiness()

@app.get("/public/human-settlements")
def public_human_settlements_overview(): return build_human_settlements_overview()
@app.get("/public/human-settlements/catalog")
def public_human_settlements_catalog(): return build_human_settlements_catalog()
@app.get("/public/human-settlements/state")
def public_human_settlements_state(source: str = Query(default="jrc-ghsl"), indicator_type: str = Query(default="built-up-surface"), area: str = Query(default=""), year: str = Query(default=""), latitude: float | None = Query(default=None), longitude: float | None = Query(default=None)):
    try: return build_human_settlements_state(source,indicator_type,area,year,latitude,longitude)
    except (ValueError,TypeError) as exc: raise HTTPException(status_code=422,detail=str(exc))
@app.post("/public/human-settlements/measurement/normalize")
def public_human_settlements_measurement_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_human_settlements_normalize_measurement(request)
    except (ValueError,TypeError) as exc: raise HTTPException(status_code=422,detail=str(exc))
@app.post("/public/human-settlements/feature/normalize")
def public_human_settlements_feature_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_human_settlements_normalize_feature(request)
    except (ValueError,TypeError) as exc: raise HTTPException(status_code=422,detail=str(exc))
@app.post("/public/human-settlements/threshold/preview")
def public_human_settlements_threshold_preview(request: dict[str, Any] = Body(default={})):
    try: return build_human_settlements_threshold_preview(request)
    except (ValueError,TypeError) as exc: raise HTTPException(status_code=422,detail=str(exc))
@app.get("/public/human-settlements/export-manifest")
def public_human_settlements_manifest(source: str = Query(default="jrc-ghsl"), indicator_type: str = Query(default="built-up-surface"), area: str = Query(default=""), year: str = Query(default=""), latitude: float | None = Query(default=None), longitude: float | None = Query(default=None)):
    try: return build_human_settlements_export_manifest(source,indicator_type,area,year,latitude,longitude)
    except (ValueError,TypeError) as exc: raise HTTPException(status_code=422,detail=str(exc))
@app.get("/public/human-settlements/readiness")
def public_human_settlements_readiness(): return build_human_settlements_readiness()

@app.get("/public/transportation-infrastructure")
def public_transportation_overview(): return build_transportation_overview()
@app.get("/public/transportation-infrastructure/catalog")
def public_transportation_catalog(): return build_transportation_catalog()
@app.get("/public/transportation-infrastructure/state")
def public_transportation_state(source: str = Query(default="overture-transportation"), indicator_type: str = Query(default="road-segment"), area: str = Query(default=""), date: str = Query(default=""), latitude: float | None = Query(default=None), longitude: float | None = Query(default=None)):
    try: return build_transportation_state(source,indicator_type,area,date,latitude,longitude)
    except (ValueError,TypeError) as exc: raise HTTPException(status_code=400,detail=str(exc))
@app.post("/public/transportation-infrastructure/feature/normalize")
def public_transportation_feature_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_transportation_normalize_feature(request)
    except (ValueError,TypeError) as exc: raise HTTPException(status_code=400,detail=str(exc))
@app.post("/public/transportation-infrastructure/feed/normalize")
def public_transportation_feed_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_transportation_normalize_feed(request)
    except (ValueError,TypeError) as exc: raise HTTPException(status_code=400,detail=str(exc))
@app.post("/public/transportation-infrastructure/accessibility/preview")
def public_transportation_accessibility_preview(request: dict[str, Any] = Body(default={})):
    try: return build_transportation_accessibility_preview(request)
    except (ValueError,TypeError) as exc: raise HTTPException(status_code=400,detail=str(exc))
@app.get("/public/transportation-infrastructure/export-manifest")
def public_transportation_manifest(source: str = Query(default="overture-transportation"), indicator_type: str = Query(default="road-segment"), area: str = Query(default=""), date: str = Query(default=""), latitude: float | None = Query(default=None), longitude: float | None = Query(default=None)):
    try: return build_transportation_export_manifest(source,indicator_type,area,date,latitude,longitude)
    except (ValueError,TypeError) as exc: raise HTTPException(status_code=400,detail=str(exc))
@app.get("/public/transportation-infrastructure/readiness")
def public_transportation_readiness(): return build_transportation_readiness()

@app.get("/public/energy-systems")
def public_energy_systems_overview(): return build_energy_systems_overview()
@app.get("/public/energy-systems/catalog")
def public_energy_systems_catalog(): return build_energy_systems_catalog()
@app.get("/public/energy-systems/state")
def public_energy_systems_state(source: str = Query(default="openstreetmap-power"), indicator_type: str = Query(default="power-line"), area: str = Query(default=""), date: str = Query(default=""), latitude: float | None = Query(default=None), longitude: float | None = Query(default=None)):
    try: return build_energy_systems_state(source,indicator_type,area,date,latitude,longitude)
    except (ValueError,TypeError) as exc: raise HTTPException(status_code=400,detail=str(exc))
@app.post("/public/energy-systems/feature/normalize")
def public_energy_systems_feature_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_energy_systems_normalize_feature(request)
    except (ValueError,TypeError) as exc: raise HTTPException(status_code=400,detail=str(exc))
@app.post("/public/energy-systems/series/normalize")
def public_energy_systems_series_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_energy_systems_normalize_series(request)
    except (ValueError,TypeError) as exc: raise HTTPException(status_code=400,detail=str(exc))
@app.post("/public/energy-systems/threshold/preview")
def public_energy_systems_threshold_preview(request: dict[str, Any] = Body(default={})):
    try: return build_energy_systems_threshold_preview(request)
    except (ValueError,TypeError) as exc: raise HTTPException(status_code=400,detail=str(exc))
@app.get("/public/energy-systems/export-manifest")
def public_energy_systems_manifest(source: str = Query(default="openstreetmap-power"), indicator_type: str = Query(default="power-line"), area: str = Query(default=""), date: str = Query(default=""), latitude: float | None = Query(default=None), longitude: float | None = Query(default=None)):
    try: return build_energy_systems_export_manifest(source,indicator_type,area,date,latitude,longitude)
    except (ValueError,TypeError) as exc: raise HTTPException(status_code=400,detail=str(exc))
@app.get("/public/energy-systems/readiness")
def public_energy_systems_readiness(): return build_energy_systems_readiness()

@app.get("/public/digital-connectivity")
def public_digital_connectivity_overview(): return build_digital_connectivity_overview()
@app.get("/public/digital-connectivity/catalog")
def public_digital_connectivity_catalog(): return build_digital_connectivity_catalog()
@app.get("/public/digital-connectivity/state")
def public_digital_connectivity_state(source: str = Query(default="openstreetmap-telecom"), indicator_type: str = Query(default="communications-tower"), area: str = Query(default=""), date: str = Query(default=""), latitude: float | None = Query(default=None), longitude: float | None = Query(default=None)):
    try: return build_digital_connectivity_state(source,indicator_type,area,date,latitude,longitude)
    except (ValueError,TypeError) as exc: raise HTTPException(status_code=400,detail=str(exc))
@app.post("/public/digital-connectivity/feature/normalize")
def public_digital_connectivity_feature_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_digital_connectivity_normalize_feature(request)
    except (ValueError,TypeError) as exc: raise HTTPException(status_code=400,detail=str(exc))
@app.post("/public/digital-connectivity/measurement/normalize")
def public_digital_connectivity_measurement_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_digital_connectivity_normalize_measurement(request)
    except (ValueError,TypeError) as exc: raise HTTPException(status_code=400,detail=str(exc))
@app.post("/public/digital-connectivity/availability/normalize")
def public_digital_connectivity_availability_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_digital_connectivity_normalize_availability(request)
    except (ValueError,TypeError) as exc: raise HTTPException(status_code=400,detail=str(exc))
@app.post("/public/digital-connectivity/threshold/preview")
def public_digital_connectivity_threshold_preview(request: dict[str, Any] = Body(default={})):
    try: return build_digital_connectivity_threshold_preview(request)
    except (ValueError,TypeError) as exc: raise HTTPException(status_code=400,detail=str(exc))
@app.get("/public/digital-connectivity/export-manifest")
def public_digital_connectivity_manifest(source: str = Query(default="openstreetmap-telecom"), indicator_type: str = Query(default="communications-tower"), area: str = Query(default=""), date: str = Query(default=""), latitude: float | None = Query(default=None), longitude: float | None = Query(default=None)):
    try: return build_digital_connectivity_export_manifest(source,indicator_type,area,date,latitude,longitude)
    except (ValueError,TypeError) as exc: raise HTTPException(status_code=400,detail=str(exc))
@app.get("/public/digital-connectivity/readiness")
def public_digital_connectivity_readiness(): return build_digital_connectivity_readiness()

@app.get("/public/industrial-manufacturing")
def public_industrial_manufacturing_overview(): return build_industrial_manufacturing_overview()
@app.get("/public/industrial-manufacturing/catalog")
def public_industrial_manufacturing_catalog(): return build_industrial_manufacturing_catalog()
@app.get("/public/industrial-manufacturing/state")
def public_industrial_manufacturing_state(source: str = Query(default="openstreetmap-industrial"), indicator_type: str = Query(default="industrial-site"), area: str = Query(default=""), date: str = Query(default=""), latitude: float | None = Query(default=None), longitude: float | None = Query(default=None)):
    try: return build_industrial_manufacturing_state(source,indicator_type,area,date,latitude,longitude)
    except (ValueError,TypeError) as exc: raise HTTPException(status_code=400,detail=str(exc))
@app.post("/public/industrial-manufacturing/feature/normalize")
def public_industrial_manufacturing_feature_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_industrial_manufacturing_normalize_feature(request)
    except (ValueError,TypeError) as exc: raise HTTPException(status_code=400,detail=str(exc))
@app.post("/public/industrial-manufacturing/series/normalize")
def public_industrial_manufacturing_series_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_industrial_manufacturing_normalize_series(request)
    except (ValueError,TypeError) as exc: raise HTTPException(status_code=400,detail=str(exc))
@app.post("/public/industrial-manufacturing/trade-flow/normalize")
def public_industrial_manufacturing_trade_flow_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_industrial_manufacturing_normalize_trade_flow(request)
    except (ValueError,TypeError) as exc: raise HTTPException(status_code=400,detail=str(exc))
@app.post("/public/industrial-manufacturing/threshold/preview")
def public_industrial_manufacturing_threshold_preview(request: dict[str, Any] = Body(default={})):
    try: return build_industrial_manufacturing_threshold_preview(request)
    except (ValueError,TypeError) as exc: raise HTTPException(status_code=400,detail=str(exc))
@app.get("/public/industrial-manufacturing/export-manifest")
def public_industrial_manufacturing_manifest(source: str = Query(default="openstreetmap-industrial"), indicator_type: str = Query(default="industrial-site"), area: str = Query(default=""), date: str = Query(default=""), latitude: float | None = Query(default=None), longitude: float | None = Query(default=None)):
    try: return build_industrial_manufacturing_export_manifest(source,indicator_type,area,date,latitude,longitude)
    except (ValueError,TypeError) as exc: raise HTTPException(status_code=400,detail=str(exc))
@app.get("/public/industrial-manufacturing/readiness")
def public_industrial_manufacturing_readiness(): return build_industrial_manufacturing_readiness()

@app.get("/public/mining-critical-materials")
def public_mining_overview(): return build_mining_overview()
@app.get("/public/mining-critical-materials/catalog")
def public_mining_catalog(): return build_mining_catalog()
@app.get("/public/mining-critical-materials/state")
def public_mining_state(source: str = Query(default="openstreetmap-mining"), indicator_type: str = Query(default="mine-site"), area: str = Query(default=""), date: str = Query(default=""), latitude: float | None = Query(default=None), longitude: float | None = Query(default=None)):
    try: return build_mining_state(source,indicator_type,area,date,latitude,longitude)
    except (ValueError,TypeError) as exc: raise HTTPException(status_code=400,detail=str(exc))
@app.post("/public/mining-critical-materials/feature/normalize")
def public_mining_feature_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_mining_normalize_feature(request)
    except (ValueError,TypeError) as exc: raise HTTPException(status_code=400,detail=str(exc))
@app.post("/public/mining-critical-materials/resource/normalize")
def public_mining_resource_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_mining_normalize_resource(request)
    except (ValueError,TypeError) as exc: raise HTTPException(status_code=400,detail=str(exc))
@app.post("/public/mining-critical-materials/series/normalize")
def public_mining_series_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_mining_normalize_series(request)
    except (ValueError,TypeError) as exc: raise HTTPException(status_code=400,detail=str(exc))
@app.post("/public/mining-critical-materials/threshold/preview")
def public_mining_threshold_preview(request: dict[str, Any] = Body(default={})):
    try: return build_mining_threshold_preview(request)
    except (ValueError,TypeError) as exc: raise HTTPException(status_code=400,detail=str(exc))
@app.get("/public/mining-critical-materials/export-manifest")
def public_mining_manifest(source: str = Query(default="openstreetmap-mining"), indicator_type: str = Query(default="mine-site"), area: str = Query(default=""), date: str = Query(default=""), latitude: float | None = Query(default=None), longitude: float | None = Query(default=None)):
    try: return build_mining_export_manifest(source,indicator_type,area,date,latitude,longitude)
    except (ValueError,TypeError) as exc: raise HTTPException(status_code=400,detail=str(exc))
@app.get("/public/mining-critical-materials/readiness")
def public_mining_readiness(): return build_mining_readiness()

@app.get("/public/wetlands-inland-water")
def public_wetlands_overview(): return build_wetlands_overview()
@app.get("/public/wetlands-inland-water/catalog")
def public_wetlands_catalog(): return build_wetlands_catalog()
@app.get("/public/wetlands-inland-water/state")
def public_wetlands_state(source: str = Query(default="usfws-nwi"), indicator_type: str = Query(default="wetland-classification"), latitude: float | None = Query(default=None), longitude: float | None = Query(default=None), date: str = Query(default="")):
    try: return build_wetlands_state(source,indicator_type,latitude,longitude,date)
    except (ValueError,TypeError) as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc
@app.post("/public/wetlands-inland-water/feature/normalize")
def public_wetlands_feature_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_wetlands_normalize_feature(request)
    except (ValueError,TypeError) as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc
@app.post("/public/wetlands-inland-water/measurement/normalize")
def public_wetlands_measurement_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_wetlands_normalize_measurement(request)
    except (ValueError,TypeError) as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc
@app.post("/public/wetlands-inland-water/overlap/preview")
def public_wetlands_overlap_preview(request: dict[str, Any] = Body(default={})):
    try: return build_wetlands_overlap_preview(request)
    except (ValueError,TypeError) as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc
@app.get("/public/wetlands-inland-water/export-manifest")
def public_wetlands_manifest(source: str = Query(default="usfws-nwi"), indicator_type: str = Query(default="wetland-classification"), latitude: float | None = Query(default=None), longitude: float | None = Query(default=None), date: str = Query(default="")):
    try: return build_wetlands_export_manifest(source,indicator_type,latitude,longitude,date)
    except (ValueError,TypeError) as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc
@app.get("/public/wetlands-inland-water/readiness")
def public_wetlands_readiness(): return build_wetlands_readiness()

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


@app.get("/public/scientific-earth-systems/discovery")
def public_scientific_earth_systems_discovery(settings: Settings = Depends(get_settings)):
    from .scientific_earth_systems_observatory import build_science_discovery
    return build_science_discovery(settings)


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


# Site Intelligence v4.35.23 — Typed Cross-Platform Intelligence Workflows.
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


# Site Intelligence v4.35.23 — Open Standards, Federation, and Institutional Data Exchange.
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


# Site Intelligence v4.35.23 — Security, Privacy, Governance, and Production Scale.
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

# Site Intelligence v4.35.23 — Connected Live Intelligence Surface.
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
    channel: str = Query(default="", max_length=100),
    region: str = Query(default="", max_length=100),
    country: str = Query(default="", max_length=100),
    settings: Settings = Depends(get_settings),
):
    try:
        return build_live_intelligence(
            settings,
            category=category,
            limit=limit,
            feeds=feeds,
            exclude=exclude,
            max_per_source=max_per_source,
            channel=channel,
            region=region,
            country=country,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Live Intelligence channel not found.") from exc


@app.get("/public/live-intelligence/homepage")
def public_live_intelligence_homepage_endpoint(
    category: str = Query(default="", max_length=80),
    limit: int = Query(default=DEFAULT_HOMEPAGE_SIGNAL_LIMIT, ge=1, le=MAX_HOMEPAGE_SIGNAL_LIMIT),
    feeds: str = Query(default="", max_length=320),
    exclude: str = Query(default="", max_length=320),
    max_per_source: int = Query(default=2, ge=1, le=5),
    channel: str = Query(default="global", max_length=100),
    region: str = Query(default="", max_length=100),
    country: str = Query(default="", max_length=100),
    settings: Settings = Depends(get_settings),
):
    try:
        payload = build_live_intelligence(
            settings, category=category, limit=24, feeds=feeds, exclude=exclude,
            max_per_source=max_per_source, channel=channel, region=region, country=country,
        )
        gateway = apply_live_intelligence_gateway_policy(payload, surface="homepage")
        result = apply_live_intelligence_rotation_policy(
            gateway, settings, limit=limit, surface="homepage", record_history=True,
        )
        result = apply_connected_surface_policy(result, "homepage", limit=limit)
        result["measurement"] = {
            "enabled": bool(settings.live_intelligence_analytics_enabled),
            "policy_url": "/public/live-intelligence/analytics-policy",
            "event_url": "/public/live-intelligence/analytics/events",
            "summary_url": "/public/live-intelligence/analytics/summary",
            "source_reliability_url": "/public/live-intelligence/analytics/source-reliability",
            "aggregate_counters_only": True,
            "individual_user_tracking": False,
            "click_through_rate_only": False,
        }
        return result
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Live Intelligence channel not found.") from exc


@app.get("/public/site-intelligence/summary")
@app.get("/v1/public/site-intelligence/summary")
def public_site_intelligence_homepage_summary_endpoint(settings: Settings = Depends(get_settings)):
    """Return a bounded homepage payload; no full-application bootstrap is required."""
    try:
        payload = build_live_intelligence(settings, limit=8, channel="global", max_per_source=2)
        payload = apply_live_intelligence_gateway_policy(payload, surface="homepage")
        payload = apply_live_intelligence_rotation_policy(payload, settings, limit=4, surface="homepage", record_history=False)
        payload = apply_connected_surface_policy(payload, "homepage", limit=4)
    except Exception:
        # The endpoint itself remains truthful and useful when every upstream feed
        # is unavailable; no live records or health claims are manufactured.
        payload = {"signals": [], "generated_at": datetime.now(timezone.utc).isoformat(), "gateway": {}}
    return build_homepage_summary(payload)


@app.get("/public/live-intelligence/status")
def public_live_intelligence_status_endpoint(settings: Settings = Depends(get_settings)):
    return live_intelligence_status(settings)


@app.get("/public/live-intelligence/gateway-policy")
def public_live_intelligence_gateway_policy_endpoint():
    return live_intelligence_gateway_policy()


@app.get("/public/live-intelligence/rotation-policy")
def public_live_intelligence_rotation_policy_endpoint():
    return live_intelligence_rotation_policy()


@app.get("/public/live-intelligence/rotation-status")
def public_live_intelligence_rotation_status_endpoint(settings: Settings = Depends(get_settings)):
    return {
        "ok": True,
        "version": APP_VERSION,
        "rotation": LiveIntelligenceRotationStore(settings).status(),
        "policy_url": "/public/live-intelligence/rotation-policy",
    }


@app.get("/public/live-intelligence/analytics-policy")
def public_live_intelligence_analytics_policy_endpoint():
    return live_intelligence_analytics_policy()


@app.post("/public/live-intelligence/analytics/events", status_code=202)
def public_live_intelligence_analytics_events_endpoint(
    request: dict = Body(default={}),
    settings: Settings = Depends(get_settings),
):
    if not settings.live_intelligence_analytics_enabled:
        raise HTTPException(status_code=404, detail="Live Intelligence analytics are disabled.")
    events = request.get("events") if isinstance(request.get("events"), list) else []
    try:
        receipt = LiveIntelligenceAnalyticsStore(settings).record(events)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "version": APP_VERSION, "receipt": receipt}


@app.get("/public/live-intelligence/analytics/summary")
def public_live_intelligence_analytics_summary_endpoint(
    days: int = Query(default=30, ge=1, le=365),
    settings: Settings = Depends(get_settings),
):
    if not settings.live_intelligence_analytics_enabled:
        raise HTTPException(status_code=404, detail="Live Intelligence analytics are disabled.")
    return LiveIntelligenceAnalyticsStore(settings).summary(days=days, include_signals=False)


@app.get("/public/live-intelligence/analytics/source-reliability")
def public_live_intelligence_analytics_source_reliability_endpoint(
    days: int = Query(default=30, ge=1, le=365),
    settings: Settings = Depends(get_settings),
):
    if not settings.live_intelligence_analytics_enabled:
        raise HTTPException(status_code=404, detail="Live Intelligence analytics are disabled.")
    summary = LiveIntelligenceAnalyticsStore(settings).summary(days=days, include_signals=False)
    engagement = {item["source_id"]: item for item in summary["source_reliability"]}
    registry = _live_source_operations(settings).registry(public=True)
    sources = []
    for source in registry.get("sources") or []:
        source_id = str(source.get("feed_id") or "unknown")
        observed = engagement.pop(source_id, {
            "source_id": source_id, "signal_impressions": 0, "source_opens": 0,
            "successful_loads": 0, "failed_loads": 0, "observed_load_success_rate": None,
        })
        health = source.get("health") or {}
        runtime = source.get("runtime") or {}
        sources.append({
            **observed,
            "label": source.get("label") or source_id,
            "provider": source.get("provider") or "",
            "enabled": bool((source.get("effective") or {}).get("enabled")),
            "operational_state": health.get("state") or "unknown",
            "operational_freshness": health.get("freshness") or "unknown",
            "age_minutes": health.get("age_minutes"),
            "due": bool(health.get("due")),
            "last_success_at": runtime.get("last_success_at"),
            "consecutive_failures": int(runtime.get("consecutive_failures") or 0),
            "interpretation": "Operational source health plus aggregate public engagement; not a contractual service-level agreement.",
        })
    sources.extend(engagement.values())
    return {
        "ok": True, "version": APP_VERSION, "schema": summary["schema"],
        "window_days": summary["window_days"], "updated_at": summary["updated_at"],
        "sources": sources, "source_summary": registry.get("summary") or {}, "delivery": summary["delivery"],
        "boundary": "Operational source receipts and aggregate engagement only; no visitor profiles and no upstream SLA claim.",
    }


def _connected_live_intelligence_surface_feed(
    surface_id: str, *, category: str, limit: int, feeds: str, exclude: str,
    max_per_source: int, channel: str, region: str, country: str, settings: Settings,
):
    definition = live_intelligence_surface_definition(surface_id)
    effective_limit = limit or int(definition["default_limit"])
    effective_limit = max(1, min(effective_limit, int(definition["maximum_limit"])))
    effective_channel = channel or str(definition["default_channel"])
    payload = build_live_intelligence(
        settings, category=category, limit=24, feeds=feeds, exclude=exclude,
        max_per_source=max_per_source, channel=effective_channel, region=region, country=country,
    )
    gateway = apply_live_intelligence_gateway_policy(payload, surface=surface_id)
    rotated = apply_live_intelligence_rotation_policy(
        gateway, settings, limit=max(effective_limit, 12), surface=surface_id,
        record_history=bool(definition["record_rotation_history"]),
    )
    result = apply_connected_surface_policy(rotated, surface_id, limit=effective_limit)
    result["measurement"] = {
        "enabled": bool(settings.live_intelligence_analytics_enabled),
        "event_url": "/public/live-intelligence/analytics/events",
        "surface": surface_id, "aggregate_counters_only": True,
        "individual_user_tracking": False,
    }
    return result


def _live_intelligence_subscriptions(settings: Settings) -> LiveIntelligenceSubscriptionCenter:
    if not settings.live_intelligence_subscriptions_enabled:
        raise HTTPException(status_code=404, detail="Live Intelligence subscriptions are disabled.")

    def load_signals(watchlist: dict[str, Any]):
        return _connected_live_intelligence_surface_feed(
            str(watchlist.get("surface") or "homepage"), category="", limit=24, feeds="", exclude="",
            max_per_source=5, channel=str(watchlist.get("channel") or "global"),
            region=str(watchlist.get("region") or ""), country=str(watchlist.get("country") or ""),
            settings=settings,
        )

    return LiveIntelligenceSubscriptionCenter(settings, signal_loader=load_signals)


def _live_intelligence_briefings(settings: Settings) -> LiveIntelligenceBriefingCenter:
    if not settings.live_intelligence_briefings_enabled:
        raise HTTPException(status_code=404, detail="Live Intelligence briefings are disabled.")

    subscriptions = _live_intelligence_subscriptions(settings)

    def load_sources(request: Mapping[str, Any]):
        if isinstance(request.get("signals"), list) and request.get("signals"):
            return {"signals": []}
        surface = str(request.get("surface") or "publication")
        channel = str(request.get("channel") or "global")
        region = str(request.get("region") or "")
        country = str(request.get("country") or "")
        payload = _connected_live_intelligence_surface_feed(
            surface, category="", limit=24, feeds="", exclude="", max_per_source=5,
            channel=channel, region=region, country=country, settings=settings,
        )
        signals = [row for row in payload.get("signals", []) if isinstance(row, Mapping)]
        requested = {str(value) for value in request.get("signal_ids", []) if str(value).strip()} if isinstance(request.get("signal_ids"), list) else set()
        if requested:
            signals = [row for row in signals if str(row.get("signal_id") or row.get("event_id") or "") in requested]
        limit = max(1, min(int(request.get("source_limit", 12)), 24))
        return {"signals": signals[:limit]}

    return LiveIntelligenceBriefingCenter(
        settings, source_loader=load_sources, subscription_center=subscriptions,
    )


def _live_intelligence_editorial(settings: Settings) -> LiveIntelligenceEditorialWorkspace:
    if not settings.live_intelligence_editorial_enabled:
        raise HTTPException(status_code=404, detail="Live Intelligence editorial workspaces are disabled.")
    return LiveIntelligenceEditorialWorkspace(settings, briefing_center=_live_intelligence_briefings(settings))


def _live_intelligence_publication_releases(settings: Settings) -> LiveIntelligencePublicationReleaseCenter:
    if not settings.live_intelligence_publication_releases_enabled:
        raise HTTPException(status_code=404, detail="Live Intelligence publication releases are disabled.")
    briefings = _live_intelligence_briefings(settings)
    editorial = LiveIntelligenceEditorialWorkspace(settings, briefing_center=briefings)
    return LiveIntelligencePublicationReleaseCenter(
        settings, editorial_center=editorial, briefing_center=briefings,
    )


def _live_intelligence_release_operations(settings: Settings) -> LiveIntelligenceReleaseOperationsCenter:
    if not settings.live_intelligence_release_operations_enabled:
        raise HTTPException(status_code=404, detail="Live Intelligence release operations are disabled.")
    return LiveIntelligenceReleaseOperationsCenter(
        settings, publication_center=_live_intelligence_publication_releases(settings),
    )


def _live_intelligence_change_history(settings: Settings) -> LiveIntelligenceChangeHistoryCenter:
    if not settings.live_intelligence_change_history_enabled:
        raise HTTPException(status_code=404, detail="Live Intelligence change history is disabled.")
    publications = _live_intelligence_publication_releases(settings)
    operations = LiveIntelligenceReleaseOperationsCenter(settings, publication_center=publications)
    return LiveIntelligenceChangeHistoryCenter(
        settings, release_operations_center=operations, publication_center=publications,
    )


def _live_intelligence_public_archive(settings: Settings) -> LiveIntelligencePublicArchive:
    if not settings.live_intelligence_public_archive_enabled:
        raise HTTPException(status_code=404, detail="Live Intelligence public archive is disabled.")
    publications = _live_intelligence_publication_releases(settings)
    briefings = _live_intelligence_briefings(settings)
    operations = LiveIntelligenceReleaseOperationsCenter(settings, publication_center=publications)
    change_history = LiveIntelligenceChangeHistoryCenter(
        settings, release_operations_center=operations, publication_center=publications,
    )
    return LiveIntelligencePublicArchive(
        settings, publication_center=publications, change_history_center=change_history, briefing_center=briefings,
    )

def _live_intelligence_archive_audits(settings: Settings) -> LiveIntelligenceArchiveAuditCenter:
    if not settings.live_intelligence_archive_audits_enabled:
        raise HTTPException(status_code=404, detail="Live Intelligence archive audits are disabled.")
    return LiveIntelligenceArchiveAuditCenter(
        settings, archive_center=_live_intelligence_public_archive(settings),
    )


def _live_intelligence_preservation_exchange(settings: Settings) -> LiveIntelligencePreservationExchangeCenter:
    if not settings.live_intelligence_preservation_exchange_enabled:
        raise HTTPException(status_code=404, detail="Live Intelligence preservation exchange is disabled.")
    return LiveIntelligencePreservationExchangeCenter(
        settings, custody_center=_live_intelligence_archive_audits(settings),
    )


def _live_intelligence_federated_registry(settings: Settings) -> LiveIntelligenceFederatedPreservationRegistry:
    if not settings.live_intelligence_preservation_registry_enabled:
        raise HTTPException(status_code=404, detail="Live Intelligence preservation registry is disabled.")
    return LiveIntelligenceFederatedPreservationRegistry(
        settings, exchange_center=_live_intelligence_preservation_exchange(settings),
    )


def _live_intelligence_registry_governance(settings: Settings) -> LiveIntelligenceRegistryGovernanceCenter:
    if not settings.live_intelligence_registry_governance_enabled:
        raise HTTPException(status_code=404, detail="Live Intelligence registry governance is disabled.")
    return LiveIntelligenceRegistryGovernanceCenter(
        settings, registry_center=_live_intelligence_federated_registry(settings),
    )


def _live_intelligence_registry_discovery(settings: Settings) -> LiveIntelligenceRegistryDiscovery:
    if not settings.live_intelligence_registry_discovery_enabled:
        raise HTTPException(status_code=404, detail="Live Intelligence registry discovery is disabled.")
    exchange = _live_intelligence_preservation_exchange(settings)
    registry = LiveIntelligenceFederatedPreservationRegistry(settings, exchange_center=exchange)
    governance = LiveIntelligenceRegistryGovernanceCenter(settings, registry_center=registry)
    return LiveIntelligenceRegistryDiscovery(
        registry_center=registry, governance_center=governance, exchange_center=exchange,
    )

def _live_intelligence_registry_collections(settings: Settings) -> LiveIntelligenceRegistryCollectionsCenter:
    if not settings.live_intelligence_registry_collections_enabled:
        raise HTTPException(status_code=404, detail="Live Intelligence registry collections are disabled.")
    return LiveIntelligenceRegistryCollectionsCenter(
        settings, discovery=_live_intelligence_registry_discovery(settings),
    )


def _live_intelligence_registry_publications(settings: Settings) -> LiveIntelligenceRegistryPublicationCenter:
    if not settings.live_intelligence_registry_publications_enabled:
        raise HTTPException(status_code=404, detail="Live Intelligence registry publications are disabled.")
    return LiveIntelligenceRegistryPublicationCenter(
        settings, collections=_live_intelligence_registry_collections(settings),
    )


@app.get("/public/live-intelligence/surfaces")
def public_live_intelligence_surfaces_endpoint():
    return live_intelligence_surface_directory()


@app.get("/public/live-intelligence/surface-policy")
def public_live_intelligence_surface_policy_endpoint():
    return live_intelligence_surface_policy()


@app.get("/public/live-intelligence/surfaces/{surface_id}")
def public_live_intelligence_surface_endpoint(surface_id: str):
    try:
        return live_intelligence_surface_definition(surface_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Live Intelligence surface not found.") from exc


@app.get("/public/live-intelligence/surfaces/{surface_id}/feed")
def public_live_intelligence_surface_feed_endpoint(
    surface_id: str,
    category: str = Query(default="", max_length=80),
    limit: int = Query(default=0, ge=0, le=24),
    feeds: str = Query(default="", max_length=320),
    exclude: str = Query(default="", max_length=320),
    max_per_source: int = Query(default=2, ge=1, le=5),
    channel: str = Query(default="", max_length=100),
    region: str = Query(default="", max_length=100),
    country: str = Query(default="", max_length=100),
    settings: Settings = Depends(get_settings),
):
    try:
        normalized = normalize_live_intelligence_surface_id(surface_id)
        return _connected_live_intelligence_surface_feed(
            normalized, category=category, limit=limit, feeds=feeds, exclude=exclude,
            max_per_source=max_per_source, channel=channel, region=region, country=country, settings=settings,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Live Intelligence surface or channel not found.") from exc


@app.get("/public/live-intelligence/embed-manifest")
def public_live_intelligence_embed_manifest_endpoint(surface: str = Query(default="external_embed", max_length=80)):
    try:
        return live_intelligence_embed_manifest(surface)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Live Intelligence surface not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/public/live-intelligence/briefings/policy")
def public_live_intelligence_briefing_policy_endpoint():
    return live_intelligence_briefing_policy()


@app.get("/public/live-intelligence/briefings/templates")
def public_live_intelligence_briefing_templates_endpoint():
    return live_intelligence_briefing_templates()


@app.get("/public/live-intelligence/briefings")
def public_live_intelligence_briefings_endpoint(
    limit: int = Query(default=20, ge=1, le=100),
    settings: Settings = Depends(get_settings),
):
    rows = _live_intelligence_briefings(settings).briefings(public=True, limit=limit)
    return {"ok": True, "version": APP_VERSION, "count": len(rows), "briefings": rows, "automatic_publication": False}


@app.get("/public/live-intelligence/briefings/{briefing_id}")
def public_live_intelligence_briefing_detail_endpoint(briefing_id: str, settings: Settings = Depends(get_settings)):
    try:
        return {"ok": True, "version": APP_VERSION, "briefing": _live_intelligence_briefings(settings)._briefing(briefing_id, public=True)}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Published Live Intelligence briefing not found.") from exc


@app.get("/public/live-intelligence/briefings/{briefing_id}/export")
def public_live_intelligence_briefing_export_endpoint(
    briefing_id: str, format: str = Query(default="json", pattern="^(json|markdown)$"),
    settings: Settings = Depends(get_settings),
):
    try:
        media_type, body = _live_intelligence_briefings(settings).package_payload(briefing_id, format, public=True)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Published Live Intelligence briefing not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    suffix = "json" if format == "json" else "md"
    return Response(content=body, media_type=media_type, headers={"Content-Disposition": f'attachment; filename="live-intelligence-briefing-{briefing_id}.{suffix}"', "X-SC-Site-Intelligence-Version": APP_VERSION})


@app.get("/admin/live-intelligence/briefings")
def admin_live_intelligence_briefings_endpoint(settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    return _live_intelligence_briefings(settings).control_center()


@app.post("/admin/live-intelligence/briefings/drafts")
def admin_live_intelligence_briefing_draft_endpoint(
    request: dict[str, Any], settings: Settings = Depends(get_settings), _: None = Depends(require_token),
):
    try:
        return _live_intelligence_briefings(settings).create_draft(request)
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/live-intelligence/briefings/{briefing_id}/review")
def admin_live_intelligence_briefing_review_endpoint(
    briefing_id: str, request: dict[str, Any], settings: Settings = Depends(get_settings), _: None = Depends(require_token),
):
    try:
        return _live_intelligence_briefings(settings).review_briefing(briefing_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Live Intelligence briefing not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/admin/live-intelligence/briefings/{briefing_id}/export")
def admin_live_intelligence_briefing_export_endpoint(
    briefing_id: str, format: str = Query(default="json", pattern="^(json|markdown)$"),
    settings: Settings = Depends(get_settings), _: None = Depends(require_token),
):
    try:
        media_type, body = _live_intelligence_briefings(settings).package_payload(briefing_id, format, public=False)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Live Intelligence briefing not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    suffix = "json" if format == "json" else "md"
    return Response(content=body, media_type=media_type, headers={"Content-Disposition": f'attachment; filename="live-intelligence-briefing-{briefing_id}.{suffix}"', "X-SC-Site-Intelligence-Version": APP_VERSION})


@app.post("/admin/live-intelligence/briefings/{briefing_id}/handoff")
def admin_live_intelligence_briefing_handoff_endpoint(
    briefing_id: str, request: dict[str, Any], settings: Settings = Depends(get_settings), _: None = Depends(require_token),
):
    try:
        return _live_intelligence_briefings(settings).create_handoff(briefing_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Live Intelligence briefing not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/public/live-intelligence/editorial/policy")
def public_live_intelligence_editorial_policy_endpoint():
    return live_intelligence_editorial_policy()


@app.get("/public/live-intelligence/editorial/status")
def public_live_intelligence_editorial_status_endpoint(settings: Settings = Depends(get_settings)):
    return _live_intelligence_editorial(settings).status()


@app.get("/admin/live-intelligence/editorial")
def admin_live_intelligence_editorial_endpoint(settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    return _live_intelligence_editorial(settings).control_center()


@app.post("/admin/live-intelligence/editorial/workspaces")
def admin_live_intelligence_editorial_workspace_create_endpoint(
    request: dict[str, Any], settings: Settings = Depends(get_settings), _: None = Depends(require_token),
):
    try:
        return _live_intelligence_editorial(settings).create_workspace(request)
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/admin/live-intelligence/editorial/workspaces/{workspace_id}")
def admin_live_intelligence_editorial_workspace_endpoint(
    workspace_id: str, settings: Settings = Depends(get_settings), _: None = Depends(require_token),
):
    try:
        return {"ok": True, "version": APP_VERSION, "workspace": _live_intelligence_editorial(settings).workspace(workspace_id)}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Editorial workspace not found.") from exc


@app.post("/admin/live-intelligence/editorial/workspaces/{workspace_id}/assign")
def admin_live_intelligence_editorial_assign_endpoint(
    workspace_id: str, request: dict[str, Any], settings: Settings = Depends(get_settings), _: None = Depends(require_token),
):
    try:
        return _live_intelligence_editorial(settings).assign(workspace_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Editorial workspace not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/live-intelligence/editorial/workspaces/{workspace_id}/revisions")
def admin_live_intelligence_editorial_revision_endpoint(
    workspace_id: str, request: dict[str, Any], settings: Settings = Depends(get_settings), _: None = Depends(require_token),
):
    try:
        return _live_intelligence_editorial(settings).add_revision(workspace_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Editorial workspace not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/live-intelligence/editorial/workspaces/{workspace_id}/submit")
def admin_live_intelligence_editorial_submit_endpoint(
    workspace_id: str, request: dict[str, Any], settings: Settings = Depends(get_settings), _: None = Depends(require_token),
):
    try:
        return _live_intelligence_editorial(settings).submit_for_review(workspace_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Editorial workspace not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/live-intelligence/editorial/workspaces/{workspace_id}/review")
def admin_live_intelligence_editorial_review_endpoint(
    workspace_id: str, request: dict[str, Any], settings: Settings = Depends(get_settings), _: None = Depends(require_token),
):
    try:
        return _live_intelligence_editorial(settings).review(workspace_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Editorial workspace not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/live-intelligence/editorial/workspaces/{workspace_id}/orchestrate")
def admin_live_intelligence_editorial_orchestrate_endpoint(
    workspace_id: str, request: dict[str, Any], settings: Settings = Depends(get_settings), _: None = Depends(require_token),
):
    try:
        return _live_intelligence_editorial(settings).orchestrate(workspace_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Editorial workspace or briefing not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/admin/live-intelligence/editorial/workspaces/{workspace_id}/history")
def admin_live_intelligence_editorial_history_endpoint(
    workspace_id: str, limit: int = Query(default=200, ge=1, le=1000),
    settings: Settings = Depends(get_settings), _: None = Depends(require_token),
):
    return {"ok": True, "version": APP_VERSION, "history": _live_intelligence_editorial(settings).history(workspace_id, limit=limit)}


@app.get("/public/live-intelligence/publication-releases/policy")
def public_live_intelligence_publication_release_policy_endpoint():
    return live_intelligence_publication_release_policy()


@app.get("/public/live-intelligence/publication-releases/adapters")
def public_live_intelligence_publication_release_adapters_endpoint():
    return live_intelligence_publication_adapter_catalog()


@app.get("/public/live-intelligence/publication-releases/status")
def public_live_intelligence_publication_release_status_endpoint(settings: Settings = Depends(get_settings)):
    return _live_intelligence_publication_releases(settings).status()


@app.get("/admin/live-intelligence/publication-releases")
def admin_live_intelligence_publication_releases_endpoint(settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    return _live_intelligence_publication_releases(settings).control_center()


@app.post("/admin/live-intelligence/publication-releases/prepare")
def admin_live_intelligence_publication_release_prepare_endpoint(request: dict[str, Any], settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _live_intelligence_publication_releases(settings).prepare(request)
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/admin/live-intelligence/publication-releases/{release_id}")
def admin_live_intelligence_publication_release_endpoint(release_id: str, settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return {"ok": True, "version": APP_VERSION, "release": _live_intelligence_publication_releases(settings).release(release_id)}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Publication release not found.") from exc


@app.post("/admin/live-intelligence/publication-releases/{release_id}/validate")
def admin_live_intelligence_publication_release_validate_endpoint(release_id: str, request: dict[str, Any], settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _live_intelligence_publication_releases(settings).validate(release_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Publication release not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/live-intelligence/publication-releases/{release_id}/approve")
def admin_live_intelligence_publication_release_approve_endpoint(release_id: str, request: dict[str, Any], settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _live_intelligence_publication_releases(settings).approve(release_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Publication release not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/live-intelligence/publication-releases/{release_id}/handoffs")
def admin_live_intelligence_publication_release_handoff_endpoint(release_id: str, request: dict[str, Any], settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _live_intelligence_publication_releases(settings).create_handoff(release_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Publication release not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/admin/live-intelligence/publication-releases/{release_id}/package")
def admin_live_intelligence_publication_release_package_endpoint(release_id: str, format: str = Query(default="json", pattern="^(json|markdown)$"), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        media_type, body = _live_intelligence_publication_releases(settings).package_payload(release_id, format)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Publication release not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    suffix = "json" if format == "json" else "md"
    return Response(content=body, media_type=media_type, headers={"Content-Disposition": f'attachment; filename="live-intelligence-publication-release-{release_id}.{suffix}"', "X-SC-Site-Intelligence-Version": APP_VERSION})


@app.get("/admin/live-intelligence/publication-releases/{release_id}/history")
def admin_live_intelligence_publication_release_history_endpoint(release_id: str, limit: int = Query(default=200, ge=1, le=1000), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    return {"ok": True, "version": APP_VERSION, "history": _live_intelligence_publication_releases(settings).history(release_id, limit)}


@app.get("/public/live-intelligence/release-operations/policy")
def public_live_intelligence_release_operations_policy_endpoint():
    return live_intelligence_release_operations_policy()


@app.get("/public/live-intelligence/release-operations/status")
def public_live_intelligence_release_operations_status_endpoint(settings: Settings = Depends(get_settings)):
    return _live_intelligence_release_operations(settings).status()


@app.get("/public/live-intelligence/release-operations/corrections")
def public_live_intelligence_release_operations_corrections_endpoint(limit: int = Query(default=50, ge=1, le=200), settings: Settings = Depends(get_settings)):
    rows = _live_intelligence_release_operations(settings).public_corrections(limit)
    return {"ok": True, "version": APP_VERSION, "count": len(rows), "corrections": rows, "destination_write_performed": False}


@app.get("/admin/live-intelligence/release-operations")
def admin_live_intelligence_release_operations_endpoint(settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    return _live_intelligence_release_operations(settings).control_center()


@app.post("/admin/live-intelligence/release-operations/deployments")
def admin_live_intelligence_release_operations_deployment_endpoint(request: dict[str, Any], settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _live_intelligence_release_operations(settings).register_deployment(request)
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/live-intelligence/release-operations/deployments/{deployment_id}/verify")
def admin_live_intelligence_release_operations_verify_endpoint(deployment_id: str, request: dict[str, Any], settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _live_intelligence_release_operations(settings).verify_deployment(deployment_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Deployment receipt not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/live-intelligence/release-operations/issues")
def admin_live_intelligence_release_operations_issue_endpoint(request: dict[str, Any], settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _live_intelligence_release_operations(settings).report_issue(request)
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/live-intelligence/release-operations/issues/{issue_id}/corrections")
def admin_live_intelligence_release_operations_correction_endpoint(issue_id: str, request: dict[str, Any], settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _live_intelligence_release_operations(settings).propose_correction(issue_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Post-publication issue not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/live-intelligence/release-operations/corrections/{correction_id}/approve")
def admin_live_intelligence_release_operations_correction_approve_endpoint(correction_id: str, request: dict[str, Any], settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _live_intelligence_release_operations(settings).approve_correction(correction_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Correction package not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/live-intelligence/release-operations/deployments/{deployment_id}/rollbacks")
def admin_live_intelligence_release_operations_rollback_endpoint(deployment_id: str, request: dict[str, Any], settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _live_intelligence_release_operations(settings).prepare_rollback(deployment_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Deployment receipt or target release not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/live-intelligence/release-operations/rollbacks/{rollback_id}/approve")
def admin_live_intelligence_release_operations_rollback_approve_endpoint(rollback_id: str, request: dict[str, Any], settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _live_intelligence_release_operations(settings).approve_rollback(rollback_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Rollback package not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/live-intelligence/release-operations/{entity_type}/{entity_id}/handoffs")
def admin_live_intelligence_release_operations_handoff_endpoint(entity_type: str, entity_id: str, request: dict[str, Any], settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _live_intelligence_release_operations(settings).create_handoff(entity_type, entity_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Release-operation entity not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/admin/live-intelligence/release-operations/{entity_id}/history")
def admin_live_intelligence_release_operations_history_endpoint(entity_id: str, limit: int = Query(default=200, ge=1, le=1000), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    return {"ok": True, "version": APP_VERSION, "history": _live_intelligence_release_operations(settings).history(entity_id, limit)}


@app.get("/public/live-intelligence/change-history/policy")
def public_live_intelligence_change_history_policy_endpoint():
    return live_intelligence_change_history_policy()


@app.get("/public/live-intelligence/change-history/status")
def public_live_intelligence_change_history_status_endpoint(settings: Settings = Depends(get_settings)):
    return _live_intelligence_change_history(settings).status()


@app.get("/public/live-intelligence/change-history")
def public_live_intelligence_change_history_endpoint(
    limit: int = Query(default=50, ge=1, le=500),
    release_id: str = Query(default="", max_length=180),
    notice_type: str = Query(default="", max_length=40),
    settings: Settings = Depends(get_settings),
):
    try:
        return {"ok": True, "version": APP_VERSION, "history": _live_intelligence_change_history(settings).public_history(limit, release_id=release_id, notice_type=notice_type)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/public/live-intelligence/change-history/releases/{release_id}")
def public_live_intelligence_release_lineage_endpoint(release_id: str, settings: Settings = Depends(get_settings)):
    try:
        return _live_intelligence_change_history(settings).release_lineage(release_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Publication release not found.") from exc


@app.get("/admin/live-intelligence/change-history")
def admin_live_intelligence_change_history_endpoint(settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    return _live_intelligence_change_history(settings).control_center()


@app.post("/admin/live-intelligence/change-history/notices")
def admin_live_intelligence_change_history_prepare_endpoint(request: dict[str, Any], settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _live_intelligence_change_history(settings).prepare_notice(request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Approved correction or publication release not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/live-intelligence/change-history/notices/{notice_id}/approve")
def admin_live_intelligence_change_history_approve_endpoint(notice_id: str, request: dict[str, Any], settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _live_intelligence_change_history(settings).approve_notice(notice_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Public change notice not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/admin/live-intelligence/change-history/notices/{notice_id}/package")
def admin_live_intelligence_change_history_package_endpoint(
    notice_id: str, format: str = Query(default="json", pattern="^(json|markdown)$"),
    settings: Settings = Depends(get_settings), _: None = Depends(require_token),
):
    try:
        media_type, body = _live_intelligence_change_history(settings).package_payload(notice_id, format)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Public change notice not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    suffix = "json" if format == "json" else "md"
    return Response(content=body, media_type=media_type, headers={"Content-Disposition": f'attachment; filename="live-intelligence-change-notice-{notice_id}.{suffix}"', "X-SC-Site-Intelligence-Version": APP_VERSION})


@app.post("/admin/live-intelligence/change-history/notices/{notice_id}/handoffs")
def admin_live_intelligence_change_history_handoff_endpoint(notice_id: str, request: dict[str, Any], settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _live_intelligence_change_history(settings).create_handoff(notice_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Public change notice not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/admin/live-intelligence/change-history/{entity_id}/history")
def admin_live_intelligence_change_history_events_endpoint(entity_id: str, limit: int = Query(default=200, ge=1, le=1000), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    return {"ok": True, "version": APP_VERSION, "history": _live_intelligence_change_history(settings).history(entity_id, limit)}


@app.get("/public/live-intelligence/archive/policy")
def public_live_intelligence_archive_policy_endpoint():
    return live_intelligence_public_archive_policy()


@app.get("/public/live-intelligence/archive/status")
def public_live_intelligence_archive_status_endpoint(settings: Settings = Depends(get_settings)):
    return _live_intelligence_public_archive(settings).status()


@app.get("/public/live-intelligence/archive")
def public_live_intelligence_archive_endpoint(
    limit: int = Query(default=50, ge=1, le=500),
    settings: Settings = Depends(get_settings),
):
    rows = _live_intelligence_public_archive(settings).records(public=True, limit=limit)
    return {"ok": True, "version": APP_VERSION, "count": len(rows), "records": rows, "append_only_ledger": True}


@app.get("/public/live-intelligence/archive/{archive_id}")
def public_live_intelligence_archive_record_endpoint(archive_id: str, settings: Settings = Depends(get_settings)):
    try:
        record = _live_intelligence_public_archive(settings).record(archive_id, public=True)
        verification = _live_intelligence_public_archive(settings).verify_public_record(archive_id)
        return {"ok": True, "version": APP_VERSION, "record": record, "verification": verification}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Public archive record not found.") from exc


@app.get("/public/live-intelligence/archive/sources/{source_id:path}")
def public_live_intelligence_archive_lineage_endpoint(source_id: str, settings: Settings = Depends(get_settings)):
    return _live_intelligence_public_archive(settings).public_lineage(source_id)


@app.get("/admin/live-intelligence/archive")
def admin_live_intelligence_archive_endpoint(settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    center = _live_intelligence_public_archive(settings)
    return {"ok": True, "version": APP_VERSION, "status": center.status(), "records": center.records(limit=500)}


@app.post("/admin/live-intelligence/archive/records")
def admin_live_intelligence_archive_create_endpoint(request: dict[str, Any], settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _live_intelligence_public_archive(settings).create_record(request)
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/live-intelligence/archive/records/{archive_id}/verify")
def admin_live_intelligence_archive_verify_endpoint(archive_id: str, request: dict[str, Any], settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _live_intelligence_public_archive(settings).verify_record(archive_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Archive record not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/live-intelligence/archive/records/{archive_id}/approve")
def admin_live_intelligence_archive_approve_endpoint(archive_id: str, request: dict[str, Any], settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _live_intelligence_public_archive(settings).approve_record(archive_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Archive record not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/admin/live-intelligence/archive/records/{archive_id}/package")
def admin_live_intelligence_archive_package_endpoint(
    archive_id: str, format: str = Query(default="json", pattern="^(json|markdown)$"),
    settings: Settings = Depends(get_settings), _: None = Depends(require_token),
):
    try:
        media_type, body = _live_intelligence_public_archive(settings).package_payload(archive_id, format)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Archive record not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    suffix = "json" if format == "json" else "md"
    return Response(content=body, media_type=media_type, headers={"Content-Disposition": f'attachment; filename="live-intelligence-public-archive-{archive_id}.{suffix}"', "X-SC-Site-Intelligence-Version": APP_VERSION})


@app.post("/admin/live-intelligence/archive/records/{archive_id}/handoffs")
def admin_live_intelligence_archive_handoff_endpoint(archive_id: str, request: dict[str, Any], settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _live_intelligence_public_archive(settings).create_handoff(archive_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Archive record not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/admin/live-intelligence/archive/{entity_id}/history")
def admin_live_intelligence_archive_history_endpoint(entity_id: str, limit: int = Query(default=200, ge=1, le=1000), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    return {"ok": True, "version": APP_VERSION, "history": _live_intelligence_public_archive(settings).history(entity_id, limit)}


@app.get("/public/live-intelligence/archive-audits/policy")
def public_live_intelligence_archive_audit_policy_endpoint():
    return live_intelligence_archive_audit_policy()


@app.get("/public/live-intelligence/archive-audits/status")
def public_live_intelligence_archive_audit_status_endpoint(settings: Settings = Depends(get_settings)):
    return _live_intelligence_archive_audits(settings).status()


@app.get("/public/live-intelligence/archive-audits")
def public_live_intelligence_archive_audits_endpoint(
    limit: int = Query(default=50, ge=1, le=500),
    settings: Settings = Depends(get_settings),
):
    rows = _live_intelligence_archive_audits(settings).audits(public=True, limit=limit)
    return {"ok": True, "version": APP_VERSION, "count": len(rows), "audits": rows, "append_only_audit_ledger": True}


@app.get("/public/live-intelligence/archive-audits/custody")
def public_live_intelligence_archive_custody_endpoint(
    limit: int = Query(default=50, ge=1, le=500),
    settings: Settings = Depends(get_settings),
):
    rows = _live_intelligence_archive_audits(settings).custody_transfers(public=True, limit=limit)
    return {"ok": True, "version": APP_VERSION, "count": len(rows), "transfers": rows, "remote_deposit_performed": False}


@app.get("/public/live-intelligence/archive-audits/{audit_id}")
def public_live_intelligence_archive_audit_endpoint(audit_id: str, settings: Settings = Depends(get_settings)):
    try:
        return {"ok": True, "version": APP_VERSION, "audit": _live_intelligence_archive_audits(settings).audit(audit_id, public=True)}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Public archive audit not found.") from exc


@app.get("/admin/live-intelligence/archive-audits")
def admin_live_intelligence_archive_audits_endpoint(settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    center = _live_intelligence_archive_audits(settings)
    return {"ok": True, "version": APP_VERSION, "status": center.status(), "audits": center.audits(limit=500), "custody_transfers": center.custody_transfers(limit=500)}


@app.post("/admin/live-intelligence/archive-audits")
def admin_live_intelligence_archive_audit_create_endpoint(request: dict[str, Any], settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _live_intelligence_archive_audits(settings).create_audit(request)
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/live-intelligence/archive-audits/{audit_id}/run")
def admin_live_intelligence_archive_audit_run_endpoint(audit_id: str, request: dict[str, Any], settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _live_intelligence_archive_audits(settings).run_audit(audit_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Archive audit not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/live-intelligence/archive-audits/{audit_id}/approve")
def admin_live_intelligence_archive_audit_approve_endpoint(audit_id: str, request: dict[str, Any], settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _live_intelligence_archive_audits(settings).approve_audit(audit_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Archive audit not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/admin/live-intelligence/archive-audits/{audit_id}/package")
def admin_live_intelligence_archive_audit_package_endpoint(
    audit_id: str, format: str = Query(default="json", pattern="^(json|markdown)$"),
    settings: Settings = Depends(get_settings), _: None = Depends(require_token),
):
    try:
        media_type, body = _live_intelligence_archive_audits(settings).report_payload(audit_id, format)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Archive audit not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    suffix = "json" if format == "json" else "md"
    return Response(content=body, media_type=media_type, headers={"Content-Disposition": f'attachment; filename="live-intelligence-archive-audit-{audit_id}.{suffix}"', "X-SC-Site-Intelligence-Version": APP_VERSION})


@app.post("/admin/live-intelligence/archive-audits/custody")
def admin_live_intelligence_archive_custody_create_endpoint(request: dict[str, Any], settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _live_intelligence_archive_audits(settings).prepare_custody_transfer(request)
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/live-intelligence/archive-audits/custody/{transfer_id}/verify")
def admin_live_intelligence_archive_custody_verify_endpoint(transfer_id: str, request: dict[str, Any], settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _live_intelligence_archive_audits(settings).verify_custody_transfer(transfer_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Custody transfer not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/live-intelligence/archive-audits/custody/{transfer_id}/approve")
def admin_live_intelligence_archive_custody_approve_endpoint(transfer_id: str, request: dict[str, Any], settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _live_intelligence_archive_audits(settings).approve_custody_transfer(transfer_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Custody transfer not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/live-intelligence/archive-audits/custody/{transfer_id}/receipts")
def admin_live_intelligence_archive_custody_receipt_endpoint(transfer_id: str, request: dict[str, Any], settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _live_intelligence_archive_audits(settings).record_custody_receipt(transfer_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Custody transfer not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/admin/live-intelligence/archive-audits/custody/{transfer_id}/package")
def admin_live_intelligence_archive_custody_package_endpoint(
    transfer_id: str, format: str = Query(default="json", pattern="^(json|markdown)$"),
    settings: Settings = Depends(get_settings), _: None = Depends(require_token),
):
    try:
        media_type, body = _live_intelligence_archive_audits(settings).custody_package_payload(transfer_id, format)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Custody transfer not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    suffix = "json" if format == "json" else "md"
    return Response(content=body, media_type=media_type, headers={"Content-Disposition": f'attachment; filename="live-intelligence-custody-{transfer_id}.{suffix}"', "X-SC-Site-Intelligence-Version": APP_VERSION})


@app.get("/admin/live-intelligence/archive-audits/{entity_id}/history")
def admin_live_intelligence_archive_audit_history_endpoint(entity_id: str, limit: int = Query(default=200, ge=1, le=1000), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    return {"ok": True, "version": APP_VERSION, "history": _live_intelligence_archive_audits(settings).history(entity_id, limit)}


@app.get("/public/live-intelligence/preservation-exchange/policy")
def public_live_intelligence_preservation_exchange_policy_endpoint():
    return live_intelligence_preservation_exchange_policy()


@app.get("/public/live-intelligence/preservation-exchange/status")
def public_live_intelligence_preservation_exchange_status_endpoint(settings: Settings = Depends(get_settings)):
    return _live_intelligence_preservation_exchange(settings).status()


@app.get("/public/live-intelligence/preservation-exchange/exchanges")
def public_live_intelligence_preservation_exchanges_endpoint(limit: int = Query(default=50, ge=1, le=500), settings: Settings = Depends(get_settings)):
    rows = _live_intelligence_preservation_exchange(settings).exchanges(public=True, limit=limit)
    return {"ok": True, "version": APP_VERSION, "count": len(rows), "exchanges": rows, "remote_deposit_performed": False}


@app.get("/public/live-intelligence/preservation-exchange/verifications")
def public_live_intelligence_preservation_verifications_endpoint(limit: int = Query(default=50, ge=1, le=500), settings: Settings = Depends(get_settings)):
    rows = _live_intelligence_preservation_exchange(settings).verifications(public=True, limit=limit)
    return {"ok": True, "version": APP_VERSION, "count": len(rows), "verifications": rows, "network_verification_performed": False}


@app.get("/public/live-intelligence/preservation-exchange/exchanges/{exchange_id}")
def public_live_intelligence_preservation_exchange_endpoint(exchange_id: str, settings: Settings = Depends(get_settings)):
    try:
        return {"ok": True, "version": APP_VERSION, "exchange": _live_intelligence_preservation_exchange(settings).exchange(exchange_id, public=True)}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Public preservation exchange not found.") from exc


@app.get("/admin/live-intelligence/preservation-exchange")
def admin_live_intelligence_preservation_exchange_endpoint(settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    center = _live_intelligence_preservation_exchange(settings)
    return {"ok": True, "version": APP_VERSION, "status": center.status(), "exchanges": center.exchanges(limit=500), "verifications": center.verifications(limit=500)}


@app.post("/admin/live-intelligence/preservation-exchange/exchanges")
def admin_live_intelligence_preservation_exchange_create_endpoint(request: dict[str, Any], settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _live_intelligence_preservation_exchange(settings).create_exchange(request)
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/live-intelligence/preservation-exchange/exchanges/{exchange_id}/verify")
def admin_live_intelligence_preservation_exchange_verify_endpoint(exchange_id: str, request: dict[str, Any], settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _live_intelligence_preservation_exchange(settings).verify_exchange(exchange_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Preservation exchange not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/live-intelligence/preservation-exchange/exchanges/{exchange_id}/approve")
def admin_live_intelligence_preservation_exchange_approve_endpoint(exchange_id: str, request: dict[str, Any], settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _live_intelligence_preservation_exchange(settings).approve_exchange(exchange_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Preservation exchange not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/live-intelligence/preservation-exchange/exchanges/{exchange_id}/verifications")
def admin_live_intelligence_preservation_exchange_verification_endpoint(exchange_id: str, request: dict[str, Any], settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _live_intelligence_preservation_exchange(settings).record_external_verification(exchange_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Preservation exchange not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/admin/live-intelligence/preservation-exchange/exchanges/{exchange_id}/package")
def admin_live_intelligence_preservation_exchange_package_endpoint(exchange_id: str, format: str = Query(default="json", pattern="^(json|markdown)$"), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        media_type, body = _live_intelligence_preservation_exchange(settings).package_payload(exchange_id, format)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Preservation exchange not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    suffix = "json" if format == "json" else "md"
    return Response(content=body, media_type=media_type, headers={"Content-Disposition": f'attachment; filename="live-intelligence-preservation-exchange-{exchange_id}.{suffix}"', "X-SC-Site-Intelligence-Version": APP_VERSION})


@app.get("/admin/live-intelligence/preservation-exchange/verifications/{verification_id}/package")
def admin_live_intelligence_preservation_verification_package_endpoint(verification_id: str, format: str = Query(default="json", pattern="^(json|markdown)$"), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        media_type, body = _live_intelligence_preservation_exchange(settings).verification_payload(verification_id, format)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="External verification receipt not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    suffix = "json" if format == "json" else "md"
    return Response(content=body, media_type=media_type, headers={"Content-Disposition": f'attachment; filename="live-intelligence-external-verification-{verification_id}.{suffix}"', "X-SC-Site-Intelligence-Version": APP_VERSION})


@app.get("/admin/live-intelligence/preservation-exchange/{entity_id}/history")
def admin_live_intelligence_preservation_exchange_history_endpoint(entity_id: str, limit: int = Query(default=200, ge=1, le=1000), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    return {"ok": True, "version": APP_VERSION, "history": _live_intelligence_preservation_exchange(settings).history(entity_id, limit)}


@app.get("/public/live-intelligence/preservation-registry/policy")
def public_live_intelligence_preservation_registry_policy_endpoint():
    return live_intelligence_federated_registry_policy()


@app.get("/public/live-intelligence/preservation-registry/status")
def public_live_intelligence_preservation_registry_status_endpoint(settings: Settings = Depends(get_settings)):
    return _live_intelligence_federated_registry(settings).status()


@app.get("/public/live-intelligence/preservation-registry/institutions")
def public_live_intelligence_preservation_registry_institutions_endpoint(limit: int = Query(default=50, ge=1, le=500), settings: Settings = Depends(get_settings)):
    rows = _live_intelligence_federated_registry(settings).institutions(public=True, limit=limit)
    return {"ok": True, "version": APP_VERSION, "count": len(rows), "institutions": rows, "certification_claimed": False}


@app.get("/public/live-intelligence/preservation-registry/institutions/{institution_id}")
def public_live_intelligence_preservation_registry_institution_endpoint(institution_id: str, settings: Settings = Depends(get_settings)):
    try:
        return {"ok": True, "version": APP_VERSION, "institution": _live_intelligence_federated_registry(settings).institution(institution_id, public=True)}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Public preservation institution not found.") from exc


@app.get("/public/live-intelligence/preservation-registry/attestations")
def public_live_intelligence_preservation_registry_attestations_endpoint(limit: int = Query(default=50, ge=1, le=500), settings: Settings = Depends(get_settings)):
    rows = _live_intelligence_federated_registry(settings).attestations(public=True, limit=limit)
    return {"ok": True, "version": APP_VERSION, "count": len(rows), "attestations": rows, "network_verification_performed": False}


@app.get("/public/live-intelligence/preservation-registry/exchanges/{exchange_id}/consensus")
def public_live_intelligence_preservation_registry_consensus_endpoint(exchange_id: str, settings: Settings = Depends(get_settings)):
    try:
        return {"ok": True, "version": APP_VERSION, "consensus": _live_intelligence_federated_registry(settings).consensus(exchange_id, public=True)}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Public preservation exchange consensus not found.") from exc


@app.get("/admin/live-intelligence/preservation-registry")
def admin_live_intelligence_preservation_registry_endpoint(settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    center = _live_intelligence_federated_registry(settings)
    return {"ok": True, "version": APP_VERSION, "status": center.status(), "institutions": center.institutions(limit=500), "attestations": center.attestations(limit=500)}


@app.post("/admin/live-intelligence/preservation-registry/institutions")
def admin_live_intelligence_preservation_registry_create_institution_endpoint(request: dict[str, Any], settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _live_intelligence_federated_registry(settings).create_institution(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/live-intelligence/preservation-registry/institutions/{institution_id}/verify")
def admin_live_intelligence_preservation_registry_verify_institution_endpoint(institution_id: str, request: dict[str, Any], settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _live_intelligence_federated_registry(settings).verify_institution(institution_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Preservation institution not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/live-intelligence/preservation-registry/institutions/{institution_id}/approve")
def admin_live_intelligence_preservation_registry_approve_institution_endpoint(institution_id: str, request: dict[str, Any], settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _live_intelligence_federated_registry(settings).approve_institution(institution_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Preservation institution not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/live-intelligence/preservation-registry/exchanges/{exchange_id}/attestations")
def admin_live_intelligence_preservation_registry_attestation_endpoint(exchange_id: str, request: dict[str, Any], settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _live_intelligence_federated_registry(settings).record_attestation(exchange_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Preservation exchange or institution not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/admin/live-intelligence/preservation-registry/exchanges/{exchange_id}/consensus")
def admin_live_intelligence_preservation_registry_consensus_endpoint(exchange_id: str, settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return {"ok": True, "version": APP_VERSION, "consensus": _live_intelligence_federated_registry(settings).consensus(exchange_id)}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Preservation exchange not found.") from exc


@app.get("/admin/live-intelligence/preservation-registry/institutions/{institution_id}/package")
def admin_live_intelligence_preservation_registry_institution_package_endpoint(institution_id: str, format: str = Query(default="json", pattern="^(json|markdown)$"), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        media_type, body = _live_intelligence_federated_registry(settings).institution_package_payload(institution_id, format)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Preservation institution not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    suffix = "json" if format == "json" else "md"
    return Response(content=body, media_type=media_type, headers={"Content-Disposition": f'attachment; filename="live-intelligence-preservation-institution-{institution_id}.{suffix}"', "X-SC-Site-Intelligence-Version": APP_VERSION})


@app.get("/admin/live-intelligence/preservation-registry/exchanges/{exchange_id}/package")
def admin_live_intelligence_preservation_registry_consensus_package_endpoint(exchange_id: str, format: str = Query(default="json", pattern="^(json|markdown)$"), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        media_type, body = _live_intelligence_federated_registry(settings).consensus_package_payload(exchange_id, format)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Preservation exchange not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    suffix = "json" if format == "json" else "md"
    return Response(content=body, media_type=media_type, headers={"Content-Disposition": f'attachment; filename="live-intelligence-federated-consensus-{exchange_id}.{suffix}"', "X-SC-Site-Intelligence-Version": APP_VERSION})


@app.get("/admin/live-intelligence/preservation-registry/{entity_id}/history")
def admin_live_intelligence_preservation_registry_history_endpoint(entity_id: str, limit: int = Query(default=200, ge=1, le=1000), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    return {"ok": True, "version": APP_VERSION, "history": _live_intelligence_federated_registry(settings).history(entity_id, limit)}


@app.get("/public/live-intelligence/registry-governance/policy")
def public_live_intelligence_registry_governance_policy_endpoint():
    return live_intelligence_registry_governance_policy()


@app.get("/public/live-intelligence/registry-governance/status")
def public_live_intelligence_registry_governance_status_endpoint(settings: Settings = Depends(get_settings)):
    return _live_intelligence_registry_governance(settings).status()


@app.get("/public/live-intelligence/registry-governance/challenges")
def public_live_intelligence_registry_governance_challenges_endpoint(limit: int = Query(default=50, ge=1, le=500), settings: Settings = Depends(get_settings)):
    rows = _live_intelligence_registry_governance(settings).challenges(public=True, limit=limit)
    return {"ok": True, "version": APP_VERSION, "count": len(rows), "challenges": rows, "automatic_enforcement_performed": False}


@app.get("/public/live-intelligence/registry-governance/appeals")
def public_live_intelligence_registry_governance_appeals_endpoint(limit: int = Query(default=50, ge=1, le=500), settings: Settings = Depends(get_settings)):
    rows = _live_intelligence_registry_governance(settings).appeals(public=True, limit=limit)
    return {"ok": True, "version": APP_VERSION, "count": len(rows), "appeals": rows, "prior_registry_records_retained": True}


@app.get("/public/live-intelligence/registry-governance/institutions/{institution_id}")
def public_live_intelligence_registry_governance_institution_endpoint(institution_id: str, settings: Settings = Depends(get_settings)):
    try:
        return {"ok": True, "version": APP_VERSION, "governance": _live_intelligence_registry_governance(settings).institution_governance(institution_id, public=True)}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Public institution governance record not found.") from exc


@app.get("/admin/live-intelligence/registry-governance")
def admin_live_intelligence_registry_governance_endpoint(settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    center = _live_intelligence_registry_governance(settings)
    return {"ok": True, "version": APP_VERSION, "status": center.status(), "challenges": center.challenges(limit=500), "appeals": center.appeals(limit=500)}


@app.post("/admin/live-intelligence/registry-governance/challenges")
def admin_live_intelligence_registry_governance_create_challenge_endpoint(request: dict[str, Any], settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _live_intelligence_registry_governance(settings).create_challenge(request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Preservation institution not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/live-intelligence/registry-governance/challenges/{challenge_id}/review")
def admin_live_intelligence_registry_governance_review_challenge_endpoint(challenge_id: str, request: dict[str, Any], settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _live_intelligence_registry_governance(settings).review_challenge(challenge_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Registry challenge not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/live-intelligence/registry-governance/challenges/{challenge_id}/approve")
def admin_live_intelligence_registry_governance_approve_challenge_endpoint(challenge_id: str, request: dict[str, Any], settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _live_intelligence_registry_governance(settings).approve_challenge(challenge_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Registry challenge or institution not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/live-intelligence/registry-governance/challenges/{challenge_id}/appeals")
def admin_live_intelligence_registry_governance_create_appeal_endpoint(challenge_id: str, request: dict[str, Any], settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _live_intelligence_registry_governance(settings).create_appeal(challenge_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Registry challenge not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/live-intelligence/registry-governance/appeals/{appeal_id}/review")
def admin_live_intelligence_registry_governance_review_appeal_endpoint(appeal_id: str, request: dict[str, Any], settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _live_intelligence_registry_governance(settings).review_appeal(appeal_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Registry appeal not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/live-intelligence/registry-governance/appeals/{appeal_id}/approve")
def admin_live_intelligence_registry_governance_approve_appeal_endpoint(appeal_id: str, request: dict[str, Any], settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _live_intelligence_registry_governance(settings).approve_appeal(appeal_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Registry appeal, challenge, or institution not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/admin/live-intelligence/registry-governance/institutions/{institution_id}/package")
def admin_live_intelligence_registry_governance_package_endpoint(institution_id: str, format: str = Query(default="json", pattern="^(json|markdown)$"), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        media_type, body = _live_intelligence_registry_governance(settings).package_payload(institution_id, format)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Institution governance record not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    suffix = "json" if format == "json" else "md"
    return Response(content=body, media_type=media_type, headers={"Content-Disposition": f'attachment; filename="live-intelligence-registry-governance-{institution_id}.{suffix}"', "X-SC-Site-Intelligence-Version": APP_VERSION})


@app.get("/admin/live-intelligence/registry-governance/{entity_id}/history")
def admin_live_intelligence_registry_governance_history_endpoint(entity_id: str, limit: int = Query(default=200, ge=1, le=1000), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    return {"ok": True, "version": APP_VERSION, "history": _live_intelligence_registry_governance(settings).history(entity_id, limit)}


@app.get("/public/live-intelligence/registry-discovery/policy")
def public_live_intelligence_registry_discovery_policy_endpoint():
    return live_intelligence_registry_discovery_policy()


@app.get("/public/live-intelligence/registry-discovery/status")
def public_live_intelligence_registry_discovery_status_endpoint(settings: Settings = Depends(get_settings)):
    return _live_intelligence_registry_discovery(settings).status()


@app.get("/public/live-intelligence/registry-discovery/facets")
def public_live_intelligence_registry_discovery_facets_endpoint(settings: Settings = Depends(get_settings)):
    return _live_intelligence_registry_discovery(settings).facets()


@app.get("/public/live-intelligence/registry-discovery/search")
def public_live_intelligence_registry_discovery_search_endpoint(
    q: str = Query(default="", max_length=200),
    record_type: str = Query(default="", max_length=40),
    institution_type: str = Query(default="", max_length=100),
    trust_profile: str = Query(default="", max_length=100),
    jurisdiction: str = Query(default="", max_length=160),
    exchange_profile: str = Query(default="", max_length=100),
    verification_method: str = Query(default="", max_length=100),
    governance_status: str = Query(default="", max_length=100),
    sort: str = Query(default="relevance", pattern="^(relevance|name|recent)$"),
    offset: int = Query(default=0, ge=0, le=10000),
    limit: int = Query(default=25, ge=1, le=100),
    settings: Settings = Depends(get_settings),
):
    try:
        return _live_intelligence_registry_discovery(settings).search(
            query=q, record_type=record_type, institution_type=institution_type,
            trust_profile=trust_profile, jurisdiction=jurisdiction, exchange_profile=exchange_profile,
            verification_method=verification_method, governance_status=governance_status,
            sort=sort, offset=offset, limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/public/live-intelligence/registry-discovery/institutions/{institution_id}")
def public_live_intelligence_registry_discovery_institution_endpoint(institution_id: str, settings: Settings = Depends(get_settings)):
    try:
        return _live_intelligence_registry_discovery(settings).institution_profile(institution_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Public preservation institution profile not found.") from exc


@app.get("/public/live-intelligence/registry-collections/policy")
def public_live_intelligence_registry_collections_policy_endpoint():
    return live_intelligence_registry_collections_policy()


@app.get("/public/live-intelligence/registry-collections/status")
def public_live_intelligence_registry_collections_status_endpoint(settings: Settings = Depends(get_settings)):
    return _live_intelligence_registry_collections(settings).status()


@app.get("/public/live-intelligence/registry-collections/views")
def public_live_intelligence_registry_collections_views_endpoint(limit: int = Query(default=50, ge=1, le=500), settings: Settings = Depends(get_settings)):
    rows = _live_intelligence_registry_collections(settings).views(public=True, limit=limit)
    return {"ok": True, "version": APP_VERSION, "count": len(rows), "views": rows, "visitor_queries_stored": False}


@app.get("/public/live-intelligence/registry-collections")
def public_live_intelligence_registry_collections_endpoint(limit: int = Query(default=50, ge=1, le=500), settings: Settings = Depends(get_settings)):
    rows = _live_intelligence_registry_collections(settings).collections(public=True, limit=limit)
    return {"ok": True, "version": APP_VERSION, "count": len(rows), "collections": rows, "visitor_profiles_created": False}


@app.get("/public/live-intelligence/registry-collections/{collection_id}")
def public_live_intelligence_registry_collection_endpoint(collection_id: str, settings: Settings = Depends(get_settings)):
    try:
        return {"ok": True, "version": APP_VERSION, "collection": _live_intelligence_registry_collections(settings).collection(collection_id, public=True)}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Public registry research collection not found.") from exc


@app.get("/public/live-intelligence/registry-collections/{collection_id}/pathway")
def public_live_intelligence_registry_collection_pathway_endpoint(collection_id: str, settings: Settings = Depends(get_settings)):
    try:
        return _live_intelligence_registry_collections(settings).pathway(collection_id, public=True)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Public registry evidence pathway not found.") from exc


@app.get("/admin/live-intelligence/registry-collections")
def admin_live_intelligence_registry_collections_endpoint(settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    center = _live_intelligence_registry_collections(settings)
    return {"ok": True, "version": APP_VERSION, "status": center.status(), "views": center.views(limit=500), "collections": center.collections(limit=500)}


@app.post("/admin/live-intelligence/registry-collections/views")
def admin_live_intelligence_registry_collections_create_view_endpoint(request: dict[str, Any], settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _live_intelligence_registry_collections(settings).create_view(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/live-intelligence/registry-collections/views/{view_id}/review")
def admin_live_intelligence_registry_collections_review_view_endpoint(view_id: str, request: dict[str, Any], settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _live_intelligence_registry_collections(settings).review_view(view_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Saved discovery view not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/live-intelligence/registry-collections/views/{view_id}/approve")
def admin_live_intelligence_registry_collections_approve_view_endpoint(view_id: str, request: dict[str, Any], settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _live_intelligence_registry_collections(settings).approve_view(view_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Saved discovery view not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/live-intelligence/registry-collections")
def admin_live_intelligence_registry_collections_create_endpoint(request: dict[str, Any], settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _live_intelligence_registry_collections(settings).create_collection(request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Saved discovery view or public registry record not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/live-intelligence/registry-collections/{collection_id}/review")
def admin_live_intelligence_registry_collections_review_endpoint(collection_id: str, request: dict[str, Any], settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _live_intelligence_registry_collections(settings).review_collection(collection_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Registry research collection not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/live-intelligence/registry-collections/{collection_id}/approve")
def admin_live_intelligence_registry_collections_approve_endpoint(collection_id: str, request: dict[str, Any], settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _live_intelligence_registry_collections(settings).approve_collection(collection_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Registry research collection not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/admin/live-intelligence/registry-collections/{collection_id}/package")
def admin_live_intelligence_registry_collections_package_endpoint(collection_id: str, format: str = Query(default="json", pattern="^(json|markdown)$"), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        media_type, body = _live_intelligence_registry_collections(settings).package_payload(collection_id, format)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Registry research collection not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    suffix = "json" if format == "json" else "md"
    return Response(content=body, media_type=media_type, headers={"Content-Disposition": f'attachment; filename="live-intelligence-registry-collection-{collection_id}.{suffix}"', "X-SC-Site-Intelligence-Version": APP_VERSION})


@app.get("/admin/live-intelligence/registry-collections/{entity_id}/history")
def admin_live_intelligence_registry_collections_history_endpoint(entity_id: str, limit: int = Query(default=200, ge=1, le=1000), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    return {"ok": True, "version": APP_VERSION, "history": _live_intelligence_registry_collections(settings).history(entity_id, limit)}


@app.get("/public/live-intelligence/registry-publications/policy")
def public_live_intelligence_registry_publications_policy_endpoint():
    return live_intelligence_registry_publication_policy()


@app.get("/public/live-intelligence/registry-publications/status")
def public_live_intelligence_registry_publications_status_endpoint(settings: Settings = Depends(get_settings)):
    return _live_intelligence_registry_publications(settings).status()


@app.get("/public/live-intelligence/registry-publications/briefs")
def public_live_intelligence_registry_publications_briefs_endpoint(limit: int = Query(default=50, ge=1, le=500), settings: Settings = Depends(get_settings)):
    rows = _live_intelligence_registry_publications(settings).briefs(public=True, limit=limit)
    return {"ok": True, "version": APP_VERSION, "count": len(rows), "briefs": rows}


@app.get("/public/live-intelligence/registry-publications/briefs/{brief_id}")
def public_live_intelligence_registry_publications_brief_endpoint(brief_id: str, settings: Settings = Depends(get_settings)):
    try:
        return {"ok": True, "version": APP_VERSION, "brief": _live_intelligence_registry_publications(settings).brief(brief_id, public=True)}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Public registry research brief not found.") from exc


@app.get("/public/live-intelligence/registry-publications/briefs/{brief_id}/citations")
def public_live_intelligence_registry_publications_citations_endpoint(brief_id: str, settings: Settings = Depends(get_settings)):
    try:
        return _live_intelligence_registry_publications(settings).citation_bundle(brief_id, public=True)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Public registry research brief not found.") from exc


@app.get("/admin/live-intelligence/registry-publications")
def admin_live_intelligence_registry_publications_endpoint(settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    center = _live_intelligence_registry_publications(settings)
    return {"ok": True, "version": APP_VERSION, "status": center.status(), "briefs": center.briefs(limit=500)}


@app.post("/admin/live-intelligence/registry-publications/briefs")
def admin_live_intelligence_registry_publications_create_endpoint(request: dict[str, Any], settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _live_intelligence_registry_publications(settings).create_brief(request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Registry research collection not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/live-intelligence/registry-publications/briefs/{brief_id}/review")
def admin_live_intelligence_registry_publications_review_endpoint(brief_id: str, request: dict[str, Any], settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _live_intelligence_registry_publications(settings).review_brief(brief_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Registry research brief not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/live-intelligence/registry-publications/briefs/{brief_id}/approve")
def admin_live_intelligence_registry_publications_approve_endpoint(brief_id: str, request: dict[str, Any], settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _live_intelligence_registry_publications(settings).approve_brief(brief_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Registry research brief not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/admin/live-intelligence/registry-publications/briefs/{brief_id}/package")
def admin_live_intelligence_registry_publications_package_endpoint(brief_id: str, format: str = Query(default="json", pattern="^(json|markdown|bibtex|ris)$"), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        media_type, body = _live_intelligence_registry_publications(settings).package_payload(brief_id, format)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Registry research brief not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    suffix = {"json": "json", "markdown": "md", "bibtex": "bib", "ris": "ris"}[format]
    return Response(content=body, media_type=media_type, headers={"Content-Disposition": f'attachment; filename="live-intelligence-registry-brief-{brief_id}.{suffix}"', "X-SC-Site-Intelligence-Version": APP_VERSION})


@app.post("/admin/live-intelligence/registry-publications/briefs/{brief_id}/handoffs")
def admin_live_intelligence_registry_publications_handoff_endpoint(brief_id: str, request: dict[str, Any], settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    try:
        return _live_intelligence_registry_publications(settings).record_handoff(brief_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Registry research brief not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/admin/live-intelligence/registry-publications/{entity_id}/history")
def admin_live_intelligence_registry_publications_history_endpoint(entity_id: str, limit: int = Query(default=200, ge=1, le=1000), settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    return {"ok": True, "version": APP_VERSION, "history": _live_intelligence_registry_publications(settings).history(entity_id, limit)}


@app.get("/public/live-intelligence/subscriptions/policy")
def public_live_intelligence_subscription_policy_endpoint():
    return live_intelligence_subscription_policy()


@app.get("/public/live-intelligence/subscriptions/preferences")
def public_live_intelligence_subscription_preferences_endpoint():
    return live_intelligence_preference_manifest()


@app.get("/public/live-intelligence/subscriptions/status")
def public_live_intelligence_subscription_status_endpoint(settings: Settings = Depends(get_settings)):
    return _live_intelligence_subscriptions(settings).status()


@app.get("/public/live-intelligence/subscriptions/catalog")
def public_live_intelligence_subscription_catalog_endpoint(settings: Settings = Depends(get_settings)):
    return _live_intelligence_subscriptions(settings).public_catalog()


@app.get("/public/live-intelligence/subscriptions/catalog/{watchlist_id}")
def public_live_intelligence_subscription_watchlist_endpoint(watchlist_id: str, settings: Settings = Depends(get_settings)):
    try:
        return {"ok": True, "version": APP_VERSION, "watchlist": _live_intelligence_subscriptions(settings)._watchlist(watchlist_id, public=True)}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Published Live Intelligence watchlist not found.") from exc


@app.get("/public/live-intelligence/subscriptions/alerts")
def public_live_intelligence_subscription_alerts_endpoint(
    watchlist_id: str = Query(default="", max_length=180),
    limit: int = Query(default=100, ge=1, le=500),
    settings: Settings = Depends(get_settings),
):
    alerts = _live_intelligence_subscriptions(settings).alerts(public=True, watchlist_id=watchlist_id, limit=limit)
    return {"ok": True, "version": APP_VERSION, "count": len(alerts), "alerts": alerts, "automatic_publication": False}


@app.get("/public/live-intelligence/subscriptions/digests")
def public_live_intelligence_subscription_digests_endpoint(
    limit: int = Query(default=50, ge=1, le=500),
    settings: Settings = Depends(get_settings),
):
    digests = _live_intelligence_subscriptions(settings).digests(public=True, limit=limit)
    return {"ok": True, "version": APP_VERSION, "count": len(digests), "digests": digests, "automatic_publication": False}


@app.get("/public/live-intelligence/subscriptions/watchlists/{watchlist_id}/feed")
def public_live_intelligence_subscription_feed_endpoint(
    watchlist_id: str,
    format: str = Query(default="json", pattern="^(json|rss|atom)$"),
    settings: Settings = Depends(get_settings),
):
    try:
        media_type, body = _live_intelligence_subscriptions(settings).feed_payload(watchlist_id, format)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Published Live Intelligence watchlist not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return Response(content=body, media_type=media_type, headers={"X-SC-Site-Intelligence-Version": APP_VERSION})


@app.get("/admin/live-intelligence/subscriptions")
def admin_live_intelligence_subscriptions_endpoint(settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    return _live_intelligence_subscriptions(settings).control_center()


@app.post("/admin/live-intelligence/subscriptions/watchlists")
def admin_live_intelligence_subscription_watchlist_save_endpoint(
    request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token),
):
    try:
        return _live_intelligence_subscriptions(settings).save_watchlist(request)
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/live-intelligence/subscriptions/watchlists/{watchlist_id}/evaluate")
def admin_live_intelligence_subscription_watchlist_evaluate_endpoint(
    watchlist_id: str, request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token),
):
    try:
        return _live_intelligence_subscriptions(settings).evaluate_watchlist(watchlist_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Live Intelligence watchlist not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/live-intelligence/subscriptions/run-due")
def admin_live_intelligence_subscriptions_run_due_endpoint(
    dry_run: bool = Query(default=True), limit: int = Query(default=100, ge=1, le=500),
    settings: Settings = Depends(get_settings), _: None = Depends(require_token),
):
    return _live_intelligence_subscriptions(settings).run_due(dry_run=dry_run, limit=limit)


@app.post("/admin/live-intelligence/subscriptions/alerts/{alert_id}/review")
def admin_live_intelligence_subscription_alert_review_endpoint(
    alert_id: str, request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token),
):
    try:
        return _live_intelligence_subscriptions(settings).review_alert(alert_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Live Intelligence alert not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/live-intelligence/subscriptions/digests")
def admin_live_intelligence_subscription_digest_create_endpoint(
    request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token),
):
    try:
        return _live_intelligence_subscriptions(settings).generate_digest(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/live-intelligence/subscriptions/digests/{digest_id}/review")
def admin_live_intelligence_subscription_digest_review_endpoint(
    digest_id: str, request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token),
):
    try:
        return _live_intelligence_subscriptions(settings).review_digest(digest_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Live Intelligence digest not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/live-intelligence/subscriptions/digests/{digest_id}/handoff")
def admin_live_intelligence_subscription_digest_handoff_endpoint(
    digest_id: str, request: dict = Body(default={}), settings: Settings = Depends(get_settings), _: None = Depends(require_token),
):
    try:
        return _live_intelligence_subscriptions(settings).create_handoff(digest_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Live Intelligence digest not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/public/live-intelligence/presentation-policy")
def public_live_intelligence_presentation_policy_endpoint():
    return live_intelligence_presentation_policy()


@app.get("/public/live-intelligence/channels")
def public_live_intelligence_channels_endpoint():
    return live_intelligence_channel_directory()


@app.get("/public/live-intelligence/channel-policy")
def public_live_intelligence_channel_policy_endpoint():
    return live_intelligence_channel_policy()


@app.get("/public/live-intelligence/channels/{channel_id}")
def public_live_intelligence_channel_endpoint(channel_id: str):
    try:
        return live_intelligence_channel_definition(channel_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Live Intelligence channel not found.") from exc


@app.get("/public/live-intelligence/channels/{channel_id}/feed")
def public_live_intelligence_channel_feed_endpoint(
    channel_id: str,
    limit: int = Query(default=16, ge=1, le=24),
    feeds: str = Query(default="", max_length=320),
    exclude: str = Query(default="", max_length=320),
    max_per_source: int = Query(default=2, ge=1, le=5),
    region: str = Query(default="", max_length=100),
    country: str = Query(default="", max_length=100),
    settings: Settings = Depends(get_settings),
):
    try:
        return build_channel_feed(
            settings, channel_id, limit=limit, feeds=feeds, exclude=exclude,
            max_per_source=max_per_source, region=region, country=country,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Live Intelligence channel not found.") from exc


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


@app.get("/admin/live-intelligence/rotation")
def admin_live_intelligence_rotation_endpoint(settings: Settings = Depends(get_settings), _: None = Depends(require_token)):
    store = LiveIntelligenceRotationStore(settings)
    return {"ok": True, "version": APP_VERSION, "state": store.read(), "status": store.status()}


@app.patch("/admin/live-intelligence/rotation/signals/{signal_id}")
def admin_live_intelligence_rotation_override_endpoint(
    signal_id: str,
    request: dict = Body(default={}),
    settings: Settings = Depends(get_settings),
    _: None = Depends(require_token),
):
    try:
        override = LiveIntelligenceRotationStore(settings).set_override(signal_id, request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "version": APP_VERSION, "override": override}


@app.get("/admin/live-intelligence/analytics")
def admin_live_intelligence_analytics_endpoint(
    days: int = Query(default=30, ge=1, le=365),
    settings: Settings = Depends(get_settings),
    _: None = Depends(require_token),
):
    if not settings.live_intelligence_analytics_enabled:
        raise HTTPException(status_code=404, detail="Live Intelligence analytics are disabled.")
    store = LiveIntelligenceAnalyticsStore(settings)
    return {"ok": True, "version": APP_VERSION, "summary": store.summary(days=days, include_signals=True), "status": store.status()}


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

@app.get("/public/water-sanitation-infrastructure")
def public_water_sanitation_overview(): return build_water_sanitation_overview()
@app.get("/public/water-sanitation-infrastructure/catalog")
def public_water_sanitation_catalog(): return build_water_sanitation_catalog()
@app.get("/public/water-sanitation-infrastructure/state")
def public_water_sanitation_state(source: str = Query(default="openstreetmap-water-infrastructure"), indicator_type: str = Query(default="water-works"), area: str = Query(default=""), date: str = Query(default=""), latitude: float | None = Query(default=None), longitude: float | None = Query(default=None)):
    try: return build_water_sanitation_state(source,indicator_type,area,date,latitude,longitude)
    except (ValueError,TypeError) as exc: raise HTTPException(status_code=400,detail=str(exc))
@app.post("/public/water-sanitation-infrastructure/feature/normalize")
def public_water_sanitation_feature_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_water_sanitation_normalize_feature(request)
    except (ValueError,TypeError) as exc: raise HTTPException(status_code=400,detail=str(exc))
@app.post("/public/water-sanitation-infrastructure/system/normalize")
def public_water_sanitation_system_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_water_sanitation_normalize_system(request)
    except (ValueError,TypeError) as exc: raise HTTPException(status_code=400,detail=str(exc))
@app.post("/public/water-sanitation-infrastructure/series/normalize")
def public_water_sanitation_series_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_water_sanitation_normalize_series(request)
    except (ValueError,TypeError) as exc: raise HTTPException(status_code=400,detail=str(exc))
@app.post("/public/water-sanitation-infrastructure/threshold/preview")
def public_water_sanitation_threshold_preview(request: dict[str, Any] = Body(default={})):
    try: return build_water_sanitation_threshold_preview(request)
    except (ValueError,TypeError) as exc: raise HTTPException(status_code=400,detail=str(exc))
@app.get("/public/water-sanitation-infrastructure/export-manifest")
def public_water_sanitation_manifest(source: str = Query(default="openstreetmap-water-infrastructure"), indicator_type: str = Query(default="water-works"), area: str = Query(default=""), date: str = Query(default=""), latitude: float | None = Query(default=None), longitude: float | None = Query(default=None)):
    try: return build_water_sanitation_export_manifest(source,indicator_type,area,date,latitude,longitude)
    except (ValueError,TypeError) as exc: raise HTTPException(status_code=400,detail=str(exc))
@app.get("/public/water-sanitation-infrastructure/readiness")
def public_water_sanitation_readiness(): return build_water_sanitation_readiness()

@app.get("/public/solid-waste-circular-materials")
def public_solid_waste_overview(): return build_solid_waste_overview()
@app.get("/public/solid-waste-circular-materials/catalog")
def public_solid_waste_catalog(): return build_solid_waste_catalog()
@app.get("/public/solid-waste-circular-materials/state")
def public_solid_waste_state(source: str = Query(default="openstreetmap-waste-recycling"), indicator_type: str = Query(default="landfill"), area: str = Query(default=""), date: str = Query(default=""), latitude: float | None = Query(default=None), longitude: float | None = Query(default=None)):
    try: return build_solid_waste_state(source,indicator_type,area,date,latitude,longitude)
    except (ValueError,TypeError) as exc: raise HTTPException(status_code=400,detail=str(exc))
@app.post("/public/solid-waste-circular-materials/feature/normalize")
def public_solid_waste_feature_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_solid_waste_normalize_feature(request)
    except (ValueError,TypeError) as exc: raise HTTPException(status_code=400,detail=str(exc))
@app.post("/public/solid-waste-circular-materials/regulatory/normalize")
def public_solid_waste_regulatory_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_solid_waste_normalize_regulatory(request)
    except (ValueError,TypeError) as exc: raise HTTPException(status_code=400,detail=str(exc))
@app.post("/public/solid-waste-circular-materials/series/normalize")
def public_solid_waste_series_normalize(request: dict[str, Any] = Body(default={})):
    try: return build_solid_waste_normalize_series(request)
    except (ValueError,TypeError) as exc: raise HTTPException(status_code=400,detail=str(exc))
@app.post("/public/solid-waste-circular-materials/threshold/preview")
def public_solid_waste_threshold_preview(request: dict[str, Any] = Body(default={})):
    try: return build_solid_waste_threshold_preview(request)
    except (ValueError,TypeError) as exc: raise HTTPException(status_code=400,detail=str(exc))
@app.get("/public/solid-waste-circular-materials/export-manifest")
def public_solid_waste_manifest(source: str = Query(default="openstreetmap-waste-recycling"), indicator_type: str = Query(default="landfill"), area: str = Query(default=""), date: str = Query(default=""), latitude: float | None = Query(default=None), longitude: float | None = Query(default=None)):
    try: return build_solid_waste_export_manifest(source,indicator_type,area,date,latitude,longitude)
    except (ValueError,TypeError) as exc: raise HTTPException(status_code=400,detail=str(exc))
@app.get("/public/solid-waste-circular-materials/readiness")
def public_solid_waste_readiness(): return build_solid_waste_readiness()
