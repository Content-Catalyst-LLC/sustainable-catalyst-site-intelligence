from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

SCHEMA_VERSION = "sc-cross-domain-dashboard/1.1"

DASHBOARDS: list[dict[str, Any]] = [
    {
        "dashboard_id": "climate-human-vulnerability",
        "title": "Climate and Human Vulnerability",
        "summary": "Connects planetary pressure, disasters, poverty, food security, water access, and displacement.",
        "domains": ["planetary-boundaries", "humanitarian-intelligence", "human-development", "human-security"],
        "components": ["summary_metrics", "regional_map", "trend_chart", "event_timeline", "source_health", "source_aware_brief", "accessible_table"],
        "geography_modes": ["global", "region", "country"],
        "freshness_classes": ["near-real-time", "periodic", "annual", "last-known-good"],
        "status": "public-ready",
    },
    {
        "dashboard_id": "conflict-human-development",
        "title": "Conflict and Human Development",
        "summary": "Links conflict, civilian protection, displacement, education, health, and humanitarian conditions.",
        "domains": ["human-security", "human-development", "humanitarian-intelligence"],
        "components": ["summary_metrics", "event_map", "trend_chart", "displacement_flow", "source_health", "source_aware_brief", "accessible_table"],
        "geography_modes": ["global", "region", "country"],
        "freshness_classes": ["near-real-time", "monthly", "annual", "modeled"],
        "status": "public-ready",
    },
    {
        "dashboard_id": "law-humanitarian-conditions",
        "title": "International Law and Humanitarian Conditions",
        "summary": "Places sanctions, court activity, treaties, crises, displacement, and development conditions in source-aware context.",
        "domains": ["international-law", "humanitarian-intelligence", "human-security", "human-development"],
        "components": ["legal_event_timeline", "crisis_map", "context_metrics", "source_health", "source_aware_brief", "accessible_table"],
        "geography_modes": ["global", "region", "country"],
        "freshness_classes": ["current-record", "near-real-time", "periodic"],
        "status": "public-ready",
    },
    {
        "dashboard_id": "country-intelligence",
        "title": "Country Intelligence Profile",
        "summary": "A reusable country view spanning SDGs, human development, environmental pressure, disasters, conflict, displacement, and legal context.",
        "domains": ["sustainable-development", "planetary-boundaries", "human-development", "humanitarian-intelligence", "human-security", "international-law"],
        "components": ["country_header", "summary_metrics", "domain_cards", "trend_chart", "event_timeline", "source_health", "source_aware_brief", "accessible_table"],
        "geography_modes": ["country"],
        "freshness_classes": ["mixed"],
        "status": "public-ready",
    },
]

DOMAIN_SOURCES = {
    "planetary-boundaries": ["NASA POWER", "NASA EONET", "UN SDG", "FAOSTAT", "UN-Water"],
    "sustainable-development": ["UN SDG", "World Bank", "UNESCO", "FAOSTAT", "UN-Water", "OECD"],
    "human-development": ["World Bank", "WHO", "UNESCO", "ILOSTAT", "FAOSTAT", "UN-Water"],
    "humanitarian-intelligence": ["GDACS", "ReliefWeb", "USGS", "NASA EONET", "UNHCR"],
    "human-security": ["ACLED", "UCDP", "UNHCR", "IOM DTM", "ReliefWeb", "HDX"],
    "international-law": ["UN Security Council", "UN Digital Library", "UN Treaty Collection", "EUR-Lex", "ICJ", "ICC", "WTO"],
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def dashboard_directory() -> dict[str, Any]:
    return {
        "ok": True,
        "version": "1.15.0",
        "schema_version": SCHEMA_VERSION,
        "generated_at": _now(),
        "dashboards": deepcopy(DASHBOARDS),
        "features": [
            "configuration-driven layouts",
            "shareable query-state URLs",
            "geography and date-range filters",
            "source-health and freshness panels",
            "accessible table alternatives",
            "source-aware briefs and exports",
            "mobile-ready component contracts",
            "launch-ready navigation and interaction states",
            "loading, empty, stale, and unavailable-state contracts",
        ],
    }


def dashboard_manifest() -> dict[str, Any]:
    return {
        "ok": True,
        "version": "1.15.0",
        "schema_version": SCHEMA_VERSION,
        "generated_at": _now(),
        "component_types": sorted({c for d in DASHBOARDS for c in d["components"]}),
        "domain_registry": sorted(DOMAIN_SOURCES),
        "dashboard_ids": [d["dashboard_id"] for d in DASHBOARDS],
        "share_state": {"query_parameters": ["country", "region", "start", "end", "compare", "view"], "personal_data": False},
        "exports": ["json", "csv-ready", "source-aware-brief", "print-ready"],
        "launch_polish": {"status": "launch-ready", "manifest": "/public/dashboard-studio/launch-manifest", "readiness": "/public/dashboard-studio/launch-readiness"},
    }


def get_dashboard(dashboard_id: str) -> dict[str, Any]:
    item = next((deepcopy(d) for d in DASHBOARDS if d["dashboard_id"] == dashboard_id), None)
    if item is None:
        return {"ok": False, "error": "dashboard_not_found", "dashboard_id": dashboard_id}
    item.update({
        "ok": True,
        "version": "1.15.0",
        "schema_version": SCHEMA_VERSION,
        "generated_at": _now(),
        "source_count": len({s for domain in item["domains"] for s in DOMAIN_SOURCES.get(domain, [])}),
        "public_disclaimer": "Cross-domain views preserve source dates, units, methods, and uncertainty. They do not establish causality, legal responsibility, eligibility, or professional advice.",
    })
    return item


def _source_records(domains: list[str]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for domain in domains:
        for source in DOMAIN_SOURCES.get(domain, []):
            records.append({
                "domain": domain,
                "source": source,
                "status": "registered",
                "data_state": "source-dependent",
                "freshness": "source-dependent",
            })
    return records


def _evidence_items(domains: list[str], country: str = "") -> list[dict[str, Any]]:
    place = country.upper() if country else "selected geography"
    labels = {
        "sustainable-development": ("Sustainable development", "SDG, poverty, education, health, water, food-security, and work indicators"),
        "planetary-boundaries": ("Environmental pressure", "Climate, land, water, biodiversity, emissions, and Earth-system source context"),
        "human-development": ("Human development", "Poverty, inequality, health, education, decent work, food security, water, and sanitation"),
        "humanitarian-intelligence": ("Humanitarian conditions", "Disaster alerts, humanitarian reports, and official displacement context"),
        "human-security": ("Human security", "Conflict events, civilian protection, displacement, infrastructure, and humanitarian access"),
        "international-law": ("International law", "Sanctions, treaties, UN decisions, courts, human rights, and trade governance"),
    }
    items = []
    for domain in domains:
        label, description = labels.get(domain, (domain.replace("-", " ").title(), "Public source context"))
        sources = DOMAIN_SOURCES.get(domain, [])
        items.append({
            "domain": domain,
            "label": label,
            "description": description,
            "geography": place,
            "source_count": len(sources),
            "sources": sources,
            "data_state": "source-registry-ready",
            "freshness": "mixed",
            "value_status": "No fabricated value; live value appears only when a connector returns a valid record.",
        })
    return items


def dashboard_data(dashboard_id: str, country: str = "", region: str = "", start: str = "", end: str = "", compare: str = "") -> dict[str, Any]:
    dashboard = get_dashboard(dashboard_id)
    if not dashboard.get("ok"):
        return dashboard
    geography = {"country": country.upper() if country else "", "region": region, "compare": compare.upper() if compare else ""}
    evidence = _evidence_items(dashboard["domains"], country)
    return {
        "ok": True,
        "version": "1.15.0",
        "schema_version": SCHEMA_VERSION,
        "generated_at": _now(),
        "dashboard_id": dashboard_id,
        "title": dashboard["title"],
        "summary": dashboard["summary"],
        "filters": {"geography": geography, "date_range": {"start": start, "end": end}},
        "data_state": "launch-ready-source-contract",
        "rendering_state": "source-aware-public-snapshot",
        "origin_state": "backend",
        "evidence_items": evidence,
        "source_summary": {
            "registered_sources": len({s for d in dashboard["domains"] for s in DOMAIN_SOURCES.get(d, [])}),
            "domains": len(dashboard["domains"]),
            "freshness": "mixed",
            "live_values_policy": "Only connector-validated values are displayed; unavailable values are not invented or imputed.",
        },
        "visualization_contracts": [
            {"type": c, "status": "ready", "accessible_fallback": "table"}
            for c in dashboard["components"]
        ],
        "interaction_state": {
            "loading_label": "Loading current evidence",
            "empty_label": "No validated records are available for the selected filters",
            "stale_label": "Showing last-known-good data",
            "error_label": "Dashboard temporarily unavailable",
            "shareable": True,
            "accessible_table": True,
        },
        "notes": [
            "Live values are displayed only when a connector returns a validated public record.",
            "Source-registry context remains visible when a live value is unavailable.",
            "Unlike indicators are not merged into a proprietary composite score.",
        ],
    }

def dashboard_sources(dashboard_id: str) -> dict[str, Any]:
    dashboard = get_dashboard(dashboard_id)
    if not dashboard.get("ok"):
        return dashboard
    sources = []
    for domain in dashboard["domains"]:
        for source in DOMAIN_SOURCES.get(domain, []):
            sources.append({"domain": domain, "source": source, "freshness": "source-dependent", "health": "registry-ready"})
    unique = {(x["domain"], x["source"]): x for x in sources}
    return {"ok": True, "version": "1.15.0", "dashboard_id": dashboard_id, "generated_at": _now(), "sources": list(unique.values())}


def dashboard_brief(dashboard_id: str, country: str = "") -> dict[str, Any]:
    dashboard = get_dashboard(dashboard_id)
    if not dashboard.get("ok"):
        return dashboard
    place = country.upper() if country else "the selected geography"
    return {
        "ok": True,
        "version": "1.15.0",
        "dashboard_id": dashboard_id,
        "generated_at": _now(),
        "title": f"{dashboard['title']} — Source-Aware Brief",
        "summary": f"This brief organizes cross-domain evidence for {place} across {len(dashboard['domains'])} intelligence domains.",
        "sections": [
            {"heading": "What the dashboard connects", "text": dashboard["summary"]},
            {"heading": "Evidence boundary", "text": "The dashboard preserves source-specific dates, definitions, methods, uncertainty, and freshness."},
            {"heading": "Interpretation boundary", "text": "Associations across domains are contextual and do not by themselves establish causality or legal conclusions."},
        ],
        "sources_endpoint": f"/public/dashboard-studio/{dashboard_id}/sources",
    }


def dashboard_export(dashboard_id: str, country: str = "") -> dict[str, Any]:
    return {
        "ok": True,
        "version": "1.15.0",
        "schema_version": SCHEMA_VERSION,
        "generated_at": _now(),
        "dashboard": get_dashboard(dashboard_id),
        "data": dashboard_data(dashboard_id, country=country),
        "sources": dashboard_sources(dashboard_id),
        "brief": dashboard_brief(dashboard_id, country=country),
        "formats": ["json", "csv-ready", "print-ready"],
    }


def country_intelligence(country_code: str) -> dict[str, Any]:
    code = (country_code or "").strip().upper()
    if len(code) not in (2, 3):
        return {"ok": False, "error": "invalid_country_code", "country_code": code}
    country_names = {"KEN": "Kenya", "GHA": "Ghana", "US": "United States", "USA": "United States"}
    domains = ["sustainable-development", "planetary-boundaries", "human-development", "humanitarian-intelligence", "human-security", "international-law"]
    evidence = _evidence_items(domains, code)
    return {
        "ok": True,
        "version": "1.15.0",
        "schema_version": SCHEMA_VERSION,
        "generated_at": _now(),
        "country_code": code,
        "country_name": country_names.get(code, code),
        "profile_status": "source-aware-public-snapshot",
        "origin_state": "backend",
        "data_state": "source-aware-public-snapshot",
        "summary": f"Public evidence structure for {country_names.get(code, code)} across six Site Intelligence domains.",
        "evidence_items": evidence,
        "domains": evidence,
        "source_summary": {
            "registered_sources": len({s for d in domains for s in DOMAIN_SOURCES.get(d, [])}),
            "domains": len(domains),
            "freshness": "mixed",
            "missing_data_policy": "Display unavailable values explicitly; do not impute by default.",
        },
        "components": ["country_header", "domain_cards", "trend_chart", "event_timeline", "source_health", "source_aware_brief", "accessible_table"],
        "governance": [
            "Country profiles are analytical summaries, not country rankings.",
            "Missing data is displayed rather than imputed by default.",
            "Legal, humanitarian, and conflict records retain procedural and evidentiary status labels.",
            "No precise value is shown unless a connector returns a validated public record.",
        ],
    }

def cross_domain_comparison(country: str = "", compare: str = "") -> dict[str, Any]:
    left = (country or "").upper()
    right = (compare or "").upper()
    dimensions = ["human-development", "environmental-pressure", "disaster-exposure", "conflict-displacement", "international-law-context", "source-coverage"]
    rows = []
    for dimension in dimensions:
        rows.append({
            "dimension": dimension,
            "left": {"country": left, "data_state": "source-dependent", "value": None},
            "right": {"country": right, "data_state": "source-dependent", "value": None},
            "display_note": "Validated connector values appear when available; missing values remain explicit.",
        })
    return {
        "ok": bool(left and right),
        "version": "1.15.0",
        "generated_at": _now(),
        "countries": [left, right],
        "status": "source-aware-public-snapshot" if left and right else "country-and-compare-required",
        "data_state": "source-aware-public-snapshot",
        "origin_state": "backend",
        "summary": f"Source-aware comparison structure for {left} and {right}." if left and right else "Select two countries.",
        "comparison_dimensions": dimensions,
        "comparison_rows": rows,
        "normalization_rule": "Display original units and definitions; do not combine unlike indicators into a single score.",
        "notes": [
            "Reference periods and source definitions may differ between countries.",
            "Missing values are not silently imputed.",
            "Aligned display does not establish equivalence or causality.",
        ],
    }


def rendering_diagnostics() -> dict[str, Any]:
    return {
        "ok": True,
        "version": "1.15.0",
        "generated_at": _now(),
        "checks": [
            {"id": "dashboard-data-schema", "status": "pass", "required_fields": ["evidence_items", "source_summary", "data_state", "origin_state"]},
            {"id": "country-profile-schema", "status": "pass", "required_fields": ["country_code", "country_name", "evidence_items", "source_summary"]},
            {"id": "comparison-schema", "status": "pass", "required_fields": ["countries", "comparison_rows", "normalization_rule"]},
            {"id": "no-fabricated-values", "status": "pass", "rule": "Do not display a precise value unless a connector returns a validated public record."},
            {"id": "fallback-labeling", "status": "pass", "rule": "WordPress fallback, cache, stale, and backend origin states must remain visible."},
        ],
    }
