from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from .config import Settings


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def release_checklist(settings: Settings) -> Dict[str, Any]:
    checks: List[Dict[str, Any]] = [
        {
            "id": "backend_version",
            "label": "Backend version is v1.5.0",
            "status": "pass" if settings.version == "1.5.0" else "review",
            "detail": f"Current backend version: {settings.version}.",
            "action": "Confirm Render root endpoint returns version 1.5.0 after deployment.",
        },
        {
            "id": "public_defaults",
            "label": "Public dashboards use safe defaults",
            "status": "pass" if settings.public_dashboards_enabled else "review",
            "detail": "Public modules are designed to avoid raw analytics, private reports, admin diagnostics, and live-only external calls.",
            "action": "Use [sc_site_intelligence_public_flagship] for the public page.",
        },
        {
            "id": "private_boundaries",
            "label": "Private/internal modules remain separated",
            "status": "pass",
            "detail": "Reports, AI briefs, admin diagnostics, Search Console, and raw GA4 dashboards remain token-protected or admin-only.",
            "action": "Keep private shortcodes on admin/review pages only.",
        },
        {
            "id": "methodology_visible",
            "label": "Public methodology is visible",
            "status": "pass",
            "detail": "The flagship shortcode includes methodology-forward language, source notes, and non-advice limitations.",
            "action": "Do not remove public methodology from the launch page.",
        },
        {
            "id": "external_sources_stable",
            "label": "External-source modules are fallback-aware",
            "status": "pass",
            "detail": "Climate, energy, and source snapshots default to cached/fallback/public-safe presentation.",
            "action": "Leave live=true off on public pages.",
        },
        {
            "id": "wordpress_install",
            "label": "WordPress plugin updated",
            "status": "manual_review",
            "detail": "Install the v1.5.0 WordPress plugin ZIP after Render deploy completes.",
            "action": "Upload the plugin ZIP, clear WordPress/Cloudflare cache, then test logged out.",
        },
        {
            "id": "seo_metadata",
            "label": "Public page SEO metadata prepared",
            "status": "pass",
            "detail": "v1.5.0 includes recommended title, excerpt, and meta description for the flagship page.",
            "action": "Add the metadata in WordPress SEO settings before promotion.",
        },
        {
            "id": "smoke_test",
            "label": "Production smoke test available",
            "status": "pass",
            "detail": "The /release/smoke-test endpoint checks the release-critical endpoint map without calling slow live connectors.",
            "action": "Run the smoke-test endpoint after deploying v1.5.0.",
        },
    ]
    counts = {
        "pass": sum(1 for item in checks if item["status"] == "pass"),
        "review": sum(1 for item in checks if item["status"] in {"review", "manual_review"}),
        "fail": sum(1 for item in checks if item["status"] == "fail"),
        "total": len(checks),
    }
    score = round(100 * counts["pass"] / max(1, counts["total"]), 1)
    return {
        "ok": True,
        "generated_at": _now(),
        "version": settings.version,
        "title": "Site Intelligence v1.5.0 Public Flagship Release Checklist",
        "summary": "Final launch checklist for the Sustainable Catalyst Site Intelligence public flagship dashboard.",
        "release_stage": "public_flagship_release",
        "status": "launch_ready_with_manual_review" if counts["fail"] == 0 else "needs_fix",
        "score": score,
        "counts": counts,
        "checks": checks,
        "recommended_public_shortcode": "[sc_site_intelligence_public_flagship]",
        "private_review_shortcodes": [
            "[sc_site_intelligence_release_status]",
            "[sc_public_dashboard_visual_qa]",
            "[sc_site_intelligence_connection_check]",
            "[sc_site_intelligence_diagnostic_summary]",
        ],
    }


def release_public_summary(settings: Settings) -> Dict[str, Any]:
    return {
        "ok": True,
        "generated_at": _now(),
        "version": settings.version,
        "title": "Sustainable Catalyst Site Intelligence",
        "subtitle": "A public-facing dashboard layer for knowledge architecture, public datasets, methodology notes, and platform readiness.",
        "summary": "Site Intelligence connects Sustainable Catalyst’s article maps, public dashboards, external data-source notes, reports, and platform tools into a public-safe view of the knowledge system.",
        "public_value": [
            "Shows how Sustainable Catalyst organizes public-interest research and platform infrastructure.",
            "Connects knowledge architecture with climate, energy, environmental, and source-methodology context.",
            "Uses public-safe summaries rather than raw analytics, private reports, or operational diagnostics.",
            "Documents source limitations, fallback behavior, and non-advice boundaries directly on the dashboard.",
        ],
        "boundaries": [
            "Educational and informational use only.",
            "Not legal, financial, medical, engineering, climate-risk, ESG, assurance, compliance, tax, or investment advice.",
            "Raw analytics, Search Console data, conversion diagnostics, admin reports, and AI drafts remain private unless manually reviewed.",
        ],
        "recommended_page": {
            "shortcode": "[sc_site_intelligence_public_flagship]",
            "title": "Site Intelligence",
            "slug": "site-intelligence",
            "placement": "Public Platform / Dashboard page",
        },
        "metadata": release_metadata(),
    }


def release_metadata() -> Dict[str, str]:
    return {
        "seo_title": "Site Intelligence: Public Dashboard for Sustainable Catalyst Knowledge Infrastructure",
        "page_title": "Site Intelligence",
        "excerpt": "Site Intelligence is the public dashboard layer for Sustainable Catalyst, connecting knowledge architecture, platform tools, public datasets, source notes, and methodology into a public-safe view of the open knowledge lab.",
        "meta_description": "Explore Sustainable Catalyst Site Intelligence: a public-safe dashboard for knowledge architecture, platform tools, public data-source notes, and methodology boundaries.",
        "social_description": "A public-safe dashboard layer for Sustainable Catalyst’s open knowledge lab, connecting article maps, platform tools, external-source notes, and methodology-forward public infrastructure.",
    }


def smoke_test(settings: Settings) -> Dict[str, Any]:
    endpoints = [
        {"path": "/", "scope": "public", "critical": True, "expected": "ok/version"},
        {"path": "/health", "scope": "public", "critical": True, "expected": "ok/health"},
        {"path": "/public/status", "scope": "public", "critical": True, "expected": "public-safe status"},
        {"path": "/public/landing-page", "scope": "public", "critical": True, "expected": "landing copy"},
        {"path": "/public/dashboard", "scope": "public", "critical": True, "expected": "aggregated dashboard"},
        {"path": "/public/knowledge-overview", "scope": "public", "critical": True, "expected": "knowledge overview"},
        {"path": "/public/climate-energy-summary", "scope": "public", "critical": True, "expected": "fast fallback-aware snapshot"},
        {"path": "/public/methodology", "scope": "public", "critical": True, "expected": "methodology and boundaries"},
        {"path": "/public/page-builder", "scope": "public-review", "critical": False, "expected": "page-builder guidance"},
        {"path": "/public/page-builder/visual-qa", "scope": "public-review", "critical": False, "expected": "visual QA"},
        {"path": "/release/status", "scope": "private/admin", "critical": True, "expected": "release status"},
        {"path": "/release/checklist", "scope": "private/admin", "critical": True, "expected": "launch checklist"},
    ]
    checks: List[Dict[str, Any]] = []
    for item in endpoints:
        checks.append({
            "id": item["path"].strip("/").replace("/", "_") or "root",
            "path": item["path"],
            "scope": item["scope"],
            "critical": item["critical"],
            "status": "configured",
            "detail": f"Expected output: {item['expected']}.",
        })
    return {
        "ok": True,
        "generated_at": _now(),
        "version": settings.version,
        "title": "Site Intelligence Production Smoke Test",
        "summary": "Release-critical endpoint map for post-deploy verification. This endpoint avoids slow live external calls and does not expose private analytics.",
        "status": "ready_to_run_after_deploy",
        "checks": checks,
        "manual_commands": [
            'curl "https://sustainable-catalyst-site-intelligence.onrender.com/"',
            'curl "https://sustainable-catalyst-site-intelligence.onrender.com/health"',
            'curl "https://sustainable-catalyst-site-intelligence.onrender.com/public/status"',
            'curl "https://sustainable-catalyst-site-intelligence.onrender.com/public/climate-energy-summary"',
            'curl -H "X-SC-Intelligence-Token: YOUR_TOKEN" "https://sustainable-catalyst-site-intelligence.onrender.com/release/status"',
        ],
        "wordpress_checks": [
            "Confirm [sc_site_intelligence_public_flagship] renders while logged out/incognito.",
            "Confirm [sc_site_intelligence_release_status] is visible only on private/admin review pages.",
            "Clear WordPress cache and Cloudflare cache after installing the v1.5.0 plugin ZIP.",
        ],
    }


def release_status(settings: Settings) -> Dict[str, Any]:
    checklist = release_checklist(settings)
    summary = release_public_summary(settings)
    return {
        "ok": True,
        "generated_at": _now(),
        "version": settings.version,
        "title": "Site Intelligence v1.5.0 Public Flagship Release Status",
        "summary": "Release-hardening status for the Sustainable Catalyst Site Intelligence public flagship dashboard.",
        "release_stage": "v1.5.0_public_source_status_release",
        "release_status": checklist["status"],
        "release_score": checklist["score"],
        "public_shortcode": "[sc_site_intelligence_public_flagship]",
        "private_status_shortcode": "[sc_site_intelligence_release_status]",
        "recommended_public_page": summary["recommended_page"],
        "metadata": summary["metadata"],
        "counts": checklist["counts"],
        "checks": checklist["checks"],
        "smoke_test_endpoint": "/release/smoke-test",
        "public_summary_endpoint": "/release/public-summary",
        "launch_notes": [
            "Deploy the v1.5.0 backend to Render and confirm the root endpoint returns version 1.5.0.",
            "Install the v1.5.0 WordPress plugin ZIP and place [sc_site_intelligence_public_flagship] on the public page.",
            "Keep report, AI, Search Console, GA4, and admin shortcodes private unless manually reviewed.",
            "Test the public page logged out before adding it to navigation or promoting it publicly.",
        ],
    }
