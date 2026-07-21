"""Public record archive, provenance ledger, and long-term preservation.

Site Intelligence v3.16.0 creates immutable preservation records from already
approved public Live Intelligence artifacts. Archive records are append-only,
checksum-bound, chain-linked, and packaged for manual institutional custody.
This module performs no deletion, destination write, remote deposit, or source
mutation.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
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

POLICY_SCHEMA_VERSION = "sc-site-intelligence-public-archive-policy/1.0"
RECORD_SCHEMA_VERSION = "sc-site-intelligence-public-archive-record/1.0"
EVENT_SCHEMA_VERSION = "sc-site-intelligence-public-archive-event/1.0"
HANDOFF_SCHEMA_VERSION = "sc-site-intelligence-public-archive-handoff/1.0"
PACKAGE_SCHEMA_VERSION = "sc-site-intelligence-preservation-package/1.0"

SOURCE_TYPES = ("publication_release", "public_change_notice", "public_briefing")
RETENTION_CLASSES = ("permanent", "ten_year", "seven_year")
HANDOFF_ADAPTERS = ("knowledge_library", "institutional_archive", "publications", "download")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def public_archive_policy() -> dict[str, Any]:
    return {
        "ok": True,
        "version": APP_VERSION,
        "schema": POLICY_SCHEMA_VERSION,
        "principle": "Preserve approved public intelligence records as append-only, checksum-bound archival packages with inspectable provenance, retention, and chain history.",
        "source_types": list(SOURCE_TYPES),
        "retention_classes": list(RETENTION_CLASSES),
        "handoff_adapters": list(HANDOFF_ADAPTERS),
        "boundaries": {
            "approved_public_source_required": True,
            "separate_archive_approval_required": True,
            "append_only_ledger": True,
            "source_record_mutated": False,
            "archive_record_deleted": False,
            "destination_write_performed": False,
            "remote_deposit_performed": False,
            "credentials_stored": False,
            "recipient_identities_stored": False,
            "manual_custody_receipts_retained": True,
        },
        "routes": {
            "policy": "/public/live-intelligence/archive/policy",
            "status": "/public/live-intelligence/archive/status",
            "records": "/public/live-intelligence/archive",
            "record": "/public/live-intelligence/archive/{archive_id}",
            "lineage": "/public/live-intelligence/archive/sources/{source_id}",
            "admin": "/admin/live-intelligence/archive",
        },
    }


def _reject_archive_identity_payload(value: Any, path: str = "request") -> None:
    _reject_identity_payload(value, path)
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized = str(key).strip().lower().replace("-", "_")
            if any(part in normalized for part in ("email", "password", "secret", "token", "credential", "recipient")):
                raise ValueError(f"{path}.{key} is not accepted; identities and credentials are outside public archive records.")
            _reject_archive_identity_payload(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_archive_identity_payload(child, f"{path}[{index}]")


def _public_projection(value: Any) -> Any:
    """Return a deterministic public-safe projection without operational identity fields."""
    blocked = {
        "actor", "created_by", "prepared_by", "approved_by", "reviewed_by",
        "assigned_to", "email", "recipient", "recipients", "token", "api_key",
        "authorization", "cookie", "password", "secret", "webhook", "credentials",
    }
    if isinstance(value, Mapping):
        return {
            str(key): _public_projection(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
            if str(key).lower() not in blocked and not str(key).lower().endswith("_token")
        }
    if isinstance(value, list):
        return [_public_projection(item) for item in value]
    return value


class LiveIntelligencePublicArchive:
    def __init__(
        self,
        settings: Settings,
        *,
        publication_center: Any,
        change_history_center: Any,
        briefing_center: Any,
        now_fn: Callable[[], datetime] = _utc_now,
    ) -> None:
        self.settings = settings
        self.publication_center = publication_center
        self.change_history_center = change_history_center
        self.briefing_center = briefing_center
        self.now_fn = now_fn
        self.records_path = _resolve(settings.live_intelligence_public_archive_records_path)
        self.events_path = _resolve(settings.live_intelligence_public_archive_events_path)
        self.handoffs_path = _resolve(settings.live_intelligence_public_archive_handoffs_path)
        self.max_records = int(settings.live_intelligence_public_archive_max_records)
        self.require_separation = bool(settings.live_intelligence_public_archive_require_separation_of_duties)

    def _event(self, entity_id: str, event_type: str, actor: str, detail: Mapping[str, Any]) -> dict[str, Any]:
        event = {
            "schema": EVENT_SCHEMA_VERSION,
            "release_version": APP_VERSION,
            "event_id": f"archive-event:{uuid4().hex[:20]}",
            "entity_id": entity_id,
            "event_type": event_type,
            "actor": actor,
            "occurred_at": _iso(self.now_fn()),
            "detail": deepcopy(dict(detail)),
            "source_record_mutated": False,
            "archive_record_deleted": False,
            "destination_write_performed": False,
        }
        event["event_sha256"] = _digest({k: v for k, v in event.items() if k != "event_sha256"})
        _append(self.events_path, event)
        return event

    def records(self, *, public: bool = False, limit: int = 1000) -> list[dict[str, Any]]:
        rows = [row for row in _latest(self.records_path, "archive_id", self.max_records) if not row.get("deleted")]
        if public:
            rows = [row for row in rows if row.get("status") == "approved" and row.get("public_visible") is True]
        rows.sort(key=lambda row: str(row.get("approved_at") or row.get("updated_at") or row.get("created_at") or ""), reverse=True)
        return rows[:max(1, min(int(limit), 2000))]

    def record(self, archive_id: str, *, public: bool = False) -> dict[str, Any]:
        target = _safe_id(archive_id, "public-archive")
        for row in self.records(public=public, limit=2000):
            if row.get("archive_id") == target:
                return row
        raise KeyError(target)

    def _resolve_source(self, source_type: str, source_id: str) -> dict[str, Any]:
        if source_type == "publication_release":
            source = self.publication_center.release(_safe_id(source_id, "publication-release"))
            if source.get("status") not in {"approved", "handoff_ready"} or source.get("visibility") != "public":
                raise ValueError("Publication release must be approved and public before archival.")
        elif source_type == "public_change_notice":
            source = self.change_history_center.notice(_safe_id(source_id, "change-notice"))
            if source.get("status") != "approved" or source.get("public_visible") is not True:
                raise ValueError("Change notice must be approved and public before archival.")
        elif source_type == "public_briefing":
            source = self.briefing_center._briefing(_safe_id(source_id, "briefing"), public=True)
        else:
            raise ValueError("Unsupported archive source type.")
        return _public_projection(deepcopy(source))

    def _latest_chain_record(self) -> dict[str, Any] | None:
        rows = self.records(public=False, limit=2000)
        if not rows:
            return None
        rows.sort(key=lambda row: str(row.get("created_at") or ""))
        return rows[-1]

    def create_record(self, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_archive_identity_payload(request)
        actor = _actor(request.get("actor"))
        source_type = _safe_text(request.get("source_type"), 80).lower()
        if source_type not in SOURCE_TYPES:
            raise ValueError("Unsupported archive source type.")
        source_id = _safe_id(request.get("source_id"), source_type)
        if any(row.get("source_type") == source_type and row.get("source_id") == source_id for row in self.records(limit=2000)):
            raise ValueError("This source already has an archive record.")
        retention_class = _safe_text(request.get("retention_class") or "permanent", 40).lower()
        if retention_class not in RETENTION_CLASSES:
            raise ValueError("Unsupported retention class.")
        title = _safe_text(request.get("title") or f"Archived public record: {source_id}", 500)
        preservation_note = _safe_text(request.get("preservation_note") or "Preserved as a source-linked public-interest record.", 4000)
        source = self._resolve_source(source_type, source_id)
        source_sha256 = _digest(source)
        previous = self._latest_chain_record()
        now = _iso(self.now_fn())
        archive_id = _safe_id(request.get("archive_id") or f"public-archive:{uuid4().hex[:20]}", "public-archive")
        record = {
            "schema": RECORD_SCHEMA_VERSION,
            "release_version": APP_VERSION,
            "archive_id": archive_id,
            "source_type": source_type,
            "source_id": source_id,
            "title": title,
            "preservation_note": preservation_note,
            "retention_class": retention_class,
            "review_due_at": _safe_text(request.get("review_due_at"), 80),
            "source_sha256": source_sha256,
            "source_snapshot": source,
            "previous_archive_id": previous.get("archive_id") if previous else "",
            "previous_record_sha256": previous.get("record_sha256") if previous else "",
            "status": "draft",
            "public_visible": False,
            "created_by": actor,
            "created_at": now,
            "updated_at": now,
            "verified_by": "",
            "verified_at": "",
            "verification_reason": "",
            "approved_by": "",
            "approved_at": "",
            "approval_reason": "",
            "source_record_mutated": False,
            "archive_record_deleted": False,
            "destination_write_performed": False,
            "remote_deposit_performed": False,
        }
        record["record_sha256"] = _digest({k: v for k, v in record.items() if k != "record_sha256"})
        _append(self.records_path, record)
        self._event(archive_id, "archive_record_created", actor, {"source_type": source_type, "source_id": source_id, "record_sha256": record["record_sha256"]})
        return {"ok": True, "version": APP_VERSION, "record": record}

    def verify_record(self, archive_id: str, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_archive_identity_payload(request)
        actor = _actor(request.get("actor"))
        reason = _safe_text(request.get("reason"), 2000)
        if not reason:
            raise ValueError("A verification reason is required.")
        current = self.record(archive_id)
        if current.get("status") not in {"draft", "verified"}:
            raise ValueError("Only draft or verified archive records may be verified.")
        source = self._resolve_source(str(current.get("source_type")), str(current.get("source_id")))
        source_sha256 = _digest(source)
        if source_sha256 != current.get("source_sha256"):
            raise ValueError("The source record changed after archive preparation.")
        expected = _digest({k: v for k, v in current.items() if k != "record_sha256"})
        if expected != current.get("record_sha256"):
            raise ValueError("Archive record checksum verification failed.")
        updated = deepcopy(current)
        updated.update({
            "status": "verified",
            "verified_by": actor,
            "verified_at": _iso(self.now_fn()),
            "verification_reason": reason,
            "updated_at": _iso(self.now_fn()),
        })
        updated["record_sha256"] = _digest({k: v for k, v in updated.items() if k != "record_sha256"})
        _append(self.records_path, updated)
        self._event(str(updated["archive_id"]), "archive_record_verified", actor, {"record_sha256": updated["record_sha256"]})
        return {"ok": True, "version": APP_VERSION, "record": updated}

    def approve_record(self, archive_id: str, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_archive_identity_payload(request)
        approver = _actor(request.get("approved_by") or request.get("actor"))
        reason = _safe_text(request.get("reason"), 2000)
        if not reason:
            raise ValueError("An approval reason is required.")
        current = self.record(archive_id)
        if current.get("status") != "verified":
            raise ValueError("Archive record must be verified before approval.")
        if self.require_separation and approver in {current.get("created_by"), current.get("verified_by")}:
            raise ValueError("Archive approval requires separation of duties.")
        updated = deepcopy(current)
        updated.update({
            "status": "approved",
            "public_visible": bool(request.get("public_visible", True)),
            "approved_by": approver,
            "approved_at": _iso(self.now_fn()),
            "approval_reason": reason,
            "updated_at": _iso(self.now_fn()),
        })
        manifest = self._preservation_manifest(updated)
        updated["preservation_manifest"] = manifest
        updated["preservation_manifest_sha256"] = _digest(manifest)
        updated["record_sha256"] = _digest({k: v for k, v in updated.items() if k != "record_sha256"})
        _append(self.records_path, updated)
        self._event(str(updated["archive_id"]), "archive_record_approved", approver, {"record_sha256": updated["record_sha256"], "manifest_sha256": updated["preservation_manifest_sha256"]})
        return {"ok": True, "version": APP_VERSION, "record": updated}

    def _preservation_manifest(self, record: Mapping[str, Any]) -> dict[str, Any]:
        files = [
            {"path": "archive-record.json", "sha256": _digest(_public_projection(record))},
            {"path": "source-snapshot.json", "sha256": str(record.get("source_sha256") or "")},
            {"path": "provenance-ledger.json", "sha256": _digest({"archive_id": record.get("archive_id"), "previous_archive_id": record.get("previous_archive_id"), "previous_record_sha256": record.get("previous_record_sha256")})},
            {"path": "retention-policy.json", "sha256": _digest({"retention_class": record.get("retention_class"), "review_due_at": record.get("review_due_at")})},
        ]
        return {
            "schema": PACKAGE_SCHEMA_VERSION,
            "release_version": APP_VERSION,
            "archive_id": record.get("archive_id"),
            "source_type": record.get("source_type"),
            "source_id": record.get("source_id"),
            "retention_class": record.get("retention_class"),
            "chain": {
                "previous_archive_id": record.get("previous_archive_id") or "",
                "previous_record_sha256": record.get("previous_record_sha256") or "",
            },
            "files": files,
            "source_record_mutated": False,
            "archive_record_deleted": False,
            "destination_write_performed": False,
        }

    def verify_public_record(self, archive_id: str) -> dict[str, Any]:
        record = self.record(archive_id, public=True)
        current_source = self._resolve_source(str(record.get("source_type")), str(record.get("source_id")))
        source_matches = _digest(current_source) == record.get("source_sha256")
        manifest = record.get("preservation_manifest") if isinstance(record.get("preservation_manifest"), Mapping) else {}
        manifest_matches = _digest(manifest) == record.get("preservation_manifest_sha256")
        return {
            "ok": source_matches and manifest_matches,
            "version": APP_VERSION,
            "archive_id": archive_id,
            "source_checksum_matches": source_matches,
            "manifest_checksum_matches": manifest_matches,
            "chain_link_present": bool(record.get("previous_record_sha256")) or not bool(record.get("previous_archive_id")),
            "destination_write_performed": False,
        }

    def public_lineage(self, source_id: str) -> dict[str, Any]:
        target = _safe_text(source_id, 240)
        rows = [row for row in self.records(public=True, limit=2000) if row.get("source_id") == target]
        return {
            "ok": True,
            "version": APP_VERSION,
            "source_id": target,
            "archive_records": rows,
            "count": len(rows),
            "append_only": True,
        }

    def package_payload(self, archive_id: str, format: str = "json", *, public: bool = False) -> tuple[str, str]:
        record = self.record(archive_id, public=public)
        if record.get("status") != "approved":
            raise ValueError("Only approved archive records may be packaged.")
        package = {
            "schema": PACKAGE_SCHEMA_VERSION,
            "release_version": APP_VERSION,
            "record": _public_projection(record),
            "verification": self.verify_public_record(archive_id) if record.get("public_visible") else {"ok": True, "public_visible": False},
            "automatic_deposit": False,
            "destination_write_performed": False,
        }
        package["package_sha256"] = _digest({k: v for k, v in package.items() if k != "package_sha256"})
        if format == "json":
            return "application/json", json.dumps(package, indent=2, sort_keys=True, ensure_ascii=False)
        if format != "markdown":
            raise ValueError("Unsupported archive package format.")
        lines = [
            f"# {record.get('title')}", "",
            f"- Archive ID: `{record.get('archive_id')}`",
            f"- Source: `{record.get('source_type')} / {record.get('source_id')}`",
            f"- Retention: `{record.get('retention_class')}`",
            f"- Source SHA-256: `{record.get('source_sha256')}`",
            f"- Record SHA-256: `{record.get('record_sha256')}`",
            f"- Previous record SHA-256: `{record.get('previous_record_sha256') or 'genesis'}`",
            "", "## Preservation note", "", str(record.get("preservation_note") or ""), "",
            "Original records remain retained. This package performs no destination write, deletion, or remote deposit.",
        ]
        return "text/markdown", "\n".join(lines) + "\n"

    def create_handoff(self, archive_id: str, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_archive_identity_payload(request)
        actor = _actor(request.get("actor"))
        adapter = _safe_text(request.get("adapter"), 80).lower()
        if adapter not in HANDOFF_ADAPTERS:
            raise ValueError("Unsupported archive handoff adapter.")
        record = self.record(archive_id)
        if record.get("status") != "approved":
            raise ValueError("Only approved archive records may create custody handoffs.")
        receipt = {
            "schema": HANDOFF_SCHEMA_VERSION,
            "release_version": APP_VERSION,
            "handoff_id": f"archive-handoff:{uuid4().hex[:20]}",
            "archive_id": archive_id,
            "adapter": adapter,
            "actor": actor,
            "created_at": _iso(self.now_fn()),
            "record_sha256": record.get("record_sha256"),
            "manifest_sha256": record.get("preservation_manifest_sha256"),
            "status": "manual_custody_required",
            "destination_write_performed": False,
            "remote_deposit_performed": False,
        }
        receipt["handoff_sha256"] = _digest({k: v for k, v in receipt.items() if k != "handoff_sha256"})
        _append(self.handoffs_path, receipt)
        self._event(archive_id, "archive_handoff_created", actor, {"handoff_id": receipt["handoff_id"], "adapter": adapter})
        return {"ok": True, "version": APP_VERSION, "handoff": receipt}

    def history(self, entity_id: str, limit: int = 200) -> list[dict[str, Any]]:
        target = _safe_text(entity_id, 240)
        rows = [row for row in _read_jsonl(self.events_path, self.max_records) if row.get("entity_id") == target]
        rows.sort(key=lambda row: str(row.get("occurred_at") or ""), reverse=True)
        return rows[:max(1, min(int(limit), 1000))]

    def status(self) -> dict[str, Any]:
        rows = self.records(limit=2000)
        public = [row for row in rows if row.get("status") == "approved" and row.get("public_visible") is True]
        counts = {kind: sum(1 for row in public if row.get("source_type") == kind) for kind in SOURCE_TYPES}
        return {
            "ok": True,
            "version": APP_VERSION,
            "archive_record_count": len(rows),
            "public_archive_record_count": len(public),
            "publication_release_count": counts["publication_release"],
            "public_change_notice_count": counts["public_change_notice"],
            "public_briefing_count": counts["public_briefing"],
            "append_only_ledger": True,
            "source_record_mutated": False,
            "archive_record_deleted": False,
            "destination_write_performed": False,
            "remote_deposit_performed": False,
        }
