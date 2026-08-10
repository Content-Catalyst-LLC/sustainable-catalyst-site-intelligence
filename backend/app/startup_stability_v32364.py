"""Production-soak, route-stability, and service-worker closure contract for v4.12.0."""
from __future__ import annotations
from copy import deepcopy
import json
from pathlib import Path
from typing import Any
from .version import APP_VERSION
POLICY_PATH = Path(__file__).resolve().parents[1] / "data" / "startup_stability_policy_v32364.json"

def public_startup_stability_contract() -> dict[str, Any]:
    payload = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    if payload.get("version") != APP_VERSION:
        raise ValueError("Startup-stability policy version does not match the application release.")
    result = deepcopy(payload)
    result.update({"ok": True, "schema": "sc-site-intelligence-startup-stability/1.0"})
    return result
