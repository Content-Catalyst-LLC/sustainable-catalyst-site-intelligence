"""Performance and offline recovery contract for Site Intelligence v4.35.15."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

from .version import APP_VERSION

SCHEMA_VERSION = "sc-site-intelligence-performance-offline/1.0"
CONTRACT = "performance-and-offline-recovery"
RELEASE_ID = f"site-intelligence-v{APP_VERSION}"
POLICY_PATH = Path(__file__).resolve().parents[1] / "data" / "performance_offline_policy_v3236.json"


def _policy() -> dict[str, Any]:
    payload = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    if payload.get("version") != APP_VERSION:
        raise ValueError("Performance and offline policy version does not match the application release.")
    return payload


def public_performance_offline_contract() -> dict[str, Any]:
    payload = deepcopy(_policy())
    payload.update({
        "ok": True,
        "version": APP_VERSION,
        "release_id": RELEASE_ID,
        "schema": SCHEMA_VERSION,
        "contract": CONTRACT,
        "runtime_statuses": ["ready", "limited", "recovering", "offline", "update-ready"],
        "measurement": {
            "first_useful_map_requires_dimensions": True,
            "first_useful_map_requires_visible_geography_or_tiles": True,
            "route_interactive_requires_active_surface": True,
            "long_tasks_observed_when_supported": True,
            "browser_measurements_are_local_and_not_uploaded": True,
        },
    })
    return payload
