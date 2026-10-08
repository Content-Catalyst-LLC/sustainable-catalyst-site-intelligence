"""v4.56.0 browser API transport and CORS repair contract."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .version import APP_VERSION

REGISTRY_PATH = Path(__file__).resolve().parents[1] / "data" / "browser_api_transport_registry_v455322.json"
PUBLIC_WEB_ORIGIN = "https://intelligence.sustainablecatalyst.com"
RUNTIME_DIAGNOSTIC_HEADER = "X-SCSI-Runtime-Diagnostic"
PRIMARY_HEALTH_PATH = "/health"

def manifest() -> dict[str, Any]:
    payload = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    if payload.get("version") != APP_VERSION:
        raise RuntimeError("browser API transport registry release mismatch")
    return payload

def required_cors_request_headers() -> tuple[str, ...]:
    return ("Accept", "Content-Type", "Cache-Control", "Pragma", "X-SC-Intelligence-Token", RUNTIME_DIAGNOSTIC_HEADER)

def classify_transport(*, browser_online: bool, primary_health_ok: bool, optional_failures: int = 0) -> str:
    if not browser_online or not primary_health_ok:
        return "offline"
    if optional_failures:
        return "degraded"
    return "healthy"
