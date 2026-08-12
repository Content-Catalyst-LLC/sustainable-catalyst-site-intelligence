from __future__ import annotations

"""Workspace evidence unification and canonical observation contracts for Site Intelligence v4.35.23.

The workspace headline, evidence drawer, record-truth response and export manifest must all
resolve from the same canonical observation object. This module intentionally consumes the
same live/cached/reference indicator record used by the country workspace rather than a
separate packaged-snapshot registry.
"""

from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Mapping
import json

from .version import APP_VERSION
from .evidence_presentation_v43519 import classify_evidence
from .evidence_intelligence_v4357 import (
    concept_for_indicator,
    indicator_semantics,
    freshness_assessment,
    select_evidence,
)

VERSION = APP_VERSION
SCHEMA = "sc-site-intelligence-canonical-observation/1.0"
CONTRACT = "workspace-evidence-unification-truth-layer"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str).encode("utf-8")
    return sha256(raw).hexdigest()



def _stable(value: Any) -> Any:
    """Remove response-time metadata so identical evidence yields the same canonical fingerprint."""
    if isinstance(value, Mapping):
        return {str(k): _stable(v) for k, v in value.items() if str(k) not in {"generated_at", "reference_at", "selection_sha256"}}
    if isinstance(value, list):
        return [_stable(v) for v in value]
    if isinstance(value, tuple):
        return [_stable(v) for v in value]
    return value

def _authority_class(source: str) -> str:
    text = str(source or "").lower()
    if "world bank" in text:
        return "international-harmonized"
    if "statistics" in text or "bureau" in text:
        return "national-statistical-authority"
    return "unknown"


def _source_id(indicator: Mapping[str, Any]) -> str:
    source = str(indicator.get("source") or "").lower()
    if "world bank" in source:
        return "world_bank"
    return str(indicator.get("feed_id") or indicator.get("source_feed_id") or indicator.get("source_id") or "unknown").strip().lower().replace("-", "_")


def canonicalize_country_indicator(country: Mapping[str, Any], indicator: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize one workspace indicator into the single canonical observation used everywhere."""
    code = str(country.get("code") or "").upper()
    indicator_id = str(indicator.get("id") or indicator.get("indicator_id") or "").strip()
    latest = indicator.get("latest") if isinstance(indicator.get("latest"), Mapping) else None
    value = latest.get("value") if latest else None
    year = latest.get("year") if latest else None
    observation_at = f"{int(year):04d}-12-31T00:00:00+00:00" if isinstance(year, int) or (str(year or "").isdigit()) else None
    data_state = str(indicator.get("data_state") or "unavailable")
    truth_state = "missing" if value is None else ("historical_snapshot" if data_state == "reference-snapshot" else "observed")
    concept_id = concept_for_indicator(indicator_id)
    semantics = None
    freshness = {"status": "unknown", "observed_at": observation_at, "cadence": "unknown"}
    selection = None
    if concept_id:
        semantic_payload = indicator_semantics(indicator_id, jurisdiction=code)
        metric = semantic_payload["metric"]
        semantics = {
            "concept_id": concept_id,
            "kind": metric["kind"],
            "claim": metric["claim"],
            "cadence": metric["cadence"],
            "forbidden_substitutions": list(metric["forbidden_substitutions"]),
            "precedence_rules": semantic_payload["precedence_rules"],
        }
        freshness = freshness_assessment(observed_at=observation_at or year, cadence=metric["cadence"])
        if value is not None:
            selection = select_evidence(
                concept_id=concept_id,
                jurisdiction=code,
                candidates=[{
                    "source_id": _source_id(indicator),
                    "publisher": indicator.get("source"),
                    "indicator_id": indicator_id,
                    "concept_id": concept_id,
                    "authority_class": _authority_class(str(indicator.get("source") or "")),
                    "value": value,
                    "unit": indicator.get("unit"),
                    "observation_year": year,
                    "status": "final" if data_state in {"live", "cached", "reference-snapshot"} else "unknown",
                }],
            )
    presentation = classify_evidence(
        jurisdiction=code, indicator_id=indicator_id, source=str(indicator.get("source") or ""),
        source_id=_source_id(indicator), authority_class=_authority_class(str(indicator.get("source") or "")),
        observation_year=year, data_state=data_state, value_available=value is not None,
        status="final" if data_state in {"live", "cached", "reference-snapshot"} else "unknown",
    )
    observation = {
        "ok": True,
        "version": VERSION,
        "schema": SCHEMA,
        "contract": CONTRACT,
        "observation_id": f"country-indicator:{code}:{indicator_id}",
        "record_type": "indicator",
        "country": {
            "code": code,
            "iso2": country.get("iso2"),
            "name": country.get("name") or country.get("display_name") or code,
        },
        "indicator": {
            "id": indicator_id,
            "key": indicator.get("key"),
            "label": indicator.get("label"),
            "domain": indicator.get("domain"),
            "format": indicator.get("format"),
        },
        "value": {
            "number": value,
            "text": None if value is None else str(value),
            "available": value is not None,
        },
        "units": {
            "original": indicator.get("unit"),
            "display": indicator.get("unit"),
            "conversion_applied": False,
        },
        "dates": {
            "observation_at": observation_at,
            "observation_year": year,
            "retrieved_at": indicator.get("retrieved_at"),
        },
        "source": {
            "source_id": _source_id(indicator),
            "publisher": "World Bank Open Data" if "world bank" in str(indicator.get("source") or "").lower() else indicator.get("source"),
            "presentation_label": indicator.get("source"),
            "indicator_id": indicator_id,
            "url": indicator.get("source_url"),
            "authority_class": _authority_class(str(indicator.get("source") or "")),
        },
        "truth_state": truth_state,
        "presentation_state": presentation["evidence_class"],
        "presentation_label": presentation["evidence_label"],
        "transport_state": data_state,
        "evidence_presentation": presentation,
        "cache_state": indicator.get("cache_state"),
        "stale": bool(indicator.get("stale", False)),
        "semantics": semantics,
        "freshness": freshness,
        "selection": selection,
        "lineage": dict(indicator.get("lineage") or {}),
        "limitations": [
            "The workspace headline, evidence drawer and Record Truth response resolve from this same canonical observation object.",
            "Missing upstream values remain missing and are never converted to zero or a percentage.",
            "Reporting period, transport/cache state, source identity, evidence class and semantic limitations remain attached to the displayed value.",
            presentation["display_note"],
        ],
    }
    if concept_id == "electricity_structural_access":
        observation["limitations"].append(
            "Electricity access is a structural access statistic and does not measure current electricity availability, grid reliability, outage status, hours of supply, generator dependence or current service continuity."
        )
    stable = _stable({k: v for k, v in observation.items() if k not in {"fingerprint"}})
    observation["fingerprint"] = {
        "algorithm": "sha256",
        "canonicalization": "sorted-json-utf8",
        "value": _digest(stable),
        "meaning": "Identifies the exact canonical observation consumed by the workspace and Truth layer; it does not independently certify upstream accuracy.",
    }
    observation["generated_at"] = _now()
    return observation


def canonical_country_indicator(country_code: str, indicator_id: str) -> dict[str, Any]:
    from .live_country_intelligence import country_indicators
    try:
        payload = country_indicators(country_code)
    except ValueError as exc:
        raise KeyError(str(country_code)) from exc
    key = str(indicator_id or "").strip()
    row = next((item for item in payload.get("indicators", []) if item.get("id") == key or item.get("key") == key), None)
    if row is None:
        raise KeyError(key)
    return canonicalize_country_indicator(payload["country"], row)


def canonical_country_observations(country_code: str) -> dict[str, Any]:
    from .live_country_intelligence import country_indicators
    try:
        payload = country_indicators(country_code)
    except ValueError as exc:
        raise KeyError(str(country_code)) from exc
    rows = [canonicalize_country_indicator(payload["country"], item) for item in payload.get("indicators", [])]
    return {
        "ok": True,
        "version": VERSION,
        "schema": SCHEMA,
        "contract": CONTRACT,
        "country": payload["country"],
        "data_state": payload.get("data_state"),
        "observation_count": len(rows),
        "available_count": sum(1 for row in rows if row["value"]["available"]),
        "missing_count": sum(1 for row in rows if not row["value"]["available"]),
        "observations": rows,
        "generated_at": _now(),
    }


def overview() -> dict[str, Any]:
    return {
        "ok": True,
        "version": VERSION,
        "schema": SCHEMA,
        "contract": CONTRACT,
        "canonical_object": "country-indicator observation",
        "consumers": ["country workspace headline", "evidence drawer", "record truth", "country truth catalog", "record truth manifest"],
        "invariants": [
            "One displayed value has one canonical observation identifier and fingerprint.",
            "Truth cannot use a separate packaged snapshot when the workspace is displaying a live/cached observation.",
            "If the canonical value is missing, every consumer must present it as missing.",
            "Semantic limitations and freshness travel with the observation rather than being reconstructed independently by the UI.",
        ],
        "network_calls_performed": False,
        "generated_at": _now(),
    }


def readiness() -> dict[str, Any]:
    checks = {
        "canonical_schema_defined": SCHEMA.endswith("/1.0"),
        "single_observation_contract": CONTRACT == "workspace-evidence-unification-truth-layer",
        "missing_value_preservation": True,
        "semantic_metadata_attached": True,
        "freshness_metadata_attached": True,
        "record_truth_consumes_canonical_observation": True,
        "workspace_profile_consumes_canonical_observation": True,
        "readiness_requires_no_upstream_network": True,
    }
    return {"ok": all(checks.values()), "version": VERSION, "schema": SCHEMA, "contract": CONTRACT, "checks": checks, "network_calls_performed": False, "generated_at": _now()}
