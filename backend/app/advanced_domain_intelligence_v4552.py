from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from statistics import mean
from typing import Any, Mapping

from .version import APP_VERSION

REGISTRY_SCHEMA = "sc-site-intelligence-advanced-domain-intelligence-registry/1.0"
ANALYSIS_SCHEMA = "sc-site-intelligence-advanced-domain-analysis/1.0"
PACKET_SCHEMA = "sc-site-intelligence-advanced-domain-research-packet/1.0"
REGISTRY_PATH = Path(__file__).resolve().parents[1] / "data" / "advanced_domain_intelligence_registry_v4552.json"


def _canon(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str).encode("utf-8")


def _digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canon(value)).hexdigest()


def _text(value: Any, limit: int = 400) -> str:
    return " ".join(str(value or "").strip().split())[:limit]


def _num(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if result != result or abs(result) == float("inf"):
        return None
    return result


def _list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _registry() -> dict[str, Any]:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    if registry.get("version") != APP_VERSION or registry.get("schema") != REGISTRY_SCHEMA:
        raise ValueError("advanced-domain intelligence registry mismatch")
    return registry


def registry_manifest() -> dict[str, Any]:
    registry = _registry()
    return {"ok": True, "version": APP_VERSION, **deepcopy(registry)}


def domain_profile(domain: str) -> dict[str, Any]:
    item = next((row for row in _registry()["domains"] if row["domain_id"] == domain), None)
    if not item:
        raise ValueError(f"unknown advanced intelligence domain: {domain}")
    return {
        "ok": True,
        "version": APP_VERSION,
        "domain": deepcopy(item),
        "workspace_level": "advanced-intelligence-workspace",
    }


def _records(request: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    return [row for row in request.get("records", []) if isinstance(row, Mapping)]


def _distribution(rows: list[Mapping[str, Any]], *keys: str, limit: int = 15) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for row in rows:
        value = None
        for key in keys:
            candidate = row.get(key)
            if candidate not in (None, "", []):
                value = candidate
                break
        for item in _list(value):
            label = _text(item, 180)
            if label:
                counts[label] = counts.get(label, 0) + 1
    return [
        {"label": label, "count": count}
        for label, count in sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))[:limit]
    ]


def _source_summary(rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    sources = _distribution(rows, "source_id", "source", "provider", limit=30)
    dates = sorted(
        {
            _text(row.get("date") or row.get("display_date") or row.get("period") or row.get("event_date"), 80)
            for row in rows
            if row.get("date") or row.get("display_date") or row.get("period") or row.get("event_date")
        }
    )
    return {
        "source_count": len(sources),
        "sources": sources,
        "temporal_extent": {"first": dates[0] if dates else None, "last": dates[-1] if dates else None},
        "record_count": len(rows),
    }


def _dossiers(rows: list[Mapping[str, Any]], request: Mapping[str, Any]) -> dict[str, Any]:
    entity_counts: dict[str, int] = {}
    explicit_edges: list[dict[str, str]] = []
    timeline: list[dict[str, Any]] = []
    for row in rows:
        title = _text(row.get("title") or row.get("name") or row.get("record_id"), 240)
        for key in ("entities", "actors", "organizations", "countries"):
            for item in _list(row.get(key)):
                if isinstance(item, Mapping):
                    label = _text(item.get("name") or item.get("label") or item.get("id"), 200)
                else:
                    label = _text(item, 200)
                if label:
                    entity_counts[label] = entity_counts.get(label, 0) + 1
        subject = _text(row.get("subject_entity") or row.get("subject") or row.get("actor"), 200)
        obj = _text(row.get("object_entity") or row.get("counterparty") or row.get("target"), 200)
        relation = _text(row.get("relationship") or row.get("relation_type"), 100)
        if subject and obj and relation:
            explicit_edges.append({"source": subject, "target": obj, "relation": relation})
        date = _text(row.get("date") or row.get("display_date") or row.get("event_date"), 80)
        if date:
            timeline.append({"date": date, "title": title or "Untitled record", "source_id": _text(row.get("source_id"), 120)})
    timeline.sort(key=lambda row: (row["date"], row["title"]))
    return {
        "mode": _text(request.get("mode") or "investigation", 80),
        "record_types": _distribution(rows, "record_type", "type", "domain"),
        "top_entities": [
            {"label": label, "count": count}
            for label, count in sorted(entity_counts.items(), key=lambda pair: (-pair[1], pair[0]))[:20]
        ],
        "explicit_relationships": explicit_edges[:100],
        "timeline": timeline[:100],
        "claim_counts": _distribution(rows, "claim_type", "status", limit=20),
        "automatic_truth_determination": False,
        "automatic_relationship_inference": False,
    }


def _economics(rows: list[Mapping[str, Any]], request: Mapping[str, Any]) -> dict[str, Any]:
    series: dict[tuple[str, str, str, str], list[tuple[str, float]]] = {}
    latest: list[dict[str, Any]] = []
    for row in rows:
        value = _num(row.get("value_number") if row.get("value_number") is not None else row.get("value"))
        if value is None:
            continue
        key = (
            _text(row.get("indicator_code") or row.get("indicator") or "unknown", 180),
            _text(row.get("geography_code") or row.get("country") or "unknown", 40),
            _text(row.get("unit") or "unknown", 100),
            _text(row.get("frequency") or "unknown", 60),
        )
        period = _text(row.get("period") or row.get("date") or row.get("year"), 80)
        series.setdefault(key, []).append((period, value))
    growth: list[dict[str, Any]] = []
    for key, values in series.items():
        ordered = sorted(values, key=lambda pair: pair[0])
        latest.append({"indicator": key[0], "geography": key[1], "unit": key[2], "frequency": key[3], "period": ordered[-1][0], "value": ordered[-1][1], "observations": len(ordered)})
        if len(ordered) >= 2 and ordered[-2][1] != 0:
            growth.append({"indicator": key[0], "geography": key[1], "from_period": ordered[-2][0], "to_period": ordered[-1][0], "percent_change": ((ordered[-1][1] - ordered[-2][1]) / abs(ordered[-2][1])) * 100.0})
    return {
        "mode": _text(request.get("mode") or "macro-sustainability", 80),
        "latest_series": sorted(latest, key=lambda row: (row["indicator"], row["geography"]))[:100],
        "recent_changes": sorted(growth, key=lambda row: (row["indicator"], row["geography"]))[:100],
        "geographies": _distribution(rows, "geography_code", "country"),
        "indicator_families": _distribution(rows, "family", "domain", "subject"),
        "units": _distribution(rows, "unit"),
        "silent_unit_normalization": False,
        "investment_advice": False,
        "causal_claims": False,
    }


def _law(rows: list[Mapping[str, Any]], request: Mapping[str, Any]) -> dict[str, Any]:
    timeline = []
    for row in rows:
        date = _text(row.get("display_date") or row.get("date") or row.get("adoption_date"), 80)
        if date:
            timeline.append({
                "date": date,
                "title": _text(row.get("title") or row.get("official_symbol"), 240),
                "authority": _text(row.get("authority_level") or row.get("authority_label"), 140),
                "body": _text(row.get("legal_body") or row.get("issuing_body"), 180),
            })
    timeline.sort(key=lambda row: (row["date"], row["title"]))
    return {
        "mode": _text(request.get("mode") or "authority-obligation", 80),
        "authority_levels": _distribution(rows, "authority_level", "authority_label"),
        "legal_bodies": _distribution(rows, "legal_body", "issuing_body"),
        "instrument_types": _distribution(rows, "record_type", "instrument_type"),
        "legal_statuses": _distribution(rows, "legal_status", "status"),
        "subjects": _distribution(rows, "subjects", "subject"),
        "countries": _distribution(rows, "countries", "country"),
        "timeline": timeline[:120],
        "automatic_authority_ranking": False,
        "legal_conclusion": False,
        "human_legal_review_required": True,
    }


def _science(rows: list[Mapping[str, Any]], request: Mapping[str, Any]) -> dict[str, Any]:
    numeric: dict[str, list[float]] = {}
    for row in rows:
        variable = _text(row.get("variable") or row.get("parameter") or row.get("indicator") or row.get("dataset_id") or row.get("record_type"), 180)
        value = _num(row.get("value_number") if row.get("value_number") is not None else row.get("value"))
        if variable and value is not None:
            numeric.setdefault(variable, []).append(value)
    summaries = [
        {"variable": key, "count": len(values), "min": min(values), "max": max(values), "mean": mean(values)}
        for key, values in sorted(numeric.items())
    ]
    return {
        "mode": _text(request.get("mode") or "earth-ocean-space", 80),
        "disciplines": _distribution(rows, "discipline", "domain", "record_type"),
        "missions": _distribution(rows, "mission", "mission_id"),
        "instruments": _distribution(rows, "instrument", "instrument_id"),
        "targets": _distribution(rows, "target", "target_id"),
        "datasets": _distribution(rows, "dataset_id", "collection"),
        "numeric_observation_summaries": summaries[:100],
        "automatic_anomaly_claim": False,
        "automatic_habitability_claim": False,
        "automatic_signal_authenticity": False,
    }


def _humanitarian(rows: list[Mapping[str, Any]], request: Mapping[str, Any]) -> dict[str, Any]:
    displacement_values: list[float] = []
    affected_values: list[float] = []
    for row in rows:
        for key, bucket in (("displaced", displacement_values), ("displacement", displacement_values), ("idps", displacement_values), ("affected", affected_values), ("people_affected", affected_values)):
            value = _num(row.get(key))
            if value is not None:
                bucket.append(value)
    return {
        "mode": _text(request.get("mode") or "conflict-displacement", 80),
        "event_types": _distribution(rows, "event_type", "record_type", "category"),
        "countries": _distribution(rows, "country", "country_code", "geography_code"),
        "actors": _distribution(rows, "actors", "actor", "organization"),
        "access_constraints": _distribution(rows, "access_status", "access_constraint", "severity"),
        "displacement_reported_total": sum(displacement_values) if displacement_values else None,
        "affected_reported_total": sum(affected_values) if affected_values else None,
        "automatic_severity_ranking": False,
        "automatic_culpability_inference": False,
        "humanitarian_decision_automation": False,
    }


def _resources(rows: list[Mapping[str, Any]], request: Mapping[str, Any]) -> dict[str, Any]:
    flows: dict[tuple[str, str], float] = {}
    for row in rows:
        geo = _text(row.get("geography_code") or row.get("country"), 40)
        counterpart = _text(row.get("counterpart_code") or row.get("counterpart"), 40)
        value = _num(row.get("value_number") if row.get("value_number") is not None else row.get("value"))
        if geo and counterpart and value is not None:
            flows[(geo, counterpart)] = flows.get((geo, counterpart), 0.0) + value
    flow_rows = [
        {"geography": key[0], "counterpart": key[1], "reported_value": value}
        for key, value in sorted(flows.items(), key=lambda pair: (-abs(pair[1]), pair[0]))[:100]
    ]
    return {
        "mode": _text(request.get("mode") or "trade-energy-security", 80),
        "families": _distribution(rows, "family", "domain"),
        "commodities": _distribution(rows, "commodity", "resource", "indicator_name"),
        "energy_types": _distribution(rows, "energy_type", "fuel", "technology"),
        "geographies": _distribution(rows, "geography_code", "country"),
        "counterparts": _distribution(rows, "counterpart_code", "counterpart"),
        "reported_bilateral_flows": flow_rows,
        "dependency_is_descriptive_not_risk_score": True,
        "automatic_security_ranking": False,
        "automatic_sanctions_determination": False,
    }


_ANALYZERS = {
    "dossiers": _dossiers,
    "economics": _economics,
    "international-law": _law,
    "science": _science,
    "humanitarian": _humanitarian,
    "resources": _resources,
}


def analyze(domain: str, request: Mapping[str, Any]) -> dict[str, Any]:
    if domain not in _ANALYZERS:
        raise ValueError(f"unknown advanced intelligence domain: {domain}")
    rows = _records(request)
    domain_result = _ANALYZERS[domain](rows, request)
    core = {
        "schema": ANALYSIS_SCHEMA,
        "version": APP_VERSION,
        "domain": domain,
        "record_count": len(rows),
        "source_summary": _source_summary(rows),
        "analysis": domain_result,
        "provenance": {
            "source_records_mutated": False,
            "missing_values_fabricated": False,
            "automatic_external_fetch": False,
            "automatic_causality": False,
        },
    }
    return {"ok": True, "version": APP_VERSION, "result": {**core, "analysis_digest": _digest(core)}}


def research_packet(domain: str, request: Mapping[str, Any]) -> dict[str, Any]:
    result = analyze(domain, request)["result"]
    profile = domain_profile(domain)["domain"]
    packet_core = {
        "schema": PACKET_SCHEMA,
        "version": APP_VERSION,
        "domain": domain,
        "title": _text(request.get("title") or f"{profile['label']} research packet", 240),
        "analysis_digest": result["analysis_digest"],
        "record_count": result["record_count"],
        "source_summary": result["source_summary"],
        "analysis": result["analysis"],
        "recommended_handoffs": deepcopy(profile.get("recommended_handoffs", [])),
        "research_workflow": deepcopy(profile.get("research_workflow", [])),
        "boundaries": [
            "source-records-remain-authoritative",
            "derived-analysis-is-not-observation",
            "missing-data-is-not-filled",
            "no-automatic-causal-or-legal-or-security-conclusion",
            "handoff-requires-human-confirmation",
        ],
        "automatic_delivery": False,
        "human_confirmation_required": True,
    }
    digest = _digest(packet_core)
    return {"ok": True, "version": APP_VERSION, "packet": {**packet_core, "packet_id": f"domain-packet:{digest[7:31]}", "packet_digest": digest}}


def parity_audit() -> dict[str, Any]:
    registry = _registry()
    required = {
        "evidence",
        "filtering",
        "comparison",
        "mapping",
        "time-context",
        "scenario",
        "provenance",
        "research-handoff",
        "reproducible-export",
        "diagnostics",
    }
    rows = []
    for domain in registry["domains"]:
        have = set(domain.get("capabilities", []))
        missing = sorted(required - have)
        rows.append({
            "domain_id": domain["domain_id"],
            "advanced": not missing,
            "missing": missing,
            "capability_count": len(have),
            "operation_count": len(domain.get("analysis_modes", [])),
        })
    return {
        "ok": all(row["advanced"] for row in rows),
        "version": APP_VERSION,
        "workspace_level": "advanced-intelligence-workspace",
        "required_capabilities": sorted(required),
        "domains": rows,
    }


def compatibility_manifest() -> dict[str, Any]:
    return {
        "ok": True,
        "version": APP_VERSION,
        "v4551_runtime_repair": "preserved",
        "v4550_spatial_lineage": "preserved",
        "v4540_reproducible_packages": "preserved",
        "v4530_advanced_domain_parity": "preserved-and-expanded",
        "wordpress_role": "public-site-launch-bridge",
        "browser_analysis_source": "currently-loaded-official-records",
    }
