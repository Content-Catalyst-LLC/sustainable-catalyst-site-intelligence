from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .version import APP_VERSION, API_SCHEMA_VERSION, RELEASE_NAME

LAUNCH_PROFILE_SCHEMA = "sc-site-intelligence-launch/1.0"
PORTFOLIO_SCHEMA = "sc-site-intelligence-portfolio/1.0"
PUBLIC_POSITIONING = (
    "Sustainable Catalyst Site Intelligence is an auditable public observatory for satellite imagery, "
    "official economics, trade, energy, resource-security, unified country and regional dossiers, reconnectable live intelligence streams, browser-local monitoring, sustainability, global country indicators, natural hazards, humanitarian reporting, source-aware comparative research, and evidence lineage."
)

PUBLIC_WORKSPACES = [
    {"id": "observatory", "title": "Auditable Public Observatory", "route": "/app/?view=observatory", "summary": "Inspect evidence records, lineage, integrity digests, and verification limits."},
    {"id": "overview", "title": "Global Observatory", "route": "/app/?view=overview", "summary": "Map-first satellite context, public event signals, and country evidence."},
    {"id": "economics", "title": "Economics, Markets, and Sustainability Signals", "route": "/app/?view=economics", "summary": "Explore official economics, labour, trade, energy, demographic, company-filing, and sustainability records with source and timing context."},
    {"id": "law", "title": "International Law and Global Governance Observatory", "route": "/app/?view=law", "summary": "Explore official legal and governance records while preserving authority type, procedural status, citations, and source context."},
    {"id": "science", "title": "Scientific and Earth Systems Observatory", "route": "/app/?view=science", "summary": "Discover Earth systems, space observations, biodiversity, chemistry, materials, scientific assets, layers, STAC items, and time series with source and quality context."},
    {"id": "humanitarian", "title": "Humanitarian, Conflict, and Displacement Observatory", "route": "/app/?view=humanitarian", "summary": "Connect public crisis reporting, displacement evidence, civilian-protection context, humanitarian access, and hazard exposure without fabricating records."},
    {"id": "resources", "title": "Trade, Energy, and Resource Security Observatory", "route": "/app/?view=resources", "summary": "Trace official trade, energy, food, water, materials, and counterpart records without converting coverage into a proprietary risk score."},
    {"id": "dossiers", "title": "Unified Country and Regional Intelligence Dossiers", "route": "/app/?view=dossiers&country=KEN", "summary": "Combine cross-domain public evidence for a country or region without creating a composite score, ranking, or automated judgment."},
    {"id": "alerts", "title": "Alerts, Monitoring, and Live Intelligence Streams", "route": "/app/?view=alerts", "summary": "Watch reconnecting public intelligence snapshots, browser-local rules, source freshness, and deterministic digests without server-side profiling."},
    {"id": "earth", "title": "Earth Observation Studio", "route": "/app/?view=earth", "summary": "Compare satellite-derived layers across dates with source and imagery limits."},
    {"id": "events", "title": "Live Event Intelligence", "route": "/app/?view=events", "summary": "Filter public hazard and humanitarian records while retaining source identity."},
    {"id": "country", "title": "Global Country Intelligence", "route": "/app/?view=country&country=KEN", "summary": "Explore country indicators, trends, event context, and reporting-year differences."},
    {"id": "compare", "title": "Comparative Intelligence", "route": "/app/?view=compare&country=KEN&compare=GHA", "summary": "Align two-country evidence without hiding units, dates, or missing values."},
    {"id": "thematic", "title": "Thematic Intelligence Dashboards", "route": "/app/?view=thematic&dashboard=climate-environment&country=KEN", "summary": "Focused climate, development, security, and infrastructure research views."},
    {"id": "briefing", "title": "Public Briefing and Export Studio", "route": "/app/?view=briefing&briefType=country&country=KEN", "summary": "Generate deterministic source-aware briefs and portable evidence exports."},
    {"id": "sources", "title": "Source and Methodology Studio", "route": "/app/?view=sources", "summary": "Inspect source coverage, delivery state, methodology, and known limitations."},
    {"id": "saved", "title": "Saved Views and Research Paths", "route": "/app/?view=saved", "summary": "Preserve public interface state locally and exchange portable research paths."},
]

LAUNCH_CTA = {
    "primary": {"label": "Open Site Intelligence", "route": "/app/?view=overview"},
    "secondary": {"label": "Explore Earth Observation", "route": "/app/?view=earth"},
    "source": {"label": "Review Sources and Methods", "route": "/app/?view=sources"},
    "github": {"label": "View the GitHub Repository", "url": "https://github.com/Content-Catalyst-LLC/sustainable-catalyst-site-intelligence"},
}

DEPRECATED_SHORTCODES = [
    {"shortcode": "sc_public_country_intelligence", "replacement": "sc_global_country_intelligence", "removal_target": "2.0.0"},
    {"shortcode": "sc_public_cross_domain_comparison", "replacement": "sc_comparative_intelligence", "removal_target": "2.0.0"},
    {"shortcode": "sc_geospatial_intelligence_map", "replacement": "sc_site_intelligence_app", "removal_target": "2.0.0"},
]


def launch_profile() -> dict[str, Any]:
    return {
        "ok": True,
        "schema": LAUNCH_PROFILE_SCHEMA,
        "application_version": APP_VERSION,
        "api_schema_version": API_SCHEMA_VERSION,
        "release": RELEASE_NAME,
        "release_status": "auditable-public-observatory",
        "positioning": PUBLIC_POSITIONING,
        "principles": [
            "Public evidence is separated from interpretation and automated judgment.",
            "Source identity, reporting date, units, data state, and limitations remain visible.",
            "Missing data is explicit and optional-source failures remain local.",
            "Shareable views and exports preserve public research context.",
            "Platform Core remains optional for public reading and deployment.",
        ],
        "workspaces": PUBLIC_WORKSPACES,
        "calls_to_action": LAUNCH_CTA,
        "portfolio": {
            "organization": "Content Catalyst LLC",
            "project": "Sustainable Catalyst Site Intelligence",
            "category": "Open-source public-interest intelligence platform",
            "architecture": ["WordPress", "Python", "FastAPI", "public APIs", "browser-local saved views"],
            "license": "MIT",
            "repository": LAUNCH_CTA["github"]["url"],
            "primary_embed": '[sc_site_intelligence_app height="1000"]',
            "launch_embed": '[sc_site_intelligence_launch height="1200"]',
        },
        "responsible_use": {
            "appropriate_for": ["public research", "source discovery", "comparative orientation", "evidence brief preparation"],
            "not_for": ["emergency response", "legal advice", "financial advice", "medical advice", "automated eligibility or risk decisions"],
        },
        "deprecated_shortcodes": DEPRECATED_SHORTCODES,
    }


def launch_checklist() -> dict[str, Any]:
    groups = [
        {"id": "product", "title": "Public product", "status": "implemented", "items": ["single primary application embed", "seventeen public research workspaces", "public launch route", "responsible-use boundary"]},
        {"id": "evidence", "title": "Evidence and provenance", "status": "implemented", "items": ["source registry", "methodology registry", "visible data states", "source-aware exports"]},
        {"id": "delivery", "title": "Delivery quality", "status": "implemented", "items": ["mobile navigation", "keyboard behavior", "reduced motion", "performance budgets", "responsive WordPress embed"]},
        {"id": "portfolio", "title": "Portfolio materials", "status": "implemented", "items": ["project description", "launch post", "homepage feature copy", "Platform page copy", "demo shot list"]},
        {"id": "manual-launch", "title": "Manual launch actions", "status": "review-required", "items": ["production deployment verification", "WordPress page update", "representative screenshots", "social preview artwork", "short demo recording"]},
    ]
    return {
        "ok": True,
        "schema": LAUNCH_PROFILE_SCHEMA,
        "application_version": APP_VERSION,
        "groups": groups,
        "automated_ready": all(group["status"] == "implemented" for group in groups if group["id"] != "manual-launch"),
        "manual_review_required": True,
    }


def launch_materials() -> dict[str, Any]:
    return {
        "ok": True,
        "schema": "sc-site-intelligence-launch-materials/1.0",
        "application_version": APP_VERSION,
        "homepage_feature": {
            "eyebrow": "PUBLIC-INTEREST OBSERVATORY",
            "title": "Site Intelligence",
            "body": PUBLIC_POSITIONING,
            "primary_cta": "Open Site Intelligence",
            "secondary_cta": "Explore Earth Observation",
        },
        "platform_feature": {
            "title": "Source-aware public intelligence",
            "body": "Site Intelligence connects live intelligence streams, browser-local monitoring, Earth observation, public events, official economics, trade, energy, resource-security records, international law and governance records, country indicators, thematic dashboards, comparative research, briefing exports, and transparent methodology in one auditable workflow.",
        },
        "linkedin_project_description": "An open-source public-interest observatory that connects official economics, international law, satellite imagery, country indicators, natural hazards, humanitarian reporting, comparative intelligence, transparent methods, and source-aware briefing exports.",
        "linkedin_launch_post": "I launched Sustainable Catalyst Site Intelligence, an open-source public-interest observatory for official economics, international law, Earth observation, global country indicators, natural hazards, humanitarian reporting, and source-aware comparative research. The platform keeps source identity, reporting dates, missing data, and methodological limits visible while supporting shareable research paths and reproducible exports.",
        "github_about": "Public-interest observatory for Earth observation, economics, international law, country indicators, live events, thematic dashboards, comparative research, and source-aware briefs.",
        "social_preview": {
            "title": "Sustainable Catalyst Site Intelligence",
            "description": "Public evidence, Economics, sustainability, Earth observation, country intelligence, live events, and source-aware research paths.",
            "recommended_size": "1200x630",
            "alt_text": "A global public-intelligence interface showing Earth observation, event signals, country evidence, and source-aware research tools.",
        },
        "demo_shot_list": [
            "Open the Global Observatory and change satellite layers.",
            "Compare two Earth-observation dates with the swipe control.",
            "Open a country profile and inspect an indicator source.",
            "Filter live event records and open a source-linked event detail.",
            "Compare Kenya and Ghana while preserving dates and missing values.",
            "Open the International Law workspace and compare authority categories for a country profile.",
            "Generate a source-aware public brief and export its manifest.",
            "Open Sources and Methods, then save and share the research path.",
        ],
    }


def portfolio_manifest() -> dict[str, Any]:
    profile = launch_profile()
    return {
        "ok": True,
        "schema": PORTFOLIO_SCHEMA,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "application_version": APP_VERSION,
        "project": profile["portfolio"],
        "positioning": profile["positioning"],
        "workspaces": profile["workspaces"],
        "principles": profile["principles"],
        "responsible_use": profile["responsible_use"],
        "calls_to_action": profile["calls_to_action"],
    }


def portfolio_markdown() -> str:
    manifest = portfolio_manifest()
    lines = [
        "# Sustainable Catalyst Site Intelligence",
        "",
        f"**Release:** v{APP_VERSION} — {RELEASE_NAME}",
        "",
        manifest["positioning"],
        "",
        "## Public workspaces",
        "",
    ]
    for workspace in manifest["workspaces"]:
        lines.append(f"- **{workspace['title']}** — {workspace['summary']} (`{workspace['route']}`)")
    lines.extend([
        "",
        "## Architecture",
        "",
        ", ".join(manifest["project"]["architecture"]),
        "",
        "## Responsible use",
        "",
        "Site Intelligence supports public research and evidence orientation. It is not an emergency-response system or a substitute for legal, financial, medical, or other professional advice.",
        "",
        f"Repository: {manifest['project']['repository']}",
    ])
    return "\n".join(lines) + "\n"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def launch_diagnostics() -> dict[str, Any]:
    root = _repo_root()
    html = (root / "backend/public_app/index.html").read_text(encoding="utf-8")
    js = (root / "backend/public_app/assets/app.js").read_text(encoding="utf-8")
    css = (root / "backend/public_app/assets/app.css").read_text(encoding="utf-8")
    php = (root / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text(encoding="utf-8")
    readme = (root / "README.md").read_text(encoding="utf-8")
    checks = {
        "launch_route_navigation": 'data-route="launch"' in html,
        "launch_portfolio_section": 'id="publicLaunchPortfolio"' in html,
        "launch_profile_fetch": "/public/launch-profile" in js,
        "launch_route_handler": 'route==="launch"' in js,
        "launch_mobile_css": "public-launch-portfolio" in css and "launch-feature-grid" in css,
        "wordpress_version": f"Version: {APP_VERSION}" in php and f"const VERSION = '{APP_VERSION}';" in php,
        "wordpress_launch_shortcode": "sc_site_intelligence_launch" in php and "site_intelligence_launch_shortcode" in php,
        "primary_embed_retained": "sc_site_intelligence_app" in php,
        "deprecated_shortcode_schedule": "LEGACY_SHORTCODE_REMOVAL_TARGET" in php,
        "readme_launch_route": "/app/?view=launch" in readme,
        "portfolio_documentation": (root / "docs/PUBLIC_LAUNCH_PORTFOLIO_V1250.md").exists(),
        "launch_materials_documentation": (root / "docs/LAUNCH_MATERIALS_V1250.md").exists(),
    }
    return {
        "ok": all(checks.values()),
        "schema": LAUNCH_PROFILE_SCHEMA,
        "application_version": APP_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
        "workspace_count": len(PUBLIC_WORKSPACES),
        "manual_launch_actions_remaining": launch_checklist()["groups"][-1]["items"],
        "secrets_exposed": False,
    }
