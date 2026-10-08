"""Modular FastAPI routers for Sustainable Catalyst Site Intelligence."""

from .system import router as system_router
from .data_truth import router as data_truth_router
from .capabilities import router as capabilities_router
from .standalone import router as standalone_router
from .wordpress_bridge import router as wordpress_bridge_router
from .spatial_evidence import router as spatial_evidence_router
from .spatiotemporal import router as spatiotemporal_router

from .spatial_graph import router as spatial_graph_router
from .live_geospatial import router as live_geospatial_router

__all__ = ["system_router", "data_truth_router", "capabilities_router", "standalone_router", "wordpress_bridge_router", "spatial_evidence_router", "spatiotemporal_router", "spatial_graph_router", "live_geospatial_router", "source_federation_router", "spatial_research_router", "predictive_spatial_router", "scenario_exposure_router", "advanced_domains_router", "reproducible_spatial_packages_router", "spatial_lineage_router", "domain_intelligence_router", "web_application_router", "reliability_router"]

from .source_federation import router as source_federation_router
from .spatial_research import router as spatial_research_router

from .predictive_spatial import router as predictive_spatial_router

from .scenario_exposure import router as scenario_exposure_router
from .advanced_domains import router as advanced_domains_router

from .reproducible_spatial_packages import router as reproducible_spatial_packages_router

from .spatial_lineage import router as spatial_lineage_router

from .domain_intelligence import router as domain_intelligence_router
from .web_application import router as web_application_router

from .reliability import router as reliability_router
