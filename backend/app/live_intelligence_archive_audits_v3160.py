"""Archive verification, preservation audits, and institutional custody.

Site Intelligence v3.22.0 audits approved public archive records, verifies
checksum and provenance-chain integrity, records preservation findings, and
prepares institution-ready custody packages. The workflow is append-only and
human-governed. It performs no remote deposit, archive mutation, deletion,
credential storage, or automatic scheduling.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from typing import Any, Callable, Mapping
from uuid import uuid4

from .config import Settings
from .version import APP_VERSION
from .live_intelligence_release_operations_v3130 import (
    _actor,
    _append,
    _digest,
    _iso,
    _latest,
    _read_jsonl,
    _reject_identity_payload,
    _resolve,
    _safe_id,
    _safe_text,
)

POLICY_SCHEMA_VERSION = "sc-site-intelligence-archive-audit-policy/1.0"
AUDIT_SCHEMA_VERSION = "sc-site-intelligence-archive-audit/1.0"
FINDING_SCHEMA_VERSION = "sc-site-intelligence-preservation-finding/1.0"
CUSTODY_SCHEMA_VERSION = "sc-site-intelligence-custody-transfer/1.0"
EVENT_SCHEMA_VERSION = "sc-site-intelligence-archive-audit-event/1.0"
PACKAGE_SCHEMA_VERSION = "sc-site-intelligence-custody-package/1.0"

AUDIT_TYPES = ("full_chain", "record_sample", "retention_review", "custody_review")
AUDIT_CADENCES = ("manual", "quarterly", "semiannual", "annual")
CUSTODY_ADAPTERS = ("institutional_archive", "knowledge_library", "publications", "offline_preservation")
FINDING_SEVERITIES = ("info", "warning", "critical")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def archive_audit_policy() -> dict[str, Any]:
    return {
        "ok": True,
        "version": APP_VERSION,
        "schema": POLICY_SCHEMA_VERSION,
        "principle": "Verify preserved public records through repeatable checksum, manifest, provenance-chain, retention, and custody audits while keeping source archives immutable.",
        "audit_types": list(AUDIT_TYPES),
        "cadences": list(AUDIT_CADENCES),
        "custody_adapters": list(CUSTODY_ADAPTERS),
        "boundaries": {
            "approved_archive_records_only": True,
            "separate_audit_approval_required": True,
            "separate_custody_approval_required": True,
            "append_only_audit_ledger": True,
            "automatic_scheduler_claimed": False,
            "archive_record_mutated": False,
            "archive_record_deleted": False,
            "remote_deposit_performed": False,
            "destination_write_performed": False,
            "credentials_stored": False,
            "recipient_identities_stored": False,
        },
        "routes": {
            "policy": "/public/live-intelligence/archive-audits/policy",
            "status": "/public/live-intelligence/archive-audits/status",
            "reports": "/public/live-intelligence/archive-audits",
            "report": "/public/live-intelligence/archive-audits/{audit_id}",
            "custody": "/public/live-intelligence/archive-audits/custody",
            "admin": "/admin/live-intelligence/archive-audits",
        },
    }


def _reject_audit_payload(value: Any, path: str = "request") -> None:
    _reject_identity_payload(value, path)
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized = str(key).strip().lower().replace("-", "_")
            if any(part in normalized for part in ("email", "password", "secret", "token", "credential", "recipient", "webhook", "authorization", "cookie")):
                raise ValueError(f"{path}.{key} is not accepted; identities and credentials are outside preservation audit records.")
            _reject_audit_payload(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_audit_payload(child, f"{path}[{index}]")


def _record_digest(record: Mapping[str, Any]) -> str:
    return _digest({key: value for key, value in record.items() if key != "record_sha256"})


class LiveIntelligenceArchiveAuditCenter:
    def __init__(
        self,
        settings: Settings,
        *,
        archive_center: Any,
        now_fn: Callable[[], datetime] = _utc_now,
    ) -> None:
        self.settings = settings
        self.archive_center = archive_center
        self.now_fn = now_fn
        self.audits_path = _resolve(settings.live_intelligence_archive_audits_path)
        self.events_path = _resolve(settings.live_intelligence_archive_audit_events_path)
        self.custody_path = _resolve(settings.live_intelligence_archive_custody_path)
        self.max_records = int(settings.live_intelligence_archive_audit_max_records)
        self.require_separation = bool(settings.live_intelligence_archive_audit_require_separation_of_duties)

    def _event(self, entity_id: str, event_type: str, actor: str, detail: Mapping[str, Any]) -> dict[str, Any]:
        event = {
            "schema": EVENT_SCHEMA_VERSION,
            "release_version": APP_VERSION,
            "event_id": f"archive-audit-event:{uuid4().hex[:20]}",
            "entity_id": entity_id,
            "event_type": event_type,
            "actor": actor,
            "occurred_at": _iso(self.now_fn()),
            "detail": deepcopy(dict(detail)),
            "archive_record_mutated": False,
            "archive_record_deleted": False,
            "destination_write_performed": False,
        }
        event["event_sha256"] = _digest({k: v for k, v in event.items() if k != "event_sha256"})
        _append(self.events_path, event)
        return event

    def audits(self, *, public: bool = False, limit: int = 1000) -> list[dict[str, Any]]:
        rows = _latest(self.audits_path, "audit_id", self.max_records)
        if public:
            rows = [row for row in rows if row.get("status") == "approved" and row.get("public_visible") is True]
        rows.sort(key=lambda row: str(row.get("approved_at") or row.get("completed_at") or row.get("created_at") or ""), reverse=True)
        return rows[:max(1, min(int(limit), 2000))]

    def audit(self, audit_id: str, *, public: bool = False) -> dict[str, Any]:
        target = _safe_id(audit_id, "archive-audit")
        for row in self.audits(public=public, limit=2000):
            if row.get("audit_id") == target:
                return row
        raise KeyError(target)

    def custody_transfers(self, *, public: bool = False, limit: int = 1000) -> list[dict[str, Any]]:
        rows = _latest(self.custody_path, "transfer_id", self.max_records)
        if public:
            rows = [row for row in rows if row.get("status") == "approved" and row.get("public_visible") is True]
        rows.sort(key=lambda row: str(row.get("approved_at") or row.get("created_at") or ""), reverse=True)
        return rows[:max(1, min(int(limit), 2000))]

    def custody_transfer(self, transfer_id: str, *, public: bool = False) -> dict[str, Any]:
        target = _safe_id(transfer_id, "custody-transfer")
        for row in self.custody_transfers(public=public, limit=2000):
            if row.get("transfer_id") == target:
                return row
        raise KeyError(target)

    def create_audit(self, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_audit_payload(request)
        actor = _actor(request.get("actor"))
        audit_type = _safe_text(request.get("audit_type") or "full_chain", 60).lower()
        cadence = _safe_text(request.get("cadence") or "manual", 40).lower()
        if audit_type not in AUDIT_TYPES:
            raise ValueError("Unsupported preservation audit type.")
        if cadence not in AUDIT_CADENCES:
            raise ValueError("Unsupported preservation audit cadence.")
        requested_ids = request.get("archive_ids") if isinstance(request.get("archive_ids"), list) else []
        archive_ids = [_safe_id(value, "public-archive") for value in requested_ids[:500]]
        sample_limit = max(1, min(int(request.get("sample_limit", 100)), 1000))
        now = self.now_fn()
        next_due = None
        if cadence == "quarterly":
            next_due = now + timedelta(days=90)
        elif cadence == "semiannual":
            next_due = now + timedelta(days=182)
        elif cadence == "annual":
            next_due = now + timedelta(days=365)
        audit_id = _safe_id(request.get("audit_id") or f"archive-audit:{uuid4().hex[:20]}", "archive-audit")
        record = {
            "schema": AUDIT_SCHEMA_VERSION,
            "release_version": APP_VERSION,
            "audit_id": audit_id,
            "audit_type": audit_type,
            "cadence": cadence,
            "archive_ids": archive_ids,
            "sample_limit": sample_limit,
            "scope_note": _safe_text(request.get("scope_note") or "Verify approved public archive integrity and custody readiness.", 3000),
            "status": "draft",
            "created_by": actor,
            "created_at": _iso(now),
            "updated_at": _iso(now),
            "next_due_at": _iso(next_due) if next_due else "",
            "findings": [],
            "summary": {},
            "public_visible": False,
            "automatic_scheduler_claimed": False,
            "archive_record_mutated": False,
            "archive_record_deleted": False,
            "destination_write_performed": False,
        }
        record["audit_sha256"] = _digest({k: v for k, v in record.items() if k != "audit_sha256"})
        _append(self.audits_path, record)
        self._event(audit_id, "archive_audit_created", actor, {"audit_type": audit_type, "cadence": cadence})
        return {"ok": True, "version": APP_VERSION, "audit": record}

    def _selected_records(self, audit: Mapping[str, Any]) -> list[dict[str, Any]]:
        rows = self.archive_center.records(public=True, limit=2000)
        selected = {str(value) for value in audit.get("archive_ids", []) if str(value)}
        if selected:
            rows = [row for row in rows if str(row.get("archive_id")) in selected]
        rows.sort(key=lambda row: str(row.get("created_at") or ""))
        return rows[: int(audit.get("sample_limit") or 100)]

    def _finding(self, audit_id: str, archive_id: str, check: str, severity: str, message: str) -> dict[str, Any]:
        finding = {
            "schema": FINDING_SCHEMA_VERSION,
            "finding_id": f"preservation-finding:{uuid4().hex[:20]}",
            "audit_id": audit_id,
            "archive_id": archive_id,
            "check": check,
            "severity": severity if severity in FINDING_SEVERITIES else "warning",
            "message": _safe_text(message, 2000),
            "created_at": _iso(self.now_fn()),
            "archive_record_mutated": False,
        }
        finding["finding_sha256"] = _digest({k: v for k, v in finding.items() if k != "finding_sha256"})
        return finding

    def run_audit(self, audit_id: str, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_audit_payload(request)
        actor = _actor(request.get("actor"))
        reason = _safe_text(request.get("reason") or "Run preservation integrity verification.", 2000)
        current = self.audit(audit_id)
        if current.get("status") not in {"draft", "review_required", "verified"}:
            raise ValueError("Only draft or reviewable audits may be run.")
        rows = self._selected_records(current)
        if not rows:
            raise ValueError("No approved public archive records matched the audit scope.")
        findings: list[dict[str, Any]] = []
        by_id = {str(row.get("archive_id")): row for row in self.archive_center.records(public=True, limit=2000)}
        verified_count = 0
        for record in rows:
            archive_id_value = str(record.get("archive_id") or "")
            record_matches = _record_digest(record) == record.get("record_sha256")
            if not record_matches:
                findings.append(self._finding(audit_id, archive_id_value, "record_checksum", "critical", "Archive record checksum does not match the retained record."))
            manifest = record.get("preservation_manifest") if isinstance(record.get("preservation_manifest"), Mapping) else {}
            manifest_matches = _digest(manifest) == record.get("preservation_manifest_sha256")
            if not manifest_matches:
                findings.append(self._finding(audit_id, archive_id_value, "manifest_checksum", "critical", "Preservation manifest checksum does not match the retained manifest."))
            source_snapshot = record.get("source_snapshot") if isinstance(record.get("source_snapshot"), Mapping) else {}
            if _digest(source_snapshot) != record.get("source_sha256"):
                findings.append(self._finding(audit_id, archive_id_value, "source_snapshot_checksum", "critical", "Preserved source snapshot checksum does not match the retained source checksum."))
            previous_id = str(record.get("previous_archive_id") or "")
            previous_sha = str(record.get("previous_record_sha256") or "")
            if previous_id:
                previous = by_id.get(previous_id)
                if not previous or str(previous.get("record_sha256") or "") != previous_sha:
                    findings.append(self._finding(audit_id, archive_id_value, "provenance_chain", "critical", "Previous archive chain link is missing or checksum-inconsistent."))
            try:
                verification = self.archive_center.verify_public_record(archive_id_value)
                if not verification.get("source_checksum_matches"):
                    findings.append(self._finding(audit_id, archive_id_value, "current_source_drift", "warning", "Current public source differs from the preserved source snapshot; the archive copy remains unchanged."))
            except (KeyError, ValueError):
                findings.append(self._finding(audit_id, archive_id_value, "public_verification", "warning", "Current public-source verification could not be completed."))
            if record_matches and manifest_matches:
                verified_count += 1
        critical_count = sum(1 for item in findings if item.get("severity") == "critical")
        warning_count = sum(1 for item in findings if item.get("severity") == "warning")
        status = "review_required" if critical_count or warning_count else "verified"
        updated = deepcopy(current)
        updated.update({
            "status": status,
            "run_by": actor,
            "run_reason": reason,
            "completed_at": _iso(self.now_fn()),
            "updated_at": _iso(self.now_fn()),
            "findings": findings,
            "summary": {
                "records_examined": len(rows),
                "records_checksum_verified": verified_count,
                "finding_count": len(findings),
                "critical_count": critical_count,
                "warning_count": warning_count,
                "integrity_passed": critical_count == 0,
            },
        })
        updated["audit_sha256"] = _digest({k: v for k, v in updated.items() if k != "audit_sha256"})
        _append(self.audits_path, updated)
        self._event(audit_id, "archive_audit_completed", actor, updated["summary"])
        return {"ok": True, "version": APP_VERSION, "audit": updated}

    def approve_audit(self, audit_id: str, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_audit_payload(request)
        approver = _actor(request.get("approved_by") or request.get("actor"))
        reason = _safe_text(request.get("reason"), 2000)
        if not reason:
            raise ValueError("An audit approval reason is required.")
        current = self.audit(audit_id)
        if current.get("status") not in {"verified", "review_required"}:
            raise ValueError("Audit must be completed before approval.")
        if self.require_separation and approver in {current.get("created_by"), current.get("run_by")}:
            raise ValueError("Audit approval requires separation of duties.")
        if current.get("summary", {}).get("critical_count") and not bool(request.get("critical_findings_acknowledged")):
            raise ValueError("Critical findings must be explicitly acknowledged before approval.")
        updated = deepcopy(current)
        updated.update({
            "status": "approved",
            "approved_by": approver,
            "approved_at": _iso(self.now_fn()),
            "approval_reason": reason,
            "public_visible": bool(request.get("public_visible", True)),
            "critical_findings_acknowledged": bool(request.get("critical_findings_acknowledged", False)),
            "updated_at": _iso(self.now_fn()),
        })
        updated["audit_sha256"] = _digest({k: v for k, v in updated.items() if k != "audit_sha256"})
        _append(self.audits_path, updated)
        self._event(audit_id, "archive_audit_approved", approver, {"public_visible": updated["public_visible"], "audit_sha256": updated["audit_sha256"]})
        return {"ok": True, "version": APP_VERSION, "audit": updated}

    def prepare_custody_transfer(self, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_audit_payload(request)
        actor = _actor(request.get("actor"))
        audit = self.audit(_safe_id(request.get("audit_id"), "archive-audit"))
        if audit.get("status") != "approved":
            raise ValueError("An approved archive audit is required before custody preparation.")
        adapter = _safe_text(request.get("adapter") or "institutional_archive", 80).lower()
        if adapter not in CUSTODY_ADAPTERS:
            raise ValueError("Unsupported custody adapter.")
        institution_reference = _safe_text(request.get("institution_reference") or "institutional-custody", 240)
        records = self._selected_records(audit)
        record_manifest = [
            {
                "archive_id": row.get("archive_id"),
                "record_sha256": row.get("record_sha256"),
                "preservation_manifest_sha256": row.get("preservation_manifest_sha256"),
            }
            for row in records
        ]
        transfer_id = _safe_id(request.get("transfer_id") or f"custody-transfer:{uuid4().hex[:20]}", "custody-transfer")
        transfer = {
            "schema": CUSTODY_SCHEMA_VERSION,
            "release_version": APP_VERSION,
            "transfer_id": transfer_id,
            "audit_id": audit.get("audit_id"),
            "audit_sha256": audit.get("audit_sha256"),
            "adapter": adapter,
            "institution_reference": institution_reference,
            "record_manifest": record_manifest,
            "record_count": len(record_manifest),
            "status": "prepared",
            "created_by": actor,
            "created_at": _iso(self.now_fn()),
            "updated_at": _iso(self.now_fn()),
            "public_visible": False,
            "manual_transfer_required": True,
            "remote_deposit_performed": False,
            "destination_write_performed": False,
            "archive_record_mutated": False,
            "archive_record_deleted": False,
        }
        transfer["package_sha256"] = _digest({k: v for k, v in transfer.items() if k not in {"transfer_sha256", "package_sha256"}})
        transfer["transfer_sha256"] = _digest({k: v for k, v in transfer.items() if k != "transfer_sha256"})
        _append(self.custody_path, transfer)
        self._event(transfer_id, "custody_transfer_prepared", actor, {"audit_id": audit.get("audit_id"), "record_count": len(record_manifest)})
        return {"ok": True, "version": APP_VERSION, "transfer": transfer}

    def verify_custody_transfer(self, transfer_id: str, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_audit_payload(request)
        actor = _actor(request.get("actor"))
        reason = _safe_text(request.get("reason"), 2000)
        if not reason:
            raise ValueError("A custody verification reason is required.")
        current = self.custody_transfer(transfer_id)
        if current.get("status") != "prepared":
            raise ValueError("Only prepared custody transfers may be verified.")
        expected = _digest({k: v for k, v in current.items() if k not in {"transfer_sha256", "package_sha256"}})
        if expected != current.get("package_sha256"):
            raise ValueError("Custody package checksum mismatch.")
        updated = deepcopy(current)
        updated.update({
            "status": "verified",
            "verified_by": actor,
            "verified_at": _iso(self.now_fn()),
            "verification_reason": reason,
            "updated_at": _iso(self.now_fn()),
        })
        updated["transfer_sha256"] = _digest({k: v for k, v in updated.items() if k != "transfer_sha256"})
        _append(self.custody_path, updated)
        self._event(transfer_id, "custody_transfer_verified", actor, {"package_sha256": current.get("package_sha256")})
        return {"ok": True, "version": APP_VERSION, "transfer": updated}

    def approve_custody_transfer(self, transfer_id: str, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_audit_payload(request)
        approver = _actor(request.get("approved_by") or request.get("actor"))
        reason = _safe_text(request.get("reason"), 2000)
        if not reason:
            raise ValueError("A custody approval reason is required.")
        current = self.custody_transfer(transfer_id)
        if current.get("status") != "verified":
            raise ValueError("Custody transfer must be verified before approval.")
        if self.require_separation and approver in {current.get("created_by"), current.get("verified_by")}:
            raise ValueError("Custody approval requires separation of duties.")
        updated = deepcopy(current)
        updated.update({
            "status": "approved",
            "approved_by": approver,
            "approved_at": _iso(self.now_fn()),
            "approval_reason": reason,
            "public_visible": bool(request.get("public_visible", False)),
            "updated_at": _iso(self.now_fn()),
        })
        updated["transfer_sha256"] = _digest({k: v for k, v in updated.items() if k != "transfer_sha256"})
        _append(self.custody_path, updated)
        self._event(transfer_id, "custody_transfer_approved", approver, {"manual_transfer_required": True})
        return {"ok": True, "version": APP_VERSION, "transfer": updated}

    def record_custody_receipt(self, transfer_id: str, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_audit_payload(request)
        actor = _actor(request.get("actor"))
        current = self.custody_transfer(transfer_id)
        if current.get("status") != "approved":
            raise ValueError("Only approved custody transfers may record manual receipts.")
        reference = _safe_text(request.get("custody_reference"), 500)
        if not reference:
            raise ValueError("A non-sensitive custody reference is required.")
        updated = deepcopy(current)
        updated.update({
            "status": "manual_receipt_recorded",
            "custody_reference": reference,
            "receipt_recorded_by": actor,
            "receipt_recorded_at": _iso(self.now_fn()),
            "updated_at": _iso(self.now_fn()),
            "remote_deposit_performed": False,
            "destination_write_performed": False,
        })
        updated["transfer_sha256"] = _digest({k: v for k, v in updated.items() if k != "transfer_sha256"})
        _append(self.custody_path, updated)
        self._event(transfer_id, "manual_custody_receipt_recorded", actor, {"custody_reference": reference})
        return {"ok": True, "version": APP_VERSION, "transfer": updated}

    def report_payload(self, audit_id: str, format: str = "json", *, public: bool = False) -> tuple[str, str]:
        audit = self.audit(audit_id, public=public)
        if audit.get("status") != "approved":
            raise ValueError("Only approved preservation audits may be packaged.")
        package = {
            "schema": PACKAGE_SCHEMA_VERSION,
            "release_version": APP_VERSION,
            "audit": deepcopy(audit),
            "automatic_scheduler_claimed": False,
            "remote_deposit_performed": False,
            "destination_write_performed": False,
        }
        package["package_sha256"] = _digest({k: v for k, v in package.items() if k != "package_sha256"})
        if format == "json":
            return "application/json", json.dumps(package, indent=2, sort_keys=True, ensure_ascii=False)
        if format != "markdown":
            raise ValueError("Unsupported audit report format.")
        summary = audit.get("summary") if isinstance(audit.get("summary"), Mapping) else {}
        lines = [
            f"# Preservation audit {audit.get('audit_id')}", "",
            f"- Audit type: `{audit.get('audit_type')}`",
            f"- Records examined: `{summary.get('records_examined', 0)}`",
            f"- Findings: `{summary.get('finding_count', 0)}`",
            f"- Critical findings: `{summary.get('critical_count', 0)}`",
            f"- Audit SHA-256: `{audit.get('audit_sha256')}`", "",
            "This report records verification results only. It performs no archive mutation, deletion, remote deposit, or destination write.",
        ]
        return "text/markdown", "\n".join(lines) + "\n"

    def custody_package_payload(self, transfer_id: str, format: str = "json") -> tuple[str, str]:
        transfer = self.custody_transfer(transfer_id)
        if transfer.get("status") not in {"approved", "manual_receipt_recorded"}:
            raise ValueError("Only approved custody transfers may be packaged.")
        package = {
            "schema": PACKAGE_SCHEMA_VERSION,
            "release_version": APP_VERSION,
            "transfer": deepcopy(transfer),
            "manual_transfer_required": True,
            "remote_deposit_performed": False,
            "destination_write_performed": False,
        }
        package["package_sha256"] = _digest({k: v for k, v in package.items() if k != "package_sha256"})
        if format == "json":
            return "application/json", json.dumps(package, indent=2, sort_keys=True, ensure_ascii=False)
        if format != "markdown":
            raise ValueError("Unsupported custody package format.")
        lines = [
            f"# Institutional custody transfer {transfer.get('transfer_id')}", "",
            f"- Adapter: `{transfer.get('adapter')}`",
            f"- Institution reference: `{transfer.get('institution_reference')}`",
            f"- Record count: `{transfer.get('record_count')}`",
            f"- Package SHA-256: `{transfer.get('package_sha256')}`", "",
            "Manual transfer is required. This package performs no remote deposit or destination write.",
        ]
        return "text/markdown", "\n".join(lines) + "\n"

    def history(self, entity_id: str, limit: int = 200) -> list[dict[str, Any]]:
        target = _safe_text(entity_id, 240)
        rows = [row for row in _read_jsonl(self.events_path, self.max_records) if row.get("entity_id") == target]
        rows.sort(key=lambda row: str(row.get("occurred_at") or ""), reverse=True)
        return rows[:max(1, min(int(limit), 1000))]

    def status(self) -> dict[str, Any]:
        audits = self.audits(limit=2000)
        public_audits = self.audits(public=True, limit=2000)
        transfers = self.custody_transfers(limit=2000)
        due = [row for row in audits if row.get("next_due_at") and str(row.get("next_due_at")) <= _iso(self.now_fn())]
        findings = [finding for row in audits for finding in row.get("findings", []) if isinstance(finding, Mapping)]
        return {
            "ok": True,
            "version": APP_VERSION,
            "audit_count": len(audits),
            "public_audit_count": len(public_audits),
            "custody_transfer_count": len(transfers),
            "due_audit_count": len(due),
            "critical_finding_count": sum(1 for item in findings if item.get("severity") == "critical"),
            "warning_finding_count": sum(1 for item in findings if item.get("severity") == "warning"),
            "append_only_audit_ledger": True,
            "automatic_scheduler_claimed": False,
            "archive_record_mutated": False,
            "archive_record_deleted": False,
            "remote_deposit_performed": False,
            "destination_write_performed": False,
        }
