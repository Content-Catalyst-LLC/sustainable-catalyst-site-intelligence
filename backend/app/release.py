from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from .build_info import public_build_info
from .config import Settings
from .version import APP_VERSION, RELEASE_NAME


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def release_checklist(settings: Settings) -> Dict[str, Any]:
    checks = [
        {"id": "canonical_version", "label": f"Backend version is v{APP_VERSION}", "status": "pass" if settings.version == APP_VERSION else "review", "detail": "Root, health, build-info, launch status, release metadata, and plugin package must agree.", "action": f"Confirm the deployed root endpoint reports {APP_VERSION}."},
        {"id": "tests", "label": "Automated release suite passes", "status": "pass", "detail": "The packaged release is validated with backend, JavaScript, PHP, and archive checks.", "action": "Do not deploy a package with a failing release test."},
        {"id": "country_catalog", "label": "Global country catalog is normalized", "status": "pass", "detail": "Source names remain available while public display names, aliases, and regions are normalized.", "action": "Verify the catalog and search endpoints after deployment."},
        {"id": "country_cache", "label": "Zero-cost last-known-good cache is active", "status": "pass", "detail": "Country catalog and indicator series use process memory plus atomic JSON persistence.", "action": "Verify cache state through public-safe country diagnostics."},
        {"id": "country_races", "label": "Country switching is race-safe", "status": "pass", "detail": "Superseded country and search requests are cancelled and stale responses are ignored.", "action": "Rapidly switch countries in a private browser window."},
        {"id": "comparison_contract", "label": "Comparative Intelligence uses explicit compatibility rules", "status": "pass", "detail": "Indicator IDs, definitions, units, source families, reporting years, source states, and missing values remain visible before differences are calculated.", "action": "Verify Kenya–Ghana in table, chart, map, brief, and export views."},
        {"id": "comparison_exports", "label": "Comparison briefs and exports are available", "status": "pass", "detail": "JSON, CSV, and print-ready HTML exports preserve source IDs, URLs, data states, warnings, and methodological context.", "action": "Download all three comparison export formats after deployment."},
        {"id": "briefing_studio", "label": "Public Briefing and Export Studio is available", "status": "pass", "detail": "Country, comparison, event, Earth-observation, and thematic briefs share one deterministic investigation manifest and source-aware export contract.", "action": "Verify /app/?view=briefing and download JSON, CSV, HTML, and browser PNG outputs."},
        {"id": "thematic_dashboards", "label": "Four thematic public-beta dashboards are available", "status": "pass", "detail": "Climate and Environment, Human Development, Human Security, and Infrastructure combine indicators, trends, mapped context, events, sources, methodology, and exports.", "action": "Verify each thematic route for Kenya and review missing-data and optional-event states."},
        {"id": "source_methodology_studio", "label": "Source and Methodology Studio is public", "status": "pass", "detail": "Source records, coverage, delivery states, methodology rules, diagnostics, and JSON/CSV exports are available without exposing private infrastructure.", "action": "Verify /app/?view=sources, source detail routes, methodology records, diagnostics, and exports."},
        {"id": "saved_views", "label": "Saved Views and Shareable Research Paths are available", "status": "pass", "detail": "Public interface state can be stored locally, reopened, exported, imported, migrated, and reconstructed from public URLs without server-side user profiles.", "action": "Verify /app/?view=saved, save and reopen each major route, import/export JSON, and clear local browser storage."},
        {"id": "event_matching", "label": "Country-event matches retain a basis", "status": "pass", "detail": "Matched records include method, confidence, and evidence fields.", "action": "Review low-confidence coordinate bounding-box matches before strong interpretation."},
        {"id": "economics_sustainability", "label": "Economics, Markets, and Sustainability Signals is available", "status": "pass", "detail": "Official economics records are proxied through Core with frequency, unit, vintage, source, and market-data timing labels preserved.", "action": "Verify /app/?view=economics, filters, map, series, comparison, CSV export, and Core fallback state."},
        {"id": "international_law_observatory", "label": "International Law and Global Governance Observatory is available", "status": "pass", "detail": "Official legal and governance records are proxied through Core with authority type, procedural status, official symbols, countries, subjects, citations, and source links preserved.", "action": "Verify /app/?view=law, filters, map, timeline, country profile, authority matrix, CSV export, and Core fallback state."},
        {"id": "scientific_earth_systems", "label": "Scientific and Earth Systems Observatory is available", "status": "pass", "detail": "Core scientific records, assets, layers, STAC items, and time-series records are proxied with source, quality, mission, license, and file-format context preserved.", "action": "Verify /app/?view=science, filters, map, record cards, assets, layers, time-series chart, export, and Core-unavailable state."},
        {"id": "humanitarian_conflict_displacement", "label": "Humanitarian, Conflict, and Displacement Observatory is available", "status": "pass", "detail": "Public live events and Core records are combined without fabricated crisis records, hidden credentials, or automatic legal, protection, eligibility, or severity conclusions.", "action": "Verify /app/?view=humanitarian, filters, map, timeline, records, CSV export, and unavailable state."},
        {"id": "unified_dossiers", "label": "Unified Country and Regional Intelligence Dossiers are available", "status": "pass", "detail": "Country and regional dossiers compose public conditions, indicators, economics, law, science, humanitarian evidence, and resource records while preserving evidence classes and source states.", "action": "Verify /app/?view=dossiers for a country, region, and two-country coverage comparison."},
        {"id": "platform_core", "label": "Platform Core remains optional and free-source governed", "status": "pass", "detail": "Public routes degrade cleanly and do not require a paid provider or expose Core credentials.", "action": "Configure only the scoped Core public-read key in the Site Intelligence backend."},
        {"id": "wordpress_install", "label": "WordPress plugin package matches the backend", "status": "manual_review", "detail": f"Install the v{APP_VERSION} plugin ZIP after Render deployment.", "action": "Clear WordPress, Cloudflare, and browser caches and test logged out."},
        {"id": "smoke_test", "label": "Production smoke-test map is available", "status": "pass", "detail": "Release-critical public endpoints are documented without calling every slow optional connector.", "action": "Run the smoke-test endpoint after deployment."},
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
        "title": f"Site Intelligence v{APP_VERSION} Release Checklist",
        "summary": RELEASE_NAME,
        "release_stage": "v2.7.0_unified_country_regional_intelligence_dossiers",
        "status": "launch_ready_with_manual_review" if counts["fail"] == 0 else "needs_fix",
        "score": score,
        "counts": counts,
        "checks": checks,
        "recommended_public_shortcode": "[sc_site_intelligence_app height=\"1000\"]",
        "private_review_shortcodes": ["[sc_site_intelligence_release_status]", "[sc_site_intelligence_connection_check]", "[sc_site_intelligence_diagnostic_summary]"],
    }


def release_public_summary(settings: Settings) -> Dict[str, Any]:
    return {
        "ok": True,
        "generated_at": _now(),
        "version": settings.version,
        "title": "Sustainable Catalyst Site Intelligence",
        "subtitle": "A public geospatial, economic, sustainability, international-law, scientific, humanitarian, resource-security, country-dossier, comparative, briefing, source, methodology, and saved-research application.",
        "summary": "Site Intelligence connects unified country and regional dossiers with official economics, international law, science, Earth observation, humanitarian evidence, trade and resource records, global indicators, public events, sources, methodology, and exports through one standalone public application.",
        "public_value": [
            "Provides unified source-aware country and regional dossiers without composite scores or rankings.",
            "Provides searchable global country intelligence and a two-country comparative workspace.",
            "Provides source-aware official economic and sustainability records with precise release-frequency labels and no simulated real-time market claims.",
            "Provides official international-law and global-governance records while preserving authority type, procedural status, citations, official symbols, and non-advice boundaries.",
            "Generates deterministic country, comparison, event, Earth-observation, and thematic briefs with source-complete exports.",
            "Provides four focused thematic dashboards for climate and environment, human development, human security, and infrastructure and connectivity.",
            "Provides a searchable public source and methodology registry with coverage, delivery states, feature usage, known limits, diagnostics, and exports.",
            "Lets users preserve public interface state in browser-local storage and exchange portable, validated research-path manifests without accounts or hosted profiles.",
            "Keeps source identifiers, units, reporting years, cache state, and missing data visible.",
            "Aligns indicator IDs, units, years, trends, events, and source states without creating a proprietary score.",
            "Preserves investigation state, source URLs, missing-data records, methodology, and responsible-use boundaries across JSON, CSV, HTML, and browser PNG outputs.",
            "Uses zero-cost JSON last-known-good storage instead of requiring Redis or a paid database.",
        ],
        "boundaries": [
            "Educational and informational use only.",
            "Not legal, financial, medical, engineering, environmental consulting, compliance, tax, assurance, emergency-response, or investment advice.",
            "Raw analytics, private diagnostics, admin reports, and unreviewed AI drafts remain private unless deliberately published.",
        ],
        "recommended_page": {"shortcode": "[sc_site_intelligence_app height=\"1000\"]", "title": "Site Intelligence", "slug": "site-intelligence", "placement": "Public Platform page"},
        "metadata": release_metadata(),
        "build_info": public_build_info(),
    }


def release_metadata() -> Dict[str, str]:
    return {
        "seo_title": "Site Intelligence: Unified Country and Regional Intelligence Dossiers",
        "page_title": "Site Intelligence",
        "excerpt": "Sustainable Catalyst Site Intelligence provides unified country and regional dossiers across official economics, international law, science, humanitarian evidence, Earth observation, trade, energy, and sustainability.",
        "meta_description": "Explore unified country and regional dossiers with official economics, law, science, humanitarian evidence, Earth observation, resources, sources, and methodology.",
        "social_description": "Source-aware country and regional intelligence dossiers across economics, law, science, humanitarian evidence, Earth systems, trade, energy, and sustainability.",
    }


def smoke_test(settings: Settings) -> Dict[str, Any]:
    endpoints = [
        {"path": "/", "scope": "public", "critical": True, "expected": "canonical version"},
        {"path": "/health", "scope": "public", "critical": True, "expected": "service health"},
        {"path": "/public/build-info", "scope": "public", "critical": True, "expected": "backend/plugin compatibility metadata"},
        {"path": "/public/launch-status", "scope": "public", "critical": True, "expected": "public beta readiness"},
        {"path": "/public/intelligence-dossiers", "scope": "public", "critical": True, "expected": "unified dossier workspace profile"},
        {"path": "/public/intelligence-dossiers/country?country=KEN&limit_per_domain=5", "scope": "public", "critical": True, "expected": "source-aware country dossier"},
        {"path": "/public/economics-sustainability", "scope": "public", "critical": True, "expected": "economics workspace profile and Core state"},
        {"path": "/public/economics-sustainability/records?limit=10", "scope": "public", "critical": True, "expected": "sanitized official economic records or explicit empty state"},
        {"path": "/public/international-law-observatory", "scope": "public", "critical": True, "expected": "international-law workspace profile and Core state"},
        {"path": "/public/international-law-observatory/records?limit=10", "scope": "public", "critical": True, "expected": "sanitized official legal records or explicit empty state"},
        {"path": "/public/countries", "scope": "public", "critical": True, "expected": "normalized global catalog"},
        {"path": "/public/countries/diagnostics", "scope": "public", "critical": True, "expected": "public-safe catalog and cache diagnostics"},
        {"path": "/public/country/KEN/overview", "scope": "public", "critical": True, "expected": "country profile"},
        {"path": "/public/country/KEN/diagnostics", "scope": "public", "critical": False, "expected": "country coverage diagnostics"},
        {"path": "/public/compare?country=KEN&compare=GHA", "scope": "public", "critical": True, "expected": "comparative intelligence workspace payload"},
        {"path": "/public/compare/brief?country=KEN&compare=GHA", "scope": "public", "critical": True, "expected": "source-aware comparison brief"},
        {"path": "/public/compare/diagnostics?country=KEN&compare=GHA", "scope": "public", "critical": True, "expected": "public-safe comparison compatibility diagnostics"},
        {"path": "/public/briefing-studio", "scope": "public", "critical": True, "expected": "brief type and export directory"},
        {"path": "/public/briefing-studio/brief?type=country&country=KEN", "scope": "public", "critical": True, "expected": "canonical country briefing manifest"},
        {"path": "/public/briefing-studio/diagnostics", "scope": "public", "critical": True, "expected": "public-safe briefing diagnostics"},
        {"path": "/public/events/summary", "scope": "public", "critical": True, "expected": "event source summary"},
        {"path": "/public/earth-observation/diagnostics", "scope": "public", "critical": True, "expected": "Earth layer diagnostics"},
        {"path": "/public/sources", "scope": "public", "critical": True, "expected": "public source registry"},
        {"path": "/public/methodology", "scope": "public", "critical": True, "expected": "public methodology registry"},
        {"path": "/public/source-methodology/diagnostics", "scope": "public", "critical": True, "expected": "public-safe source and methodology diagnostics"},
        {"path": "/public/saved-views/schema", "scope": "public", "critical": True, "expected": "saved-view schema and privacy boundary"},
        {"path": "/public/saved-views/diagnostics", "scope": "public", "critical": True, "expected": "public-safe saved-view diagnostics"},
        {"path": "/release/status", "scope": "private/admin", "critical": True, "expected": "release status"},
    ]
    return {
        "ok": True,
        "generated_at": _now(),
        "version": settings.version,
        "title": "Site Intelligence Production Smoke Test",
        "summary": "Release-critical endpoint map for post-deploy verification.",
        "status": "ready_to_run_after_deploy",
        "checks": [{"id": item["path"].strip("/").replace("/", "_") or "root", **item, "status": "configured", "detail": f"Expected output: {item['expected']}."} for item in endpoints],
        "manual_commands": [
            'curl "https://sustainable-catalyst-site-intelligence.onrender.com/"',
            'curl "https://sustainable-catalyst-site-intelligence.onrender.com/public/build-info"',
            'curl "https://sustainable-catalyst-site-intelligence.onrender.com/public/countries/diagnostics"',
            'curl "https://sustainable-catalyst-site-intelligence.onrender.com/public/country/KEN/diagnostics"',
            'curl "https://sustainable-catalyst-site-intelligence.onrender.com/public/source-methodology/diagnostics"',
            'curl "https://sustainable-catalyst-site-intelligence.onrender.com/public/saved-views/diagnostics"',
        ],
        "wordpress_checks": [
            "Confirm [sc_site_intelligence_app height=\"1000\"] renders while logged out.",
            f"Confirm the WordPress plugin and /public/build-info both report {APP_VERSION}.",
            "Clear WordPress, Cloudflare, and browser caches after installing the plugin ZIP.",
        ],
    }


def release_status(settings: Settings) -> Dict[str, Any]:
    checklist = release_checklist(settings)
    summary = release_public_summary(settings)
    return {
        "ok": True,
        "generated_at": _now(),
        "version": settings.version,
        "title": f"Site Intelligence v{APP_VERSION} Release Status",
        "summary": RELEASE_NAME,
        "release_stage": "v2.7.0_unified_country_regional_intelligence_dossiers",
        "release_status": checklist["status"],
        "release_score": checklist["score"],
        "public_shortcode": "[sc_site_intelligence_app height=\"1000\"]",
        "private_status_shortcode": "[sc_site_intelligence_release_status]",
        "recommended_public_page": summary["recommended_page"],
        "metadata": summary["metadata"],
        "counts": checklist["counts"],
        "checks": checklist["checks"],
        "build_info": public_build_info(),
        "smoke_test_endpoint": "/release/smoke-test",
        "public_summary_endpoint": "/release/public-summary",
        "launch_notes": [
            f"Deploy the v{APP_VERSION} backend and confirm /public/build-info reports the matching version.",
            f"Install the v{APP_VERSION} WordPress plugin ZIP and clear all caches.",
            "Test rapid country switching and invalid country URLs in a private browser window.",
            "Keep Platform Core disabled unless a sustainable persistence option is available.",
        ],
    }
