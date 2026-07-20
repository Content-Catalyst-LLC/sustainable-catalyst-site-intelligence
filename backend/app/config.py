from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .version import APP_VERSION


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_prefix="SC_SI_", env_file=".env", extra="ignore")

    app_name: str = "Sustainable Catalyst Site Intelligence"
    version: str = APP_VERSION
    environment: str = "development"
    demo_mode: bool = True
    api_token: str = "dev-token-change-me"
    cors_origins: str = "http://127.0.0.1:8091,http://localhost:8091,https://sustainablecatalyst.com"
    cache_ttl_seconds: int = 900
    registry_path: str = "backend/data/site_registry.seed.json"

    ga4_property_id: str = ""
    google_application_credentials_json: str = ""
    google_application_credentials_file: str = ""

    max_ga4_rows: int = Field(default=250, ge=1, le=10000)

    # External data connector settings. Live connectors attempt public API calls
    # and gracefully fall back to sample data when an upstream service is unavailable.
    external_live: bool = True
    external_request_timeout_seconds: int = Field(default=8, ge=1, le=30)
    external_cache_enabled: bool = True
    external_cache_ttl_seconds: int = Field(default=1800, ge=60, le=86400)
    external_stale_ttl_seconds: int = Field(default=86400, ge=300, le=604800)
    external_registry_path: str = "backend/data/external_connectors.seed.json"
    external_default_latitude: float = 41.8781
    external_default_longitude: float = -87.6298
    external_default_country: str = "USA"
    nasa_power_base_url: str = "https://power.larc.nasa.gov/api/temporal/daily/point"
    nasa_gibs_wmts_capabilities_url: str = "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/1.0.0/WMTSCapabilities.xml"
    climate_trace_base_url: str = "https://api.climatetrace.org/v6"

    # Google Search Console / SEO Intelligence settings. Uses the same service
    # account credential as GA4, but the service account must also be added to
    # the Search Console property.
    search_console_live: bool = True
    search_console_site_url: str = "https://sustainablecatalyst.com/"
    search_console_max_rows: int = Field(default=250, ge=1, le=25000)
    search_console_timeout_seconds: int = Field(default=10, ge=1, le=30)

    # Sitemap / Indexing Intelligence settings. These drive v0.4.0 structural
    # integrity checks across sitemap, registry, GA4, and Search Console.
    sitemap_live: bool = True
    sitemap_url: str = "https://sustainablecatalyst.com/sitemap.xml"
    sitemap_timeout_seconds: int = Field(default=10, ge=1, le=30)
    sitemap_max_urls: int = Field(default=500, ge=1, le=10000)
    site_base_url: str = "https://sustainablecatalyst.com"

    # Public Dashboard Framework settings. Public endpoints return sanitized,
    # aggregated output and should never expose raw internal GA4 diagnostics,
    # private conversion queues, or backend configuration values.
    public_dashboards_enabled: bool = True
    public_metrics_rounding_bucket: int = Field(default=100, ge=1, le=100000)
    public_show_exact_counts: bool = False
    public_default_mode: str = "summary"

    # Advanced External Data Connectors v0.6.0. Optional API keys unlock live
    # source calls where required; dashboards fall back safely when keys are not configured.
    noaa_weather_base_url: str = "https://api.weather.gov"
    eia_base_url: str = "https://api.eia.gov/v2"
    eia_api_key: str = ""
    epa_aqs_base_url: str = "https://aqs.epa.gov/data/api"
    epa_aqs_email: str = ""
    epa_aqs_key: str = ""
    census_base_url: str = "https://api.census.gov"
    gbif_base_url: str = "https://api.gbif.org"

    # Public live connector layer retained through v1.14.1. These public-safe source panels
    # expose readiness, cache, and freshness metadata without returning raw
    # upstream payloads or secrets.
    world_bank_base_url: str = "https://api.worldbank.org/v2"
    openalex_base_url: str = "https://api.openalex.org"
    crossref_base_url: str = "https://api.crossref.org"
    github_api_base_url: str = "https://api.github.com"
    github_org: str = "Content-Catalyst-LLC"
    public_connector_live_checks: bool = True


    # Platform Core v2.5.0 integration — optional in Site Intelligence v1.20.0.
    # Write credentials remain backend-only and must never be exposed through
    # WordPress, browser JavaScript, public diagnostics, or export payloads.
    platform_core_enabled: bool = False
    platform_core_url: str = ""
    platform_core_write_api_key: str = ""
    platform_core_public_api_key: str = ""
    platform_core_timeout_seconds: int = Field(default=5, ge=1, le=30)
    platform_core_queue_path: str = "backend/data/platform_core_queue.jsonl"
    platform_core_public_evidence_url: str = ""


    # Site Intelligence v2.2.0 — Economics, Markets, and Sustainability Signals.
    # Reads scoped public records through Platform Core; no provider credentials
    # or licensed real-time exchange feeds are exposed to the browser.
    economics_sustainability_enabled: bool = True
    economics_sustainability_timeout_seconds: int = Field(default=9, ge=2, le=30)
    economics_sustainability_cache_ttl_seconds: int = Field(default=120, ge=15, le=1800)

    # Site Intelligence v2.3.0 — International Law and Global Governance Observatory.
    # Reads public international-law records and authority taxonomy through
    # Platform Core while preserving legal effect, procedural status, source
    # links, and non-advice safeguards.
    international_law_observatory_enabled: bool = True
    international_law_observatory_timeout_seconds: int = Field(default=9, ge=2, le=30)
    international_law_observatory_cache_ttl_seconds: int = Field(default=120, ge=15, le=1800)

    # Site Intelligence v2.4.0 — Scientific and Earth Systems Observatory.
    # Reads public scientific records, assets, map layers, STAC items, and
    # time-series data through Platform Core without exposing credentials or
    # fabricating scientific records when the data fabric is unavailable.
    scientific_earth_systems_enabled: bool = True
    scientific_earth_systems_timeout_seconds: int = Field(default=9, ge=2, le=30)
    scientific_earth_systems_cache_ttl_seconds: int = Field(default=120, ge=15, le=1800)

    # Site Intelligence v2.5.0 — Humanitarian, Conflict, and Displacement Observatory.
    # Combines public live-event records with scoped Platform Core data while
    # preserving source, date, geographic precision, uncertainty, and safety
    # boundaries. No demonstration records are used in this workspace.
    humanitarian_conflict_displacement_enabled: bool = True
    humanitarian_conflict_displacement_timeout_seconds: int = Field(default=9, ge=2, le=30)
    humanitarian_conflict_displacement_cache_ttl_seconds: int = Field(default=90, ge=15, le=1800)

    # Site Intelligence v2.6.0 — Trade, Energy, and Resource Security Observatory.
    # Reads free official trade, energy, agriculture, water, materials, and
    # sustainability records through Platform Core. Dependencies and exposure
    # summaries preserve source units and never become proprietary risk scores.
    trade_energy_resource_security_enabled: bool = True
    trade_energy_resource_security_timeout_seconds: int = Field(default=9, ge=2, le=30)
    trade_energy_resource_security_cache_ttl_seconds: int = Field(default=120, ge=15, le=1800)

    # Site Intelligence v2.7.0 — Unified Country and Regional Intelligence Dossiers.
    # Composes existing public observatories into source-aware dossiers without
    # creating country rankings, composite scores, causal claims, or automated
    # legal, humanitarian, financial, or national-security determinations.
    unified_dossiers_enabled: bool = True
    unified_dossiers_max_records_per_domain: int = Field(default=40, ge=5, le=60)

    # Site Intelligence v2.8.0 — Alerts, Monitoring, and Live Intelligence Streams.
    # Alert rules remain browser-local. The backend evaluates rules statelessly
    # against public records and emits reconnectable server-sent snapshots.
    alerts_monitoring_enabled: bool = True
    alerts_stream_reconnect_seconds: int = Field(default=30, ge=10, le=300)
    alerts_stream_max_signals: int = Field(default=180, ge=20, le=400)
    alerts_stale_source_hours: int = Field(default=72, ge=6, le=8760)

    # Site Intelligence v2.9.0 — Comparative Intelligence and Scenario Studio.
    # Comparisons retain source units and methodological distinctions. Scenario
    # transformations are user-defined arithmetic, not forecasts or causal models.
    comparative_scenario_studio_enabled: bool = True
    comparative_scenario_max_geographies: int = Field(default=5, ge=2, le=6)
    comparative_scenario_max_indicators: int = Field(default=12, ge=1, le=16)
    comparative_scenario_max_records: int = Field(default=400, ge=50, le=500)

    # Site Intelligence v2.10.0 — Research Paths, Saved Investigations, and Briefing Workflows.
    # Investigation records remain browser-local unless the user explicitly exports
    # or sends a structured handoff. The backend validates and packages records
    # statelessly and never persists private notes or research history.
    research_workflows_enabled: bool = True
    research_workflows_max_investigations: int = Field(default=30, ge=1, le=100)
    research_workflows_max_evidence_items: int = Field(default=120, ge=1, le=300)
    research_workflows_max_notes: int = Field(default=80, ge=1, le=200)

    # Site Intelligence v2.11.0 — Public Data API, Embeds, and Institutional Integration.
    # Exposes versioned read-only public records, embed manifests, and public
    # institutional presentation metadata without provider credentials or user tracking.
    public_data_api_enabled: bool = True
    public_data_api_max_limit: int = Field(default=200, ge=10, le=500)
    public_embeds_enabled: bool = True
    public_embed_allowed_origins: str = ""
    institution_name: str = "Sustainable Catalyst"
    institution_website: str = "https://sustainablecatalyst.com"
    institution_logo_url: str = ""
    institution_contact: str = ""
    institution_accent: str = "#8b1e3f"

    # Site Intelligence v2.12.1 — Production Offline, Mobile, and Embed Reliability Patch.
    # Offline data and preferences remain browser-local. Cached responses must
    # retain stale-state labels and never become a substitute for live sources.
    offline_experience_enabled: bool = True
    service_worker_enabled: bool = True
    offline_cache_max_entries: int = Field(default=120, ge=20, le=500)
    offline_cache_ttl_hours: int = Field(default=24, ge=1, le=168)
    low_bandwidth_default: bool = False

    # Site Intelligence v2.13.0 — Connector Operations and Data Ingestion Control Center.
    # The zero-cost default uses file-backed receipts and state. Runtime files are
    # excluded from release manifests and may be redirected to /tmp on ephemeral hosts.
    connector_operations_enabled: bool = True
    connector_operations_registry_path: str = "backend/data/connector_operations_registry_v2130.json"
    connector_operations_state_path: str = "backend/data/connector_operations_state_v2130.json"
    connector_operations_history_path: str = "backend/data/connector_operations_history_v2130.jsonl"
    connector_operations_quarantine_path: str = "backend/data/connector_operations_quarantine_v2130.jsonl"
    connector_operations_max_history: int = Field(default=500, ge=50, le=5000)
    connector_operations_default_retry_attempts: int = Field(default=3, ge=1, le=5)
    connector_operations_retry_backoff_seconds: float = Field(default=0.25, ge=0.0, le=10.0)
    connector_operations_circuit_breaker_failures: int = Field(default=3, ge=1, le=20)
    connector_operations_circuit_breaker_seconds: int = Field(default=300, ge=30, le=86400)
    connector_operations_max_records_per_run: int = Field(default=500, ge=1, le=5000)
    connector_operations_max_payload_bytes: int = Field(default=2000000, ge=10000, le=20000000)

    # Site Intelligence v2.14.0 — Historical Archive and Temporal Change Intelligence.
    # Accepted connector payloads are sanitized before file-backed archival. The
    # default path may be redirected to a persistent disk; runtime archive files
    # are excluded from immutable release manifests and Git history.
    historical_archive_enabled: bool = True
    historical_archive_capture_on_ingest: bool = True
    historical_archive_root_path: str = "backend/data/historical_archive_v2140"
    historical_archive_index_path: str = "backend/data/historical_archive_v2140/snapshot_index_v2140.jsonl"
    historical_archive_change_path: str = "backend/data/historical_archive_v2140/change_events_v2140.jsonl"
    historical_archive_revision_path: str = "backend/data/historical_archive_v2140/revision_events_v2140.jsonl"
    historical_archive_retention_log_path: str = "backend/data/historical_archive_v2140/retention_events_v2140.jsonl"
    historical_archive_policy_path: str = "backend/data/historical_archive_policy_v2140.json"
    historical_archive_max_snapshot_bytes: int = Field(default=5000000, ge=10000, le=50000000)
    historical_archive_max_index_records: int = Field(default=10000, ge=100, le=100000)
    historical_archive_public_series_limit: int = Field(default=120, ge=10, le=1000)
    historical_archive_default_retention_days: int = Field(default=3650, ge=30, le=36500)
    historical_archive_max_snapshots_per_dataset: int = Field(default=3650, ge=2, le=50000)
    historical_archive_material_change_ratio: float = Field(default=0.01, ge=0.0, le=1.0)

    # Site Intelligence v2.15.0 — Geospatial Analysis and Spatial Evidence Studio.
    # Spatial workspaces use validated WGS84 GeoJSON and dependency-light,
    # inspectable methods. Writable areas, datasets, and analyses are excluded
    # from immutable releases and may be redirected to persistent storage.
    spatial_evidence_enabled: bool = True
    spatial_evidence_root_path: str = "backend/data/spatial_evidence_v2150"
    spatial_evidence_areas_path: str = "backend/data/spatial_evidence_v2150/areas_v2150.jsonl"
    spatial_evidence_datasets_path: str = "backend/data/spatial_evidence_v2150/datasets_v2150.jsonl"
    spatial_evidence_analysis_path: str = "backend/data/spatial_evidence_v2150/analyses_v2150.jsonl"
    spatial_evidence_policy_path: str = "backend/data/spatial_evidence_policy_v2150.json"
    spatial_evidence_layer_catalog_path: str = "backend/data/spatial_layer_catalog_v2150.json"
    spatial_evidence_max_features: int = Field(default=5000, ge=1, le=50000)
    spatial_evidence_max_payload_bytes: int = Field(default=10000000, ge=10000, le=100000000)
    spatial_evidence_max_records: int = Field(default=10000, ge=100, le=100000)
    spatial_evidence_max_radius_km: float = Field(default=5000.0, ge=0.1, le=20000.0)
    spatial_evidence_max_proximity_km: float = Field(default=5000.0, ge=0.1, le=20000.0)

    # Site Intelligence v3.1.4 — Statistical Harmonization and Comparable-Series Engine.
    # Source series, transformed series, and lineage receipts are writable runtime
    # state and may be redirected to durable storage. Release registries remain immutable.
    statistical_harmonization_enabled: bool = True
    statistical_harmonization_root_path: str = "backend/data/statistical_harmonization_v2160"
    statistical_harmonization_series_index_path: str = "backend/data/statistical_harmonization_v2160/series_index_v2160.jsonl"
    statistical_harmonization_lineage_path: str = "backend/data/statistical_harmonization_v2160/transformation_lineage_v2160.jsonl"
    statistical_harmonization_policy_path: str = "backend/data/statistical_harmonization_policy_v2160.json"
    statistical_harmonization_unit_registry_path: str = "backend/data/unit_registry_v2160.json"
    statistical_harmonization_geography_registry_path: str = "backend/data/geography_compatibility_registry_v2160.json"
    statistical_harmonization_max_records: int = Field(default=10000, ge=100, le=100000)
    statistical_harmonization_max_observations: int = Field(default=5000, ge=1, le=100000)

    # Site Intelligence v3.1.4 — Model Registry, Forecast Evaluation, and Early-Warning Indicators.
    # Model cards and immutable policy registries ship with the release. Forecasts,
    # evaluations, warning rules, and warning events are writable runtime state.
    model_governance_enabled: bool = True
    model_governance_root_path: str = "backend/data/model_governance_v2170"
    model_governance_models_path: str = "backend/data/model_governance_v2170/models_v2170.jsonl"
    model_governance_forecasts_path: str = "backend/data/model_governance_v2170/forecasts_v2170.jsonl"
    model_governance_evaluations_path: str = "backend/data/model_governance_v2170/evaluations_v2170.jsonl"
    model_governance_warning_rules_path: str = "backend/data/model_governance_v2170/warning_rules_v2170.jsonl"
    model_governance_warning_events_path: str = "backend/data/model_governance_v2170/warning_events_v2170.jsonl"
    model_governance_policy_path: str = "backend/data/model_governance_policy_v2170.json"
    model_governance_metric_registry_path: str = "backend/data/model_metric_registry_v2170.json"
    model_governance_max_records: int = Field(default=10000, ge=100, le=100000)
    model_governance_max_forecast_points: int = Field(default=5000, ge=1, le=100000)

    # Site Intelligence v3.1.4 — Evidence Synthesis, Claims, and Contradiction Review.
    # Claims, evidence, reviews, syntheses, and uncertainty records are writable
    # runtime state. Immutable policy files ship with the release.
    evidence_synthesis_enabled: bool = True
    evidence_synthesis_root_path: str = "backend/data/evidence_synthesis_v2180"
    evidence_synthesis_claims_path: str = "backend/data/evidence_synthesis_v2180/claims_v2180.jsonl"
    evidence_synthesis_evidence_path: str = "backend/data/evidence_synthesis_v2180/evidence_v2180.jsonl"
    evidence_synthesis_reviews_path: str = "backend/data/evidence_synthesis_v2180/reviews_v2180.jsonl"
    evidence_synthesis_syntheses_path: str = "backend/data/evidence_synthesis_v2180/syntheses_v2180.jsonl"
    evidence_synthesis_uncertainty_path: str = "backend/data/evidence_synthesis_v2180/uncertainty_v2180.jsonl"
    evidence_synthesis_policy_path: str = "backend/data/evidence_synthesis_policy_v2180.json"
    evidence_synthesis_max_records: int = Field(default=10000, ge=100, le=100000)
    evidence_synthesis_max_excerpt_chars: int = Field(default=4000, ge=100, le=20000)

    # Site Intelligence v3.1.4 — Intelligence Publishing and Story Map Studio.
    # Entity, relationship, and alias records are writable runtime state. Immutable
    # policy and relationship registries ship with the release.
    knowledge_graph_enabled: bool = True
    knowledge_graph_root_path: str = "backend/data/knowledge_graph_v2190"
    knowledge_graph_entities_path: str = "backend/data/knowledge_graph_v2190/entities_v2190.jsonl"
    knowledge_graph_relationships_path: str = "backend/data/knowledge_graph_v2190/relationships_v2190.jsonl"
    knowledge_graph_aliases_path: str = "backend/data/knowledge_graph_v2190/aliases_v2190.jsonl"
    knowledge_graph_policy_path: str = "backend/data/knowledge_graph_policy_v2190.json"
    knowledge_graph_relationship_registry_path: str = "backend/data/knowledge_graph_relationship_registry_v2190.json"
    knowledge_graph_max_records: int = Field(default=20000, ge=100, le=200000)
    knowledge_graph_max_traversal_depth: int = Field(default=6, ge=1, le=12)
    knowledge_graph_max_results: int = Field(default=1000, ge=10, le=10000)


    # Site Intelligence v3.1.4 — Intelligence Publishing and Story Map Studio.
    # Publication projects, blocks, reviews, and immutable published versions are
    # writable runtime state. Policy files ship with the immutable release.
    intelligence_publishing_enabled: bool = True
    intelligence_publishing_root_path: str = "backend/data/intelligence_publishing_v2200"
    intelligence_publishing_projects_path: str = "backend/data/intelligence_publishing_v2200/projects_v2200.jsonl"
    intelligence_publishing_blocks_path: str = "backend/data/intelligence_publishing_v2200/blocks_v2200.jsonl"
    intelligence_publishing_reviews_path: str = "backend/data/intelligence_publishing_v2200/reviews_v2200.jsonl"
    intelligence_publishing_versions_path: str = "backend/data/intelligence_publishing_v2200/versions_v2200.jsonl"
    intelligence_publishing_policy_path: str = "backend/data/intelligence_publishing_policy_v2200.json"
    intelligence_publishing_max_records: int = Field(default=10000, ge=100, le=100000)
    intelligence_publishing_max_blocks: int = Field(default=250, ge=1, le=2000)
    intelligence_publishing_max_block_chars: int = Field(default=100000, ge=1000, le=1000000)

    # Site Intelligence v3.1.4 — Scheduled Monitoring, Digests, and Public Intelligence Feeds.
    # Monitor definitions, checks, alerts, digests, delivery receipts, and feed
    # definitions are writable runtime state. The policy file is immutable.
    scheduled_monitoring_enabled: bool = True
    scheduled_monitoring_root_path: str = "backend/data/scheduled_monitoring_v2210"
    scheduled_monitoring_monitors_path: str = "backend/data/scheduled_monitoring_v2210/monitors_v2210.jsonl"
    scheduled_monitoring_checks_path: str = "backend/data/scheduled_monitoring_v2210/checks_v2210.jsonl"
    scheduled_monitoring_alerts_path: str = "backend/data/scheduled_monitoring_v2210/alerts_v2210.jsonl"
    scheduled_monitoring_digests_path: str = "backend/data/scheduled_monitoring_v2210/digests_v2210.jsonl"
    scheduled_monitoring_deliveries_path: str = "backend/data/scheduled_monitoring_v2210/deliveries_v2210.jsonl"
    scheduled_monitoring_feeds_path: str = "backend/data/scheduled_monitoring_v2210/feeds_v2210.jsonl"
    scheduled_monitoring_policy_path: str = "backend/data/scheduled_monitoring_policy_v2210.json"
    scheduled_monitoring_max_records: int = Field(default=20000, ge=100, le=200000)
    scheduled_monitoring_max_signals: int = Field(default=400, ge=20, le=1000)
    scheduled_monitoring_dedupe_hours: int = Field(default=72, ge=1, le=8760)
    scheduled_monitoring_email_enabled: bool = False
    scheduled_monitoring_webhook_enabled: bool = False

    # Site Intelligence v3.1.4 — Institutional Workspaces, Collaboration, and Review.
    # Roles and permissions are enforced inside token-protected administrative APIs,
    # but this release does not provision accounts or replace an identity provider.
    # All writable workspace state is excluded from immutable release packages.
    institutional_workspaces_enabled: bool = True
    institutional_workspaces_root_path: str = "backend/data/institutional_workspaces_v2220"
    institutional_workspaces_workspaces_path: str = "backend/data/institutional_workspaces_v2220/workspaces_v2220.jsonl"
    institutional_workspaces_members_path: str = "backend/data/institutional_workspaces_v2220/members_v2220.jsonl"
    institutional_workspaces_assignments_path: str = "backend/data/institutional_workspaces_v2220/assignments_v2220.jsonl"
    institutional_workspaces_comments_path: str = "backend/data/institutional_workspaces_v2220/comments_v2220.jsonl"
    institutional_workspaces_reviews_path: str = "backend/data/institutional_workspaces_v2220/evidence_reviews_v2220.jsonl"
    institutional_workspaces_collections_path: str = "backend/data/institutional_workspaces_v2220/source_collections_v2220.jsonl"
    institutional_workspaces_activity_path: str = "backend/data/institutional_workspaces_v2220/activity_v2220.jsonl"
    institutional_workspaces_retention_path: str = "backend/data/institutional_workspaces_v2220/retention_v2220.jsonl"
    institutional_workspaces_policy_path: str = "backend/data/institutional_workspaces_policy_v2220.json"
    institutional_workspaces_max_records: int = Field(default=20000, ge=100, le=200000)
    institutional_workspaces_max_members: int = Field(default=500, ge=1, le=5000)
    institutional_workspaces_max_comments: int = Field(default=50000, ge=100, le=500000)
    institutional_workspaces_default_retention_days: int = Field(default=365, ge=30, le=3650)



    # Site Intelligence v3.1.4 — Typed Cross-Platform Intelligence Workflows.
    # Packets, receipts, delivery attempts, linkbacks, and retry records are writable
    # runtime state. This release validates and records handoffs but does not perform
    # remote writes or replace Platform Core orchestration.
    cross_platform_workflows_enabled: bool = True
    cross_platform_workflows_root_path: str = "backend/data/cross_platform_workflows_v2230"
    cross_platform_workflows_packets_path: str = "backend/data/cross_platform_workflows_v2230/packets_v2230.jsonl"
    cross_platform_workflows_receipts_path: str = "backend/data/cross_platform_workflows_v2230/receipts_v2230.jsonl"
    cross_platform_workflows_attempts_path: str = "backend/data/cross_platform_workflows_v2230/attempts_v2230.jsonl"
    cross_platform_workflows_linkbacks_path: str = "backend/data/cross_platform_workflows_v2230/linkbacks_v2230.jsonl"
    cross_platform_workflows_queue_path: str = "backend/data/cross_platform_workflows_v2230/recovery_queue_v2230.jsonl"
    cross_platform_workflows_policy_path: str = "backend/data/cross_platform_workflow_policy_v2230.json"
    cross_platform_workflows_registry_path: str = "backend/data/cross_platform_workflow_registry_v2230.json"
    cross_platform_workflows_max_records: int = Field(default=30000, ge=100, le=300000)
    cross_platform_workflows_max_attempts: int = Field(default=5, ge=1, le=20)
    cross_platform_workflows_retry_delay_seconds: int = Field(default=300, ge=10, le=86400)
    cross_platform_workflows_max_payload_bytes: int = Field(default=2000000, ge=1000, le=20000000)

    # Open Standards, Federation, and Institutional Data Exchange v3.1.4.
    federation_exchange_enabled: bool = True
    federation_root_path: str = "backend/data/federation_exchange_v2240"
    federation_institutions_path: str = "backend/data/federation_exchange_v2240/institutions_v2240.jsonl"
    federation_records_path: str = "backend/data/federation_exchange_v2240/records_v2240.jsonl"
    federation_manifests_path: str = "backend/data/federation_exchange_v2240/manifests_v2240.jsonl"
    federation_imports_path: str = "backend/data/federation_exchange_v2240/imports_v2240.jsonl"
    federation_trust_path: str = "backend/data/federation_exchange_v2240/trust_v2240.jsonl"
    federation_policy_path: str = "backend/data/federation_policy_v2240.json"
    federation_context_path: str = "backend/data/federation_context_v2240.json"
    federation_signing_key: str = ""
    federation_signing_key_id: str = ""
    federation_max_records: int = Field(default=30000, ge=100, le=300000)
    federation_max_manifest_bytes: int = Field(default=5000000, ge=1000, le=50000000)

    # Site Intelligence v3.1.4 — Security, Privacy, Governance, and Production Scale.
    # SQLite provides a zero-cost durable mode with explicit migrations. Production
    # deployments should map the database and backup paths to a persistent disk.
    production_governance_enabled: bool = True
    production_database_path: str = "backend/data/production_governance_v2250/site_intelligence.sqlite3"
    production_backup_path: str = "backend/data/production_governance_v2250/backups"
    production_governance_policy_path: str = "backend/data/production_governance_policy_v2250.json"
    production_governance_max_records: int = Field(default=50000, ge=100, le=500000)
    production_default_retention_days: int = Field(default=365, ge=30, le=3650)
    production_privacy_request_days: int = Field(default=30, ge=1, le=365)
    production_admin_rate_limit: int = Field(default=120, ge=10, le=10000)
    production_admin_rate_window_seconds: int = Field(default=60, ge=1, le=3600)

    # Site Intelligence v3.1.4 — Connected Public Intelligence and Evidence Platform.
    # The default zero-cost index is generated from public-safe registries and
    # approved runtime records. It does not expose private records or claim a
    # persistent search cluster, automatic publication, or remote delivery.
    connected_platform_enabled: bool = True
    connected_platform_max_results: int = Field(default=1000, ge=50, le=20000)

    # Sustainable Development Data Connectors v1.14.1.
    sustainable_development_connectors_enabled: bool = True
    sustainable_development_live_checks: bool = False
    sustainable_development_cache_ttl_seconds: int = Field(default=21600, ge=300, le=604800)
    sustainable_development_stale_ttl_seconds: int = Field(default=604800, ge=3600, le=2592000)
    sustainable_development_retry_attempts: int = Field(default=3, ge=1, le=5)
    sustainable_development_retry_backoff_seconds: float = Field(default=0.25, ge=0.0, le=5.0)
    sustainable_development_circuit_breaker_failures: int = Field(default=3, ge=1, le=20)
    sustainable_development_circuit_breaker_seconds: int = Field(default=300, ge=30, le=86400)

    # AI-Assisted Intelligence Briefs v0.8.2. Disabled by default; deterministic
    # fallback briefs remain available without external model calls.
    ai_provider: str = "disabled"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"
    ai_temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    ai_max_output_tokens: int = Field(default=1200, ge=256, le=8192)
    ai_timeout_seconds: int = Field(default=12, ge=3, le=30)

    @property
    def cors_origin_list(self) -> List[str]:
        origins = [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
        origins.extend(origin.strip() for origin in self.public_embed_allowed_origins.split(",") if origin.strip())
        return list(dict.fromkeys(origins))

    @property
    def ga4_enabled(self) -> bool:
        return bool(self.ga4_property_id) and not self.demo_mode


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
