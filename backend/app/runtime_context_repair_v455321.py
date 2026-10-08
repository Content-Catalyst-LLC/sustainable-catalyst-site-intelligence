"""v4.55.3.2.1 runtime-health truth and domain-context repair contract.

This module is intentionally provider-neutral.  It mirrors the public browser
contract in executable Python so deployment/certification can verify the
semantics without claiming any new domain data is available.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .version import APP_VERSION

REGISTRY_PATH = Path(__file__).resolve().parents[1] / "data" / "runtime_health_domain_context_registry_v455321.json"
GEOGRAPHY_CODE_DOMAINS = frozenset({"economics", "science", "resources"})
COUNTRY_DOMAINS = frozenset({"law", "humanitarian", "dossiers"})


def manifest() -> dict[str, Any]:
    payload = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    if payload.get("version") != APP_VERSION:
        raise RuntimeError("runtime/context repair registry release mismatch")
    return payload


def normalize_domain_context(view: str, country: str, params: Mapping[str, str] | None = None) -> dict[str, str]:
    """Return canonical query context without inventing geographic identity."""
    out = {str(k): str(v) for k, v in dict(params or {}).items() if v is not None}
    resolved_view = str(view or out.get("view") or "").strip().lower()
    resolved_country = str(country or out.get("country") or out.get("geography_code") or "").strip().upper()
    if resolved_view:
        out.setdefault("view", resolved_view)
    if resolved_country:
        out.setdefault("country", resolved_country)
        if resolved_view in GEOGRAPHY_CODE_DOMAINS:
            out.setdefault("geography_code", resolved_country)
        if resolved_view in COUNTRY_DOMAINS:
            out["country"] = resolved_country
    return out


def classify_runtime_health(*, online: bool, endpoints: list[Mapping[str, Any]], degraded_runtime: bool = False) -> str:
    """Classify public runtime health with strict offline semantics.

    Offline is reserved for browser/network loss or canonical `/health`
    failure.  Failures of optional diagnostics or domain services degrade the
    application but do not make the whole site offline.
    """
    if not online:
        return "offline"
    primary = next(
        (item for item in endpoints if item.get("path") == "/health" or item.get("label") == "Service"),
        None,
    )
    if primary is not None and not bool(primary.get("ok")):
        return "offline"
    if any(not bool(item.get("ok")) for item in endpoints) or degraded_runtime:
        return "degraded"
    if not endpoints:
        return "checking"
    return "healthy"
