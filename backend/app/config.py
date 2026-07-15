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
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def ga4_enabled(self) -> bool:
        return bool(self.ga4_property_id) and not self.demo_mode


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
