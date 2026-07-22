"""Collection publication, citation exports, and research brief packages.

Site Intelligence v3.22.0 adds a human-governed publication layer above
approved public registry research collections. It prepares source-linked
briefs and citation packages without mutating source records, publishing to
remote systems, or storing visitor identities, recipients, or credentials.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
import re
from typing import Any, Callable, Mapping
from uuid import uuid4

from .config import Settings
from .version import APP_VERSION
from .live_intelligence_release_operations_v3130 import (
    _actor, _append, _digest, _iso, _latest, _read_jsonl,
    _resolve, _safe_id, _safe_text,
)
from .live_intelligence_registry_collections_v3210 import _reject_collection_payload

POLICY_SCHEMA_VERSION = "sc-site-intelligence-registry-publication-policy/1.0"
BRIEF_SCHEMA_VERSION = "sc-site-intelligence-registry-research-brief/1.0"
CITATION_SCHEMA_VERSION = "sc-site-intelligence-registry-citation-bundle/1.0"
EVENT_SCHEMA_VERSION = "sc-site-intelligence-registry-publication-event/1.0"
HANDOFF_SCHEMA_VERSION = "sc-site-intelligence-registry-publication-handoff/1.0"
PACKAGE_SCHEMA_VERSION = "sc-site-intelligence-registry-publication-package/1.0"

BRIEF_STATUSES = ("draft", "reviewed", "approved")
CITATION_FORMATS = ("json", "markdown", "bibtex", "ris")
HANDOFF_TARGETS = ("download", "knowledge_library", "publications", "decision_studio", "wordpress_manual_import")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def registry_publication_policy() -> dict[str, Any]:
    return {
        "ok": True,
        "version": APP_VERSION,
        "schema": POLICY_SCHEMA_VERSION,
        "principle": "Publish human-reviewed research briefs from approved public evidence pathways while retaining source checksums, citations, limitations, and manual delivery boundaries.",
        "brief_statuses": list(BRIEF_STATUSES),
        "citation_formats": list(CITATION_FORMATS),
        "handoff_targets": list(HANDOFF_TARGETS),
        "boundaries": {
            "human_review_required": True,
            "separation_of_duties_required": True,
            "approved_public_collections_only": True,
            "source_records_mutated": False,
            "source_collections_overwritten": False,
            "automatic_publication_performed": False,
            "remote_write_performed": False,
            "visitor_queries_stored": False,
            "visitor_profiles_created": False,
            "recipient_identities_stored": False,
            "credentials_stored": False,
            "citation_standard_certification_claimed": False,
        },
        "routes": {
            "policy": "/public/live-intelligence/registry-publications/policy",
            "status": "/public/live-intelligence/registry-publications/status",
            "briefs": "/public/live-intelligence/registry-publications/briefs",
            "brief": "/public/live-intelligence/registry-publications/briefs/{brief_id}",
            "citations": "/public/live-intelligence/registry-publications/briefs/{brief_id}/citations",
            "admin": "/admin/live-intelligence/registry-publications",
        },
    }


def _record_digest(record: Mapping[str, Any], field: str) -> str:
    return _digest({key: value for key, value in record.items() if key != field})


def _public_projection(record: Mapping[str, Any]) -> dict[str, Any]:
    excluded = {
        "created_by", "reviewed_by", "approved_by", "review_note", "approval_note",
        "internal_note", "actor", "handoff_actor", "review_evidence_reference",
    }
    return {key: deepcopy(value) for key, value in record.items() if key not in excluded}


def _text_list(value: Any, *, limit: int = 12, width: int = 1200) -> list[str]:
    if not isinstance(value, list):
        raise ValueError("Key findings must be a list.")
    rows = [_safe_text(item, width) for item in value]
    rows = [item for item in rows if item]
    if not rows:
        raise ValueError("At least one key finding is required.")
    return rows[:limit]


def _citation_key(record_id: str, index: int) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", record_id.lower()).strip("-")[:48]
    return f"sc-{slug or 'record'}-{index}"


def _citation_from_snapshot(snapshot: Mapping[str, Any], index: int) -> dict[str, Any]:
    record_id = str(snapshot.get("record_id") or f"record-{index}")
    reference = (
        snapshot.get("repository_reference") or snapshot.get("evidence_reference")
        or snapshot.get("public_policy_reference") or ""
    )
    citation = {
        "citation_key": _citation_key(record_id, index),
        "record_id": record_id,
        "record_type": snapshot.get("record_type") or "public_registry_record",
        "title": snapshot.get("title") or record_id,
        "publisher": "Sustainable Catalyst",
        "published_at": snapshot.get("published_at") or "",
        "reference": reference,
        "record_sha256": snapshot.get("record_sha256") or "",
        "source_note": "Approved public registry record retained in the source collection snapshot.",
    }
    citation["citation_sha256"] = _digest(citation)
    return citation


def _bibtex_escape(value: Any) -> str:
    return str(value or "").replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")


class LiveIntelligenceRegistryPublicationCenter:
    def __init__(
        self,
        settings: Settings,
        *,
        collections: Any,
        now_fn: Callable[[], datetime] = _utc_now,
    ) -> None:
        self.settings = settings
        self.collections_center = collections
        self.now_fn = now_fn
        self.briefs_path = _resolve(settings.live_intelligence_registry_publications_briefs_path)
        self.events_path = _resolve(settings.live_intelligence_registry_publications_events_path)
        self.handoffs_path = _resolve(settings.live_intelligence_registry_publications_handoffs_path)
        self.max_records = int(settings.live_intelligence_registry_publications_max_records)
        self.require_separation = bool(settings.live_intelligence_registry_publications_require_separation_of_duties)

    def _event(self, entity_id: str, event_type: str, actor: str, detail: Mapping[str, Any]) -> dict[str, Any]:
        event = {
            "schema": EVENT_SCHEMA_VERSION,
            "release_version": APP_VERSION,
            "event_id": f"registry-publication-event:{uuid4().hex[:20]}",
            "entity_id": entity_id,
            "event_type": event_type,
            "actor": actor,
            "occurred_at": _iso(self.now_fn()),
            "detail": deepcopy(dict(detail)),
            "append_only_publication_ledger": True,
            "source_records_mutated": False,
            "automatic_publication_performed": False,
            "remote_write_performed": False,
        }
        event["event_sha256"] = _record_digest(event, "event_sha256")
        _append(self.events_path, event)
        return event

    def briefs(self, *, public: bool = False, limit: int = 1000) -> list[dict[str, Any]]:
        rows = _latest(self.briefs_path, "brief_id", self.max_records)
        if public:
            rows = [
                _public_projection(row) for row in rows
                if row.get("status") == "approved" and row.get("public_visible") is True
            ]
        rows.sort(key=lambda row: str(row.get("approved_at") or row.get("created_at") or ""), reverse=True)
        return rows[:max(1, min(int(limit), 2000))]

    def brief(self, brief_id: str, *, public: bool = False) -> dict[str, Any]:
        target = _safe_id(brief_id, "registry-brief")
        for row in self.briefs(public=public, limit=2000):
            if row.get("brief_id") == target:
                return row
        raise KeyError(target)

    def _source_collection(self, collection_id: str) -> dict[str, Any]:
        collection = self.collections_center.collection(collection_id)
        if collection.get("status") != "approved" or collection.get("public_visible") is not True:
            raise ValueError("Research briefs may use approved public collections only.")
        return collection

    def _source_drift(self, brief: Mapping[str, Any]) -> dict[str, Any]:
        try:
            collection = self._source_collection(str(brief.get("collection_id") or ""))
        except (KeyError, ValueError):
            return {"source_missing": True, "source_changed": True, "current_collection_sha256": ""}
        current = str(collection.get("collection_sha256") or "")
        expected = str(brief.get("source_collection_sha256") or "")
        return {
            "source_missing": False,
            "source_changed": current != expected,
            "current_collection_sha256": current,
        }

    def create_brief(self, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_collection_payload(request)
        actor = _actor(request.get("actor"))
        collection_id = _safe_id(request.get("collection_id"), "registry-collection")
        collection = self._source_collection(collection_id)
        title = _safe_text(request.get("title"), 260)
        deck = _safe_text(request.get("deck"), 600)
        abstract = _safe_text(request.get("abstract"), 4000)
        methodology = _safe_text(request.get("methodology"), 4000)
        limitations = _safe_text(request.get("limitations"), 4000)
        if not all((title, deck, abstract, methodology, limitations)):
            raise ValueError("Brief title, deck, abstract, methodology, and limitations are required.")
        findings = _text_list(request.get("key_findings") or [])
        snapshots = deepcopy(collection.get("record_snapshots") or [])
        citations = [_citation_from_snapshot(row, index) for index, row in enumerate(snapshots, start=1)]
        pathway = deepcopy(collection.get("evidence_pathway") or [])
        brief_id = _safe_id(request.get("brief_id") or f"registry-brief:{uuid4().hex[:20]}", "registry-brief")
        if any(row.get("brief_id") == brief_id for row in self.briefs(limit=2000)):
            raise ValueError("Research brief ID already exists.")
        now = _iso(self.now_fn())
        record = {
            "schema": BRIEF_SCHEMA_VERSION,
            "release_version": APP_VERSION,
            "brief_id": brief_id,
            "collection_id": collection_id,
            "source_collection_sha256": collection.get("collection_sha256"),
            "source_pathway_sha256": collection.get("evidence_pathway_sha256"),
            "title": title,
            "deck": deck,
            "abstract": abstract,
            "key_findings": findings,
            "methodology": methodology,
            "limitations": limitations,
            "evidence_pathway": pathway,
            "record_snapshots": snapshots,
            "citations": citations,
            "citations_sha256": _digest(citations),
            "status": "draft",
            "created_by": actor,
            "created_at": now,
            "updated_at": now,
            "public_visible_requested": bool(request.get("public_visible", False)),
            "public_visible": False,
            "human_authored": True,
            "human_review_required": True,
            "approved_public_collections_only": True,
            "source_records_mutated": False,
            "source_collections_overwritten": False,
            "automatic_publication_performed": False,
            "remote_write_performed": False,
            "visitor_profiles_created": False,
            "recipient_identities_stored": False,
            "credentials_stored": False,
            "citation_standard_certification_claimed": False,
        }
        record["brief_sha256"] = _record_digest(record, "brief_sha256")
        _append(self.briefs_path, record)
        self._event(brief_id, "research_brief_created", actor, {"collection_id": collection_id, "citation_count": len(citations)})
        return {"ok": True, "version": APP_VERSION, "brief": record}

    def review_brief(self, brief_id: str, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_collection_payload(request)
        actor = _actor(request.get("actor"))
        note = _safe_text(request.get("note"), 3000)
        evidence_reference = _safe_text(request.get("evidence_reference"), 600)
        if not note or not evidence_reference:
            raise ValueError("Brief review note and evidence reference are required.")
        current = self.brief(brief_id)
        if current.get("status") != "draft":
            raise ValueError("Only draft research briefs may be reviewed.")
        if self.require_separation and actor == current.get("created_by"):
            raise ValueError("Brief review requires separation of duties.")
        drift = self._source_drift(current)
        updated = deepcopy(current)
        updated.update({
            "status": "reviewed", "reviewed_by": actor, "reviewed_at": _iso(self.now_fn()),
            "review_note": note, "review_evidence_reference": evidence_reference,
            "review_source_drift": drift, "updated_at": _iso(self.now_fn()),
        })
        updated["brief_sha256"] = _record_digest(updated, "brief_sha256")
        _append(self.briefs_path, updated)
        self._event(brief_id, "research_brief_reviewed", actor, {"source_changed": drift["source_changed"]})
        return {"ok": True, "version": APP_VERSION, "brief": updated}

    def approve_brief(self, brief_id: str, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_collection_payload(request)
        actor = _actor(request.get("approved_by") or request.get("actor"))
        note = _safe_text(request.get("note"), 3000)
        if not note:
            raise ValueError("Brief approval note is required.")
        current = self.brief(brief_id)
        if current.get("status") != "reviewed":
            raise ValueError("Only reviewed research briefs may be approved.")
        if self.require_separation and actor in {current.get("created_by"), current.get("reviewed_by")}:
            raise ValueError("Brief approval requires a separate approver.")
        drift = self._source_drift(current)
        if drift["source_changed"] and not bool(request.get("acknowledge_drift", False)):
            raise ValueError("Source collection drift must be acknowledged before approval.")
        updated = deepcopy(current)
        updated.update({
            "status": "approved", "approved_by": actor, "approved_at": _iso(self.now_fn()),
            "approval_note": note,
            "public_visible": bool(request.get("public_visible", current.get("public_visible_requested", False))),
            "approved_source_drift": drift,
            "drift_acknowledged": bool(request.get("acknowledge_drift", False)),
            "updated_at": _iso(self.now_fn()),
        })
        updated["brief_sha256"] = _record_digest(updated, "brief_sha256")
        _append(self.briefs_path, updated)
        self._event(brief_id, "research_brief_approved", actor, {"public_visible": updated["public_visible"], "source_changed": drift["source_changed"]})
        return {"ok": True, "version": APP_VERSION, "brief": updated}

    def citation_bundle(self, brief_id: str, *, public: bool = False) -> dict[str, Any]:
        brief = self.brief(brief_id, public=public)
        bundle = {
            "ok": True,
            "version": APP_VERSION,
            "schema": CITATION_SCHEMA_VERSION,
            "brief_id": brief.get("brief_id"),
            "collection_id": brief.get("collection_id"),
            "brief_sha256": brief.get("brief_sha256"),
            "source_collection_sha256": brief.get("source_collection_sha256"),
            "citation_count": len(brief.get("citations") or []),
            "citations": deepcopy(brief.get("citations") or []),
            "citations_sha256": brief.get("citations_sha256"),
            "citation_standard_certification_claimed": False,
            "source_records_mutated": False,
            "remote_write_performed": False,
        }
        bundle["bundle_sha256"] = _digest(bundle)
        return bundle

    def publication_package(self, brief_id: str, *, public: bool = False) -> dict[str, Any]:
        brief = self.brief(brief_id, public=public)
        package = {
            "ok": True,
            "version": APP_VERSION,
            "schema": PACKAGE_SCHEMA_VERSION,
            "brief": _public_projection(brief),
            "citation_bundle": self.citation_bundle(brief_id, public=public),
            "manual_delivery_only": True,
            "automatic_publication_performed": False,
            "remote_write_performed": False,
            "source_records_mutated": False,
        }
        package["package_sha256"] = _digest(package)
        return package

    def package_payload(self, brief_id: str, format: str = "json") -> tuple[str, str]:
        fmt = _safe_text(format, 20).lower()
        package = self.publication_package(brief_id)
        brief = package["brief"]
        citations = package["citation_bundle"]["citations"]
        if fmt == "json":
            return "application/json", json.dumps(package, indent=2, sort_keys=True) + "\n"
        if fmt == "markdown":
            lines = [
                f"# {brief.get('title')}", "", brief.get("deck") or "", "",
                f"**Brief:** `{brief.get('brief_id')}`", f"**Brief checksum:** `{brief.get('brief_sha256')}`",
                f"**Source collection:** `{brief.get('collection_id')}`", f"**Source checksum:** `{brief.get('source_collection_sha256')}`", "",
                "## Abstract", "", brief.get("abstract") or "", "", "## Key findings", "",
            ]
            lines.extend([f"- {item}" for item in brief.get("key_findings") or []])
            lines.extend(["", "## Methodology", "", brief.get("methodology") or "", "", "## Limitations", "", brief.get("limitations") or "", "", "## Evidence pathway", ""])
            for step in brief.get("evidence_pathway") or []:
                lines.extend([f"### {step.get('sequence')}. {step.get('title')}", "", step.get("rationale") or "", f"- Record: `{step.get('record_id')}`", f"- Checksum: `{step.get('record_sha256')}`", ""])
            lines.extend(["## Citations", ""])
            for index, citation in enumerate(citations, start=1):
                reference = f" Available at {citation.get('reference')}." if citation.get("reference") else ""
                lines.append(f"{index}. {citation.get('title')}. Sustainable Catalyst. `{citation.get('record_id')}`.{reference} Checksum `{citation.get('record_sha256')}`.")
            lines.extend(["", "## Publication boundaries", "", "- Human authored and reviewed", "- No automatic publication", "- No remote-system write", "- No source-record mutation", "- Citation exports are source-linked mappings, not certification of external citation-standard conformance", ""])
            return "text/markdown", "\n".join(lines)
        if fmt == "bibtex":
            blocks = []
            for citation in citations:
                fields = [
                    f"  title = {{{_bibtex_escape(citation.get('title'))}}}",
                    "  publisher = {Sustainable Catalyst}",
                    f"  note = {{Record {_bibtex_escape(citation.get('record_id'))}; checksum {_bibtex_escape(citation.get('record_sha256'))}}}",
                ]
                if citation.get("reference"):
                    fields.append(f"  howpublished = {{{_bibtex_escape(citation.get('reference'))}}}")
                blocks.append("@misc{" + citation["citation_key"] + ",\n" + ",\n".join(fields) + "\n}")
            return "application/x-bibtex", "\n\n".join(blocks) + "\n"
        if fmt == "ris":
            blocks = []
            for citation in citations:
                rows = ["TY  - GEN", f"TI  - {citation.get('title')}", "PB  - Sustainable Catalyst"]
                if citation.get("reference"):
                    rows.append(f"UR  - {citation.get('reference')}")
                rows.extend([f"N1  - Record {citation.get('record_id')}; checksum {citation.get('record_sha256')}", "ER  - "])
                blocks.append("\n".join(rows))
            return "application/x-research-info-systems", "\n\n".join(blocks) + "\n"
        raise ValueError("Unsupported research brief package format.")

    def record_handoff(self, brief_id: str, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_collection_payload(request)
        brief = self.brief(brief_id)
        if brief.get("status") != "approved":
            raise ValueError("Only approved research briefs may receive handoff receipts.")
        target = _safe_text(request.get("target"), 80).lower()
        fmt = _safe_text(request.get("format"), 20).lower() or "json"
        if target not in HANDOFF_TARGETS:
            raise ValueError("Unsupported publication handoff target.")
        if fmt not in CITATION_FORMATS:
            raise ValueError("Unsupported publication handoff format.")
        actor = _actor(request.get("actor"))
        note = _safe_text(request.get("note"), 2000)
        if not note:
            raise ValueError("Handoff note is required.")
        media_type, body = self.package_payload(brief_id, fmt)
        receipt = {
            "schema": HANDOFF_SCHEMA_VERSION,
            "release_version": APP_VERSION,
            "handoff_id": f"registry-publication-handoff:{uuid4().hex[:20]}",
            "brief_id": brief_id,
            "target": target,
            "format": fmt,
            "media_type": media_type,
            "package_sha256": _digest(body),
            "handoff_actor": actor,
            "note": note,
            "recorded_at": _iso(self.now_fn()),
            "manual_delivery_only": True,
            "automatic_publication_performed": False,
            "remote_write_performed": False,
            "credentials_stored": False,
            "recipient_identities_stored": False,
        }
        receipt["handoff_sha256"] = _record_digest(receipt, "handoff_sha256")
        _append(self.handoffs_path, receipt)
        self._event(brief_id, "research_brief_handoff_recorded", actor, {"target": target, "format": fmt, "package_sha256": receipt["package_sha256"]})
        return {"ok": True, "version": APP_VERSION, "handoff": receipt}

    def history(self, entity_id: str, limit: int = 200) -> list[dict[str, Any]]:
        target = _safe_id(entity_id, "registry-publication-entity")
        rows = [row for row in _read_jsonl(self.events_path, self.max_records) if row.get("entity_id") == target]
        rows.sort(key=lambda row: str(row.get("occurred_at") or ""), reverse=True)
        return rows[:max(1, min(int(limit), 1000))]

    def status(self) -> dict[str, Any]:
        briefs = self.briefs(limit=2000)
        handoffs = _read_jsonl(self.handoffs_path, self.max_records)
        return {
            "ok": True,
            "version": APP_VERSION,
            "brief_count": len(briefs),
            "approved_public_brief_count": sum(1 for row in briefs if row.get("status") == "approved" and row.get("public_visible") is True),
            "handoff_receipt_count": len(handoffs),
            "source_records_mutated": False,
            "source_collections_overwritten": False,
            "automatic_publication_performed": False,
            "remote_write_performed": False,
            "visitor_queries_stored": False,
            "visitor_profiles_created": False,
            "recipient_identities_stored": False,
            "credentials_stored": False,
            "citation_standard_certification_claimed": False,
        }
