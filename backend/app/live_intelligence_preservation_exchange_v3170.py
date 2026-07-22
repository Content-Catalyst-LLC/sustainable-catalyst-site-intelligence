"""Preservation interoperability, external verification, and institutional exchange.

Site Intelligence v3.18.0 prepares standards-aligned, checksum-bound exchange
packages from approved institutional custody records. Exchange, verification,
and receipt records are append-only and human-governed. The workflow performs
no remote deposit, network verification, destination write, credential storage,
or source/archive mutation.
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

POLICY_SCHEMA_VERSION = "sc-site-intelligence-preservation-exchange-policy/1.0"
EXCHANGE_SCHEMA_VERSION = "sc-site-intelligence-preservation-exchange/1.0"
VERIFICATION_SCHEMA_VERSION = "sc-site-intelligence-external-verification/1.0"
EVENT_SCHEMA_VERSION = "sc-site-intelligence-preservation-exchange-event/1.0"
PACKAGE_SCHEMA_VERSION = "sc-site-intelligence-preservation-exchange-package/1.0"

EXCHANGE_PROFILES = (
    "bagit_manifest_1_0",
    "oais_sip_profile",
    "premis_event_profile",
    "ro_crate_metadata_1_1",
)
VERIFICATION_METHODS = (
    "manual_checksum",
    "independent_repository_review",
    "preservation_system_report",
)
VERIFICATION_RESULTS = ("verified", "partial", "rejected")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def preservation_exchange_policy() -> dict[str, Any]:
    return {
        "ok": True,
        "version": APP_VERSION,
        "schema": POLICY_SCHEMA_VERSION,
        "principle": "Exchange approved public-record custody packages through standards-aligned, checksum-verifiable manifests without granting remote systems write access.",
        "profiles": list(EXCHANGE_PROFILES),
        "verification_methods": list(VERIFICATION_METHODS),
        "standards_note": "Profiles are interoperability mappings and do not claim third-party certification or full standards conformance.",
        "boundaries": {
            "approved_custody_required": True,
            "separate_exchange_approval_required": True,
            "append_only_exchange_ledger": True,
            "external_verification_human_reported": True,
            "network_verification_performed": False,
            "remote_deposit_performed": False,
            "destination_write_performed": False,
            "archive_record_mutated": False,
            "archive_record_deleted": False,
            "credentials_stored": False,
            "recipient_identities_stored": False,
        },
        "routes": {
            "policy": "/public/live-intelligence/preservation-exchange/policy",
            "status": "/public/live-intelligence/preservation-exchange/status",
            "exchanges": "/public/live-intelligence/preservation-exchange/exchanges",
            "verifications": "/public/live-intelligence/preservation-exchange/verifications",
            "admin": "/admin/live-intelligence/preservation-exchange",
        },
    }


def _reject_exchange_payload(value: Any, path: str = "request") -> None:
    _reject_identity_payload(value, path)
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized = str(key).strip().lower().replace("-", "_")
            if any(part in normalized for part in (
                "email", "password", "secret", "token", "credential", "recipient",
                "webhook", "authorization", "cookie", "private_key", "access_key",
            )):
                raise ValueError(f"{path}.{key} is not accepted; identities and credentials are outside preservation exchange records.")
            _reject_exchange_payload(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_exchange_payload(child, f"{path}[{index}]")


def _sha256(value: Any, field: str) -> str:
    text = _safe_text(value, 128).lower()
    if not re.fullmatch(r"[a-f0-9]{64}", text):
        raise ValueError(f"{field} must be a lowercase SHA-256 checksum.")
    return text


def _exchange_package_digest(record: Mapping[str, Any]) -> str:
    excluded = {
        "exchange_sha256", "package_sha256", "status", "verified_by", "verified_at", "verification_reason",
        "approved_by", "approved_at", "approval_reason", "public_visible", "updated_at",
    }
    return _digest({key: value for key, value in record.items() if key not in excluded})


class LiveIntelligencePreservationExchangeCenter:
    def __init__(
        self,
        settings: Settings,
        *,
        custody_center: Any,
        now_fn: Callable[[], datetime] = _utc_now,
    ) -> None:
        self.settings = settings
        self.custody_center = custody_center
        self.now_fn = now_fn
        self.exchanges_path = _resolve(settings.live_intelligence_preservation_exchange_path)
        self.verifications_path = _resolve(settings.live_intelligence_preservation_exchange_verifications_path)
        self.events_path = _resolve(settings.live_intelligence_preservation_exchange_events_path)
        self.max_records = int(settings.live_intelligence_preservation_exchange_max_records)
        self.require_separation = bool(settings.live_intelligence_preservation_exchange_require_separation_of_duties)

    def _event(self, entity_id: str, event_type: str, actor: str, detail: Mapping[str, Any]) -> dict[str, Any]:
        event = {
            "schema": EVENT_SCHEMA_VERSION,
            "release_version": APP_VERSION,
            "event_id": f"preservation-exchange-event:{uuid4().hex[:20]}",
            "entity_id": entity_id,
            "event_type": event_type,
            "actor": actor,
            "occurred_at": _iso(self.now_fn()),
            "detail": deepcopy(dict(detail)),
            "network_verification_performed": False,
            "remote_deposit_performed": False,
            "destination_write_performed": False,
            "archive_record_mutated": False,
        }
        event["event_sha256"] = _digest({k: v for k, v in event.items() if k != "event_sha256"})
        _append(self.events_path, event)
        return event

    def exchanges(self, *, public: bool = False, limit: int = 1000) -> list[dict[str, Any]]:
        rows = _latest(self.exchanges_path, "exchange_id", self.max_records)
        if public:
            rows = [row for row in rows if row.get("status") == "approved" and row.get("public_visible") is True]
        rows.sort(key=lambda row: str(row.get("approved_at") or row.get("created_at") or ""), reverse=True)
        return rows[:max(1, min(int(limit), 2000))]

    def exchange(self, exchange_id: str, *, public: bool = False) -> dict[str, Any]:
        target = _safe_id(exchange_id, "preservation-exchange")
        for row in self.exchanges(public=public, limit=2000):
            if row.get("exchange_id") == target:
                return row
        raise KeyError(target)

    def verifications(self, *, public: bool = False, limit: int = 1000) -> list[dict[str, Any]]:
        rows = _latest(self.verifications_path, "verification_id", self.max_records)
        if public:
            rows = [row for row in rows if row.get("public_visible") is True]
        rows.sort(key=lambda row: str(row.get("verified_at") or row.get("created_at") or ""), reverse=True)
        return rows[:max(1, min(int(limit), 2000))]

    def verification(self, verification_id: str, *, public: bool = False) -> dict[str, Any]:
        target = _safe_id(verification_id, "external-verification")
        for row in self.verifications(public=public, limit=2000):
            if row.get("verification_id") == target:
                return row
        raise KeyError(target)

    def create_exchange(self, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_exchange_payload(request)
        actor = _actor(request.get("actor"))
        transfer_id = _safe_id(request.get("custody_transfer_id"), "custody-transfer")
        transfer = self.custody_center.custody_transfer(transfer_id)
        if transfer.get("status") not in {"approved", "manual_receipt_recorded"}:
            raise ValueError("An approved custody transfer is required before preservation exchange preparation.")
        profile = _safe_text(request.get("profile") or "bagit_manifest_1_0", 80).lower()
        if profile not in EXCHANGE_PROFILES:
            raise ValueError("Unsupported preservation exchange profile.")
        institution_reference = _safe_text(request.get("institution_reference") or transfer.get("institution_reference") or "institutional-exchange", 500)
        record_manifest = deepcopy(transfer.get("record_manifest") if isinstance(transfer.get("record_manifest"), list) else [])
        metadata = {
            "profile": profile,
            "custody_transfer_id": transfer_id,
            "custody_transfer_sha256": transfer.get("transfer_sha256"),
            "record_count": len(record_manifest),
            "institution_reference": institution_reference,
            "standards_alignment_only": True,
        }
        exchange_manifest = [
            {"path": "metadata/exchange.json", "sha256": _digest(metadata)},
            {"path": "metadata/custody-transfer.json", "sha256": str(transfer.get("transfer_sha256") or "")},
        ]
        for item in record_manifest:
            archive_id = _safe_text(item.get("archive_id"), 240) if isinstance(item, Mapping) else ""
            record_sha = str(item.get("record_sha256") or "") if isinstance(item, Mapping) else ""
            exchange_manifest.append({"path": f"records/{archive_id.replace(':', '_')}.json", "sha256": record_sha})
        exchange_id = _safe_id(request.get("exchange_id") or f"preservation-exchange:{uuid4().hex[:20]}", "preservation-exchange")
        now = self.now_fn()
        record = {
            "schema": EXCHANGE_SCHEMA_VERSION,
            "release_version": APP_VERSION,
            "exchange_id": exchange_id,
            "custody_transfer_id": transfer_id,
            "custody_transfer_sha256": transfer.get("transfer_sha256"),
            "custody_package_sha256": transfer.get("package_sha256"),
            "profile": profile,
            "institution_reference": institution_reference,
            "record_manifest": record_manifest,
            "record_count": len(record_manifest),
            "exchange_manifest": exchange_manifest,
            "exchange_manifest_sha256": _digest(exchange_manifest),
            "status": "prepared",
            "created_by": actor,
            "created_at": _iso(now),
            "updated_at": _iso(now),
            "public_visible": False,
            "manual_exchange_required": True,
            "external_verification_human_reported": True,
            "standards_alignment_only": True,
            "network_verification_performed": False,
            "remote_deposit_performed": False,
            "destination_write_performed": False,
            "archive_record_mutated": False,
            "archive_record_deleted": False,
        }
        record["package_sha256"] = _exchange_package_digest(record)
        record["exchange_sha256"] = _digest({k: v for k, v in record.items() if k != "exchange_sha256"})
        _append(self.exchanges_path, record)
        self._event(exchange_id, "preservation_exchange_prepared", actor, {"profile": profile, "record_count": len(record_manifest)})
        return {"ok": True, "version": APP_VERSION, "exchange": record}

    def verify_exchange(self, exchange_id: str, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_exchange_payload(request)
        actor = _actor(request.get("actor"))
        reason = _safe_text(request.get("reason"), 2000)
        if not reason:
            raise ValueError("A preservation exchange verification reason is required.")
        current = self.exchange(exchange_id)
        if current.get("status") != "prepared":
            raise ValueError("Only prepared preservation exchanges may be verified.")
        if _digest(current.get("exchange_manifest") or []) != current.get("exchange_manifest_sha256"):
            raise ValueError("Preservation exchange manifest checksum mismatch.")
        if _exchange_package_digest(current) != current.get("package_sha256"):
            raise ValueError("Preservation exchange package checksum mismatch.")
        transfer = self.custody_center.custody_transfer(str(current.get("custody_transfer_id") or ""))
        if transfer.get("transfer_sha256") != current.get("custody_transfer_sha256"):
            raise ValueError("Custody transfer changed after exchange preparation.")
        updated = deepcopy(current)
        updated.update({
            "status": "verified",
            "verified_by": actor,
            "verified_at": _iso(self.now_fn()),
            "verification_reason": reason,
            "updated_at": _iso(self.now_fn()),
        })
        updated["exchange_sha256"] = _digest({k: v for k, v in updated.items() if k != "exchange_sha256"})
        _append(self.exchanges_path, updated)
        self._event(exchange_id, "preservation_exchange_verified", actor, {"package_sha256": current.get("package_sha256")})
        return {"ok": True, "version": APP_VERSION, "exchange": updated}

    def approve_exchange(self, exchange_id: str, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_exchange_payload(request)
        approver = _actor(request.get("approved_by") or request.get("actor"))
        reason = _safe_text(request.get("reason"), 2000)
        if not reason:
            raise ValueError("A preservation exchange approval reason is required.")
        current = self.exchange(exchange_id)
        if current.get("status") != "verified":
            raise ValueError("Preservation exchange must be verified before approval.")
        if self.require_separation and approver in {current.get("created_by"), current.get("verified_by")}:
            raise ValueError("Preservation exchange approval requires separation of duties.")
        updated = deepcopy(current)
        updated.update({
            "status": "approved",
            "approved_by": approver,
            "approved_at": _iso(self.now_fn()),
            "approval_reason": reason,
            "public_visible": bool(request.get("public_visible", False)),
            "updated_at": _iso(self.now_fn()),
        })
        updated["exchange_sha256"] = _digest({k: v for k, v in updated.items() if k != "exchange_sha256"})
        _append(self.exchanges_path, updated)
        self._event(exchange_id, "preservation_exchange_approved", approver, {"public_visible": updated["public_visible"]})
        return {"ok": True, "version": APP_VERSION, "exchange": updated}

    def record_external_verification(self, exchange_id: str, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_exchange_payload(request)
        actor = _actor(request.get("actor"))
        exchange = self.exchange(exchange_id)
        if exchange.get("status") != "approved":
            raise ValueError("Only approved preservation exchanges may receive external verification records.")
        method = _safe_text(request.get("method") or "manual_checksum", 100).lower()
        result = _safe_text(request.get("result") or "verified", 40).lower()
        if method not in VERIFICATION_METHODS:
            raise ValueError("Unsupported external verification method.")
        if result not in VERIFICATION_RESULTS:
            raise ValueError("Unsupported external verification result.")
        reported_sha = _sha256(request.get("reported_package_sha256"), "reported_package_sha256")
        checksum_matches = reported_sha == exchange.get("package_sha256")
        if result == "verified" and not checksum_matches:
            raise ValueError("A verified receipt must report the approved exchange package checksum.")
        institution_reference = _safe_text(request.get("institution_reference"), 500)
        verification_reference = _safe_text(request.get("verification_reference"), 500)
        if not institution_reference or not verification_reference:
            raise ValueError("Institution and verification references are required.")
        verification_id = _safe_id(request.get("verification_id") or f"external-verification:{uuid4().hex[:20]}", "external-verification")
        record = {
            "schema": VERIFICATION_SCHEMA_VERSION,
            "release_version": APP_VERSION,
            "verification_id": verification_id,
            "exchange_id": exchange.get("exchange_id"),
            "exchange_package_sha256": exchange.get("package_sha256"),
            "reported_package_sha256": reported_sha,
            "checksum_matches": checksum_matches,
            "method": method,
            "result": result,
            "institution_reference": institution_reference,
            "verification_reference": verification_reference,
            "verification_note": _safe_text(request.get("verification_note") or "Externally reported preservation verification receipt.", 3000),
            "verified_by": actor,
            "verified_at": _iso(self.now_fn()),
            "public_visible": bool(request.get("public_visible", False)),
            "external_verification_human_reported": True,
            "network_verification_performed": False,
            "remote_deposit_performed": False,
            "destination_write_performed": False,
            "archive_record_mutated": False,
        }
        record["verification_sha256"] = _digest({k: v for k, v in record.items() if k != "verification_sha256"})
        _append(self.verifications_path, record)
        self._event(verification_id, "external_verification_recorded", actor, {"exchange_id": exchange_id, "result": result, "checksum_matches": checksum_matches})
        return {"ok": True, "version": APP_VERSION, "verification": record}

    def package_payload(self, exchange_id: str, format: str = "json", *, public: bool = False) -> tuple[str, str]:
        exchange = self.exchange(exchange_id, public=public)
        if exchange.get("status") != "approved":
            raise ValueError("Only approved preservation exchanges may be packaged.")
        verifications = [row for row in self.verifications(public=public, limit=2000) if row.get("exchange_id") == exchange_id]
        package = {
            "schema": PACKAGE_SCHEMA_VERSION,
            "release_version": APP_VERSION,
            "exchange": deepcopy(exchange),
            "external_verifications": deepcopy(verifications),
            "standards_alignment_only": True,
            "manual_exchange_required": True,
            "network_verification_performed": False,
            "remote_deposit_performed": False,
            "destination_write_performed": False,
        }
        package["package_sha256"] = _digest({k: v for k, v in package.items() if k != "package_sha256"})
        if format == "json":
            return "application/json", json.dumps(package, indent=2, sort_keys=True, ensure_ascii=False)
        if format != "markdown":
            raise ValueError("Unsupported preservation exchange package format.")
        lines = [
            f"# Preservation exchange {exchange.get('exchange_id')}", "",
            f"- Profile: `{exchange.get('profile')}`",
            f"- Custody transfer: `{exchange.get('custody_transfer_id')}`",
            f"- Records: `{exchange.get('record_count')}`",
            f"- Exchange package SHA-256: `{exchange.get('package_sha256')}`",
            f"- External verification receipts: `{len(verifications)}`", "",
            "This standards-aligned package requires manual exchange. It performs no network verification, remote deposit, archive mutation, or destination write.",
        ]
        return "text/markdown", "\n".join(lines) + "\n"

    def verification_payload(self, verification_id: str, format: str = "json", *, public: bool = False) -> tuple[str, str]:
        verification = self.verification(verification_id, public=public)
        package = {
            "schema": PACKAGE_SCHEMA_VERSION,
            "release_version": APP_VERSION,
            "verification": deepcopy(verification),
            "external_verification_human_reported": True,
            "network_verification_performed": False,
        }
        package["package_sha256"] = _digest({k: v for k, v in package.items() if k != "package_sha256"})
        if format == "json":
            return "application/json", json.dumps(package, indent=2, sort_keys=True, ensure_ascii=False)
        if format != "markdown":
            raise ValueError("Unsupported verification receipt format.")
        lines = [
            f"# External verification receipt {verification.get('verification_id')}", "",
            f"- Exchange: `{verification.get('exchange_id')}`",
            f"- Result: `{verification.get('result')}`",
            f"- Method: `{verification.get('method')}`",
            f"- Checksum matches: `{verification.get('checksum_matches')}`",
            f"- Verification SHA-256: `{verification.get('verification_sha256')}`", "",
            "This is a human-reported verification record. Site Intelligence performed no network verification or remote action.",
        ]
        return "text/markdown", "\n".join(lines) + "\n"

    def history(self, entity_id: str, limit: int = 200) -> list[dict[str, Any]]:
        target = _safe_text(entity_id, 240)
        rows = [row for row in _read_jsonl(self.events_path, self.max_records) if row.get("entity_id") == target]
        rows.sort(key=lambda row: str(row.get("occurred_at") or ""), reverse=True)
        return rows[:max(1, min(int(limit), 1000))]

    def status(self) -> dict[str, Any]:
        exchanges = self.exchanges(limit=2000)
        public_exchanges = self.exchanges(public=True, limit=2000)
        verifications = self.verifications(limit=2000)
        return {
            "ok": True,
            "version": APP_VERSION,
            "exchange_count": len(exchanges),
            "public_exchange_count": len(public_exchanges),
            "external_verification_count": len(verifications),
            "verified_receipt_count": sum(1 for row in verifications if row.get("result") == "verified" and row.get("checksum_matches") is True),
            "profile_counts": {profile: sum(1 for row in exchanges if row.get("profile") == profile) for profile in EXCHANGE_PROFILES},
            "append_only_exchange_ledger": True,
            "external_verification_human_reported": True,
            "network_verification_performed": False,
            "remote_deposit_performed": False,
            "destination_write_performed": False,
            "archive_record_mutated": False,
            "archive_record_deleted": False,
        }
