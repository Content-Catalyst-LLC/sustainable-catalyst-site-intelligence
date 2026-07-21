"""Compatibility alias for the active Site Intelligence Live Intelligence implementation."""
from __future__ import annotations
import sys
from . import live_intelligence_channels_v350 as _implementation
sys.modules[__name__] = _implementation
