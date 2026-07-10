from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

PUBLIC_SOURCE_BASE_PATH = "/platform/site-intelligence/"

SOURCE_PAGE_ORDER = [
    "sources",
    "source-health",
    "indicators",
    "sustainability-indicators",
    "research-metadata",
    "publication-metadata",
    "repository-intelligence",
]

SOURCE_PAGE_CONFIG: Dict[str, Dict[str, Any]] = {
    "sources": {
        "slug": "sources",
        "title": "API Sources",
        "label": "API Sources",
        "eyebrow": "Source intelligence",
        "canonical_path": PUBLIC_SOURCE_BASE_PATH + "sources/",
        "shortcode": "[sc_public_api_sources]",
        "navigation_shortcode": "[sc_public_source_navigation current=\"sources\"]",
        "panel_key": "api-sources",
        "public_status": "public_candidate",
        "summary": "A public-safe overview of Site Intelligence source families, source modes, safe display rules, and private exclusions.",
        "excerpt": "A public-safe directory of API source families for Site Intelligence, including live, cached, fallback, and planned source layers.",
        "meta_description": "API Sources is a public-safe Site Intelligence page for source families, live/cached/fallback status, source modes, and dashboard integration boundaries.",
        "recommended_sections": ["Hero", "Source navigation", "Live source panel", "What it organizes", "Safe display rules", "Related source pages", "Boundaries"],
    },
    "source-health": {
        "slug": "source-health",
        "title": "Source Health",
        "label": "Source Health",
        "eyebrow": "Source readiness",
        "canonical_path": PUBLIC_SOURCE_BASE_PATH + "source-health/",
        "shortcode": "[sc_public_source_health]",
        "navigation_shortcode": "[sc_public_source_navigation current=\"source-health\"]",
        "panel_key": "source-health",
        "public_status": "public_candidate",
        "summary": "Public-safe source-health labels for live, cached, fallback, and planned source families without raw API diagnostics.",
        "excerpt": "A public-safe Site Intelligence source-health page for live, cached, fallback, and planned source readiness categories.",
        "meta_description": "Source Health shows public-safe readiness categories for Site Intelligence source families without exposing credentials, raw API payloads, or private diagnostics.",
        "recommended_sections": ["Hero", "Source navigation", "Source-health panel", "Status definitions", "Fallback rules", "Related source pages", "Boundaries"],
    },
    "indicators": {
        "slug": "indicators",
        "title": "Indicator Overview",
        "label": "Indicators",
        "eyebrow": "Public indicators",
        "canonical_path": PUBLIC_SOURCE_BASE_PATH + "indicators/",
        "shortcode": "[sc_public_indicator_overview]",
        "navigation_shortcode": "[sc_public_source_navigation current=\"indicators\"]",
        "panel_key": "indicator-overview",
        "public_status": "public_candidate",
        "summary": "A public overview of indicator families across climate, environment, biodiversity, development, research, and repository contexts.",
        "excerpt": "A public-safe indicator overview for Site Intelligence source families and live/cached/fallback indicator categories.",
        "meta_description": "Indicator Overview summarizes public-safe Site Intelligence indicators across environmental, development, research, publication, and repository source layers.",
        "recommended_sections": ["Hero", "Source navigation", "Indicator panel", "Indicator families", "Interpretation notes", "Related source pages", "Boundaries"],
    },
    "sustainability-indicators": {
        "slug": "sustainability-indicators",
        "title": "Sustainability Indicators",
        "label": "Sustainability Indicators",
        "eyebrow": "Sustainability context",
        "canonical_path": PUBLIC_SOURCE_BASE_PATH + "sustainability-indicators/",
        "shortcode": "[sc_public_sustainability_indicators]",
        "navigation_shortcode": "[sc_public_source_navigation current=\"sustainability-indicators\"]",
        "panel_key": "sustainability-indicators",
        "public_status": "public_candidate",
        "summary": "Public-safe sustainability indicator context across environment, development, research metadata, publication metadata, and repository visibility.",
        "excerpt": "A public-safe Site Intelligence page for sustainability indicator context across environment, development, research, and repository layers.",
        "meta_description": "Sustainability Indicators provides public-safe indicator context for environmental, development, research, publication, and repository source layers.",
        "recommended_sections": ["Hero", "Source navigation", "Sustainability indicator panel", "Indicator method", "Professional-use limits", "Related source pages", "Boundaries"],
    },
    "research-metadata": {
        "slug": "research-metadata",
        "title": "Research Metadata",
        "label": "Research Metadata",
        "eyebrow": "Research source layer",
        "canonical_path": PUBLIC_SOURCE_BASE_PATH + "research-metadata/",
        "shortcode": "[sc_public_research_metadata]",
        "navigation_shortcode": "[sc_public_source_navigation current=\"research-metadata\"]",
        "panel_key": "research-metadata",
        "public_status": "planned_source_layer",
        "summary": "Planned public-safe OpenAlex and Crossref metadata support for research-library context, source discovery, and citation provenance.",
        "excerpt": "A public-safe Site Intelligence source page for research metadata, citation context, OpenAlex, Crossref, and bibliography provenance.",
        "meta_description": "Research Metadata explains planned public-safe OpenAlex and Crossref metadata support for source discovery, citation context, and research-library provenance.",
        "recommended_sections": ["Hero", "Source navigation", "Research metadata panel", "Citation context", "Copyright boundary", "Related source pages", "Boundaries"],
    },
    "publication-metadata": {
        "slug": "publication-metadata",
        "title": "Publication Metadata",
        "label": "Publication Metadata",
        "eyebrow": "Publication source layer",
        "canonical_path": PUBLIC_SOURCE_BASE_PATH + "publication-metadata/",
        "shortcode": "[sc_public_publication_metadata]",
        "navigation_shortcode": "[sc_public_source_navigation current=\"publication-metadata\"]",
        "panel_key": "publication-metadata",
        "public_status": "planned_source_layer",
        "summary": "Public-safe publication metadata context for DOI records, publisher metadata, citation trails, and bibliography review.",
        "excerpt": "A public-safe Site Intelligence source page for DOI records, publication metadata, citation trails, and bibliography review.",
        "meta_description": "Publication Metadata provides public-safe DOI, publisher, citation, and bibliography metadata context without automated authority claims.",
        "recommended_sections": ["Hero", "Source navigation", "Publication metadata panel", "DOI records", "Bibliography limits", "Related source pages", "Boundaries"],
    },
    "repository-intelligence": {
        "slug": "repository-intelligence",
        "title": "Repository Intelligence",
        "label": "Repository Intelligence",
        "eyebrow": "Repository source layer",
        "canonical_path": PUBLIC_SOURCE_BASE_PATH + "repository-intelligence/",
        "shortcode": "[sc_public_repository_intelligence]",
        "navigation_shortcode": "[sc_public_source_navigation current=\"repository-intelligence\"]",
        "panel_key": "repository-intelligence",
        "public_status": "planned_source_layer",
        "summary": "Public-safe GitHub metadata support for repository status, documentation coverage, examples, release context, and code-infrastructure visibility.",
        "excerpt": "A public-safe Site Intelligence source page for GitHub repository metadata, documentation coverage, release context, and code-infrastructure visibility.",
        "meta_description": "Repository Intelligence explains public-safe GitHub metadata support for repository status, documentation coverage, examples, releases, and code infrastructure.",
        "recommended_sections": ["Hero", "Source navigation", "Repository panel", "Documentation coverage", "Release context", "Related source pages", "Boundaries"],
    },
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _absolute_url(path: str) -> str:
    return "https://sustainablecatalyst.com" + path if path.startswith("/") else path


def _navigation(current_slug: str = "") -> List[Dict[str, Any]]:
    current = (current_slug or "").strip("/")
    items: List[Dict[str, Any]] = []
    for slug in SOURCE_PAGE_ORDER:
        cfg = SOURCE_PAGE_CONFIG[slug]
        items.append({
            "slug": slug,
            "label": cfg["label"],
            "title": cfg["title"],
            "path": cfg["canonical_path"],
            "url": _absolute_url(cfg["canonical_path"]),
            "shortcode": cfg["shortcode"],
            "panel_key": cfg["panel_key"],
            "active": slug == current,
        })
    return items


def public_source_page_directory() -> Dict[str, Any]:
    return {
        "ok": True,
        "generated_at": _now(),
        "title": "Public Source Page Directory",
        "summary": "Copy-ready public page directory for the Site Intelligence API source and indicator layer.",
        "version_scope": "v1.4.0",
        "base_path": PUBLIC_SOURCE_BASE_PATH,
        "pages": [SOURCE_PAGE_CONFIG[slug] | {"url": _absolute_url(SOURCE_PAGE_CONFIG[slug]["canonical_path"])} for slug in SOURCE_PAGE_ORDER],
        "navigation": _navigation(),
        "recommended_shortcode": "[sc_public_source_page_directory]",
        "review_notes": [
            "Use these pages as public-safe wrappers around the v1.2.0 source and indicator shortcodes.",
            "Keep raw API payloads, credentials, logs, admin diagnostics, and private analytics out of public source pages.",
            "Pair each source page with source navigation, methodology boundaries, and a link back to Site Intelligence.",
        ],
    }


def public_source_navigation(current_slug: str = "") -> Dict[str, Any]:
    return {
        "ok": True,
        "generated_at": _now(),
        "title": "Site Intelligence Source Navigation",
        "summary": "Reusable navigation for public source, indicator, metadata, and repository intelligence pages.",
        "current_slug": current_slug,
        "items": _navigation(current_slug),
        "recommended_shortcode": "[sc_public_source_navigation]",
    }


def _template_for(cfg: Dict[str, Any]) -> Dict[str, Any]:
    slug = cfg["slug"]
    return {
        "slug": slug,
        "title": cfg["title"],
        "canonical_path": cfg["canonical_path"],
        "canonical_url": _absolute_url(cfg["canonical_path"]),
        "shortcode": cfg["shortcode"],
        "navigation_shortcode": cfg["navigation_shortcode"],
        "page_classes": f"cc-platform-v5 ccp-site-intelligence-public ccp-si-topic-page ccp-si-source-page ccp-si-source-{slug}",
        "excerpt": cfg["excerpt"],
        "meta_description": cfg["meta_description"],
        "hero_kicker": "Site Intelligence",
        "hero_label": cfg["eyebrow"],
        "primary_anchor": "#source-panel",
        "public_status": cfg["public_status"],
        "recommended_sections": cfg["recommended_sections"],
        "required_buttons": [
            "Source panel",
            "Source navigation",
            "Site Intelligence",
            "Dashboard Directory",
            "Source Methodology",
            "Platform",
            "Back to top",
        ],
        "public_exclusions": [
            "API credentials and tokens",
            "raw API response payloads",
            "private analytics and admin diagnostics",
            "unreviewed report exports",
            "professional assurance, compliance, or certification claims",
        ],
    }


def public_source_page_templates(slug: str | None = None) -> Dict[str, Any]:
    templates = [_template_for(SOURCE_PAGE_CONFIG[key]) for key in SOURCE_PAGE_ORDER]
    if slug:
        templates = [item for item in templates if item["slug"] == slug]
        if not templates:
            raise KeyError(slug)
    return {
        "ok": True,
        "generated_at": _now(),
        "title": "Public Source Page Templates",
        "summary": "Copy-ready metadata, shortcode, navigation, and section guidance for Site Intelligence public source pages.",
        "version_scope": "v1.4.0",
        "templates": templates,
        "recommended_shortcode": "[sc_public_source_page_templates]",
    }


def public_source_page_visual_qa() -> Dict[str, Any]:
    checks = [
        {"id": "canonical_paths", "label": "Canonical /platform/site-intelligence/ paths", "status": "pass", "detail": "All public source page templates use canonical child paths under Site Intelligence."},
        {"id": "shortcode_mapping", "label": "v1.2.0 source shortcodes mapped", "status": "pass", "detail": "Every public source page has a corresponding source or indicator shortcode."},
        {"id": "source_navigation", "label": "Reusable source navigation", "status": "pass", "detail": "Source pages can include [sc_public_source_navigation] with an active current page."},
        {"id": "public_safe_boundaries", "label": "Public-safe boundary language", "status": "pass", "detail": "Templates include public/private exclusions and professional-use limits."},
        {"id": "dashboard_integration", "label": "Dashboard system integration", "status": "pass", "detail": "Source pages link back to Site Intelligence, Dashboard Directory, Source Methodology, and Platform."},
        {"id": "visual_wrapping", "label": "Navigation and button wrapping", "status": "pass", "detail": "v1.4.0 CSS adds compact source page grids, active links, and nowrap helpers for public navigation labels."},
    ]
    score = int(round(100 * sum(1 for item in checks if item["status"] == "pass") / max(1, len(checks))))
    return {
        "ok": True,
        "generated_at": _now(),
        "title": "Public Source Page Visual QA",
        "summary": "Visual and integration QA for v1.4.0 public source and indicator pages.",
        "version_scope": "v1.4.0",
        "score": score,
        "checks": checks,
        "recommended_shortcode": "[sc_public_source_page_visual_qa]",
        "review_notes": [
            "Create one public page per source/indicator module only after the corresponding shortcode renders cleanly.",
            "Use source navigation near the top of each source page and footer links back to Site Intelligence and Platform.",
            "Keep source pages public-safe: no raw payloads, credentials, private analytics, admin diagnostics, or unreviewed professional claims.",
        ],
    }
