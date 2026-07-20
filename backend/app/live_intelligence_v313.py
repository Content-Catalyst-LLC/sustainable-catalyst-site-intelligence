"""Compatibility alias for the Site Intelligence v3.1.3 import path.

The active implementation moved to :mod:`live_intelligence_v314` in v3.1.5.
The module alias keeps monkeypatching and legacy imports attached to the active
implementation rather than to a detached wrapper namespace.
"""
from __future__ import annotations

import sys
from . import live_intelligence_v314 as _implementation

sys.modules[__name__] = _implementation
