"""Modular FastAPI routers introduced in Site Intelligence v4.43.0."""

from .system import router as system_router
from .data_truth import router as data_truth_router
from .capabilities import router as capabilities_router

__all__ = ["system_router", "data_truth_router", "capabilities_router"]
