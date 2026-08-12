from __future__ import annotations

"""Evidence presentation semantics for Site Intelligence v4.35.21.

Transport freshness (a successful HTTP request, a cache hit, or a stale fallback) is
not evidence freshness and is never allowed to imply that an annual statistic is a
current operational condition. This module is network-free.
"""

from datetime import datetime, timezone
from typing import Any, Mapping

from .evidence_intelligence_v4357 import METRIC_CONCEPTS, concept_for_indicator, freshness_assessment
from .version import APP_VERSION

VERSION = APP_VERSION
CONTRACT = "evidence-class-transport-separation-source-authority-v43519"

EVIDENCE_CLASSES = {
    "live-operational": "LIVE / OPERATIONAL",
    "current-official": "CURRENT OFFICIAL",
    "annual-statistic": "ANNUAL STATISTIC",
    "modeled-estimate": "MODELED ESTIMATE",
    "harmonized-benchmark": "HARMONIZED BENCHMARK",
    "historical": "HISTORICAL",
    "unavailable": "UNAVAILABLE",
}

# These are precedence/interpretation rules, not claims that every named source has
# a production connector. ``connected`` is deliberately explicit where known.
PSE_SOURCE_PRIORITY: dict[str, list[dict[str, Any]]] = {
    "population_total": [
        {"source_id": "pcbs-pxweb-sdgs", "publisher": "Palestinian Central Bureau of Statistics", "role": "primary", "connected": True},
        {"source_id": "un-population-division", "publisher": "UN Population Division", "role": "comparison", "connected": False},
        {"source_id": "world_bank", "publisher": "World Bank Open Data", "role": "harmonized-fallback", "connected": True},
    ],
    "life_expectancy_at_birth": [
        {"source_id": "pcbs-pxweb-sdgs", "publisher": "Palestinian Central Bureau of Statistics", "role": "primary", "connected": True},
        {"source_id": "palestinian-ministry-health", "publisher": "Palestinian Ministry of Health", "role": "sector-primary", "connected": False},
        {"source_id": "who", "publisher": "World Health Organization", "role": "sector-comparison", "connected": False},
        {"source_id": "world_bank", "publisher": "World Bank Open Data", "role": "harmonized-fallback", "connected": True},
    ],
    "gdp_per_capita_current_usd": [
        {"source_id": "pcbs-pxweb-sdgs", "publisher": "Palestinian Central Bureau of Statistics", "role": "primary", "connected": True},
        {"source_id": "palestine-monetary-authority", "publisher": "Palestine Monetary Authority", "role": "economic-complement", "connected": False},
        {"source_id": "world_bank", "publisher": "World Bank Open Data", "role": "harmonized-fallback", "connected": True},
    ],
    "electricity_structural_access": [
        {"source_id": "pcbs-pxweb-sdgs", "publisher": "Palestinian Central Bureau of Statistics", "role": "primary", "connected": True},
        {"source_id": "world_bank", "publisher": "World Bank Open Data", "role": "harmonized-fallback", "connected": True},
    ],
    "electricity_operational_availability": [
        {"source_id": "gedco", "publisher": "Gaza Electricity Distribution Company", "role": "operator-primary", "connected": False},
        {"source_id": "palestinian-energy-authority", "publisher": "Palestinian energy authority", "role": "sector-primary", "connected": False},
        {"source_id": "ocha-opt", "publisher": "UN OCHA occupied Palestinian territory", "role": "operational-context", "connected": False},
    ],
    "basic_drinking_water_access": [
        {"source_id": "pcbs-pxweb-sdgs", "publisher": "Palestinian Central Bureau of Statistics", "role": "primary", "connected": True},
        {"source_id": "who-unicef-jmp", "publisher": "WHO/UNICEF Joint Monitoring Programme", "role": "custodian-comparison", "connected": False},
        {"source_id": "world_bank", "publisher": "World Bank Open Data", "role": "harmonized-fallback", "connected": True},
    ],
    "secondary_enrollment_gross": [
        {"source_id": "pcbs-pxweb-sdgs", "publisher": "Palestinian Central Bureau of Statistics", "role": "primary", "connected": True},
        {"source_id": "palestinian-ministry-education", "publisher": "Palestinian Ministry of Education", "role": "sector-primary", "connected": False},
        {"source_id": "unesco-uis", "publisher": "UNESCO Institute for Statistics", "role": "custodian-comparison", "connected": False},
        {"source_id": "world_bank", "publisher": "World Bank Open Data", "role": "harmonized-fallback", "connected": True},
    ],
}

STRUCTURAL_OPERATIONAL_WARNINGS = {
    "electricity_structural_access": "Structural electricity access does not represent current electricity availability, outage status, hours of service, grid reliability, or generator dependence.",
    "basic_drinking_water_access": "Structural drinking-water access does not represent current water availability, pressure, quality, continuity, or household service conditions.",
}


def _source_id(source: str, explicit: str = "") -> str:
    text = str(source or "").lower()
    if "world bank" in text:
        return "world_bank"
    value = str(explicit or "").strip().lower().replace("-", "_")
    return value or "unknown"


def _authority_class(source: str, explicit: str = "") -> str:
    if explicit:
        return explicit
    text = str(source or "").lower()
    if "world bank" in text:
        return "international-harmonized"
    if "statistics" in text or "bureau" in text:
        return "national-statistical-authority"
    if "ministry" in text or "authority" in text or "distribution company" in text:
        return "official-sector-authority"
    if "who" in text or "un " in text or "united nations" in text:
        return "intergovernmental-custodian"
    return "unknown"


def source_priority(jurisdiction: str, concept_id: str) -> list[dict[str, Any]]:
    if str(jurisdiction or "").upper() != "PSE":
        return []
    return [dict(row) for row in PSE_SOURCE_PRIORITY.get(concept_id, [])]


def classify_evidence(*, jurisdiction: str, indicator_id: str, source: str, source_id: str = "", authority_class: str = "", observation_year: Any = None, data_state: str = "unavailable", value_available: bool = True, status: str = "final", now: Any = None) -> dict[str, Any]:
    concept_id = concept_for_indicator(indicator_id)
    metric = METRIC_CONCEPTS.get(concept_id or "", {})
    cadence = str(metric.get("cadence") or "unknown")
    freshness = freshness_assessment(observed_at=observation_year, cadence=cadence, now=now)
    sid = _source_id(source, source_id)
    authority = _authority_class(source, authority_class)
    transport_state = str(data_state or "unavailable")
    status_key = str(status or "").lower()

    if not value_available:
        evidence_class = "unavailable"
    elif status_key in {"estimated", "modeled", "modelled"}:
        evidence_class = "modeled-estimate"
    elif authority == "international-harmonized" or sid == "world_bank":
        evidence_class = "harmonized-benchmark"
    elif metric.get("kind") == "operational_condition" and freshness["status"] in {"current", "recent"}:
        evidence_class = "live-operational"
    elif freshness["status"] in {"stale"}:
        evidence_class = "historical"
    elif authority in {"national-statistical-authority", "official-sector-authority"} and freshness["status"] in {"current", "recent"}:
        evidence_class = "current-official"
    elif cadence in {"annual", "periodic_official"}:
        evidence_class = "annual-statistic"
    else:
        evidence_class = "historical" if freshness["status"] in {"older", "dated"} else "annual-statistic"

    operational = metric.get("kind") == "operational_condition"
    warning = STRUCTURAL_OPERATIONAL_WARNINGS.get(concept_id or "", "")
    return {
        "version": VERSION,
        "contract": CONTRACT,
        "concept_id": concept_id,
        "evidence_class": evidence_class,
        "evidence_label": EVIDENCE_CLASSES[evidence_class],
        "transport_state": transport_state,
        "transport_is_observation_claim": False,
        "operational_scope": "operational" if operational else "structural/statistical",
        "current_condition_claim_allowed": evidence_class == "live-operational",
        "freshness": freshness,
        "authority_class": authority,
        "source_id": sid,
        "source_priority": source_priority(jurisdiction, concept_id or ""),
        "warning": warning,
        "display_note": warning or "Retrieval state is reported separately from the evidence class and observation period.",
    }


def readiness() -> dict[str, Any]:
    wb = classify_evidence(
        jurisdiction="PSE", indicator_id="EG.ELC.ACCS.ZS", source="World Bank Open Data",
        observation_year=2024, data_state="live", value_available=True, now="2026-08-12",
    )
    operational_misuse = classify_evidence(
        jurisdiction="PSE", indicator_id="EG.ELC.ACCS.ZS", source="World Bank Open Data",
        observation_year=2024, data_state="cached", value_available=True, now="2026-08-12",
    )
    priorities = source_priority("PSE", "electricity_structural_access")
    checks = {
        "transport_state_separate_from_evidence_class": wb["transport_state"] == "live" and wb["evidence_class"] != "live-operational",
        "world_bank_annual_is_harmonized_benchmark": wb["evidence_class"] == "harmonized-benchmark",
        "structural_electricity_never_current_supply": wb["current_condition_claim_allowed"] is False and "does not represent current electricity availability" in wb["warning"],
        "cache_state_cannot_upgrade_semantics": operational_misuse["evidence_class"] == "harmonized-benchmark",
        "palestine_pcbs_precedence_present": bool(priorities) and priorities[0]["source_id"] == "pcbs-pxweb-sdgs",
        "world_bank_retained_as_comparison_fallback": any(row["source_id"] == "world_bank" for row in priorities),
        "network_free": True,
    }
    return {
        "ok": all(checks.values()), "version": VERSION, "contract": CONTRACT,
        "checks": checks, "evidence_classes": dict(EVIDENCE_CLASSES),
        "network_calls_performed": False, "generated_at": datetime.now(timezone.utc).isoformat(),
    }
