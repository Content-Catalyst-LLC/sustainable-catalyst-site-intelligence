"""Registry governance, challenges, revocation, and appeals.

Site Intelligence v3.19.0 adds an append-only governance layer above the
federated preservation registry. Public-safe challenges can be reviewed and
resolved through separated human roles. Institutional suspension, revocation,
trust-profile change, or reinstatement appends a new registry state; it never
deletes prior institutions, attestations, exchanges, evidence, or history.
The workflow performs no network verification, remote write, credential
storage, certification, or automated enforcement outside Site Intelligence.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
from typing import Any, Callable, Mapping
from uuid import uuid4

from .config import Settings
from .version import APP_VERSION
from .live_intelligence_federated_registry_v3180 import (
    TRUST_PROFILES,
    _institution_package_digest,
)
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

POLICY_SCHEMA_VERSION = "sc-site-intelligence-registry-governance-policy/1.0"
CHALLENGE_SCHEMA_VERSION = "sc-site-intelligence-registry-challenge/1.0"
APPEAL_SCHEMA_VERSION = "sc-site-intelligence-registry-appeal/1.0"
EVENT_SCHEMA_VERSION = "sc-site-intelligence-registry-governance-event/1.0"
PACKAGE_SCHEMA_VERSION = "sc-site-intelligence-registry-governance-package/1.0"

CHALLENGE_TYPES = (
    "evidence_gap",
    "policy_change",
    "checksum_dispute",
    "status_accuracy",
    "governance_concern",
)
RESOLUTION_ACTIONS = (
    "no_action",
    "update_trust_profile",
    "suspend",
    "revoke",
)
APPEAL_OUTCOMES = (
    "uphold",
    "reinstate",
    "modify_trust_profile",
)
ACTIVE_INSTITUTION_STATUSES = ("approved", "suspended", "revoked")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def registry_governance_policy() -> dict[str, Any]:
    return {
        "ok": True,
        "version": APP_VERSION,
        "schema": POLICY_SCHEMA_VERSION,
        "principle": "Resolve evidence-based registry challenges through separated human review while preserving every prior institution state, attestation, and decision.",
        "challenge_types": list(CHALLENGE_TYPES),
        "resolution_actions": list(RESOLUTION_ACTIONS),
        "appeal_outcomes": list(APPEAL_OUTCOMES),
        "boundaries": {
            "append_only_governance_ledger": True,
            "separate_review_and_approval_required": True,
            "original_registry_records_retained": True,
            "prior_attestations_retained": True,
            "inactive_institutions_excluded_from_current_consensus": True,
            "appeal_required_for_reinstatement": True,
            "public_records_require_explicit_visibility": True,
            "automatic_suspension_performed": False,
            "automatic_revocation_performed": False,
            "network_verification_performed": False,
            "remote_write_performed": False,
            "archive_or_evidence_mutated": False,
            "credentials_stored": False,
            "personal_contact_data_stored": False,
            "certification_claimed": False,
        },
        "routes": {
            "policy": "/public/live-intelligence/registry-governance/policy",
            "status": "/public/live-intelligence/registry-governance/status",
            "challenges": "/public/live-intelligence/registry-governance/challenges",
            "appeals": "/public/live-intelligence/registry-governance/appeals",
            "institution": "/public/live-intelligence/registry-governance/institutions/{institution_id}",
            "admin": "/admin/live-intelligence/registry-governance",
        },
    }


def _reject_governance_payload(value: Any, path: str = "request") -> None:
    _reject_identity_payload(value, path)
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized = str(key).strip().lower().replace("-", "_")
            if any(part in normalized for part in (
                "email", "password", "secret", "token", "credential", "recipient",
                "webhook", "authorization", "cookie", "private_key", "access_key",
                "contact_person", "personal_name", "phone", "ip_address",
            )):
                raise ValueError(f"{path}.{key} is not accepted; identities and credentials are outside registry governance.")
            _reject_governance_payload(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_governance_payload(child, f"{path}[{index}]")


def _record_digest(record: Mapping[str, Any], checksum_field: str) -> str:
    return _digest({key: value for key, value in record.items() if key != checksum_field})


def _public_projection(record: Mapping[str, Any]) -> dict[str, Any]:
    excluded = {
        "created_by", "reviewed_by", "approved_by", "submitted_by",
        "review_note", "approval_note", "internal_note", "appeal_note",
    }
    return {key: deepcopy(value) for key, value in record.items() if key not in excluded}


class LiveIntelligenceRegistryGovernanceCenter:
    def __init__(
        self,
        settings: Settings,
        *,
        registry_center: Any,
        now_fn: Callable[[], datetime] = _utc_now,
    ) -> None:
        self.settings = settings
        self.registry_center = registry_center
        self.now_fn = now_fn
        self.challenges_path = _resolve(settings.live_intelligence_registry_governance_challenges_path)
        self.appeals_path = _resolve(settings.live_intelligence_registry_governance_appeals_path)
        self.events_path = _resolve(settings.live_intelligence_registry_governance_events_path)
        self.max_records = int(settings.live_intelligence_registry_governance_max_records)
        self.require_separation = bool(settings.live_intelligence_registry_governance_require_separation_of_duties)

    def _event(self, entity_id: str, event_type: str, actor: str, detail: Mapping[str, Any]) -> dict[str, Any]:
        event = {
            "schema": EVENT_SCHEMA_VERSION,
            "release_version": APP_VERSION,
            "event_id": f"registry-governance-event:{uuid4().hex[:20]}",
            "entity_id": entity_id,
            "event_type": event_type,
            "actor": actor,
            "occurred_at": _iso(self.now_fn()),
            "detail": deepcopy(dict(detail)),
            "append_only_governance_ledger": True,
            "automatic_enforcement_performed": False,
            "network_verification_performed": False,
            "remote_write_performed": False,
            "archive_or_evidence_mutated": False,
            "certification_claimed": False,
        }
        event["event_sha256"] = _record_digest(event, "event_sha256")
        _append(self.events_path, event)
        return event

    def challenges(self, *, public: bool = False, limit: int = 1000) -> list[dict[str, Any]]:
        rows = _latest(self.challenges_path, "challenge_id", self.max_records)
        if public:
            rows = [
                _public_projection(row) for row in rows
                if row.get("status") == "resolved" and row.get("public_visible") is True
            ]
        rows.sort(key=lambda row: str(row.get("resolved_at") or row.get("created_at") or ""), reverse=True)
        return rows[:max(1, min(int(limit), 2000))]

    def challenge(self, challenge_id: str, *, public: bool = False) -> dict[str, Any]:
        target = _safe_id(challenge_id, "registry-challenge")
        for row in self.challenges(public=public, limit=2000):
            if row.get("challenge_id") == target:
                return row
        raise KeyError(target)

    def appeals(self, *, public: bool = False, limit: int = 1000) -> list[dict[str, Any]]:
        rows = _latest(self.appeals_path, "appeal_id", self.max_records)
        if public:
            public_challenges = {row.get("challenge_id") for row in self.challenges(public=True, limit=2000)}
            rows = [
                _public_projection(row) for row in rows
                if row.get("status") == "resolved" and row.get("public_visible") is True
                and row.get("challenge_id") in public_challenges
            ]
        rows.sort(key=lambda row: str(row.get("resolved_at") or row.get("created_at") or ""), reverse=True)
        return rows[:max(1, min(int(limit), 2000))]

    def appeal(self, appeal_id: str, *, public: bool = False) -> dict[str, Any]:
        target = _safe_id(appeal_id, "registry-appeal")
        for row in self.appeals(public=public, limit=2000):
            if row.get("appeal_id") == target:
                return row
        raise KeyError(target)

    def create_challenge(self, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_governance_payload(request)
        actor = _actor(request.get("actor"))
        institution_id = _safe_id(request.get("institution_id"), "preservation-institution")
        institution = self.registry_center.institution(institution_id)
        if institution.get("status") not in ACTIVE_INSTITUTION_STATUSES:
            raise ValueError("Only approved, suspended, or revoked institutions may receive governance challenges.")
        challenge_type = _safe_text(request.get("challenge_type"), 80).lower()
        if challenge_type not in CHALLENGE_TYPES:
            raise ValueError("Unsupported registry challenge type.")
        summary = _safe_text(request.get("summary"), 500)
        evidence_reference = _safe_text(request.get("evidence_reference"), 500)
        rationale = _safe_text(request.get("rationale"), 4000)
        if not all((summary, evidence_reference, rationale)):
            raise ValueError("Challenge summary, rationale, and public-safe evidence reference are required.")
        challenge_id = _safe_id(request.get("challenge_id") or f"registry-challenge:{uuid4().hex[:20]}", "registry-challenge")
        if any(row.get("challenge_id") == challenge_id for row in self.challenges(limit=2000)):
            raise ValueError("Registry challenge ID already exists.")
        now = _iso(self.now_fn())
        record = {
            "schema": CHALLENGE_SCHEMA_VERSION,
            "release_version": APP_VERSION,
            "challenge_id": challenge_id,
            "institution_id": institution_id,
            "institution_name": institution.get("institution_name"),
            "challenged_institution_sha256": institution.get("institution_sha256"),
            "challenge_type": challenge_type,
            "summary": summary,
            "rationale": rationale,
            "evidence_reference": evidence_reference,
            "status": "submitted",
            "created_by": actor,
            "created_at": now,
            "updated_at": now,
            "public_visible_requested": bool(request.get("public_visible", False)),
            "public_visible": False,
            "prior_registry_records_retained": True,
            "prior_attestations_retained": True,
            "automatic_enforcement_performed": False,
            "network_verification_performed": False,
            "remote_write_performed": False,
            "archive_or_evidence_mutated": False,
            "certification_claimed": False,
        }
        record["challenge_sha256"] = _record_digest(record, "challenge_sha256")
        _append(self.challenges_path, record)
        self._event(challenge_id, "registry_challenge_submitted", actor, {"institution_id": institution_id, "challenge_type": challenge_type})
        return {"ok": True, "version": APP_VERSION, "challenge": record}

    def review_challenge(self, challenge_id: str, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_governance_payload(request)
        actor = _actor(request.get("actor"))
        reason = _safe_text(request.get("reason"), 4000)
        evidence_reference = _safe_text(request.get("evidence_reference"), 500)
        recommended_action = _safe_text(request.get("recommended_action"), 80).lower()
        if not reason or not evidence_reference:
            raise ValueError("Challenge review reason and evidence reference are required.")
        if recommended_action not in RESOLUTION_ACTIONS:
            raise ValueError("Unsupported registry challenge recommendation.")
        current = self.challenge(challenge_id)
        if current.get("status") != "submitted":
            raise ValueError("Only submitted registry challenges may be reviewed.")
        if self.require_separation and actor == current.get("created_by"):
            raise ValueError("Registry challenge review requires separation of duties.")
        updated = deepcopy(current)
        updated.update({
            "status": "reviewed",
            "reviewed_by": actor,
            "reviewed_at": _iso(self.now_fn()),
            "review_reason": reason,
            "review_evidence_reference": evidence_reference,
            "recommended_action": recommended_action,
            "recommended_trust_profile": _safe_text(request.get("recommended_trust_profile"), 80).lower() or None,
            "updated_at": _iso(self.now_fn()),
        })
        if recommended_action == "update_trust_profile" and updated["recommended_trust_profile"] not in TRUST_PROFILES:
            raise ValueError("A supported recommended trust profile is required.")
        updated["challenge_sha256"] = _record_digest(updated, "challenge_sha256")
        _append(self.challenges_path, updated)
        self._event(challenge_id, "registry_challenge_reviewed", actor, {"recommended_action": recommended_action})
        return {"ok": True, "version": APP_VERSION, "challenge": updated}

    def approve_challenge(self, challenge_id: str, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_governance_payload(request)
        actor = _actor(request.get("approved_by") or request.get("actor"))
        reason = _safe_text(request.get("reason"), 4000)
        action = _safe_text(request.get("action"), 80).lower()
        if not reason:
            raise ValueError("Challenge approval reason is required.")
        if action not in RESOLUTION_ACTIONS:
            raise ValueError("Unsupported registry challenge resolution action.")
        current = self.challenge(challenge_id)
        if current.get("status") != "reviewed":
            raise ValueError("Registry challenge must be reviewed before approval.")
        if self.require_separation and actor in {current.get("created_by"), current.get("reviewed_by")}:
            raise ValueError("Registry challenge approval requires separation of duties.")
        if action != current.get("recommended_action") and not _safe_text(request.get("variance_reason"), 2000):
            raise ValueError("A variance reason is required when approval differs from the review recommendation.")
        institution = self.registry_center.institution(str(current.get("institution_id")))
        new_trust_profile = _safe_text(request.get("trust_profile") or current.get("recommended_trust_profile"), 80).lower() or None
        if action == "update_trust_profile" and new_trust_profile not in TRUST_PROFILES:
            raise ValueError("A supported trust profile is required for a trust-profile update.")
        governance_status = institution.get("status")
        if action == "suspend":
            governance_status = "suspended"
        elif action == "revoke":
            governance_status = "revoked"
        elif action in {"no_action", "update_trust_profile"}:
            governance_status = "approved"
        institution_update = deepcopy(institution)
        institution_update.update({
            "status": governance_status,
            "governance_status": governance_status,
            "governance_challenge_id": current.get("challenge_id"),
            "governance_action": action,
            "governance_reason": reason,
            "governance_approved_at": _iso(self.now_fn()),
            "prior_institution_sha256": institution.get("institution_sha256"),
            "updated_at": _iso(self.now_fn()),
        })
        if action == "update_trust_profile":
            institution_update["trust_profile"] = new_trust_profile
            institution_update["package_sha256"] = _institution_package_digest(institution_update)
        institution_update["institution_sha256"] = _record_digest(institution_update, "institution_sha256")
        _append(self.registry_center.institutions_path, institution_update)

        updated = deepcopy(current)
        updated.update({
            "status": "resolved",
            "approved_by": actor,
            "resolved_at": _iso(self.now_fn()),
            "approval_reason": reason,
            "resolution_action": action,
            "resolved_trust_profile": new_trust_profile if action == "update_trust_profile" else institution_update.get("trust_profile"),
            "resulting_institution_status": governance_status,
            "resulting_institution_sha256": institution_update.get("institution_sha256"),
            "public_visible": bool(request.get("public_visible", current.get("public_visible_requested", False))) and institution.get("public_visible") is True,
            "updated_at": _iso(self.now_fn()),
        })
        updated["challenge_sha256"] = _record_digest(updated, "challenge_sha256")
        _append(self.challenges_path, updated)
        self._event(challenge_id, "registry_challenge_resolved", actor, {"action": action, "resulting_status": governance_status})
        return {"ok": True, "version": APP_VERSION, "challenge": updated, "institution": institution_update}

    def create_appeal(self, challenge_id: str, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_governance_payload(request)
        actor = _actor(request.get("actor"))
        challenge = self.challenge(challenge_id)
        if challenge.get("status") != "resolved":
            raise ValueError("Only resolved registry challenges may be appealed.")
        if challenge.get("resolution_action") == "no_action":
            raise ValueError("No-action registry resolutions do not require an appeal workflow.")
        rationale = _safe_text(request.get("rationale"), 4000)
        evidence_reference = _safe_text(request.get("evidence_reference"), 500)
        if not rationale or not evidence_reference:
            raise ValueError("Appeal rationale and public-safe evidence reference are required.")
        appeal_id = _safe_id(request.get("appeal_id") or f"registry-appeal:{uuid4().hex[:20]}", "registry-appeal")
        if any(row.get("appeal_id") == appeal_id for row in self.appeals(limit=2000)):
            raise ValueError("Registry appeal ID already exists.")
        now = _iso(self.now_fn())
        record = {
            "schema": APPEAL_SCHEMA_VERSION,
            "release_version": APP_VERSION,
            "appeal_id": appeal_id,
            "challenge_id": challenge.get("challenge_id"),
            "institution_id": challenge.get("institution_id"),
            "challenged_resolution_action": challenge.get("resolution_action"),
            "challenge_sha256": challenge.get("challenge_sha256"),
            "rationale": rationale,
            "evidence_reference": evidence_reference,
            "status": "submitted",
            "submitted_by": actor,
            "created_at": now,
            "updated_at": now,
            "public_visible_requested": bool(request.get("public_visible", challenge.get("public_visible", False))),
            "public_visible": False,
            "original_resolution_retained": True,
            "prior_registry_records_retained": True,
            "prior_attestations_retained": True,
            "automatic_reinstatement_performed": False,
            "network_verification_performed": False,
            "remote_write_performed": False,
            "archive_or_evidence_mutated": False,
            "certification_claimed": False,
        }
        record["appeal_sha256"] = _record_digest(record, "appeal_sha256")
        _append(self.appeals_path, record)
        self._event(appeal_id, "registry_appeal_submitted", actor, {"challenge_id": challenge_id})
        return {"ok": True, "version": APP_VERSION, "appeal": record}

    def review_appeal(self, appeal_id: str, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_governance_payload(request)
        actor = _actor(request.get("actor"))
        reason = _safe_text(request.get("reason"), 4000)
        evidence_reference = _safe_text(request.get("evidence_reference"), 500)
        recommended_outcome = _safe_text(request.get("recommended_outcome"), 80).lower()
        if not reason or not evidence_reference:
            raise ValueError("Appeal review reason and evidence reference are required.")
        if recommended_outcome not in APPEAL_OUTCOMES:
            raise ValueError("Unsupported registry appeal recommendation.")
        current = self.appeal(appeal_id)
        if current.get("status") != "submitted":
            raise ValueError("Only submitted registry appeals may be reviewed.")
        if self.require_separation and actor == current.get("submitted_by"):
            raise ValueError("Registry appeal review requires separation of duties.")
        updated = deepcopy(current)
        updated.update({
            "status": "reviewed",
            "reviewed_by": actor,
            "reviewed_at": _iso(self.now_fn()),
            "review_reason": reason,
            "review_evidence_reference": evidence_reference,
            "recommended_outcome": recommended_outcome,
            "recommended_trust_profile": _safe_text(request.get("recommended_trust_profile"), 80).lower() or None,
            "updated_at": _iso(self.now_fn()),
        })
        if recommended_outcome == "modify_trust_profile" and updated["recommended_trust_profile"] not in TRUST_PROFILES:
            raise ValueError("A supported recommended trust profile is required.")
        updated["appeal_sha256"] = _record_digest(updated, "appeal_sha256")
        _append(self.appeals_path, updated)
        self._event(appeal_id, "registry_appeal_reviewed", actor, {"recommended_outcome": recommended_outcome})
        return {"ok": True, "version": APP_VERSION, "appeal": updated}

    def approve_appeal(self, appeal_id: str, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_governance_payload(request)
        actor = _actor(request.get("approved_by") or request.get("actor"))
        reason = _safe_text(request.get("reason"), 4000)
        outcome = _safe_text(request.get("outcome"), 80).lower()
        if not reason:
            raise ValueError("Appeal approval reason is required.")
        if outcome not in APPEAL_OUTCOMES:
            raise ValueError("Unsupported registry appeal outcome.")
        current = self.appeal(appeal_id)
        if current.get("status") != "reviewed":
            raise ValueError("Registry appeal must be reviewed before approval.")
        if self.require_separation and actor in {current.get("submitted_by"), current.get("reviewed_by")}:
            raise ValueError("Registry appeal approval requires separation of duties.")
        if outcome != current.get("recommended_outcome") and not _safe_text(request.get("variance_reason"), 2000):
            raise ValueError("A variance reason is required when approval differs from the appeal recommendation.")
        institution = self.registry_center.institution(str(current.get("institution_id")))
        institution_update = None
        resulting_status = institution.get("status")
        trust_profile = institution.get("trust_profile")
        if outcome in {"reinstate", "modify_trust_profile"}:
            resulting_status = "approved"
            if outcome == "modify_trust_profile":
                trust_profile = _safe_text(request.get("trust_profile") or current.get("recommended_trust_profile"), 80).lower()
                if trust_profile not in TRUST_PROFILES:
                    raise ValueError("A supported trust profile is required for the appeal outcome.")
            institution_update = deepcopy(institution)
            institution_update.update({
                "status": "approved",
                "governance_status": "approved",
                "trust_profile": trust_profile,
                "governance_appeal_id": current.get("appeal_id"),
                "governance_appeal_outcome": outcome,
                "governance_appeal_reason": reason,
                "governance_appeal_approved_at": _iso(self.now_fn()),
                "prior_institution_sha256": institution.get("institution_sha256"),
                "updated_at": _iso(self.now_fn()),
            })
            if outcome == "modify_trust_profile":
                institution_update["package_sha256"] = _institution_package_digest(institution_update)
            institution_update["institution_sha256"] = _record_digest(institution_update, "institution_sha256")
            _append(self.registry_center.institutions_path, institution_update)

        challenge = self.challenge(str(current.get("challenge_id")))
        updated = deepcopy(current)
        updated.update({
            "status": "resolved",
            "approved_by": actor,
            "resolved_at": _iso(self.now_fn()),
            "approval_reason": reason,
            "appeal_outcome": outcome,
            "resulting_institution_status": resulting_status,
            "resulting_trust_profile": trust_profile,
            "resulting_institution_sha256": (institution_update or institution).get("institution_sha256"),
            "public_visible": bool(request.get("public_visible", current.get("public_visible_requested", False))) and challenge.get("public_visible") is True,
            "updated_at": _iso(self.now_fn()),
        })
        updated["appeal_sha256"] = _record_digest(updated, "appeal_sha256")
        _append(self.appeals_path, updated)
        self._event(appeal_id, "registry_appeal_resolved", actor, {"outcome": outcome, "resulting_status": resulting_status})
        return {"ok": True, "version": APP_VERSION, "appeal": updated, "institution": institution_update or institution}

    def institution_governance(self, institution_id: str, *, public: bool = False) -> dict[str, Any]:
        institution = self.registry_center.institution(institution_id)
        if public and institution.get("public_visible") is not True:
            raise KeyError(institution_id)
        challenges = [row for row in self.challenges(public=public, limit=2000) if row.get("institution_id") == institution_id]
        challenge_ids = {row.get("challenge_id") for row in challenges}
        appeals = [row for row in self.appeals(public=public, limit=2000) if row.get("challenge_id") in challenge_ids]
        summary = {
            "schema": "sc-site-intelligence-institution-governance-summary/1.0",
            "release_version": APP_VERSION,
            "institution_id": institution.get("institution_id"),
            "institution_name": institution.get("institution_name"),
            "current_status": institution.get("status"),
            "current_trust_profile": institution.get("trust_profile"),
            "institution_sha256": institution.get("institution_sha256"),
            "challenge_count": len(challenges),
            "appeal_count": len(appeals),
            "challenges": challenges,
            "appeals": appeals,
            "original_registry_records_retained": True,
            "prior_attestations_retained": True,
            "inactive_institutions_excluded_from_current_consensus": institution.get("status") != "approved",
            "automatic_enforcement_performed": False,
            "remote_write_performed": False,
            "certification_claimed": False,
        }
        summary["governance_sha256"] = _record_digest(summary, "governance_sha256")
        return summary

    def package_payload(self, institution_id: str, format: str = "json", *, public: bool = False) -> tuple[str, str]:
        governance = self.institution_governance(institution_id, public=public)
        package = {
            "schema": PACKAGE_SCHEMA_VERSION,
            "release_version": APP_VERSION,
            "governance": governance,
            "original_registry_records_retained": True,
            "prior_attestations_retained": True,
            "automatic_enforcement_performed": False,
            "remote_write_performed": False,
            "certification_claimed": False,
        }
        package["package_sha256"] = _record_digest(package, "package_sha256")
        if format == "json":
            return "application/json", json.dumps(package, indent=2, sort_keys=True, ensure_ascii=False)
        if format != "markdown":
            raise ValueError("Unsupported registry governance package format.")
        lines = [
            f"# Registry governance — {institution_id}", "",
            f"- Release version: `{APP_VERSION}`",
            f"- Current status: `{governance.get('current_status')}`",
            f"- Current trust profile: `{governance.get('current_trust_profile')}`",
            f"- Package SHA-256: `{package.get('package_sha256')}`", "",
            "This append-only governance package preserves prior registry states and attestations. It is not certification, automatic enforcement, or a remote-system write.",
        ]
        return "text/markdown", "\n".join(lines) + "\n"

    def history(self, entity_id: str, limit: int = 200) -> list[dict[str, Any]]:
        target = _safe_text(entity_id, 240)
        rows = [row for row in _read_jsonl(self.events_path, self.max_records) if row.get("entity_id") == target]
        rows.sort(key=lambda row: str(row.get("occurred_at") or ""), reverse=True)
        return rows[:max(1, min(int(limit), 1000))]

    def status(self) -> dict[str, Any]:
        challenges = self.challenges(limit=2000)
        appeals = self.appeals(limit=2000)
        institutions = self.registry_center.institutions(limit=2000)
        return {
            "ok": True,
            "version": APP_VERSION,
            "challenge_count": len(challenges),
            "public_challenge_count": len(self.challenges(public=True, limit=2000)),
            "open_challenge_count": sum(1 for row in challenges if row.get("status") != "resolved"),
            "appeal_count": len(appeals),
            "public_appeal_count": len(self.appeals(public=True, limit=2000)),
            "open_appeal_count": sum(1 for row in appeals if row.get("status") != "resolved"),
            "approved_institution_count": sum(1 for row in institutions if row.get("status") == "approved"),
            "suspended_institution_count": sum(1 for row in institutions if row.get("status") == "suspended"),
            "revoked_institution_count": sum(1 for row in institutions if row.get("status") == "revoked"),
            "append_only_governance_ledger": True,
            "original_registry_records_retained": True,
            "prior_attestations_retained": True,
            "automatic_enforcement_performed": False,
            "network_verification_performed": False,
            "remote_write_performed": False,
            "archive_or_evidence_mutated": False,
            "certification_claimed": False,
        }
