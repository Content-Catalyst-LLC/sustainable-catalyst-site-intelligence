from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

PUBLIC_SOURCE_STATUS = {
    "live": "Live source is available or can be enabled when credentials/configuration are present.",
    "cached": "Public display can use cached or stale-safe summaries when upstream sources are slow.",
    "fallback": "Stable public fallback is available so the dashboard does not expose errors or raw payloads.",
    "planned": "Source family is documented for public methodology and future integration.",
}

SOURCE_FAMILIES: List[Dict[str, Any]] = [
    {
        "slug": "climate-energy",
        "label": "Climate + Energy",
        "status": "cached",
        "source_mode": "live_cached_fallback",
        "source_examples": ["NASA POWER", "NASA GIBS", "Climate TRACE", "NOAA/NWS", "EIA"],
        "public_use": "Climate, energy, emissions, Earth observation, and weather-context dashboards.",
        "safe_display": "Source-labeled indicators, cached summaries, fallback notes, and methodology boundaries.",
        "private_exclusions": ["API keys", "raw payloads", "force-refresh diagnostics", "unreviewed emissions claims"],
    },
    {
        "slug": "environmental-monitoring",
        "label": "Environmental Monitoring",
        "status": "cached",
        "source_mode": "live_cached_fallback",
        "source_examples": ["EPA AQS", "USGS", "NOAA/NWS", "NASA GIBS"],
        "public_use": "Air, land, water, observation status, monitoring context, and QA/QC notes.",
        "safe_display": "Monitoring summaries with availability, coverage, units, and source-limit language.",
        "private_exclusions": ["credentials", "raw station payloads", "unreviewed compliance determinations"],
    },
    {
        "slug": "biodiversity-land-use",
        "label": "Biodiversity + Land Use",
        "status": "cached",
        "source_mode": "source_context",
        "source_examples": ["GBIF", "USGS", "NASA GIBS"],
        "public_use": "Species occurrence context, land-cover signals, habitat framing, and sampling-bias notes.",
        "safe_display": "Ecological context with explicit caveats about observation density and completeness.",
        "private_exclusions": ["raw occurrence dumps", "professional ecological certification", "site-specific determinations"],
    },
    {
        "slug": "development-indicators",
        "label": "Development Indicators",
        "status": "planned",
        "source_mode": "curated_public_context",
        "source_examples": ["World Bank", "OECD", "UN SDG data"],
        "public_use": "Public context for development, institutions, economy, sustainability, and governance dashboards.",
        "safe_display": "Curated indicator groups, source labels, update notes, and public interpretation boundaries.",
        "private_exclusions": ["country rankings presented as judgments", "policy prescriptions", "unreviewed causal claims"],
    },
    {
        "slug": "research-metadata",
        "label": "Research Metadata",
        "status": "planned",
        "source_mode": "curated_public_context",
        "source_examples": ["OpenAlex", "Crossref"],
        "public_use": "Research-source context, publication metadata, citation trails, and bibliography support.",
        "safe_display": "Metadata summaries, source links, bibliographic context, and review notes.",
        "private_exclusions": ["copyrighted full-text ingestion", "unreviewed authority scoring", "private reading notes"],
    },
    {
        "slug": "repository-intelligence",
        "label": "Repository Intelligence",
        "status": "planned",
        "source_mode": "curated_public_context",
        "source_examples": ["GitHub repositories", "release metadata", "documentation coverage"],
        "public_use": "Repository status, documentation coverage, releases, tests, examples, and public code-health context.",
        "safe_display": "Public repository summaries without tokens, secrets, private issues, or unpublished planning notes.",
        "private_exclusions": ["tokens", "private issues", "local environment details", "secret-scan contents"],
    },
]

DEVELOPMENT_INDICATOR_GROUPS: List[Dict[str, Any]] = [
    {
        "group": "Development and capacity",
        "sources": ["World Bank", "UN SDG data"],
        "indicator_examples": ["population context", "income and development bands", "education and health context", "SDG-aligned public indicators"],
        "dashboard_use": "Adds regional and institutional context for sustainability, infrastructure, governance, and development pages.",
        "status": "planned",
    },
    {
        "group": "Economy and institutions",
        "sources": ["World Bank", "OECD"],
        "indicator_examples": ["macroeconomic context", "public governance indicators", "innovation and labor context", "sectoral structure"],
        "dashboard_use": "Supports public background panels for economic systems, governance, and decision-analysis content.",
        "status": "planned",
    },
    {
        "group": "Sustainability context",
        "sources": ["UN SDG data", "World Bank", "OECD"],
        "indicator_examples": ["energy access", "emissions context", "water and sanitation", "resilience and infrastructure indicators"],
        "dashboard_use": "Connects environmental dashboards to human development and public-interest outcomes.",
        "status": "planned",
    },
]

RESEARCH_METADATA_GROUPS: List[Dict[str, Any]] = [
    {
        "group": "Research graph context",
        "sources": ["OpenAlex"],
        "metadata_examples": ["works", "authors", "institutions", "concepts", "open access status"],
        "dashboard_use": "Supports research-library context, source discovery, and article-map bibliography review.",
        "status": "planned",
    },
    {
        "group": "Publication metadata",
        "sources": ["Crossref"],
        "metadata_examples": ["DOI records", "publication dates", "publisher metadata", "reference metadata"],
        "dashboard_use": "Helps public pages explain citations, publication provenance, and source metadata boundaries.",
        "status": "planned",
    },
]

REPOSITORY_GROUPS: List[Dict[str, Any]] = [
    {
        "group": "Sustainable Catalyst repositories",
        "sources": ["GitHub"],
        "metadata_examples": ["repository list", "README presence", "release tags", "license status", "documentation folders"],
        "dashboard_use": "Shows public code infrastructure without exposing credentials or private development notes.",
        "status": "planned",
    },
    {
        "group": "Module readiness",
        "sources": ["GitHub", "internal registry"],
        "metadata_examples": ["tests", "docs", "examples", "schemas", "plugin assets"],
        "dashboard_use": "Supports public methodology and project maturity context for platform modules.",
        "status": "planned",
    },
]

SUSTAINABILITY_INDICATORS: List[Dict[str, str]] = [
    {"label": "Climate and energy", "source_family": "NASA / NOAA / EIA / Climate TRACE", "status": "cached", "public_note": "Use as source-labeled environmental context, not risk certification."},
    {"label": "Air, land, and water", "source_family": "EPA / USGS / NOAA / NASA", "status": "cached", "public_note": "Use with QA/QC and coverage caveats."},
    {"label": "Biodiversity and land use", "source_family": "GBIF / USGS / NASA", "status": "cached", "public_note": "Use with sampling-bias and completeness caveats."},
    {"label": "Development indicators", "source_family": "World Bank / OECD / UN SDG", "status": "planned", "public_note": "Use as public development context after source and indicator review."},
    {"label": "Research and publication metadata", "source_family": "OpenAlex / Crossref", "status": "planned", "public_note": "Use as bibliographic context, not authority automation."},
    {"label": "Repository health", "source_family": "GitHub", "status": "planned", "public_note": "Use as public project-infrastructure context without exposing secrets."},
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _counts() -> Dict[str, int]:
    counts: Dict[str, int] = {"live": 0, "cached": 0, "fallback": 0, "planned": 0}
    for item in SOURCE_FAMILIES:
        status = item.get("status", "planned")
        counts[status] = counts.get(status, 0) + 1
    return counts


def public_sources() -> Dict[str, Any]:
    return {
        "ok": True,
        "generated_at": _now(),
        "title": "Public API Source Expansion",
        "summary": "Public-safe source families for Site Intelligence API connectors, metadata layers, repository intelligence, and live/cached/fallback indicator summaries.",
        "version_scope": "v1.5.0",
        "public_status": "public_candidate",
        "source_families": SOURCE_FAMILIES,
        "status_definitions": PUBLIC_SOURCE_STATUS,
        "recommended_shortcode": "[sc_public_api_sources]",
        "review_notes": [
            "Treat all public indicators as source context, not professional advice or live operational truth.",
            "Use live sources only when public display is stable, labeled, and fallback-safe.",
            "Never expose API keys, credentials, raw payloads, backend logs, private analytics, or unpublished review notes.",
        ],
    }


def public_source_health() -> Dict[str, Any]:
    counts = _counts()
    total = sum(counts.values())
    score = int(round(((counts.get("live", 0) + counts.get("cached", 0)) / max(total, 1)) * 100))
    return {
        "ok": True,
        "generated_at": _now(),
        "title": "Public Source Health",
        "summary": "Public-safe status summary for Site Intelligence source families. This shows source readiness categories without exposing raw API diagnostics.",
        "public_status": "public_candidate",
        "score": score,
        "counts": counts,
        "source_families": SOURCE_FAMILIES,
        "status_definitions": PUBLIC_SOURCE_STATUS,
        "recommended_shortcode": "[sc_public_source_health]",
        "hidden": [
            "API credentials and keys",
            "raw upstream response payloads",
            "force-refresh logs",
            "private admin diagnostics",
            "unreleased report exports",
        ],
    }


def public_development_indicators() -> Dict[str, Any]:
    return {
        "ok": True,
        "generated_at": _now(),
        "title": "Development Indicator Layer",
        "summary": "Planned public-safe indicator groups for World Bank, OECD, and UN/SDG context inside Site Intelligence dashboards.",
        "public_status": "planned_source_layer",
        "source_mode": "curated_public_context",
        "indicator_groups": DEVELOPMENT_INDICATOR_GROUPS,
        "recommended_shortcode": "[sc_public_development_indicators]",
        "methodology": [
            "Use indicators for context rather than country scoring or policy prescriptions.",
            "Show source name, update status, geographic scope, and interpretation limits.",
            "Keep raw API diagnostics and unreviewed transformations out of public pages.",
        ],
    }


def public_research_metadata() -> Dict[str, Any]:
    return {
        "ok": True,
        "generated_at": _now(),
        "title": "Research Metadata Layer",
        "summary": "Planned public-safe OpenAlex and Crossref metadata support for research-library context, source discovery, and citation provenance.",
        "public_status": "planned_source_layer",
        "source_mode": "metadata_context",
        "metadata_groups": RESEARCH_METADATA_GROUPS,
        "recommended_shortcode": "[sc_public_research_metadata]",
        "methodology": [
            "Use metadata for bibliographic context, not automated authority claims.",
            "Do not ingest or redistribute copyrighted full text through this public layer.",
            "Separate public citation context from private research notes and draft bibliographies.",
        ],
    }


def public_publication_metadata() -> Dict[str, Any]:
    return {
        "ok": True,
        "generated_at": _now(),
        "title": "Publication Metadata Layer",
        "summary": "Public-safe publication metadata context for DOI records, publisher metadata, citation trails, and bibliography review.",
        "public_status": "planned_source_layer",
        "source_mode": "metadata_context",
        "metadata_groups": [group for group in RESEARCH_METADATA_GROUPS if "Crossref" in group.get("sources", [])],
        "recommended_shortcode": "[sc_public_publication_metadata]",
        "methodology": [
            "Use publication metadata to support citations and provenance notes.",
            "Do not treat DOI metadata as a claim that an article has been fully reviewed.",
            "Keep full-text use and copyright boundaries explicit.",
        ],
    }


def public_repository_intelligence() -> Dict[str, Any]:
    return {
        "ok": True,
        "generated_at": _now(),
        "title": "Repository Intelligence Layer",
        "summary": "Planned public-safe GitHub metadata support for repository status, documentation coverage, examples, release context, and code-infrastructure visibility.",
        "public_status": "planned_source_layer",
        "source_mode": "public_repository_metadata",
        "repository_groups": REPOSITORY_GROUPS,
        "recommended_shortcode": "[sc_public_repository_intelligence]",
        "methodology": [
            "Show public repository context without exposing secrets, tokens, local paths, or private issues.",
            "Use repository metadata for project transparency, not security certification.",
            "Pair repository panels with documentation and license notes where possible.",
        ],
    }


def public_indicator_overview() -> Dict[str, Any]:
    return {
        "ok": True,
        "generated_at": _now(),
        "title": "Public Indicator Overview",
        "summary": "Live/cached/fallback indicator overview for the Site Intelligence public source layer.",
        "public_status": "public_candidate",
        "indicators": SUSTAINABILITY_INDICATORS,
        "counts": _counts(),
        "recommended_shortcode": "[sc_public_indicator_overview]",
        "review_notes": [
            "Use status labels so visitors can distinguish live, cached, fallback, and planned sources.",
            "Pair indicator panels with source-methodology and professional-advice boundaries.",
        ],
    }


def public_sustainability_indicators() -> Dict[str, Any]:
    return {
        "ok": True,
        "generated_at": _now(),
        "title": "Sustainability Indicator Context",
        "summary": "Public-safe sustainability indicator context across climate, energy, environment, biodiversity, development, research, and repository layers.",
        "public_status": "public_candidate",
        "indicators": SUSTAINABILITY_INDICATORS,
        "indicator_groups": DEVELOPMENT_INDICATOR_GROUPS,
        "recommended_shortcode": "[sc_public_sustainability_indicators]",
        "methodology": [
            "Use sustainability indicators as context for learning, dashboards, and source methodology.",
            "Do not present them as SDG certification, ESG assurance, compliance review, or investment advice.",
            "Prefer conservative descriptions and source-labeled display over automated scoring claims.",
        ],
    }
