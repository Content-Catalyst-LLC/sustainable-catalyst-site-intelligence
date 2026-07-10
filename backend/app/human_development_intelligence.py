from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

SCHEMA = "sc-human-development-social-conditions/1.0"

SOURCES: List[Dict[str, Any]] = [
    {
        "source_id": "un-sdg",
        "title": "United Nations SDG Global Database",
        "organization": "United Nations Statistics Division",
        "base_url": "https://unstats.un.org/SDGAPI/v1/sdg",
        "freshness": "periodic_official",
        "coverage": "global",
        "domains": ["poverty", "health", "education", "gender", "water", "work", "inequality"],
        "requires_key": False,
        "role": "Official SDG indicator, target, series, geography, and disaggregation metadata.",
        "limitations": "Availability and reporting frequency vary substantially by indicator and country.",
    },
    {
        "source_id": "world-bank-indicators",
        "title": "World Bank Indicators API",
        "organization": "World Bank",
        "base_url": "https://api.worldbank.org/v2",
        "freshness": "annual_or_periodic",
        "coverage": "global",
        "domains": ["poverty", "inequality", "health", "education", "employment", "social_protection"],
        "requires_key": False,
        "role": "Cross-country development indicators and historical time series.",
        "limitations": "Publication years, revisions, estimation methods, and country coverage differ by series.",
    },
    {
        "source_id": "world-bank-pip",
        "title": "Poverty and Inequality Platform API",
        "organization": "World Bank",
        "base_url": "https://api.worldbank.org/pip/v1",
        "freshness": "periodic_official",
        "coverage": "global",
        "domains": ["poverty", "inequality", "shared_prosperity"],
        "requires_key": False,
        "role": "Poverty headcounts, poverty gaps, welfare distributions, and inequality measures.",
        "limitations": "Results depend on poverty line, welfare concept, survey year, interpolation, and comparability metadata.",
    },
    {
        "source_id": "who-gho",
        "title": "WHO Global Health Observatory",
        "organization": "World Health Organization",
        "base_url": "https://ghoapi.azureedge.net/api",
        "freshness": "periodic_official",
        "coverage": "global",
        "domains": ["health", "mortality", "disease", "health_systems", "environmental_health"],
        "requires_key": False,
        "role": "Health-related SDG indicators and public-health statistics.",
        "limitations": "Interfaces and indicator definitions can change; production connectors must retain WHO metadata and revision dates.",
    },
    {
        "source_id": "who-health-inequality",
        "title": "WHO Health Inequality Data Repository",
        "organization": "World Health Organization",
        "base_url": "https://www.who.int/data/inequality-monitor",
        "freshness": "periodic_official",
        "coverage": "global",
        "domains": ["health_inequality", "sex", "wealth", "education", "place_of_residence"],
        "requires_key": False,
        "role": "Disaggregated health indicators and inequality dimensions.",
        "limitations": "Subgroup comparability and sample sizes must remain visible; not every country reports every dimension.",
    },
    {
        "source_id": "unesco-uis",
        "title": "UNESCO Institute for Statistics",
        "organization": "UNESCO",
        "base_url": "https://api.uis.unesco.org/sdmx",
        "freshness": "annual_or_periodic",
        "coverage": "global",
        "domains": ["education", "literacy", "learning", "science", "culture"],
        "requires_key": False,
        "role": "Official education, literacy, completion, participation, and SDG 4 statistics.",
        "limitations": "Learning assessments, administrative records, household surveys, and modeled series must not be treated as interchangeable.",
    },
    {
        "source_id": "ilostat",
        "title": "ILOSTAT SDMX and Bulk Data",
        "organization": "International Labour Organization",
        "base_url": "https://rplumber.ilo.org/data/indicator",
        "freshness": "annual_quarterly_or_monthly",
        "coverage": "global",
        "domains": ["employment", "unemployment", "working_poverty", "wages", "child_labour", "occupational_safety"],
        "requires_key": False,
        "role": "Decent-work, labour-market, wages, employment, and labour-rights indicators.",
        "limitations": "National concepts, survey coverage, seasonality, and modeled estimates require explicit labeling.",
    },
    {
        "source_id": "faostat",
        "title": "FAOSTAT",
        "organization": "Food and Agriculture Organization of the United Nations",
        "base_url": "https://fenixservices.fao.org/faostat/api/v1",
        "freshness": "annual_or_periodic",
        "coverage": "global",
        "domains": ["food_security", "nutrition", "agriculture", "food_prices", "land", "emissions"],
        "requires_key": False,
        "role": "Food, agriculture, hunger, production, price, land-use, and nutrition context.",
        "limitations": "Commodity, unit, aggregation, and methodological definitions vary across domains.",
    },
    {
        "source_id": "un-water-sdg6",
        "title": "UN-Water SDG 6 Data Portal",
        "organization": "UN-Water",
        "base_url": "https://sdg6data.org/api",
        "freshness": "periodic_official",
        "coverage": "global",
        "domains": ["drinking_water", "sanitation", "hygiene", "wastewater", "water_stress", "water_ecosystems"],
        "requires_key": False,
        "role": "SDG 6 indicators and source-agency water and sanitation series.",
        "limitations": "Source agencies, reporting cycles, estimates, and geographic coverage vary by indicator.",
    },
]

DOMAINS: List[Dict[str, Any]] = [
    {"domain_id": "poverty", "label": "Poverty and material deprivation", "sdgs": ["1"], "sources": ["world-bank-pip", "world-bank-indicators", "un-sdg"], "indicators": ["poverty headcount", "poverty gap", "multidimensional deprivation", "social protection coverage"]},
    {"domain_id": "inequality", "label": "Inequality and shared prosperity", "sdgs": ["5", "10"], "sources": ["world-bank-pip", "world-bank-indicators", "who-health-inequality", "un-sdg"], "indicators": ["Gini index", "income shares", "growth by welfare group", "gender and subgroup disparities"]},
    {"domain_id": "health", "label": "Health and wellbeing", "sdgs": ["3"], "sources": ["who-gho", "who-health-inequality", "un-sdg", "world-bank-indicators"], "indicators": ["life expectancy", "maternal mortality", "child mortality", "disease burden", "health service coverage"]},
    {"domain_id": "education", "label": "Education and learning", "sdgs": ["4"], "sources": ["unesco-uis", "world-bank-indicators", "un-sdg"], "indicators": ["enrollment", "completion", "literacy", "learning proficiency", "education expenditure"]},
    {"domain_id": "decent-work", "label": "Employment and decent work", "sdgs": ["8"], "sources": ["ilostat", "world-bank-indicators", "un-sdg"], "indicators": ["employment", "unemployment", "working poverty", "wages", "child labour", "occupational injury"]},
    {"domain_id": "food-security", "label": "Food security and nutrition", "sdgs": ["2"], "sources": ["faostat", "un-sdg", "world-bank-indicators"], "indicators": ["undernourishment", "food insecurity", "food prices", "agricultural productivity", "nutrition outcomes"]},
    {"domain_id": "water-sanitation", "label": "Water, sanitation, and hygiene", "sdgs": ["6"], "sources": ["un-water-sdg6", "who-gho", "un-sdg", "world-bank-indicators"], "indicators": ["safe drinking water", "sanitation", "hygiene", "wastewater treatment", "water stress"]},
]

NORMALIZED_OBSERVATION_SCHEMA: Dict[str, Any] = {
    "schema": SCHEMA,
    "required": ["source_id", "indicator_id", "geography", "period", "value", "unit", "freshness", "observation_type", "retrieved_at"],
    "optional": ["sdg_goals", "dimensions", "uncertainty", "methodology", "revision_status", "comparability", "source_url", "is_derived"],
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def source_registry() -> Dict[str, Any]:
    return {
        "ok": True,
        "generated_at": _now(),
        "version_scope": "v1.10.0",
        "schema": SCHEMA,
        "title": "Human Development and Social Conditions Source Registry",
        "summary": "Official and public sources for poverty, inequality, health, education, work, food security, and water and sanitation.",
        "counts": {"sources": len(SOURCES), "domains": len(DOMAINS), "no_key_required": sum(not item["requires_key"] for item in SOURCES)},
        "sources": SOURCES,
    }


def overview() -> Dict[str, Any]:
    return {
        "ok": True,
        "generated_at": _now(),
        "version_scope": "v1.10.0",
        "schema": SCHEMA,
        "title": "Human Development and Social Conditions",
        "summary": "A source-aware public observatory for material wellbeing, opportunity, health, learning, work, food security, water, sanitation, and inequality.",
        "domains": DOMAINS,
        "sources": SOURCES,
        "freshness_labels": ["monthly", "quarterly", "annual", "periodic_official", "modeled_estimate", "last_known_good", "temporarily_unavailable"],
        "governance": [
            "Do not combine different poverty lines or welfare concepts without explicit labels.",
            "Retain sex, age, residence, wealth, disability, and other disaggregation dimensions when available.",
            "Do not present modeled estimates as directly observed values.",
            "Display reference period and revision status prominently.",
            "Do not infer individual eligibility, diagnosis, legal status, or entitlement from aggregate indicators.",
        ],
    }


def domain_detail(domain_id: str) -> Dict[str, Any]:
    domain = next((item for item in DOMAINS if item["domain_id"] == domain_id), None)
    if not domain:
        raise KeyError(domain_id)
    source_ids = set(domain["sources"])
    return {
        "ok": True,
        "generated_at": _now(),
        "version_scope": "v1.10.0",
        "schema": SCHEMA,
        "domain": domain,
        "sources": [item for item in SOURCES if item["source_id"] in source_ids],
        "observations": [],
        "display_state": "connector_contract_ready",
        "note": "Empty observations mean the live connector runtime has not supplied normalized records; they do not indicate an absence of social need.",
    }


def country_profile(country_code: Optional[str] = None) -> Dict[str, Any]:
    return {
        "ok": True,
        "generated_at": _now(),
        "version_scope": "v1.10.0",
        "schema": SCHEMA,
        "title": "Human Development Country Profile",
        "country_code": (country_code or "").upper() or None,
        "sections": [item["domain_id"] for item in DOMAINS],
        "indicators": [],
        "display_state": "country_required" if not country_code else "connector_contract_ready",
        "comparison_rules": ["Use consistent indicator definitions and units.", "Keep source year visible.", "Show missing data rather than imputing silently.", "Retain modeled-estimate labels."],
    }


def inequality_dimensions() -> Dict[str, Any]:
    return {
        "ok": True,
        "generated_at": _now(),
        "version_scope": "v1.10.0",
        "schema": SCHEMA,
        "title": "Disaggregation and Inequality Dimensions",
        "dimensions": ["sex", "age", "wealth_quintile", "education", "urban_rural", "subnational_area", "disability", "migration_status", "employment_status"],
        "rules": ["Suppress unsafe small cells.", "Retain denominator and sample information when published.", "Do not compare subgroup estimates across incompatible surveys.", "Separate absolute gaps, relative gaps, and distributional measures."],
    }


def methodology() -> Dict[str, Any]:
    return {
        "ok": True,
        "generated_at": _now(),
        "version_scope": "v1.10.0",
        "schema": SCHEMA,
        "title": "Human Development and Social Conditions Methodology",
        "normalized_observation_schema": NORMALIZED_OBSERVATION_SCHEMA,
        "rules": [
            "Preserve source definitions, units, reference periods, revisions, and estimation status.",
            "Do not aggregate poverty, health, education, labour, food, and water indicators into a proprietary score by default.",
            "Separate official reported data from modeled estimates and Sustainable Catalyst derived analysis.",
            "Show data gaps and methodological breaks as intelligence, not as zero values.",
            "Use population-weighted aggregation only when the indicator methodology permits it.",
        ],
    }


def export_manifest() -> Dict[str, Any]:
    return {
        "ok": True,
        "generated_at": _now(),
        "version_scope": "v1.10.0",
        "schema": SCHEMA,
        "title": "Human Development and Social Conditions Export Manifest",
        "formats": ["json", "csv-ready"],
        "datasets": ["sources", "domains", "disaggregation_dimensions", "normalized_observation_schema"],
        "records": {"sources": SOURCES, "domains": DOMAINS, "observation_schema": NORMALIZED_OBSERVATION_SCHEMA},
        "required_attribution": True,
    }
