"""Compatibility import for the v3.1.1 module name.

The active implementation moved to :mod:`live_intelligence_v311` in v3.1.1.
"""
from .live_intelligence_v311 import (  # noqa: F401
    CATEGORY_ALIASES,
    SCHEMA_VERSION,
    build_live_intelligence,
    live_intelligence_status,
)
