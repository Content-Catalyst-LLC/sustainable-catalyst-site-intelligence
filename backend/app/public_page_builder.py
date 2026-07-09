from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from .config import Settings


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def public_shortcode_bundles() -> Dict[str, Any]:
    bundles: List[Dict[str, Any]] = [
        {
            "id": "flagship_complete",
            "name": "Flagship public dashboard",
            "visibility": "public",
            "recommended_page_type": "Public Site Intelligence landing page",
            "shortcode": "[sc_site_intelligence_public_flagship]",
            "sections": [
                "Public dashboard hero",
                "Public Site Intelligence",
                "Knowledge overview",
                "Climate, energy, and external source snapshot",
                "Public methodology",
            ],
            "notes": "Recommended default for a polished public dashboard page. Uses public-safe shortcodes only.",
        },
        {
            "id": "public_core_stack",
            "name": "Public core stack",
            "visibility": "public",
            "recommended_page_type": "Custom public dashboard layout",
            "shortcode": "[sc_site_intelligence_public_landing]\n\n[sc_public_site_intelligence]\n\n[sc_public_knowledge_overview]\n\n[sc_public_climate_energy_summary]\n\n[sc_public_methodology]",
            "sections": ["Landing", "Aggregated site intelligence", "Knowledge overview", "External-source snapshot", "Methodology"],
            "notes": "Use when the page already has custom editorial copy and you want the canonical public module sequence.",
        },
        {
            "id": "compact_public_overview",
            "name": "Compact public overview",
            "visibility": "public",
            "recommended_page_type": "Homepage or Platform page inset",
            "shortcode": "[sc_site_intelligence_public_landing]\n\n[sc_public_knowledge_overview]",
            "sections": ["Landing", "Knowledge overview"],
            "notes": "Best for a shorter overview block that links readers to the full dashboard.",
        },
        {
            "id": "external_sources_public",
            "name": "Climate and external-source snapshot",
            "visibility": "public",
            "recommended_page_type": "Climate, energy, environment, or dashboard source-note page",
            "shortcode": "[sc_public_climate_energy_summary]\n\n[sc_public_methodology]",
            "sections": ["External-source snapshot", "Methodology"],
            "notes": "Use for a focused public source snapshot; leave live mode off for fast stable rendering.",
        },
        {
            "id": "private_readiness_review",
            "name": "Private public-readiness review",
            "visibility": "private",
            "recommended_page_type": "Internal admin/review page",
            "shortcode": "[sc_public_dashboard_readiness]\n\n[sc_site_intelligence_public_page_builder]\n\n[sc_public_dashboard_shortcode_bundle]",
            "sections": ["Readiness checks", "Page-builder guidance", "Copyable bundles"],
            "notes": "Keep this private; it includes placement guidance and readiness review context.",
        },
    ]
    return {
        "ok": True,
        "generated_at": _now(),
        "title": "Public Dashboard Shortcode Bundles",
        "summary": "Copy-ready shortcode bundles for building public-safe Site Intelligence pages without exposing internal analytics or admin diagnostics.",
        "bundles": bundles,
    }


def public_page_builder(settings: Settings) -> Dict[str, Any]:
    bundles = public_shortcode_bundles()["bundles"]
    flagship_shortcode = bundles[0]["shortcode"]
    canonical_stack = bundles[1]["shortcode"]
    return {
        "ok": True,
        "generated_at": _now(),
        "version": settings.version,
        "title": "Public Flagship Dashboard Page Builder",
        "eyebrow": "Site Intelligence Public Release Builder",
        "summary": "A public-safe page-building layer for assembling the flagship Sustainable Catalyst Site Intelligence dashboard from reviewed shortcodes, methodology notes, and public-only defaults.",
        "mode": "public_safe_builder",
        "public_defaults": {
            "raw_analytics_exposed": False,
            "private_reports_exposed": False,
            "admin_diagnostics_exposed": False,
            "live_external_calls_required": False,
            "recommended_live_external_mode": False,
            "public_dashboards_enabled": settings.public_dashboards_enabled,
        },
        "flagship_shortcode": flagship_shortcode,
        "canonical_stack": canonical_stack,
        "page_presets": [
            {
                "id": "flagship_public_dashboard",
                "name": "Flagship Public Dashboard",
                "status": "recommended",
                "visibility": "public",
                "description": "Full public-facing Site Intelligence dashboard with hero, public overview, knowledge map signal, climate/energy snapshot, and methodology.",
                "shortcode": "[sc_site_intelligence_public_flagship]",
            },
            {
                "id": "platform_overview_inset",
                "name": "Platform Overview Inset",
                "status": "ready",
                "visibility": "public",
                "description": "Shorter dashboard introduction suitable for Platform, Demos, or homepage sections.",
                "shortcode": "[sc_site_intelligence_public_landing]\n\n[sc_public_knowledge_overview]",
            },
            {
                "id": "methodology_and_sources",
                "name": "Methodology and Sources Page",
                "status": "ready",
                "visibility": "public",
                "description": "Public explanation of what the dashboard shows, what it hides, and how external-source notes should be interpreted.",
                "shortcode": "[sc_public_climate_energy_summary]\n\n[sc_public_methodology]",
            },
            {
                "id": "internal_release_review",
                "name": "Internal Release Review",
                "status": "private_only",
                "visibility": "private",
                "description": "Internal quality-control page for readiness, shortcode placement, and public/private boundaries.",
                "shortcode": "[sc_public_dashboard_readiness]\n\n[sc_site_intelligence_public_page_builder]\n\n[sc_public_dashboard_shortcode_bundle]",
            },
        ],
        "layout_sections": [
            {
                "order": 1,
                "title": "Public dashboard hero",
                "shortcode": "[sc_site_intelligence_public_landing]",
                "visibility": "public",
                "purpose": "Introduces the dashboard as a public-safe knowledge-system and data-source window.",
                "status": "ready",
            },
            {
                "order": 2,
                "title": "Aggregated public Site Intelligence",
                "shortcode": "[sc_public_site_intelligence]",
                "visibility": "public",
                "purpose": "Shows rounded, aggregated public platform signals without exposing raw GA4 or private strategy details.",
                "status": "ready",
            },
            {
                "order": 3,
                "title": "Knowledge overview",
                "shortcode": "[sc_public_knowledge_overview]",
                "visibility": "public",
                "purpose": "Connects Sustainable Catalyst knowledge areas, article maps, and public surfaces.",
                "status": "ready",
            },
            {
                "order": 4,
                "title": "Climate, energy, and external-source snapshot",
                "shortcode": "[sc_public_climate_energy_summary]",
                "visibility": "public",
                "purpose": "Displays stable public-safe source snapshots with methodology and fallback awareness.",
                "status": "ready",
            },
            {
                "order": 5,
                "title": "Public methodology",
                "shortcode": "[sc_public_methodology]",
                "visibility": "public",
                "purpose": "Explains boundaries, source notes, aggregation, review requirements, and non-advice limitations.",
                "status": "ready",
            },
        ],
        "editorial_copy": {
            "intro": "Sustainable Catalyst Site Intelligence is a public-safe dashboard framework for showing how the site’s knowledge architecture, public datasets, article maps, and platform tools connect into a larger public-interest research system.",
            "boundary_note": "This dashboard is educational and informational. It does not provide legal, financial, medical, engineering, climate-risk, ESG, assurance, compliance, or investment advice.",
            "source_note": "External-source sections use cached, fallback-aware, or public-stable snapshots unless live mode is explicitly enabled for private testing.",
        },
        "cta_blocks": [
            {"label": "Explore the Research Library", "url": "https://sustainablecatalyst.com/research-library/", "event": "sc_library_nav"},
            {"label": "Open the Workbench", "url": "https://sustainablecatalyst.com/workbench/", "event": "sc_workbench_open"},
            {"label": "View GitHub", "url": "https://github.com/Content-Catalyst-LLC", "event": "sc_repository_click"},
        ],
        "release_checklist": [
            "Use only public shortcodes on public pages.",
            "Leave live=true off for public climate and external-source snapshots.",
            "Keep readiness, admin, reports, Search Console, GA4, and AI internal briefs private unless manually reviewed.",
            "Add methodology notes and non-advice boundaries near public dashboards.",
            "Test the page logged out or in an incognito window before public promotion.",
        ],
        "bundles": bundles,
    }


def public_page_builder_readiness(settings: Settings) -> Dict[str, Any]:
    checks = [
        {
            "id": "public_dashboards_enabled",
            "label": "Public dashboards enabled",
            "status": "pass" if settings.public_dashboards_enabled else "review",
            "detail": "SC_SI_PUBLIC_DASHBOARDS_ENABLED controls whether public endpoints are intended for public display.",
        },
        {
            "id": "safe_shortcode_stack",
            "label": "Public shortcode stack available",
            "status": "pass",
            "detail": "The flagship shortcode uses only public-safe modules and local presentation copy.",
        },
        {
            "id": "live_external_default",
            "label": "Live external data not required",
            "status": "pass",
            "detail": "Public climate/energy sections default to stable public snapshots rather than blocking live connector calls.",
        },
        {
            "id": "private_modules_excluded",
            "label": "Private modules excluded from public preset",
            "status": "pass",
            "detail": "GA4 dashboards, Search Console reports, admin controls, raw reports, and private AI briefs are not included in the flagship public preset.",
        },
        {
            "id": "methodology_included",
            "label": "Public methodology included",
            "status": "pass",
            "detail": "The flagship layout includes a methodology and limitations section by default.",
        },
    ]
    score = round(100 * sum(1 for item in checks if item["status"] == "pass") / max(1, len(checks)), 1)
    return {
        "ok": True,
        "generated_at": _now(),
        "version": settings.version,
        "title": "Public Flagship Dashboard Readiness",
        "score": score,
        "status": "public_ready" if score >= 90 else "public_candidate" if score >= 70 else "internal_review",
        "checks": checks,
        "recommended_shortcode": "[sc_site_intelligence_public_flagship]",
        "notes": [
            "The page builder is public-safe by design, but final editorial copy should still be reviewed before promotion.",
            "Use private readiness and diagnostic shortcodes only on internal pages.",
        ],
    }
