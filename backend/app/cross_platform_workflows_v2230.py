from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Callable
from uuid import uuid4

from .config import Settings

RELEASE_VERSION = "3.10.0"
SCHEMA_VERSION = "sc-site-intelligence-cross-platform-workflows/1.0"
PACKET_SCHEMA = "sc-cross-platform-intelligence-packet/1.0"
RECEIPT_SCHEMA = "sc-cross-platform-intelligence-receipt/1.0"
ATTEMPT_SCHEMA = "sc-cross-platform-delivery-attempt/1.0"
LINKBACK_SCHEMA = "sc-cross-platform-linkback/1.0"
QUEUE_SCHEMA = "sc-cross-platform-recovery-queue/1.0"

PLATFORMS = {
    "site-intelligence", "workbench", "decision-studio", "research-librarian",
    "knowledge-library", "research-lab", "platform-core",
}
PACKET_STATUSES = {"draft", "validated", "queued", "waiting_external_receipt", "accepted", "completed", "rejected", "failed", "cancelled"}
RECEIPT_STATUSES = {"accepted", "completed", "rejected", "failed"}
ACTOR_ROLES = {"analyst", "reviewer", "publisher", "administrator", "system"}
_SECRET = re.compile(r"(?:token|secret|password|authorization|api[_-]?key|cookie|session|email|phone|address)", re.I)

DEFAULT_ROUTES = [
    {"route_id":"site-intelligence-to-workbench-analysis","source_platform":"site-intelligence","target_platform":"workbench","packet_type":"analytical_packet","required_payload_fields":["title","question","datasets"],"description":"Send evidence-linked datasets, questions, assumptions, and units to Workbench."},
    {"route_id":"workbench-to-site-intelligence-evidence","source_platform":"workbench","target_platform":"site-intelligence","packet_type":"calculated_evidence","required_payload_fields":["title","method","results"],"description":"Return calculated evidence with methods, units, assumptions, and reproducibility references."},
    {"route_id":"site-intelligence-to-decision-studio-scenario","source_platform":"site-intelligence","target_platform":"decision-studio","packet_type":"scenario_decision_packet","required_payload_fields":["title","scenarios","evidence_ids"],"description":"Send source-aware scenarios, uncertainties, and evidence into Decision Studio."},
    {"route_id":"decision-studio-to-site-intelligence-outcome","source_platform":"decision-studio","target_platform":"site-intelligence","packet_type":"decision_assumption_outcome","required_payload_fields":["decision_id","assumptions","outcomes"],"description":"Return decision assumptions, selected options, and monitored outcomes."},
    {"route_id":"site-intelligence-to-research-librarian-question","source_platform":"site-intelligence","target_platform":"research-librarian","packet_type":"research_question","required_payload_fields":["question","scope"],"description":"Send bounded research questions and current evidence gaps."},
    {"route_id":"research-librarian-to-site-intelligence-sources","source_platform":"research-librarian","target_platform":"site-intelligence","packet_type":"source_recommendations","required_payload_fields":["question_id","sources"],"description":"Return source and reading recommendations without claiming automatic ingestion."},
    {"route_id":"site-intelligence-to-knowledge-library-publication","source_platform":"site-intelligence","target_platform":"knowledge-library","packet_type":"publication_archive","required_payload_fields":["title","publication_id","source_ids"],"description":"Prepare publication and archival metadata for Knowledge Library."},
    {"route_id":"knowledge-library-to-site-intelligence-document","source_platform":"knowledge-library","target_platform":"site-intelligence","packet_type":"document_evidence","required_payload_fields":["document_id","title","evidence"],"description":"Return document evidence and citations to Site Intelligence."},
    {"route_id":"site-intelligence-to-research-lab-dataset","source_platform":"site-intelligence","target_platform":"research-lab","packet_type":"dataset_observation_package","required_payload_fields":["title","dataset_refs","methods"],"description":"Send datasets, observations, methods, and provenance to Research Lab."},
    {"route_id":"research-lab-to-site-intelligence-result","source_platform":"research-lab","target_platform":"site-intelligence","packet_type":"experiment_result","required_payload_fields":["run_id","dataset_id","results"],"description":"Return experiment, calibration, and observation results with provenance."},
    {"route_id":"site-intelligence-to-platform-core-registration","source_platform":"site-intelligence","target_platform":"platform-core","packet_type":"workflow_registration","required_payload_fields":["workflow_id","route_id","packet_sha256"],"description":"Prepare a workflow registration envelope for Platform Core orchestration."},
    {"route_id":"platform-core-to-site-intelligence-status","source_platform":"platform-core","target_platform":"site-intelligence","packet_type":"workflow_status","required_payload_fields":["workflow_id","status","receipt_id"],"description":"Return orchestration status and receipt references."},
]


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
    return (cleaned or fallback)[:200]


def _safe_text(value: Any, limit: int = 4000) -> str:
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", str(value or "")).strip()[:limit]


def _safe_list(value: Any, maximum: int = 200, length: int = 300) -> list[str]:
    if not isinstance(value, list):
        return []
    output: list[str] = []
    for item in value[:maximum]:
        token = _safe_text(item, length)
        if token and token not in output:
            output.append(token)
    return output


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): ("[redacted]" if _SECRET.search(str(k)) else _redact(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


def _read_json(path: Path, default: Any) -> Any:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default
    return value


def _read_jsonl(path: Path, limit: int = 50000) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()[-limit:]
    except (FileNotFoundError, OSError):
        return []
    output: list[dict[str, Any]] = []
    for line in lines:
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            output.append(row)
    return output


def _append(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _latest(path: Path, key: str, limit: int) -> list[dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for row in _read_jsonl(path, limit):
        identifier = str(row.get(key) or "")
        if identifier:
            rows[identifier] = row
    return [row for row in rows.values() if not row.get("deleted")]


class CrossPlatformWorkflowCenter:
    """Typed, file-backed workflow handoff control plane.

    This component prepares and validates portable packets, receipts, linkbacks, and
    retry records. It does not claim remote delivery, account provisioning, or a
    persistent message broker. Platform Core remains the intended orchestration layer.
    """

    def __init__(self, settings: Settings, now_fn: Callable[[], datetime] = _utc_now) -> None:
        self.settings = settings
        self.now_fn = now_fn
        self.packets_path = _resolve(settings.cross_platform_workflows_packets_path)
        self.receipts_path = _resolve(settings.cross_platform_workflows_receipts_path)
        self.attempts_path = _resolve(settings.cross_platform_workflows_attempts_path)
        self.linkbacks_path = _resolve(settings.cross_platform_workflows_linkbacks_path)
        self.queue_path = _resolve(settings.cross_platform_workflows_queue_path)
        self.policy = _read_json(_resolve(settings.cross_platform_workflows_policy_path), {})
        registry = _read_json(_resolve(settings.cross_platform_workflows_registry_path), {})
        routes = registry.get("routes") if isinstance(registry, dict) else None
        self.route_rows = routes if isinstance(routes, list) and routes else DEFAULT_ROUTES
        self.route_map = {str(row.get("route_id")): row for row in self.route_rows if isinstance(row, dict) and row.get("route_id")}
        self.max_records = settings.cross_platform_workflows_max_records
        self.max_attempts = settings.cross_platform_workflows_max_attempts
        self.retry_delay_seconds = settings.cross_platform_workflows_retry_delay_seconds

    def routes(self, public: bool = False) -> list[dict[str, Any]]:
        rows = []
        for route in self.route_rows:
            row = {
                "route_id": route.get("route_id"),
                "source_platform": route.get("source_platform"),
                "target_platform": route.get("target_platform"),
                "packet_type": route.get("packet_type"),
                "description": route.get("description"),
                "required_payload_fields": list(route.get("required_payload_fields") or []),
                "bidirectional_counterpart": route.get("bidirectional_counterpart", ""),
            }
            if not public:
                row["validation_schema"] = route.get("validation_schema", PACKET_SCHEMA)
            rows.append(row)
        return rows

    def packets(self) -> list[dict[str, Any]]:
        return sorted(_latest(self.packets_path, "packet_id", self.max_records), key=lambda row: str(row.get("updated_at", "")), reverse=True)

    def _packet(self, packet_id: str) -> dict[str, Any]:
        token = _safe_id(packet_id)
        for row in self.packets():
            if row.get("packet_id") == token:
                return row
        raise KeyError(token)

    def receipts(self, packet_id: str | None = None) -> list[dict[str, Any]]:
        rows = _latest(self.receipts_path, "receipt_id", self.max_records)
        if packet_id:
            rows = [row for row in rows if row.get("packet_id") == _safe_id(packet_id)]
        return sorted(rows, key=lambda row: str(row.get("received_at", "")), reverse=True)

    def attempts(self, packet_id: str | None = None) -> list[dict[str, Any]]:
        rows = _latest(self.attempts_path, "attempt_id", self.max_records)
        if packet_id:
            rows = [row for row in rows if row.get("packet_id") == _safe_id(packet_id)]
        return sorted(rows, key=lambda row: str(row.get("created_at", "")), reverse=True)

    def linkbacks(self, packet_id: str | None = None) -> list[dict[str, Any]]:
        rows = _latest(self.linkbacks_path, "linkback_id", self.max_records)
        if packet_id:
            rows = [row for row in rows if row.get("packet_id") == _safe_id(packet_id)]
        return sorted(rows, key=lambda row: str(row.get("created_at", "")), reverse=True)

    def queue(self) -> list[dict[str, Any]]:
        return sorted(_latest(self.queue_path, "queue_id", self.max_records), key=lambda row: str(row.get("updated_at", "")), reverse=True)

    def _route_for_request(self, request: dict[str, Any]) -> dict[str, Any]:
        route_id = _safe_id(request.get("route_id"), "")
        if route_id and route_id in self.route_map:
            return self.route_map[route_id]
        source = _safe_text(request.get("source_platform"), 80).lower()
        target = _safe_text(request.get("target_platform"), 80).lower()
        packet_type = _safe_text(request.get("packet_type"), 100).lower()
        matches = [route for route in self.route_rows if route.get("source_platform") == source and route.get("target_platform") == target and route.get("packet_type") == packet_type]
        if len(matches) != 1:
            raise ValueError("A registered route_id or unique source/target/packet_type combination is required.")
        return matches[0]

    def validate_payload(self, route: dict[str, Any], payload: Any) -> dict[str, Any]:
        errors: list[str] = []
        warnings: list[str] = []
        if not isinstance(payload, dict):
            errors.append("payload must be an object")
            payload = {}
        for field in route.get("required_payload_fields") or []:
            if field not in payload or payload.get(field) in (None, "", []):
                errors.append(f"payload.{field} is required")
        if len(_canonical(payload)) > self.settings.cross_platform_workflows_max_payload_bytes:
            errors.append("payload exceeds configured maximum bytes")
        if not payload.get("provenance"):
            warnings.append("payload.provenance is recommended; packet-level provenance remains required")
        return {"valid": not errors, "errors": errors, "warnings": warnings}

    def create_packet(self, request: dict[str, Any], actor_role: str = "administrator", actor_id: str = "system", direction: str = "outbound") -> dict[str, Any]:
        role = _safe_text(actor_role, 30).lower()
        if role not in ACTOR_ROLES:
            raise ValueError("Unsupported actor_role.")
        route = self._route_for_request(request)
        source = str(route.get("source_platform"))
        target = str(route.get("target_platform"))
        if source not in PLATFORMS or target not in PLATFORMS:
            raise ValueError("Unsupported platform identifier.")
        payload = request.get("payload") if isinstance(request.get("payload"), dict) else {}
        validation = self.validate_payload(route, payload)
        provenance = request.get("provenance") if isinstance(request.get("provenance"), dict) else {}
        source_record_ids = _safe_list(provenance.get("source_record_ids"), 500, 300)
        if not source_record_ids and direction == "outbound":
            validation["warnings"].append("No source_record_ids were supplied.")
        now = self.now_fn()
        packet_id = _safe_id(request.get("packet_id") or f"packet:{uuid4().hex[:20]}")
        if any(row.get("packet_id") == packet_id for row in self.packets()):
            raise ValueError("packet_id already exists.")
        record = {
            "schema": PACKET_SCHEMA,
            "release_version": RELEASE_VERSION,
            "packet_id": packet_id,
            "workflow_id": _safe_id(request.get("workflow_id") or f"workflow:{uuid4().hex[:16]}"),
            "route_id": route.get("route_id"),
            "packet_type": route.get("packet_type"),
            "source_platform": source,
            "target_platform": target,
            "direction": direction,
            "status": "validated" if validation["valid"] else "draft",
            "title": _safe_text(request.get("title") or payload.get("title") or route.get("description"), 300),
            "payload": _redact(payload),
            "provenance": {
                "source_record_ids": source_record_ids,
                "source_packet_ids": _safe_list(provenance.get("source_packet_ids"), 200, 300),
                "source_urls": _safe_list(provenance.get("source_urls"), 100, 1000),
                "methodology_ids": _safe_list(provenance.get("methodology_ids"), 100, 300),
                "created_by": _safe_id(actor_id),
                "created_by_role": role,
            },
            "validation": validation,
            "platform_core_envelope": {
                "orchestration_requested": bool(request.get("platform_core_orchestration")),
                "remote_registration_confirmed": False,
                "transport": "portable-json-packet",
            },
            "created_at": _iso(now),
            "updated_at": _iso(now),
            "expires_at": _safe_text(request.get("expires_at"), 80),
            "automatic_remote_write": False,
            "external_delivery_confirmed": False,
        }
        record["sha256"] = _digest({k: v for k, v in record.items() if k != "sha256"})
        _append(self.packets_path, record)
        return record

    def validate_packet(self, packet_id: str) -> dict[str, Any]:
        packet = self._packet(packet_id)
        route = self.route_map.get(str(packet.get("route_id")))
        errors: list[str] = []
        if not route:
            errors.append("route_id is not registered")
            validation = {"valid": False, "errors": errors, "warnings": []}
        else:
            validation = self.validate_payload(route, packet.get("payload"))
            if packet.get("source_platform") != route.get("source_platform"):
                validation["errors"].append("source_platform does not match route")
            if packet.get("target_platform") != route.get("target_platform"):
                validation["errors"].append("target_platform does not match route")
            validation["valid"] = not validation["errors"]
        return {
            "schema": "sc-cross-platform-validation-receipt/1.0",
            "release_version": RELEASE_VERSION,
            "packet_id": packet.get("packet_id"),
            "route_id": packet.get("route_id"),
            **validation,
            "validated_at": _iso(self.now_fn()),
            "packet_sha256": packet.get("sha256"),
        }

    def _save_packet_status(self, packet: dict[str, Any], status: str, detail: str = "") -> dict[str, Any]:
        if status not in PACKET_STATUSES:
            raise ValueError("Unsupported packet status.")
        updated = dict(packet)
        updated["status"] = status
        updated["status_detail"] = _safe_text(detail, 1000)
        updated["updated_at"] = _iso(self.now_fn())
        updated["sha256"] = _digest({k: v for k, v in updated.items() if k != "sha256"})
        _append(self.packets_path, updated)
        return updated

    def queue_packet(self, packet_id: str, request: dict[str, Any] | None = None) -> dict[str, Any]:
        packet = self._packet(packet_id)
        validation = self.validate_packet(packet_id)
        if not validation["valid"]:
            raise ValueError("Packet validation failed: " + "; ".join(validation["errors"]))
        request = request or {}
        previous_attempts = self.attempts(packet_id)
        attempt_number = len(previous_attempts) + 1
        if attempt_number > self.max_attempts:
            raise ValueError("Maximum delivery attempts reached.")
        now = self.now_fn()
        next_retry = now + timedelta(seconds=self.retry_delay_seconds * max(1, 2 ** (attempt_number - 1)))
        attempt = {
            "schema": ATTEMPT_SCHEMA,
            "release_version": RELEASE_VERSION,
            "attempt_id": _safe_id(f"attempt:{uuid4().hex[:18]}"),
            "packet_id": packet_id,
            "attempt_number": attempt_number,
            "status": "queued",
            "transport": _safe_text(request.get("transport") or "portable-json-packet", 80),
            "target_platform": packet.get("target_platform"),
            "created_at": _iso(now),
            "next_retry_at": _iso(next_retry),
            "remote_write_performed": False,
        }
        attempt["sha256"] = _digest({k: v for k, v in attempt.items() if k != "sha256"})
        _append(self.attempts_path, attempt)
        queue = {
            "schema": QUEUE_SCHEMA,
            "release_version": RELEASE_VERSION,
            "queue_id": _safe_id(f"queue:{packet_id}"),
            "packet_id": packet_id,
            "attempt_id": attempt["attempt_id"],
            "status": "queued",
            "reason": _safe_text(request.get("reason") or "awaiting external transport or receipt", 1000),
            "next_retry_at": attempt["next_retry_at"],
            "updated_at": _iso(now),
            "automatic_retry": False,
        }
        queue["sha256"] = _digest({k: v for k, v in queue.items() if k != "sha256"})
        _append(self.queue_path, queue)
        self._save_packet_status(packet, "queued", queue["reason"])
        return {"ok": True, "version": RELEASE_VERSION, "packet_id": packet_id, "attempt": attempt, "queue": queue}

    def dispatch_preview(self, packet_id: str) -> dict[str, Any]:
        packet = self._packet(packet_id)
        validation = self.validate_packet(packet_id)
        return {
            "ok": validation["valid"],
            "version": RELEASE_VERSION,
            "preview_only": True,
            "packet_id": packet_id,
            "route_id": packet.get("route_id"),
            "source_platform": packet.get("source_platform"),
            "target_platform": packet.get("target_platform"),
            "packet_sha256": packet.get("sha256"),
            "validation": validation,
            "external_delivery_enabled": False,
            "platform_core_registration_confirmed": False,
            "next_action": "Export or queue the typed packet, deliver it through an independently configured adapter or Platform Core, then record the returned receipt.",
        }

    def record_receipt(self, packet_id: str, request: dict[str, Any]) -> dict[str, Any]:
        packet = self._packet(packet_id)
        status = _safe_text(request.get("status"), 40).lower()
        if status not in RECEIPT_STATUSES:
            raise ValueError("Receipt status must be accepted, completed, rejected, or failed.")
        platform = _safe_text(request.get("platform") or packet.get("target_platform"), 80).lower()
        if platform != packet.get("target_platform"):
            raise ValueError("Receipt platform must match packet target_platform.")
        now = self.now_fn()
        receipt = {
            "schema": RECEIPT_SCHEMA,
            "release_version": RELEASE_VERSION,
            "receipt_id": _safe_id(request.get("receipt_id") or f"receipt:{uuid4().hex[:20]}"),
            "packet_id": packet_id,
            "workflow_id": packet.get("workflow_id"),
            "route_id": packet.get("route_id"),
            "platform": platform,
            "status": status,
            "external_record_id": _safe_id(request.get("external_record_id"), "") if request.get("external_record_id") else "",
            "external_version": _safe_text(request.get("external_version"), 100),
            "message": _safe_text(request.get("message"), 2000),
            "received_at": _iso(now),
            "packet_sha256": packet.get("sha256"),
            "remote_write_asserted_by_receipt": bool(request.get("remote_write_confirmed")),
            "verified_transport": False,
        }
        receipt["sha256"] = _digest({k: v for k, v in receipt.items() if k != "sha256"})
        _append(self.receipts_path, receipt)
        self._save_packet_status(packet, status, receipt["message"])
        if status == "failed":
            queue = {
                "schema": QUEUE_SCHEMA,
                "release_version": RELEASE_VERSION,
                "queue_id": _safe_id(f"queue:{packet_id}"),
                "packet_id": packet_id,
                "receipt_id": receipt["receipt_id"],
                "status": "failed",
                "reason": receipt["message"] or "external platform reported failure",
                "next_retry_at": _iso(now + timedelta(seconds=self.retry_delay_seconds)),
                "updated_at": _iso(now),
                "automatic_retry": False,
            }
            queue["sha256"] = _digest({k: v for k, v in queue.items() if k != "sha256"})
            _append(self.queue_path, queue)
        return receipt

    def retry_preview(self, packet_id: str) -> dict[str, Any]:
        packet = self._packet(packet_id)
        attempts = self.attempts(packet_id)
        return {
            "ok": packet.get("status") in {"failed", "rejected", "queued", "waiting_external_receipt"},
            "version": RELEASE_VERSION,
            "preview_only": True,
            "packet_id": packet_id,
            "current_status": packet.get("status"),
            "attempt_count": len(attempts),
            "attempts_remaining": max(0, self.max_attempts - len(attempts)),
            "automatic_retry": False,
        }

    def retry_failed(self, packet_id: str, request: dict[str, Any]) -> dict[str, Any]:
        if request.get("confirm") is not True:
            raise ValueError("confirm=true is required to queue a retry.")
        packet = self._packet(packet_id)
        if packet.get("status") not in {"failed", "rejected", "queued", "waiting_external_receipt"}:
            raise ValueError("Packet is not eligible for retry.")
        return self.queue_packet(packet_id, {"reason": request.get("reason") or "human-confirmed retry", "transport": request.get("transport")})

    def add_linkback(self, packet_id: str, request: dict[str, Any]) -> dict[str, Any]:
        packet = self._packet(packet_id)
        platform = _safe_text(request.get("platform") or packet.get("target_platform"), 80).lower()
        if platform not in PLATFORMS:
            raise ValueError("Unsupported linkback platform.")
        url = _safe_text(request.get("url"), 1200)
        record_id = _safe_id(request.get("record_id"), "") if request.get("record_id") else ""
        if not url and not record_id:
            raise ValueError("url or record_id is required.")
        row = {
            "schema": LINKBACK_SCHEMA,
            "release_version": RELEASE_VERSION,
            "linkback_id": _safe_id(request.get("linkback_id") or f"linkback:{uuid4().hex[:18]}"),
            "packet_id": packet_id,
            "platform": platform,
            "record_id": record_id,
            "url": url,
            "label": _safe_text(request.get("label") or "Related external record", 300),
            "created_at": _iso(self.now_fn()),
            "verified": False,
        }
        row["sha256"] = _digest({k: v for k, v in row.items() if k != "sha256"})
        _append(self.linkbacks_path, row)
        return row

    def ingest_incoming(self, request: dict[str, Any], actor_role: str = "system", actor_id: str = "external-platform") -> dict[str, Any]:
        packet = self.create_packet(request, actor_role, actor_id, direction="inbound")
        validation = self.validate_packet(packet["packet_id"])
        status = "accepted" if validation["valid"] else "rejected"
        receipt = self.record_receipt(packet["packet_id"], {
            "status": status,
            "platform": packet["target_platform"],
            "message": "Typed incoming packet accepted for local review." if status == "accepted" else "Typed incoming packet rejected by schema validation.",
            "remote_write_confirmed": False,
        })
        return {"ok": validation["valid"], "version": RELEASE_VERSION, "packet": self._packet(packet["packet_id"]), "validation": validation, "receipt": receipt}

    def export_packet(self, packet_id: str) -> bytes:
        packet = self._packet(packet_id)
        payload = {
            "schema": SCHEMA_VERSION,
            "release_version": RELEASE_VERSION,
            "exported_at": _iso(self.now_fn()),
            "packet": packet,
            "receipts": self.receipts(packet_id),
            "attempts": self.attempts(packet_id),
            "linkbacks": self.linkbacks(packet_id),
            "boundaries": [
                "This export is a portable typed packet and audit bundle, not proof of external ingestion.",
                "No remote write, account provisioning, or message-broker delivery is performed by export.",
                "External systems must validate the packet and return an explicit receipt.",
            ],
        }
        payload["sha256"] = _digest({k: v for k, v in payload.items() if k != "sha256"})
        return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")

    def public_summary(self) -> dict[str, Any]:
        counts = Counter()
        for route in self.route_rows:
            counts[str(route.get("source_platform"))] += 1
            counts[str(route.get("target_platform"))] += 1
        return {
            "ok": True,
            "version": RELEASE_VERSION,
            "schema": SCHEMA_VERSION,
            "routes": self.routes(public=True),
            "platforms": sorted(PLATFORMS),
            "platform_route_counts": dict(sorted(counts.items())),
            "methodology": "Public workflow metadata describes typed route contracts only. Packet payloads, receipts, retry records, external identifiers, and linkbacks remain private.",
            "governance": {
                "automatic_remote_write": False,
                "automatic_retry": False,
                "platform_core_required_for_persistent_orchestration": True,
                "external_delivery_claimed": False,
                "account_provisioning": False,
                "public_packet_payloads": False,
            },
        }

    def diagnostics(self, public: bool = False) -> dict[str, Any]:
        packets = self.packets()
        receipts = self.receipts()
        attempts = self.attempts()
        queue = self.queue()
        summary = {
            "route_count": len(self.route_rows),
            "platform_count": len(PLATFORMS),
            "packet_count": len(packets),
            "receipt_count": len(receipts),
            "attempt_count": len(attempts),
            "failed_queue_count": len([row for row in queue if row.get("status") == "failed"]),
            "queued_count": len([row for row in queue if row.get("status") == "queued"]),
            "packet_statuses": dict(Counter(str(row.get("status") or "unknown") for row in packets)),
        }
        result = {
            "ok": True,
            "version": RELEASE_VERSION,
            "schema": SCHEMA_VERSION,
            "summary": summary,
            "automatic_remote_write": False,
            "automatic_retry": False,
            "persistent_message_broker_included": False,
            "platform_core_orchestration_confirmed": False,
        }
        if public:
            result["summary"] = {"route_count": summary["route_count"], "platform_count": summary["platform_count"]}
            result["methodology"] = "Public diagnostics exclude packet payloads, workflow identifiers, receipts, external record IDs, queue details, and linkbacks."
        else:
            result["storage"] = {
                "packets": str(self.packets_path), "receipts": str(self.receipts_path), "attempts": str(self.attempts_path),
                "linkbacks": str(self.linkbacks_path), "queue": str(self.queue_path),
            }
        return result

    def control_center(self) -> dict[str, Any]:
        packet_rows = []
        for packet in self.packets()[:200]:
            packet_rows.append({k: v for k, v in packet.items() if k != "payload"} | {"payload_keys": sorted((packet.get("payload") or {}).keys())})
        return {
            "ok": True,
            "version": RELEASE_VERSION,
            "schema": SCHEMA_VERSION,
            "diagnostics": self.diagnostics(public=False),
            "routes": self.routes(public=False),
            "packets": packet_rows,
            "recent_receipts": self.receipts()[:200],
            "recent_attempts": self.attempts()[:200],
            "recovery_queue": self.queue()[:200],
            "recent_linkbacks": self.linkbacks()[:200],
            "policy": self.policy,
            "orchestration": {
                "preferred_layer": "Sustainable Catalyst Platform Core",
                "persistent_message_broker_included": False,
                "remote_delivery_adapter_included": False,
                "note": "Site Intelligence validates and records typed packets. A separately configured adapter or Platform Core must perform remote delivery and return receipts.",
            },
        }
