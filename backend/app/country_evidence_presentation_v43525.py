from __future__ import annotations

"""Country Intelligence presentation and evidence hierarchy for Site Intelligence v4.36.1.

This module is deliberately presentation-only and network-free. It does not create,
average, or upgrade evidence. It translates canonical observation semantics into a
clear public hierarchy so annual structural statistics cannot visually masquerade
as current operational conditions.
"""

from datetime import datetime, timezone
from typing import Any, Mapping

from .version import APP_VERSION

VERSION = APP_VERSION
CONTRACT = "country-intelligence-presentation-evidence-hierarchy-v43525"
SCHEMA = "sc-site-intelligence-country-evidence-presentation/1.0"

ROLE_LABELS = {
    "national-statistical-authority": "PRIMARY OFFICIAL",
    "official-sector-authority": "SECTOR OFFICIAL",
    "intergovernmental-custodian": "INTERGOVERNMENTAL",
    "international-harmonized": "HARMONIZED BENCHMARK",
    "unknown": "PUBLISHED EVIDENCE",
}

CONCEPT_PRESENTATION = {
    "electricity_structural_access": {
        "scope_label": "STRUCTURAL ACCESS BASELINE",
        "priority": "supporting",
        "condition_status": "not-established-by-this-indicator",
        "note": "Measures structural electricity access under the source methodology. It does not measure current electricity supply, outage duration, grid functionality, hours of service, reliability, or generator dependence.",
    },
    "basic_drinking_water_access": {
        "scope_label": "STRUCTURAL WATER-ACCESS BASELINE",
        "priority": "supporting",
        "condition_status": "not-established-by-this-indicator",
        "note": "Measures structural drinking-water access under the source methodology. It does not measure current water availability, continuity, pressure, quality, or household service conditions.",
    },
    "population_total": {
        "scope_label": "POPULATION ESTIMATE",
        "priority": "core",
        "condition_status": "statistical",
        "note": "Population estimates remain tied to their reference period, methodology, geographic scope, and source authority.",
    },
    "life_expectancy_at_birth": {
        "scope_label": "HEALTH STATISTIC",
        "priority": "core",
        "condition_status": "statistical",
        "note": "Life expectancy is a population-level statistical measure, not a statement about current health-system functionality.",
    },
    "gdp_per_capita_current_usd": {
        "scope_label": "ECONOMIC STATISTIC",
        "priority": "core",
        "condition_status": "statistical",
        "note": "GDP per capita is an aggregate economic statistic and does not describe distribution, household welfare, physical destruction, or current access to goods and services by itself.",
    },
    "secondary_enrollment_gross": {
        "scope_label": "EDUCATION STATISTIC",
        "priority": "core",
        "condition_status": "statistical",
        "note": "Gross enrollment is a statistical participation measure and does not establish current school operability, physical access, attendance, or facility condition.",
    },
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _role_label(observation: Mapping[str, Any]) -> str:
    source = observation.get("source") if isinstance(observation.get("source"), Mapping) else {}
    evidence_label = _clean(observation.get("presentation_label") or observation.get("evidence_label")).upper()
    authority = _clean(source.get("authority_class") or observation.get("authority_class")).lower()
    if evidence_label == "LIVE / OPERATIONAL":
        return "OPERATIONAL"
    if evidence_label == "CURRENT OFFICIAL":
        return "CURRENT OFFICIAL"
    if evidence_label == "HARMONIZED BENCHMARK":
        return "HARMONIZED BENCHMARK"
    return ROLE_LABELS.get(authority, "PUBLISHED EVIDENCE")


def present_indicator(item: Mapping[str, Any]) -> dict[str, Any]:
    observation = item.get("canonical_observation") if isinstance(item.get("canonical_observation"), Mapping) else {}
    semantics = observation.get("semantics") if isinstance(observation.get("semantics"), Mapping) else {}
    concept_id = _clean(semantics.get("concept_id") or item.get("concept_id"))
    rule = CONCEPT_PRESENTATION.get(concept_id, {})
    source = observation.get("source") if isinstance(observation.get("source"), Mapping) else {}
    evidence_label = _clean(observation.get("presentation_label") or item.get("evidence_label") or item.get("data_state"))
    role = _role_label({**observation, "evidence_label": evidence_label})
    structural_warning = _clean(semantics.get("display_note") or semantics.get("warning"))
    note = structural_warning or rule.get("note") or "Interpret this value with its source, reporting period, geographic scope, units, and methodology."
    current_condition_allowed = bool(semantics.get("current_condition_claim_allowed"))
    if role == "HARMONIZED BENCHMARK":
        section = "international-benchmark"
    elif role in {"PRIMARY OFFICIAL", "CURRENT OFFICIAL", "SECTOR OFFICIAL"}:
        section = "official"
    elif role == "OPERATIONAL":
        section = "operational"
    else:
        section = "published"
    return {
        "role_label": role,
        "section": section,
        "scope_label": rule.get("scope_label") or ("OPERATIONAL CONDITION" if current_condition_allowed else "PUBLISHED INDICATOR"),
        "priority": rule.get("priority") or ("current" if current_condition_allowed else "core"),
        "current_condition_claim_allowed": current_condition_allowed,
        "condition_status": rule.get("condition_status") or ("operational" if current_condition_allowed else "statistical"),
        "interpretation_note": note,
        "transport_state": _clean(observation.get("transport_state") or item.get("transport_state")),
        "evidence_label": evidence_label,
        "authority_class": _clean(source.get("authority_class") or item.get("authority_class")) or "unknown",
        "source_id": _clean(source.get("source_id") or item.get("source_id")) or "unknown",
    }


def build_country_presentation(country: Mapping[str, Any], highlights: list[Mapping[str, Any]], *, missing_indicators: list[str] | None = None) -> dict[str, Any]:
    code = _clean(country.get("code")).upper()
    presented = []
    counts = {"official": 0, "operational": 0, "international-benchmark": 0, "published": 0}
    for raw in highlights:
        row = dict(raw)
        presentation = present_indicator(row)
        row["presentation"] = presentation
        presented.append(row)
        section = presentation["section"]
        counts[section] = counts.get(section, 0) + 1

    structural = [row for row in presented if row["presentation"]["condition_status"] == "not-established-by-this-indicator"]
    benchmark_count = counts.get("international-benchmark", 0)
    official_count = counts.get("official", 0)
    if official_count and benchmark_count:
        evidence_status = "Official and harmonized evidence · mixed reference periods"
    elif official_count:
        evidence_status = "Official evidence · mixed reference periods"
    elif benchmark_count:
        evidence_status = "Harmonized comparison evidence · preferred national sources may be absent"
    else:
        evidence_status = "Published country evidence · source roles remain explicit"

    if code == "PSE":
        authority_summary = "PCBS is preferred for exact supported Palestine statistics when a compatible candidate is present; harmonized international series remain comparison/fallback evidence."
        operational_boundary = "Operational humanitarian and essential-service reporting is kept separate from structural national statistics. A structural access percentage cannot establish present electricity, water, hospital, school, food, fuel, or aid-access conditions."
    else:
        authority_summary = "National or sector authorities take precedence when an exact compatible source is connected and present; harmonized international series remain clearly labeled comparison evidence."
        operational_boundary = "Operational conditions remain separate from annual or structural national statistics. A structural access percentage cannot establish current service continuity, facility functionality, or humanitarian access."

    return {
        "schema": SCHEMA,
        "contract": CONTRACT,
        "version": VERSION,
        "evidence_status": evidence_status,
        "authority_summary": authority_summary,
        "operational_boundary": operational_boundary,
        "layers": [
            {"id": "operational", "label": "CONDITIONS NOW", "description": "Recent operational and humanitarian reporting. Never inferred from structural statistics."},
            {"id": "official", "label": "OFFICIAL EVIDENCE", "description": "National statistical and sector-authority evidence when exact compatible records are present."},
            {"id": "international-benchmark", "label": "INTERNATIONAL BENCHMARK", "description": "Harmonized series retained for comparability and fallback, not treated as operational truth."},
            {"id": "reconciliation", "label": "EVIDENCE RECONCILIATION", "description": "Source, period, method, and geographic disagreement remains visible; no automatic blending."},
        ],
        "counts": counts,
        "structural_condition_boundary_count": len(structural),
        "missing_indicator_count": len(missing_indicators or []),
        "indicators": presented,
        "generated_at": _now(),
    }


def readiness() -> dict[str, Any]:
    electricity = present_indicator({
        "id": "EG.ELC.ACCS.ZS",
        "label": "Access to electricity",
        "canonical_observation": {
            "presentation_label": "HARMONIZED BENCHMARK",
            "transport_state": "live",
            "source": {"source_id": "world_bank", "authority_class": "international-harmonized"},
            "semantics": {
                "concept_id": "electricity_structural_access",
                "current_condition_claim_allowed": False,
                "display_note": "Structural electricity access does not represent current electricity availability, outage status, hours of service, grid reliability, or generator dependence.",
            },
        },
    })
    official = present_indicator({
        "id": "SP.POP.TOTL",
        "canonical_observation": {
            "presentation_label": "CURRENT OFFICIAL",
            "source": {"source_id": "pcbs-pxweb-sdgs", "authority_class": "national-statistical-authority"},
            "semantics": {"concept_id": "population_total", "current_condition_claim_allowed": False},
        },
    })
    profile = build_country_presentation({"code": "PSE", "name": "Palestine"}, [
        {"id": "EG.ELC.ACCS.ZS", "canonical_observation": {
            "presentation_label": "HARMONIZED BENCHMARK", "transport_state": "live",
            "source": {"source_id": "world_bank", "authority_class": "international-harmonized"},
            "semantics": {"concept_id": "electricity_structural_access", "current_condition_claim_allowed": False},
        }},
    ])
    checks = {
        "world_bank_electricity_is_benchmark": electricity["role_label"] == "HARMONIZED BENCHMARK",
        "structural_electricity_not_conditions_now": electricity["current_condition_claim_allowed"] is False and electricity["condition_status"] == "not-established-by-this-indicator",
        "structural_electricity_warning_visible": "does not represent current electricity" in electricity["interpretation_note"].lower(),
        "national_authority_gets_official_role": official["role_label"] in {"CURRENT OFFICIAL", "PRIMARY OFFICIAL"},
        "transport_live_does_not_upgrade_evidence": electricity["transport_state"] == "live" and electricity["role_label"] == "HARMONIZED BENCHMARK",
        "palestine_operational_boundary_explicit": "structural access percentage cannot establish present electricity" in profile["operational_boundary"].lower(),
        "automatic_blending_not_presented": any(layer["id"] == "reconciliation" and "no automatic blending" in layer["description"].lower() for layer in profile["layers"]),
    }
    return {
        "ok": all(checks.values()),
        "version": VERSION,
        "contract": CONTRACT,
        "schema": SCHEMA,
        "checks": checks,
        "network_calls_performed": False,
        "upstream_health_release_blocking": False,
        "generated_at": _now(),
    }
