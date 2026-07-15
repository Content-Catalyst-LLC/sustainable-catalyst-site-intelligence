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
        {"id": "platform_core", "label": "Platform Core remains optional", "status": "pass", "detail": "Public routes do not require another paid service.", "action": "Keep Platform Core disabled until sustainable persistence is available."},
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
        "release_stage": "v2.1.0_global_conditions_live_map_observatory",
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
        "subtitle": "A public geospatial, country, comparative, thematic, briefing, source, methodology, and saved-research application.",
        "summary": "Site Intelligence connects Earth observation, global country indicators, public events, dashboards, source records, methodology, saved research paths, diagnostics, and exports through one standalone public application.",
        "public_value": [
            "Provides searchable global country intelligence and a two-country comparative workspace.",
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
        "seo_title": "Site Intelligence: Earth Observation, Global Country Data, and Public Event Intelligence",
        "page_title": "Site Intelligence",
        "excerpt": "Sustainable Catalyst Site Intelligence is a public-interest observatory for Earth observation, global country indicators, natural hazards, humanitarian reporting, and source-aware research.",
        "meta_description": "Explore Earth observation, global country indicators, public events, trends, sources, and methodology through Sustainable Catalyst Site Intelligence.",
        "social_description": "A public-interest observatory for satellite imagery, country indicators, natural hazards, humanitarian reporting, and source-aware research.",
    }


def smoke_test(settings: Settings) -> Dict[str, Any]:
    endpoints = [
        {"path": "/", "scope": "public", "critical": True, "expected": "canonical version"},
        {"path": "/health", "scope": "public", "critical": True, "expected": "service health"},
        {"path": "/public/build-info", "scope": "public", "critical": True, "expected": "backend/plugin compatibility metadata"},
        {"path": "/public/launch-status", "scope": "public", "critical": True, "expected": "public beta readiness"},
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
        "release_stage": "v2.1.0_global_conditions_live_map_observatory",
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
