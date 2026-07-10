from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

SCHEMA = "sc-conflict-displacement-human-security/1.0"

SOURCES: List[Dict[str, Any]] = [
    {
        "source_id": "acled",
        "title": "Armed Conflict Location & Event Data",
        "organization": "ACLED",
        "base_url": "https://acleddata.com",
        "access_type": "authenticated_api",
        "freshness": "near_real_time",
        "coverage": "global",
        "requires_key": True,
        "domains": ["political_violence", "protests", "violence_against_civilians", "infrastructure_events"],
        "role": "Event-level conflict and protest monitoring with actor, location, event-type, and fatality fields.",
        "limitations": "Access terms, attribution, methodological revisions, reporting bias, and verification status must remain visible. Fatality values are estimates.",
    },
    {
        "source_id": "ucdp",
        "title": "Uppsala Conflict Data Program",
        "organization": "Uppsala University",
        "base_url": "https://ucdp.uu.se",
        "access_type": "public_api_and_downloads",
        "freshness": "periodic",
        "coverage": "global",
        "requires_key": False,
        "domains": ["organized_violence", "battle_deaths", "one_sided_violence", "non_state_conflict"],
        "role": "Research-grade conflict definitions, event records, conflict episodes, and fatality estimates.",
        "limitations": "Not a live alert feed; definitions, inclusion thresholds, coding rules, and release versions must remain explicit.",
    },
    {
        "source_id": "unhcr",
        "title": "UNHCR Refugee Data Finder",
        "organization": "United Nations High Commissioner for Refugees",
        "base_url": "https://api.unhcr.org/population/v1",
        "access_type": "public_api",
        "freshness": "annual_and_periodic",
        "coverage": "global",
        "requires_key": False,
        "domains": ["refugees", "asylum_seekers", "internal_displacement", "statelessness", "durable_solutions"],
        "role": "Official population statistics for forced displacement and international protection.",
        "limitations": "Reference periods differ from event feeds; figures may be provisional, revised, estimated, or jointly reported.",
    },
    {
        "source_id": "iom-dtm",
        "title": "IOM Displacement Tracking Matrix",
        "organization": "International Organization for Migration",
        "base_url": "https://dtm.iom.int",
        "access_type": "public_portal_and_datasets",
        "freshness": "country_specific_periodic",
        "coverage": "multi-country",
        "requires_key": False,
        "domains": ["mobility_tracking", "displacement", "flow_monitoring", "needs_assessments"],
        "role": "Operational displacement, mobility, flow-monitoring, and needs-assessment datasets.",
        "limitations": "Methods and geographic coverage differ by operation; records must preserve round, assessment date, population definition, and source methodology.",
    },
    {
        "source_id": "reliefweb",
        "title": "ReliefWeb API",
        "organization": "UN Office for the Coordination of Humanitarian Affairs",
        "base_url": "https://api.reliefweb.int/v1",
        "access_type": "public_api_with_appname",
        "freshness": "near_real_time",
        "coverage": "global",
        "requires_key": False,
        "domains": ["humanitarian_reports", "access", "protection", "displacement", "crisis_updates"],
        "role": "Current humanitarian reports, assessments, maps, appeals, and situation updates.",
        "limitations": "A pre-approved appname is required for production use; source documents retain their own evidentiary and editorial status.",
    },
    {
        "source_id": "hdx",
        "title": "Humanitarian Data Exchange",
        "organization": "OCHA Centre for Humanitarian Data",
        "base_url": "https://data.humdata.org",
        "access_type": "catalog_api_and_downloads",
        "freshness": "dataset_specific",
        "coverage": "global",
        "requires_key": False,
        "domains": ["humanitarian_access", "population_exposure", "infrastructure", "food_security", "displacement"],
        "role": "Catalog and distribution layer for humanitarian datasets from UN agencies, governments, and response organizations.",
        "limitations": "Licenses, sensitivity classifications, update schedules, field definitions, and responsible-data restrictions vary by dataset.",
    },
]

MONITORS: List[Dict[str, Any]] = [
    {"monitor_id": "conflict-events", "label": "Conflict and political-violence events", "sources": ["acled", "ucdp"], "outputs": ["event map", "actor context", "event types", "fatality estimates"]},
    {"monitor_id": "civilian-protection", "label": "Violence against civilians and protection risk", "sources": ["acled", "reliefweb", "hdx"], "outputs": ["civilian events", "protection reports", "risk context", "source caveats"]},
    {"monitor_id": "displacement-flows", "label": "Forced displacement and mobility", "sources": ["unhcr", "iom-dtm", "reliefweb"], "outputs": ["refugees", "asylum seekers", "IDPs", "returns", "mobility flows"]},
    {"monitor_id": "infrastructure-security", "label": "Attacks and disruption affecting civilian infrastructure", "sources": ["acled", "reliefweb", "hdx"], "outputs": ["health", "education", "water", "energy", "transport", "communications"]},
    {"monitor_id": "humanitarian-access", "label": "Humanitarian access and operational constraints", "sources": ["reliefweb", "hdx", "iom-dtm"], "outputs": ["access constraints", "service disruption", "needs assessments", "operational coverage"]},
    {"monitor_id": "modeled-risk", "label": "Modeled conflict and displacement risk", "sources": ["acled", "ucdp", "unhcr"], "outputs": ["forecast metadata", "confidence", "horizon", "model version", "limitations"]},
]

EVENT_SCHEMA: Dict[str, Any] = {
    "schema": SCHEMA,
    "required": ["source_id", "record_id", "record_type", "title", "event_date", "geographies", "source_url", "retrieved_at"],
    "optional": ["actors", "event_type", "civilian_targeting", "fatalities", "infrastructure_sectors", "displacement_categories", "population_value", "unit", "confidence", "forecast_horizon", "model_version", "methodology", "caveats", "is_modeled", "is_derived"],
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def source_registry() -> Dict[str, Any]:
    return {
        "ok": True,
        "generated_at": _now(),
        "version_scope": "v1.11.0",
        "schema": SCHEMA,
        "title": "Conflict, Displacement, and Human Security Source Registry",
        "summary": "Source-aware conflict, civilian-protection, forced-displacement, infrastructure, and humanitarian-access monitoring.",
        "counts": {"sources": len(SOURCES), "monitors": len(MONITORS), "key_required": sum(bool(s["requires_key"]) for s in SOURCES)},
        "sources": SOURCES,
    }


def overview() -> Dict[str, Any]:
    return {
        "ok": True,
        "generated_at": _now(),
        "version_scope": "v1.11.0",
        "schema": SCHEMA,
        "title": "Conflict, Displacement, and Human Security",
        "summary": "An evidence-aware monitor connecting conflict events, civilian harm, infrastructure disruption, forced displacement, humanitarian access, and modeled risk.",
        "monitors": MONITORS,
        "sources": SOURCES,
        "freshness_labels": ["near_real_time", "daily", "periodic", "annual", "modeled_forecast", "last_known_good", "temporarily_unavailable"],
        "governance": [
            "Distinguish observed events, reported allegations, verified findings, official statistics, and modeled forecasts.",
            "Never infer guilt, combatant status, legal responsibility, refugee status, or eligibility from aggregate records.",
            "Preserve source methodology, publication date, event date, confidence, geographic precision, and revision status.",
            "Suppress or generalize sensitive geographic detail when disclosure could increase risk to affected people or responders.",
            "Treat fatality, displacement, and population-exposure values as source-bound estimates with visible uncertainty.",
        ],
    }


def monitor_detail(monitor_id: str) -> Dict[str, Any]:
    monitor = next((item for item in MONITORS if item["monitor_id"] == monitor_id), None)
    if not monitor:
        raise KeyError(monitor_id)
    ids = set(monitor["sources"])
    return {
        "ok": True,
        "generated_at": _now(),
        "version_scope": "v1.11.0",
        "schema": SCHEMA,
        "title": monitor["label"],
        "monitor": monitor,
        "sources": [source for source in SOURCES if source["source_id"] in ids],
        "records": [],
        "public_status": "registered_source_monitor",
        "notice": "Live ingestion is source-specific. Public records must retain source, date, geography, confidence, methodology, and safety caveats.",
    }


def event_stream(record_type: Optional[str] = None, country: Optional[str] = None) -> Dict[str, Any]:
    return {
        "ok": True,
        "generated_at": _now(),
        "version_scope": "v1.11.0",
        "schema": SCHEMA,
        "title": "Conflict and Human Security Event Stream",
        "filters": {"record_type": record_type, "country": country},
        "records": [],
        "supported_record_types": ["conflict_event", "violence_against_civilians", "infrastructure_incident", "displacement_update", "access_constraint", "humanitarian_report", "modeled_forecast"],
        "record_schema": EVENT_SCHEMA,
        "notice": "Empty records indicate a contract-ready monitor without configured live credentials or approved source ingestion.",
    }


def displacement_flows() -> Dict[str, Any]:
    return {
        "ok": True,
        "generated_at": _now(),
        "version_scope": "v1.11.0",
        "schema": SCHEMA,
        "title": "Forced Displacement and Mobility Context",
        "sources": [s for s in SOURCES if s["source_id"] in {"unhcr", "iom-dtm", "reliefweb"}],
        "categories": ["refugees", "asylum_seekers", "internally_displaced_people", "stateless_people", "returnees", "other_people_in_need_of_international_protection"],
        "records": [],
        "methodology_notes": ["Keep stock, flow, event, registration, and assessment figures separate.", "Retain reference date, population definition, geographic coverage, and provisional or revised status."],
    }


def modeled_risk() -> Dict[str, Any]:
    return {
        "ok": True,
        "generated_at": _now(),
        "version_scope": "v1.11.0",
        "schema": SCHEMA,
        "title": "Modeled Conflict and Displacement Risk",
        "records": [],
        "required_forecast_metadata": ["model_provider", "model_version", "forecast_horizon", "generated_at", "confidence_or_probability", "training_or_reference_window", "known_limitations"],
        "labels": ["modeled_forecast", "experimental", "not_observed", "not_an_emergency_warning"],
        "notice": "Forecasts are scenario and risk signals, not predictions of individual behavior or authoritative emergency warnings.",
    }


def methodology() -> Dict[str, Any]:
    return {
        "ok": True,
        "generated_at": _now(),
        "version_scope": "v1.11.0",
        "schema": SCHEMA,
        "title": "Conflict, Displacement, and Human Security Methodology",
        "normalized_record_schema": EVENT_SCHEMA,
        "status_taxonomy": ["observed", "reported", "alleged", "verified_by_source", "official_statistic", "estimated", "modeled_forecast", "revised", "unknown"],
        "methods": [
            "Use source-specific definitions and retain coding-system versions.",
            "Separate event dates, publication dates, assessment rounds, and reference periods.",
            "Keep fatalities, affected populations, displacement stocks, and displacement flows as distinct measures.",
            "Do not combine unlike sources into a proprietary human-security score by default.",
            "Require human review for narrative claims about responsibility, intent, legal classification, or civilian status.",
            "Apply responsible-data review before exposing granular locations or vulnerable-group attributes.",
        ],
        "excluded_uses": ["military targeting", "individual risk scoring", "refugee-status determination", "legal advice", "automated attribution of responsibility", "emergency warning"],
    }


def export_manifest() -> Dict[str, Any]:
    return {
        "ok": True,
        "generated_at": _now(),
        "version_scope": "v1.11.0",
        "schema": SCHEMA,
        "title": "Conflict, Displacement, and Human Security Export",
        "formats": ["json", "csv_ready"],
        "sources": SOURCES,
        "monitors": MONITORS,
        "record_schema": EVENT_SCHEMA,
        "methodology": methodology(),
        "records": [],
    }
