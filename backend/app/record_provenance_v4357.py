from __future__ import annotations

"""v4.35.20 semantic/freshness enrichment for record-level provenance."""

from typing import Any, Mapping
from .config import Settings
from . import record_provenance_v3238 as prior
from .evidence_intelligence_v4357 import concept_for_indicator, indicator_semantics, freshness_assessment


def _enrich_indicator(record: dict[str, Any], country_code: str, indicator_id: str) -> dict[str, Any]:
    concept_id = concept_for_indicator(indicator_id)
    if not concept_id:
        return record
    semantics = indicator_semantics(indicator_id, jurisdiction=country_code)
    observed = record.get("dates", {}).get("observation_at") or record.get("dates", {}).get("observation_year")
    freshness = freshness_assessment(observed_at=observed, cadence=semantics["metric"]["cadence"])
    record["semantics"] = {
        "concept_id": concept_id,
        "kind": semantics["metric"]["kind"],
        "claim": semantics["metric"]["claim"],
        "forbidden_substitutions": list(semantics["metric"]["forbidden_substitutions"]),
        "precedence_rules": semantics["precedence_rules"],
    }
    record["freshness"] = freshness
    record.setdefault("limitations", []).append("Freshness is evaluated against the expected publication cadence and does not change the metric's meaning.")
    if concept_id == "electricity_structural_access":
        record["limitations"].append("Electricity access is a structural access statistic. It does not measure current electricity availability, grid reliability, outage status, hours of supply, generator dependence or current service continuity.")
        record["assertion"] = "A dated structural electricity-access observation is disclosed for the source reference period; it is not a statement about current electricity supply or reliability."
    return record


def public_indicator_record_truth(settings: Settings, country_code: str, indicator_id: str) -> dict[str, Any]:
    return _enrich_indicator(prior.public_indicator_record_truth(settings, country_code, indicator_id), country_code.upper(), indicator_id)


def public_country_record_truth(settings: Settings, country_code: str) -> dict[str, Any]:
    catalog = prior.public_country_record_truth(settings, country_code)
    catalog["records"] = [_enrich_indicator(record, country_code.upper(), record.get("source", {}).get("indicator_id") or "") for record in catalog.get("records", [])]
    return catalog


def public_map_layer_truth(settings: Settings, layer_id: str, date: str | None = None) -> dict[str, Any]:
    return prior.public_map_layer_truth(settings, layer_id, date=date)


def public_normalized_record_truth(settings: Settings, record: Mapping[str, Any]) -> dict[str, Any]:
    normalized = prior.public_normalized_record_truth(settings, record)
    concept_id = str(record.get("concept_id") or "").strip()
    if concept_id:
        normalized["semantics"] = {"concept_id": concept_id}
    return normalized


def public_record_truth_manifest(settings: Settings, country_code: str) -> dict[str, Any]:
    # Keep the prior manifest identity contract; individual indicator endpoints carry semantic enrichment.
    return prior.public_record_truth_manifest(settings, country_code)
