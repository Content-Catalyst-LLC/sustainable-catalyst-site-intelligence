from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ContentItem(BaseModel):
    id: str
    title: str
    url_path: str
    content_type: str = "article"
    hub: str = "Uncategorized"
    article_map: Optional[str] = None
    discipline: Optional[str] = None
    pathway_id: Optional[str] = None
    repository_url: Optional[str] = None
    workbench_tool_ids: List[str] = Field(default_factory=list)
    research_librarian_scope: Optional[str] = None
    intended_next_paths: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)


class Registry(BaseModel):
    version: str = "0.6.0"
    site: str = "Sustainable Catalyst"
    base_url: str = "https://sustainablecatalyst.com"
    generated_at: str
    items: List[ContentItem]


class RegistryMatch(BaseModel):
    item: Optional[ContentItem] = None
    status: str = "unmapped"  # explicit, inferred, unmapped, excluded
    confidence: float = 0.0
    reason: str = "No registry or inference match."


class RegistrySuggestion(BaseModel):
    path: str
    title: str = ""
    suggested_id: str
    suggested_hub: str
    suggested_article_map: Optional[str] = None
    suggested_content_type: str = "article"
    suggested_discipline: Optional[str] = None
    confidence: float = 0.0
    reason: str = ""
    sample_registry_item: Dict[str, Any] = Field(default_factory=dict)
    views: float = 0
    active_users: float = 0


class GA4ReportRow(BaseModel):
    dimensions: Dict[str, str] = Field(default_factory=dict)
    metrics: Dict[str, float] = Field(default_factory=dict)


class PageMetric(BaseModel):
    path: str
    title: str = ""
    hub: str = "Unmapped"
    article_map: Optional[str] = None
    discipline: Optional[str] = None
    content_type: str = "unknown"
    mapping_status: str = "unmapped"
    mapping_confidence: float = 0.0
    mapping_reason: str = ""
    screen_page_views: float = 0
    active_users: float = 0
    event_count: float = 0
    engagement_rate: float = 0
    average_session_duration: float = 0
    repository_clicks: float = 0
    workbench_events: float = 0
    research_librarian_events: float = 0
    pathway_events: float = 0
    decision_studio_events: float = 0
    institutional_depth_score: float = 0
    authority_surface_score: float = 0
    hub_efficiency_score: float = 0
    recommendations: List[str] = Field(default_factory=list)


class DashboardResponse(BaseModel):
    ok: bool = True
    generated_at: str
    source: str
    date_range: Dict[str, str]
    totals: Dict[str, float]
    top_pages: List[PageMetric]
    hub_summary: List[Dict[str, Any]]
    recommendations: List[str]
    registry_count: int
    unmapped_pages: List[RegistrySuggestion] = Field(default_factory=list)
    mapping_coverage: Dict[str, float] = Field(default_factory=dict)
    event_diagnostics: Dict[str, Any] = Field(default_factory=dict)
    conversion_readiness: Dict[str, Any] = Field(default_factory=dict)


class CollectedEvent(BaseModel):
    event_name: str
    page_path: str
    page_title: Optional[str] = None
    content_hub: Optional[str] = None
    article_map: Optional[str] = None
    tool_id: Optional[str] = None
    repository_url: Optional[str] = None
    pathway_id: Optional[str] = None
    value: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    client_time: Optional[str] = None


class EventAck(BaseModel):
    ok: bool
    stored: bool
    event_name: str
    message: str


class ExternalConnector(BaseModel):
    connector_id: str
    name: str
    provider: str
    connector_type: str
    description: str = ""
    domains: List[str] = Field(default_factory=list)
    auth_required: bool = False
    status: str = "unknown"
    cache_policy: str = "daily"
    documentation_url: Optional[str] = None
    linked_dashboards: List[str] = Field(default_factory=list)
    linked_tools: List[str] = Field(default_factory=list)
    linked_article_maps: List[str] = Field(default_factory=list)


class ExternalConnectorRegistry(BaseModel):
    version: str = "0.6.0"
    generated_at: str
    connectors: List[ExternalConnector]


class ExternalHealthItem(BaseModel):
    connector_id: str
    name: str
    status: str
    live: bool = False
    message: str = ""
    last_checked: str
    latency_ms: Optional[float] = None
    cache_status: str = "none"
    cached: bool = False
    age_seconds: Optional[float] = None
    cached_at: Optional[str] = None
    expires_at: Optional[str] = None


class ExternalDataPoint(BaseModel):
    label: str
    value: Optional[float] = None
    unit: str = ""
    interpretation: str = ""
    source: str = ""


class ExternalLayer(BaseModel):
    layer_id: str
    title: str
    category: str = "earth_observation"
    service: str = "NASA GIBS"
    endpoint_hint: Optional[str] = None
    interpretation: str = ""


class ClimateEnergyDashboard(BaseModel):
    ok: bool = True
    generated_at: str
    source: str
    location: Dict[str, Any]
    connector_health: List[ExternalHealthItem] = Field(default_factory=list)
    cache_summary: Dict[str, Any] = Field(default_factory=dict)
    stability: Dict[str, Any] = Field(default_factory=dict)
    indicators: List[ExternalDataPoint] = Field(default_factory=list)
    earth_observation_layers: List[ExternalLayer] = Field(default_factory=list)
    emissions_summary: Dict[str, Any] = Field(default_factory=dict)
    linked_article_maps: List[str] = Field(default_factory=list)
    linked_workbench_tools: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)
    methodology: Dict[str, Any] = Field(default_factory=dict)
