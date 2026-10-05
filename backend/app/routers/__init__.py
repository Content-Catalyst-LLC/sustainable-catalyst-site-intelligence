"""Modular FastAPI routers for Sustainable Catalyst Site Intelligence."""

from .system import router as system_router
from .data_truth import router as data_truth_router
from .capabilities import router as capabilities_router
from .standalone import router as standalone_router
from .wordpress_bridge import router as wordpress_bridge_router

__all__ = ["system_router", "data_truth_router", "capabilities_router", "standalone_router", "wordpress_bridge_router"]
