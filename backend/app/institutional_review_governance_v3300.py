"""Institutional Workspaces and Review Governance for Site Intelligence v4.35.10.

The public contracts in this module prepare portable workspace, review, annotation,
audit, export, and import-preview artifacts. They never provision accounts, persist
private collaboration records, approve evidence, or publish content automatically.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any, Mapping

from .version import APP_VERSION

SCHEMA = "sc-site-intelligence-institutional-governance/1.0"
WORKSPACE_SCHEMA = "sc-site-intelligence-portable-workspace/1.0"
POLICY_PATH = Path(__file__).resolve().parents[1] / "data" / "institutional_review_governance_policy_v3300.json"
_SECRET = re.compile(r"(?:password|secret|token|authorization|cookie|session|api[_-]?key|email|phone|address|user[_-]?id|person[_-]?id)", re.I)
ROLES = ("preparer", "reviewer", "publisher", "administrator")
REVIEW_STATES = ("pending", "in_review", "needs_changes", "approved", "rejected", "withdrawn")
ANNOTATION_TYPES = ("comment", "question", "concern", "methodology", "source", "decision_note")


def _policy() -> dict[str, Any]:
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def _text(value: Any, limit: int = 2000) -> str:
    return str(value or "").strip()[:limit]


def _list(value: Any, maximum: int = 500) -> list[Any]:
    return list(value[:maximum]) if isinstance(value, list) else []


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def _digest(value: Any) -> str:
    return sha256(_canonical(value)).hexdigest()


def _scan(value: Any, path: str = "request") -> list[str]:
    issues: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            if _SECRET.search(str(key)):
                issues.append(f"{path}.{key} is not permitted in a portable public-safe workspace package")
            issues.extend(_scan(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value[:1000]):
            issues.extend(_scan(child, f"{path}[{index}]"))
    return issues


def _role(value: Any, fallback: str = "preparer") -> str:
    role = _text(value or fallback, 40).lower()
    if role not in ROLES:
        raise ValueError("unsupported workspace role")
    return role


def _evidence(raw: Mapping[str, Any], index: int) -> dict[str, Any]:
    row = {
        "evidence_id": _text(raw.get("evidence_id") or raw.get("record_id") or raw.get("id") or f"evidence-{index+1}", 180),
        "title": _text(raw.get("title") or raw.get("name") or "Evidence record", 500),
        "source_id": _text(raw.get("source_id") or raw.get("source"), 180),
        "truth_state": _text(raw.get("truth_state") or "unknown", 80).lower(),
        "review_state": _text(raw.get("review_state") or "pending", 40).lower(),
        "limitations": [_text(x, 600) for x in _list(raw.get("limitations"), 40) if _text(x, 600)],
    }
    if row["review_state"] not in REVIEW_STATES:
        row["review_state"] = "pending"
    row["record_sha256"] = _digest(row)
    return row


def _annotation(raw: Mapping[str, Any], index: int) -> dict[str, Any]:
    annotation_type = _text(raw.get("annotation_type") or raw.get("type") or "comment", 60).lower()
    if annotation_type not in ANNOTATION_TYPES:
        annotation_type = "comment"
    row = {
        "annotation_id": _text(raw.get("annotation_id") or raw.get("id") or f"annotation-{index+1}", 180),
        "target_id": _text(raw.get("target_id") or raw.get("evidence_id") or raw.get("record_id"), 180),
        "annotation_type": annotation_type,
        "author_role": _role(raw.get("author_role") or "reviewer", "reviewer"),
        "text": _text(raw.get("text") or raw.get("note"), 4000),
        "resolution_state": _text(raw.get("resolution_state") or "open", 60).lower(),
    }
    row["annotation_sha256"] = _digest(row)
    return row


class InstitutionalReviewGovernance:
    def __init__(self) -> None:
        self.policy = _policy()

    def schema(self) -> dict[str, Any]:
        return {
            "ok": True,
            "version": APP_VERSION,
            "schema": SCHEMA,
            "contract": "institutional-workspaces-review-governance",
            "roles": list(ROLES),
            "review_states": list(REVIEW_STATES),
            "annotation_types": list(ANNOTATION_TYPES),
            "portable_workspace_schema": WORKSPACE_SCHEMA,
            "persistent_identity_provider_included": False,
            "public_accounts_required": False,
            "paid_multi_tenant_infrastructure_required": False,
            "automatic_evidence_approval": False,
            "automatic_publication": False,
            "public_write_performed": False,
            "boundaries": list(self.policy["principles"]),
        }

    def workspace_preview(self, request: Mapping[str, Any] | None = None) -> dict[str, Any]:
        request = dict(request or {})
        issues = _scan(request)
        if issues:
            raise ValueError("; ".join(issues[:5]))
        title = _text(request.get("title"), 500)
        if not title:
            raise ValueError("title is required")
        workspace_id = _text(request.get("workspace_id") or "workspace:portable-preview", 180)
        evidence = [_evidence(x, i) for i, x in enumerate(_list(request.get("evidence"), 1000)) if isinstance(x, Mapping)]
        annotations = [_annotation(x, i) for i, x in enumerate(_list(request.get("annotations"), 1000)) if isinstance(x, Mapping)]
        workspace = {
            "schema": WORKSPACE_SCHEMA,
            "version": APP_VERSION,
            "workspace_id": workspace_id,
            "title": title,
            "summary": _text(request.get("summary"), 5000),
            "topics": [_text(x, 200) for x in _list(request.get("topics"), 100) if _text(x, 200)],
            "geographies": [_text(x, 200).upper() for x in _list(request.get("geographies"), 100) if _text(x, 200)],
            "prepared_by_role": _role(request.get("prepared_by_role") or "preparer"),
            "workspace_state": _text(request.get("workspace_state") or "draft", 60).lower(),
            "evidence": evidence,
            "annotations": annotations,
            "evidence_count": len(evidence),
            "annotation_count": len(annotations),
            "review_required": True,
            "approval_required": True,
            "automatic_publication": False,
            "write_performed": False,
        }
        workspace["workspace_sha256"] = _digest({k: v for k, v in workspace.items() if k != "workspace_sha256"})
        return {"ok": True, "version": APP_VERSION, "schema": SCHEMA, "contract": "portable-workspace-preview", "workspace": workspace}

    def review_queue(self, request: Mapping[str, Any] | None = None) -> dict[str, Any]:
        workspace = self.workspace_preview(request)["workspace"]
        queue = []
        for row in workspace["evidence"]:
            if row["review_state"] in {"approved", "rejected", "withdrawn"}:
                continue
            queue.append({
                "queue_id": f"review:{workspace['workspace_id']}:{row['evidence_id']}",
                "workspace_id": workspace["workspace_id"],
                "evidence_id": row["evidence_id"],
                "title": row["title"],
                "truth_state": row["truth_state"],
                "review_state": row["review_state"],
                "required_role": "reviewer",
                "publisher_approval_separate": True,
            })
        return {"ok": True, "version": APP_VERSION, "schema": SCHEMA, "contract": "review-queue-preview", "queue": queue, "count": len(queue), "write_performed": False}

    def annotation_preview(self, request: Mapping[str, Any] | None = None) -> dict[str, Any]:
        request = dict(request or {})
        issues = _scan(request)
        if issues:
            raise ValueError("; ".join(issues[:5]))
        annotation = _annotation(request, 0)
        if not annotation["target_id"]:
            raise ValueError("target_id is required")
        if not annotation["text"]:
            raise ValueError("annotation text is required")
        return {"ok": True, "version": APP_VERSION, "schema": SCHEMA, "contract": "annotation-preview", "annotation": annotation, "write_performed": False}

    def decision_preview(self, request: Mapping[str, Any] | None = None) -> dict[str, Any]:
        request = dict(request or {})
        issues = _scan(request)
        if issues:
            raise ValueError("; ".join(issues[:5]))
        actor_role = _role(request.get("actor_role") or "reviewer", "reviewer")
        prepared_by_role = _role(request.get("prepared_by_role") or "preparer", "preparer")
        action = _text(request.get("action") or "approve_evidence", 80).lower()
        allowed_actions = {"request_changes", "approve_evidence", "reject_evidence", "approve_publication", "withdraw"}
        if action not in allowed_actions:
            raise ValueError("unsupported review action")
        reasons: list[str] = []
        allowed = True
        required_role = "reviewer"
        if action == "approve_publication":
            required_role = "publisher"
        if actor_role not in {required_role, "administrator"}:
            allowed = False; reasons.append(f"{action} requires {required_role} or administrator role")
        if action in {"approve_evidence", "approve_publication"} and actor_role == prepared_by_role and actor_role != "administrator":
            allowed = False; reasons.append("preparation and approval must be role-separated")
        decision = {
            "workspace_id": _text(request.get("workspace_id") or "workspace:portable-preview", 180),
            "target_id": _text(request.get("target_id") or request.get("evidence_id") or "workspace", 180),
            "action": action,
            "actor_role": actor_role,
            "prepared_by_role": prepared_by_role,
            "required_role": required_role,
            "allowed": allowed,
            "reasons": reasons,
            "decision_state": "eligible-for-human-confirmation" if allowed else "blocked",
            "human_confirmation_required": True,
            "automatic_transition": False,
            "write_performed": False,
        }
        decision["decision_sha256"] = _digest(decision)
        return {"ok": True, "version": APP_VERSION, "schema": SCHEMA, "contract": "review-decision-preview", "decision": decision}

    def audit_preview(self, request: Mapping[str, Any] | None = None) -> dict[str, Any]:
        request = dict(request or {})
        workspace = self.workspace_preview(request)["workspace"]
        events = [{
            "sequence": 1,
            "event_type": "workspace_prepared",
            "workspace_id": workspace["workspace_id"],
            "actor_role": workspace["prepared_by_role"],
            "object_sha256": workspace["workspace_sha256"],
        }]
        for i, annotation in enumerate(workspace["annotations"], start=2):
            events.append({"sequence": i, "event_type": "annotation_prepared", "workspace_id": workspace["workspace_id"], "actor_role": annotation["author_role"], "object_sha256": annotation["annotation_sha256"]})
        chain = ""
        for event in events:
            event["previous_event_sha256"] = chain
            event["event_sha256"] = _digest(event)
            chain = event["event_sha256"]
        return {"ok": True, "version": APP_VERSION, "schema": SCHEMA, "contract": "append-only-audit-preview", "events": events, "event_count": len(events), "chain_head_sha256": chain, "complete_historical_log_claimed": False, "write_performed": False}

    def export_package(self, request: Mapping[str, Any] | None = None) -> dict[str, Any]:
        workspace = self.workspace_preview(request)["workspace"]
        queue = self.review_queue(request)
        audit = self.audit_preview(request)
        package = {
            "schema": "sc-site-intelligence-portable-workspace-package/1.0",
            "version": APP_VERSION,
            "workspace": workspace,
            "review_queue": queue["queue"],
            "audit_preview": audit["events"],
            "storage_adapter": "portable-json",
            "persistent_identity_included": False,
            "private_credentials_included": False,
            "remote_delivery_performed": False,
            "write_performed": False,
        }
        package["package_sha256"] = _digest({k: v for k, v in package.items() if k != "package_sha256"})
        return {"ok": True, "version": APP_VERSION, "schema": SCHEMA, "contract": "portable-workspace-export", "package": package}

    def import_preview(self, request: Mapping[str, Any] | None = None) -> dict[str, Any]:
        request = dict(request or {})
        issues = _scan(request)
        if issues:
            raise ValueError("; ".join(issues[:5]))
        package = request.get("package") if isinstance(request.get("package"), Mapping) else request
        schema = _text(package.get("schema"), 200)
        workspace = package.get("workspace") if isinstance(package.get("workspace"), Mapping) else {}
        checks = {
            "package_schema_supported": schema == "sc-site-intelligence-portable-workspace-package/1.0",
            "workspace_schema_supported": _text(workspace.get("schema"), 200) == WORKSPACE_SCHEMA,
            "workspace_id_present": bool(_text(workspace.get("workspace_id"), 180)),
            "title_present": bool(_text(workspace.get("title"), 500)),
            "credentials_absent": not bool(_scan(package)),
        }
        compatible = all(checks.values())
        return {
            "ok": True,
            "version": APP_VERSION,
            "schema": SCHEMA,
            "contract": "portable-workspace-import-preview",
            "compatible": compatible,
            "checks": checks,
            "import_allowed_after_human_review": compatible,
            "automatic_import": False,
            "write_performed": False,
            "note": "Compatibility does not authenticate the originating institution or approve the workspace contents.",
        }


_CENTER = InstitutionalReviewGovernance()

def public_institutional_governance() -> dict[str, Any]: return _CENTER.schema()
def public_workspace_governance_preview(request: Mapping[str, Any] | None = None) -> dict[str, Any]: return _CENTER.workspace_preview(request)
def public_review_queue_preview(request: Mapping[str, Any] | None = None) -> dict[str, Any]: return _CENTER.review_queue(request)
def public_annotation_governance_preview(request: Mapping[str, Any] | None = None) -> dict[str, Any]: return _CENTER.annotation_preview(request)
def public_review_decision_preview(request: Mapping[str, Any] | None = None) -> dict[str, Any]: return _CENTER.decision_preview(request)
def public_workspace_audit_preview(request: Mapping[str, Any] | None = None) -> dict[str, Any]: return _CENTER.audit_preview(request)
def public_workspace_package_export(request: Mapping[str, Any] | None = None) -> dict[str, Any]: return _CENTER.export_package(request)
def public_workspace_package_import_preview(request: Mapping[str, Any] | None = None) -> dict[str, Any]: return _CENTER.import_preview(request)
