"""Research Paths, Saved Investigations, and Briefing Workflows for v2.10.0.

The service validates and packages user-created research records statelessly. The
browser owns persistence. No account, hosted profile, paid queue, or server-side
research-history database is required.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
import re
from typing import Any, Mapping, Sequence

VERSION = "2.10.0"
RELEASE_SCHEMA = "sc-site-intelligence-research-workflows/1.0"
INVESTIGATION_SCHEMA = "sc-site-intelligence-investigation/1.0"
EVIDENCE_SET_SCHEMA = "sc-site-intelligence-evidence-set/1.0"
BRIEFING_SCHEMA = "sc-site-intelligence-briefing-workflow/1.0"
HANDOFF_SCHEMA = "sc-site-intelligence-product-handoff/1.0"
ALLOWED_STATUSES = {"draft", "active", "review", "complete", "archived"}
ALLOWED_TARGETS = {"knowledge-library", "research-librarian", "workbench", "decision-studio"}
ALLOWED_EVIDENCE_CLASSES = {
    "official-statistic", "scientific-observation", "forecast", "legal-record",
    "humanitarian-report", "event-record", "derived-analysis", "source-note",
}
SENSITIVE_RE = re.compile(r"(?:api[_-]?key|password|secret|token|authorization|cookie|session|private[_-]?url|stack[_-]?trace|environment)", re.I)


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _text(value: Any, limit: int = 500, *, required: bool = False) -> str:
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", str(value or "")).strip()
    text = " ".join(text.split())
    if required and not text:
        raise ValueError("A required text field is empty.")
    return text[:limit]


def _url(value: Any) -> str:
    text = _text(value, 1200)
    if not text.lower().startswith(("https://", "http://")):
        return ""
    if re.search(r"(?:api[_-]?key|access[_-]?token|token|authorization)=", text, re.I):
        return text.split("?", 1)[0]
    return text


def _list(value: Any, *, limit: int, item_limit: int = 120, upper: bool = False) -> list[str]:
    if isinstance(value, str):
        raw = [part.strip() for part in value.split(",")]
    elif isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        raw = list(value)
    else:
        raw = []
    out: list[str] = []
    for item in raw:
        text = _text(item, item_limit)
        if upper:
            text = text.upper()
        if text and text not in out:
            out.append(text)
    return out[:limit]


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


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def workflow_config(settings: Any = None) -> dict[str, Any]:
    enabled = getattr(settings, "research_workflows_enabled", None)
    if enabled is None:
        enabled = os.getenv("SC_SI_RESEARCH_WORKFLOWS_ENABLED", "true").lower() in {"1", "true", "yes", "on"}
    return {
        "enabled": bool(enabled),
        "max_investigations": int(getattr(settings, "research_workflows_max_investigations", 30)),
        "max_evidence_items": int(getattr(settings, "research_workflows_max_evidence_items", 120)),
        "max_notes": int(getattr(settings, "research_workflows_max_notes", 80)),
    }


def _normalize_note(value: Mapping[str, Any], index: int) -> dict[str, Any]:
    return {
        "id": _text(value.get("id") or f"note-{index+1}", 120),
        "title": _text(value.get("title") or "Research note", 180),
        "body": _text(value.get("body") or value.get("text"), 5000),
        "created_at": _text(value.get("created_at") or _now(), 80),
        "updated_at": _text(value.get("updated_at") or value.get("created_at") or _now(), 80),
    }


def _normalize_evidence(value: Mapping[str, Any], index: int) -> dict[str, Any]:
    evidence_class = _text(value.get("evidence_class") or "source-note", 80).lower()
    if evidence_class not in ALLOWED_EVIDENCE_CLASSES:
        evidence_class = "source-note"
    numeric = value.get("value_number")
    if not isinstance(numeric, (int, float)) or isinstance(numeric, bool):
        numeric = None
    return {
        "id": _text(value.get("id") or f"evidence-{index+1}", 120),
        "title": _text(value.get("title") or value.get("indicator_name") or "Evidence record", 300),
        "domain": _text(value.get("domain") or "general", 100).lower(),
        "evidence_class": evidence_class,
        "source_id": _text(value.get("source_id") or value.get("source"), 180),
        "source_url": _url(value.get("source_url") or value.get("url")),
        "citation": _text(value.get("citation"), 800),
        "observed_at": _text(value.get("observed_at") or value.get("period") or value.get("published_at"), 100),
        "geography_code": _text(value.get("geography_code") or value.get("country_code"), 20).upper(),
        "authority_type": _text(value.get("authority_type"), 160),
        "value_number": float(numeric) if numeric is not None else None,
        "value_text": _text(value.get("value_text"), 300),
        "unit": _text(value.get("unit"), 120),
        "excerpt": _text(value.get("excerpt") or value.get("quote"), 1600),
        "research_note": _text(value.get("research_note") or value.get("note"), 1800),
        "captured_at": _text(value.get("captured_at") or _now(), 80),
    }


def normalize_investigation(payload: Mapping[str, Any], settings: Any = None) -> dict[str, Any]:
    issues = _scan_sensitive(payload)
    if issues:
        raise ValueError("; ".join(issues[:5]))
    cfg = workflow_config(settings)
    if not cfg["enabled"]:
        raise ValueError("Research workflows are disabled.")
    status = _text(payload.get("status") or "draft", 40).lower()
    if status not in ALLOWED_STATUSES:
        raise ValueError("Unsupported investigation status.")
    evidence_raw = payload.get("evidence") or payload.get("evidence_items") or []
    notes_raw = payload.get("notes") or []
    checkpoints_raw = payload.get("checkpoints") or []
    views_raw = payload.get("saved_views") or payload.get("views") or []
    if not isinstance(evidence_raw, list) or not isinstance(notes_raw, list):
        raise ValueError("evidence and notes must be lists.")
    evidence = [_normalize_evidence(item, i) for i, item in enumerate(evidence_raw[:cfg["max_evidence_items"]]) if isinstance(item, Mapping)]
    notes = [_normalize_note(item, i) for i, item in enumerate(notes_raw[:cfg["max_notes"]]) if isinstance(item, Mapping)]
    checkpoints = []
    for i, item in enumerate(checkpoints_raw[:50] if isinstance(checkpoints_raw, list) else []):
        if isinstance(item, Mapping):
            checkpoints.append({"id": _text(item.get("id") or f"checkpoint-{i+1}", 120), "label": _text(item.get("label") or item.get("title") or "Checkpoint", 240), "note": _text(item.get("note"), 1200), "created_at": _text(item.get("created_at") or _now(), 80)})
    views = []
    for i, item in enumerate(views_raw[:60] if isinstance(views_raw, list) else []):
        if isinstance(item, Mapping):
            views.append({"id": _text(item.get("id") or f"view-{i+1}", 120), "title": _text(item.get("title") or "Saved public view", 240), "route": _text(item.get("route"), 80), "url": _url(item.get("url")), "captured_at": _text(item.get("captured_at") or _now(), 80)})
    normalized = {
        "schema": INVESTIGATION_SCHEMA,
        "id": _text(payload.get("id") or f"investigation-{_digest(payload)[:12]}", 140),
        "title": _text(payload.get("title"), 240, required=True),
        "research_question": _text(payload.get("research_question") or payload.get("question"), 1600),
        "status": status,
        "tags": _list(payload.get("tags"), limit=20, item_limit=80),
        "countries": _list(payload.get("countries"), limit=30, item_limit=20, upper=True),
        "regions": _list(payload.get("regions"), limit=20, item_limit=120),
        "domains": _list(payload.get("domains"), limit=20, item_limit=100),
        "date_start": _text(payload.get("date_start"), 40),
        "date_end": _text(payload.get("date_end"), 40),
        "created_at": _text(payload.get("created_at") or _now(), 80),
        "updated_at": _text(payload.get("updated_at") or _now(), 80),
        "evidence": evidence,
        "notes": notes,
        "checkpoints": checkpoints,
        "saved_views": views,
        "privacy": {"storage": "browser-local", "server_persistence": False, "account_required": False},
    }
    normalized["integrity"] = {"algorithm": "sha256", "digest": _digest(normalized)}
    return normalized


def build_workflow_overview(settings: Any = None) -> dict[str, Any]:
    cfg = workflow_config(settings)
    return {
        "ok": True,
        "schema": RELEASE_SCHEMA,
        "version": VERSION,
        "release_name": "Research Paths, Saved Investigations, and Briefing Workflows",
        "generated_at": _now(),
        "integration": {"state": "ready" if cfg["enabled"] else "disabled", "browser_local": True, "server_persistence": False, "credential_exposed": False},
        "limits": cfg,
        "capabilities": ["research paths", "saved investigations", "evidence sets", "notes and checkpoints", "briefing packets", "structured product handoffs", "JSON import and export"],
        "responsible_use": ["User notes remain browser-local unless explicitly exported.", "Packets preserve evidence classes and source context.", "The workflow does not generate factual claims, legal conclusions, rankings, or forecasts."],
    }


def build_workflow_schema(settings: Any = None) -> dict[str, Any]:
    return {
        "ok": True, "version": VERSION, "schema": INVESTIGATION_SCHEMA,
        "statuses": sorted(ALLOWED_STATUSES), "evidence_classes": sorted(ALLOWED_EVIDENCE_CLASSES),
        "handoff_targets": sorted(ALLOWED_TARGETS), "limits": workflow_config(settings),
        "required": ["title"], "storage": "browser-local",
    }


def validate_investigation(payload: Mapping[str, Any], settings: Any = None) -> dict[str, Any]:
    record = normalize_investigation(payload, settings)
    return {"ok": True, "version": VERSION, "schema": INVESTIGATION_SCHEMA, "valid": True, "investigation": record, "warnings": []}


def build_evidence_set(payload: Mapping[str, Any], settings: Any = None) -> dict[str, Any]:
    record = normalize_investigation(payload, settings)
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in record["evidence"]:
        grouped.setdefault(item["domain"], []).append(item)
    result = {
        "schema": EVIDENCE_SET_SCHEMA, "version": VERSION, "generated_at": _now(),
        "investigation_id": record["id"], "title": record["title"], "research_question": record["research_question"],
        "evidence_count": len(record["evidence"]), "domains": grouped,
        "source_count": len({item["source_id"] for item in record["evidence"] if item["source_id"]}),
        "methodology": {"deduplication": "none beyond user-managed record identifiers", "claim_generation": False, "evidence_classes_preserved": True},
    }
    result["integrity"] = {"algorithm": "sha256", "digest": _digest(result)}
    return result


def build_briefing_packet(payload: Mapping[str, Any], settings: Any = None) -> dict[str, Any]:
    record = normalize_investigation(payload, settings)
    evidence_set = build_evidence_set(payload, settings)
    sections = []
    for domain, items in evidence_set["domains"].items():
        sections.append({"id": domain, "title": domain.replace("-", " ").title(), "evidence_count": len(items), "evidence": items, "editorial_prompt": f"Summarize the {domain} evidence without exceeding what the cited records establish."})
    packet = {
        "schema": BRIEFING_SCHEMA, "version": VERSION, "generated_at": _now(),
        "title": record["title"], "research_question": record["research_question"], "status": record["status"],
        "scope": {"countries": record["countries"], "regions": record["regions"], "domains": record["domains"], "date_start": record["date_start"], "date_end": record["date_end"]},
        "briefing_outline": ["Executive context", "Evidence by domain", "Known gaps and conflicts", "Implications requiring human review", "Sources and methodology"],
        "sections": sections, "notes": record["notes"], "checkpoints": record["checkpoints"], "saved_views": record["saved_views"],
        "evidence_summary": {"records": evidence_set["evidence_count"], "sources": evidence_set["source_count"], "domains": len(evidence_set["domains"])},
        "editorial_controls": {"human_review_required": True, "automatic_claim_generation": False, "legal_advice": False, "forecasting": False, "ranking": False},
    }
    packet["integrity"] = {"algorithm": "sha256", "digest": _digest(packet)}
    return packet


def build_product_handoff(payload: Mapping[str, Any], target: str, settings: Any = None) -> dict[str, Any]:
    target = _text(target, 80).lower()
    if target not in ALLOWED_TARGETS:
        raise ValueError("Unsupported handoff target.")
    record = normalize_investigation(payload, settings)
    instructions = {
        "knowledge-library": "Create or update a source-aware research collection without publishing private notes automatically.",
        "research-librarian": "Use the question, scope, and evidence identifiers to continue source discovery.",
        "workbench": "Use numeric evidence only for explicit calculations with original units and periods preserved.",
        "decision-studio": "Create a reviewable decision packet that separates evidence, assumptions, scenarios, and recommendations.",
    }
    handoff = {
        "schema": HANDOFF_SCHEMA, "version": VERSION, "generated_at": _now(), "target": target,
        "instruction": instructions[target],
        "investigation": record,
        "constraints": {"credentials_included": False, "server_persistence": False, "automatic_publication": False, "human_review_required": True},
    }
    handoff["integrity"] = {"algorithm": "sha256", "digest": _digest(handoff)}
    return handoff


def build_workflow_diagnostics(settings: Any = None) -> dict[str, Any]:
    cfg = workflow_config(settings)
    return {"ok": True, "version": VERSION, "enabled": cfg["enabled"], "storage": "browser-local", "server_persistence": False, "paid_service_required": False, "credential_exposed": False, "schemas": [INVESTIGATION_SCHEMA, EVIDENCE_SET_SCHEMA, BRIEFING_SCHEMA, HANDOFF_SCHEMA], "limits": cfg}
