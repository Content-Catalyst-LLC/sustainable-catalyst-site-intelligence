from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_prefix="SC_SI_", env_file=".env", extra="ignore")

    app_name: str = "Sustainable Catalyst Site Intelligence"
    version: str = "1.3.0"
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

    # Public live connector layer v1.3.0. These public-safe source panels
    # expose readiness, cache, and freshness metadata without returning raw
    # upstream payloads or secrets.
    world_bank_base_url: str = "https://api.worldbank.org/v2"
    openalex_base_url: str = "https://api.openalex.org"
    crossref_base_url: str = "https://api.crossref.org"
    github_api_base_url: str = "https://api.github.com"
    github_org: str = "Content-Catalyst-LLC"
    public_connector_live_checks: bool = True

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
