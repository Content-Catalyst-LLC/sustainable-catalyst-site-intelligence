"""Deployment verification and non-blocking source-health policy for Site Intelligence v4.35.12.

Release verification is intentionally limited to first-party deployment identity,
packaging, and deterministic application/runtime contracts. External authoritative
source availability is reported separately and can never block a release.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .authoritative_connectors_v4355 import CONNECTORS, connector_readiness
from .version import APP_VERSION

VERSION = APP_VERSION
CONTRACT = "deployment-verification-source-health-v43531"
PUBLIC_APP_DIR = Path(__file__).resolve().parent.parent / "public_app"
REQUIRED_ASSETS = (
    "index.html",
    "assets/app.js",
    "assets/app.css",
    "assets/unified-platform-v4000.js",
    "assets/vector-cartography-v3230.js",
    "assets/world-cartography-v3230.geojson",
)
REQUIRED_ROUTES = (
    "/health",
    "/public/release-gate",
    "/public/runtime-health",
    "/public/v4/readiness",
    "/public/authoritative-connectors/readiness",
    "/public/deployment-verification",
    "/public/source-health-policy",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _setting(settings: Any, name: str, default: str = "") -> str:
    return str(getattr(settings, name, default) or "").strip()


def deployment_verification(settings: Any) -> dict[str, Any]:
    assets = []
    for relative in REQUIRED_ASSETS:
        path = PUBLIC_APP_DIR / relative
        assets.append({
            "path": f"/app/{relative}" if relative != "index.html" else "/app/",
            "available": path.is_file(),
            "bytes": path.stat().st_size if path.is_file() else 0,
        })
    connector_contract = connector_readiness(settings)
    checks = {
        "version_aligned": _setting(settings, "version", VERSION) == VERSION,
        "application_shell_packaged": all(row["available"] for row in assets),
        "authoritative_connector_router_contract_ready": bool(connector_contract.get("ok")),
        "external_source_health_is_non_blocking": True,
        "required_route_contract_declared": len(REQUIRED_ROUTES) == 7,
    }
    return {
        "ok": all(checks.values()),
        "version": VERSION,
        "contract": CONTRACT,
        "release_gate_scope": "first-party deployment identity and deterministic application/runtime integrity",
        "checks": checks,
        "required_routes": list(REQUIRED_ROUTES),
        "assets": assets,
        "source_health_blocks_release": False,
        "network_calls_performed": False,
        "generated_at": _now(),
    }


def source_health_policy(settings: Any) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for connector in CONNECTORS:
        base_setting = str(connector.get("base_url_setting") or "")
        configured_url = _setting(settings, base_setting)
        credential_setting = str(connector.get("credential_setting") or "")
        credential_ok = bool(_setting(settings, credential_setting)) if credential_setting else True
        state = "configured" if configured_url and credential_ok else "configuration-required"
        rows.append({
            "id": connector["id"],
            "title": connector["title"],
            "organization": connector["organization"],
            "mode": connector["mode"],
            "state": state,
            "release_blocking": False,
            "network_probe_performed": False,
            "required_environment": connector.get("credential_environment"),
            "interpretation": "Configuration/readiness state only; current upstream availability is not inferred without a live probe.",
        })
    reliefweb_configured = bool(_setting(settings, "reliefweb_appname"))
    rows.append({
        "id": "reliefweb-v2",
        "title": "ReliefWeb API V2",
        "organization": "UN OCHA ReliefWeb",
        "mode": "AUTH_REQUIRED",
        "state": "configured" if reliefweb_configured else "configuration-required",
        "release_blocking": False,
        "network_probe_performed": False,
        "interpretation": "A missing approved appname disables ReliefWeb retrieval only; it never invalidates the Site Intelligence deployment.",
    })
    summary = {
        "sources": len(rows),
        "configured": sum(row["state"] == "configured" for row in rows),
        "configuration_required": sum(row["state"] == "configuration-required" for row in rows),
        "release_blocking_sources": sum(bool(row["release_blocking"]) for row in rows),
    }
    return {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "policy": "External source health is operational evidence, not a deployment prerequisite.",
        "states": ["configured", "configuration-required", "healthy", "degraded", "unavailable", "unknown"],
        "network_calls_performed": False,
        "summary": summary,
        "sources": rows,
        "generated_at": _now(),
    }
