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
