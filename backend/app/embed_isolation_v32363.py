"""Fixed application viewport and WordPress embed-isolation contract for v4.13.0."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

from .version import APP_VERSION

POLICY_PATH = Path(__file__).resolve().parents[1] / "data" / "embed_isolation_policy_v32363.json"


def public_embed_isolation_contract() -> dict[str, Any]:
    payload = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    if payload.get("version") != APP_VERSION:
        raise ValueError("Embed-isolation policy version does not match the application release.")
    result = deepcopy(payload)
    result.update({"ok": True, "schema": "sc-site-intelligence-embed-isolation/1.0"})
    return result
