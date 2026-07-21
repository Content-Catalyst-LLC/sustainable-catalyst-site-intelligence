"""Compatibility exports for the v3.12.0 Live Intelligence module.

The active implementation moved to :mod:`live_intelligence_v313` in v3.12.0.
"""
from .live_intelligence_v313 import (  # noqa: F401
    DEFAULT_FEEDS,
    DEFAULT_MAX_SIGNALS_PER_SOURCE,
    DEFAULT_SIGNAL_LIMIT,
    FEED_REGISTRY,
    MAX_CONFIGURABLE_SIGNALS_PER_SOURCE,
    MAX_SIGNAL_LIMIT,
    SCHEMA_VERSION,
    build_live_intelligence,
    live_intelligence_status,
)
