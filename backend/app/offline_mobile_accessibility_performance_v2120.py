"""Offline, mobile, accessibility, performance, and embed reliability controls.

v2.12.1 is a production reliability patch over the v2.12.0 delivery layer. It
publishes public-safe diagnostics for service-worker upgrades, bounded cache
retention, cache recovery, responsive embeds, and release-version alignment.
It does not claim formal accessibility certification, guarantee offline
freshness, or persist a hosted user profile.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any

from .experience_quality import (
    ACCESSIBILITY_TARGET,
    MOBILE_BREAKPOINTS,
    PERFORMANCE_BUDGETS,
    experience_checklist,
    experience_diagnostics,
)
from .version import APP_VERSION

VERSION = APP_VERSION
SCHEMA = "sc-site-intelligence-offline-mobile-accessibility-performance/1.1"
CACHE_SCHEMA = "sc-site-intelligence-offline-cache-plan/1.1"
RELIABILITY_SCHEMA = "sc-site-intelligence-delivery-reliability/1.0"
RELEASE_NAME = "Production Offline, Mobile, and Embed Reliability Patch"


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
        "release_name": RELEASE_NAME,
        "generated_at": _now(),
        "state": "ready" if cfg["enabled"] else "disabled",
        "capabilities": [
            "resilient partial application-shell installation",
            "service-worker upgrade activation and old-cache removal",
            "bounded and age-limited browser-local public-data cache",
            "offline cache reset and corruption recovery controls",
            "version-aligned application, manifest, service worker, and WordPress plugin",
            "responsive source-checked WordPress iframe resizing",
            "mobile safe-area and viewport-height delivery",
            "browser-local low-bandwidth mode",
            "keyboard, focus, reduced-motion, and forced-color contracts",
            "first-party performance budgets",
        ],
        "privacy": {
            "telemetry_added": False,
            "accounts_added": False,
            "server_profile_storage_added": False,
            "offline_data_location": "browser cache and local storage",
            "embed_height_messages_contain_evidence": False,
        },
        "limits": [
            "Offline content can become stale and must display its cached state.",
            "External map tiles, imagery, and third-party libraries may not be available offline.",
            "Automated checks are not a WCAG certification or substitute for assistive-technology review.",
            "The browser or operating system can evict cached data at any time.",
            "Iframe resizing is constrained by origin and source-window checks in the WordPress host.",
        ],
        "links": {
            "workspace": "/app/?view=experience",
            "manifest": "/app/manifest.webmanifest",
            "service_worker": "/app/service-worker.js",
            "offline": "/app/offline.html",
            "reliability": "/public/offline-experience/reliability",
        },
    }


def build_cache_plan(settings: Any = None) -> dict[str, Any]:
    cfg = delivery_config(settings)
    root = Path(__file__).resolve().parents[2] / "backend" / "public_app" / "assets"
    asset_urls = sorted(
        f"/app/assets/{path.name}"
        for path in root.iterdir()
        if path.is_file() and path.suffix.lower() in {".js", ".css", ".png"}
    )
    shell = ["/app/", "/app/offline.html", "/app/manifest.webmanifest", *asset_urls]
    return {
        "ok": True,
        "schema": CACHE_SCHEMA,
        "version": VERSION,
        "generated_at": _now(),
        "enabled": cfg["enabled"] and cfg["service_worker_enabled"],
        "cache_prefix": f"scsi-v{VERSION}",
        "cache_names": {"shell": f"scsi-v{VERSION}-shell", "public_data": f"scsi-v{VERSION}-data"},
        "application_shell": shell,
        "installation": {
            "mode": "partial-resilient",
            "minimum_successful_assets": 1,
            "single_optional_asset_failure_aborts_install": False,
        },
        "strategies": {
            "navigation": "network-first with navigation preload, exact cached fallback, application-shell fallback, then offline HTML",
            "first_party_assets": "stale-while-revalidate with release-scoped cache",
            "public_json": "network-first with bounded, age-limited cached fallback",
            "external_tiles_and_imagery": "network-only unless independently cached by the browser or provider",
            "writes": "network-only",
        },
        "limits": {
            "maximum_entries": cfg["offline_cache_max_entries"],
            "maximum_age_hours": cfg["offline_cache_ttl_hours"],
            "shell_maximum_entries": 80,
        },
        "upgrade_policy": {
            "service_worker_script_cache": "no-store",
            "old_release_caches_removed_on_activate": True,
            "waiting_worker_can_activate_immediately": True,
            "controlled_clients_receive_release_message": True,
        },
        "clear_controls": [
            "Clear offline cache in the experience workspace",
            "Reset offline cache from the offline fallback page",
            "Reset low-bandwidth preference",
            "Remove the installed application through browser or operating-system settings",
        ],
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
        "manual_review": [
            "screen-reader traversal",
            "keyboard-only review",
            "200% and 400% browser zoom",
            "real-device touch testing",
            "embedded WordPress page review on iOS and Android",
            "forced-colors review",
            "representative slow-network and offline-upgrade review",
        ],
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
        "delivery": {
            "compression": "gzip",
            "asset_cache": "short public cache with stale-while-revalidate and release-scoped service-worker cache",
            "application_html": "no-store and must-revalidate",
            "service_worker_script": "no-store and updateViaCache none",
            "optional_capture_library": "lazy-loaded",
        },
        "measurement_boundary": "First-party application shell only; external maps, imagery, fonts, and provider latency are reported separately.",
    }


def build_reliability(settings: Any = None) -> dict[str, Any]:
    cfg = delivery_config(settings)
    return {
        "ok": True,
        "schema": RELIABILITY_SCHEMA,
        "version": VERSION,
        "release_name": RELEASE_NAME,
        "generated_at": _now(),
        "release_alignment": {
            "backend": VERSION,
            "expected_wordpress_plugin": VERSION,
            "service_worker_cache_generation": f"scsi-v{VERSION}",
            "manifest_release_parameter": VERSION,
        },
        "service_worker": {
            "partial_install_recovery": True,
            "navigation_preload": True,
            "old_cache_cleanup": True,
            "bounded_public_cache": True,
            "age_limited_public_cache": True,
            "message_channel_clear_acknowledgement": True,
        },
        "embeds": {
            "source_window_checked": True,
            "origin_checked": True,
            "height_messages_throttled": True,
            "mobile_minimum_height": 760,
            "desktop_minimum_height": 620,
            "maximum_height": 2600,
            "open_in_new_tab_fallback": True,
        },
        "cache_limits": {
            "public_entries": cfg["offline_cache_max_entries"],
            "public_age_hours": cfg["offline_cache_ttl_hours"],
        },
        "production_checks": [
            "logged-out WordPress embed loads without REST authentication",
            "iframe height adjusts after route and content changes",
            "service worker upgrades from the previous release without retaining old caches",
            "offline fallback can clear corrupted Site Intelligence caches",
            "application, plugin, service worker, and response headers report the same release",
            "mobile layout is reviewed at 320, 375, 390, 768, and 1024 CSS pixels",
        ],
    }


def build_diagnostics(settings: Any = None) -> dict[str, Any]:
    root = Path(__file__).resolve().parents[2]
    files = {
        "manifest": root / "backend/public_app/manifest.webmanifest",
        "service_worker": root / "backend/public_app/service-worker.js",
        "offline_page": root / "backend/public_app/offline.html",
        "workspace_js": root / "backend/public_app/assets/experience-v2120.js",
        "workspace_css": root / "backend/public_app/assets/experience-v2120.css",
        "application_js": root / "backend/public_app/assets/app.js",
        "wordpress_plugin": root / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php",
        "wordpress_js": root / "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js",
    }
    checks = {f"{name}_present": path.exists() and path.stat().st_size > 0 for name, path in files.items()}
    if files["service_worker"].exists():
        sw = files["service_worker"].read_text(encoding="utf-8")
        checks.update(
            {
                "service_worker_versioned": f'const RELEASE="{VERSION}"' in sw,
                "offline_fallback": "/app/offline.html" in sw,
                "no_write_caching": 'request.method!=="GET"' in sw,
                "bounded_cache": "trimCache" in sw and "MAX_DATA_ENTRIES" in sw,
                "age_limited_cache": "MAX_DATA_AGE_MS" in sw,
                "partial_install_recovery": "Promise.allSettled" in sw,
                "old_cache_cleanup": "!key.startsWith(VERSION)" in sw,
            }
        )
    if files["manifest"].exists():
        manifest = json.loads(files["manifest"].read_text(encoding="utf-8"))
        checks.update(
            {
                "manifest_standalone": manifest.get("display") == "standalone",
                "manifest_scope": manifest.get("scope") == "/app/",
                "manifest_release_aligned": VERSION in str(manifest.get("start_url", "")),
                "manifest_shortcuts": len(manifest.get("shortcuts", [])) >= 3,
            }
        )
    if files["application_js"].exists():
        app_js = files["application_js"].read_text(encoding="utf-8")
        checks.update(
            {
                "frontend_version_aligned": f'APP_VERSION="{VERSION}"' in app_js,
                "service_worker_update_cache_disabled": 'updateViaCache:"none"' in app_js,
                "embed_height_release_message": "scsi-height" in app_js and "version:APP_VERSION" in app_js,
            }
        )
    if files["wordpress_plugin"].exists():
        plugin = files["wordpress_plugin"].read_text(encoding="utf-8")
        checks.update(
            {
                "wordpress_version_aligned": f"Version: {VERSION}" in plugin and f"const VERSION = '{VERSION}';" in plugin,
                "wordpress_embed_asset_loaded": "sc-site-intelligence.js" in plugin,
            }
        )
    if files["wordpress_js"].exists():
        wp_js = files["wordpress_js"].read_text(encoding="utf-8")
        checks.update(
            {
                "wordpress_origin_check": "event.origin !== record.origin" in wp_js,
                "wordpress_source_window_check": "event.source !== record.frame.contentWindow" in wp_js,
                "wordpress_resize_observer": "setupResponsiveEmbeds" in wp_js,
            }
        )
    return {
        "ok": all(checks.values()),
        "schema": SCHEMA,
        "version": VERSION,
        "generated_at": _now(),
        "checks": checks,
        "config": delivery_config(settings),
        "accessibility_certification": "none",
        "offline_freshness_guaranteed": False,
    }
