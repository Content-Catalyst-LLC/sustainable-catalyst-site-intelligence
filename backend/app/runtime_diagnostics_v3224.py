"""Public-safe runtime diagnostics for Site Intelligence v4.22.0.

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
    "assets/vector-cartography-v3230.css",
    "assets/vector-cartography-v3230.js",
    "assets/world-cartography-v3230.geojson",
    "assets/runtime-v3230.css",
    "assets/runtime-v3230.js",
    "assets/embed-isolation-v32363.css",
    "assets/embed-isolation-v32363.js",
    "assets/cartographic-workspace-v3230.css",
    "assets/cartographic-workspace-v3230.js",
    "assets/cartographic-interaction-v3232.css",
    "assets/cartographic-interaction-v3232.js",
    "assets/analytical-workspaces-v3234.css",
    "assets/analytical-workspaces-v3234.js",
    "assets/browser-reliability-v3235.css",
    "assets/browser-reliability-v3235.js",
    "assets/performance-offline-v3236.css",
    "assets/bootstrap-v32361.js",
    "assets/startup-stability-v32364.js",
    "assets/performance-offline-v3236.js",
    "assets/data-truth-v32371.css",
    "assets/data-truth-v32371.js",
    "assets/record-provenance-v3238.css",
    "assets/record-provenance-v3238.js",
    "assets/production-truth-v3231.css",
    "assets/production-truth-v3231.js",
    "assets/service-recovery-v3224.js",
    "assets/app.css",
    "assets/app.js",
    "assets/spatial-v2150.css",
    "assets/spatial-v2150.js",
)

CRITICAL_PUBLIC_ENDPOINTS = (
    "/health",
    "/public/build-info",
    "/public/release-gate",
    "/public/geospatial/diagnostics",
    "/public/geospatial/events",
    "/public/spatial",
    "/public/spatial/areas",
    "/public/runtime-health",
    "/public/runtime-recovery",
    "/public/workspaces/production-truth",
    "/public/maps/interaction",
    "/public/workflows/analytical",
    "/public/browser-reliability",
    "/public/performance-offline",
    "/public/bootstrap-recovery",
    "/public/mutation-observer-recovery",
    "/public/embed-isolation",
    "/public/startup-stability",
    "/public/data-truth",
    "/public/data-truth/countries",
    "/public/data-truth/coverage-matrix",
    "/public/data-truth/country/KEN",
    "/public/record-truth/country/KEN",
    "/public/record-truth/indicator/KEN/SP.POP.TOTL",
    "/public/record-truth/manifest",
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

    fallback_js = "/app/assets/vector-cartography-v3230.js"
    recovery_js = "/app/assets/service-recovery-v3224.js"
    runtime_js = "/app/assets/runtime-v3230.js"
    workspace_js = "/app/assets/cartographic-workspace-v3230.js"
    interaction_js = "/app/assets/cartographic-interaction-v3232.js"
    app_js = "/app/assets/app.js"
    browser_reliability_js = "/app/assets/browser-reliability-v3235.js"
    bootstrap_js = "/app/assets/bootstrap-v32361.js"
    performance_offline_js = "/app/assets/performance-offline-v3236.js"
    startup_stability_js = "/app/assets/startup-stability-v32364.js"
    data_truth_js = "/app/assets/data-truth-v32371.js"
    record_truth_js = "/app/assets/record-provenance-v3238.js"
    production_truth_js = "/app/assets/production-truth-v3231.js"
    ordered_scripts = all(token in index_html for token in (fallback_js, recovery_js, runtime_js, startup_stability_js, bootstrap_js, performance_offline_js, workspace_js, interaction_js, app_js, browser_reliability_js, data_truth_js, record_truth_js, production_truth_js))
    if ordered_scripts:
        ordered_scripts = (
            index_html.index(fallback_js)
            < index_html.index(recovery_js)
            < index_html.index(runtime_js)
            < index_html.index(startup_stability_js)
            < index_html.index(bootstrap_js)
            < index_html.index(performance_offline_js)
            < index_html.index(app_js)
            < index_html.index(workspace_js)
            < index_html.index(interaction_js)
            < index_html.index(browser_reliability_js)
            < index_html.index(data_truth_js)
            < index_html.index(record_truth_js)
            < index_html.index(production_truth_js)
        )

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
            "First-party map and fault-isolation runtimes load before application modules",
            ordered_scripts,
            "First-party map runtime → service recovery → runtime diagnostics → application → cartographic workspace order is enforced." if ordered_scripts else "Required script order is incomplete.",
        ),
        _check(
            "first-party-map-runtime",
            "Map startup has no blocking third-party JavaScript dependency",
            "unpkg.com/leaflet" not in index_html and "cdn.jsdelivr.net/npm/leaflet" not in index_html and "__scsiSelfHosted" in _read(PUBLIC_APP_DIR / "assets/vector-cartography-v3230.js") and (PUBLIC_APP_DIR / "assets/world-cartography-v3230.geojson").is_file(),
            "The vector cartography engine, real raster tile renderer, local country labels, and local world geometry are packaged before application modules.",
        ),
        _check(
            "offline-shell",
            "Offline shell contains the reliability assets",
            all(name in worker for name in ("vector-cartography-v3230.js", "vector-cartography-v3230.css", "world-cartography-v3230.geojson", "runtime-v3230.js", "runtime-v3230.css", "cartographic-workspace-v3230.js", "cartographic-workspace-v3230.css", "cartographic-interaction-v3232.js", "cartographic-interaction-v3232.css", "analytical-workspaces-v3234.js", "analytical-workspaces-v3234.css", "bootstrap-v32361.js", "startup-stability-v32364.js", "performance-offline-v3236.js", "performance-offline-v3236.css", "data-truth-v32371.js", "data-truth-v32371.css", "record-provenance-v3238.js", "record-provenance-v3238.css", "production-truth-v3231.js", "production-truth-v3231.css", "service-recovery-v3224.js")) and f'const RELEASE="{APP_VERSION}"' in worker,
            "Service worker release and runtime assets are aligned." if worker else "Service worker is missing or unreadable.",
        ),
        _check(
            "mutation-observer-recovery",
            "Map summaries cannot trigger an unbounded observer loop",
            all(token in _read(PUBLIC_APP_DIR / "assets/browser-reliability-v3235.js") for token in ("summary.textContent!==nextText", "requestAnimationFrame(flushMapSummaries)", "state.observer?.disconnect()", "MAX_SUMMARY_PASSES_PER_SECOND=8")),
            "Map-summary updates are idempotent, frame-debounced, disconnected during writes, and bounded per second.",
        ),
        _check(
            "fixed-wordpress-embed-isolation",
            "The complete WordPress application uses a fixed isolated viewport",
            all(token in _read(PUBLIC_APP_DIR / "assets/embed-isolation-v32363.js") for token in ("wordpress-fixed", "SCSI_FIXED_WORDPRESS_EMBED", "heightMessagesEnabled")) and all(token in _read(PUBLIC_APP_DIR / "assets/app.js") for token in ("FIXED_WORDPRESS_EMBED", "if(FIXED_WORDPRESS_EMBED)return")),
            "WordPress application mode disables child height negotiation and keeps scrolling inside the fixed viewport.",
        ),
        _check(
            "startup-stability-and-worker-closure",
            "The application shell is independent from data hydration and service-worker updates cannot force reloads",
            all(token in _read(PUBLIC_APP_DIR / "assets/app.js") for token in ("Promise.allSettled", "launchFinished", "routeTransitionActive")) and all(token in _read(PUBLIC_APP_DIR / "assets/bootstrap-v32361.js") for token in ("automaticReloads:0", "activateWaitingWorker", "automaticReload:false")) and "event.waitUntil(installCritical())" in worker and "installCritical().then(()=>self.skipWaiting())" not in worker,
            "The shell fail-opens, startup data hydrates in the background, route changes are serialized, and service-worker activation never forces a current-session reload.",
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
            "map_engine": "Use the vector cartography engine with local Natural Earth country boundaries and labels.",
            "carto_tiles_unavailable": "Retry with OpenStreetMap tiles.",
            "openstreetmap_tiles_unavailable": "Retain local world boundaries, geographic controls, and verified overlays without lowering application health.",
            "imagery_tiles_unavailable": "Keep the local basemap and other layers interactive; report imagery as limited without degrading the application.",
            "endpoint_unavailable": "Retry transient failures, isolate the affected service group, and use a marked last-known-good public JSON response when available.",
            "service_recovered": "Close the affected circuit and refresh the active workspace through the serialized route queue without reloading the full application.",
            "service_worker_update": "Keep the current application session stable; activate explicitly or on a later navigation without an automatic reload.",
        },
        "limitations": [
            "This endpoint does not contact third-party APIs or tile providers.",
            "Browser-side diagnostics determine actual map modes, visible-workspace failures, and service-worker state.",
            "A healthy local contract does not guarantee that every upstream public data service is currently available.",
        ],
    }
