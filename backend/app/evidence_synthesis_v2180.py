from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import csv
import hashlib
import io
import json
import re
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

from .config import Settings

RELEASE_VERSION = "3.17.0"
SCHEMA_VERSION = "sc-site-intelligence-evidence-synthesis/1.0"
CLAIM_SCHEMA = "sc-site-intelligence-claim/1.0"
EVIDENCE_SCHEMA = "sc-site-intelligence-claim-evidence/1.0"
REVIEW_SCHEMA = "sc-site-intelligence-claim-review/1.0"
SYNTHESIS_SCHEMA = "sc-site-intelligence-synthesis/1.0"
UNCERTAINTY_SCHEMA = "sc-site-intelligence-uncertainty/1.0"
RELATIONSHIPS = {"supports", "qualifies", "conflicts", "context"}
CLAIM_TYPES = {"factual", "interpretive", "causal", "projection", "normative"}
CLAIM_STATUS = {"draft", "in_review", "approved", "rejected", "superseded", "unresolved"}
DECISIONS = {"approve", "reject", "needs_revision", "unresolved", "supersede"}
VISIBILITY = {"public", "private"}
UNCERTAINTY_TYPES = {"measurement", "method", "source", "comparability", "causal", "forecast", "coverage", "other"}
_SECRET = re.compile(r"(?:token|secret|password|authorization|api[_-]?key|email|phone|user[_-]?id)", re.I)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def _resolve(value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else Path(__file__).resolve().parents[2] / path


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _safe_id(value: str, fallback: str = "record") -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_.-]+", "-", str(value or "").strip()).strip("-.")
    return (cleaned or fallback)[:140]


def _read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default


def _write_jsonl(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n")


def _read_jsonl(path: Path, limit: int) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()[-limit:]
    except (FileNotFoundError, OSError):
        return []
    rows: list[dict[str, Any]] = []
    for line in lines:
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            rows.append(item)
    return rows


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): ("[redacted]" if _SECRET.search(str(k)) else _redact(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


def _clean_list(values: Any, maximum: int = 100, length: int = 240) -> list[str]:
    if not isinstance(values, list):
        return []
    return [str(item).strip()[:length] for item in values[:maximum] if str(item).strip()]


class EvidenceSynthesisCenter:
    def __init__(self, settings: Settings, now_fn: Callable[[], datetime] = _utc_now) -> None:
        self.settings = settings
        self.now_fn = now_fn
        self.claims_path = _resolve(settings.evidence_synthesis_claims_path)
        self.evidence_path = _resolve(settings.evidence_synthesis_evidence_path)
        self.reviews_path = _resolve(settings.evidence_synthesis_reviews_path)
        self.syntheses_path = _resolve(settings.evidence_synthesis_syntheses_path)
        self.uncertainty_path = _resolve(settings.evidence_synthesis_uncertainty_path)
        self.policy = _read_json(_resolve(settings.evidence_synthesis_policy_path), {})
        self.max_records = settings.evidence_synthesis_max_records

    def _rows(self, path: Path) -> list[dict[str, Any]]:
        return _read_jsonl(path, self.max_records)

    def _latest_claims(self, public: bool = False) -> list[dict[str, Any]]:
        latest: dict[str, dict[str, Any]] = {}
        for item in self._rows(self.claims_path):
            latest[str(item.get("claim_id"))] = item
        rows = list(latest.values())
        if public:
            rows = [item for item in rows if item.get("visibility") == "public" and item.get("status") == "approved"]
        return sorted(rows, key=lambda item: (str(item.get("title")), str(item.get("claim_id"))))

    def _claim(self, claim_id: str, public: bool = False) -> dict[str, Any]:
        matches = [item for item in self._rows(self.claims_path) if item.get("claim_id") == claim_id]
        if public:
            matches = [item for item in matches if item.get("visibility") == "public" and item.get("status") == "approved"]
        if not matches:
            raise KeyError(claim_id)
        return matches[-1]

    def register_claim(self, request: dict[str, Any]) -> dict[str, Any]:
        raw_id = str(request.get("claim_id") or "").strip()
        title = str(request.get("title") or "").strip()
        statement = str(request.get("statement") or "").strip()
        claim_type = str(request.get("claim_type") or "factual").strip().lower()
        status = str(request.get("status") or "draft").strip().lower()
        visibility = str(request.get("visibility") or "private").strip().lower()
        if not raw_id or not title or not statement:
            raise ValueError("claim_id, title, and statement are required.")
        if claim_type not in CLAIM_TYPES or status not in CLAIM_STATUS or visibility not in VISIBILITY:
            raise ValueError("Unsupported claim_type, status, or visibility.")
        if status == "approved" and not bool(request.get("human_review_confirmed")):
            raise ValueError("Approved claims require explicit human_review_confirmed=true.")
        now = self.now_fn()
        claim = {
            "schema": CLAIM_SCHEMA,
            "release_version": RELEASE_VERSION,
            "claim_id": _safe_id(raw_id),
            "title": title[:240],
            "statement": statement[:5000],
            "claim_type": claim_type,
            "scope": str(request.get("scope") or "")[:1000],
            "status": status,
            "visibility": visibility,
            "source_claim_ids": _clean_list(request.get("source_claim_ids")),
            "tags": _clean_list(request.get("tags"), 50, 100),
            "human_review_required": True,
            "human_review_confirmed": bool(request.get("human_review_confirmed")),
            "causation_not_assumed": claim_type != "causal" or bool(request.get("causal_basis_documented")),
            "created_at": _iso(now),
            "updated_at": _iso(now),
        }
        claim["claim_sha256"] = _digest({k: v for k, v in claim.items() if k != "claim_sha256"})
        _write_jsonl(self.claims_path, claim)
        return {"ok": True, "claim": claim}

    def add_evidence(self, request: dict[str, Any]) -> dict[str, Any]:
        claim_id = _safe_id(str(request.get("claim_id") or ""))
        self._claim(claim_id)
        raw_id = str(request.get("evidence_id") or "").strip()
        relation = str(request.get("relationship") or "context").strip().lower()
        source_id = str(request.get("source_id") or "").strip()
        source_title = str(request.get("source_title") or "").strip()
        if not raw_id or not source_id or not source_title:
            raise ValueError("evidence_id, source_id, and source_title are required.")
        if relation not in RELATIONSHIPS:
            raise ValueError("Unsupported evidence relationship.")
        visibility = str(request.get("visibility") or "private").strip().lower()
        if visibility not in VISIBILITY:
            raise ValueError("Unsupported visibility.")
        excerpt = str(request.get("excerpt") or "").strip()[: self.settings.evidence_synthesis_max_excerpt_chars]
        record = {
            "schema": EVIDENCE_SCHEMA,
            "release_version": RELEASE_VERSION,
            "evidence_id": _safe_id(raw_id),
            "claim_id": claim_id,
            "relationship": relation,
            "source_id": source_id[:240],
            "source_title": source_title[:500],
            "source_url": str(request.get("source_url") or "")[:2000],
            "source_type": str(request.get("source_type") or "document")[:120],
            "authority_context": str(request.get("authority_context") or "")[:1000],
            "methodology_context": str(request.get("methodology_context") or "")[:1500],
            "excerpt": excerpt,
            "locator": str(request.get("locator") or "")[:500],
            "observed_at": str(request.get("observed_at") or "")[:120],
            "visibility": visibility,
            "limitations": _clean_list(request.get("limitations"), 30, 400),
            "redacted_metadata": _redact(request.get("metadata") or {}),
            "captured_at": _iso(self.now_fn()),
            "evidence_not_conclusion": True,
        }
        record["evidence_sha256"] = _digest({k: v for k, v in record.items() if k != "evidence_sha256"})
        _write_jsonl(self.evidence_path, record)
        return {"ok": True, "evidence": record}

    def record_uncertainty(self, request: dict[str, Any]) -> dict[str, Any]:
        claim_id = _safe_id(str(request.get("claim_id") or ""))
        self._claim(claim_id)
        category = str(request.get("category") or "other").strip().lower()
        description = str(request.get("description") or "").strip()
        if category not in UNCERTAINTY_TYPES or not description:
            raise ValueError("A supported uncertainty category and description are required.")
        record = {
            "schema": UNCERTAINTY_SCHEMA,
            "release_version": RELEASE_VERSION,
            "uncertainty_id": _safe_id(str(request.get("uncertainty_id") or uuid4())),
            "claim_id": claim_id,
            "category": category,
            "severity": str(request.get("severity") or "review").strip().lower()[:60],
            "description": description[:2500],
            "mitigation": str(request.get("mitigation") or "")[:1500],
            "resolved": bool(request.get("resolved")),
            "visibility": str(request.get("visibility") or "private").lower() if str(request.get("visibility") or "private").lower() in VISIBILITY else "private",
            "recorded_at": _iso(self.now_fn()),
        }
        record["uncertainty_sha256"] = _digest({k: v for k, v in record.items() if k != "uncertainty_sha256"})
        _write_jsonl(self.uncertainty_path, record)
        return {"ok": True, "uncertainty": record}

    def review_claim(self, request: dict[str, Any]) -> dict[str, Any]:
        claim_id = _safe_id(str(request.get("claim_id") or ""))
        claim = self._claim(claim_id)
        decision = str(request.get("decision") or "").strip().lower()
        rationale = str(request.get("rationale") or "").strip()
        role = str(request.get("reviewer_role") or "").strip()
        if decision not in DECISIONS or not rationale or not role:
            raise ValueError("decision, rationale, and reviewer_role are required.")
        evidence = self._evidence(claim_id)
        if decision == "approve" and not evidence:
            raise ValueError("A claim cannot be approved without evidence records.")
        review = {
            "schema": REVIEW_SCHEMA,
            "release_version": RELEASE_VERSION,
            "review_id": _safe_id(str(request.get("review_id") or uuid4())),
            "claim_id": claim_id,
            "decision": decision,
            "reviewer_role": role[:200],
            "rationale": rationale[:4000],
            "evidence_ids_reviewed": _clean_list(request.get("evidence_ids_reviewed")) or [item["evidence_id"] for item in evidence],
            "conflicts_resolved": bool(request.get("conflicts_resolved")),
            "reviewed_at": _iso(self.now_fn()),
            "human_decision": True,
        }
        review["review_sha256"] = _digest({k: v for k, v in review.items() if k != "review_sha256"})
        _write_jsonl(self.reviews_path, review)
        mapped = {"approve": "approved", "reject": "rejected", "needs_revision": "in_review", "unresolved": "unresolved", "supersede": "superseded"}[decision]
        updated = dict(claim)
        updated.update({"status": mapped, "human_review_confirmed": decision == "approve", "updated_at": _iso(self.now_fn()), "last_review_id": review["review_id"]})
        updated["claim_sha256"] = _digest({k: v for k, v in updated.items() if k != "claim_sha256"})
        _write_jsonl(self.claims_path, updated)
        return {"ok": True, "review": review, "claim": updated}

    def _evidence(self, claim_id: str, public: bool = False) -> list[dict[str, Any]]:
        rows = [item for item in self._rows(self.evidence_path) if item.get("claim_id") == claim_id]
        if public:
            rows = [item for item in rows if item.get("visibility") == "public"]
        return rows

    def _uncertainties(self, claim_id: str, public: bool = False) -> list[dict[str, Any]]:
        rows = [item for item in self._rows(self.uncertainty_path) if item.get("claim_id") == claim_id]
        if public:
            rows = [item for item in rows if item.get("visibility") == "public"]
        return rows

    def contradiction_review(self, claim_id: str, public: bool = False) -> dict[str, Any]:
        claim = self._claim(claim_id, public=public)
        evidence = self._evidence(claim_id, public=public)
        counts = Counter(str(item.get("relationship")) for item in evidence)
        conflicts = [item for item in evidence if item.get("relationship") == "conflicts"]
        support = [item for item in evidence if item.get("relationship") == "supports"]
        qualifying = [item for item in evidence if item.get("relationship") == "qualifies"]
        status = "none"
        if conflicts and support:
            status = "review_required"
        elif conflicts:
            status = "conflicting_only"
        completeness = "insufficient" if not support else ("qualified" if qualifying or conflicts else "supported")
        return {
            "schema": SCHEMA_VERSION,
            "release_version": RELEASE_VERSION,
            "claim": claim,
            "counts": dict(counts),
            "contradiction_status": status,
            "evidence_completeness": completeness,
            "supporting_evidence_ids": [item["evidence_id"] for item in support],
            "conflicting_evidence_ids": [item["evidence_id"] for item in conflicts],
            "qualifying_evidence_ids": [item["evidence_id"] for item in qualifying],
            "causation_not_inferred": True,
            "human_resolution_required": bool(conflicts),
        }

    def synthesize(self, request: dict[str, Any]) -> dict[str, Any]:
        claim_id = _safe_id(str(request.get("claim_id") or ""))
        claim = self._claim(claim_id)
        evidence = self._evidence(claim_id)
        if not evidence:
            raise ValueError("Synthesis requires at least one evidence record.")
        review = self.contradiction_review(claim_id)
        uncertainties = self._uncertainties(claim_id)
        support = [e for e in evidence if e["relationship"] == "supports"]
        conflicts = [e for e in evidence if e["relationship"] == "conflicts"]
        qualifies = [e for e in evidence if e["relationship"] == "qualifies"]
        if conflicts and support:
            conclusion = "contested"
        elif conflicts:
            conclusion = "not_supported"
        elif support and (qualifies or uncertainties):
            conclusion = "supported_with_qualifications"
        elif support:
            conclusion = "supported"
        else:
            conclusion = "insufficient"
        citations = [
            {"evidence_id": item["evidence_id"], "source_id": item["source_id"], "source_title": item["source_title"], "relationship": item["relationship"], "locator": item.get("locator", "")}
            for item in evidence
        ]
        narrative = f"Claim review outcome: {conclusion.replace('_', ' ')}. {len(support)} supporting, {len(qualifies)} qualifying, and {len(conflicts)} conflicting evidence records were reviewed."
        synthesis = {
            "schema": SYNTHESIS_SCHEMA,
            "release_version": RELEASE_VERSION,
            "synthesis_id": _safe_id(str(request.get("synthesis_id") or uuid4())),
            "claim_id": claim_id,
            "claim_statement": claim["statement"],
            "conclusion": conclusion,
            "narrative": narrative,
            "citations": citations,
            "contradiction_status": review["contradiction_status"],
            "uncertainties": [{k: item.get(k) for k in ("uncertainty_id", "category", "severity", "description", "resolved")} for item in uncertainties],
            "visibility": str(request.get("visibility") or "private").lower() if str(request.get("visibility") or "private").lower() in VISIBILITY else "private",
            "approval_status": "approved" if bool(request.get("human_review_confirmed")) else "draft",
            "human_review_required": True,
            "grounded_only": True,
            "ai_assistance": {
                "requested": bool(request.get("ai_assist")),
                "mode": "deterministic-grounded-template",
                "external_model_invoked": False,
                "source_invention_prohibited": True,
                "citation_ids_required": True,
            },
            "created_at": _iso(self.now_fn()),
        }
        if synthesis["approval_status"] == "approved" and claim.get("status") != "approved":
            raise ValueError("Public-ready synthesis requires an approved claim.")
        synthesis["synthesis_sha256"] = _digest({k: v for k, v in synthesis.items() if k != "synthesis_sha256"})
        _write_jsonl(self.syntheses_path, synthesis)
        return {"ok": True, "synthesis": synthesis}

    def claims(self, public: bool = False) -> dict[str, Any]:
        rows = self._latest_claims(public=public)
        return {"schema": SCHEMA_VERSION, "release_version": RELEASE_VERSION, "count": len(rows), "claims": rows}

    def claim_detail(self, claim_id: str, public: bool = False) -> dict[str, Any]:
        claim = self._claim(claim_id, public=public)
        evidence = self._evidence(claim_id, public=public)
        syntheses = [item for item in self._rows(self.syntheses_path) if item.get("claim_id") == claim_id]
        if public:
            syntheses = [item for item in syntheses if item.get("visibility") == "public" and item.get("approval_status") == "approved"]
        return {
            "schema": SCHEMA_VERSION,
            "release_version": RELEASE_VERSION,
            "claim": claim,
            "evidence": evidence,
            "uncertainties": self._uncertainties(claim_id, public=public),
            "syntheses": syntheses,
            "contradiction_review": self.contradiction_review(claim_id, public=public),
        }

    def public_summary(self) -> dict[str, Any]:
        claims = self._latest_claims(public=True)
        public_ids = {item["claim_id"] for item in claims}
        evidence = [item for item in self._rows(self.evidence_path) if item.get("visibility") == "public" and item.get("claim_id") in public_ids]
        syntheses = [item for item in self._rows(self.syntheses_path) if item.get("visibility") == "public" and item.get("approval_status") == "approved" and item.get("claim_id") in public_ids]
        return {
            "schema": SCHEMA_VERSION,
            "release_version": RELEASE_VERSION,
            "title": "Evidence Synthesis, Claims, and Contradiction Review",
            "counts": {"approved_claims": len(claims), "public_evidence": len(evidence), "approved_syntheses": len(syntheses), "conflicting_evidence": sum(1 for item in evidence if item.get("relationship") == "conflicts")},
            "boundaries": list(self.policy.get("boundaries", [])),
            "deterministic_synthesis": True,
            "external_ai_enabled": False,
            "human_review_required": True,
        }

    def methodology(self) -> dict[str, Any]:
        return {"schema": SCHEMA_VERSION, "release_version": RELEASE_VERSION, "policy": self.policy, "relationships": sorted(RELATIONSHIPS), "claim_types": sorted(CLAIM_TYPES), "uncertainty_types": sorted(UNCERTAINTY_TYPES)}

    def diagnostics(self, public: bool = False) -> dict[str, Any]:
        claims = self._latest_claims(public=public)
        claim_ids = {item["claim_id"] for item in claims}
        evidence = [item for item in self._rows(self.evidence_path) if item.get("claim_id") in claim_ids and (not public or item.get("visibility") == "public")]
        return {"schema": SCHEMA_VERSION, "release_version": RELEASE_VERSION, "ok": True, "public": public, "claim_count": len(claims), "evidence_count": len(evidence), "conflict_count": sum(1 for item in evidence if item.get("relationship") == "conflicts"), "storage_mode": "file-backed", "human_review_required": True}

    def control_center(self) -> dict[str, Any]:
        claims = self._latest_claims()
        evidence = self._rows(self.evidence_path)
        reviews = self._rows(self.reviews_path)
        syntheses = self._rows(self.syntheses_path)
        uncertainties = self._rows(self.uncertainty_path)
        return {"schema": SCHEMA_VERSION, "release_version": RELEASE_VERSION, "counts": {"claims": len(claims), "evidence": len(evidence), "reviews": len(reviews), "syntheses": len(syntheses), "uncertainties": len(uncertainties)}, "claims": claims[-100:], "recent_reviews": reviews[-50:], "recent_syntheses": syntheses[-50:], "policy": self.policy}

    def export_packet(self, claim_id: str, public: bool = False) -> dict[str, Any]:
        detail = self.claim_detail(claim_id, public=public)
        packet = {"schema": "sc-site-intelligence-evidence-packet/1.0", "release_version": RELEASE_VERSION, "generated_at": _iso(self.now_fn()), "read_only": True, **detail}
        packet["packet_sha256"] = _digest({k: v for k, v in packet.items() if k != "packet_sha256"})
        out = io.StringIO()
        writer = csv.writer(out)
        writer.writerow(["evidence_id", "relationship", "source_id", "source_title", "locator", "excerpt"])
        for item in detail["evidence"]:
            writer.writerow([item.get("evidence_id"), item.get("relationship"), item.get("source_id"), item.get("source_title"), item.get("locator"), item.get("excerpt")])
        markdown = [f"# {detail['claim']['title']}", "", detail["claim"]["statement"], "", "## Evidence"]
        for item in detail["evidence"]:
            markdown.append(f"- **{item['relationship']}** — {item['source_title']} ({item['source_id']}) {item.get('locator','')}")
        return {"schema": packet["schema"], "release_version": RELEASE_VERSION, "read_only": True, "packet": packet, "csv": out.getvalue(), "markdown": "\n".join(markdown) + "\n"}

    def handoff(self, claim_id: str, destination: str, public: bool = False) -> dict[str, Any]:
        allowed = {"knowledge-library", "research-librarian"}
        if destination not in allowed:
            raise ValueError("Unsupported handoff destination.")
        export = self.export_packet(claim_id, public=public)
        return {"schema": "sc-site-intelligence-evidence-handoff/1.0", "release_version": RELEASE_VERSION, "destination": destination, "read_only": True, "packet": export["packet"], "instructions": "Preserve claim, evidence relationships, contradictions, uncertainty, citations, and human-review status without inventing sources or conclusions."}
