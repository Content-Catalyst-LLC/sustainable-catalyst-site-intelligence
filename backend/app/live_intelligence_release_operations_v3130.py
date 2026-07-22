"""Release monitoring, rollback, and post-publication governance.

Site Intelligence v3.17.0 records externally performed publication deployments,
verifies immutable release checksums and public safeguards, prepares controlled
rollback and correction packages, and retains auditable manual handoff receipts.
It never performs a destination write, deployment, rollback, deletion, or
publication action by itself.
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

POLICY_SCHEMA_VERSION = "sc-site-intelligence-release-operations-policy/1.0"
DEPLOYMENT_SCHEMA_VERSION = "sc-site-intelligence-deployment-receipt/1.0"
EVENT_SCHEMA_VERSION = "sc-site-intelligence-release-operation-event/1.0"
ISSUE_SCHEMA_VERSION = "sc-site-intelligence-post-publication-issue/1.0"
CORRECTION_SCHEMA_VERSION = "sc-site-intelligence-correction-package/1.0"
ROLLBACK_SCHEMA_VERSION = "sc-site-intelligence-rollback-package/1.0"
HANDOFF_SCHEMA_VERSION = "sc-site-intelligence-release-operation-handoff/1.0"

ALLOWED_ENVIRONMENTS = ("production", "staging", "preview", "archive")
ALLOWED_SEVERITIES = ("informational", "minor", "major", "critical")
ALLOWED_CORRECTION_TYPES = ("correction_notice", "replacement", "withdrawal", "rollback_notice")
HANDOFF_ADAPTERS = ("publications", "knowledge_library", "wordpress_package", "download")
DENIED_IDENTITY_FIELDS = {
    "email", "email_address", "phone", "phone_number", "ip", "ip_address",
    "cookie", "session_id", "user_agent", "referrer", "recipient", "recipients",
    "subscriber", "subscriber_id", "subscriber_email", "contact_id", "metadata",
    "access_token", "api_key", "secret", "password", "webhook", "webhook_url",
    "authorization", "credentials", "token",
}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime | None = None) -> str:
    return (value or _utc_now()).astimezone(timezone.utc).isoformat()


def _safe_text(value: Any, limit: int = 1200) -> str:
    return " ".join(str(value or "").split())[:limit]


def _safe_id(value: Any, prefix: str = "item") -> str:
    text = _safe_text(value, 180).lower()
    text = re.sub(r"[^a-z0-9._:-]+", "-", text).strip("-._:")
    return text or f"{prefix}:{uuid4().hex[:16]}"


def _actor(value: Any, field: str = "actor") -> str:
    text = _safe_text(value, 120)
    if not text:
        raise ValueError(f"{field} is required.")
    if "@" in text or re.search(r"\b\+?\d[\d\s().-]{7,}\b", text):
        raise ValueError(f"{field} must be a role label or governance handle, not contact information.")
    return text


def _reject_identity_payload(value: Any, path: str = "request") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized = str(key).strip().lower().replace("-", "_")
            if normalized in DENIED_IDENTITY_FIELDS:
                raise ValueError(f"{path}.{key} is not accepted; identities, credentials, and delivery secrets are outside release operations.")
            _reject_identity_payload(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_identity_payload(child, f"{path}[{index}]")


def _digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)
    return sha256(raw.encode("utf-8")).hexdigest()


def _resolve(value: str) -> Path:
    return Path(value).expanduser()


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
        identifier = _safe_text(row.get(key), 180)
        if identifier:
            rows[identifier] = row
    return list(rows.values())


def _destination_reference(value: Any) -> str:
    text = _safe_text(value, 1000)
    lowered = text.lower()
    if re.search(r"://[^/\s]+@", text) or re.search(r"[?&](?:api[_-]?key|access[_-]?token|token|secret|password)=", lowered):
        raise ValueError("destination_reference must not contain embedded credentials or delivery secrets.")
    return text


def _list_text(value: Any, *, limit: int = 30, item_limit: int = 500) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    rows: list[str] = []
    for item in value[:limit]:
        text = _safe_text(item, item_limit)
        if text and text not in rows:
            rows.append(text)
    return rows


def release_operations_policy() -> dict[str, Any]:
    return {
        "ok": True,
        "version": APP_VERSION,
        "schema": POLICY_SCHEMA_VERSION,
        "principle": "Verify published release integrity, prepare controlled corrections and rollback packages, and retain human-confirmed receipts without performing destination writes.",
        "environments": list(ALLOWED_ENVIRONMENTS),
        "severities": list(ALLOWED_SEVERITIES),
        "correction_types": list(ALLOWED_CORRECTION_TYPES),
        "boundaries": {
            "approved_release_required": True,
            "checksum_verification_required": True,
            "human_verification_required": True,
            "separate_correction_approval_required": True,
            "separate_rollback_approval_required": True,
            "network_fetch_performed": False,
            "deployment_performed": False,
            "rollback_performed": False,
            "destination_write_performed": False,
            "automatic_deletion": False,
            "credentials_stored": False,
            "recipient_identities_stored": False,
            "manual_handoff_receipts_retained": True,
        },
        "routes": {
            "policy": "/public/live-intelligence/release-operations/policy",
            "status": "/public/live-intelligence/release-operations/status",
            "corrections": "/public/live-intelligence/release-operations/corrections",
            "admin": "/admin/live-intelligence/release-operations",
        },
    }


class LiveIntelligenceReleaseOperationsCenter:
    def __init__(
        self,
        settings: Settings,
        *,
        publication_center: Any,
        now_fn: Callable[[], datetime] = _utc_now,
    ) -> None:
        self.settings = settings
        self.publication_center = publication_center
        self.now_fn = now_fn
        self.deployments_path = _resolve(settings.live_intelligence_release_deployments_path)
        self.events_path = _resolve(settings.live_intelligence_release_operation_events_path)
        self.issues_path = _resolve(settings.live_intelligence_release_issues_path)
        self.corrections_path = _resolve(settings.live_intelligence_release_corrections_path)
        self.rollbacks_path = _resolve(settings.live_intelligence_release_rollbacks_path)
        self.handoffs_path = _resolve(settings.live_intelligence_release_operation_handoffs_path)
        self.max_records = int(settings.live_intelligence_release_operations_max_records)
        self.require_separation = bool(settings.live_intelligence_release_operations_require_separation_of_duties)

    def _event(self, entity_id: str, event_type: str, actor: str, detail: Mapping[str, Any]) -> dict[str, Any]:
        event = {
            "schema": EVENT_SCHEMA_VERSION,
            "release_version": APP_VERSION,
            "event_id": f"release-operation-event:{uuid4().hex[:20]}",
            "entity_id": entity_id,
            "event_type": event_type,
            "actor": actor,
            "occurred_at": _iso(self.now_fn()),
            "detail": deepcopy(dict(detail)),
        }
        event["event_sha256"] = _digest({k: v for k, v in event.items() if k != "event_sha256"})
        _append(self.events_path, event)
        return event

    def _rows(self, path: Path, key: str, limit: int = 500) -> list[dict[str, Any]]:
        rows = [row for row in _latest(path, key, self.max_records) if not row.get("deleted")]
        return sorted(rows, key=lambda row: str(row.get("updated_at") or row.get("created_at") or ""), reverse=True)[:max(1, min(int(limit), 1000))]

    def _one(self, path: Path, key: str, value: str, prefix: str) -> dict[str, Any]:
        target = _safe_id(value, prefix)
        for row in self._rows(path, key, 1000):
            if row.get(key) == target:
                return row
        raise KeyError(target)

    def deployments(self, limit: int = 100) -> list[dict[str, Any]]:
        return self._rows(self.deployments_path, "deployment_id", limit)

    def deployment(self, deployment_id: str) -> dict[str, Any]:
        return self._one(self.deployments_path, "deployment_id", deployment_id, "deployment")

    def issues(self, limit: int = 100) -> list[dict[str, Any]]:
        return self._rows(self.issues_path, "issue_id", limit)

    def issue(self, issue_id: str) -> dict[str, Any]:
        return self._one(self.issues_path, "issue_id", issue_id, "release-issue")

    def corrections(self, limit: int = 100) -> list[dict[str, Any]]:
        return self._rows(self.corrections_path, "correction_id", limit)

    def correction(self, correction_id: str) -> dict[str, Any]:
        return self._one(self.corrections_path, "correction_id", correction_id, "correction")

    def rollbacks(self, limit: int = 100) -> list[dict[str, Any]]:
        return self._rows(self.rollbacks_path, "rollback_id", limit)

    def rollback(self, rollback_id: str) -> dict[str, Any]:
        return self._one(self.rollbacks_path, "rollback_id", rollback_id, "rollback")

    @staticmethod
    def _package(release: Mapping[str, Any], adapter_id: str) -> dict[str, Any]:
        for package in release.get("packages") or []:
            if isinstance(package, Mapping) and package.get("adapter_id") == adapter_id:
                return dict(package)
        raise ValueError("The selected adapter is not present in the approved release package.")

    def register_deployment(self, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_identity_payload(request)
        actor = _actor(request.get("actor"))
        release = self.publication_center.release(_safe_id(request.get("release_id"), "publication-release"))
        if release.get("status") not in {"approved", "handoff_ready"}:
            raise ValueError("Only an approved publication release may receive a deployment receipt.")
        adapter_id = _safe_text(request.get("adapter_id"), 80).lower()
        package = self._package(release, adapter_id)
        environment = _safe_text(request.get("environment") or "production", 40).lower()
        if environment not in ALLOWED_ENVIRONMENTS:
            raise ValueError("Unsupported deployment environment.")
        destination_label = _safe_text(request.get("destination_label"), 240)
        destination_reference = _destination_reference(request.get("destination_reference"))
        if not destination_label or not destination_reference:
            raise ValueError("destination_label and destination_reference are required.")
        now = _iso(self.now_fn())
        record = {
            "schema": DEPLOYMENT_SCHEMA_VERSION,
            "release_version": APP_VERSION,
            "deployment_id": _safe_id(request.get("deployment_id") or f"deployment:{uuid4().hex[:20]}", "deployment"),
            "release_id": release.get("release_id"),
            "workspace_id": release.get("workspace_id"),
            "adapter_id": adapter_id,
            "environment": environment,
            "destination_label": destination_label,
            "destination_reference": destination_reference,
            "state": "reported",
            "reported_by": actor,
            "reported_at": now,
            "verified_by": "",
            "verified_at": "",
            "verification": {},
            "release_sha256": release.get("release_sha256"),
            "payload_sha256": release.get("payload_sha256"),
            "package_sha256": package.get("package_sha256"),
            "external_deployment_reported": True,
            "network_fetch_performed": False,
            "deployment_performed_by_site_intelligence": False,
            "destination_write_performed": False,
            "created_at": now,
            "updated_at": now,
        }
        record["deployment_sha256"] = _digest({k: v for k, v in record.items() if k != "deployment_sha256"})
        _append(self.deployments_path, record)
        self._event(record["deployment_id"], "deployment_reported", actor, {"release_id": record["release_id"], "adapter_id": adapter_id, "environment": environment})
        return {"ok": True, "version": APP_VERSION, "deployment": record}

    def verify_deployment(self, deployment_id: str, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_identity_payload(request)
        actor = _actor(request.get("actor"))
        reason = _safe_text(request.get("reason"), 1400)
        if not reason:
            raise ValueError("reason is required.")
        current = self.deployment(deployment_id)
        if current.get("state") not in {"reported", "verification_failed", "verified"}:
            raise ValueError("Deployment is not eligible for verification.")
        observed = {
            "release_sha256": _safe_text(request.get("observed_release_sha256"), 128),
            "payload_sha256": _safe_text(request.get("observed_payload_sha256"), 128),
            "package_sha256": _safe_text(request.get("observed_package_sha256"), 128),
        }
        if not all(observed.values()):
            raise ValueError("Observed release, payload, and package checksums are required.")
        checks = {
            "release_checksum_matches": observed["release_sha256"] == current.get("release_sha256"),
            "payload_checksum_matches": observed["payload_sha256"] == current.get("payload_sha256"),
            "package_checksum_matches": observed["package_sha256"] == current.get("package_sha256"),
            "destination_accessible": request.get("destination_accessible") is True,
            "source_links_present": request.get("source_links_present") is True,
            "freshness_labels_present": request.get("freshness_labels_present") is True,
            "correction_path_present": request.get("correction_path_present") is True,
        }
        passed = all(checks.values())
        updated = dict(current)
        updated.update({
            "state": "verified" if passed else "verification_failed",
            "verified_by": actor,
            "verified_at": _iso(self.now_fn()),
            "verification": {"passed": passed, "checks": checks, "observed": observed, "reason": reason},
            "network_fetch_performed": False,
            "updated_at": _iso(self.now_fn()),
        })
        updated["deployment_sha256"] = _digest({k: v for k, v in updated.items() if k != "deployment_sha256"})
        _append(self.deployments_path, updated)
        self._event(updated["deployment_id"], "deployment_verified", actor, {"passed": passed, "checks": checks, "reason": reason})
        return {"ok": True, "version": APP_VERSION, "deployment": updated, "verification": updated["verification"]}

    def report_issue(self, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_identity_payload(request)
        actor = _actor(request.get("actor"))
        deployment_id = _safe_text(request.get("deployment_id"), 180)
        release_id = _safe_text(request.get("release_id"), 180)
        deployment: dict[str, Any] | None = None
        if deployment_id:
            deployment = self.deployment(deployment_id)
            release_id = str(deployment.get("release_id") or "")
        if not release_id:
            raise ValueError("release_id or deployment_id is required.")
        release = self.publication_center.release(_safe_id(release_id, "publication-release"))
        severity = _safe_text(request.get("severity") or "minor", 40).lower()
        if severity not in ALLOWED_SEVERITIES:
            raise ValueError("Unsupported issue severity.")
        title = _safe_text(request.get("title"), 400)
        description = _safe_text(request.get("description"), 5000)
        if not title or not description:
            raise ValueError("title and description are required.")
        now = _iso(self.now_fn())
        record = {
            "schema": ISSUE_SCHEMA_VERSION,
            "release_version": APP_VERSION,
            "issue_id": _safe_id(request.get("issue_id") or f"release-issue:{uuid4().hex[:20]}", "release-issue"),
            "release_id": release.get("release_id"),
            "deployment_id": deployment.get("deployment_id") if deployment else "",
            "severity": severity,
            "title": title,
            "description": description,
            "evidence_references": _list_text(request.get("evidence_references")),
            "status": "open",
            "reported_by": actor,
            "reported_at": now,
            "resolved_at": "",
            "correction_id": "",
            "rollback_id": "",
            "public_visible": False,
            "destination_write_performed": False,
            "created_at": now,
            "updated_at": now,
        }
        record["issue_sha256"] = _digest({k: v for k, v in record.items() if k != "issue_sha256"})
        _append(self.issues_path, record)
        self._event(record["issue_id"], "issue_reported", actor, {"release_id": record["release_id"], "deployment_id": record["deployment_id"], "severity": severity})
        return {"ok": True, "version": APP_VERSION, "issue": record}

    def propose_correction(self, issue_id: str, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_identity_payload(request)
        actor = _actor(request.get("actor"))
        issue = self.issue(issue_id)
        if issue.get("status") == "resolved":
            raise ValueError("Resolved issues cannot receive a new correction package.")
        correction_type = _safe_text(request.get("correction_type") or "correction_notice", 60).lower()
        if correction_type not in ALLOWED_CORRECTION_TYPES:
            raise ValueError("Unsupported correction type.")
        summary = _safe_text(request.get("summary"), 3000)
        rationale = _safe_text(request.get("rationale"), 3000)
        if not summary or not rationale:
            raise ValueError("summary and rationale are required.")
        replacement_release_id = _safe_text(request.get("replacement_release_id"), 180)
        replacement_release: dict[str, Any] | None = None
        if replacement_release_id:
            replacement_release = self.publication_center.release(_safe_id(replacement_release_id, "publication-release"))
            if replacement_release.get("status") not in {"approved", "handoff_ready"}:
                raise ValueError("Replacement releases must be approved.")
        if correction_type == "replacement" and not replacement_release:
            raise ValueError("replacement_release_id is required for a replacement correction.")
        now = _iso(self.now_fn())
        record = {
            "schema": CORRECTION_SCHEMA_VERSION,
            "release_version": APP_VERSION,
            "correction_id": _safe_id(request.get("correction_id") or f"correction:{uuid4().hex[:20]}", "correction"),
            "issue_id": issue.get("issue_id"),
            "release_id": issue.get("release_id"),
            "deployment_id": issue.get("deployment_id"),
            "correction_type": correction_type,
            "summary": summary,
            "rationale": rationale,
            "replacement_release_id": replacement_release.get("release_id") if replacement_release else "",
            "replacement_release_sha256": replacement_release.get("release_sha256") if replacement_release else "",
            "status": "draft",
            "created_by": actor,
            "created_at": now,
            "approved_by": "",
            "approved_at": "",
            "approval_reason": "",
            "public_visible": False,
            "destination_write_performed": False,
            "updated_at": now,
        }
        record["correction_sha256"] = _digest({k: v for k, v in record.items() if k != "correction_sha256"})
        _append(self.corrections_path, record)
        issue_updated = dict(issue)
        issue_updated.update({"status": "correction_drafted", "correction_id": record["correction_id"], "updated_at": now})
        issue_updated["issue_sha256"] = _digest({k: v for k, v in issue_updated.items() if k != "issue_sha256"})
        _append(self.issues_path, issue_updated)
        self._event(record["correction_id"], "correction_drafted", actor, {"issue_id": issue.get("issue_id"), "correction_type": correction_type})
        return {"ok": True, "version": APP_VERSION, "correction": record, "issue": issue_updated}

    def approve_correction(self, correction_id: str, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_identity_payload(request)
        approver = _actor(request.get("approved_by"), "approved_by")
        reason = _safe_text(request.get("reason"), 1600)
        if not reason:
            raise ValueError("reason is required.")
        current = self.correction(correction_id)
        if current.get("status") != "draft":
            raise ValueError("Only a draft correction may be approved.")
        if self.require_separation and approver == current.get("created_by"):
            raise ValueError("Correction approval requires separation of duties from correction preparation.")
        now = _iso(self.now_fn())
        updated = dict(current)
        updated.update({
            "status": "approved",
            "approved_by": approver,
            "approved_at": now,
            "approval_reason": reason,
            "public_visible": request.get("public_visible") is True,
            "updated_at": now,
        })
        updated["correction_sha256"] = _digest({k: v for k, v in updated.items() if k != "correction_sha256"})
        _append(self.corrections_path, updated)
        issue = self.issue(str(updated.get("issue_id")))
        issue_updated = dict(issue)
        issue_updated.update({"status": "correction_approved", "public_visible": updated["public_visible"], "updated_at": now})
        issue_updated["issue_sha256"] = _digest({k: v for k, v in issue_updated.items() if k != "issue_sha256"})
        _append(self.issues_path, issue_updated)
        self._event(updated["correction_id"], "correction_approved", approver, {"issue_id": updated.get("issue_id"), "public_visible": updated["public_visible"], "reason": reason})
        return {"ok": True, "version": APP_VERSION, "correction": updated, "issue": issue_updated}

    def prepare_rollback(self, deployment_id: str, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_identity_payload(request)
        actor = _actor(request.get("actor"))
        reason = _safe_text(request.get("reason"), 1800)
        if not reason:
            raise ValueError("reason is required.")
        deployment = self.deployment(deployment_id)
        target_release = self.publication_center.release(_safe_id(request.get("target_release_id"), "publication-release"))
        if target_release.get("status") not in {"approved", "handoff_ready"}:
            raise ValueError("Rollback target must be an approved release.")
        if target_release.get("release_id") == deployment.get("release_id"):
            raise ValueError("Rollback target must differ from the deployed release.")
        target_package = self._package(target_release, str(deployment.get("adapter_id") or ""))
        now = _iso(self.now_fn())
        record = {
            "schema": ROLLBACK_SCHEMA_VERSION,
            "release_version": APP_VERSION,
            "rollback_id": _safe_id(request.get("rollback_id") or f"rollback:{uuid4().hex[:20]}", "rollback"),
            "deployment_id": deployment.get("deployment_id"),
            "adapter_id": deployment.get("adapter_id"),
            "environment": deployment.get("environment"),
            "from_release_id": deployment.get("release_id"),
            "from_release_sha256": deployment.get("release_sha256"),
            "from_package_sha256": deployment.get("package_sha256"),
            "target_release_id": target_release.get("release_id"),
            "target_release_sha256": target_release.get("release_sha256"),
            "target_payload_sha256": target_release.get("payload_sha256"),
            "target_package_sha256": target_package.get("package_sha256"),
            "reason": reason,
            "status": "prepared",
            "prepared_by": actor,
            "prepared_at": now,
            "approved_by": "",
            "approved_at": "",
            "approval_reason": "",
            "manual_confirmation_required": True,
            "rollback_performed": False,
            "destination_write_performed": False,
            "created_at": now,
            "updated_at": now,
        }
        record["rollback_sha256"] = _digest({k: v for k, v in record.items() if k != "rollback_sha256"})
        _append(self.rollbacks_path, record)
        self._event(record["rollback_id"], "rollback_prepared", actor, {"deployment_id": deployment.get("deployment_id"), "target_release_id": target_release.get("release_id")})
        return {"ok": True, "version": APP_VERSION, "rollback": record}

    def approve_rollback(self, rollback_id: str, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_identity_payload(request)
        approver = _actor(request.get("approved_by"), "approved_by")
        reason = _safe_text(request.get("reason"), 1600)
        if not reason:
            raise ValueError("reason is required.")
        current = self.rollback(rollback_id)
        if current.get("status") != "prepared":
            raise ValueError("Only a prepared rollback may be approved.")
        if self.require_separation and approver == current.get("prepared_by"):
            raise ValueError("Rollback approval requires separation of duties from rollback preparation.")
        updated = dict(current)
        updated.update({"status": "approved", "approved_by": approver, "approved_at": _iso(self.now_fn()), "approval_reason": reason, "updated_at": _iso(self.now_fn())})
        updated["rollback_sha256"] = _digest({k: v for k, v in updated.items() if k != "rollback_sha256"})
        _append(self.rollbacks_path, updated)
        self._event(updated["rollback_id"], "rollback_approved", approver, {"reason": reason, "rollback_performed": False})
        return {"ok": True, "version": APP_VERSION, "rollback": updated}

    def create_handoff(self, entity_type: str, entity_id: str, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_identity_payload(request)
        actor = _actor(request.get("actor"))
        normalized = _safe_text(entity_type, 40).lower()
        if normalized == "correction":
            entity = self.correction(entity_id)
            if entity.get("status") != "approved":
                raise ValueError("Only an approved correction may create a handoff receipt.")
        elif normalized == "rollback":
            entity = self.rollback(entity_id)
            if entity.get("status") != "approved":
                raise ValueError("Only an approved rollback may create a handoff receipt.")
        else:
            raise ValueError("entity_type must be correction or rollback.")
        requested = request.get("adapters") or list(HANDOFF_ADAPTERS)
        if not isinstance(requested, Sequence) or isinstance(requested, (str, bytes)):
            raise ValueError("adapters must be a list.")
        adapters: list[str] = []
        for value in requested:
            adapter = _safe_text(value, 80).lower()
            if adapter not in HANDOFF_ADAPTERS:
                raise ValueError("Unsupported release-operation handoff adapter.")
            if adapter not in adapters:
                adapters.append(adapter)
        handoff = {
            "schema": HANDOFF_SCHEMA_VERSION,
            "release_version": APP_VERSION,
            "handoff_id": f"release-operation-handoff:{uuid4().hex[:20]}",
            "entity_type": normalized,
            "entity_id": entity.get(f"{normalized}_id"),
            "entity_sha256": entity.get(f"{normalized}_sha256"),
            "created_by": actor,
            "created_at": _iso(self.now_fn()),
            "adapters": adapters,
            "states": [{"adapter_id": adapter, "state": "download_ready" if adapter == "download" else "manual_delivery_ready", "destination_write_performed": False} for adapter in adapters],
            "credentials_included": False,
            "recipient_data_included": False,
            "deployment_performed": False,
            "rollback_performed": False,
            "destination_write_performed": False,
        }
        handoff["handoff_sha256"] = _digest({k: v for k, v in handoff.items() if k != "handoff_sha256"})
        _append(self.handoffs_path, handoff)
        self._event(str(handoff["entity_id"]), f"{normalized}_handoff_created", actor, {"handoff_id": handoff["handoff_id"], "adapters": adapters})
        return {"ok": True, "version": APP_VERSION, "handoff": handoff}

    def public_corrections(self, limit: int = 50) -> list[dict[str, Any]]:
        rows = [row for row in self.corrections(500) if row.get("status") == "approved" and row.get("public_visible") is True]
        return [{
            "correction_id": row.get("correction_id"),
            "issue_id": row.get("issue_id"),
            "release_id": row.get("release_id"),
            "correction_type": row.get("correction_type"),
            "summary": row.get("summary"),
            "replacement_release_id": row.get("replacement_release_id"),
            "approved_at": row.get("approved_at"),
            "destination_write_performed": False,
        } for row in rows[:max(1, min(int(limit), 200))]]

    def history(self, entity_id: str, limit: int = 200) -> list[dict[str, Any]]:
        target = _safe_id(entity_id, "release-operation")
        rows = [row for row in _read_jsonl(self.events_path, self.max_records) if row.get("entity_id") == target]
        return rows[-max(1, min(int(limit), 1000)):]

    def status(self) -> dict[str, Any]:
        deployments = self.deployments(1000)
        issues = self.issues(1000)
        corrections = self.corrections(1000)
        rollbacks = self.rollbacks(1000)
        handoffs = _latest(self.handoffs_path, "handoff_id", self.max_records)
        return {
            "ok": True,
            "version": APP_VERSION,
            "schema": POLICY_SCHEMA_VERSION,
            "deployment_count": len(deployments),
            "verified_deployment_count": sum(1 for row in deployments if row.get("state") == "verified"),
            "verification_failed_count": sum(1 for row in deployments if row.get("state") == "verification_failed"),
            "open_issue_count": sum(1 for row in issues if row.get("status") != "resolved"),
            "approved_correction_count": sum(1 for row in corrections if row.get("status") == "approved"),
            "public_correction_count": len(self.public_corrections(500)),
            "approved_rollback_count": sum(1 for row in rollbacks if row.get("status") == "approved"),
            "handoff_count": len(handoffs),
            "separation_of_duties_required": self.require_separation,
            "network_fetch_performed": False,
            "deployment_performed": False,
            "rollback_performed": False,
            "destination_write_performed": False,
        }

    def control_center(self) -> dict[str, Any]:
        return {
            "ok": True,
            "version": APP_VERSION,
            "policy": release_operations_policy(),
            "status": self.status(),
            "deployments": self.deployments(100),
            "issues": self.issues(100),
            "corrections": self.corrections(100),
            "rollbacks": self.rollbacks(100),
            "handoffs": _latest(self.handoffs_path, "handoff_id", self.max_records)[-100:],
        }
