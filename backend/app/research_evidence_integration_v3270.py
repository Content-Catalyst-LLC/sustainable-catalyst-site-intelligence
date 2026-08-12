"""Research evidence and knowledge integration for Site Intelligence v4.35.13.

This module prepares public-safe research context, provenance manifests, citation
exports, claim/evidence relationship maps, and explicit handoff previews. It does
not remotely deliver packets or publish content. Human confirmation is required.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

from .config import Settings
from .version import APP_VERSION

SCHEMA_VERSION = "sc-site-intelligence-research-evidence-integration/1.0"
RELEASE_ID = f"site-intelligence-v{APP_VERSION}"
POLICY_PATH = Path(__file__).resolve().parents[1] / "data" / "research_evidence_integration_policy_v3270.json"
HTTP_RE = re.compile(r"^https?://", re.I)
SENSITIVE_RE = re.compile(r"(?:api[_-]?key|password|secret|token|authorization|cookie|session|private[_-]?url)", re.I)
RELATIONS = {"supports", "contradicts", "qualifies", "contextualizes"}


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _policy() -> dict[str, Any]:
    payload = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    if payload.get("version") != APP_VERSION:
        raise ValueError("Research integration policy version does not match the application release.")
    return payload


def _text(value: Any, limit: int = 1200) -> str:
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", str(value or "")).strip()[:limit]


def _safe_url(value: Any) -> str:
    value = _text(value, 1800)
    if not HTTP_RE.match(value):
        return ""
    if re.search(r"(?:token|api[_-]?key|authorization)=", value, re.I):
        return value.split("?", 1)[0]
    return value


def _seq(value: Any, limit: int = 200) -> list[Any]:
    return list(value)[:limit] if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)) else []


def _digest(value: Any) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()


def _scan_sensitive(value: Any, path: str = "payload") -> list[str]:
    issues: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if SENSITIVE_RE.search(str(key)):
                issues.append(f"Sensitive field is not allowed: {child_path}")
            issues.extend(_scan_sensitive(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            issues.extend(_scan_sensitive(child, f"{path}[{index}]") )
    return issues


def _record(raw: Mapping[str, Any], index: int) -> dict[str, Any]:
    value = raw.get("value") if "value" in raw else raw.get("value_number")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        value = None
    evidence_class = _text(raw.get("evidence_class") or raw.get("record_type") or "source-note", 80).lower()
    if evidence_class not in set(_policy()["evidence_classes"]):
        evidence_class = "source-note"
    source_snapshot = {
        "source_id": _text(raw.get("source_id") or raw.get("source"), 180),
        "source_url": _safe_url(raw.get("source_url") or raw.get("url")),
        "publisher": _text(raw.get("publisher"), 220),
        "retrieved_at": _text(raw.get("retrieved_at") or raw.get("captured_at") or _now(), 100),
        "observed_at": _text(raw.get("observed_at") or raw.get("period") or raw.get("published_at"), 100),
    }
    normalized = {
        "record_id": _text(raw.get("record_id") or raw.get("id") or f"record-{index+1}", 180),
        "title": _text(raw.get("title") or raw.get("indicator_name") or raw.get("name") or "Evidence record", 320),
        "record_type": _text(raw.get("record_type") or "evidence", 80).lower(),
        "evidence_class": evidence_class,
        "country": _text(raw.get("country") or raw.get("country_code") or raw.get("geography_code"), 20).upper(),
        "geography": _text(raw.get("geography") or raw.get("geography_name"), 180),
        "indicator_id": _text(raw.get("indicator_id") or raw.get("indicator_code"), 180),
        "value": float(value) if value is not None else None,
        "value_text": _text(raw.get("value_text"), 300),
        "unit": _text(raw.get("unit") or raw.get("display_unit"), 120),
        "citation": _text(raw.get("citation"), 1000),
        "excerpt": _text(raw.get("excerpt") or raw.get("summary"), 1800),
        "source_snapshot": source_snapshot,
        "truth_state": _text(raw.get("truth_state") or raw.get("state") or "unknown", 80).lower(),
        "limitations": [_text(item, 500) for item in _seq(raw.get("limitations"), 20) if _text(item, 500)],
    }
    normalized["fingerprint"] = _digest(normalized)
    return normalized


class ResearchEvidenceIntegrationCenter:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.policy = _policy()

    def schema(self) -> dict[str, Any]:
        return {
            "ok": True,
            "version": APP_VERSION,
            "release_id": RELEASE_ID,
            "schema": SCHEMA_VERSION,
            "contract": "research-evidence-and-knowledge-integration",
            "targets": self.policy["targets"],
            "capabilities": [
                "selected-context normalization",
                "source snapshot retention",
                "evidence manifest export",
                "citation export",
                "claim-evidence relationship mapping",
                "Knowledge Library discovery query preparation",
                "Research Librarian question preparation",
                "Workbench quantitative handoff preview",
                "Decision Studio evidence handoff preview",
            ],
            "human_confirmation_required": True,
            "automatic_delivery": False,
            "automatic_publication": False,
            "boundaries": list(self.policy["boundaries"]),
        }

    def context(self, request: Mapping[str, Any] | None = None) -> dict[str, Any]:
        request = dict(request or {})
        issues = _scan_sensitive(request)
        if issues:
            raise ValueError("; ".join(issues[:5]))
        records = [_record(raw, i) for i, raw in enumerate(_seq(request.get("records") or request.get("evidence"), 200)) if isinstance(raw, Mapping)]
        countries = []
        for item in _seq(request.get("countries"), 40):
            code = _text(item, 20).upper()
            if code and code not in countries:
                countries.append(code)
        for row in records:
            if row["country"] and row["country"] not in countries:
                countries.append(row["country"])
        context = {
            "title": _text(request.get("title") or "Site Intelligence research context", 280),
            "question": _text(request.get("question") or request.get("research_question"), 1800),
            "route": _text(request.get("route") or request.get("workspace"), 80).lower(),
            "countries": countries[:40],
            "indicator_ids": sorted({row["indicator_id"] for row in records if row["indicator_id"]}),
            "record_ids": [row["record_id"] for row in records],
            "records": records,
            "evidence_gaps": [_text(item, 600) for item in _seq(request.get("evidence_gaps") or request.get("gaps"), 50) if _text(item, 600)],
            "saved_view": _safe_url(request.get("saved_view") or request.get("url")),
            "captured_at": _text(request.get("captured_at") or _now(), 100),
        }
        context["fingerprint"] = _digest(context)
        return {"ok": True, "version": APP_VERSION, "schema": SCHEMA_VERSION, "contract": "research-context", "context": context, "boundaries": list(self.policy["boundaries"])}

    def manifest(self, request: Mapping[str, Any] | None = None) -> dict[str, Any]:
        context = self.context(request)["context"]
        rows = context["records"]
        manifest = {
            "title": context["title"],
            "question": context["question"],
            "countries": context["countries"],
            "captured_at": context["captured_at"],
            "context_fingerprint": context["fingerprint"],
            "records": [{
                "record_id": row["record_id"], "fingerprint": row["fingerprint"], "evidence_class": row["evidence_class"],
                "truth_state": row["truth_state"], "source_snapshot": row["source_snapshot"], "limitations": row["limitations"],
            } for row in rows],
        }
        manifest["fingerprint"] = _digest(manifest)
        return {"ok": True, "version": APP_VERSION, "schema": SCHEMA_VERSION, "contract": "research-evidence-manifest", "manifest": manifest, "record_count": len(rows)}

    def citations(self, request: Mapping[str, Any] | None = None) -> dict[str, Any]:
        context = self.context(request)["context"]
        citations: list[dict[str, Any]] = []
        seen: set[str] = set()
        for row in context["records"]:
            snapshot = row["source_snapshot"]
            key = snapshot["source_url"] or snapshot["source_id"] or row["record_id"]
            if key in seen:
                continue
            seen.add(key)
            label = row["citation"] or " · ".join(part for part in [snapshot["publisher"], row["title"], snapshot["observed_at"]] if part)
            citations.append({
                "record_id": row["record_id"], "label": label or row["title"], "source_id": snapshot["source_id"],
                "source_url": snapshot["source_url"], "publisher": snapshot["publisher"], "observed_at": snapshot["observed_at"],
                "retrieved_at": snapshot["retrieved_at"], "record_fingerprint": row["fingerprint"],
            })
        payload = {"citations": citations, "context_fingerprint": context["fingerprint"]}
        return {"ok": True, "version": APP_VERSION, "schema": SCHEMA_VERSION, "contract": "research-citation-export", **payload, "fingerprint": _digest(payload)}

    def claim_map(self, request: Mapping[str, Any] | None = None) -> dict[str, Any]:
        source = dict(request or {})
        context = self.context(source)["context"]
        claims: list[dict[str, Any]] = []
        for index, raw in enumerate(_seq(source.get("claims"), 100)):
            if not isinstance(raw, Mapping):
                continue
            claim_id = _text(raw.get("claim_id") or raw.get("id") or f"claim-{index+1}", 160)
            text = _text(raw.get("claim") or raw.get("text"), 1800)
            if not text:
                continue
            claims.append({"claim_id": claim_id, "claim": text, "status": _text(raw.get("status") or "unresolved", 80).lower()})
        valid_record_ids = {row["record_id"] for row in context["records"]}
        valid_claim_ids = {row["claim_id"] for row in claims}
        relationships: list[dict[str, Any]] = []
        for raw in _seq(source.get("relationships"), 300):
            if not isinstance(raw, Mapping):
                continue
            claim_id = _text(raw.get("claim_id"), 160)
            record_id = _text(raw.get("record_id") or raw.get("evidence_id"), 180)
            relation = _text(raw.get("relation") or "contextualizes", 80).lower()
            if claim_id not in valid_claim_ids or record_id not in valid_record_ids or relation not in RELATIONS:
                continue
            relationships.append({"claim_id": claim_id, "record_id": record_id, "relation": relation, "note": _text(raw.get("note"), 900)})
        payload = {"claims": claims, "records": context["records"], "relationships": relationships, "automatic_resolution": False, "human_review_required": True}
        return {"ok": True, "version": APP_VERSION, "schema": SCHEMA_VERSION, "contract": "claim-evidence-map", **payload, "fingerprint": _digest(payload), "boundaries": list(self.policy["boundaries"])}

    def discovery_plan(self, request: Mapping[str, Any] | None = None) -> dict[str, Any]:
        context = self.context(request)["context"]
        terms: list[str] = []
        for value in [context["question"], *context["countries"], *context["indicator_ids"]]:
            token = _text(value, 300)
            if token and token not in terms:
                terms.append(token)
        plan = {
            "target": "knowledge-library",
            "query_terms": terms[:20],
            "filters": {"countries": context["countries"], "indicator_ids": context["indicator_ids"]},
            "verified_matches": [],
            "match_state": "not-executed",
            "requires_library_index": True,
        }
        plan["fingerprint"] = _digest(plan)
        return {"ok": True, "version": APP_VERSION, "schema": SCHEMA_VERSION, "contract": "knowledge-library-discovery-plan", "plan": plan, "statement": "This prepares a Knowledge Library query; it does not claim that any document match was executed or verified."}

    def handoff_preview(self, target: str, request: Mapping[str, Any] | None = None) -> dict[str, Any]:
        target = _text(target, 80).lower()
        if target not in self.policy["targets"]:
            raise KeyError(target)
        context = self.context(request)["context"]
        records = context["records"]
        source_ids = sorted({row["source_snapshot"]["source_id"] for row in records if row["source_snapshot"]["source_id"]})
        evidence_ids = [row["record_id"] for row in records]
        title = context["title"]
        if target == "research-librarian":
            payload = {"question": context["question"] or title, "scope": {"countries": context["countries"], "indicator_ids": context["indicator_ids"], "evidence_gaps": context["evidence_gaps"]}, "evidence_ids": evidence_ids, "provenance": {"context_fingerprint": context["fingerprint"], "source_ids": source_ids}}
        elif target == "knowledge-library":
            payload = {"title": title, "publication_id": f"research-context:{context['fingerprint'][:16]}", "source_ids": source_ids, "discovery_query": self.discovery_plan(request)["plan"], "provenance": {"context_fingerprint": context["fingerprint"], "record_ids": evidence_ids}}
        elif target == "workbench":
            quantitative = [{"record_id": row["record_id"], "indicator_id": row["indicator_id"], "country": row["country"], "value": row["value"], "unit": row["unit"], "record_fingerprint": row["fingerprint"]} for row in records if row["value"] is not None]
            payload = {"title": title, "question": context["question"], "datasets": quantitative, "assumptions": _seq((request or {}).get("assumptions"), 50), "provenance": {"context_fingerprint": context["fingerprint"], "source_ids": source_ids}}
        else:
            payload = {"title": title, "scenarios": _seq((request or {}).get("scenarios"), 40), "evidence_ids": evidence_ids, "uncertainties": _seq((request or {}).get("uncertainties"), 60), "assumptions": _seq((request or {}).get("assumptions"), 60), "provenance": {"context_fingerprint": context["fingerprint"], "source_ids": source_ids}}
        packet = {
            "target": target,
            "target_label": self.policy["targets"][target]["label"],
            "packet_type": self.policy["targets"][target]["packet_type"],
            "payload": payload,
            "source_record_ids": evidence_ids,
            "preview_only": True,
            "delivery_attempted": False,
            "delivery_verified": False,
            "human_confirmation_required": True,
            "publication_allowed": False,
            "created_at": _now(),
        }
        packet["packet_fingerprint"] = _digest(packet)
        return {"ok": True, "version": APP_VERSION, "release_id": RELEASE_ID, "schema": SCHEMA_VERSION, "contract": "research-product-handoff-preview", "packet": packet, "boundaries": list(self.policy["boundaries"])}


def public_research_integration(settings: Settings) -> dict[str, Any]:
    return ResearchEvidenceIntegrationCenter(settings).schema()


def public_research_context(settings: Settings, request: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return ResearchEvidenceIntegrationCenter(settings).context(request)


def public_research_manifest(settings: Settings, request: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return ResearchEvidenceIntegrationCenter(settings).manifest(request)


def public_research_citations(settings: Settings, request: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return ResearchEvidenceIntegrationCenter(settings).citations(request)


def public_research_claim_map(settings: Settings, request: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return ResearchEvidenceIntegrationCenter(settings).claim_map(request)


def public_knowledge_library_discovery(settings: Settings, request: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return ResearchEvidenceIntegrationCenter(settings).discovery_plan(request)


def public_research_handoff_preview(settings: Settings, target: str, request: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return ResearchEvidenceIntegrationCenter(settings).handoff_preview(target, request)
