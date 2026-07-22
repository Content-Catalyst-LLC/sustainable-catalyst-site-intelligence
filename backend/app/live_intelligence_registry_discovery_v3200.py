"""Public registry discovery, evidence search, and institutional profiles.

Site Intelligence v3.22.0 builds a read-only discovery index over approved,
public-safe preservation registry, exchange, attestation, challenge, and appeal
records. The discovery layer never mutates source records, stores queries,
profiles visitors, exposes staff identities, or grants remote write authority.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import re
from typing import Any, Iterable, Mapping

from .version import APP_VERSION

POLICY_SCHEMA_VERSION = "sc-site-intelligence-registry-discovery-policy/1.0"
PROFILE_SCHEMA_VERSION = "sc-site-intelligence-preservation-institution-profile/1.0"
SEARCH_SCHEMA_VERSION = "sc-site-intelligence-preservation-registry-search/1.0"

RECORD_TYPES = ("institution", "attestation", "exchange", "challenge", "appeal")
SORT_MODES = ("relevance", "name", "recent")

_PRIVATE_KEYS = {
    "actor", "created_by", "verified_by", "approved_by", "attested_by", "reviewed_by",
    "resolved_by", "appealed_by", "review_reason", "approval_reason", "resolution_reason",
    "variance_reason", "internal_note", "email", "phone", "contact_person", "recipient",
    "credential", "token", "secret", "authorization", "cookie", "private_key", "access_key",
}


def registry_discovery_policy() -> dict[str, Any]:
    return {
        "ok": True,
        "version": APP_VERSION,
        "schema": POLICY_SCHEMA_VERSION,
        "principle": "Make approved preservation records discoverable through bounded public search and evidence-linked profiles without exposing identities, internal workflow details, or remote write capability.",
        "record_types": list(RECORD_TYPES),
        "sort_modes": list(SORT_MODES),
        "filters": [
            "record_type", "institution_type", "trust_profile", "jurisdiction",
            "exchange_profile", "verification_method", "governance_status",
        ],
        "boundaries": {
            "approved_public_records_only": True,
            "staff_identities_exposed": False,
            "internal_review_reasons_exposed": False,
            "search_queries_stored": False,
            "visitor_profiles_created": False,
            "source_records_mutated": False,
            "network_verification_performed": False,
            "remote_write_performed": False,
            "certification_claimed": False,
        },
        "routes": {
            "policy": "/public/live-intelligence/registry-discovery/policy",
            "status": "/public/live-intelligence/registry-discovery/status",
            "facets": "/public/live-intelligence/registry-discovery/facets",
            "search": "/public/live-intelligence/registry-discovery/search",
            "institution_profile": "/public/live-intelligence/registry-discovery/institutions/{institution_id}",
        },
    }


def _clean_text(value: Any, max_length: int = 500) -> str:
    text = " ".join(str(value or "").replace("\x00", " ").split())
    return text[:max_length]


def _safe_reference(value: Any) -> str:
    text = _clean_text(value, 600)
    if re.search(r"(?i)(?:password|secret|token|credential|authorization|cookie|private[_-]?key|access[_-]?key)=", text):
        return ""
    return text


def _public_copy(record: Mapping[str, Any], allowed: Iterable[str]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key in allowed:
        if key in _PRIVATE_KEYS or key not in record:
            continue
        value = record.get(key)
        if key.endswith("reference"):
            value = _safe_reference(value)
        output[key] = deepcopy(value)
    return output


def _tokens(query: str) -> list[str]:
    clean = _clean_text(query, 200).lower()
    return [token for token in re.findall(r"[a-z0-9][a-z0-9._:-]{1,63}", clean) if token]


def _timestamp(record: Mapping[str, Any]) -> str:
    for key in ("approved_at", "resolved_at", "attested_at", "verified_at", "created_at", "updated_at"):
        value = record.get(key)
        if value:
            return str(value)
    return ""


def _score(record: Mapping[str, Any], query_tokens: list[str]) -> int:
    if not query_tokens:
        return 0
    title = str(record.get("title") or "").lower()
    identifier = str(record.get("record_id") or "").lower()
    searchable = str(record.get("search_text") or "").lower()
    score = 0
    for token in query_tokens:
        if token == title:
            score += 120
        elif title.startswith(token):
            score += 80
        elif token in title:
            score += 50
        if token in identifier:
            score += 35
        occurrences = searchable.count(token)
        score += min(occurrences, 6) * 12
    return score


class LiveIntelligenceRegistryDiscovery:
    def __init__(self, *, registry_center: Any, governance_center: Any, exchange_center: Any) -> None:
        self.registry_center = registry_center
        self.governance_center = governance_center
        self.exchange_center = exchange_center

    @staticmethod
    def _institution_record(row: Mapping[str, Any]) -> dict[str, Any]:
        public = _public_copy(row, (
            "institution_id", "institution_name", "jurisdiction", "institution_type",
            "repository_reference", "public_policy_reference", "trust_profile", "trust_basis_note",
            "supported_profiles", "verification_methods", "status", "approved_at", "evidence_reference",
            "institution_sha256", "trust_declaration_human_reviewed", "certification_claimed",
        ))
        public.update({
            "record_type": "institution",
            "record_id": row.get("institution_id"),
            "title": row.get("institution_name"),
            "summary": _clean_text(row.get("trust_basis_note") or "Approved public preservation institution.", 500),
            "published_at": _timestamp(row),
        })
        public["search_text"] = " ".join(_clean_text(value, 1000) for value in (
            row.get("institution_name"), row.get("jurisdiction"), row.get("institution_type"),
            row.get("trust_profile"), row.get("trust_basis_note"), row.get("repository_reference"),
            row.get("public_policy_reference"), " ".join(row.get("supported_profiles") or []),
            " ".join(row.get("verification_methods") or []),
        )).lower()
        return public

    @staticmethod
    def _attestation_record(row: Mapping[str, Any]) -> dict[str, Any]:
        public = _public_copy(row, (
            "attestation_id", "exchange_id", "exchange_package_sha256", "reported_package_sha256",
            "checksum_matches", "institution_id", "institution_sha256", "institution_name", "trust_profile",
            "method", "result", "evidence_reference", "attestation_note", "attested_at",
            "attestation_sha256", "external_attestation_human_reported", "network_verification_performed",
            "certification_claimed",
        ))
        public.update({
            "record_type": "attestation",
            "record_id": row.get("attestation_id"),
            "title": f"{row.get('institution_name') or 'Institution'} attestation",
            "summary": _clean_text(row.get("attestation_note") or "Human-reported checksum attestation.", 500),
            "published_at": _timestamp(row),
        })
        public["search_text"] = " ".join(_clean_text(value, 1000) for value in (
            row.get("institution_name"), row.get("trust_profile"), row.get("method"), row.get("result"),
            row.get("evidence_reference"), row.get("attestation_note"), row.get("exchange_id"),
        )).lower()
        return public

    def _exchange_record(self, row: Mapping[str, Any]) -> dict[str, Any]:
        public = _public_copy(row, (
            "exchange_id", "profile", "institution_reference", "record_count", "status", "approved_at",
            "package_sha256", "exchange_sha256", "standards_alignment_only", "public_visible",
        ))
        try:
            consensus = self.registry_center.consensus(str(row.get("exchange_id")), public=True)
        except KeyError:
            consensus = None
        public.update({
            "record_type": "exchange",
            "record_id": row.get("exchange_id"),
            "title": f"Preservation exchange {row.get('exchange_id')}",
            "summary": f"{row.get('profile') or 'Preservation'} exchange with {int(row.get('record_count') or 0)} preserved records.",
            "published_at": _timestamp(row),
            "consensus": self._sanitize_consensus(consensus) if consensus else None,
        })
        public["search_text"] = " ".join(_clean_text(value, 1000) for value in (
            row.get("exchange_id"), row.get("profile"), row.get("institution_reference"),
            (consensus or {}).get("consensus_status"), " ".join((consensus or {}).get("verification_methods") or []),
        )).lower()
        return public

    @staticmethod
    def _challenge_record(row: Mapping[str, Any]) -> dict[str, Any]:
        public = _public_copy(row, (
            "challenge_id", "institution_id", "institution_name", "challenge_type", "summary", "rationale",
            "evidence_reference", "status", "created_at", "review_evidence_reference", "recommended_action",
            "resolution_action", "resolution_evidence_reference", "resolved_at", "public_visible",
            "prior_registry_records_retained", "prior_attestations_retained", "challenge_sha256",
            "automatic_enforcement_performed", "certification_claimed",
        ))
        public.update({
            "record_type": "challenge",
            "record_id": row.get("challenge_id"),
            "title": row.get("summary") or f"Registry challenge {row.get('challenge_id')}",
            "summary": _clean_text(row.get("rationale") or row.get("summary"), 500),
            "published_at": _timestamp(row),
        })
        public["search_text"] = " ".join(_clean_text(value, 1000) for value in (
            row.get("institution_name"), row.get("challenge_type"), row.get("summary"), row.get("rationale"),
            row.get("evidence_reference"), row.get("recommended_action"), row.get("resolution_action"),
        )).lower()
        return public

    @staticmethod
    def _appeal_record(row: Mapping[str, Any]) -> dict[str, Any]:
        public = _public_copy(row, (
            "appeal_id", "challenge_id", "institution_id", "institution_name", "rationale", "evidence_reference",
            "status", "created_at", "review_evidence_reference", "recommended_outcome", "resolution_outcome",
            "resolution_evidence_reference", "resolved_at", "public_visible", "appeal_sha256",
            "prior_registry_records_retained", "prior_attestations_retained", "automatic_enforcement_performed",
            "certification_claimed",
        ))
        public.update({
            "record_type": "appeal",
            "record_id": row.get("appeal_id"),
            "title": f"Registry appeal for {row.get('institution_name') or row.get('institution_id')}",
            "summary": _clean_text(row.get("rationale"), 500),
            "published_at": _timestamp(row),
        })
        public["search_text"] = " ".join(_clean_text(value, 1000) for value in (
            row.get("institution_name"), row.get("rationale"), row.get("evidence_reference"),
            row.get("recommended_outcome"), row.get("resolution_outcome"), row.get("challenge_id"),
        )).lower()
        return public

    @staticmethod
    def _sanitize_consensus(consensus: Mapping[str, Any]) -> dict[str, Any]:
        return _public_copy(consensus, (
            "exchange_id", "exchange_package_sha256", "consensus_status", "consensus_threshold",
            "verified_institution_count", "verified_institution_ids", "verification_methods", "attestation_count",
            "consensus_sha256", "multi_party_consensus_unique_institutions",
            "external_attestations_human_reported", "network_verification_performed", "certification_claimed",
        ))

    def records(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        rows.extend(self._institution_record(row) for row in self.registry_center.institutions(public=True, limit=2000))
        rows.extend(self._attestation_record(row) for row in self.registry_center.attestations(public=True, limit=2000))
        rows.extend(self._exchange_record(row) for row in self.exchange_center.exchanges(public=True, limit=2000))
        rows.extend(self._challenge_record(row) for row in self.governance_center.challenges(public=True, limit=2000))
        rows.extend(self._appeal_record(row) for row in self.governance_center.appeals(public=True, limit=2000))
        return rows

    def facets(self) -> dict[str, Any]:
        records = self.records()
        institutions = [row for row in records if row.get("record_type") == "institution"]
        exchanges = [row for row in records if row.get("record_type") == "exchange"]
        challenges = [row for row in records if row.get("record_type") == "challenge"]
        return {
            "ok": True,
            "version": APP_VERSION,
            "schema": SEARCH_SCHEMA_VERSION,
            "record_types": self._counts(records, "record_type"),
            "institution_types": self._counts(institutions, "institution_type"),
            "trust_profiles": self._counts(institutions, "trust_profile"),
            "jurisdictions": self._counts(institutions, "jurisdiction"),
            "exchange_profiles": self._counts(exchanges, "profile"),
            "governance_actions": self._counts(challenges, "resolution_action"),
            "search_queries_stored": False,
            "visitor_profiles_created": False,
        }

    @staticmethod
    def _counts(rows: Iterable[Mapping[str, Any]], field: str) -> list[dict[str, Any]]:
        counts: dict[str, int] = {}
        for row in rows:
            value = _clean_text(row.get(field), 160)
            if value:
                counts[value] = counts.get(value, 0) + 1
        return [{"value": key, "count": counts[key]} for key in sorted(counts, key=lambda item: (-counts[item], item.lower()))]

    def search(
        self,
        *,
        query: str = "",
        record_type: str = "",
        institution_type: str = "",
        trust_profile: str = "",
        jurisdiction: str = "",
        exchange_profile: str = "",
        verification_method: str = "",
        governance_status: str = "",
        sort: str = "relevance",
        offset: int = 0,
        limit: int = 25,
    ) -> dict[str, Any]:
        query_tokens = _tokens(query)
        record_type = _clean_text(record_type, 40).lower()
        if record_type and record_type not in RECORD_TYPES:
            raise ValueError("Unsupported registry discovery record type.")
        sort = _clean_text(sort, 40).lower() or "relevance"
        if sort not in SORT_MODES:
            raise ValueError("Unsupported registry discovery sort mode.")
        offset = max(0, min(int(offset), 10000))
        limit = max(1, min(int(limit), 100))
        filters = {
            "institution_type": _clean_text(institution_type, 100).lower(),
            "trust_profile": _clean_text(trust_profile, 100).lower(),
            "jurisdiction": _clean_text(jurisdiction, 160).lower(),
            "exchange_profile": _clean_text(exchange_profile, 100).lower(),
            "verification_method": _clean_text(verification_method, 100).lower(),
            "governance_status": _clean_text(governance_status, 100).lower(),
        }
        results: list[dict[str, Any]] = []
        for row in self.records():
            if record_type and row.get("record_type") != record_type:
                continue
            if filters["institution_type"] and str(row.get("institution_type") or "").lower() != filters["institution_type"]:
                continue
            if filters["trust_profile"] and str(row.get("trust_profile") or "").lower() != filters["trust_profile"]:
                continue
            if filters["jurisdiction"] and filters["jurisdiction"] not in str(row.get("jurisdiction") or "").lower():
                continue
            if filters["exchange_profile"] and str(row.get("profile") or "").lower() != filters["exchange_profile"]:
                continue
            methods = [str(value).lower() for value in (row.get("verification_methods") or [])]
            if row.get("method"):
                methods.append(str(row.get("method")).lower())
            if filters["verification_method"] and filters["verification_method"] not in methods:
                continue
            status_value = str(row.get("resolution_action") or row.get("resolution_outcome") or row.get("status") or "").lower()
            if filters["governance_status"] and status_value != filters["governance_status"]:
                continue
            score = _score(row, query_tokens)
            if query_tokens and score <= 0:
                continue
            public = {key: deepcopy(value) for key, value in row.items() if key != "search_text"}
            public["relevance_score"] = score
            results.append(public)
        if sort == "name":
            results.sort(key=lambda row: (str(row.get("title") or "").lower(), str(row.get("record_id") or "")))
        elif sort == "recent":
            results.sort(key=lambda row: (str(row.get("published_at") or ""), str(row.get("record_id") or "")), reverse=True)
        else:
            results.sort(key=lambda row: (-int(row.get("relevance_score") or 0), str(row.get("title") or "").lower(), str(row.get("record_id") or "")))
        total = len(results)
        page = results[offset:offset + limit]
        return {
            "ok": True,
            "version": APP_VERSION,
            "schema": SEARCH_SCHEMA_VERSION,
            "query": _clean_text(query, 200),
            "total": total,
            "offset": offset,
            "limit": limit,
            "results": page,
            "facets": self.facets(),
            "search_queries_stored": False,
            "visitor_profiles_created": False,
            "staff_identities_exposed": False,
            "source_records_mutated": False,
            "certification_claimed": False,
        }

    def institution_profile(self, institution_id: str) -> dict[str, Any]:
        institution = self.registry_center.institution(institution_id, public=True)
        institution_public = self._institution_record(institution)
        attestations = [
            self._attestation_record(row)
            for row in self.registry_center.attestations(public=True, limit=2000)
            if row.get("institution_id") == institution_id
        ]
        exchange_ids = sorted({str(row.get("exchange_id")) for row in attestations if row.get("exchange_id")})
        exchanges: list[dict[str, Any]] = []
        for exchange_id in exchange_ids:
            try:
                exchange = self.exchange_center.exchange(exchange_id, public=True)
                exchanges.append(self._exchange_record(exchange))
            except KeyError:
                continue
        try:
            governance = self.governance_center.institution_governance(institution_id, public=True)
            challenges = [self._challenge_record(row) for row in governance.get("challenges") or []]
            appeals = [self._appeal_record(row) for row in governance.get("appeals") or []]
            governance_summary = _public_copy(governance, (
                "institution_id", "institution_name", "current_status", "current_trust_profile", "institution_sha256",
                "challenge_count", "appeal_count", "original_registry_records_retained", "prior_attestations_retained",
                "inactive_institutions_excluded_from_current_consensus", "automatic_enforcement_performed",
                "remote_write_performed", "certification_claimed", "governance_sha256",
            ))
        except KeyError:
            challenges, appeals, governance_summary = [], [], None
        evidence_links: list[dict[str, str]] = []
        seen: set[str] = set()
        for label, value in (
            ("Repository record", institution.get("repository_reference")),
            ("Preservation policy", institution.get("public_policy_reference")),
            ("Registry verification evidence", institution.get("evidence_reference")),
        ):
            reference = _safe_reference(value)
            if reference and reference not in seen:
                seen.add(reference); evidence_links.append({"label": label, "reference": reference})
        for row in attestations + challenges + appeals:
            reference = _safe_reference(row.get("evidence_reference"))
            if reference and reference not in seen:
                seen.add(reference); evidence_links.append({"label": f"{str(row.get('record_type')).title()} evidence", "reference": reference})
        profile = {
            "ok": True,
            "version": APP_VERSION,
            "schema": PROFILE_SCHEMA_VERSION,
            "institution": institution_public,
            "governance": governance_summary,
            "attestations": attestations,
            "exchanges": exchanges,
            "challenges": challenges,
            "appeals": appeals,
            "evidence_links": evidence_links,
            "staff_identities_exposed": False,
            "search_queries_stored": False,
            "visitor_profiles_created": False,
            "source_records_mutated": False,
            "network_verification_performed": False,
            "remote_write_performed": False,
            "certification_claimed": False,
        }
        return profile

    def status(self) -> dict[str, Any]:
        records = self.records()
        return {
            "ok": True,
            "version": APP_VERSION,
            "record_count": len(records),
            "record_type_counts": {kind: sum(1 for row in records if row.get("record_type") == kind) for kind in RECORD_TYPES},
            "institution_profile_count": sum(1 for row in records if row.get("record_type") == "institution"),
            "search_queries_stored": False,
            "visitor_profiles_created": False,
            "staff_identities_exposed": False,
            "source_records_mutated": False,
            "network_verification_performed": False,
            "remote_write_performed": False,
            "certification_claimed": False,
        }
