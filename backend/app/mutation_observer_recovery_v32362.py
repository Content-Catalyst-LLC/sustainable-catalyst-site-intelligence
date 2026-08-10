"""Mutation-observer recovery and complete-shell browser-gate contract for v4.30.0."""
from __future__ import annotations
from copy import deepcopy
import json
from pathlib import Path
from typing import Any
from .version import APP_VERSION
POLICY_PATH = Path(__file__).resolve().parents[1] / "data" / "mutation_observer_recovery_policy_v32362.json"
def public_mutation_observer_recovery_contract() -> dict[str, Any]:
    payload=json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    if payload.get("version") != APP_VERSION:
        raise ValueError("Mutation observer recovery policy version does not match the application release.")
    result=deepcopy(payload)
    result.update({"ok":True,"schema":"sc-site-intelligence-mutation-observer-recovery/1.0"})
    return result
