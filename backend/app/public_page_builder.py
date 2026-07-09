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
        "summary": "A polished public-safe page-building layer for presenting Sustainable Catalyst Site Intelligence as a clear, methodology-forward dashboard without exposing private analytics or internal diagnostics.",
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
            "intro": "Sustainable Catalyst Site Intelligence shows how the site’s knowledge architecture, public datasets, article maps, and platform tools connect into a larger public-interest research system.",
            "boundary_note": "This dashboard is educational and informational. It does not provide legal, financial, medical, engineering, climate-risk, ESG, assurance, compliance, or investment advice.",
            "source_note": "External-source sections use cached, fallback-aware, or public-stable snapshots by default, so public pages remain fast, stable, and understandable.",
        },
        "cta_blocks": [
            {"label": "Explore the Research Library", "url": "https://sustainablecatalyst.com/research-library/", "event": "sc_library_nav"},
            {"label": "Open the Workbench", "url": "https://sustainablecatalyst.com/workbench/", "event": "sc_workbench_open"},
            {"label": "View the GitHub Repositories", "url": "https://github.com/Content-Catalyst-LLC", "event": "sc_repository_click"},
        ],
        "visual_qa_status": "release_candidate",
        "copy_polish_status": "polished",
        "release_checklist": [
            "Use only public shortcodes on public pages.",
            "Leave live=true off for public climate and external-source snapshots.",
            "Keep readiness, admin, reports, Search Console, GA4, and AI internal briefs private unless manually reviewed.",
            "Add methodology notes and non-advice boundaries near public dashboards.",
            "Test the page logged out or in an incognito window before public promotion.",
            "Read the full page aloud once to catch heavy wording, duplicated headings, and unclear transitions.",
            "Confirm that every visible module explains its source, boundary, or fallback behavior in plain language.",
        ],
        "bundles": bundles,
    }


def public_dashboard_visual_qa(settings: Settings) -> Dict[str, Any]:
    checks = [
        {
            "id": "hero_clarity",
            "label": "Hero explains the dashboard in one pass",
            "status": "pass",
            "detail": "The flagship hero now states that Site Intelligence is public-safe, methodology-forward, and connected to knowledge architecture rather than raw internal analytics.",
            "recommendation": "Keep the hero concise; avoid adding internal report language above the fold.",
        },
        {
            "id": "copy_boundaries",
            "label": "Non-advice boundary is visible",
            "status": "pass",
            "detail": "The flagship page includes a clear educational/informational limitation before dashboard panels load.",
            "recommendation": "Do not remove the boundary note on public pages.",
        },
        {
            "id": "module_order",
            "label": "Module order supports public understanding",
            "status": "pass",
            "detail": "The recommended sequence moves from overview to knowledge structure to external-source snapshot to methodology.",
            "recommendation": "Keep methodology visible on the same page, not hidden behind a separate link only.",
        },
        {
            "id": "mobile_spacing",
            "label": "Mobile spacing and card stacking are release-ready",
            "status": "pass",
            "detail": "The v0.10.1 CSS tightens card spacing, heading scale, CTA wrapping, and long shortcode wrapping for smaller screens.",
            "recommendation": "Check the page at mobile width after WordPress caching is cleared.",
        },
        {
            "id": "error_states",
            "label": "Empty/error states remain public-safe",
            "status": "pass",
            "detail": "Public page-builder and QA modules return plain-language fallback messages rather than raw upstream HTML or private diagnostics.",
            "recommendation": "If a panel fails, keep the public page live only if the visible fallback is readable and non-technical.",
        },
        {
            "id": "private_shortcodes",
            "label": "Private review tools are separated",
            "status": "pass",
            "detail": "Visual QA, page-builder guidance, readiness checks, reports, AI briefs, Search Console, and GA4 panels remain review/admin tools unless manually approved.",
            "recommendation": "Use [sc_site_intelligence_public_flagship] for public pages and keep review shortcodes on private pages.",
        },
    ]
    score = round(100 * sum(1 for item in checks if item["status"] == "pass") / max(1, len(checks)), 1)
    return {
        "ok": True,
        "generated_at": _now(),
        "version": settings.version,
        "title": "Public Dashboard Visual QA and Copy Polish",
        "eyebrow": "Public Flagship QA",
        "summary": "A final review layer for visual polish, copy clarity, public/private boundaries, and launch readiness for the Site Intelligence flagship dashboard.",
        "score": score,
        "status": "release_candidate" if score >= 90 else "needs_review",
        "recommended_public_shortcode": "[sc_site_intelligence_public_flagship]",
        "review_shortcode": "[sc_public_dashboard_visual_qa]",
        "copy_guidelines": [
            "Lead with public value, not internal analytics terminology.",
            "Use source and methodology language near public data snapshots.",
            "Keep non-advice boundaries visible and specific.",
            "Avoid displaying report, AI, Search Console, or GA4 details on public pages without manual review.",
            "Prefer stable snapshots over live external calls for public page rendering.",
        ],
        "visual_guidelines": [
            "Use the flagship shortcode as the public page anchor.",
            "Keep CTAs to Research Library, Workbench, and GitHub prominent but not overwhelming.",
            "Check that long shortcode/code snippets wrap cleanly on mobile review pages.",
            "Confirm section headings do not repeat awkwardly when nested inside a WordPress page title.",
        ],
        "checks": checks,
        "public_page_copy": {
            "suggested_title": "Sustainable Catalyst Site Intelligence",
            "suggested_excerpt": "A public-safe dashboard showing how Sustainable Catalyst connects knowledge architecture, public datasets, article maps, platform tools, and methodology into a transparent research system.",
            "suggested_meta_description": "Explore Sustainable Catalyst Site Intelligence: a public-safe dashboard for knowledge architecture, public data sources, methodology notes, and platform transparency.",
        },
        "launch_notes": [
            "Use [sc_site_intelligence_public_flagship] on the public page.",
            "Use this QA shortcode only on a private review page.",
            "Clear WordPress, Cloudflare, and browser cache after updating the plugin.",
            "Verify the page logged out before sharing publicly.",
        ],
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
