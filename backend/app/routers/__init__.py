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

__all__ = ["system_router", "data_truth_router", "capabilities_router", "standalone_router", "wordpress_bridge_router", "spatial_evidence_router", "spatiotemporal_router", "spatial_graph_router", "live_geospatial_router"]
