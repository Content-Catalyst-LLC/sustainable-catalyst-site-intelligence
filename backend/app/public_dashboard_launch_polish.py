from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

VERSION = "1.13.0"
SCHEMA_VERSION = "sc-public-dashboard-launch-polish/1.0"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def launch_manifest() -> dict[str, Any]:
    return {
        "ok": True,
        "version": VERSION,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _now(),
        "release_status": "launch-ready",
        "experience_principles": [
            "clear public navigation",
            "mobile-first responsive layouts",
            "keyboard-visible interactive controls",
            "screen-reader-readable status changes",
            "plain-language source and freshness notes",
            "accessible table alternatives for every visual",
            "stable share and export states",
        ],
        "public_states": {
            "loading": {"label": "Loading current evidence", "aria_live": "polite"},
            "ready": {"label": "Current dashboard view", "aria_live": "polite"},
            "empty": {"label": "No matching records", "guidance": "Change geography, date range, or comparison filters."},
            "stale": {"label": "Showing last-known-good data", "guidance": "The source is temporarily delayed or unavailable."},
            "error": {"label": "Dashboard temporarily unavailable", "guidance": "Source notes and methodology remain available."},
        },
        "navigation": [
            {"id": "dashboard-directory", "label": "Dashboards"},
            {"id": "country-intelligence", "label": "Country Profiles"},
            {"id": "cross-domain-comparison", "label": "Compare Places"},
            {"id": "sources", "label": "Sources"},
            {"id": "methodology", "label": "Methodology"},
            {"id": "exports", "label": "Exports"},
        ],
        "launch_checks": launch_readiness()["checks"],
    }


def launch_readiness() -> dict[str, Any]:
    checks = [
        ("responsive_layouts", "Responsive layouts", "pass", "Dashboard cards, filters, tables, and navigation stack cleanly on narrow screens."),
        ("keyboard_access", "Keyboard access", "pass", "Interactive controls retain visible focus and semantic button/link behavior."),
        ("screen_reader_status", "Screen-reader status", "pass", "Loading, empty, stale, and error regions use concise live-region text."),
        ("accessible_tables", "Accessible tables", "pass", "Every configured visual retains a table fallback contract."),
        ("share_state", "Shareable state", "pass", "Dashboard, geography, comparison, date, and view settings remain URL-safe and exclude personal data."),
        ("source_transparency", "Source transparency", "pass", "Source, freshness, methodology, and last-known-good states remain visible."),
        ("export_reliability", "Export reliability", "pass", "JSON, CSV-ready, brief, and print-ready contracts remain available."),
        ("browser_qa", "Browser visual QA", "review", "Complete final review in current Chrome, Safari, Firefox, and mobile browsers after deployment."),
        ("performance_qa", "Performance QA", "review", "Confirm production cache, compression, and Core Web Vitals after Render and WordPress deployment."),
    ]
    return {
        "ok": True,
        "version": VERSION,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _now(),
        "status": "launch-ready-with-production-qa",
        "counts": {
            "pass": sum(1 for _, _, status, _ in checks if status == "pass"),
            "review": sum(1 for _, _, status, _ in checks if status == "review"),
        },
        "checks": [
            {"id": cid, "label": label, "status": status, "detail": detail}
            for cid, label, status, detail in checks
        ],
        "production_actions": [
            "Deploy the v1.13.0 backend and confirm the root endpoint reports version 1.13.0.",
            "Install the v1.13.0 WordPress plugin and clear WordPress and Cloudflare caches.",
            "Review the four flagship dashboards on desktop, tablet, and mobile.",
            "Test keyboard navigation, visible focus, loading states, empty states, and exports.",
            "Capture final screenshots for the Site Intelligence landing page and release notes.",
        ],
    }


def public_navigation() -> dict[str, Any]:
    manifest = launch_manifest()
    return {
        "ok": True,
        "version": VERSION,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _now(),
        "items": manifest["navigation"],
        "default_dashboard": "climate-human-vulnerability",
        "public_copy": {
            "eyebrow": "Sustainable Catalyst Site Intelligence",
            "title": "Public Intelligence Dashboards",
            "summary": "Explore source-aware evidence across planetary boundaries, human development, disasters, conflict, displacement, and international law.",
        },
    }
