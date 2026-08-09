"""Single-owner bootstrap and loading recovery contract for Site Intelligence v4.5.0."""
from __future__ import annotations
from copy import deepcopy
import json
from pathlib import Path
from typing import Any
from .version import APP_VERSION

POLICY_PATH = Path(__file__).resolve().parents[1] / "data" / "bootstrap_recovery_policy_v32361.json"

def public_bootstrap_recovery_contract() -> dict[str, Any]:
    payload = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    if payload.get("version") != APP_VERSION:
        raise ValueError("Bootstrap recovery policy version does not match the application release.")
    result = deepcopy(payload)
    result.update({"ok": True, "schema": "sc-site-intelligence-bootstrap-recovery/1.0"})
    return result
