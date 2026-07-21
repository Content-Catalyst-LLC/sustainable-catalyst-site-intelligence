"""Governed editorial workspaces for Live Intelligence briefings.

Site Intelligence v3.13.0 adds assignment, revision history, separation-of-duty
review gates, and provider-neutral publication orchestration. Editorial changes
may refine explanatory copy, but cannot rewrite canonical evidence, claim-source
links, observed values, or provenance. No adapter write is performed here.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any, Callable, Mapping, Sequence
from uuid import uuid4

from .config import Settings
from .version import APP_VERSION

POLICY_SCHEMA_VERSION = "sc-site-intelligence-editorial-workspace-policy/1.0"
WORKSPACE_SCHEMA_VERSION = "sc-site-intelligence-editorial-workspace/1.0"
REVISION_SCHEMA_VERSION = "sc-site-intelligence-editorial-revision/1.0"
REVIEW_SCHEMA_VERSION = "sc-site-intelligence-editorial-review/1.0"
ORCHESTRATION_SCHEMA_VERSION = "sc-site-intelligence-publication-orchestration/1.0"

ALLOWED_ROLES = ("author", "editor", "fact_checker", "legal_reviewer", "publisher")
ALLOWED_ADAPTERS = ("publications", "knowledge_library", "decision_studio", "download")
EDITABLE_FIELDS = ("title", "deck", "executive_summary", "key_observations", "limitations")
PROTECTED_FIELDS = {
    "claims", "evidence", "chronology", "source_count", "claim_count", "source_refs",
    "source_url", "context_url", "value", "formatted_value", "numeric_value",
    "observed_at", "updated_at", "freshness_state", "signal_family", "geography",
}
DENIED_IDENTITY_FIELDS = {
    "email", "email_address", "phone", "phone_number", "ip", "ip_address",
    "cookie", "session_id", "user_agent", "referrer", "recipient", "recipients",
    "subscriber", "subscriber_id", "subscriber_email", "contact_id", "metadata",
}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime | None = None) -> str:
    return (value or _utc_now()).astimezone(timezone.utc).isoformat()


def _safe_text(value: Any, limit: int = 500) -> str:
    return " ".join(str(value or "").split())[:limit]


def _safe_id(value: Any, prefix: str = "item") -> str:
    text = _safe_text(value, 180).lower()
    text = re.sub(r"[^a-z0-9._:-]+", "-", text).strip("-._:")
    return text or f"{prefix}:{uuid4().hex[:16]}"


def _resolve(value: str) -> Path:
    return Path(value).expanduser()


def _digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)
    return sha256(encoded.encode("utf-8")).hexdigest()


def _append(path: Path, record: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(dict(record), sort_keys=True, ensure_ascii=False) + "\n")


def _read_jsonl(path: Path, limit: int) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()[-limit:]
    except (FileNotFoundError, OSError):
        return []
    rows: list[dict[str, Any]] = []
    for line in lines:
        try:
            row = json.loads(line)
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def _latest(path: Path, key: str, limit: int) -> list[dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for row in _read_jsonl(path, limit):
        row_id = _safe_text(row.get(key), 180)
        if row_id:
            rows[row_id] = row
    return list(rows.values())


def _reject_identity_payload(value: Any, path: str = "request") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized = str(key).strip().lower().replace("-", "_")
            if normalized in DENIED_IDENTITY_FIELDS:
                raise ValueError(f"{path}.{key} is not accepted; contact and recipient identities are outside this workspace.")
            _reject_identity_payload(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_identity_payload(child, f"{path}[{index}]")


def _actor(value: Any, field: str = "actor") -> str:
    text = _safe_text(value, 120)
    if not text:
        raise ValueError(f"{field} is required.")
    if "@" in text or re.search(r"\b\+?\d[\d\s().-]{7,}\b", text):
        raise ValueError(f"{field} must be an editorial handle or role label, not contact information.")
    return text


def _string_list(value: Any, maximum: int = 100, item_limit: int = 1000) -> list[str]:
    if not isinstance(value, (list, tuple)):
        raise ValueError("Expected a list of editorial text items.")
    output: list[str] = []
    for item in value[:maximum]:
        text = _safe_text(item, item_limit)
        if text:
            output.append(text)
    return output


def editorial_workspace_policy() -> dict[str, Any]:
    return {
        "ok": True,
        "version": APP_VERSION,
        "schema": POLICY_SCHEMA_VERSION,
        "principle": "Support accountable editorial collaboration without allowing copy edits to rewrite evidence or publish themselves.",
        "roles": list(ALLOWED_ROLES),
        "editable_fields": list(EDITABLE_FIELDS),
        "publication_adapters": list(ALLOWED_ADAPTERS),
        "boundaries": {
            "human_approval_required": True,
            "separation_of_duties": True,
            "evidence_mutation_allowed": False,
            "claim_source_mutation_allowed": False,
            "automatic_publication": False,
            "automatic_wordpress_write": False,
            "adapter_write_performed": False,
            "recipient_identities_stored": False,
            "revision_history_retained": True,
        },
        "routes": {
            "policy": "/public/live-intelligence/editorial/policy",
            "status": "/public/live-intelligence/editorial/status",
            "admin": "/admin/live-intelligence/editorial",
        },
    }


class LiveIntelligenceEditorialWorkspace:
    def __init__(
        self,
        settings: Settings,
        *,
        briefing_center: Any,
        now_fn: Callable[[], datetime] = _utc_now,
    ) -> None:
        self.settings = settings
        self.briefing_center = briefing_center
        self.now_fn = now_fn
        self.workspaces_path = _resolve(settings.live_intelligence_editorial_workspaces_path)
        self.events_path = _resolve(settings.live_intelligence_editorial_events_path)
        self.orchestration_path = _resolve(settings.live_intelligence_editorial_orchestration_path)
        self.max_records = int(settings.live_intelligence_editorial_max_records)
        self.require_separation = bool(settings.live_intelligence_editorial_require_separation_of_duties)

    def _event(self, workspace_id: str, event_type: str, actor: str, detail: Mapping[str, Any]) -> dict[str, Any]:
        event = {
            "schema": REVISION_SCHEMA_VERSION,
            "release_version": APP_VERSION,
            "event_id": f"editorial-event:{uuid4().hex[:20]}",
            "workspace_id": workspace_id,
            "event_type": event_type,
            "actor": actor,
            "occurred_at": _iso(self.now_fn()),
            "detail": deepcopy(dict(detail)),
        }
        event["event_sha256"] = _digest({key: value for key, value in event.items() if key != "event_sha256"})
        _append(self.events_path, event)
        return event

    def workspaces(self, limit: int = 100) -> list[dict[str, Any]]:
        rows = [row for row in _latest(self.workspaces_path, "workspace_id", self.max_records) if not row.get("deleted")]
        return sorted(rows, key=lambda row: str(row.get("updated_at") or row.get("created_at") or ""), reverse=True)[:max(1, min(int(limit), 500))]

    def workspace(self, workspace_id: str) -> dict[str, Any]:
        target = _safe_id(workspace_id, "editorial-workspace")
        for row in self.workspaces(limit=500):
            if row.get("workspace_id") == target:
                return row
        raise KeyError(target)

    def create_workspace(self, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_identity_payload(request)
        briefing_id = _safe_id(request.get("briefing_id"), "briefing")
        created_by = _actor(request.get("created_by"), "created_by")
        assigned_role = _safe_text(request.get("assigned_role") or "editor", 40).lower()
        if assigned_role not in ALLOWED_ROLES:
            raise ValueError("Unsupported assigned_role.")
        briefing = self.briefing_center._briefing(briefing_id, public=False)
        now = self.now_fn().astimezone(timezone.utc)
        immutable = {
            "claims": deepcopy(briefing.get("claims") or []),
            "evidence": deepcopy(briefing.get("evidence") or []),
            "chronology": deepcopy(briefing.get("chronology") or []),
        }
        content = {field: deepcopy(briefing.get(field)) for field in EDITABLE_FIELDS}
        record = {
            "schema": WORKSPACE_SCHEMA_VERSION,
            "release_version": APP_VERSION,
            "workspace_id": _safe_id(request.get("workspace_id") or f"editorial-workspace:{uuid4().hex[:20]}", "editorial-workspace"),
            "briefing_id": briefing_id,
            "briefing_visibility": _safe_text(briefing.get("visibility"), 20),
            "status": "drafting",
            "created_by": created_by,
            "assigned_to": _safe_text(request.get("assigned_to"), 120),
            "assigned_role": assigned_role,
            "revision_number": 0,
            "content": content,
            "immutable_source_digest": _digest(immutable),
            "content_sha256": _digest(content),
            "last_revision_by": created_by,
            "submitted_by": "",
            "submitted_at": "",
            "reviewed_by": "",
            "reviewed_at": "",
            "review_reason": "",
            "publication_ready": False,
            "created_at": _iso(now),
            "updated_at": _iso(now),
            "automatic_publication": False,
            "automatic_wordpress_write": False,
        }
        if record["assigned_to"]:
            record["assigned_to"] = _actor(record["assigned_to"], "assigned_to")
        record["workspace_sha256"] = _digest({key: value for key, value in record.items() if key != "workspace_sha256"})
        _append(self.workspaces_path, record)
        self._event(record["workspace_id"], "workspace_created", created_by, {"briefing_id": briefing_id, "assigned_role": assigned_role})
        return {"ok": True, "version": APP_VERSION, "workspace": record}

    def assign(self, workspace_id: str, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_identity_payload(request)
        actor = _actor(request.get("actor"))
        assigned_to = _actor(request.get("assigned_to"), "assigned_to")
        role = _safe_text(request.get("assigned_role") or "editor", 40).lower()
        if role not in ALLOWED_ROLES:
            raise ValueError("Unsupported assigned_role.")
        current = self.workspace(workspace_id)
        updated = dict(current)
        updated.update({"assigned_to": assigned_to, "assigned_role": role, "updated_at": _iso(self.now_fn())})
        updated["workspace_sha256"] = _digest({key: value for key, value in updated.items() if key != "workspace_sha256"})
        _append(self.workspaces_path, updated)
        self._event(updated["workspace_id"], "assignment_changed", actor, {"assigned_to": assigned_to, "assigned_role": role})
        return {"ok": True, "version": APP_VERSION, "workspace": updated}

    def add_revision(self, workspace_id: str, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_identity_payload(request)
        actor = _actor(request.get("actor"))
        current = self.workspace(workspace_id)
        if current.get("status") not in {"drafting", "changes_requested"}:
            raise ValueError("Revisions are allowed only while drafting or after changes are requested.")
        patch = request.get("changes")
        if not isinstance(patch, Mapping) or not patch:
            raise ValueError("changes must contain at least one editable field.")
        protected = sorted(set(str(key) for key in patch) & PROTECTED_FIELDS)
        unsupported = sorted(set(str(key) for key in patch) - set(EDITABLE_FIELDS) - PROTECTED_FIELDS)
        if protected:
            raise ValueError("Evidence, claims, source links, values, and provenance are immutable in editorial revisions.")
        if unsupported:
            raise ValueError(f"Unsupported editorial fields: {', '.join(unsupported)}")
        content = deepcopy(current.get("content") or {})
        changed_fields: list[str] = []
        for field, value in patch.items():
            if field in {"key_observations", "limitations"}:
                clean = _string_list(value)
            else:
                clean = _safe_text(value, 5000 if field == "executive_summary" else 1000)
            if content.get(field) != clean:
                content[field] = clean
                changed_fields.append(field)
        if not changed_fields:
            raise ValueError("Revision did not change any editorial content.")
        updated = dict(current)
        updated.update({
            "content": content,
            "content_sha256": _digest(content),
            "revision_number": int(current.get("revision_number") or 0) + 1,
            "last_revision_by": actor,
            "status": "drafting",
            "publication_ready": False,
            "updated_at": _iso(self.now_fn()),
        })
        updated["workspace_sha256"] = _digest({key: value for key, value in updated.items() if key != "workspace_sha256"})
        _append(self.workspaces_path, updated)
        self._event(updated["workspace_id"], "revision_created", actor, {
            "revision_number": updated["revision_number"],
            "changed_fields": changed_fields,
            "previous_content_sha256": current.get("content_sha256"),
            "content_sha256": updated["content_sha256"],
            "reason": _safe_text(request.get("reason"), 1000),
        })
        return {"ok": True, "version": APP_VERSION, "workspace": updated}

    def submit_for_review(self, workspace_id: str, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_identity_payload(request)
        actor = _actor(request.get("actor"))
        reason = _safe_text(request.get("reason"), 1000)
        if not reason:
            raise ValueError("reason is required.")
        current = self.workspace(workspace_id)
        if current.get("status") not in {"drafting", "changes_requested"}:
            raise ValueError("Workspace is not ready to submit for review.")
        updated = dict(current)
        updated.update({"status": "in_review", "submitted_by": actor, "submitted_at": _iso(self.now_fn()), "updated_at": _iso(self.now_fn())})
        updated["workspace_sha256"] = _digest({key: value for key, value in updated.items() if key != "workspace_sha256"})
        _append(self.workspaces_path, updated)
        self._event(updated["workspace_id"], "submitted_for_review", actor, {"reason": reason, "revision_number": updated.get("revision_number", 0)})
        return {"ok": True, "version": APP_VERSION, "workspace": updated}

    def review(self, workspace_id: str, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_identity_payload(request)
        decision = _safe_text(request.get("decision"), 30).lower()
        reviewer = _actor(request.get("reviewed_by"), "reviewed_by")
        reason = _safe_text(request.get("reason"), 1400)
        if decision not in {"approve", "request_changes", "reject"}:
            raise ValueError("decision must be approve, request_changes, or reject.")
        if not reason:
            raise ValueError("reason is required.")
        current = self.workspace(workspace_id)
        if current.get("status") != "in_review":
            raise ValueError("Workspace must be in review before a decision is recorded.")
        if decision == "approve" and self.require_separation:
            prohibited = {str(current.get("created_by") or ""), str(current.get("submitted_by") or ""), str(current.get("last_revision_by") or "")}
            if reviewer in prohibited:
                raise ValueError("Final approval requires separation of duties from authorship, revision, and submission.")
        status = "approved" if decision == "approve" else "changes_requested" if decision == "request_changes" else "rejected"
        updated = dict(current)
        updated.update({
            "status": status,
            "reviewed_by": reviewer,
            "reviewed_at": _iso(self.now_fn()),
            "review_reason": reason,
            "publication_ready": decision == "approve",
            "updated_at": _iso(self.now_fn()),
        })
        updated["workspace_sha256"] = _digest({key: value for key, value in updated.items() if key != "workspace_sha256"})
        _append(self.workspaces_path, updated)
        review_record = {
            "schema": REVIEW_SCHEMA_VERSION,
            "decision": decision,
            "reviewed_by": reviewer,
            "reason": reason,
            "separation_of_duties_verified": bool(decision != "approve" or self.require_separation),
        }
        self._event(updated["workspace_id"], "review_decision", reviewer, review_record)
        return {"ok": True, "version": APP_VERSION, "workspace": updated, "review": review_record}

    def orchestrate(self, workspace_id: str, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_identity_payload(request)
        actor = _actor(request.get("actor"))
        current = self.workspace(workspace_id)
        if current.get("status") != "approved" or current.get("publication_ready") is not True:
            raise ValueError("Only a human-approved editorial workspace may create publication orchestration manifests.")
        requested = request.get("adapters") or list(ALLOWED_ADAPTERS)
        if not isinstance(requested, Sequence) or isinstance(requested, (str, bytes)):
            raise ValueError("adapters must be a list.")
        adapters: list[str] = []
        for value in requested:
            adapter = _safe_text(value, 80).lower()
            if adapter not in ALLOWED_ADAPTERS:
                raise ValueError("Unsupported publication adapter.")
            if adapter not in adapters:
                adapters.append(adapter)
        if not adapters:
            raise ValueError("At least one publication adapter is required.")
        briefing = self.briefing_center._briefing(current["briefing_id"], public=False)
        immutable = {"claims": briefing.get("claims") or [], "evidence": briefing.get("evidence") or [], "chronology": briefing.get("chronology") or []}
        if _digest(immutable) != current.get("immutable_source_digest"):
            raise ValueError("Canonical evidence changed after workspace creation; reopen review against the current briefing source set.")
        now = self.now_fn().astimezone(timezone.utc)
        plan = {
            "schema": ORCHESTRATION_SCHEMA_VERSION,
            "release_version": APP_VERSION,
            "orchestration_id": f"publication-orchestration:{uuid4().hex[:20]}",
            "workspace_id": current.get("workspace_id"),
            "briefing_id": current.get("briefing_id"),
            "created_by": actor,
            "created_at": _iso(now),
            "content": deepcopy(current.get("content") or {}),
            "claims": deepcopy(briefing.get("claims") or []),
            "evidence": deepcopy(briefing.get("evidence") or []),
            "chronology": deepcopy(briefing.get("chronology") or []),
            "adapters": [
                {
                    "adapter": adapter,
                    "state": "ready_for_download" if adapter == "download" else "ready_for_external_adapter",
                    "write_performed": False,
                }
                for adapter in adapters
            ],
            "publication_performed": False,
            "wordpress_write_performed": False,
            "provider_neutral": True,
            "recipient_data_included": False,
            "human_approval_record": {
                "reviewed_by": current.get("reviewed_by"),
                "reviewed_at": current.get("reviewed_at"),
                "reason": current.get("review_reason"),
            },
        }
        plan["orchestration_sha256"] = _digest({key: value for key, value in plan.items() if key != "orchestration_sha256"})
        _append(self.orchestration_path, plan)
        self._event(current["workspace_id"], "publication_orchestration_created", actor, {"orchestration_id": plan["orchestration_id"], "adapters": adapters})
        return {"ok": True, "version": APP_VERSION, "orchestration": plan}

    def history(self, workspace_id: str, limit: int = 200) -> list[dict[str, Any]]:
        target = _safe_id(workspace_id, "editorial-workspace")
        rows = [row for row in _read_jsonl(self.events_path, self.max_records) if row.get("workspace_id") == target]
        return rows[-max(1, min(int(limit), 1000)):]

    def status(self) -> dict[str, Any]:
        rows = self.workspaces(limit=500)
        plans = _latest(self.orchestration_path, "orchestration_id", self.max_records)
        counts = {state: sum(1 for row in rows if row.get("status") == state) for state in ("drafting", "in_review", "changes_requested", "approved", "rejected")}
        return {
            "ok": True,
            "version": APP_VERSION,
            "schema": POLICY_SCHEMA_VERSION,
            "workspace_count": len(rows),
            "status_counts": counts,
            "publication_ready_count": sum(1 for row in rows if row.get("publication_ready") is True),
            "orchestration_count": len(plans),
            "separation_of_duties_required": self.require_separation,
            "automatic_publication": False,
            "automatic_wordpress_write": False,
        }

    def control_center(self) -> dict[str, Any]:
        return {
            "ok": True,
            "version": APP_VERSION,
            "policy": editorial_workspace_policy(),
            "status": self.status(),
            "workspaces": self.workspaces(limit=100),
            "orchestrations": _latest(self.orchestration_path, "orchestration_id", self.max_records)[-100:],
        }
