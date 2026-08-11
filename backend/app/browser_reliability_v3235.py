"""Browser reliability, mobile, and accessibility contract for Site Intelligence v4.35.4."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

from .version import APP_VERSION

SCHEMA_VERSION = "sc-site-intelligence-browser-reliability/1.0"
CONTRACT = "browser-reliability-mobile-accessibility"
RELEASE_ID = f"site-intelligence-v{APP_VERSION}"
POLICY_PATH = Path(__file__).resolve().parents[1] / "data" / "browser_reliability_policy_v3235.json"


def _policy() -> dict[str, Any]:
    payload = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    if payload.get("version") != APP_VERSION:
        raise ValueError("Browser reliability policy version does not match the application release.")
    return payload


def public_browser_reliability_contract() -> dict[str, Any]:
    payload = deepcopy(_policy())
    payload.update({
        "ok": True,
        "version": APP_VERSION,
        "release_id": RELEASE_ID,
        "schema": SCHEMA_VERSION,
        "contract": CONTRACT,
        "runtime_states": ["ready", "limited", "recovering", "unsupported"],
        "boundaries": {
            "browser_detection_is_capability_based": True,
            "user_agent_blocking": False,
            "accessibility_claim_is_conformance_contract_not_certification": True,
            "low_bandwidth_mode_does_not_change_source_values": True,
            "map_summary_does_not_replace_source_provenance": True
        }
    })
    return payload
