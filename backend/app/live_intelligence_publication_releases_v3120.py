"""Governed publication adapters and release packages for Live Intelligence.

Site Intelligence v3.12.0 converts human-approved editorial workspaces into
immutable, adapter-specific delivery packages. It validates release metadata,
requires a separate release approver, records manual handoff receipts, and
never writes to WordPress or an institutional destination by itself.
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

POLICY_SCHEMA_VERSION = "sc-site-intelligence-publication-release-policy/1.0"
RELEASE_SCHEMA_VERSION = "sc-site-intelligence-publication-release/1.0"
EVENT_SCHEMA_VERSION = "sc-site-intelligence-publication-release-event/1.0"
PACKAGE_SCHEMA_VERSION = "sc-site-intelligence-publication-package/1.0"
HANDOFF_SCHEMA_VERSION = "sc-site-intelligence-publication-handoff/1.0"

ADAPTERS = {
    "publications": {
        "label": "Sustainable Catalyst Publications",
        "formats": ["json", "markdown"],
        "delivery": "manual_import",
        "destination_write_performed": False,
    },
    "knowledge_library": {
        "label": "Knowledge Library",
        "formats": ["json", "markdown"],
        "delivery": "manual_import",
        "destination_write_performed": False,
    },
    "decision_studio": {
        "label": "Decision Studio",
        "formats": ["json"],
        "delivery": "provider_neutral_handoff",
        "destination_write_performed": False,
    },
    "wordpress_package": {
        "label": "WordPress reviewed-content package",
        "formats": ["json", "markdown"],
        "delivery": "manual_import",
        "destination_write_performed": False,
    },
    "download": {
        "label": "Download archive",
        "formats": ["json", "markdown"],
        "delivery": "direct_download",
        "destination_write_performed": False,
    },
}
ALLOWED_VISIBILITY = ("public", "unlisted", "internal")
DENIED_IDENTITY_FIELDS = {
    "email", "email_address", "phone", "phone_number", "ip", "ip_address",
    "cookie", "session_id", "user_agent", "referrer", "recipient", "recipients",
    "subscriber", "subscriber_id", "subscriber_email", "contact_id", "metadata",
    "access_token", "api_key", "secret", "webhook", "webhook_url",
}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime | None = None) -> str:
    return (value or _utc_now()).astimezone(timezone.utc).isoformat()


def _safe_text(value: Any, limit: int = 1000) -> str:
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
        raise ValueError(f"{field} must be a role label or editorial handle, not contact information.")
    return text


def _reject_identity_payload(value: Any, path: str = "request") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized = str(key).strip().lower().replace("-", "_")
            if normalized in DENIED_IDENTITY_FIELDS:
                raise ValueError(f"{path}.{key} is not accepted; identities, credentials, and delivery secrets are outside release packages.")
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
    rows=[]
    for line in lines:
        try:
            row=json.loads(line)
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def _latest(path: Path, key: str, limit: int) -> list[dict[str, Any]]:
    rows={}
    for row in _read_jsonl(path, limit):
        identifier=_safe_text(row.get(key),180)
        if identifier:
            rows[identifier]=row
    return list(rows.values())


def publication_release_policy() -> dict[str, Any]:
    return {
        "ok": True,
        "version": APP_VERSION,
        "schema": POLICY_SCHEMA_VERSION,
        "principle": "Create verifiable publication packages from human-approved evidence without performing silent destination writes.",
        "adapters": adapter_catalog()["adapters"],
        "visibility": list(ALLOWED_VISIBILITY),
        "boundaries": {
            "approved_editorial_workspace_required": True,
            "release_validation_required": True,
            "separate_release_approval_required": True,
            "evidence_mutation_allowed": False,
            "automatic_publication": False,
            "automatic_wordpress_write": False,
            "institutional_adapter_write_performed": False,
            "credentials_stored": False,
            "recipient_identities_stored": False,
            "manual_handoff_receipts_retained": True,
            "package_checksums_required": True,
        },
        "routes": {
            "policy": "/public/live-intelligence/publication-releases/policy",
            "adapters": "/public/live-intelligence/publication-releases/adapters",
            "status": "/public/live-intelligence/publication-releases/status",
            "admin": "/admin/live-intelligence/publication-releases",
        },
    }


def adapter_catalog() -> dict[str, Any]:
    return {
        "ok": True,
        "version": APP_VERSION,
        "schema": POLICY_SCHEMA_VERSION,
        "adapters": [{"adapter_id": key, **deepcopy(value)} for key, value in ADAPTERS.items()],
        "destination_writes_performed": False,
    }


class LiveIntelligencePublicationReleaseCenter:
    def __init__(
        self,
        settings: Settings,
        *,
        editorial_center: Any,
        briefing_center: Any,
        now_fn: Callable[[], datetime] = _utc_now,
    ) -> None:
        self.settings=settings
        self.editorial_center=editorial_center
        self.briefing_center=briefing_center
        self.now_fn=now_fn
        self.releases_path=_resolve(settings.live_intelligence_publication_releases_path)
        self.events_path=_resolve(settings.live_intelligence_publication_release_events_path)
        self.handoffs_path=_resolve(settings.live_intelligence_publication_handoffs_path)
        self.max_records=int(settings.live_intelligence_publication_max_records)
        self.require_separation=bool(settings.live_intelligence_publication_require_separation_of_duties)

    def _event(self, release_id: str, event_type: str, actor: str, detail: Mapping[str, Any]) -> dict[str, Any]:
        event={
            "schema": EVENT_SCHEMA_VERSION,
            "release_version": APP_VERSION,
            "event_id": f"publication-event:{uuid4().hex[:20]}",
            "release_id": release_id,
            "event_type": event_type,
            "actor": actor,
            "occurred_at": _iso(self.now_fn()),
            "detail": deepcopy(dict(detail)),
        }
        event["event_sha256"]=_digest({k:v for k,v in event.items() if k!="event_sha256"})
        _append(self.events_path,event)
        return event

    def releases(self, limit: int = 100) -> list[dict[str, Any]]:
        rows=[row for row in _latest(self.releases_path,"release_id",self.max_records) if not row.get("deleted")]
        return sorted(rows,key=lambda row:str(row.get("updated_at") or row.get("created_at") or ""),reverse=True)[:max(1,min(int(limit),500))]

    def release(self, release_id: str) -> dict[str, Any]:
        target=_safe_id(release_id,"publication-release")
        for row in self.releases(500):
            if row.get("release_id")==target:
                return row
        raise KeyError(target)

    def _canonical_payload(self, workspace: Mapping[str, Any], briefing: Mapping[str, Any], request: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "schema": PACKAGE_SCHEMA_VERSION,
            "release_version": APP_VERSION,
            "workspace_id": workspace.get("workspace_id"),
            "briefing_id": workspace.get("briefing_id"),
            "title": _safe_text((workspace.get("content") or {}).get("title"),1000),
            "deck": _safe_text((workspace.get("content") or {}).get("deck"),2000),
            "executive_summary": _safe_text((workspace.get("content") or {}).get("executive_summary"),6000),
            "key_observations": deepcopy((workspace.get("content") or {}).get("key_observations") or []),
            "limitations": deepcopy((workspace.get("content") or {}).get("limitations") or []),
            "claims": deepcopy(briefing.get("claims") or []),
            "evidence": deepcopy(briefing.get("evidence") or []),
            "chronology": deepcopy(briefing.get("chronology") or []),
            "visibility": _safe_text(request.get("visibility") or workspace.get("briefing_visibility") or "public",20).lower(),
            "target_slug": _safe_id(request.get("target_slug") or (workspace.get("content") or {}).get("title"),"briefing"),
            "embargo_until": _safe_text(request.get("embargo_until"),80),
            "human_editorial_approval": {
                "reviewed_by": workspace.get("reviewed_by"),
                "reviewed_at": workspace.get("reviewed_at"),
                "reason": workspace.get("review_reason"),
            },
            "automatic_publication": False,
            "destination_write_performed": False,
        }

    def prepare(self, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_identity_payload(request)
        actor=_actor(request.get("actor"))
        workspace=self.editorial_center.workspace(_safe_id(request.get("workspace_id"),"editorial-workspace"))
        if workspace.get("status")!="approved" or workspace.get("publication_ready") is not True:
            raise ValueError("Only a human-approved editorial workspace may become a release candidate.")
        requested=request.get("adapters") or list(ADAPTERS)
        if not isinstance(requested,Sequence) or isinstance(requested,(str,bytes)):
            raise ValueError("adapters must be a list.")
        adapters=[]
        for value in requested:
            key=_safe_text(value,80).lower()
            if key not in ADAPTERS:
                raise ValueError("Unsupported publication adapter.")
            if key not in adapters:
                adapters.append(key)
        if not adapters:
            raise ValueError("At least one publication adapter is required.")
        visibility=_safe_text(request.get("visibility") or workspace.get("briefing_visibility") or "public",20).lower()
        if visibility not in ALLOWED_VISIBILITY:
            raise ValueError("Unsupported release visibility.")
        briefing=self.briefing_center._briefing(workspace["briefing_id"],public=False)
        immutable={"claims":briefing.get("claims") or [],"evidence":briefing.get("evidence") or [],"chronology":briefing.get("chronology") or []}
        if _digest(immutable)!=workspace.get("immutable_source_digest"):
            raise ValueError("Canonical evidence changed after editorial approval; return the workspace to review.")
        payload=self._canonical_payload(workspace,briefing,{**dict(request),"visibility":visibility})
        payload_sha=_digest(payload)
        packages=[]
        for adapter in adapters:
            definition=ADAPTERS[adapter]
            packages.append({
                "adapter_id":adapter,
                "label":definition["label"],
                "delivery":definition["delivery"],
                "formats":definition["formats"],
                "filename_base":f"{payload['target_slug']}-{adapter}",
                "package_sha256":_digest({"adapter":adapter,"payload_sha256":payload_sha,"formats":definition["formats"]}),
                "destination_write_performed":False,
                "manual_action_required":adapter!="download",
            })
        now=_iso(self.now_fn())
        record={
            "schema":RELEASE_SCHEMA_VERSION,
            "release_version":APP_VERSION,
            "release_id":_safe_id(request.get("release_id") or f"publication-release:{uuid4().hex[:20]}","publication-release"),
            "workspace_id":workspace.get("workspace_id"),
            "briefing_id":workspace.get("briefing_id"),
            "status":"prepared",
            "prepared_by":actor,
            "prepared_at":now,
            "validated_by":"",
            "validated_at":"",
            "approved_by":"",
            "approved_at":"",
            "approval_reason":"",
            "visibility":visibility,
            "target_slug":payload["target_slug"],
            "embargo_until":payload["embargo_until"],
            "immutable_source_digest":workspace.get("immutable_source_digest"),
            "workspace_sha256":workspace.get("workspace_sha256"),
            "content_sha256":workspace.get("content_sha256"),
            "payload":payload,
            "payload_sha256":payload_sha,
            "packages":packages,
            "validation":{},
            "automatic_publication":False,
            "automatic_wordpress_write":False,
            "institutional_write_performed":False,
            "created_at":now,
            "updated_at":now,
        }
        record["release_sha256"]=_digest({k:v for k,v in record.items() if k!="release_sha256"})
        _append(self.releases_path,record)
        self._event(record["release_id"],"release_prepared",actor,{"workspace_id":record["workspace_id"],"adapters":adapters,"payload_sha256":payload_sha})
        return {"ok":True,"version":APP_VERSION,"release":record}

    def validate(self, release_id: str, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_identity_payload(request)
        actor=_actor(request.get("actor"))
        reason=_safe_text(request.get("reason"),1200)
        if not reason:
            raise ValueError("reason is required.")
        current=self.release(release_id)
        if current.get("status") not in {"prepared","validation_failed"}:
            raise ValueError("Only a prepared release may be validated.")
        workspace=self.editorial_center.workspace(current["workspace_id"])
        briefing=self.briefing_center._briefing(current["briefing_id"],public=False)
        immutable={"claims":briefing.get("claims") or [],"evidence":briefing.get("evidence") or [],"chronology":briefing.get("chronology") or []}
        checks={
            "workspace_still_approved": workspace.get("status")=="approved" and workspace.get("publication_ready") is True,
            "workspace_unchanged": workspace.get("workspace_sha256")==current.get("workspace_sha256"),
            "content_unchanged": workspace.get("content_sha256")==current.get("content_sha256"),
            "evidence_unchanged": _digest(immutable)==current.get("immutable_source_digest"),
            "payload_checksum_valid": _digest(current.get("payload") or {})==current.get("payload_sha256"),
            "packages_have_checksums": bool(current.get("packages")) and all(row.get("package_sha256") for row in current.get("packages",[])),
            "no_destination_write": all(row.get("destination_write_performed") is False for row in current.get("packages",[])),
        }
        passed=all(checks.values())
        updated=dict(current)
        updated.update({
            "status":"validated" if passed else "validation_failed",
            "validated_by":actor,
            "validated_at":_iso(self.now_fn()),
            "validation":{"passed":passed,"checks":checks,"reason":reason},
            "updated_at":_iso(self.now_fn()),
        })
        updated["release_sha256"]=_digest({k:v for k,v in updated.items() if k!="release_sha256"})
        _append(self.releases_path,updated)
        self._event(updated["release_id"],"release_validated",actor,{"passed":passed,"checks":checks,"reason":reason})
        return {"ok":True,"version":APP_VERSION,"release":updated,"validation":updated["validation"]}

    def approve(self, release_id: str, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_identity_payload(request)
        approver=_actor(request.get("approved_by"),"approved_by")
        reason=_safe_text(request.get("reason"),1400)
        if not reason:
            raise ValueError("reason is required.")
        current=self.release(release_id)
        if current.get("status")!="validated" or not (current.get("validation") or {}).get("passed"):
            raise ValueError("Release must pass validation before approval.")
        if self.require_separation and approver in {str(current.get("prepared_by") or ""),str(current.get("validated_by") or "")}:
            raise ValueError("Release approval requires separation of duties from preparation and validation.")
        updated=dict(current)
        updated.update({
            "status":"approved",
            "approved_by":approver,
            "approved_at":_iso(self.now_fn()),
            "approval_reason":reason,
            "updated_at":_iso(self.now_fn()),
        })
        updated["release_sha256"]=_digest({k:v for k,v in updated.items() if k!="release_sha256"})
        _append(self.releases_path,updated)
        self._event(updated["release_id"],"release_approved",approver,{"reason":reason,"separation_of_duties_verified":self.require_separation})
        return {"ok":True,"version":APP_VERSION,"release":updated}

    def create_handoff(self, release_id: str, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_identity_payload(request)
        actor=_actor(request.get("actor"))
        current=self.release(release_id)
        if current.get("status") not in {"approved","handoff_ready"}:
            raise ValueError("Only an approved release may create manual handoff receipts.")
        requested=request.get("adapters") or [row.get("adapter_id") for row in current.get("packages",[])]
        if not isinstance(requested,Sequence) or isinstance(requested,(str,bytes)):
            raise ValueError("adapters must be a list.")
        available={row.get("adapter_id"):row for row in current.get("packages",[])}
        receipts=[]
        for value in requested:
            adapter=_safe_text(value,80).lower()
            if adapter not in available:
                raise ValueError("Adapter was not included in the approved release package.")
            receipts.append({
                "adapter_id":adapter,
                "package_sha256":available[adapter].get("package_sha256"),
                "state":"download_ready" if adapter=="download" else "manual_delivery_ready",
                "destination_write_performed":False,
                "manual_confirmation_required":adapter!="download",
            })
        handoff={
            "schema":HANDOFF_SCHEMA_VERSION,
            "release_version":APP_VERSION,
            "handoff_id":f"publication-handoff:{uuid4().hex[:20]}",
            "release_id":current.get("release_id"),
            "workspace_id":current.get("workspace_id"),
            "created_by":actor,
            "created_at":_iso(self.now_fn()),
            "receipts":receipts,
            "release_sha256":current.get("release_sha256"),
            "destination_write_performed":False,
            "provider_neutral":True,
            "credentials_included":False,
            "recipient_data_included":False,
        }
        handoff["handoff_sha256"]=_digest({k:v for k,v in handoff.items() if k!="handoff_sha256"})
        _append(self.handoffs_path,handoff)
        updated=dict(current)
        updated.update({"status":"handoff_ready","updated_at":_iso(self.now_fn())})
        updated["release_sha256"]=_digest({k:v for k,v in updated.items() if k!="release_sha256"})
        _append(self.releases_path,updated)
        self._event(updated["release_id"],"handoff_created",actor,{"handoff_id":handoff["handoff_id"],"adapters":[r["adapter_id"] for r in receipts]})
        return {"ok":True,"version":APP_VERSION,"release":updated,"handoff":handoff}

    def package_payload(self, release_id: str, format: str="json") -> tuple[str,str]:
        current=self.release(release_id)
        if current.get("status") not in {"approved","handoff_ready"}:
            raise ValueError("Only an approved release package may be exported.")
        payload={
            "schema":PACKAGE_SCHEMA_VERSION,
            "version":APP_VERSION,
            "release_id":current.get("release_id"),
            "release_sha256":current.get("release_sha256"),
            "payload_sha256":current.get("payload_sha256"),
            "visibility":current.get("visibility"),
            "embargo_until":current.get("embargo_until"),
            "packages":current.get("packages"),
            "content":current.get("payload"),
            "approval":{"approved_by":current.get("approved_by"),"approved_at":current.get("approved_at"),"reason":current.get("approval_reason")},
            "destination_write_performed":False,
        }
        normalized=_safe_text(format,20).lower()
        if normalized=="json":
            return "application/json",json.dumps(payload,indent=2,sort_keys=True,ensure_ascii=False)+"\n"
        if normalized!="markdown":
            raise ValueError("format must be json or markdown.")
        content=payload["content"] or {}
        lines=[f"# {content.get('title') or 'Live Intelligence release'}","",str(content.get("deck") or ""),"","## Executive summary","",str(content.get("executive_summary") or "")]
        for heading,key in (("Key observations","key_observations"),("Limitations","limitations")):
            rows=content.get(key) or []
            if rows:
                lines.extend(["",f"## {heading}"]+[f"- {row}" for row in rows])
        lines.extend(["","## Release governance",f"- Release ID: `{payload['release_id']}`",f"- Payload SHA-256: `{payload['payload_sha256']}`","- Destination write performed: no"])
        return "text/markdown","\n".join(lines).strip()+"\n"

    def history(self, release_id: str, limit: int=200) -> list[dict[str, Any]]:
        target=_safe_id(release_id,"publication-release")
        rows=[row for row in _read_jsonl(self.events_path,self.max_records) if row.get("release_id")==target]
        return rows[-max(1,min(int(limit),1000)):]

    def status(self) -> dict[str, Any]:
        rows=self.releases(500)
        handoffs=_latest(self.handoffs_path,"handoff_id",self.max_records)
        states=("prepared","validated","validation_failed","approved","handoff_ready")
        return {
            "ok":True,"version":APP_VERSION,"schema":POLICY_SCHEMA_VERSION,
            "release_count":len(rows),
            "status_counts":{state:sum(1 for row in rows if row.get("status")==state) for state in states},
            "approved_count":sum(1 for row in rows if row.get("status") in {"approved","handoff_ready"}),
            "handoff_count":len(handoffs),
            "adapter_count":len(ADAPTERS),
            "separation_of_duties_required":self.require_separation,
            "automatic_publication":False,
            "automatic_wordpress_write":False,
            "institutional_write_performed":False,
        }

    def control_center(self) -> dict[str, Any]:
        return {"ok":True,"version":APP_VERSION,"policy":publication_release_policy(),"status":self.status(),"releases":self.releases(100),"handoffs":_latest(self.handoffs_path,"handoff_id",self.max_records)[-100:]}
