"""Saved discovery views, public research collections, and evidence pathways.

Site Intelligence v3.21.0 adds an append-only, human-governed curation layer
above the public preservation-registry discovery service. It preserves
reproducible filter states and approved record snapshots without storing
visitor identities, visitor queries, credentials, or remote-write authority.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
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

POLICY_SCHEMA_VERSION = "sc-site-intelligence-registry-collections-policy/1.0"
VIEW_SCHEMA_VERSION = "sc-site-intelligence-registry-saved-view/1.0"
COLLECTION_SCHEMA_VERSION = "sc-site-intelligence-registry-research-collection/1.0"
EVENT_SCHEMA_VERSION = "sc-site-intelligence-registry-collection-event/1.0"
PACKAGE_SCHEMA_VERSION = "sc-site-intelligence-registry-collection-package/1.0"

VIEW_STATUSES = ("draft", "reviewed", "approved")
COLLECTION_STATUSES = ("draft", "reviewed", "approved")
ALLOWED_SORTS = ("relevance", "name", "recent")
ALLOWED_RECORD_TYPES = ("institution", "attestation", "exchange", "challenge", "appeal")
FILTER_FIELDS = (
    "query", "record_type", "institution_type", "trust_profile", "jurisdiction",
    "exchange_profile", "verification_method", "governance_status", "sort",
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def registry_collections_policy() -> dict[str, Any]:
    return {
        "ok": True,
        "version": APP_VERSION,
        "schema": POLICY_SCHEMA_VERSION,
        "principle": "Preserve reproducible public discovery states and human-curated evidence pathways without storing visitor identities or silently rewriting approved collections.",
        "view_statuses": list(VIEW_STATUSES),
        "collection_statuses": list(COLLECTION_STATUSES),
        "filter_fields": list(FILTER_FIELDS),
        "boundaries": {
            "human_review_required": True,
            "separation_of_duties_required": True,
            "approved_public_records_only": True,
            "visitor_queries_stored": False,
            "visitor_profiles_created": False,
            "personal_identity_data_stored": False,
            "source_records_mutated": False,
            "approved_snapshots_overwritten": False,
            "network_verification_performed": False,
            "remote_write_performed": False,
            "certification_claimed": False,
        },
        "routes": {
            "policy": "/public/live-intelligence/registry-collections/policy",
            "status": "/public/live-intelligence/registry-collections/status",
            "views": "/public/live-intelligence/registry-collections/views",
            "collections": "/public/live-intelligence/registry-collections",
            "collection": "/public/live-intelligence/registry-collections/{collection_id}",
            "pathway": "/public/live-intelligence/registry-collections/{collection_id}/pathway",
            "admin": "/admin/live-intelligence/registry-collections",
        },
    }


def _reject_collection_payload(value: Any, path: str = "request") -> None:
    _reject_identity_payload(value, path)
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized = str(key).strip().lower().replace("-", "_")
            if any(part in normalized for part in (
                "email", "phone", "password", "secret", "token", "credential",
                "recipient", "subscriber", "visitor_id", "user_id", "ip_address",
                "cookie", "authorization", "private_key", "access_key", "contact_person",
            )):
                raise ValueError(f"{path}.{key} is not accepted; identities and credentials are outside public research collections.")
            _reject_collection_payload(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_collection_payload(child, f"{path}[{index}]")


def _record_digest(record: Mapping[str, Any], checksum_field: str) -> str:
    return _digest({key: value for key, value in record.items() if key != checksum_field})


def _public_projection(record: Mapping[str, Any]) -> dict[str, Any]:
    excluded = {
        "created_by", "reviewed_by", "approved_by", "review_note", "approval_note",
        "internal_note", "actor", "query_execution_detail",
    }
    return {key: deepcopy(value) for key, value in record.items() if key not in excluded}


def _canonical_filter_state(value: Mapping[str, Any]) -> dict[str, Any]:
    state: dict[str, Any] = {}
    for key in FILTER_FIELDS:
        if key not in value:
            continue
        raw = value.get(key)
        if key == "sort":
            clean = _safe_text(raw, 30).lower() or "relevance"
            if clean not in ALLOWED_SORTS:
                raise ValueError("Unsupported saved-view sort mode.")
        elif key == "record_type":
            clean = _safe_text(raw, 40).lower()
            if clean and clean not in ALLOWED_RECORD_TYPES:
                raise ValueError("Unsupported saved-view record type.")
        elif key == "query":
            clean = _safe_text(raw, 200)
        else:
            clean = _safe_text(raw, 160).lower()
        if clean:
            state[key] = clean
    state.setdefault("sort", "relevance")
    return {key: state[key] for key in sorted(state)}


def _record_snapshot(record: Mapping[str, Any]) -> dict[str, Any]:
    allowed = (
        "record_type", "record_id", "title", "summary", "published_at",
        "institution_id", "institution_name", "institution_type", "jurisdiction",
        "trust_profile", "exchange_id", "profile", "method", "result",
        "status", "resolution_action", "resolution_outcome", "evidence_reference",
        "repository_reference", "public_policy_reference", "package_sha256",
        "exchange_sha256", "attestation_sha256", "institution_sha256",
        "challenge_sha256", "appeal_sha256", "consensus",
    )
    snapshot = {key: deepcopy(record.get(key)) for key in allowed if record.get(key) is not None}
    snapshot["record_sha256"] = _digest(snapshot)
    return snapshot


class LiveIntelligenceRegistryCollectionsCenter:
    def __init__(
        self,
        settings: Settings,
        *,
        discovery: Any,
        now_fn: Callable[[], datetime] = _utc_now,
    ) -> None:
        self.settings = settings
        self.discovery = discovery
        self.now_fn = now_fn
        self.views_path = _resolve(settings.live_intelligence_registry_collections_views_path)
        self.collections_path = _resolve(settings.live_intelligence_registry_collections_path)
        self.events_path = _resolve(settings.live_intelligence_registry_collections_events_path)
        self.max_records = int(settings.live_intelligence_registry_collections_max_records)
        self.snapshot_limit = int(settings.live_intelligence_registry_collections_snapshot_limit)
        self.require_separation = bool(settings.live_intelligence_registry_collections_require_separation_of_duties)

    def _event(self, entity_id: str, event_type: str, actor: str, detail: Mapping[str, Any]) -> dict[str, Any]:
        event = {
            "schema": EVENT_SCHEMA_VERSION,
            "release_version": APP_VERSION,
            "event_id": f"registry-collection-event:{uuid4().hex[:20]}",
            "entity_id": entity_id,
            "event_type": event_type,
            "actor": actor,
            "occurred_at": _iso(self.now_fn()),
            "detail": deepcopy(dict(detail)),
            "append_only_collection_ledger": True,
            "visitor_queries_stored": False,
            "visitor_profiles_created": False,
            "source_records_mutated": False,
            "remote_write_performed": False,
        }
        event["event_sha256"] = _record_digest(event, "event_sha256")
        _append(self.events_path, event)
        return event

    def views(self, *, public: bool = False, limit: int = 1000) -> list[dict[str, Any]]:
        rows = _latest(self.views_path, "view_id", self.max_records)
        if public:
            rows = [
                _public_projection(row) for row in rows
                if row.get("status") == "approved" and row.get("public_visible") is True
            ]
        rows.sort(key=lambda row: str(row.get("approved_at") or row.get("created_at") or ""), reverse=True)
        return rows[:max(1, min(int(limit), 2000))]

    def view(self, view_id: str, *, public: bool = False) -> dict[str, Any]:
        target = _safe_id(view_id, "registry-view")
        for row in self.views(public=public, limit=2000):
            if row.get("view_id") == target:
                return row
        raise KeyError(target)

    def collections(self, *, public: bool = False, limit: int = 1000) -> list[dict[str, Any]]:
        rows = _latest(self.collections_path, "collection_id", self.max_records)
        if public:
            rows = [
                _public_projection(row) for row in rows
                if row.get("status") == "approved" and row.get("public_visible") is True
            ]
        rows.sort(key=lambda row: str(row.get("approved_at") or row.get("created_at") or ""), reverse=True)
        return rows[:max(1, min(int(limit), 2000))]

    def collection(self, collection_id: str, *, public: bool = False) -> dict[str, Any]:
        target = _safe_id(collection_id, "registry-collection")
        for row in self.collections(public=public, limit=2000):
            if row.get("collection_id") == target:
                return row
        raise KeyError(target)

    def _execute_state(self, state: Mapping[str, Any]) -> dict[str, Any]:
        result = self.discovery.search(
            query=str(state.get("query") or ""),
            record_type=str(state.get("record_type") or ""),
            institution_type=str(state.get("institution_type") or ""),
            trust_profile=str(state.get("trust_profile") or ""),
            jurisdiction=str(state.get("jurisdiction") or ""),
            exchange_profile=str(state.get("exchange_profile") or ""),
            verification_method=str(state.get("verification_method") or ""),
            governance_status=str(state.get("governance_status") or ""),
            sort=str(state.get("sort") or "relevance"),
            offset=0,
            limit=self.snapshot_limit,
        )
        snapshots = [_record_snapshot(row) for row in result.get("results") or []]
        return {
            "total": int(result.get("total") or 0),
            "record_ids": [row.get("record_id") for row in snapshots if row.get("record_id")],
            "records": snapshots,
            "result_sha256": _digest(snapshots),
            "truncated": int(result.get("total") or 0) > len(snapshots),
        }

    def create_view(self, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_collection_payload(request)
        actor = _actor(request.get("actor"))
        title = _safe_text(request.get("title"), 240)
        description = _safe_text(request.get("description"), 2000)
        if not title or not description:
            raise ValueError("Saved-view title and description are required.")
        state = _canonical_filter_state(request.get("filter_state") or {})
        executed = self._execute_state(state)
        view_id = _safe_id(request.get("view_id") or f"registry-view:{uuid4().hex[:20]}", "registry-view")
        if any(row.get("view_id") == view_id for row in self.views(limit=2000)):
            raise ValueError("Saved-view ID already exists.")
        now = _iso(self.now_fn())
        record = {
            "schema": VIEW_SCHEMA_VERSION,
            "release_version": APP_VERSION,
            "view_id": view_id,
            "title": title,
            "description": description,
            "filter_state": state,
            "filter_state_sha256": _digest(state),
            "snapshot_record_ids": executed["record_ids"],
            "snapshot_result_count": executed["total"],
            "snapshot_result_sha256": executed["result_sha256"],
            "snapshot_truncated": executed["truncated"],
            "status": "draft",
            "created_by": actor,
            "created_at": now,
            "updated_at": now,
            "public_visible_requested": bool(request.get("public_visible", False)),
            "public_visible": False,
            "human_curated": True,
            "visitor_queries_stored": False,
            "visitor_profiles_created": False,
            "source_records_mutated": False,
            "approved_snapshots_overwritten": False,
            "remote_write_performed": False,
            "certification_claimed": False,
        }
        record["view_sha256"] = _record_digest(record, "view_sha256")
        _append(self.views_path, record)
        self._event(view_id, "saved_view_created", actor, {"filter_state_sha256": record["filter_state_sha256"]})
        return {"ok": True, "version": APP_VERSION, "view": record}

    def review_view(self, view_id: str, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_collection_payload(request)
        actor = _actor(request.get("actor"))
        note = _safe_text(request.get("note"), 3000)
        evidence_reference = _safe_text(request.get("evidence_reference"), 600)
        if not note or not evidence_reference:
            raise ValueError("Saved-view review note and evidence reference are required.")
        current = self.view(view_id)
        if current.get("status") != "draft":
            raise ValueError("Only draft saved views may be reviewed.")
        if self.require_separation and actor == current.get("created_by"):
            raise ValueError("Saved-view review requires separation of duties.")
        executed = self._execute_state(current.get("filter_state") or {})
        updated = deepcopy(current)
        updated.update({
            "status": "reviewed",
            "reviewed_by": actor,
            "reviewed_at": _iso(self.now_fn()),
            "review_note": note,
            "review_evidence_reference": evidence_reference,
            "review_result_sha256": executed["result_sha256"],
            "review_result_count": executed["total"],
            "snapshot_drift_detected": executed["result_sha256"] != current.get("snapshot_result_sha256"),
            "updated_at": _iso(self.now_fn()),
        })
        updated["view_sha256"] = _record_digest(updated, "view_sha256")
        _append(self.views_path, updated)
        self._event(view_id, "saved_view_reviewed", actor, {"snapshot_drift_detected": updated["snapshot_drift_detected"]})
        return {"ok": True, "version": APP_VERSION, "view": updated}

    def approve_view(self, view_id: str, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_collection_payload(request)
        actor = _actor(request.get("approved_by") or request.get("actor"))
        note = _safe_text(request.get("note"), 3000)
        if not note:
            raise ValueError("Saved-view approval note is required.")
        current = self.view(view_id)
        if current.get("status") != "reviewed":
            raise ValueError("Only reviewed saved views may be approved.")
        if self.require_separation and actor in {current.get("created_by"), current.get("reviewed_by")}:
            raise ValueError("Saved-view approval requires a separate approver.")
        executed = self._execute_state(current.get("filter_state") or {})
        updated = deepcopy(current)
        updated.update({
            "status": "approved",
            "approved_by": actor,
            "approved_at": _iso(self.now_fn()),
            "approval_note": note,
            "public_visible": bool(request.get("public_visible", current.get("public_visible_requested", False))),
            "approved_record_ids": executed["record_ids"],
            "approved_result_count": executed["total"],
            "approved_result_sha256": executed["result_sha256"],
            "approved_snapshot_truncated": executed["truncated"],
            "snapshot_drift_detected": executed["result_sha256"] != current.get("snapshot_result_sha256"),
            "updated_at": _iso(self.now_fn()),
        })
        updated["view_sha256"] = _record_digest(updated, "view_sha256")
        _append(self.views_path, updated)
        self._event(view_id, "saved_view_approved", actor, {"public_visible": updated["public_visible"]})
        return {"ok": True, "version": APP_VERSION, "view": updated}

    def _available_public_records(self) -> dict[str, dict[str, Any]]:
        return {
            str(row.get("record_id")): row
            for row in self.discovery.records()
            if row.get("record_id")
        }

    def create_collection(self, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_collection_payload(request)
        actor = _actor(request.get("actor"))
        title = _safe_text(request.get("title"), 240)
        purpose = _safe_text(request.get("purpose"), 3000)
        summary = _safe_text(request.get("summary"), 3000)
        if not title or not purpose or not summary:
            raise ValueError("Collection title, purpose, and summary are required.")
        source_view_ids = [_safe_id(value, "registry-view") for value in (request.get("source_view_ids") or [])]
        explicit_record_ids = [_safe_id(value, "registry-record") for value in (request.get("record_ids") or [])]
        if not source_view_ids and not explicit_record_ids:
            raise ValueError("At least one approved saved view or public registry record is required.")
        record_ids: list[str] = []
        source_view_sha256: dict[str, str] = {}
        for view_id in source_view_ids:
            view = self.view(view_id)
            if view.get("status") != "approved":
                raise ValueError("Collections may use approved saved views only.")
            source_view_sha256[view_id] = str(view.get("view_sha256") or "")
            record_ids.extend(str(value) for value in (view.get("approved_record_ids") or []))
        record_ids.extend(explicit_record_ids)
        ordered_ids = list(dict.fromkeys(record_ids))[:self.snapshot_limit]
        public_records = self._available_public_records()
        missing = [record_id for record_id in ordered_ids if record_id not in public_records]
        if missing:
            raise ValueError("Collections may include approved public registry records only.")
        snapshots = [_record_snapshot(public_records[record_id]) for record_id in ordered_ids]
        requested_steps = request.get("pathway_steps") or []
        step_notes: dict[str, str] = {}
        for step in requested_steps:
            if not isinstance(step, Mapping):
                raise ValueError("Evidence pathway steps must be objects.")
            record_id = _safe_id(step.get("record_id"), "registry-record")
            step_notes[record_id] = _safe_text(step.get("rationale"), 1200)
        pathway = []
        for index, snapshot in enumerate(snapshots, start=1):
            pathway.append({
                "sequence": index,
                "record_id": snapshot.get("record_id"),
                "record_type": snapshot.get("record_type"),
                "title": snapshot.get("title"),
                "rationale": step_notes.get(str(snapshot.get("record_id"))) or "Included as an approved public record in this evidence pathway.",
                "record_sha256": snapshot.get("record_sha256"),
            })
        collection_id = _safe_id(request.get("collection_id") or f"registry-collection:{uuid4().hex[:20]}", "registry-collection")
        if any(row.get("collection_id") == collection_id for row in self.collections(limit=2000)):
            raise ValueError("Research collection ID already exists.")
        now = _iso(self.now_fn())
        record = {
            "schema": COLLECTION_SCHEMA_VERSION,
            "release_version": APP_VERSION,
            "collection_id": collection_id,
            "title": title,
            "purpose": purpose,
            "summary": summary,
            "source_view_ids": source_view_ids,
            "source_view_sha256": source_view_sha256,
            "record_ids": ordered_ids,
            "record_count": len(snapshots),
            "record_snapshots": snapshots,
            "record_snapshot_sha256": _digest(snapshots),
            "evidence_pathway": pathway,
            "evidence_pathway_sha256": _digest(pathway),
            "status": "draft",
            "created_by": actor,
            "created_at": now,
            "updated_at": now,
            "public_visible_requested": bool(request.get("public_visible", False)),
            "public_visible": False,
            "human_curated": True,
            "approved_public_records_only": True,
            "visitor_queries_stored": False,
            "visitor_profiles_created": False,
            "personal_identity_data_stored": False,
            "source_records_mutated": False,
            "approved_snapshots_overwritten": False,
            "remote_write_performed": False,
            "certification_claimed": False,
        }
        record["collection_sha256"] = _record_digest(record, "collection_sha256")
        _append(self.collections_path, record)
        self._event(collection_id, "research_collection_created", actor, {"record_count": len(snapshots)})
        return {"ok": True, "version": APP_VERSION, "collection": record}

    def _collection_drift(self, collection: Mapping[str, Any]) -> dict[str, Any]:
        public_records = self._available_public_records()
        current = []
        missing = []
        changed = []
        for snapshot in collection.get("record_snapshots") or []:
            record_id = str(snapshot.get("record_id") or "")
            row = public_records.get(record_id)
            if not row:
                missing.append(record_id)
                continue
            current_snapshot = _record_snapshot(row)
            current.append(current_snapshot)
            if current_snapshot.get("record_sha256") != snapshot.get("record_sha256"):
                changed.append(record_id)
        source_view_changed = []
        for view_id, expected in (collection.get("source_view_sha256") or {}).items():
            try:
                if self.view(str(view_id)).get("view_sha256") != expected:
                    source_view_changed.append(str(view_id))
            except KeyError:
                source_view_changed.append(str(view_id))
        return {
            "missing_record_ids": missing,
            "changed_record_ids": changed,
            "changed_source_view_ids": source_view_changed,
            "drift_detected": bool(missing or changed or source_view_changed),
            "current_snapshot_sha256": _digest(current),
        }

    def review_collection(self, collection_id: str, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_collection_payload(request)
        actor = _actor(request.get("actor"))
        note = _safe_text(request.get("note"), 3000)
        evidence_reference = _safe_text(request.get("evidence_reference"), 600)
        if not note or not evidence_reference:
            raise ValueError("Collection review note and evidence reference are required.")
        current = self.collection(collection_id)
        if current.get("status") != "draft":
            raise ValueError("Only draft collections may be reviewed.")
        if self.require_separation and actor == current.get("created_by"):
            raise ValueError("Collection review requires separation of duties.")
        drift = self._collection_drift(current)
        updated = deepcopy(current)
        updated.update({
            "status": "reviewed",
            "reviewed_by": actor,
            "reviewed_at": _iso(self.now_fn()),
            "review_note": note,
            "review_evidence_reference": evidence_reference,
            "review_drift": drift,
            "updated_at": _iso(self.now_fn()),
        })
        updated["collection_sha256"] = _record_digest(updated, "collection_sha256")
        _append(self.collections_path, updated)
        self._event(collection_id, "research_collection_reviewed", actor, {"drift_detected": drift["drift_detected"]})
        return {"ok": True, "version": APP_VERSION, "collection": updated}

    def approve_collection(self, collection_id: str, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_collection_payload(request)
        actor = _actor(request.get("approved_by") or request.get("actor"))
        note = _safe_text(request.get("note"), 3000)
        if not note:
            raise ValueError("Collection approval note is required.")
        current = self.collection(collection_id)
        if current.get("status") != "reviewed":
            raise ValueError("Only reviewed collections may be approved.")
        if self.require_separation and actor in {current.get("created_by"), current.get("reviewed_by")}:
            raise ValueError("Collection approval requires a separate approver.")
        drift = self._collection_drift(current)
        if drift["drift_detected"] and not bool(request.get("acknowledge_drift", False)):
            raise ValueError("Collection drift must be acknowledged before approval.")
        updated = deepcopy(current)
        updated.update({
            "status": "approved",
            "approved_by": actor,
            "approved_at": _iso(self.now_fn()),
            "approval_note": note,
            "public_visible": bool(request.get("public_visible", current.get("public_visible_requested", False))),
            "approved_drift": drift,
            "drift_acknowledged": bool(request.get("acknowledge_drift", False)),
            "updated_at": _iso(self.now_fn()),
        })
        updated["collection_sha256"] = _record_digest(updated, "collection_sha256")
        _append(self.collections_path, updated)
        self._event(collection_id, "research_collection_approved", actor, {"public_visible": updated["public_visible"], "drift_detected": drift["drift_detected"]})
        return {"ok": True, "version": APP_VERSION, "collection": updated}

    def pathway(self, collection_id: str, *, public: bool = False) -> dict[str, Any]:
        collection = self.collection(collection_id, public=public)
        return {
            "ok": True,
            "version": APP_VERSION,
            "schema": PACKAGE_SCHEMA_VERSION,
            "collection_id": collection.get("collection_id"),
            "title": collection.get("title"),
            "purpose": collection.get("purpose"),
            "summary": collection.get("summary"),
            "record_count": collection.get("record_count"),
            "pathway": deepcopy(collection.get("evidence_pathway") or []),
            "records": deepcopy(collection.get("record_snapshots") or []),
            "collection_sha256": collection.get("collection_sha256"),
            "evidence_pathway_sha256": collection.get("evidence_pathway_sha256"),
            "human_curated": True,
            "visitor_queries_stored": False,
            "visitor_profiles_created": False,
            "source_records_mutated": False,
            "remote_write_performed": False,
            "certification_claimed": False,
        }

    def package_payload(self, collection_id: str, format: str = "json") -> tuple[str, str]:
        package = self.pathway(collection_id)
        format = _safe_text(format, 20).lower()
        if format == "json":
            return "application/json", json.dumps(package, indent=2, sort_keys=True) + "\n"
        if format != "markdown":
            raise ValueError("Unsupported collection package format.")
        lines = [
            f"# {package['title']}", "", f"**Collection:** `{package['collection_id']}`",
            f"**Checksum:** `{package['collection_sha256']}`", "", package.get("summary") or "", "",
            "## Purpose", "", package.get("purpose") or "", "", "## Evidence pathway", "",
        ]
        for step in package.get("pathway") or []:
            lines.extend([
                f"### {step.get('sequence')}. {step.get('title')}", "",
                f"- Record: `{step.get('record_id')}`",
                f"- Type: `{step.get('record_type')}`",
                f"- Record checksum: `{step.get('record_sha256')}`", "",
                step.get("rationale") or "", "",
            ])
        lines.extend(["## Boundaries", "", "- Human curated", "- No visitor query storage", "- No visitor profiling", "- No source-record mutation", "- No remote write", ""])
        return "text/markdown", "\n".join(lines)

    def history(self, entity_id: str, limit: int = 200) -> list[dict[str, Any]]:
        target = _safe_id(entity_id, "registry-collection-entity")
        rows = [row for row in _read_jsonl(self.events_path, self.max_records) if row.get("entity_id") == target]
        rows.sort(key=lambda row: str(row.get("occurred_at") or ""), reverse=True)
        return rows[:max(1, min(int(limit), 1000))]

    def status(self) -> dict[str, Any]:
        views = self.views(limit=2000)
        collections = self.collections(limit=2000)
        return {
            "ok": True,
            "version": APP_VERSION,
            "view_count": len(views),
            "approved_public_view_count": sum(1 for row in views if row.get("status") == "approved" and row.get("public_visible") is True),
            "collection_count": len(collections),
            "approved_public_collection_count": sum(1 for row in collections if row.get("status") == "approved" and row.get("public_visible") is True),
            "visitor_queries_stored": False,
            "visitor_profiles_created": False,
            "personal_identity_data_stored": False,
            "source_records_mutated": False,
            "approved_snapshots_overwritten": False,
            "network_verification_performed": False,
            "remote_write_performed": False,
            "certification_claimed": False,
        }
