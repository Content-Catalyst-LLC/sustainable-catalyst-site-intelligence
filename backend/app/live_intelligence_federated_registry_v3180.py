"""Federated preservation registry, trust profiles, and cross-institution verification.

Site Intelligence v3.18.0 records public-safe institutional registry entries and
checksum-bound attestations against approved preservation exchange packages.
Registry approval and attestations are human-governed and append-only. Trust
profiles are evidence declarations, not certifications or endorsements. The
workflow performs no network verification, remote deposit, destination write,
credential storage, or archive/source mutation.
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
from .live_intelligence_preservation_exchange_v3170 import EXCHANGE_PROFILES, VERIFICATION_METHODS
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

POLICY_SCHEMA_VERSION = "sc-site-intelligence-federated-preservation-registry-policy/1.0"
INSTITUTION_SCHEMA_VERSION = "sc-site-intelligence-preservation-institution/1.0"
ATTESTATION_SCHEMA_VERSION = "sc-site-intelligence-federated-attestation/1.0"
EVENT_SCHEMA_VERSION = "sc-site-intelligence-federated-registry-event/1.0"
PACKAGE_SCHEMA_VERSION = "sc-site-intelligence-federated-registry-package/1.0"

INSTITUTION_TYPES = (
    "national_archive",
    "university_repository",
    "public_library",
    "research_institute",
    "civil_society_archive",
    "other_public_repository",
)
TRUST_PROFILES = (
    "declared",
    "policy_reviewed",
    "verified_exchange_partner",
)
ATTESTATION_RESULTS = ("verified", "partial", "rejected")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def federated_registry_policy() -> dict[str, Any]:
    return {
        "ok": True,
        "version": APP_VERSION,
        "schema": POLICY_SCHEMA_VERSION,
        "principle": "Publish evidence-linked institutional registry profiles and multi-party checksum attestations without treating registry presence as certification or granting remote write authority.",
        "institution_types": list(INSTITUTION_TYPES),
        "trust_profiles": list(TRUST_PROFILES),
        "exchange_profiles": list(EXCHANGE_PROFILES),
        "verification_methods": list(VERIFICATION_METHODS),
        "trust_note": "Trust profiles are scoped governance declarations supported by public references; they are not accreditation, certification, ranking, or endorsement.",
        "boundaries": {
            "approved_exchange_required": True,
            "approved_institution_required": True,
            "separate_registry_approval_required": True,
            "append_only_registry_ledger": True,
            "multi_party_consensus_unique_institutions": True,
            "external_attestations_human_reported": True,
            "network_verification_performed": False,
            "remote_deposit_performed": False,
            "destination_write_performed": False,
            "archive_record_mutated": False,
            "credentials_stored": False,
            "recipient_identities_stored": False,
            "certification_claimed": False,
        },
        "routes": {
            "policy": "/public/live-intelligence/preservation-registry/policy",
            "status": "/public/live-intelligence/preservation-registry/status",
            "institutions": "/public/live-intelligence/preservation-registry/institutions",
            "attestations": "/public/live-intelligence/preservation-registry/attestations",
            "consensus": "/public/live-intelligence/preservation-registry/exchanges/{exchange_id}/consensus",
            "admin": "/admin/live-intelligence/preservation-registry",
        },
    }


def _reject_registry_payload(value: Any, path: str = "request") -> None:
    _reject_identity_payload(value, path)
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized = str(key).strip().lower().replace("-", "_")
            if any(part in normalized for part in (
                "email", "password", "secret", "token", "credential", "recipient",
                "webhook", "authorization", "cookie", "private_key", "access_key",
                "contact_person", "personal_name", "phone",
            )):
                raise ValueError(f"{path}.{key} is not accepted; identities and credentials are outside the public preservation registry.")
            _reject_registry_payload(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_registry_payload(child, f"{path}[{index}]")


def _sha256(value: Any, field: str) -> str:
    text = _safe_text(value, 128).lower()
    if not re.fullmatch(r"[a-f0-9]{64}", text):
        raise ValueError(f"{field} must be a lowercase SHA-256 checksum.")
    return text


def _string_list(value: Any, *, allowed: tuple[str, ...], field: str, default: tuple[str, ...] = ()) -> list[str]:
    raw = value if isinstance(value, list) else list(default)
    values: list[str] = []
    for item in raw:
        normalized = _safe_text(item, 100).lower()
        if normalized not in allowed:
            raise ValueError(f"Unsupported {field}: {normalized or '<empty>'}.")
        if normalized not in values:
            values.append(normalized)
    if not values:
        raise ValueError(f"At least one {field} is required.")
    return values


def _institution_package_digest(record: Mapping[str, Any]) -> str:
    excluded = {
        "institution_sha256", "package_sha256", "status", "verified_by", "verified_at", "verification_reason",
        "approved_by", "approved_at", "approval_reason", "public_visible", "updated_at",
    }
    return _digest({key: value for key, value in record.items() if key not in excluded})


class LiveIntelligenceFederatedPreservationRegistry:
    def __init__(
        self,
        settings: Settings,
        *,
        exchange_center: Any,
        now_fn: Callable[[], datetime] = _utc_now,
    ) -> None:
        self.settings = settings
        self.exchange_center = exchange_center
        self.now_fn = now_fn
        self.institutions_path = _resolve(settings.live_intelligence_preservation_registry_institutions_path)
        self.attestations_path = _resolve(settings.live_intelligence_preservation_registry_attestations_path)
        self.events_path = _resolve(settings.live_intelligence_preservation_registry_events_path)
        self.max_records = int(settings.live_intelligence_preservation_registry_max_records)
        self.require_separation = bool(settings.live_intelligence_preservation_registry_require_separation_of_duties)
        self.consensus_threshold = int(settings.live_intelligence_preservation_registry_consensus_threshold)

    def _event(self, entity_id: str, event_type: str, actor: str, detail: Mapping[str, Any]) -> dict[str, Any]:
        event = {
            "schema": EVENT_SCHEMA_VERSION,
            "release_version": APP_VERSION,
            "event_id": f"preservation-registry-event:{uuid4().hex[:20]}",
            "entity_id": entity_id,
            "event_type": event_type,
            "actor": actor,
            "occurred_at": _iso(self.now_fn()),
            "detail": deepcopy(dict(detail)),
            "network_verification_performed": False,
            "remote_deposit_performed": False,
            "destination_write_performed": False,
            "archive_record_mutated": False,
            "certification_claimed": False,
        }
        event["event_sha256"] = _digest({k: v for k, v in event.items() if k != "event_sha256"})
        _append(self.events_path, event)
        return event

    def institutions(self, *, public: bool = False, limit: int = 1000) -> list[dict[str, Any]]:
        rows = _latest(self.institutions_path, "institution_id", self.max_records)
        if public:
            rows = [row for row in rows if row.get("status") == "approved" and row.get("public_visible") is True]
        rows.sort(key=lambda row: (str(row.get("institution_name") or "").lower(), str(row.get("approved_at") or row.get("created_at") or "")))
        return rows[:max(1, min(int(limit), 2000))]

    def institution(self, institution_id: str, *, public: bool = False) -> dict[str, Any]:
        target = _safe_id(institution_id, "preservation-institution")
        for row in self.institutions(public=public, limit=2000):
            if row.get("institution_id") == target:
                return row
        raise KeyError(target)

    def attestations(self, *, public: bool = False, limit: int = 1000) -> list[dict[str, Any]]:
        rows = _latest(self.attestations_path, "attestation_id", self.max_records)
        if public:
            public_ids = {row.get("institution_id") for row in self.institutions(public=True, limit=2000)}
            rows = [row for row in rows if row.get("public_visible") is True and row.get("institution_id") in public_ids]
        rows.sort(key=lambda row: str(row.get("attested_at") or row.get("created_at") or ""), reverse=True)
        return rows[:max(1, min(int(limit), 2000))]

    def attestation(self, attestation_id: str, *, public: bool = False) -> dict[str, Any]:
        target = _safe_id(attestation_id, "federated-attestation")
        for row in self.attestations(public=public, limit=2000):
            if row.get("attestation_id") == target:
                return row
        raise KeyError(target)

    def create_institution(self, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_registry_payload(request)
        actor = _actor(request.get("actor"))
        institution_name = _safe_text(request.get("institution_name"), 300)
        jurisdiction = _safe_text(request.get("jurisdiction"), 160)
        repository_reference = _safe_text(request.get("repository_reference"), 500)
        public_policy_reference = _safe_text(request.get("public_policy_reference"), 500)
        if not all((institution_name, jurisdiction, repository_reference, public_policy_reference)):
            raise ValueError("Institution name, jurisdiction, repository reference, and public policy reference are required.")
        institution_type = _safe_text(request.get("institution_type") or "other_public_repository", 80).lower()
        if institution_type not in INSTITUTION_TYPES:
            raise ValueError("Unsupported preservation institution type.")
        trust_profile = _safe_text(request.get("trust_profile") or "declared", 80).lower()
        if trust_profile not in TRUST_PROFILES:
            raise ValueError("Unsupported preservation trust profile.")
        profiles = _string_list(request.get("supported_profiles"), allowed=EXCHANGE_PROFILES, field="exchange profile", default=("bagit_manifest_1_0",))
        methods = _string_list(request.get("verification_methods"), allowed=VERIFICATION_METHODS, field="verification method", default=("manual_checksum",))
        institution_id = _safe_id(request.get("institution_id") or f"preservation-institution:{uuid4().hex[:20]}", "preservation-institution")
        if any(row.get("institution_id") == institution_id for row in self.institutions(limit=2000)):
            raise ValueError("Preservation institution ID already exists.")
        now = self.now_fn()
        record = {
            "schema": INSTITUTION_SCHEMA_VERSION,
            "release_version": APP_VERSION,
            "institution_id": institution_id,
            "institution_name": institution_name,
            "jurisdiction": jurisdiction,
            "institution_type": institution_type,
            "repository_reference": repository_reference,
            "public_policy_reference": public_policy_reference,
            "trust_profile": trust_profile,
            "trust_basis_note": _safe_text(request.get("trust_basis_note") or "Publicly referenced preservation and verification capabilities.", 3000),
            "supported_profiles": profiles,
            "verification_methods": methods,
            "status": "prepared",
            "created_by": actor,
            "created_at": _iso(now),
            "updated_at": _iso(now),
            "public_visible": False,
            "trust_declaration_human_reviewed": False,
            "certification_claimed": False,
            "network_verification_performed": False,
            "remote_deposit_performed": False,
            "destination_write_performed": False,
            "credentials_stored": False,
        }
        record["package_sha256"] = _institution_package_digest(record)
        record["institution_sha256"] = _digest({k: v for k, v in record.items() if k != "institution_sha256"})
        _append(self.institutions_path, record)
        self._event(institution_id, "preservation_institution_prepared", actor, {"trust_profile": trust_profile, "institution_type": institution_type})
        return {"ok": True, "version": APP_VERSION, "institution": record}

    def verify_institution(self, institution_id: str, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_registry_payload(request)
        actor = _actor(request.get("actor"))
        reason = _safe_text(request.get("reason"), 2000)
        evidence_reference = _safe_text(request.get("evidence_reference"), 500)
        if not reason or not evidence_reference:
            raise ValueError("Verification reason and public evidence reference are required.")
        current = self.institution(institution_id)
        if current.get("status") != "prepared":
            raise ValueError("Only prepared preservation institutions may be verified.")
        if _institution_package_digest(current) != current.get("package_sha256"):
            raise ValueError("Preservation institution package checksum mismatch.")
        updated = deepcopy(current)
        updated.update({
            "status": "verified",
            "verified_by": actor,
            "verified_at": _iso(self.now_fn()),
            "verification_reason": reason,
            "evidence_reference": evidence_reference,
            "trust_declaration_human_reviewed": True,
            "updated_at": _iso(self.now_fn()),
        })
        updated["institution_sha256"] = _digest({k: v for k, v in updated.items() if k != "institution_sha256"})
        _append(self.institutions_path, updated)
        self._event(institution_id, "preservation_institution_verified", actor, {"evidence_reference": evidence_reference})
        return {"ok": True, "version": APP_VERSION, "institution": updated}

    def approve_institution(self, institution_id: str, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_registry_payload(request)
        approver = _actor(request.get("approved_by") or request.get("actor"))
        reason = _safe_text(request.get("reason"), 2000)
        if not reason:
            raise ValueError("A preservation institution approval reason is required.")
        current = self.institution(institution_id)
        if current.get("status") != "verified":
            raise ValueError("Preservation institution must be verified before approval.")
        if self.require_separation and approver in {current.get("created_by"), current.get("verified_by")}:
            raise ValueError("Preservation institution approval requires separation of duties.")
        updated = deepcopy(current)
        updated.update({
            "status": "approved",
            "approved_by": approver,
            "approved_at": _iso(self.now_fn()),
            "approval_reason": reason,
            "public_visible": bool(request.get("public_visible", False)),
            "updated_at": _iso(self.now_fn()),
        })
        updated["institution_sha256"] = _digest({k: v for k, v in updated.items() if k != "institution_sha256"})
        _append(self.institutions_path, updated)
        self._event(institution_id, "preservation_institution_approved", approver, {"public_visible": updated["public_visible"]})
        return {"ok": True, "version": APP_VERSION, "institution": updated}

    def record_attestation(self, exchange_id: str, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_registry_payload(request)
        actor = _actor(request.get("actor"))
        exchange = self.exchange_center.exchange(_safe_id(exchange_id, "preservation-exchange"))
        if exchange.get("status") != "approved":
            raise ValueError("Only approved preservation exchanges may receive federated attestations.")
        institution_id = _safe_id(request.get("institution_id"), "preservation-institution")
        institution = self.institution(institution_id)
        if institution.get("status") != "approved":
            raise ValueError("Only approved preservation institutions may attest to an exchange.")
        method = _safe_text(request.get("method") or "manual_checksum", 100).lower()
        if method not in VERIFICATION_METHODS or method not in set(institution.get("verification_methods") or []):
            raise ValueError("Attestation method is not approved for this institution.")
        result = _safe_text(request.get("result") or "verified", 40).lower()
        if result not in ATTESTATION_RESULTS:
            raise ValueError("Unsupported federated attestation result.")
        reported_sha = _sha256(request.get("reported_package_sha256"), "reported_package_sha256")
        checksum_matches = reported_sha == exchange.get("package_sha256")
        if result == "verified" and not checksum_matches:
            raise ValueError("A verified attestation must report the approved exchange package checksum.")
        evidence_reference = _safe_text(request.get("evidence_reference"), 500)
        if not evidence_reference:
            raise ValueError("A public-safe attestation evidence reference is required.")
        attestation_id = _safe_id(request.get("attestation_id") or f"federated-attestation:{uuid4().hex[:20]}", "federated-attestation")
        record = {
            "schema": ATTESTATION_SCHEMA_VERSION,
            "release_version": APP_VERSION,
            "attestation_id": attestation_id,
            "exchange_id": exchange.get("exchange_id"),
            "exchange_package_sha256": exchange.get("package_sha256"),
            "reported_package_sha256": reported_sha,
            "checksum_matches": checksum_matches,
            "institution_id": institution_id,
            "institution_sha256": institution.get("institution_sha256"),
            "institution_name": institution.get("institution_name"),
            "trust_profile": institution.get("trust_profile"),
            "method": method,
            "result": result,
            "evidence_reference": evidence_reference,
            "attestation_note": _safe_text(request.get("attestation_note") or "Human-reported cross-institution checksum attestation.", 3000),
            "attested_by": actor,
            "attested_at": _iso(self.now_fn()),
            "public_visible": bool(request.get("public_visible", False)) and institution.get("public_visible") is True and exchange.get("public_visible") is True,
            "external_attestation_human_reported": True,
            "network_verification_performed": False,
            "remote_deposit_performed": False,
            "destination_write_performed": False,
            "archive_record_mutated": False,
            "certification_claimed": False,
        }
        record["attestation_sha256"] = _digest({k: v for k, v in record.items() if k != "attestation_sha256"})
        _append(self.attestations_path, record)
        self._event(attestation_id, "federated_attestation_recorded", actor, {"exchange_id": exchange_id, "institution_id": institution_id, "result": result, "checksum_matches": checksum_matches})
        return {"ok": True, "version": APP_VERSION, "attestation": record}

    def consensus(self, exchange_id: str, *, public: bool = False) -> dict[str, Any]:
        exchange = self.exchange_center.exchange(_safe_id(exchange_id, "preservation-exchange"), public=public)
        rows = [row for row in self.attestations(public=public, limit=2000) if row.get("exchange_id") == exchange.get("exchange_id")]
        latest_by_institution: dict[str, dict[str, Any]] = {}
        for row in rows:
            institution_id = str(row.get("institution_id") or "")
            if not institution_id:
                continue
            previous = latest_by_institution.get(institution_id)
            if previous is None or str(row.get("attested_at") or "") >= str(previous.get("attested_at") or ""):
                latest_by_institution[institution_id] = row
        accepted = [
            row for row in latest_by_institution.values()
            if row.get("result") == "verified" and row.get("checksum_matches") is True
            and row.get("reported_package_sha256") == exchange.get("package_sha256")
        ]
        unique_institutions = sorted({str(row.get("institution_id")) for row in accepted})
        methods = sorted({str(row.get("method")) for row in accepted})
        count = len(unique_institutions)
        status = "verified_consensus" if count >= self.consensus_threshold else ("partial_consensus" if count else "unverified")
        consensus = {
            "schema": "sc-site-intelligence-federated-consensus/1.0",
            "release_version": APP_VERSION,
            "exchange_id": exchange.get("exchange_id"),
            "exchange_package_sha256": exchange.get("package_sha256"),
            "consensus_status": status,
            "consensus_threshold": self.consensus_threshold,
            "verified_institution_count": count,
            "verified_institution_ids": unique_institutions,
            "verification_methods": methods,
            "attestation_count": len(rows),
            "latest_attestations": deepcopy(sorted(latest_by_institution.values(), key=lambda row: str(row.get("institution_id") or ""))),
            "multi_party_consensus_unique_institutions": True,
            "external_attestations_human_reported": True,
            "network_verification_performed": False,
            "remote_deposit_performed": False,
            "destination_write_performed": False,
            "certification_claimed": False,
        }
        consensus["consensus_sha256"] = _digest({k: v for k, v in consensus.items() if k != "consensus_sha256"})
        return consensus

    def institution_package_payload(self, institution_id: str, format: str = "json", *, public: bool = False) -> tuple[str, str]:
        institution = self.institution(institution_id, public=public)
        package = {
            "schema": PACKAGE_SCHEMA_VERSION,
            "release_version": APP_VERSION,
            "institution": deepcopy(institution),
            "attestations": [row for row in self.attestations(public=public, limit=2000) if row.get("institution_id") == institution_id],
            "certification_claimed": False,
            "network_verification_performed": False,
            "destination_write_performed": False,
        }
        package["package_sha256"] = _digest({k: v for k, v in package.items() if k != "package_sha256"})
        return self._render_package(package, format, title=f"Preservation institution {institution_id}")

    def consensus_package_payload(self, exchange_id: str, format: str = "json", *, public: bool = False) -> tuple[str, str]:
        consensus = self.consensus(exchange_id, public=public)
        package = {
            "schema": PACKAGE_SCHEMA_VERSION,
            "release_version": APP_VERSION,
            "consensus": consensus,
            "certification_claimed": False,
            "network_verification_performed": False,
            "remote_deposit_performed": False,
        }
        package["package_sha256"] = _digest({k: v for k, v in package.items() if k != "package_sha256"})
        return self._render_package(package, format, title=f"Federated preservation consensus {exchange_id}")

    def _render_package(self, package: Mapping[str, Any], format: str, *, title: str) -> tuple[str, str]:
        if format == "json":
            return "application/json", json.dumps(package, indent=2, sort_keys=True, ensure_ascii=False)
        if format != "markdown":
            raise ValueError("Unsupported federated registry package format.")
        lines = [
            f"# {title}", "",
            f"- Release version: `{APP_VERSION}`",
            f"- Package SHA-256: `{package.get('package_sha256')}`", "",
            "This is a human-governed, public-safe registry package. It is not a certification or endorsement and performs no network verification, remote deposit, archive mutation, or destination write.",
        ]
        return "text/markdown", "\n".join(lines) + "\n"

    def history(self, entity_id: str, limit: int = 200) -> list[dict[str, Any]]:
        target = _safe_text(entity_id, 240)
        rows = [row for row in _read_jsonl(self.events_path, self.max_records) if row.get("entity_id") == target]
        rows.sort(key=lambda row: str(row.get("occurred_at") or ""), reverse=True)
        return rows[:max(1, min(int(limit), 1000))]

    def status(self) -> dict[str, Any]:
        institutions = self.institutions(limit=2000)
        public_institutions = self.institutions(public=True, limit=2000)
        attestations = self.attestations(limit=2000)
        public_attestations = self.attestations(public=True, limit=2000)
        exchange_ids = sorted({str(row.get("exchange_id")) for row in public_attestations if row.get("exchange_id")})
        consensus_count = 0
        for exchange_id in exchange_ids:
            try:
                if self.consensus(exchange_id, public=True).get("consensus_status") == "verified_consensus":
                    consensus_count += 1
            except KeyError:
                continue
        return {
            "ok": True,
            "version": APP_VERSION,
            "institution_count": len(institutions),
            "public_institution_count": len(public_institutions),
            "attestation_count": len(attestations),
            "public_attestation_count": len(public_attestations),
            "verified_consensus_count": consensus_count,
            "consensus_threshold": self.consensus_threshold,
            "trust_profile_counts": {profile: sum(1 for row in public_institutions if row.get("trust_profile") == profile) for profile in TRUST_PROFILES},
            "append_only_registry_ledger": True,
            "multi_party_consensus_unique_institutions": True,
            "external_attestations_human_reported": True,
            "network_verification_performed": False,
            "remote_deposit_performed": False,
            "destination_write_performed": False,
            "archive_record_mutated": False,
            "certification_claimed": False,
        }
