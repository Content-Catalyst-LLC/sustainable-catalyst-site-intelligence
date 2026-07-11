from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .version import APP_VERSION

PROFILE_SCHEMA = "sc-experience-profile/1.0"
ACCESSIBILITY_TARGET = "WCAG 2.2 Level AA target; not a third-party certification"

PERFORMANCE_BUDGETS = {
    "first_party_javascript_bytes": 260_000,
    "first_party_css_bytes": 100_000,
    "application_html_bytes": 140_000,
    "first_party_shell_bytes": 500_000,
}

MOBILE_BREAKPOINTS = {
    "compact_phone": 480,
    "phone": 760,
    "tablet": 1050,
}

REQUIRED_HEADERS = {
    "x-content-type-options": "nosniff",
    "referrer-policy": "strict-origin-when-cross-origin",
    "permissions-policy": "camera=(), microphone=(), geolocation=()",
}

def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]

def _file_sizes() -> dict[str, int]:
    root = _repo_root()
    paths = {
        "application_html_bytes": root / "backend/public_app/index.html",
        "first_party_javascript_bytes": root / "backend/public_app/assets/app.js",
        "first_party_css_bytes": root / "backend/public_app/assets/app.css",
    }
    sizes = {key: path.stat().st_size for key, path in paths.items()}
    sizes["first_party_shell_bytes"] = sum(sizes.values())
    return sizes

def experience_profile() -> dict[str, Any]:
    return {
        "ok": True,
        "schema": PROFILE_SCHEMA,
        "application_version": APP_VERSION,
        "release": "Accessibility, Performance, and Mobile Release",
        "accessibility_target": ACCESSIBILITY_TARGET,
        "principles": [
            "Keyboard access and visible focus are required for public controls.",
            "Motion is reduced when the operating system requests reduced motion.",
            "Color is not the only carrier of status or meaning.",
            "Maps and charts retain text, table, source, or status alternatives.",
            "Mobile navigation must expose every public research workspace.",
            "Performance improvements must not hide data state or source provenance.",
        ],
        "mobile_breakpoints_css_px": MOBILE_BREAKPOINTS,
        "performance_budgets": PERFORMANCE_BUDGETS,
        "delivery": {
            "compression": "gzip for eligible responses",
            "application_html_cache": "no-cache",
            "application_asset_cache": "short public cache with stale-while-revalidate",
            "optional_png_library": "loaded on demand only when a PNG export is requested",
            "below_fold_rendering": "content-visibility where supported",
        },
        "privacy": {
            "telemetry_added": False,
            "accounts_added": False,
            "server_profile_storage_added": False,
        },
    }

def experience_checklist() -> dict[str, Any]:
    groups = [
        {
            "id": "keyboard-and-focus",
            "title": "Keyboard and focus",
            "status": "implemented",
            "checks": ["skip links", "visible focus rings", "aria-current navigation", "escape-close overlays", "route announcements"],
        },
        {
            "id": "motion-and-contrast",
            "title": "Motion and contrast",
            "status": "implemented",
            "checks": ["prefers-reduced-motion", "forced-colors support", "text status labels", "no autoplay under reduced motion"],
        },
        {
            "id": "mobile-navigation",
            "title": "Mobile navigation",
            "status": "implemented",
            "checks": ["drawer navigation", "all routes visible", "safe-area padding", "44px design touch targets", "no fixed five-item route truncation"],
        },
        {
            "id": "performance-delivery",
            "title": "Performance and delivery",
            "status": "implemented",
            "checks": ["gzip middleware", "explicit cache policy", "lazy optional PNG dependency", "content visibility", "throttled embed height messages"],
        },
        {
            "id": "manual-review",
            "title": "Manual review still required",
            "status": "review-required",
            "checks": ["screen-reader traversal", "browser zoom at 200 and 400 percent", "real-device touch testing", "representative network throttling", "external map-tile behavior"],
        },
    ]
    return {
        "ok": True,
        "schema": PROFILE_SCHEMA,
        "application_version": APP_VERSION,
        "certification": "none",
        "groups": groups,
    }

def experience_diagnostics() -> dict[str, Any]:
    root = _repo_root()
    html = (root / "backend/public_app/index.html").read_text(encoding="utf-8")
    css = (root / "backend/public_app/assets/app.css").read_text(encoding="utf-8")
    js = (root / "backend/public_app/assets/app.js").read_text(encoding="utf-8")
    php = (root / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text(encoding="utf-8")
    sizes = _file_sizes()
    budget_checks = {
        key: sizes[key] <= limit for key, limit in PERFORMANCE_BUDGETS.items()
    }
    checks = {
        "viewport_fit_cover": "viewport-fit=cover" in html,
        "mobile_navigation_toggle": 'id="mobileNavToggle"' in html,
        "mobile_navigation_backdrop": 'id="mobileNavBackdrop"' in html,
        "route_live_region": 'id="routeAnnouncement"' in html and 'aria-live="polite"' in html,
        "deferred_first_party_script": 'src="/app/assets/app.js" defer' in html,
        "optional_png_library_not_eager": "html2canvas.min.js" not in html,
        "reduced_motion_css": "prefers-reduced-motion:reduce" in css or "prefers-reduced-motion: reduce" in css,
        "forced_colors_css": "forced-colors:active" in css or "forced-colors: active" in css,
        "safe_area_css": "env(safe-area-inset-bottom)" in css,
        "content_visibility_css": "content-visibility:auto" in css or "content-visibility: auto" in css,
        "mobile_touch_target_css": "min-height:44px" in css or "min-height: 44px" in css,
        "lazy_png_loader": "ensureHtml2Canvas" in js and "loadScriptOnce" in js,
        "aria_current_navigation": 'setAttribute("aria-current","page")' in js,
        "mobile_drawer_logic": "setMobileNavigation" in js,
        "reduced_motion_logic": "prefers-reduced-motion: reduce" in js,
        "throttled_height_reporting": "requestAnimationFrame" in js and "heightFrame" in js,
        "wordpress_version": "Version: 1.25.0" in php and "const VERSION = '1.25.0';" in php,
        "wordpress_lazy_iframe": 'loading="lazy"' in php,
        "wordpress_clipboard_permission": 'allow="fullscreen; clipboard-write"' in php,
        "wordpress_message_origin_check": "e.origin!==expectedOrigin" in php,
    }
    checks.update({f"budget_{key}": value for key, value in budget_checks.items()})
    return {
        "ok": all(checks.values()),
        "schema": PROFILE_SCHEMA,
        "application_version": APP_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
        "file_sizes": sizes,
        "performance_budgets": PERFORMANCE_BUDGETS,
        "required_response_headers": REQUIRED_HEADERS,
        "manual_review_required": True,
        "notes": [
            "Automated diagnostics verify release contracts, not full assistive-technology conformance.",
            "External Leaflet, map-tile, imagery, and font delivery remain outside the first-party byte budgets.",
        ],
    }
