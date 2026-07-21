from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import zipfile
from typing import Any, Callable
from uuid import uuid4

from .config import Settings

RELEASE_VERSION = "3.7.2"
SCHEMA_VERSION = "sc-site-intelligence-institutional-workspaces/1.0"
WORKSPACE_SCHEMA = "sc-site-intelligence-shared-workspace/1.0"
MEMBER_SCHEMA = "sc-site-intelligence-workspace-member/1.0"
ASSIGNMENT_SCHEMA = "sc-site-intelligence-workspace-assignment/1.0"
COMMENT_SCHEMA = "sc-site-intelligence-workspace-comment/1.0"
REVIEW_SCHEMA = "sc-site-intelligence-workspace-evidence-review/1.0"
COLLECTION_SCHEMA = "sc-site-intelligence-workspace-source-collection/1.0"
ACTIVITY_SCHEMA = "sc-site-intelligence-workspace-activity/1.0"
RETENTION_SCHEMA = "sc-site-intelligence-workspace-retention/1.0"

ROLES = {"analyst", "reviewer", "publisher", "administrator"}
VISIBILITY = {"private", "unlisted", "public"}
WORKSPACE_STATUSES = {"draft", "active", "in_review", "published", "archived"}
ASSIGNMENT_STATUSES = {"open", "in_progress", "blocked", "in_review", "completed", "cancelled"}
PRIORITIES = {"low", "normal", "high", "urgent"}
REVIEW_DECISIONS = {"approved", "rejected", "needs_changes", "unresolved"}
COMMENT_TYPES = {"comment", "review_note", "decision_note", "handoff_note"}
PERMISSIONS = {
    "analyst": {"read", "comment", "create_assignment", "update_own_assignment", "manage_sources"},
    "reviewer": {"read", "comment", "review_evidence", "update_assignment", "manage_sources"},
    "publisher": {"read", "comment", "review_evidence", "update_assignment", "publish", "manage_sources", "export", "manage_workspace"},
    "administrator": {"read", "comment", "create_assignment", "update_own_assignment", "review_evidence", "update_assignment", "publish", "manage_sources", "export", "manage_members", "manage_workspace", "retention"},
}
_SECRET = re.compile(r"(?:token|secret|password|authorization|api[_-]?key|email|phone|address|session|cookie)", re.I)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def _parse(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _resolve(value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else Path(__file__).resolve().parents[2] / path


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _safe_id(value: Any, fallback: str = "record") -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_.:-]+", "-", str(value or "").strip()).strip("-:.")
    return (cleaned or fallback)[:180]


def _safe_text(value: Any, limit: int = 2000) -> str:
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", str(value or "")).strip()[:limit]


def _list(value: Any, maximum: int = 100, length: int = 300) -> list[str]:
    if not isinstance(value, list):
        return []
    output: list[str] = []
    for item in value[:maximum]:
        text = _safe_text(item, length)
        if text and text not in output:
            output.append(text)
    return output


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): ("[redacted]" if _SECRET.search(str(k)) else _redact(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


def _read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default


def _read_jsonl(path: Path, limit: int = 50000) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()[-limit:]
    except (FileNotFoundError, OSError):
        return []
    output: list[dict[str, Any]] = []
    for line in lines:
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            output.append(value)
    return output


def _append(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def _latest(path: Path, key: str, limit: int = 50000) -> list[dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for row in _read_jsonl(path, limit):
        identifier = str(row.get(key) or "")
        if identifier:
            rows[identifier] = row
    return [row for row in rows.values() if not row.get("deleted")]


class InstitutionalWorkspaceCenter:
    """File-backed shared-workspace control plane.

    Authentication remains outside this class. Administrative API calls are token protected;
    the optional ``actor_role`` supplied to methods is an authorization assertion from that
    authenticated boundary, not a replacement identity provider.
    """

    def __init__(self, settings: Settings, now_fn: Callable[[], datetime] = _utc_now) -> None:
        self.settings = settings
        self.now_fn = now_fn
        self.workspaces_path = _resolve(settings.institutional_workspaces_workspaces_path)
        self.members_path = _resolve(settings.institutional_workspaces_members_path)
        self.assignments_path = _resolve(settings.institutional_workspaces_assignments_path)
        self.comments_path = _resolve(settings.institutional_workspaces_comments_path)
        self.reviews_path = _resolve(settings.institutional_workspaces_reviews_path)
        self.collections_path = _resolve(settings.institutional_workspaces_collections_path)
        self.activity_path = _resolve(settings.institutional_workspaces_activity_path)
        self.retention_path = _resolve(settings.institutional_workspaces_retention_path)
        self.policy = _read_json(_resolve(settings.institutional_workspaces_policy_path), {})
        self.max_records = settings.institutional_workspaces_max_records
        self.max_members = settings.institutional_workspaces_max_members
        self.max_comments = settings.institutional_workspaces_max_comments

    def _require(self, role: str, permission: str) -> str:
        normalized = _safe_text(role or "administrator", 30).lower()
        if normalized not in ROLES:
            raise ValueError("Unsupported workspace role.")
        if permission not in PERMISSIONS[normalized]:
            raise PermissionError(f"Role {normalized} does not have {permission} permission.")
        return normalized

    def workspaces(self, public: bool = False) -> list[dict[str, Any]]:
        rows = _latest(self.workspaces_path, "workspace_id", self.max_records)
        if public:
            rows = [row for row in rows if row.get("visibility") == "public" and row.get("status") == "published"]
            return [self._public_workspace(row) for row in sorted(rows, key=lambda x: str(x.get("updated_at", "")), reverse=True)]
        return sorted(rows, key=lambda x: str(x.get("updated_at", "")), reverse=True)

    def _workspace(self, workspace_id: str) -> dict[str, Any]:
        token = _safe_id(workspace_id)
        for row in self.workspaces(False):
            if row.get("workspace_id") == token:
                return row
        raise KeyError(token)

    def _public_workspace(self, row: dict[str, Any]) -> dict[str, Any]:
        workspace_id = str(row.get("workspace_id"))
        approved = [r for r in self.reviews(workspace_id) if r.get("decision") == "approved" and r.get("public_eligible")]
        collections = [c for c in self.collections(workspace_id) if c.get("visibility") == "public"]
        return {
            "schema": WORKSPACE_SCHEMA,
            "release_version": RELEASE_VERSION,
            "workspace_id": workspace_id,
            "title": row.get("title"),
            "summary": row.get("summary"),
            "status": row.get("status"),
            "visibility": row.get("visibility"),
            "institution": row.get("institution", {}),
            "topics": row.get("topics", []),
            "approved_evidence_count": len(approved),
            "public_source_collections": [self._public_collection(item) for item in collections],
            "published_at": row.get("published_at", ""),
            "updated_at": row.get("updated_at", ""),
            "methodology": "Public workspaces expose only human-published summaries, approved public-eligible evidence counts, and public source collections. Member identities, assignments, comments, private evidence, and activity logs are never public.",
        }

    def create_workspace(self, request: dict[str, Any], actor_role: str = "administrator", actor_id: str = "system") -> dict[str, Any]:
        role = self._require(actor_role, "manage_workspace")
        title = _safe_text(request.get("title"), 300)
        if not title:
            raise ValueError("title is required.")
        workspace_id = _safe_id(request.get("workspace_id") or f"workspace:{uuid4().hex[:16]}")
        if any(row.get("workspace_id") == workspace_id for row in self.workspaces(False)):
            raise ValueError("workspace_id already exists.")
        visibility = _safe_text(request.get("visibility") or "private", 20).lower()
        if visibility not in VISIBILITY:
            raise ValueError("Unsupported visibility.")
        institution = request.get("institution") if isinstance(request.get("institution"), dict) else {}
        branding = request.get("branding") if isinstance(request.get("branding"), dict) else {}
        now = self.now_fn()
        record = {
            "schema": WORKSPACE_SCHEMA,
            "release_version": RELEASE_VERSION,
            "workspace_id": workspace_id,
            "title": title,
            "summary": _safe_text(request.get("summary"), 5000),
            "status": "draft",
            "visibility": visibility,
            "institution": {
                "name": _safe_text(institution.get("name") or self.settings.institution_name, 300),
                "website": _safe_text(institution.get("website") or self.settings.institution_website, 500),
                "unit": _safe_text(institution.get("unit"), 300),
            },
            "branding": {
                "label": _safe_text(branding.get("label"), 200),
                "accent": _safe_text(branding.get("accent") or self.settings.institution_accent, 30),
                "logo_url": _safe_text(branding.get("logo_url"), 500),
            },
            "topics": _list(request.get("topics"), 50, 120),
            "retention_days": max(30, min(int(request.get("retention_days", self.settings.institutional_workspaces_default_retention_days)), 3650)),
            "created_at": _iso(now),
            "updated_at": _iso(now),
            "published_at": "",
            "created_by_role": role,
            "automatic_publication": False,
            "requires_human_review": True,
        }
        record["sha256"] = _digest({k: v for k, v in record.items() if k != "sha256"})
        _append(self.workspaces_path, record)
        self._activity(workspace_id, actor_id, role, "workspace.created", "workspace", workspace_id, {"visibility": visibility})
        return record

    def update_workspace(self, workspace_id: str, request: dict[str, Any], actor_role: str = "administrator", actor_id: str = "system") -> dict[str, Any]:
        role = self._require(actor_role, "manage_workspace")
        previous = self._workspace(workspace_id)
        status = _safe_text(request.get("status") or previous.get("status"), 30).lower()
        visibility = _safe_text(request.get("visibility") or previous.get("visibility"), 20).lower()
        if status not in WORKSPACE_STATUSES or visibility not in VISIBILITY:
            raise ValueError("Unsupported workspace status or visibility.")
        if status == "published" and role not in {"publisher", "administrator"}:
            raise PermissionError("Publishing requires publisher or administrator role.")
        if status == "published" and not self._publication_ready(workspace_id):
            raise ValueError("Workspace cannot be published until at least one evidence review is approved and all urgent assignments are resolved.")
        now = self.now_fn()
        record = dict(previous)
        record.update({
            "title": _safe_text(request.get("title") or previous.get("title"), 300),
            "summary": _safe_text(request.get("summary") if "summary" in request else previous.get("summary"), 5000),
            "status": status,
            "visibility": visibility,
            "topics": _list(request.get("topics"), 50, 120) if "topics" in request else previous.get("topics", []),
            "updated_at": _iso(now),
            "published_at": _iso(now) if status == "published" else previous.get("published_at", ""),
        })
        if isinstance(request.get("branding"), dict):
            brand = request["branding"]
            record["branding"] = {
                "label": _safe_text(brand.get("label"), 200),
                "accent": _safe_text(brand.get("accent"), 30),
                "logo_url": _safe_text(brand.get("logo_url"), 500),
            }
        record["sha256"] = _digest({k: v for k, v in record.items() if k != "sha256"})
        _append(self.workspaces_path, record)
        self._activity(workspace_id, actor_id, role, "workspace.updated", "workspace", workspace_id, {"status": status, "visibility": visibility})
        return record

    def members(self, workspace_id: str) -> list[dict[str, Any]]:
        token = _safe_id(workspace_id)
        return sorted([row for row in _latest(self.members_path, "membership_id", self.max_records) if row.get("workspace_id") == token], key=lambda x: str(x.get("updated_at", "")), reverse=True)

    def add_member(self, workspace_id: str, request: dict[str, Any], actor_role: str = "administrator", actor_id: str = "system") -> dict[str, Any]:
        role = self._require(actor_role, "manage_members")
        self._workspace(workspace_id)
        member_role = _safe_text(request.get("role"), 30).lower()
        if member_role not in ROLES:
            raise ValueError("Unsupported member role.")
        subject_id = _safe_id(request.get("subject_id"))
        if not subject_id:
            raise ValueError("subject_id is required.")
        existing = next((m for m in self.members(workspace_id) if m.get("subject_id") == subject_id), None)
        now = self.now_fn()
        record = {
            "schema": MEMBER_SCHEMA,
            "release_version": RELEASE_VERSION,
            "membership_id": (existing or {}).get("membership_id") or _safe_id(f"member:{workspace_id}:{subject_id}"),
            "workspace_id": _safe_id(workspace_id),
            "subject_id": subject_id,
            "display_label": _safe_text(request.get("display_label") or (existing or {}).get("display_label") or "Workspace member", 200),
            "role": member_role,
            "status": _safe_text(request.get("status") or "active", 30),
            "permissions": sorted(PERMISSIONS[member_role]),
            "created_at": (existing or {}).get("created_at") or _iso(now),
            "updated_at": _iso(now),
        }
        record["sha256"] = _digest({k: v for k, v in record.items() if k != "sha256"})
        _append(self.members_path, record)
        self._activity(workspace_id, actor_id, role, "member.saved", "member", record["membership_id"], {"member_role": member_role})
        return record

    def assignments(self, workspace_id: str) -> list[dict[str, Any]]:
        token = _safe_id(workspace_id)
        return sorted([row for row in _latest(self.assignments_path, "assignment_id", self.max_records) if row.get("workspace_id") == token], key=lambda x: str(x.get("updated_at", "")), reverse=True)

    def save_assignment(self, workspace_id: str, request: dict[str, Any], actor_role: str = "administrator", actor_id: str = "system") -> dict[str, Any]:
        role = self._require(actor_role, "create_assignment" if not request.get("assignment_id") else "update_assignment")
        self._workspace(workspace_id)
        title = _safe_text(request.get("title"), 400)
        if not title:
            raise ValueError("title is required.")
        assignment_id = _safe_id(request.get("assignment_id") or f"assignment:{uuid4().hex[:16]}")
        previous = next((a for a in self.assignments(workspace_id) if a.get("assignment_id") == assignment_id), None)
        status = _safe_text(request.get("status") or (previous or {}).get("status") or "open", 30).lower()
        priority = _safe_text(request.get("priority") or (previous or {}).get("priority") or "normal", 20).lower()
        if status not in ASSIGNMENT_STATUSES or priority not in PRIORITIES:
            raise ValueError("Unsupported assignment status or priority.")
        now = self.now_fn()
        record = {
            "schema": ASSIGNMENT_SCHEMA,
            "release_version": RELEASE_VERSION,
            "assignment_id": assignment_id,
            "workspace_id": _safe_id(workspace_id),
            "title": title,
            "description": _safe_text(request.get("description") if "description" in request else (previous or {}).get("description"), 5000),
            "status": status,
            "priority": priority,
            "assignee_id": _safe_id(request.get("assignee_id") or (previous or {}).get("assignee_id") or "unassigned"),
            "due_at": _safe_text(request.get("due_at") or (previous or {}).get("due_at"), 80),
            "evidence_ids": _list(request.get("evidence_ids") if "evidence_ids" in request else (previous or {}).get("evidence_ids", []), 100, 180),
            "created_at": (previous or {}).get("created_at") or _iso(now),
            "updated_at": _iso(now),
            "completed_at": _iso(now) if status == "completed" else (previous or {}).get("completed_at", ""),
        }
        record["sha256"] = _digest({k: v for k, v in record.items() if k != "sha256"})
        _append(self.assignments_path, record)
        self._activity(workspace_id, actor_id, role, "assignment.saved", "assignment", assignment_id, {"status": status, "priority": priority})
        return record

    def comments(self, workspace_id: str) -> list[dict[str, Any]]:
        token = _safe_id(workspace_id)
        return sorted([row for row in _latest(self.comments_path, "comment_id", self.max_comments) if row.get("workspace_id") == token], key=lambda x: str(x.get("created_at", "")))

    def add_comment(self, workspace_id: str, request: dict[str, Any], actor_role: str = "administrator", actor_id: str = "system") -> dict[str, Any]:
        role = self._require(actor_role, "comment")
        self._workspace(workspace_id)
        body = _safe_text(request.get("body"), 10000)
        if not body:
            raise ValueError("body is required.")
        comment_type = _safe_text(request.get("comment_type") or "comment", 30).lower()
        if comment_type not in COMMENT_TYPES:
            raise ValueError("Unsupported comment type.")
        now = self.now_fn()
        record = {
            "schema": COMMENT_SCHEMA,
            "release_version": RELEASE_VERSION,
            "comment_id": _safe_id(request.get("comment_id") or f"comment:{uuid4().hex[:16]}"),
            "workspace_id": _safe_id(workspace_id),
            "target_type": _safe_text(request.get("target_type") or "workspace", 50),
            "target_id": _safe_id(request.get("target_id") or workspace_id),
            "comment_type": comment_type,
            "body": body,
            "author_id": _safe_id(actor_id),
            "author_role": role,
            "created_at": _iso(now),
            "resolved": bool(request.get("resolved", False)),
            "public": False,
        }
        record["sha256"] = _digest({k: v for k, v in record.items() if k != "sha256"})
        _append(self.comments_path, record)
        self._activity(workspace_id, actor_id, role, "comment.added", "comment", record["comment_id"], {"comment_type": comment_type})
        return record

    def reviews(self, workspace_id: str) -> list[dict[str, Any]]:
        token = _safe_id(workspace_id)
        return sorted([row for row in _latest(self.reviews_path, "review_id", self.max_records) if row.get("workspace_id") == token], key=lambda x: str(x.get("reviewed_at", "")), reverse=True)

    def review_evidence(self, workspace_id: str, request: dict[str, Any], actor_role: str = "reviewer", actor_id: str = "system") -> dict[str, Any]:
        role = self._require(actor_role, "review_evidence")
        self._workspace(workspace_id)
        evidence_id = _safe_id(request.get("evidence_id"))
        if not evidence_id:
            raise ValueError("evidence_id is required.")
        decision = _safe_text(request.get("decision"), 30).lower()
        if decision not in REVIEW_DECISIONS:
            raise ValueError("Unsupported evidence-review decision.")
        rationale = _safe_text(request.get("rationale"), 5000)
        if not rationale:
            raise ValueError("rationale is required.")
        now = self.now_fn()
        record = {
            "schema": REVIEW_SCHEMA,
            "release_version": RELEASE_VERSION,
            "review_id": _safe_id(request.get("review_id") or f"review:{uuid4().hex[:16]}"),
            "workspace_id": _safe_id(workspace_id),
            "evidence_id": evidence_id,
            "decision": decision,
            "rationale": rationale,
            "limitations": _list(request.get("limitations"), 50, 500),
            "public_eligible": bool(request.get("public_eligible", False)) if decision == "approved" else False,
            "reviewer_id": _safe_id(actor_id),
            "reviewer_role": role,
            "reviewed_at": _iso(now),
            "automatic_decision": False,
        }
        record["sha256"] = _digest({k: v for k, v in record.items() if k != "sha256"})
        _append(self.reviews_path, record)
        self._activity(workspace_id, actor_id, role, "evidence.reviewed", "evidence", evidence_id, {"decision": decision, "public_eligible": record["public_eligible"]})
        return record

    def collections(self, workspace_id: str) -> list[dict[str, Any]]:
        token = _safe_id(workspace_id)
        return sorted([row for row in _latest(self.collections_path, "collection_id", self.max_records) if row.get("workspace_id") == token], key=lambda x: str(x.get("updated_at", "")), reverse=True)

    def _public_collection(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "collection_id": row.get("collection_id"),
            "title": row.get("title"),
            "summary": row.get("summary"),
            "source_ids": row.get("source_ids", []),
            "evidence_ids": row.get("public_evidence_ids", []),
            "updated_at": row.get("updated_at", ""),
        }

    def save_collection(self, workspace_id: str, request: dict[str, Any], actor_role: str = "analyst", actor_id: str = "system") -> dict[str, Any]:
        role = self._require(actor_role, "manage_sources")
        self._workspace(workspace_id)
        title = _safe_text(request.get("title"), 300)
        if not title:
            raise ValueError("title is required.")
        collection_id = _safe_id(request.get("collection_id") or f"collection:{uuid4().hex[:16]}")
        previous = next((c for c in self.collections(workspace_id) if c.get("collection_id") == collection_id), None)
        visibility = _safe_text(request.get("visibility") or (previous or {}).get("visibility") or "private", 20).lower()
        if visibility not in VISIBILITY:
            raise ValueError("Unsupported collection visibility.")
        evidence_ids = _list(request.get("evidence_ids") if "evidence_ids" in request else (previous or {}).get("evidence_ids", []), 1000, 180)
        approved_public = {r.get("evidence_id") for r in self.reviews(workspace_id) if r.get("decision") == "approved" and r.get("public_eligible")}
        now = self.now_fn()
        record = {
            "schema": COLLECTION_SCHEMA,
            "release_version": RELEASE_VERSION,
            "collection_id": collection_id,
            "workspace_id": _safe_id(workspace_id),
            "title": title,
            "summary": _safe_text(request.get("summary") if "summary" in request else (previous or {}).get("summary"), 5000),
            "visibility": visibility,
            "source_ids": _list(request.get("source_ids") if "source_ids" in request else (previous or {}).get("source_ids", []), 1000, 180),
            "evidence_ids": evidence_ids,
            "public_evidence_ids": sorted(set(evidence_ids) & approved_public) if visibility == "public" else [],
            "created_at": (previous or {}).get("created_at") or _iso(now),
            "updated_at": _iso(now),
        }
        record["sha256"] = _digest({k: v for k, v in record.items() if k != "sha256"})
        _append(self.collections_path, record)
        self._activity(workspace_id, actor_id, role, "collection.saved", "collection", collection_id, {"visibility": visibility})
        return record

    def activity(self, workspace_id: str, limit: int = 500) -> list[dict[str, Any]]:
        token = _safe_id(workspace_id)
        rows = [row for row in _read_jsonl(self.activity_path, self.max_records) if row.get("workspace_id") == token]
        return list(reversed(rows[-max(1, min(limit, 5000)):]))

    def _activity(self, workspace_id: str, actor_id: str, role: str, action: str, target_type: str, target_id: str, detail: dict[str, Any]) -> dict[str, Any]:
        record = {
            "schema": ACTIVITY_SCHEMA,
            "release_version": RELEASE_VERSION,
            "activity_id": _safe_id(f"activity:{uuid4().hex}"),
            "workspace_id": _safe_id(workspace_id),
            "actor_id": _safe_id(actor_id),
            "actor_role": role,
            "action": _safe_text(action, 100),
            "target_type": _safe_text(target_type, 80),
            "target_id": _safe_id(target_id),
            "detail": _redact(detail),
            "occurred_at": _iso(self.now_fn()),
        }
        record["sha256"] = _digest({k: v for k, v in record.items() if k != "sha256"})
        _append(self.activity_path, record)
        return record

    def _publication_ready(self, workspace_id: str) -> bool:
        approved = any(r.get("decision") == "approved" for r in self.reviews(workspace_id))
        urgent_open = any(a.get("priority") == "urgent" and a.get("status") not in {"completed", "cancelled"} for a in self.assignments(workspace_id))
        return approved and not urgent_open

    def retention_preview(self, workspace_id: str, cutoff_days: int | None = None) -> dict[str, Any]:
        workspace = self._workspace(workspace_id)
        days = max(30, min(int(cutoff_days or workspace.get("retention_days") or self.settings.institutional_workspaces_default_retention_days), 3650))
        cutoff = self.now_fn() - timedelta(days=days)
        candidates: dict[str, list[str]] = {"comments": [], "assignments": [], "activity": []}
        for row in self.comments(workspace_id):
            created = _parse(row.get("created_at"))
            if created and created < cutoff and row.get("resolved"):
                candidates["comments"].append(str(row.get("comment_id")))
        for row in self.assignments(workspace_id):
            updated = _parse(row.get("updated_at"))
            if updated and updated < cutoff and row.get("status") in {"completed", "cancelled"}:
                candidates["assignments"].append(str(row.get("assignment_id")))
        for row in reversed(self.activity(workspace_id, limit=5000)):
            occurred = _parse(row.get("occurred_at"))
            if occurred and occurred < cutoff:
                candidates["activity"].append(str(row.get("activity_id")))
        return {
            "schema": RETENTION_SCHEMA,
            "release_version": RELEASE_VERSION,
            "workspace_id": workspace_id,
            "preview_only": True,
            "cutoff_days": days,
            "cutoff_at": _iso(cutoff),
            "candidates": candidates,
            "candidate_count": sum(len(value) for value in candidates.values()),
            "protected": ["workspace record", "member-role history", "evidence review decisions", "published summaries", "latest 100 activity events"],
            "automatic_deletion": False,
        }

    def apply_retention(self, workspace_id: str, request: dict[str, Any], actor_role: str = "administrator", actor_id: str = "system") -> dict[str, Any]:
        role = self._require(actor_role, "retention")
        if request.get("confirm") is not True:
            raise ValueError("confirm=true is required to apply retention.")
        preview = self.retention_preview(workspace_id, request.get("cutoff_days"))
        now = self.now_fn()
        deleted = Counter()
        ids = preview["candidates"]
        for path, key, group in [
            (self.comments_path, "comment_id", "comments"),
            (self.assignments_path, "assignment_id", "assignments"),
        ]:
            for identifier in ids[group]:
                _append(path, {key: identifier, "workspace_id": workspace_id, "deleted": True, "deleted_at": _iso(now), "release_version": RELEASE_VERSION})
                deleted[group] += 1
        # Activity is append-only. Retention is represented by a receipt, not physical line removal.
        receipt = {
            "schema": RETENTION_SCHEMA,
            "release_version": RELEASE_VERSION,
            "retention_id": _safe_id(f"retention:{uuid4().hex[:16]}"),
            "workspace_id": workspace_id,
            "applied_at": _iso(now),
            "cutoff_at": preview["cutoff_at"],
            "deleted": dict(deleted),
            "activity_candidates_preserved_as_append_only_audit": len(ids["activity"]),
            "actor_id": _safe_id(actor_id),
            "actor_role": role,
        }
        receipt["sha256"] = _digest({k: v for k, v in receipt.items() if k != "sha256"})
        _append(self.retention_path, receipt)
        self._activity(workspace_id, actor_id, role, "retention.applied", "retention", receipt["retention_id"], {"deleted": dict(deleted)})
        return receipt

    def export_workspace(self, workspace_id: str, actor_role: str = "publisher", format: str = "json") -> tuple[str, bytes]:
        self._require(actor_role, "export")
        workspace = self._workspace(workspace_id)
        payload = {
            "schema": SCHEMA_VERSION,
            "release_version": RELEASE_VERSION,
            "exported_at": _iso(self.now_fn()),
            "workspace": workspace,
            "members": self.members(workspace_id),
            "assignments": self.assignments(workspace_id),
            "comments": self.comments(workspace_id),
            "evidence_reviews": self.reviews(workspace_id),
            "source_collections": self.collections(workspace_id),
            "activity": self.activity(workspace_id, limit=5000),
            "retention_receipts": [r for r in _read_jsonl(self.retention_path, self.max_records) if r.get("workspace_id") == workspace_id],
            "boundaries": [
                "Export is an archive packet, not proof of external ingestion, and does not provision accounts.",
                "Public/private visibility labels and human review decisions remain explicit.",
                "No automatic identity provider, account provisioning, or remote write is claimed.",
            ],
        }
        payload["sha256"] = _digest({k: v for k, v in payload.items() if k != "sha256"})
        if format == "json":
            return "application/json", json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
        if format != "zip":
            raise ValueError("format must be json or zip.")
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("workspace.json", json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
            archive.writestr("README.txt", "Sustainable Catalyst Site Intelligence institutional workspace archive. This export is read-only and does not provision accounts or write to another system.\n")
        return "application/zip", buffer.getvalue()

    def workspace_detail(self, workspace_id: str, public: bool = False) -> dict[str, Any]:
        workspace = self._workspace(workspace_id)
        if public:
            if workspace.get("visibility") != "public" or workspace.get("status") != "published":
                raise KeyError(workspace_id)
            return self._public_workspace(workspace)
        return {
            "ok": True,
            "version": RELEASE_VERSION,
            "workspace": workspace,
            "members": self.members(workspace_id),
            "assignments": self.assignments(workspace_id),
            "comments": self.comments(workspace_id),
            "reviews": self.reviews(workspace_id),
            "collections": self.collections(workspace_id),
            "activity": self.activity(workspace_id, 250),
            "publication_ready": self._publication_ready(workspace_id),
        }

    def diagnostics(self, public: bool = False) -> dict[str, Any]:
        workspaces = self.workspaces(False)
        summary = {
            "workspace_count": len(workspaces),
            "public_workspace_count": len([w for w in workspaces if w.get("visibility") == "public" and w.get("status") == "published"]),
            "member_count": len(_latest(self.members_path, "membership_id", self.max_records)),
            "assignment_count": len(_latest(self.assignments_path, "assignment_id", self.max_records)),
            "comment_count": len(_latest(self.comments_path, "comment_id", self.max_comments)),
            "evidence_review_count": len(_latest(self.reviews_path, "review_id", self.max_records)),
            "source_collection_count": len(_latest(self.collections_path, "collection_id", self.max_records)),
        }
        base = {
            "ok": True,
            "version": RELEASE_VERSION,
            "schema": SCHEMA_VERSION,
            "summary": summary,
            "roles": sorted(ROLES),
            "role_permissions": {key: sorted(value) for key, value in PERMISSIONS.items()},
            "persistent_authentication_claimed": False,
            "public_accounts_required": False,
            "automatic_publication": False,
            "automatic_evidence_approval": False,
            "individual_tracking": False,
        }
        if public:
            base.pop("role_permissions", None)
            base["methodology"] = "Public diagnostics expose aggregate counts and governance boundaries only. Member identities, private workspaces, comments, assignments, and review notes remain private."
        else:
            base["storage"] = {
                "workspaces": str(self.workspaces_path), "members": str(self.members_path), "assignments": str(self.assignments_path),
                "comments": str(self.comments_path), "reviews": str(self.reviews_path), "collections": str(self.collections_path),
                "activity": str(self.activity_path), "retention": str(self.retention_path),
            }
        return base

    def public_summary(self) -> dict[str, Any]:
        return {
            "ok": True,
            "version": RELEASE_VERSION,
            "schema": SCHEMA_VERSION,
            "workspaces": self.workspaces(public=True),
            "diagnostics": self.diagnostics(public=True),
            "governance": self.policy,
        }

    def control_center(self) -> dict[str, Any]:
        return {
            "ok": True,
            "version": RELEASE_VERSION,
            "schema": SCHEMA_VERSION,
            "summary": self.diagnostics(public=False)["summary"],
            "workspaces": self.workspaces(False),
            "recent_activity": list(reversed(_read_jsonl(self.activity_path, 100)[-100:])),
            "retention_receipts": list(reversed(_read_jsonl(self.retention_path, 100)[-100:])),
            "policy": self.policy,
            "authentication": {
                "mode": "external-token-boundary",
                "persistent_identity_provider_included": False,
                "note": "This release defines roles and permission checks but does not provision institutional accounts or replace an identity provider.",
            },
        }
