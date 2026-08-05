"""Public-safe runtime diagnostics for Site Intelligence v3.22.4.

The diagnostics intentionally avoid outbound network calls. They report the local
application contract, required first-party assets, map surfaces, embed policy,
and offline-shell alignment so production operators can distinguish a packaging
failure from an upstream data or tile-service failure.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import re
from typing import Any

from .config import Settings
from .version import APP_VERSION

PUBLIC_APP_DIR = Path(__file__).resolve().parent.parent / "public_app"
INDEX_FILE = PUBLIC_APP_DIR / "index.html"
SERVICE_WORKER_FILE = PUBLIC_APP_DIR / "service-worker.js"

REQUIRED_ASSETS = (
    "assets/map-fallback-v3224.css",
    "assets/map-fallback-v3224.js",
    "assets/runtime-v3224.css",
    "assets/runtime-v3224.js",
    "assets/service-recovery-v3224.js",
    "assets/app.css",
    "assets/app.js",
    "assets/spatial-v2150.css",
    "assets/spatial-v2150.js",
)

CRITICAL_PUBLIC_ENDPOINTS = (
    "/health",
    "/public/build-info",
    "/public/geospatial/diagnostics",
    "/public/geospatial/events",
    "/public/spatial",
    "/public/spatial/areas",
    "/public/runtime-health",
    "/public/runtime-recovery",
)

MAP_SURFACE_HINTS = {
    "map": "Primary geospatial intelligence map",
    "eventExplorerMap": "Live-event explorer",
    "earthMapA": "Earth observation comparison A",
    "earthMapB": "Earth observation comparison B",
    "thematicMap": "Thematic intelligence map",
    "compareMap": "Comparative intelligence map",
    "economicsMap": "Economics and markets map",
    "resourceMap": "Trade, energy, and resource-security map",
    "humanitarianMap": "Humanitarian intelligence map",
    "scienceMap": "Earth-systems science map",
    "lawMap": "International-law context map",
    "dossierMap": "Country and regional dossier map",
    "countryOverviewMap": "Country overview map",
    "spatialEvidenceMap": "Spatial evidence workspace",
}


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _check(check_id: str, label: str, passed: bool, detail: str, critical: bool = True) -> dict[str, Any]:
    return {
        "id": check_id,
        "label": label,
        "status": "pass" if passed else "fail",
        "critical": critical,
        "detail": detail,
    }


def _asset_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for relative in REQUIRED_ASSETS:
        path = PUBLIC_APP_DIR / relative
        exists = path.is_file()
        records.append(
            {
                "path": f"/app/{relative}",
                "status": "available" if exists else "missing",
                "bytes": path.stat().st_size if exists else 0,
                "first_party": True,
            }
        )
    return records


def _map_surfaces(index_html: str) -> list[dict[str, Any]]:
    ids = set(re.findall(r'id="([^"]*[Mm]ap[^"]*)"', index_html))
    surfaces: list[dict[str, Any]] = []
    for container_id, purpose in MAP_SURFACE_HINTS.items():
        surfaces.append(
            {
                "container_id": container_id,
                "purpose": purpose,
                "status": "declared" if container_id in ids else "missing",
                "fallback_supported": True,
            }
        )
    return surfaces


def build_runtime_health(settings: Settings) -> dict[str, Any]:
    index_html = _read(INDEX_FILE)
    worker = _read(SERVICE_WORKER_FILE)
    assets = _asset_records()
    surfaces = _map_surfaces(index_html)

    fallback_js = "/app/assets/map-fallback-v3224.js"
    recovery_js = "/app/assets/service-recovery-v3224.js"
    runtime_js = "/app/assets/runtime-v3224.js"
    app_js = "/app/assets/app.js"
    ordered_scripts = all(token in index_html for token in (fallback_js, recovery_js, runtime_js, app_js))
    if ordered_scripts:
        ordered_scripts = index_html.index(fallback_js) < index_html.index(recovery_js) < index_html.index(runtime_js) < index_html.index(app_js)

    checks = [
        _check(
            "version-alignment",
            "Backend and configured version agree",
            settings.version == APP_VERSION,
            f"Backend {APP_VERSION}; configured {settings.version}.",
        ),
        _check(
            "public-app-index",
            "Standalone application shell exists",
            bool(index_html),
            "The first-party application index is readable." if index_html else "The application index is missing or unreadable.",
        ),
        _check(
            "required-assets",
            "Required runtime assets are packaged",
            all(item["status"] == "available" for item in assets),
            f"{sum(item['status'] == 'available' for item in assets)} of {len(assets)} required assets are available.",
        ),
        _check(
            "script-order",
            "Fault-isolation runtime loads before application modules",
            ordered_scripts,
            "Map fallback → service recovery → runtime diagnostics → application order is enforced." if ordered_scripts else "Required script order is incomplete.",
        ),
        _check(
            "offline-shell",
            "Offline shell contains the reliability assets",
            all(name in worker for name in ("map-fallback-v3224.js", "runtime-v3224.js", "runtime-v3224.css", "service-recovery-v3224.js")) and f'const RELEASE="{APP_VERSION}"' in worker,
            "Service worker release and runtime assets are aligned." if worker else "Service worker is missing or unreadable.",
        ),
        _check(
            "map-surfaces",
            "Known map containers are declared",
            all(item["status"] == "declared" for item in surfaces),
            f"{sum(item['status'] == 'declared' for item in surfaces)} of {len(surfaces)} known map containers are declared.",
            critical=False,
        ),
    ]

    failed_critical = [item for item in checks if item["critical"] and item["status"] != "pass"]
    failed_review = [item for item in checks if not item["critical"] and item["status"] != "pass"]
    status = "healthy" if not failed_critical and not failed_review else "degraded" if not failed_critical else "unhealthy"

    return {
        "ok": not failed_critical,
        "status": status,
        "version": APP_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope": "local-runtime-contract",
        "live_upstream_checks_performed": False,
        "summary": {
            "checks": len(checks),
            "passed": sum(item["status"] == "pass" for item in checks),
            "failed": sum(item["status"] != "pass" for item in checks),
            "required_assets": len(assets),
            "available_assets": sum(item["status"] == "available" for item in assets),
            "known_map_surfaces": len(surfaces),
            "declared_map_surfaces": sum(item["status"] == "declared" for item in surfaces),
        },
        "checks": checks,
        "assets": assets,
        "map_surfaces": surfaces,
        "endpoint_contracts": [
            {"path": path, "status": "declared", "live_check": False} for path in CRITICAL_PUBLIC_ENDPOINTS
        ],
        "embed_policy": {
            "public_embeds_enabled": bool(settings.public_embeds_enabled),
            "frame_policy": "configured-origin-csp" if settings.public_embeds_enabled else "same-origin-only",
            "allowed_origin_count": len(settings.cors_origin_list) if settings.public_embeds_enabled else 0,
        },
        "recovery_policy": {
            "leaflet_unavailable": "Use the first-party static geographic grid.",
            "carto_tiles_unavailable": "Retry with OpenStreetMap tiles.",
            "openstreetmap_tiles_unavailable": "Hide the failed tile pane and retain verified overlays on the geographic grid.",
            "imagery_tiles_unavailable": "Keep other layers interactive and expose a degraded-imagery status.",
            "endpoint_unavailable": "Retry transient failures, isolate the affected service group, and use a marked last-known-good public JSON response when available.",
            "service_recovered": "Close the affected circuit and refresh the active workspace once without reloading the full application.",
        },
        "limitations": [
            "This endpoint does not contact third-party APIs or tile providers.",
            "Browser-side diagnostics determine actual map modes, request failures, and service-worker state.",
            "A healthy local contract does not guarantee that every upstream public data service is currently available.",
        ],
    }
