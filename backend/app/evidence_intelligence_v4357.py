from __future__ import annotations

"""Source precedence, metric semantics and freshness intelligence for Site Intelligence v4.35.11.

This layer does not fetch upstream data. It evaluates already disclosed candidate evidence and
keeps semantic compatibility ahead of authority or freshness. A fresher record for the wrong
concept can never replace an older record for the requested concept.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Iterable, Mapping
import json
import math

from .version import APP_VERSION

VERSION = APP_VERSION
CONTRACT = "source-precedence-metric-semantics-freshness"
SCHEMA = "sc-site-intelligence-evidence-selection/1.0"

AUTHORITY_RANK = {
    "national-statistical-authority": 100,
    "official-sector-authority": 95,
    "intergovernmental-custodian": 90,
    "international-harmonized": 80,
    "scientific-observatory": 80,
    "regulatory-authority": 80,
    "research-consortium": 65,
    "aggregator": 50,
    "unknown": 0,
}

STATUS_RANK = {"final": 30, "approved": 25, "revised": 20, "provisional": 10, "estimated": 5, "unknown": 0}

FRESHNESS_WINDOWS_DAYS = {
    "real_time": (1, 3, 7),
    "near_real_time": (2, 7, 30),
    "daily": (3, 14, 45),
    "weekly": (14, 45, 120),
    "monthly": (45, 120, 240),
    "quarterly": (150, 300, 540),
    "annual": (550, 900, 1460),
    "periodic_official": (730, 1460, 2555),
    "historical": (3650, 7300, 15000),
    "unknown": (0, 0, 0),
}

METRIC_CONCEPTS: dict[str, dict[str, Any]] = {
    "population_total": {
        "label": "Total population",
        "kind": "structural_stock",
        "canonical_units": ["people", "persons"],
        "cadence": "annual",
        "compatible_indicators": ["SP.POP.TOTL"],
        "claim": "Estimated or enumerated resident population for the disclosed reference period and geographic definition.",
        "forbidden_substitutions": ["population currently present", "real-time population movement"],
    },
    "life_expectancy_at_birth": {
        "label": "Life expectancy at birth",
        "kind": "demographic_health_statistic",
        "canonical_units": ["years"],
        "cadence": "annual",
        "compatible_indicators": ["SP.DYN.LE00.IN"],
        "claim": "Period life expectancy at birth under the source methodology.",
        "forbidden_substitutions": ["individual prognosis", "current hospital outcomes"],
    },
    "gdp_per_capita_current_usd": {
        "label": "GDP per capita, current US$",
        "kind": "economic_statistic",
        "canonical_units": ["current US$", "USD/person"],
        "cadence": "annual",
        "compatible_indicators": ["NY.GDP.PCAP.CD"],
        "claim": "Nominal GDP per person for the source reference period and accounting framework.",
        "forbidden_substitutions": ["household income", "wealth per person", "current purchasing power"],
    },
    "electricity_structural_access": {
        "label": "Population with access to electricity",
        "kind": "structural_access_statistic",
        "canonical_units": ["% of population", "percent"],
        "cadence": "annual",
        "compatible_indicators": ["EG.ELC.ACCS.ZS", "SDG 7.1.1"],
        "claim": "Share of the population classified as having electricity access under the source methodology for the stated reference period.",
        "forbidden_substitutions": [
            "current electricity availability",
            "hours of electricity supplied",
            "grid reliability",
            "outage status",
            "generator dependence",
            "current service continuity",
        ],
    },
    "electricity_operational_availability": {
        "label": "Current electricity supply availability",
        "kind": "operational_condition",
        "canonical_units": ["hours/day", "MW", "MWh", "operational status"],
        "cadence": "near_real_time",
        "compatible_indicators": [],
        "claim": "Current or recent operational evidence about electricity supply, outages, generation, feeder availability or service continuity.",
        "forbidden_substitutions": ["electricity access percentage", "historical electrification rate"],
    },
    "basic_drinking_water_access": {
        "label": "Population using at least basic drinking-water services",
        "kind": "structural_access_statistic",
        "canonical_units": ["% of population", "percent"],
        "cadence": "annual",
        "compatible_indicators": ["SH.H2O.BASW.ZS"],
        "claim": "Share of population using at least basic drinking-water services under the source definition.",
        "forbidden_substitutions": ["current water pressure", "current potable water availability", "water quality at a specific tap"],
    },
    "secondary_enrollment_gross": {
        "label": "Secondary school enrollment, gross",
        "kind": "education_statistic",
        "canonical_units": ["% gross", "percent gross"],
        "cadence": "annual",
        "compatible_indicators": ["SE.SEC.ENRR"],
        "claim": "Gross secondary enrollment ratio for the disclosed academic/reference period.",
        "forbidden_substitutions": ["attendance rate", "completion rate", "school quality"],
    },
    "co2_emissions_per_capita": {
        "label": "CO₂ emissions per capita",
        "kind": "environmental_inventory_statistic",
        "canonical_units": ["metric tons", "t/person"],
        "cadence": "annual",
        "compatible_indicators": ["EN.ATM.CO2E.PC"],
        "claim": "Territorial CO₂ emissions allocated per person under the source inventory methodology.",
        "forbidden_substitutions": ["consumption footprint", "current air quality", "individual emissions"],
    },
    "gini_income_inequality": {
        "label": "Gini index",
        "kind": "distribution_statistic",
        "canonical_units": ["index"],
        "cadence": "periodic_official",
        "compatible_indicators": ["SI.POV.GINI"],
        "claim": "Income or consumption inequality summarized using the source survey and Gini methodology.",
        "forbidden_substitutions": ["wealth inequality", "poverty rate", "current household hardship"],
    },
}

INDICATOR_TO_CONCEPT = {
    indicator: concept_id
    for concept_id, spec in METRIC_CONCEPTS.items()
    for indicator in spec.get("compatible_indicators", [])
}

PRECEDENCE_RULES: list[dict[str, Any]] = [
    {
        "jurisdiction": "PSE",
        "concept_id": "electricity_structural_access",
        "preferred_sources": ["pcbs-pxweb-sdgs", "world_bank"],
        "rationale": "Prefer the Palestinian national statistical authority for a Palestine-specific structural access statistic when the same concept is available; retain World Bank as a harmonized comparison/fallback source.",
    },
    {
        "jurisdiction": "PSE",
        "concept_id": "electricity_operational_availability",
        "preferred_sources": ["gedco", "palestinian-energy-authority", "ocha-opt", "reliefweb"],
        "rationale": "Operational electricity conditions require grid/operator, energy-authority or humanitarian operational evidence; structural access statistics are semantically ineligible.",
    },
    {
        "jurisdiction": "CAN",
        "concept_id": "*",
        "preferred_sources": ["statistics-canada-wds", "world_bank"],
        "rationale": "For Canadian official statistics, prefer Statistics Canada when the metric semantics are an exact match; harmonized international data remains useful for comparison.",
    },
    {
        "jurisdiction": "GBR",
        "concept_id": "*",
        "preferred_sources": ["uk-ons-api", "world_bank"],
        "rationale": "For UK official statistics, prefer ONS when the metric semantics are an exact match.",
    },
    {
        "jurisdiction": "AUS",
        "concept_id": "*",
        "preferred_sources": ["australian-bureau-statistics-sdmx", "world_bank"],
        "rationale": "For Australian official statistics, prefer ABS when the metric semantics are an exact match.",
    },
    {
        "jurisdiction": "USA",
        "concept_id": "labor_statistics",
        "preferred_sources": ["us-bls-public-data-api"],
        "rationale": "BLS is the first-party federal statistical authority for U.S. labor and price series within its published scope.",
    },
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str).encode("utf-8")
    return sha256(raw).hexdigest()


def _parse_date(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    if len(text) == 4 and text.isdigit():
        text = f"{text}-12-31T00:00:00+00:00"
    elif len(text) == 10 and text[4] == "-":
        text += "T00:00:00+00:00"
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def metric_catalog() -> dict[str, Any]:
    rows = []
    for concept_id, spec in METRIC_CONCEPTS.items():
        rows.append({"concept_id": concept_id, **spec})
    return {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "schema": SCHEMA,
        "concept_count": len(rows),
        "concepts": rows,
        "indicator_mapping": dict(INDICATOR_TO_CONCEPT),
        "generated_at": _now(),
    }


def precedence_catalog(*, jurisdiction: str = "", concept_id: str = "") -> dict[str, Any]:
    j = str(jurisdiction or "").strip().upper()
    c = str(concept_id or "").strip()
    rules = [dict(row) for row in PRECEDENCE_RULES]
    if j:
        rules = [row for row in rules if row["jurisdiction"] == j]
    if c:
        rules = [row for row in rules if row["concept_id"] in {c, "*"}]
    return {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "jurisdiction": j or None,
        "concept_id": c or None,
        "rule_count": len(rules),
        "rules": rules,
        "principles": [
            "Semantic compatibility is mandatory before source authority, freshness or convenience is considered.",
            "A national statistical authority may outrank an international harmonized source for country-specific official statistics only when the metric definition is compatible.",
            "International harmonized sources remain valuable for cross-country comparability and fallback evidence.",
            "Operational conditions and structural access statistics are separate evidence concepts.",
            "Conflicting exact-concept observations are disclosed rather than averaged or silently overwritten.",
        ],
        "generated_at": _now(),
    }


def freshness_assessment(*, observed_at: Any, cadence: str = "unknown", now: Any = None) -> dict[str, Any]:
    cadence_key = str(cadence or "unknown").strip().lower()
    if cadence_key not in FRESHNESS_WINDOWS_DAYS:
        cadence_key = "unknown"
    observed = _parse_date(observed_at)
    reference = _parse_date(now) if now is not None else datetime.now(timezone.utc)
    if observed is None:
        return {
            "status": "unknown",
            "cadence": cadence_key,
            "observed_at": None,
            "reference_at": reference.isoformat(),
            "age_days": None,
            "thresholds_days": list(FRESHNESS_WINDOWS_DAYS[cadence_key]),
            "reason": "Observation date is missing or invalid; freshness is not inferred.",
        }
    age_days = max(0, int((reference - observed).total_seconds() // 86400))
    current, recent, stale = FRESHNESS_WINDOWS_DAYS[cadence_key]
    if cadence_key == "unknown":
        status = "dated"
    elif age_days <= current:
        status = "current"
    elif age_days <= recent:
        status = "recent"
    elif age_days <= stale:
        status = "older"
    else:
        status = "stale"
    return {
        "status": status,
        "cadence": cadence_key,
        "observed_at": observed.isoformat(),
        "reference_at": reference.isoformat(),
        "age_days": age_days,
        "thresholds_days": [current, recent, stale],
        "reason": "Freshness is evaluated against the expected publication cadence; it does not imply upstream accuracy.",
    }


def freshness_policy() -> dict[str, Any]:
    return {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "windows_days": {key: list(value) for key, value in FRESHNESS_WINDOWS_DAYS.items()},
        "states": ["current", "recent", "older", "stale", "dated", "unknown"],
        "principles": [
            "Freshness is relative to the expected source cadence, not to a universal number of days.",
            "An annual statistic can be current evidence while being many months old.",
            "A near-real-time operational source can be stale after days.",
            "Freshness never upgrades a semantically incompatible candidate.",
        ],
        "generated_at": _now(),
    }


def concept_for_indicator(indicator_id: str) -> str | None:
    return INDICATOR_TO_CONCEPT.get(str(indicator_id or "").strip())


def _precedence_index(jurisdiction: str, concept_id: str, source_id: str) -> int:
    source = str(source_id or "").strip()
    matches = [
        row for row in PRECEDENCE_RULES
        if row["jurisdiction"] == jurisdiction and row["concept_id"] in {concept_id, "*"}
    ]
    for rule in matches:
        if source in rule["preferred_sources"]:
            return rule["preferred_sources"].index(source)
    return 999


def _normalize_candidate(raw: Mapping[str, Any], requested_concept: str, jurisdiction: str, now: Any = None) -> dict[str, Any]:
    source_id = str(raw.get("source_id") or raw.get("feed_id") or "unknown").strip()
    candidate_concept = str(raw.get("concept_id") or concept_for_indicator(str(raw.get("indicator_id") or "")) or "unknown").strip()
    authority_class = str(raw.get("authority_class") or "unknown").strip().lower()
    cadence = str(raw.get("cadence") or METRIC_CONCEPTS.get(candidate_concept, {}).get("cadence") or "unknown").strip().lower()
    freshness = freshness_assessment(observed_at=raw.get("observed_at") or raw.get("observation_at") or raw.get("observation_year"), cadence=cadence, now=now)
    status = str(raw.get("status") or raw.get("observation_status") or "unknown").strip().lower()
    exact_semantics = candidate_concept == requested_concept
    unit = raw.get("unit")
    canonical_units = METRIC_CONCEPTS.get(requested_concept, {}).get("canonical_units", [])
    unit_compatible = unit is None or not canonical_units or str(unit).strip() in canonical_units
    value = raw.get("value")
    value_available = value is not None
    precedence_index = _precedence_index(jurisdiction, requested_concept, source_id)
    freshness_rank = {"current": 30, "recent": 20, "older": 10, "dated": 5, "stale": 0, "unknown": -5}.get(freshness["status"], -5)
    score = (
        (10000 if exact_semantics else -10000)
        + (1000 if unit_compatible else -1000)
        + AUTHORITY_RANK.get(authority_class, 0) * 10
        + (500 - min(precedence_index, 500))
        + freshness_rank
        + STATUS_RANK.get(status, 0)
        + (10 if value_available else -500)
    )
    return {
        "source_id": source_id,
        "publisher": raw.get("publisher") or raw.get("organization"),
        "concept_id": candidate_concept,
        "indicator_id": raw.get("indicator_id"),
        "authority_class": authority_class,
        "authority_rank": AUTHORITY_RANK.get(authority_class, 0),
        "precedence_index": precedence_index,
        "exact_semantics": exact_semantics,
        "unit": unit,
        "unit_compatible": unit_compatible,
        "value": value,
        "value_available": value_available,
        "status": status,
        "freshness": freshness,
        "observed_at": freshness["observed_at"],
        "score": score,
        "raw": dict(raw),
    }


def _numeric_conflict(a: Any, b: Any) -> bool:
    if not isinstance(a, (int, float)) or isinstance(a, bool) or not isinstance(b, (int, float)) or isinstance(b, bool):
        return a != b
    if not math.isfinite(float(a)) or not math.isfinite(float(b)):
        return a != b
    tolerance = max(1e-9, 0.005 * max(abs(float(a)), abs(float(b)), 1.0))
    return abs(float(a) - float(b)) > tolerance


def select_evidence(*, concept_id: str, jurisdiction: str, candidates: Iterable[Mapping[str, Any]], now: Any = None) -> dict[str, Any]:
    concept = str(concept_id or "").strip()
    if concept not in METRIC_CONCEPTS:
        raise ValueError("concept_id is not registered in the metric semantics catalog")
    geo = str(jurisdiction or "").strip().upper()
    if not geo or len(geo) > 12:
        raise ValueError("jurisdiction is required")
    raw_candidates = list(candidates)
    if not raw_candidates or len(raw_candidates) > 50:
        raise ValueError("candidates must contain between 1 and 50 evidence records")
    normalized = [_normalize_candidate(row, concept, geo, now=now) for row in raw_candidates]
    eligible = [row for row in normalized if row["exact_semantics"] and row["unit_compatible"] and row["value_available"]]
    eligible.sort(key=lambda row: row["score"], reverse=True)
    selected = eligible[0] if eligible else None
    exact_available = [row for row in normalized if row["exact_semantics"] and row["value_available"]]
    conflicts = []
    for idx, left in enumerate(exact_available):
        for right in exact_available[idx + 1:]:
            if left["unit"] == right["unit"] and left["observed_at"] == right["observed_at"] and _numeric_conflict(left["value"], right["value"]):
                conflicts.append({
                    "left_source_id": left["source_id"], "right_source_id": right["source_id"],
                    "left_value": left["value"], "right_value": right["value"],
                    "unit": left["unit"], "observed_at": left["observed_at"],
                    "resolution": "disclose-both-no-automatic-blending",
                })
    result = {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "schema": SCHEMA,
        "requested": {"concept_id": concept, "jurisdiction": geo},
        "concept": {"concept_id": concept, **METRIC_CONCEPTS[concept]},
        "candidate_count": len(normalized),
        "eligible_count": len(eligible),
        "selection_state": "selected" if selected else "no-semantically-eligible-evidence",
        "selected": selected,
        "candidates": normalized,
        "conflicts": conflicts,
        "boundaries": [
            "Semantic compatibility is evaluated before authority or freshness.",
            "A missing preferred source does not permit substitution with a different concept.",
            "Conflicting exact-concept observations are retained for review rather than averaged.",
            "This selection contract ranks disclosed evidence; it does not independently validate the upstream source.",
        ],
        "generated_at": _now(),
    }
    result["selection_sha256"] = _digest({"requested": result["requested"], "selected": selected, "conflicts": conflicts})
    return result


def indicator_semantics(indicator_id: str, *, jurisdiction: str = "") -> dict[str, Any]:
    concept_id = concept_for_indicator(indicator_id)
    if concept_id is None:
        raise KeyError(indicator_id)
    spec = METRIC_CONCEPTS[concept_id]
    geo = str(jurisdiction or "").strip().upper()
    precedence = precedence_catalog(jurisdiction=geo, concept_id=concept_id)["rules"] if geo else []
    return {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "indicator_id": indicator_id,
        "concept_id": concept_id,
        "metric": {"concept_id": concept_id, **spec},
        "jurisdiction": geo or None,
        "precedence_rules": precedence,
        "generated_at": _now(),
    }


def overview() -> dict[str, Any]:
    return {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "schema": SCHEMA,
        "metric_concept_count": len(METRIC_CONCEPTS),
        "precedence_rule_count": len(PRECEDENCE_RULES),
        "freshness_cadence_count": len(FRESHNESS_WINDOWS_DAYS),
        "authority_class_count": len(AUTHORITY_RANK),
        "capabilities": [
            "metric concept registry",
            "indicator-to-concept mapping",
            "jurisdiction-aware source precedence",
            "cadence-aware freshness assessment",
            "semantic-incompatibility blocking",
            "conflict disclosure without automatic blending",
            "selection fingerprinting",
        ],
        "critical_boundary": "Electricity access is a structural access statistic and cannot answer current electricity availability, grid reliability, outage status or service-continuity questions.",
        "generated_at": _now(),
    }


def readiness() -> dict[str, Any]:
    access = METRIC_CONCEPTS["electricity_structural_access"]
    operational = METRIC_CONCEPTS["electricity_operational_availability"]
    checks = {
        "metric_semantics_registered": len(METRIC_CONCEPTS) >= 9,
        "electricity_access_and_operational_supply_are_distinct": access["kind"] != operational["kind"],
        "electricity_access_forbids_current_supply_substitution": "current electricity availability" in access["forbidden_substitutions"],
        "palestine_structural_access_precedence_present": any(row["jurisdiction"] == "PSE" and row["concept_id"] == "electricity_structural_access" and row["preferred_sources"][0] == "pcbs-pxweb-sdgs" for row in PRECEDENCE_RULES),
        "palestine_operational_supply_rule_excludes_world_bank": any(row["jurisdiction"] == "PSE" and row["concept_id"] == "electricity_operational_availability" and "world_bank" not in row["preferred_sources"] for row in PRECEDENCE_RULES),
        "freshness_is_cadence_aware": FRESHNESS_WINDOWS_DAYS["annual"] != FRESHNESS_WINDOWS_DAYS["near_real_time"],
        "selection_does_not_require_network": True,
        "source_health_remains_non_blocking_for_release": True,
    }
    return {"ok": all(checks.values()), "version": VERSION, "contract": CONTRACT, "network_calls_performed": False, "checks": checks, "generated_at": _now()}
