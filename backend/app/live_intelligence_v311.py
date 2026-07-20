"""Compatibility import for the v3.1.2 module name.

The active implementation moved to :mod:`live_intelligence_v312` in v3.1.2.
"""
from .live_intelligence_v312 import (  # noqa: F401
    CATEGORY_ALIASES,
    DEFAULT_SIGNAL_LIMIT,
    MAX_SIGNAL_LIMIT,
    SCHEMA_VERSION,
    build_live_intelligence,
    live_intelligence_status,
)
