from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

from .evidence_intelligence_v4357 import AUTHORITY_RANK, PRECEDENCE_RULES, STATUS_RANK
from .version import APP_VERSION

REGISTRY_SCHEMA = "sc-site-intelligence-global-source-federation-registry/1.0"
SOURCE_SCHEMA = "sc-site-intelligence-source-authority/1.0"
SELECTION_SCHEMA = "sc-site-intelligence-source-selection/1.0"
FEDERATION_PLAN_SCHEMA = "sc-site-intelligence-source-federation-plan/1.0"
TRUST_EVALUATION_SCHEMA = "sc-site-intelligence-source-trust-evaluation/1.0"
CONTRACT_VERSION = "1.0.0"
REGISTRY_PATH = Path(__file__).resolve().parents[1] / "data" / "global_source_federation_registry_v4500.json"
COUNTRY_REGISTRY_PATH = Path(__file__).resolve().parents[1] / "data" / "country_identity_registry_v43523.json"

FRESHNESS_RANK = {"fresh": 30, "current": 30, "aging": 20, "stale": 10, "unknown": 0}
SCOPE_RANK = {"country": 400, "regional": 300, "multinational": 200, "global": 100}


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str).encode("utf-8")


def _digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def _registry() -> dict[str, Any]:
    payload = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    if payload.get("schema") != REGISTRY_SCHEMA:
        raise ValueError("Global source federation registry schema mismatch")
    if payload.get("version") != APP_VERSION:
        raise ValueError("Global source federation registry version does not match application version")
    return payload


def _countries() -> dict[str, Any]:
    payload = json.loads(COUNTRY_REGISTRY_PATH.read_text(encoding="utf-8"))
    if payload.get("version") != APP_VERSION:
        raise ValueError("Country identity registry version does not match application version")
    return payload


def _source_index() -> dict[str, dict[str, Any]]:
    return {row["source_id"]: row for row in _registry()["sources"]}


def _authority_index() -> dict[str, dict[str, Any]]:
    return {row["id"]: row for row in _registry()["authority_classes"]}


def _country_index() -> dict[str, dict[str, Any]]:
    return {row["code"].upper(): row for row in _countries().get("countries") or []}


def _precedence_rule(jurisdiction: str, concept_id: str) -> dict[str, Any] | None:
    jurisdiction = jurisdiction.upper()
    exact = [row for row in PRECEDENCE_RULES if row.get("jurisdiction") == jurisdiction and row.get("concept_id") == concept_id]
    if exact:
        return deepcopy(exact[0])
    wildcard = [row for row in PRECEDENCE_RULES if row.get("jurisdiction") == jurisdiction and row.get("concept_id") == "*"]
    return deepcopy(wildcard[0]) if wildcard else None


def _eligible_for_jurisdiction(source: dict[str, Any], jurisdiction: str | None, region: str | None) -> bool:
    scope = source.get("scope_type")
    if scope in {"global", "multinational"}:
        return True
    if scope == "country":
        return bool(jurisdiction and jurisdiction.upper() in {str(x).upper() for x in source.get("iso3") or []})
    if scope == "regional":
        return bool(region and region in set(source.get("regions") or []))
    return False


def _trust_decision(source: dict[str, Any], trust_profile: dict[str, Any] | None) -> dict[str, Any]:
    profile = trust_profile if isinstance(trust_profile, dict) else {}
    allowed_ids = {str(x) for x in profile.get("allowed_source_ids") or []}
    blocked_ids = {str(x) for x in profile.get("blocked_source_ids") or []}
    allowed_classes = {str(x) for x in profile.get("allowed_authority_classes") or []}
    allowed_modes = {str(x) for x in profile.get("allowed_federation_modes") or []}
    reasons: list[str] = []
    accepted = True
    sid = source["source_id"]
    if sid in blocked_ids:
        accepted = False; reasons.append("source-explicitly-blocked")
    if allowed_ids and sid not in allowed_ids:
        accepted = False; reasons.append("source-not-in-allowed-source-list")
    if allowed_classes and source.get("authority_class") not in allowed_classes:
        accepted = False; reasons.append("authority-class-not-allowed")
    if allowed_modes and source.get("federation_mode") not in allowed_modes:
        accepted = False; reasons.append("federation-mode-not-allowed")
    if accepted:
        reasons.append("accepted-by-user-trust-profile")
    return {
        "accepted": accepted,
        "reasons": reasons,
        "authority_class_unchanged": source.get("authority_class"),
        "quality_status_unchanged": source.get("quality_status"),
    }


def registry_manifest() -> dict[str, Any]:
    registry = _registry()
    return {
        "ok": True,
        "version": APP_VERSION,
        "contract_version": CONTRACT_VERSION,
        "schema": registry["schema"],
        "source_catalog_schema": SOURCE_SCHEMA,
        "selection_schema": SELECTION_SCHEMA,
        "federation_plan_schema": FEDERATION_PLAN_SCHEMA,
        "trust_evaluation_schema": TRUST_EVALUATION_SCHEMA,
        "source_count": len(registry["sources"]),
        "authority_class_count": len(registry["authority_classes"]),
        "regional_group_count": len(registry["regional_groups"]),
        "selection_policy": deepcopy(registry["selection_policy"]),
        "trust_policy": deepcopy(registry["trust_policy"]),
        "endpoints": {
            "authorities": "/public/source-federation/authorities",
            "source_detail": "/public/source-federation/authorities/{source_id}",
            "regions": "/public/source-federation/regions",
            "jurisdiction": "/public/source-federation/jurisdictions/{code}",
            "authority_types": "/public/source-federation/authority-types",
            "select": "/public/source-federation/select",
            "federate": "/public/source-federation/federate",
            "trust_evaluate": "/public/source-federation/trust-profile/evaluate",
            "compatibility": "/public/source-federation/compatibility",
        },
        "principles": deepcopy(registry["principles"]),
    }


def authority_types_manifest() -> dict[str, Any]:
    registry = _registry()
    return {
        "ok": True,
        "version": APP_VERSION,
        "count": len(registry["authority_classes"]),
        "authority_classes": deepcopy(registry["authority_classes"]),
        "boundary": "Authority class is source/jurisdiction metadata; it is not a user-trust score and does not override semantic compatibility.",
    }


def source_manifest(*, jurisdiction: str = "", region: str = "", domain: str = "", language: str = "", authority_class: str = "", federation_mode: str = "", query: str = "") -> dict[str, Any]:
    jurisdiction = jurisdiction.strip().upper()
    country = _country_index().get(jurisdiction) if jurisdiction else None
    resolved_region = region.strip() or (country.get("region") if country else "")
    q = query.strip().lower()
    rows = []
    for row in _registry()["sources"]:
        if jurisdiction and not _eligible_for_jurisdiction(row, jurisdiction, resolved_region):
            continue
        if region and row.get("scope_type") == "regional" and region not in (row.get("regions") or []):
            continue
        if domain and domain not in (row.get("domains") or []):
            continue
        if language and language not in (row.get("languages") or []):
            continue
        if authority_class and row.get("authority_class") != authority_class:
            continue
        if federation_mode and row.get("federation_mode") != federation_mode:
            continue
        if q and q not in " ".join([row.get("source_id", ""), row.get("name", ""), row.get("provider", ""), " ".join(row.get("domains") or [])]).lower():
            continue
        authority = _authority_index().get(row.get("authority_class"), {})
        rows.append({**deepcopy(row), "schema": SOURCE_SCHEMA, "authority_rank": authority.get("authority_rank")})
    rows.sort(key=lambda r: (-int(r.get("authority_rank") or 0), r["source_id"]))
    return {
        "ok": True,
        "version": APP_VERSION,
        "schema": SOURCE_SCHEMA,
        "count": len(rows),
        "filters": {"jurisdiction": jurisdiction or None, "region": resolved_region or None, "domain": domain or None, "language": language or None, "authority_class": authority_class or None, "federation_mode": federation_mode or None, "query": query or None},
        "sources": rows,
    }


def source_detail(source_id: str) -> dict[str, Any]:
    source = _source_index().get(source_id)
    if not source:
        raise ValueError(f"Unknown source_id: {source_id}")
    authority = _authority_index().get(source.get("authority_class"), {})
    return {
        "ok": True,
        "version": APP_VERSION,
        "schema": SOURCE_SCHEMA,
        "source": {**deepcopy(source), "authority_rank": authority.get("authority_rank")},
        "boundaries": {
            "authority_is_jurisdiction_limited": True,
            "authority_is_not_user_trust": True,
            "quality_is_not_user_trust": True,
            "discovery_mode_is_not_observation": source.get("federation_mode") == "discovery",
        },
    }


def regions_manifest() -> dict[str, Any]:
    registry = _registry()
    countries = _countries().get("countries") or []
    sources = registry["sources"]
    rows = []
    for group in registry["regional_groups"]:
        values = set(group["country_region_values"])
        country_rows = [c for c in countries if c.get("region") in values]
        source_rows = [s for s in sources if s.get("scope_type") in {"global", "multinational"} or bool(values.intersection(s.get("regions") or []))]
        rows.append({
            **deepcopy(group),
            "country_count": len(country_rows),
            "eligible_source_count": len(source_rows),
            "regional_authority_count": sum(1 for s in source_rows if s.get("scope_type") == "regional"),
            "country_codes": sorted(c["code"] for c in country_rows),
        })
    return {"ok": True, "version": APP_VERSION, "count": len(rows), "regions": rows}


def jurisdiction_manifest(code: str) -> dict[str, Any]:
    code = code.strip().upper()
    country = _country_index().get(code)
    if not country:
        raise ValueError(f"Unknown jurisdiction code: {code}")
    sources = source_manifest(jurisdiction=code)["sources"]
    rules = [deepcopy(row) for row in PRECEDENCE_RULES if row.get("jurisdiction") == code]
    return {
        "ok": True,
        "version": APP_VERSION,
        "jurisdiction": deepcopy(country),
        "eligible_source_count": len(sources),
        "eligible_sources": sources,
        "precedence_rules": rules,
        "precedence_boundary": "Declared precedence is applied only after exact semantic/unit/geographic compatibility is established.",
    }


def evaluate_trust_profile(request: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise ValueError("Trust evaluation request must be an object")
    profile = request.get("trust_profile") if isinstance(request.get("trust_profile"), dict) else {}
    source_ids = request.get("source_ids")
    if source_ids is None:
        source_ids = [row["source_id"] for row in _registry()["sources"]]
    if not isinstance(source_ids, list):
        raise ValueError("source_ids must be an array")
    rows = []
    for source_id in source_ids:
        source = _source_index().get(str(source_id))
        if not source:
            rows.append({"source_id": str(source_id), "accepted": False, "reasons": ["unknown-source-id"]})
            continue
        rows.append({"source_id": source["source_id"], **_trust_decision(source, profile)})
    result = {
        "schema": TRUST_EVALUATION_SCHEMA,
        "version": APP_VERSION,
        "profile": deepcopy(profile),
        "evaluations": rows,
        "accepted_source_ids": [row["source_id"] for row in rows if row.get("accepted")],
        "authority_mutated": False,
        "quality_mutated": False,
    }
    result["evaluation_digest"] = _digest(result)
    return result


def select_source(request: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise ValueError("Source selection request must be an object")
    candidates = request.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("candidates must be a non-empty array")
    jurisdiction = str(request.get("jurisdiction") or "").upper()
    concept_id = str(request.get("concept_id") or "*")
    country = _country_index().get(jurisdiction) if jurisdiction else None
    region = country.get("region") if country else None
    trust_profile = request.get("trust_profile") if isinstance(request.get("trust_profile"), dict) else None
    apply_trust = bool(request.get("apply_trust_profile", True))
    precedence = _precedence_rule(jurisdiction, concept_id) if jurisdiction else None
    preferred = precedence.get("preferred_sources") if precedence else []
    source_index = _source_index()
    authority_index = _authority_index()
    ranked = []
    excluded = []
    for position, candidate in enumerate(candidates):
        if not isinstance(candidate, dict):
            excluded.append({"position": position, "reason": "candidate-not-object"}); continue
        source_id = str(candidate.get("source_id") or "")
        source = source_index.get(source_id)
        if not source:
            excluded.append({"source_id": source_id, "reason": "unknown-source-id"}); continue
        if candidate.get("available", True) is False:
            excluded.append({"source_id": source_id, "reason": "candidate-unavailable"}); continue
        if candidate.get("semantic_compatible", True) is not True:
            excluded.append({"source_id": source_id, "reason": "semantic-incompatibility"}); continue
        if jurisdiction and not _eligible_for_jurisdiction(source, jurisdiction, region):
            excluded.append({"source_id": source_id, "reason": "outside-source-jurisdiction"}); continue
        trust = _trust_decision(source, trust_profile)
        if apply_trust and not trust["accepted"]:
            excluded.append({"source_id": source_id, "reason": "user-trust-profile-filter", "trust_reasons": trust["reasons"]}); continue
        precedence_index = preferred.index(source_id) if source_id in preferred else 9999
        authority_rank = int(authority_index.get(source.get("authority_class"), {}).get("authority_rank") or AUTHORITY_RANK.get(source.get("authority_class"), 0))
        scope_rank = SCOPE_RANK.get(source.get("scope_type"), 0)
        freshness_rank = FRESHNESS_RANK.get(str(candidate.get("freshness_state") or "unknown"), 0)
        status_rank = STATUS_RANK.get(str(candidate.get("record_status") or "unknown"), 0)
        precedence_rank = 10000 - precedence_index if precedence_index < 9999 else 0
        sort_vector = [precedence_rank, scope_rank, authority_rank, freshness_rank, status_rank]
        ranked.append({
            "source_id": source_id,
            "source": deepcopy(source),
            "candidate": deepcopy(candidate),
            "trust_evaluation": trust,
            "precedence_index": None if precedence_index == 9999 else precedence_index,
            "sort_vector": sort_vector,
        })
    if not ranked:
        raise ValueError("No eligible candidates remain after semantic, jurisdiction, availability, and trust filters")
    ranked.sort(key=lambda row: tuple([-x for x in row["sort_vector"]]) + (row["source_id"],))
    selected = ranked[0]
    result = {
        "schema": SELECTION_SCHEMA,
        "version": APP_VERSION,
        "jurisdiction": jurisdiction or None,
        "region": region,
        "concept_id": concept_id,
        "selected_source_id": selected["source_id"],
        "selected_source": selected["source"],
        "selection_components": {
            "semantic_compatibility": "required-before-ranking",
            "declared_precedence_rule": precedence,
            "sort_vector": selected["sort_vector"],
            "authority_class": selected["source"].get("authority_class"),
            "freshness_state": selected["candidate"].get("freshness_state", "unknown"),
            "record_status": selected["candidate"].get("record_status", "unknown"),
        },
        "ranked_source_ids": [row["source_id"] for row in ranked],
        "excluded": excluded,
        "trust_profile_applied": apply_trust,
        "authority_mutated_by_trust": False,
        "quality_mutated_by_trust": False,
    }
    result["selection_digest"] = _digest(result)
    return result


def federation_plan(request: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise ValueError("Federation request must be an object")
    jurisdiction = str(request.get("jurisdiction") or "").upper()
    region = str(request.get("region") or "")
    domains = {str(x) for x in request.get("domains") or []}
    languages = {str(x) for x in request.get("languages") or []}
    modes = {str(x) for x in request.get("federation_modes") or []}
    classes = {str(x) for x in request.get("authority_classes") or []}
    country = _country_index().get(jurisdiction) if jurisdiction else None
    if jurisdiction and not country:
        raise ValueError(f"Unknown jurisdiction code: {jurisdiction}")
    resolved_region = region or (country.get("region") if country else "")
    sources = []
    for row in _registry()["sources"]:
        if jurisdiction and not _eligible_for_jurisdiction(row, jurisdiction, resolved_region):
            continue
        if domains and not domains.intersection(row.get("domains") or []):
            continue
        if languages and row.get("languages") and not languages.intersection(row.get("languages") or []):
            continue
        if modes and row.get("federation_mode") not in modes:
            continue
        if classes and row.get("authority_class") not in classes:
            continue
        sources.append(deepcopy(row))
    sources.sort(key=lambda row: (-SCOPE_RANK.get(row.get("scope_type"), 0), -int(_authority_index().get(row.get("authority_class"), {}).get("authority_rank") or 0), row["source_id"]))
    result = {
        "schema": FEDERATION_PLAN_SCHEMA,
        "version": APP_VERSION,
        "jurisdiction": deepcopy(country) if country else None,
        "region": resolved_region or None,
        "requested_domains": sorted(domains),
        "requested_languages": sorted(languages),
        "source_count": len(sources),
        "sources": sources,
        "execution": {
            "network_calls_performed": False,
            "automatic_import_performed": False,
            "automatic_remote_write_performed": False,
            "plan_only": True,
        },
        "boundaries": [
            "Discovery sources describe available datasets but are not observations.",
            "Federation eligibility does not establish semantic compatibility for a requested metric.",
            "User trust choices remain separate from source authority and quality signals.",
        ],
    }
    result["plan_digest"] = _digest(result)
    return result


def compatibility_manifest() -> dict[str, Any]:
    return {
        "ok": True,
        "version": APP_VERSION,
        "v4_35_source_precedence": {"status": "preserved-and-consumed", "semantic_compatibility_first": True},
        "v4_43_capability_registry": {"status": "preserved-and-extended"},
        "v4_46_spatial_evidence": {"status": "preserved", "source_identity_boundary": True},
        "v4_49_live_geospatial": {"status": "preserved", "source_registry_interoperability": True},
        "institutional_federation_v2240": {"status": "preserved", "automatic_remote_fetch": False},
        "network_calls_performed": False,
        "wordpress_role": "thin-shell-and-embed-bridge",
    }
