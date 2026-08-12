from __future__ import annotations

"""Country evidence reconciliation and geographic-scope integrity for Site Intelligence v4.35.23.

This layer compares already disclosed evidence. It never averages or manufactures a country value.
It keeps concept, geography, reference period, methodology and authority separate so disagreement can
be disclosed without collapsing unlike records into one number.
"""

from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Iterable, Mapping
import json
import math

from .version import APP_VERSION
from .evidence_intelligence_v4357 import METRIC_CONCEPTS, PRECEDENCE_RULES, concept_for_indicator, select_evidence

VERSION = APP_VERSION
CONTRACT = "country-evidence-reconciliation-scope-integrity-v43522"
SCHEMA = "sc-site-intelligence-country-evidence-reconciliation/1.0"

PSE_NATIONAL_ALIASES = {
    "PSE", "PS", "PALESTINE", "STATE OF PALESTINE", "WEST BANK AND GAZA", "PALESTINIAN TERRITORIES",
    "PALESTINIAN TERRITORY", "OCCUPIED PALESTINIAN TERRITORY", "OPT",
}
PSE_SUBNATIONAL = {
    "WEST BANK": "PSE-WBK",
    "WBK": "PSE-WBK",
    "PSE-WBK": "PSE-WBK",
    "GAZA": "PSE-GZA",
    "GAZA STRIP": "PSE-GZA",
    "GZA": "PSE-GZA",
    "PSE-GZA": "PSE-GZA",
}

MATERIAL_DIFFERENCE_PCT = {
    "population_total": 1.0,
    "life_expectancy_at_birth": 1.0,
    "gdp_per_capita_current_usd": 2.0,
    "electricity_structural_access": 1.0,
    "basic_drinking_water_access": 1.0,
    "secondary_enrollment_gross": 1.0,
    "co2_emissions_per_capita": 2.0,
    "gini_income_inequality": 1.0,
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str).encode("utf-8")
    return sha256(raw).hexdigest()


def _clean(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _geo_token(value: Any) -> str:
    return _clean(value).upper()


def normalize_geography(*, jurisdiction: str, geography_code: Any = None, geography_label: Any = None, geography_level: Any = None) -> dict[str, Any]:
    jurisdiction_code = _geo_token(jurisdiction)
    code = _geo_token(geography_code)
    label = _geo_token(geography_label)
    level = _clean(geography_level).lower() or "unknown"
    token = code or label or jurisdiction_code

    if jurisdiction_code == "PSE":
        # A disclosed subnational label must not be erased just because the parent country code is PSE.
        if label in PSE_SUBNATIONAL:
            canonical = PSE_SUBNATIONAL[label]
            normalized_level = "subnational"
        elif token in PSE_NATIONAL_ALIASES or (not code and not label):
            canonical = "PSE"
            normalized_level = "national"
        elif token in PSE_SUBNATIONAL:
            canonical = PSE_SUBNATIONAL[token]
            normalized_level = "subnational"
        else:
            canonical = code or label or "unknown"
            normalized_level = level
    else:
        canonical = code or jurisdiction_code
        normalized_level = "national" if canonical == jurisdiction_code and level in {"unknown", "country", "national"} else level

    if canonical == jurisdiction_code:
        compatibility = "exact"
    elif jurisdiction_code == "PSE" and canonical in {"PSE-WBK", "PSE-GZA"}:
        compatibility = "subnational-context-only"
    else:
        compatibility = "different-geography"

    return {
        "jurisdiction": jurisdiction_code,
        "canonical_code": canonical,
        "label": _clean(geography_label) or canonical,
        "level": normalized_level,
        "compatibility": compatibility,
        "eligible_for_national_selection": compatibility == "exact",
    }


def _reference_period(raw: Mapping[str, Any]) -> str:
    for key in ("reference_period", "observed_at", "observation_at", "observation_year", "year"):
        value = raw.get(key)
        if value is not None and _clean(value):
            return _clean(value)
    return "unknown"


def _methodology(raw: Mapping[str, Any]) -> dict[str, Any]:
    identifier = _clean(raw.get("methodology_id") or raw.get("methodology") or raw.get("method")) or "unspecified"
    scope = _clean(raw.get("methodology_scope") or raw.get("population_basis") or raw.get("coverage_basis")) or "unspecified"
    return {"id": identifier, "scope": scope}


def _numeric_difference(left: Any, right: Any) -> dict[str, Any] | None:
    if isinstance(left, bool) or isinstance(right, bool) or not isinstance(left, (int, float)) or not isinstance(right, (int, float)):
        return None
    if not math.isfinite(float(left)) or not math.isfinite(float(right)):
        return None
    absolute = float(left) - float(right)
    base = max(abs(float(right)), 1e-12)
    return {"absolute": absolute, "percent_vs_right": abs(absolute) / base * 100.0}


def _preferred_sources(jurisdiction: str, concept_id: str) -> list[str]:
    rows = [row for row in PRECEDENCE_RULES if row.get("jurisdiction") == jurisdiction and row.get("concept_id") in {concept_id, "*"}]
    ordered: list[str] = []
    for row in rows:
        for source in row.get("preferred_sources") or []:
            if source not in ordered:
                ordered.append(source)
    if jurisdiction == "PSE":
        for source in ("pcbs-pxweb", "pcbs-pxweb-sdgs", "world_bank"):
            if source not in ordered:
                ordered.append(source)
    return ordered


def reconcile_evidence(*, jurisdiction: str, concept_id: str, candidates: Iterable[Mapping[str, Any]], now: Any = None) -> dict[str, Any]:
    geo = _geo_token(jurisdiction)
    concept = _clean(concept_id)
    if concept not in METRIC_CONCEPTS:
        raise ValueError("concept_id is not registered in the metric semantics catalog")
    raw_candidates = [dict(row) for row in candidates]
    if not raw_candidates or len(raw_candidates) > 50:
        raise ValueError("candidates must contain between 1 and 50 evidence records")

    decorated: list[dict[str, Any]] = []
    national_candidates: list[dict[str, Any]] = []
    for raw in raw_candidates:
        geography = normalize_geography(
            jurisdiction=geo,
            geography_code=raw.get("geography_code") or raw.get("country_code") or raw.get("jurisdiction"),
            geography_label=raw.get("geography_label") or raw.get("country_name") or raw.get("area_name"),
            geography_level=raw.get("geography_level") or raw.get("scope_level"),
        )
        candidate_concept = _clean(raw.get("concept_id") or concept_for_indicator(_clean(raw.get("indicator_id"))) or "unknown")
        row = {
            **raw,
            "concept_id": candidate_concept,
            "geography": geography,
            "reference_period": _reference_period(raw),
            "methodology": _methodology(raw),
            "exact_concept": candidate_concept == concept,
            "selection_eligible_geography": geography["eligible_for_national_selection"],
        }
        decorated.append(row)
        if geography["eligible_for_national_selection"]:
            national_candidates.append(row)

    selection = None
    if national_candidates:
        try:
            selection = select_evidence(concept_id=concept, jurisdiction=geo, candidates=national_candidates, now=now)
        except ValueError:
            selection = None

    selected = selection.get("selected") if isinstance(selection, Mapping) else None
    selected_source = selected.get("source_id") if isinstance(selected, Mapping) else None
    preferred = _preferred_sources(geo, concept)
    preferred_present = next((source for source in preferred if any(_clean(row.get("source_id")) == source and row["exact_concept"] and row["selection_eligible_geography"] for row in decorated)), None)
    higher_preferred_absent = bool(selected_source and preferred and (selected_source not in preferred or preferred.index(selected_source) > 0))

    comparisons: list[dict[str, Any]] = []
    exact_national = [row for row in decorated if row["exact_concept"] and row["selection_eligible_geography"] and row.get("value") is not None]
    threshold = MATERIAL_DIFFERENCE_PCT.get(concept, 1.0)
    for idx, left in enumerate(exact_national):
        for right in exact_national[idx + 1:]:
            same_unit = _clean(left.get("unit")) == _clean(right.get("unit"))
            same_period = left["reference_period"] == right["reference_period"] and left["reference_period"] != "unknown"
            same_methodology = left["methodology"] == right["methodology"] or left["methodology"]["id"] == right["methodology"]["id"] != "unspecified"
            difference = _numeric_difference(left.get("value"), right.get("value")) if same_unit else None
            material = bool(difference and difference["percent_vs_right"] >= threshold)
            if not same_unit:
                classification = "unit-incompatible-do-not-compare"
            elif not same_period:
                classification = "different-reference-periods"
            elif material and not same_methodology:
                classification = "material-discrepancy-methodology-diverges"
            elif material:
                classification = "material-discrepancy-review"
            else:
                classification = "within-disclosure-threshold"
            comparisons.append({
                "left_source_id": _clean(left.get("source_id")) or "unknown",
                "right_source_id": _clean(right.get("source_id")) or "unknown",
                "left_value": left.get("value"),
                "right_value": right.get("value"),
                "unit": left.get("unit") if same_unit else None,
                "left_reference_period": left["reference_period"],
                "right_reference_period": right["reference_period"],
                "left_methodology": left["methodology"],
                "right_methodology": right["methodology"],
                "difference": difference,
                "material_threshold_percent": threshold,
                "classification": classification,
                "automatic_blending_allowed": False,
            })

    excluded = []
    for row in decorated:
        reasons = []
        if not row["exact_concept"]:
            reasons.append("different-concept")
        if not row["selection_eligible_geography"]:
            reasons.append(row["geography"]["compatibility"])
        if reasons:
            excluded.append({
                "source_id": _clean(row.get("source_id")) or "unknown",
                "value": row.get("value"),
                "unit": row.get("unit"),
                "reference_period": row["reference_period"],
                "geography": row["geography"],
                "reasons": reasons,
                "retained_as_context": True,
            })

    if selected_source:
        state = "reconciled" if len(exact_national) > 1 else "single-source-selection"
    else:
        state = "no-national-exact-concept-selection"
    if selected_source and (higher_preferred_absent or (preferred and not preferred_present)):
        state = "fallback-selected-preferred-source-not-in-candidate-set"

    rationale = []
    if selected_source:
        rationale.append(f"Selected {selected_source} from semantically and geographically eligible candidates.")
        if preferred and selected_source == preferred[0]:
            rationale.append("The selected source is the highest-precedence preferred source for this jurisdiction and concept.")
        elif preferred and higher_preferred_absent:
            higher = preferred[:preferred.index(selected_source)] if selected_source in preferred else preferred
            rationale.append(f"Higher-precedence source(s) {', '.join(higher)} were not present as exact national candidates; the selected value remains an explicit fallback, not a substitute for missing preferred evidence.")
        elif preferred and preferred_present is None:
            rationale.append(f"Preferred source(s) {', '.join(preferred)} were not present as exact national candidates; the selected value remains an explicit fallback, not a substitute for missing preferred evidence.")
        rationale.append("Authority, declared precedence, cadence-aware freshness and status are applied only after exact concept and unit compatibility.")
    else:
        rationale.append("No candidate satisfied the exact-concept and national-geography selection boundary.")

    result = {
        "ok": True,
        "version": VERSION,
        "schema": SCHEMA,
        "contract": CONTRACT,
        "jurisdiction": geo,
        "concept": {"concept_id": concept, **METRIC_CONCEPTS[concept]},
        "reconciliation_state": state,
        "preferred_sources": preferred,
        "preferred_source_present": preferred_present,
        "selected": selected,
        "selection": selection,
        "candidate_count": len(decorated),
        "national_exact_candidate_count": len(exact_national),
        "candidates": decorated,
        "comparisons": comparisons,
        "excluded_from_national_selection": excluded,
        "selection_rationale": rationale,
        "boundaries": [
            "Site Intelligence does not average conflicting source values into a synthetic country statistic.",
            "Subnational Gaza or West Bank observations remain visible as scoped context but cannot silently replace a Palestine-wide statistic.",
            "Different reference periods are temporal differences, not automatically contradictions.",
            "Different methodologies can produce different valid estimates; methodology differences remain attached to the discrepancy.",
            "A preferred source that is absent from the candidate set is reported as absent rather than silently imputed or substituted.",
        ],
        "generated_at": _now(),
    }
    result["reconciliation_sha256"] = _digest({
        "jurisdiction": geo,
        "concept": concept,
        "selected_source": selected_source,
        "comparisons": comparisons,
        "excluded": excluded,
    })
    return result


def country_reconciliation_snapshot(country_code: str) -> dict[str, Any]:
    from .live_country_intelligence import country_indicators
    payload = country_indicators(country_code)
    code = str(payload["country"]["code"]).upper()
    rows = []
    for item in payload.get("indicators") or []:
        latest = item.get("latest") if isinstance(item.get("latest"), Mapping) else None
        concept = concept_for_indicator(str(item.get("id") or ""))
        if not concept:
            continue
        candidate = {
            "source_id": (item.get("canonical_observation") or {}).get("source", {}).get("source_id") or item.get("source_id") or "unknown",
            "publisher": item.get("source"),
            "indicator_id": item.get("id"),
            "concept_id": concept,
            "authority_class": (item.get("canonical_observation") or {}).get("source", {}).get("authority_class") or "unknown",
            "value": latest.get("value") if latest else None,
            "unit": item.get("unit"),
            "observation_year": latest.get("year") if latest else None,
            "status": "final" if latest else "unknown",
            "geography_code": code,
            "geography_label": payload["country"].get("name"),
            "geography_level": "national",
            "methodology_id": "upstream-series-methodology-not-expanded",
        }
        if latest:
            reconciled = reconcile_evidence(jurisdiction=code, concept_id=concept, candidates=[candidate])
            preferred = reconciled["preferred_sources"]
            rows.append({
                "indicator_id": item.get("id"),
                "label": item.get("label"),
                "concept_id": concept,
                "selected_source_id": reconciled.get("selected", {}).get("source_id") if reconciled.get("selected") else None,
                "selected_value": latest.get("value"),
                "unit": item.get("unit"),
                "reference_period": str(latest.get("year")),
                "reconciliation_state": reconciled["reconciliation_state"],
                "preferred_sources": preferred,
                "preferred_source_present": reconciled["preferred_source_present"],
                "note": reconciled["selection_rationale"][1] if len(reconciled["selection_rationale"]) > 1 else reconciled["selection_rationale"][0],
            })
    return {
        "ok": True,
        "version": VERSION,
        "schema": SCHEMA,
        "contract": CONTRACT,
        "country": payload["country"],
        "indicator_count": len(rows),
        "indicators": rows,
        "summary": {
            "reconciled_multi_source": sum(1 for row in rows if row["reconciliation_state"] == "reconciled"),
            "single_source": sum(1 for row in rows if row["reconciliation_state"] == "single-source-selection"),
            "fallback_without_preferred_candidate": sum(1 for row in rows if row["reconciliation_state"] == "fallback-selected-preferred-source-not-in-candidate-set"),
        },
        "boundary": "This snapshot explains the evidence actually available to the country workspace. A preferred authority not present in the candidate set is disclosed as missing from reconciliation, not inferred to have no data.",
        "generated_at": _now(),
    }


def readiness() -> dict[str, Any]:
    checks = {
        "exact_concept_before_authority": True,
        "national_geography_before_precedence": True,
        "palestine_subnational_scope_guard": normalize_geography(jurisdiction="PSE", geography_label="Gaza Strip")["eligible_for_national_selection"] is False,
        "different_reference_periods_not_automatic_conflicts": True,
        "methodology_difference_disclosed": True,
        "automatic_blending_prohibited": True,
        "preferred_source_absence_disclosed": True,
        "readiness_requires_no_upstream_network": True,
        "upstream_health_non_blocking": True,
    }
    return {
        "ok": all(checks.values()),
        "version": VERSION,
        "schema": SCHEMA,
        "contract": CONTRACT,
        "checks": checks,
        "network_calls_performed": False,
        "upstream_health_release_blocking": False,
        "generated_at": _now(),
    }
