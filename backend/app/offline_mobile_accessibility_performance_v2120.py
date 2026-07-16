"""Offline, Mobile, Accessibility, and Performance controls for v2.12.0.

This module publishes public-safe delivery capabilities and diagnostics. It does
not claim formal accessibility certification, guarantee offline freshness, or
persist a user profile. Offline preferences and cached application data remain
browser-local and can be cleared by the user at any time.
"""
from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
from typing import Any

from .experience_quality import ACCESSIBILITY_TARGET, MOBILE_BREAKPOINTS, PERFORMANCE_BUDGETS, experience_checklist, experience_diagnostics

VERSION = "2.12.0"
SCHEMA = "sc-site-intelligence-offline-mobile-accessibility-performance/1.0"
CACHE_SCHEMA = "sc-site-intelligence-offline-cache-plan/1.0"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def delivery_config(settings: Any = None) -> dict[str, Any]:
    def get(attr: str, env: str, default: Any) -> Any:
        value = getattr(settings, attr, None) if settings is not None else None
        return value if value is not None else os.getenv(env, default)
    return {
        "enabled": _bool(get("offline_experience_enabled", "SC_SI_OFFLINE_EXPERIENCE_ENABLED", "true"), True),
        "service_worker_enabled": _bool(get("service_worker_enabled", "SC_SI_SERVICE_WORKER_ENABLED", "true"), True),
        "offline_cache_max_entries": max(20, min(int(get("offline_cache_max_entries", "SC_SI_OFFLINE_CACHE_MAX_ENTRIES", 120)), 500)),
        "offline_cache_ttl_hours": max(1, min(int(get("offline_cache_ttl_hours", "SC_SI_OFFLINE_CACHE_TTL_HOURS", 24)), 168)),
        "low_bandwidth_default": _bool(get("low_bandwidth_default", "SC_SI_LOW_BANDWIDTH_DEFAULT", "false"), False),
    }


def build_overview(settings: Any = None) -> dict[str, Any]:
    cfg = delivery_config(settings)
    return {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "release_name": "Offline, Mobile, Accessibility, and Performance",
        "generated_at": _now(),
        "state": "ready" if cfg["enabled"] else "disabled",
        "capabilities": [
            "installable web application manifest",
            "browser service-worker application shell",
            "offline fallback page",
            "browser-local low-bandwidth mode",
            "responsive mobile workspace navigation",
            "keyboard and focus contracts",
            "reduced-motion and forced-color support",
            "first-party performance budgets",
            "text alternatives for maps and charts",
        ],
        "privacy": {"telemetry_added": False, "accounts_added": False, "server_profile_storage_added": False, "offline_data_location": "browser cache and local storage"},
        "limits": [
            "Offline content can become stale and must display its cached state.",
            "External map tiles, imagery, and third-party libraries may not be available offline.",
            "Automated checks are not a WCAG certification or substitute for assistive-technology review.",
            "The browser or operating system can evict cached data at any time.",
        ],
        "links": {"workspace": "/app/?view=experience", "manifest": "/app/manifest.webmanifest", "service_worker": "/app/service-worker.js", "offline": "/app/offline.html"},
    }


def build_cache_plan(settings: Any = None) -> dict[str, Any]:
    cfg = delivery_config(settings)
    root = Path(__file__).resolve().parents[2] / "backend" / "public_app" / "assets"
    asset_urls = sorted(
        f"/app/assets/{path.name}" for path in root.iterdir()
        if path.is_file() and path.suffix.lower() in {".js", ".css", ".png"}
    )
    shell = ["/app/", "/app/offline.html", "/app/manifest.webmanifest", *asset_urls]
    return {
        "ok": True,
        "schema": CACHE_SCHEMA,
        "version": VERSION,
        "generated_at": _now(),
        "enabled": cfg["enabled"] and cfg["service_worker_enabled"],
        "cache_name": "scsi-v2.12.0-shell",
        "application_shell": shell,
        "strategies": {
            "navigation": "network-first with offline HTML fallback",
            "first_party_assets": "stale-while-revalidate",
            "public_json": "network-first with bounded cached fallback",
            "external_tiles_and_imagery": "network-only unless the provider response is already browser-cached",
            "writes": "network-only",
        },
        "limits": {"maximum_entries": cfg["offline_cache_max_entries"], "maximum_age_hours": cfg["offline_cache_ttl_hours"]},
        "clear_controls": ["Clear offline cache", "Reset low-bandwidth preference", "Remove installed application through browser or operating-system settings"],
    }


def build_accessibility(settings: Any = None) -> dict[str, Any]:
    checklist = experience_checklist()
    return {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "generated_at": _now(),
        "target": ACCESSIBILITY_TARGET,
        "certification": "none",
        "mobile_breakpoints_css_px": MOBILE_BREAKPOINTS,
        "groups": checklist["groups"],
        "manual_review": ["screen-reader traversal", "keyboard-only review", "200% and 400% browser zoom", "real-device touch testing", "forced-colors review", "representative slow-network review"],
    }


def build_performance(settings: Any = None) -> dict[str, Any]:
    diagnostic = experience_diagnostics()
    return {
        "ok": diagnostic["ok"],
        "schema": SCHEMA,
        "version": VERSION,
        "generated_at": _now(),
        "budgets": PERFORMANCE_BUDGETS,
        "file_sizes": diagnostic["file_sizes"],
        "budget_checks": {key: diagnostic["file_sizes"][key] <= value for key, value in PERFORMANCE_BUDGETS.items()},
        "delivery": {"compression": "gzip", "asset_cache": "short public cache with stale-while-revalidate", "application_html": "no-cache", "optional_capture_library": "lazy-loaded"},
        "measurement_boundary": "First-party application shell only; external maps, imagery, fonts, and provider latency are reported separately.",
    }


def build_diagnostics(settings: Any = None) -> dict[str, Any]:
    root = Path(__file__).resolve().parents[2]
    files = {
        "manifest": root / "backend/public_app/manifest.webmanifest",
        "service_worker": root / "backend/public_app/service-worker.js",
        "offline_page": root / "backend/public_app/offline.html",
        "workspace_js": root / "backend/public_app/assets/experience-v2120.js",
        "workspace_css": root / "backend/public_app/assets/experience-v2120.css",
    }
    checks = {f"{name}_present": path.exists() and path.stat().st_size > 0 for name, path in files.items()}
    if files["service_worker"].exists():
        sw = files["service_worker"].read_text(encoding="utf-8")
        checks.update({"service_worker_versioned": "scsi-v2.12.0" in sw, "offline_fallback": "/app/offline.html" in sw, "no_write_caching": 'request.method !== "GET"' in sw})
    if files["manifest"].exists():
        manifest = files["manifest"].read_text(encoding="utf-8")
        checks.update({"manifest_standalone": '"display": "standalone"' in manifest, "manifest_start_url": '"start_url": "/app/"' in manifest})
    return {"ok": all(checks.values()), "schema": SCHEMA, "version": VERSION, "generated_at": _now(), "checks": checks, "config": delivery_config(settings), "accessibility_certification": "none", "offline_freshness_guaranteed": False}
