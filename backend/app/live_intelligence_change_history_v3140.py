"""Corrections, retractions, and public change history for Live Intelligence.

Site Intelligence v3.21.0 converts approved post-publication correction packages
into immutable, source-linked public notices and manual delivery packages. The
original release remains retained and addressable. This module never edits,
deletes, retracts, replaces, or republishes destination content by itself.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence
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

POLICY_SCHEMA_VERSION = "sc-site-intelligence-change-history-policy/1.0"
NOTICE_SCHEMA_VERSION = "sc-site-intelligence-public-change-notice/1.0"
EVENT_SCHEMA_VERSION = "sc-site-intelligence-change-history-event/1.0"
HANDOFF_SCHEMA_VERSION = "sc-site-intelligence-change-history-handoff/1.0"
PACKAGE_SCHEMA_VERSION = "sc-site-intelligence-change-history-package/1.0"

ALLOWED_NOTICE_TYPES = ("correction", "clarification", "replacement", "retraction", "rollback")
ALLOWED_SCOPES = ("full_release", "section", "claim", "source_link", "presentation")
HANDOFF_ADAPTERS = ("publications", "knowledge_library", "wordpress_package", "download")
CORRECTION_TYPE_TO_NOTICE = {
    "correction_notice": "correction",
    "replacement": "replacement",
    "withdrawal": "retraction",
    "rollback_notice": "rollback",
}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def change_history_policy() -> dict[str, Any]:
    return {
        "ok": True,
        "version": APP_VERSION,
        "schema": POLICY_SCHEMA_VERSION,
        "principle": "Publish an append-only, source-linked record of approved corrections, clarifications, replacements, retractions, and rollback notices while preserving the original release and evidence history.",
        "notice_types": list(ALLOWED_NOTICE_TYPES),
        "scopes": list(ALLOWED_SCOPES),
        "boundaries": {
            "approved_public_correction_required": True,
            "separate_notice_approval_required": True,
            "original_release_retained": True,
            "append_only_public_history": True,
            "evidence_rewritten": False,
            "destination_content_modified": False,
            "destination_content_deleted": False,
            "automatic_republication": False,
            "credentials_stored": False,
            "recipient_identities_stored": False,
            "manual_handoff_receipts_retained": True,
        },
        "routes": {
            "policy": "/public/live-intelligence/change-history/policy",
            "history": "/public/live-intelligence/change-history",
            "status": "/public/live-intelligence/change-history/status",
            "release_lineage": "/public/live-intelligence/change-history/releases/{release_id}",
            "admin": "/admin/live-intelligence/change-history",
        },
    }


class LiveIntelligenceChangeHistoryCenter:
    def __init__(
        self,
        settings: Settings,
        *,
        release_operations_center: Any,
        publication_center: Any,
        now_fn: Callable[[], datetime] = _utc_now,
    ) -> None:
        self.settings = settings
        self.release_operations_center = release_operations_center
        self.publication_center = publication_center
        self.now_fn = now_fn
        self.notices_path = _resolve(settings.live_intelligence_change_history_notices_path)
        self.events_path = _resolve(settings.live_intelligence_change_history_events_path)
        self.handoffs_path = _resolve(settings.live_intelligence_change_history_handoffs_path)
        self.max_records = int(settings.live_intelligence_change_history_max_records)
        self.require_separation = bool(settings.live_intelligence_change_history_require_separation_of_duties)

    def _event(self, entity_id: str, event_type: str, actor: str, detail: Mapping[str, Any]) -> dict[str, Any]:
        event = {
            "schema": EVENT_SCHEMA_VERSION,
            "release_version": APP_VERSION,
            "event_id": f"change-history-event:{uuid4().hex[:20]}",
            "entity_id": entity_id,
            "event_type": event_type,
            "actor": actor,
            "occurred_at": _iso(self.now_fn()),
            "detail": deepcopy(dict(detail)),
            "destination_write_performed": False,
            "deletion_performed": False,
        }
        event["event_sha256"] = _digest({k: v for k, v in event.items() if k != "event_sha256"})
        _append(self.events_path, event)
        return event

    def notices(self, limit: int = 1000) -> list[dict[str, Any]]:
        rows = [row for row in _latest(self.notices_path, "notice_id", self.max_records) if not row.get("deleted")]
        rows.sort(key=lambda row: str(row.get("updated_at") or row.get("created_at") or ""), reverse=True)
        return rows[:max(1, min(int(limit), 2000))]

    def notice(self, notice_id: str) -> dict[str, Any]:
        target = _safe_id(notice_id, "change-notice")
        for row in self.notices(2000):
            if row.get("notice_id") == target:
                return row
        raise KeyError(target)

    def _existing_for_correction(self, correction_id: str) -> dict[str, Any] | None:
        for row in self.notices(2000):
            if row.get("correction_id") == correction_id:
                return row
        return None

    def prepare_notice(self, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_identity_payload(request)
        actor = _actor(request.get("actor"))
        correction = self.release_operations_center.correction(_safe_id(request.get("correction_id"), "correction"))
        if correction.get("status") != "approved" or correction.get("public_visible") is not True:
            raise ValueError("Only an approved public correction may create a public change notice.")
        existing = self._existing_for_correction(str(correction.get("correction_id")))
        if existing:
            raise ValueError("This correction already has a change-history notice.")

        default_type = CORRECTION_TYPE_TO_NOTICE.get(str(correction.get("correction_type")), "correction")
        notice_type = _safe_text(request.get("notice_type") or default_type, 40).lower()
        if notice_type not in ALLOWED_NOTICE_TYPES:
            raise ValueError("Unsupported public change notice type.")
        if default_type in {"replacement", "retraction", "rollback"} and notice_type != default_type:
            raise ValueError("The public notice type must preserve the approved correction type.")

        scope = _safe_text(request.get("scope") or ("full_release" if notice_type in {"replacement", "retraction", "rollback"} else "section"), 40).lower()
        if scope not in ALLOWED_SCOPES:
            raise ValueError("Unsupported change scope.")
        if notice_type in {"replacement", "retraction", "rollback"} and scope != "full_release":
            raise ValueError("Replacement, retraction, and rollback notices must apply to the full release.")

        release = self.publication_center.release(_safe_id(correction.get("release_id"), "publication-release"))
        replacement_release: dict[str, Any] | None = None
        replacement_release_id = _safe_text(correction.get("replacement_release_id"), 180)
        if replacement_release_id:
            replacement_release = self.publication_center.release(_safe_id(replacement_release_id, "publication-release"))
            if replacement_release.get("status") not in {"approved", "handoff_ready"}:
                raise ValueError("Replacement release must remain approved.")
        if notice_type == "replacement" and not replacement_release:
            raise ValueError("Replacement notices require an approved replacement release.")

        title = _safe_text(request.get("title") or f"{notice_type.replace('_', ' ').title()}: {release.get('title') or release.get('target_slug') or release.get('release_id')}", 500)
        public_summary = _safe_text(request.get("public_summary") or correction.get("summary"), 4000)
        rationale = _safe_text(request.get("rationale") or correction.get("rationale"), 4000)
        if not title or not public_summary or not rationale:
            raise ValueError("title, public_summary, and rationale are required.")

        now = _iso(self.now_fn())
        record = {
            "schema": NOTICE_SCHEMA_VERSION,
            "release_version": APP_VERSION,
            "notice_id": _safe_id(request.get("notice_id") or f"change-notice:{uuid4().hex[:20]}", "change-notice"),
            "correction_id": correction.get("correction_id"),
            "issue_id": correction.get("issue_id"),
            "notice_type": notice_type,
            "scope": scope,
            "title": title,
            "public_summary": public_summary,
            "rationale": rationale,
            "affected_release_id": release.get("release_id"),
            "affected_release_sha256": release.get("release_sha256"),
            "affected_payload_sha256": release.get("payload_sha256"),
            "affected_target_slug": release.get("target_slug") or "",
            "replacement_release_id": replacement_release.get("release_id") if replacement_release else "",
            "replacement_release_sha256": replacement_release.get("release_sha256") if replacement_release else "",
            "replacement_target_slug": replacement_release.get("target_slug") if replacement_release else "",
            "status": "draft",
            "prepared_by": actor,
            "prepared_at": now,
            "approved_by": "",
            "approved_at": "",
            "approval_reason": "",
            "effective_at": "",
            "public_visible": False,
            "original_release_retained": True,
            "append_only_history": True,
            "evidence_rewritten": False,
            "destination_write_performed": False,
            "deletion_performed": False,
            "automatic_republication_performed": False,
            "created_at": now,
            "updated_at": now,
        }
        record["notice_sha256"] = _digest({k: v for k, v in record.items() if k != "notice_sha256"})
        _append(self.notices_path, record)
        self._event(record["notice_id"], "notice_prepared", actor, {
            "correction_id": record["correction_id"],
            "notice_type": notice_type,
            "affected_release_id": record["affected_release_id"],
            "replacement_release_id": record["replacement_release_id"],
        })
        return {"ok": True, "version": APP_VERSION, "notice": record}

    def approve_notice(self, notice_id: str, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_identity_payload(request)
        actor = _actor(request.get("approved_by"), "approved_by")
        reason = _safe_text(request.get("reason"), 3000)
        if not reason:
            raise ValueError("reason is required.")
        current = self.notice(notice_id)
        if current.get("status") != "draft":
            raise ValueError("Only a draft public change notice may be approved.")
        if self.require_separation and actor == current.get("prepared_by"):
            raise ValueError("Change-notice approval requires separation of duties.")
        if current.get("notice_type") == "retraction" and request.get("original_record_retained_acknowledged") is not True:
            raise ValueError("Retraction approval must acknowledge that the original record remains retained.")

        now = _iso(self.now_fn())
        updated = dict(current)
        updated.update({
            "status": "approved",
            "approved_by": actor,
            "approved_at": now,
            "approval_reason": reason,
            "effective_at": _safe_text(request.get("effective_at"), 80) or now,
            "public_visible": True,
            "updated_at": now,
            "original_release_retained": True,
            "append_only_history": True,
            "evidence_rewritten": False,
            "destination_write_performed": False,
            "deletion_performed": False,
            "automatic_republication_performed": False,
        })
        updated["notice_sha256"] = _digest({k: v for k, v in updated.items() if k != "notice_sha256"})
        _append(self.notices_path, updated)
        self._event(updated["notice_id"], "notice_approved", actor, {
            "reason": reason,
            "effective_at": updated["effective_at"],
            "notice_sha256": updated["notice_sha256"],
        })
        return {"ok": True, "version": APP_VERSION, "notice": updated}

    @staticmethod
    def _public_record(row: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "notice_id": row.get("notice_id"),
            "notice_type": row.get("notice_type"),
            "scope": row.get("scope"),
            "title": row.get("title"),
            "public_summary": row.get("public_summary"),
            "rationale": row.get("rationale"),
            "affected_release_id": row.get("affected_release_id"),
            "affected_release_sha256": row.get("affected_release_sha256"),
            "affected_target_slug": row.get("affected_target_slug"),
            "replacement_release_id": row.get("replacement_release_id"),
            "replacement_release_sha256": row.get("replacement_release_sha256"),
            "replacement_target_slug": row.get("replacement_target_slug"),
            "effective_at": row.get("effective_at"),
            "approved_at": row.get("approved_at"),
            "notice_sha256": row.get("notice_sha256"),
            "original_release_retained": True,
            "append_only_history": True,
            "evidence_rewritten": False,
            "destination_write_performed": False,
            "deletion_performed": False,
        }

    def public_history(
        self,
        limit: int = 100,
        *,
        release_id: str = "",
        notice_type: str = "",
    ) -> list[dict[str, Any]]:
        target_release = _safe_id(release_id, "publication-release") if release_id else ""
        normalized_type = _safe_text(notice_type, 40).lower()
        if normalized_type and normalized_type not in ALLOWED_NOTICE_TYPES:
            raise ValueError("Unsupported public change notice type.")
        rows: list[dict[str, Any]] = []
        for row in self.notices(2000):
            if row.get("status") != "approved" or row.get("public_visible") is not True:
                continue
            if normalized_type and row.get("notice_type") != normalized_type:
                continue
            if target_release and target_release not in {row.get("affected_release_id"), row.get("replacement_release_id")}:
                continue
            rows.append(self._public_record(row))
        rows.sort(key=lambda row: str(row.get("effective_at") or row.get("approved_at") or ""), reverse=True)
        return rows[:max(1, min(int(limit), 500))]

    def release_lineage(self, release_id: str) -> dict[str, Any]:
        release = self.publication_center.release(_safe_id(release_id, "publication-release"))
        history = self.public_history(500, release_id=str(release.get("release_id")))
        outgoing = [row for row in history if row.get("affected_release_id") == release.get("release_id")]
        incoming = [row for row in history if row.get("replacement_release_id") == release.get("release_id")]
        current_state = "active"
        for row in outgoing:
            if row.get("notice_type") == "retraction":
                current_state = "retracted"
                break
            if row.get("notice_type") in {"replacement", "rollback"}:
                current_state = "superseded"
        return {
            "ok": True,
            "version": APP_VERSION,
            "release": {
                "release_id": release.get("release_id"),
                "release_sha256": release.get("release_sha256"),
                "target_slug": release.get("target_slug"),
                "status": release.get("status"),
                "change_state": current_state,
                "original_record_retained": True,
            },
            "outgoing_changes": outgoing,
            "incoming_changes": incoming,
            "append_only_history": True,
            "destination_write_performed": False,
            "deletion_performed": False,
        }

    def package_payload(self, notice_id: str, format: str = "json") -> tuple[str, str]:
        notice = self.notice(notice_id)
        if notice.get("status") != "approved" or notice.get("public_visible") is not True:
            raise ValueError("Only an approved public change notice may be packaged.")
        package = {
            "schema": PACKAGE_SCHEMA_VERSION,
            "release_version": APP_VERSION,
            "notice": self._public_record(notice),
            "lineage": self.release_lineage(str(notice.get("affected_release_id"))),
            "generated_at": _iso(self.now_fn()),
            "original_release_retained": True,
            "destination_write_performed": False,
            "deletion_performed": False,
        }
        package["package_sha256"] = _digest({k: v for k, v in package.items() if k != "package_sha256"})
        normalized = _safe_text(format or "json", 20).lower()
        if normalized == "json":
            return "application/json", json.dumps(package, indent=2, sort_keys=True, ensure_ascii=False)
        if normalized != "markdown":
            raise ValueError("format must be json or markdown.")
        record = package["notice"]
        body = [
            f"# {record.get('title')}",
            "",
            f"**Notice type:** {record.get('notice_type')}",
            f"**Effective:** {record.get('effective_at')}",
            f"**Affected release:** `{record.get('affected_release_id')}`",
            f"**Replacement release:** `{record.get('replacement_release_id') or 'None'}`",
            "",
            str(record.get("public_summary") or ""),
            "",
            "## Rationale",
            "",
            str(record.get("rationale") or ""),
            "",
            "## Record integrity",
            "",
            "- Original release retained: Yes",
            "- Evidence rewritten: No",
            "- Destination write performed by Site Intelligence: No",
            "- Destination deletion performed by Site Intelligence: No",
            f"- Notice SHA-256: `{record.get('notice_sha256')}`",
            f"- Package SHA-256: `{package.get('package_sha256')}`",
            "",
        ]
        return "text/markdown", "\n".join(body)

    def create_handoff(self, notice_id: str, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_identity_payload(request)
        actor = _actor(request.get("actor"))
        notice = self.notice(notice_id)
        if notice.get("status") != "approved" or notice.get("public_visible") is not True:
            raise ValueError("Only an approved public change notice may create a handoff receipt.")
        requested = request.get("adapters") or list(HANDOFF_ADAPTERS)
        if not isinstance(requested, Sequence) or isinstance(requested, (str, bytes)):
            raise ValueError("adapters must be a list.")
        adapters: list[str] = []
        for value in requested:
            adapter = _safe_text(value, 80).lower()
            if adapter not in HANDOFF_ADAPTERS:
                raise ValueError("Unsupported change-history handoff adapter.")
            if adapter not in adapters:
                adapters.append(adapter)
        handoff = {
            "schema": HANDOFF_SCHEMA_VERSION,
            "release_version": APP_VERSION,
            "handoff_id": f"change-history-handoff:{uuid4().hex[:20]}",
            "notice_id": notice.get("notice_id"),
            "notice_sha256": notice.get("notice_sha256"),
            "created_by": actor,
            "created_at": _iso(self.now_fn()),
            "adapters": adapters,
            "states": [
                {
                    "adapter_id": adapter,
                    "state": "download_ready" if adapter == "download" else "manual_delivery_ready",
                    "destination_write_performed": False,
                    "deletion_performed": False,
                }
                for adapter in adapters
            ],
            "credentials_included": False,
            "recipient_data_included": False,
            "destination_write_performed": False,
            "deletion_performed": False,
            "automatic_republication_performed": False,
        }
        handoff["handoff_sha256"] = _digest({k: v for k, v in handoff.items() if k != "handoff_sha256"})
        _append(self.handoffs_path, handoff)
        self._event(str(notice.get("notice_id")), "notice_handoff_created", actor, {
            "handoff_id": handoff["handoff_id"],
            "adapters": adapters,
        })
        return {"ok": True, "version": APP_VERSION, "handoff": handoff}

    def history(self, entity_id: str, limit: int = 200) -> list[dict[str, Any]]:
        target = _safe_id(entity_id, "change-history")
        rows = [row for row in _read_jsonl(self.events_path, self.max_records) if row.get("entity_id") == target]
        return rows[-max(1, min(int(limit), 1000)):]

    def status(self) -> dict[str, Any]:
        notices = self.notices(2000)
        handoffs = _latest(self.handoffs_path, "handoff_id", self.max_records)
        public = self.public_history(500)
        return {
            "ok": True,
            "version": APP_VERSION,
            "schema": POLICY_SCHEMA_VERSION,
            "notice_count": len(notices),
            "draft_notice_count": sum(1 for row in notices if row.get("status") == "draft"),
            "approved_notice_count": sum(1 for row in notices if row.get("status") == "approved"),
            "public_notice_count": len(public),
            "correction_count": sum(1 for row in public if row.get("notice_type") == "correction"),
            "clarification_count": sum(1 for row in public if row.get("notice_type") == "clarification"),
            "replacement_count": sum(1 for row in public if row.get("notice_type") == "replacement"),
            "retraction_count": sum(1 for row in public if row.get("notice_type") == "retraction"),
            "rollback_notice_count": sum(1 for row in public if row.get("notice_type") == "rollback"),
            "handoff_count": len(handoffs),
            "separation_of_duties_required": self.require_separation,
            "original_release_retained": True,
            "append_only_history": True,
            "destination_write_performed": False,
            "deletion_performed": False,
        }

    def control_center(self) -> dict[str, Any]:
        return {
            "ok": True,
            "version": APP_VERSION,
            "policy": change_history_policy(),
            "status": self.status(),
            "notices": self.notices(100),
            "handoffs": _latest(self.handoffs_path, "handoff_id", self.max_records)[-100:],
        }
