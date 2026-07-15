"""International Law and Global Governance Observatory for Site Intelligence v2.3.0.

This module is a public-safe bridge to Sustainable Catalyst Core's governed
international-law record layer. It preserves legal authority distinctions,
official symbols, procedural status, source attribution, and review limits. It
never exposes Core credentials and never converts an official record into legal
advice, a compliance determination, or an unsupported claim of binding effect.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
import os
from typing import Any, Iterable, Mapping
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .global_conditions_observatory import CoreReadConfig, _core_json, _items, _safe_text, _safe_url, core_read_config
from .international_law_governance import MONITORS, SOURCES

RELEASE_SCHEMA = "sc-site-intelligence-international-law-observatory/1.0"
RECORDS_SCHEMA = "sc-site-intelligence-international-law-records/1.0"
MAX_RECORDS = 300
MAX_TIMELINE_RECORDS = 240

_AUTHORITY_FALLBACK = {
    "binding_treaty_obligation": "Binding treaty obligation or treaty-status record.",
    "official_security_council_resolution": "Official Security Council resolution; binding effect requires reviewed Charter and textual analysis.",
    "binding_security_council_decision": "Security Council decision whose binding status has been established through reviewed legal analysis.",
    "judicial_decision": "Judicial decision for the parties and matter concerned.",
    "advisory_judicial_opinion": "Advisory judicial opinion; authoritative but not a contentious judgment.",
    "official_interpretation": "Official interpretation by an authorized mechanism.",
    "recommendatory_resolution": "Official resolution or decision with recommendatory authority.",
    "non_binding_recommendation": "Official recommendation from a monitoring or review mechanism.",
    "draft_codification_text": "Draft codification work, such as articles, conclusions, or principles.",
    "official_report": "Official report or document that is evidentiary rather than itself a binding rule.",
    "humanitarian_reporting": "Humanitarian report or situation update; informational rather than legal authority.",
    "statistical_observation": "Official statistical observation; evidence rather than legal authority.",
    "commentary": "Secondary commentary or analysis.",
}

_AUTHORITY_LABELS = {
    "binding_treaty_obligation": "Binding treaty obligation",
    "official_security_council_resolution": "Official Security Council resolution",
    "binding_security_council_decision": "Binding Security Council decision",
    "judicial_decision": "Judicial decision",
    "advisory_judicial_opinion": "Advisory judicial opinion",
    "official_interpretation": "Official interpretation",
    "recommendatory_resolution": "Recommendatory resolution",
    "non_binding_recommendation": "Non-binding recommendation",
    "draft_codification_text": "Draft codification text",
    "official_report": "Official report",
    "humanitarian_reporting": "Humanitarian reporting",
    "statistical_observation": "Statistical observation",
    "commentary": "Commentary",
}

_AUTHORITY_GROUPS = {
    "binding_treaty_obligation": "binding",
    "binding_security_council_decision": "binding",
    "judicial_decision": "judicial",
    "advisory_judicial_opinion": "judicial",
    "official_security_council_resolution": "institutional",
    "official_interpretation": "interpretive",
    "recommendatory_resolution": "recommendatory",
    "non_binding_recommendation": "recommendatory",
    "draft_codification_text": "development",
    "official_report": "evidentiary",
    "humanitarian_reporting": "evidentiary",
    "statistical_observation": "evidentiary",
    "commentary": "secondary",
}

_ALLOWED_RECORD_TYPES = {
    "treaty", "treaty_action", "reservation", "declaration",
    "security_council_resolution", "general_assembly_resolution", "resolution",
    "vote", "judicial_case", "judgment", "advisory_opinion", "order",
    "human_rights_recommendation", "ilc_draft_text", "un_report",
    "humanitarian_report", "sanctions_measure", "legal_commentary",
    "official_document", "statistical_observation",
}

_SENSITIVE_KEYS = {
    "api_key", "apikey", "key", "token", "authorization", "password", "secret",
    "credential", "write_api_key", "public_api_key", "raw_record_id",
}


@dataclass(frozen=True)
class LawObservatoryConfig:
    enabled: bool
    timeout_seconds: float
    cache_ttl_seconds: int


def _as_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on", "enabled"}


def law_observatory_config(settings: Any = None) -> LawObservatoryConfig:
    enabled = getattr(settings, "international_law_observatory_enabled", None)
    if enabled is None:
        enabled = os.getenv("SC_SI_INTERNATIONAL_LAW_OBSERVATORY_ENABLED", "true")
    timeout = getattr(settings, "international_law_observatory_timeout_seconds", None)
    if timeout is None:
        timeout = os.getenv("SC_SI_INTERNATIONAL_LAW_OBSERVATORY_TIMEOUT_SECONDS", "9")
    ttl = getattr(settings, "international_law_observatory_cache_ttl_seconds", None)
    if ttl is None:
        ttl = os.getenv("SC_SI_INTERNATIONAL_LAW_OBSERVATORY_CACHE_TTL_SECONDS", "120")
    return LawObservatoryConfig(
        enabled=_as_bool(enabled, True),
        timeout_seconds=max(2.0, min(float(timeout), 30.0)),
        cache_ttl_seconds=max(15, min(int(ttl), 1800)),
    )


def _core_config(settings: Any = None) -> CoreReadConfig:
    base = core_read_config(settings)
    local = law_observatory_config(settings)
    return CoreReadConfig(
        enabled=bool(base.enabled and local.enabled),
        base_url=base.base_url,
        api_key=base.api_key,
        timeout_seconds=local.timeout_seconds,
        cache_ttl_seconds=local.cache_ttl_seconds,
    )


def _sensitive_key(value: Any) -> bool:
    normalized = "".join(character for character in str(value or "").lower() if character.isalnum())
    return normalized in {"key", "rawrecordid"} or any(
        token in normalized for token in ("apikey", "token", "authorization", "password", "secret", "credential")
    )


def _public_url(value: Any) -> str:
    safe = _safe_url(value)
    if not safe:
        return ""
    parts = urlsplit(safe)
    query = [(key, item) for key, item in parse_qsl(parts.query, keep_blank_values=True) if not _sensitive_key(key)]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query, doseq=True), parts.fragment))


def _safe_list(value: Any, limit: int = 40, item_limit: int = 240) -> list[str]:
    if not isinstance(value, list):
        return []
    output: list[str] = []
    for item in value[:limit]:
        clean = _safe_text(item, item_limit)
        if clean and clean not in output:
            output.append(clean)
    return output


def _safe_mapping(value: Any, *, depth: int = 0) -> dict[str, Any]:
    if not isinstance(value, Mapping) or depth > 2:
        return {}
    output: dict[str, Any] = {}
    for raw_key, raw_value in value.items():
        key = _safe_text(raw_key, 80)
        if not key or key.lower() in _SENSITIVE_KEYS or _sensitive_key(key):
            continue
        if isinstance(raw_value, Mapping):
            nested = _safe_mapping(raw_value, depth=depth + 1)
            if nested:
                output[key] = nested
        elif isinstance(raw_value, list):
            cleaned = _safe_list(raw_value, 30, 240)
            if cleaned:
                output[key] = cleaned
        elif raw_value is None or isinstance(raw_value, (bool, int, float)):
            output[key] = raw_value
        else:
            output[key] = _safe_text(raw_value, 500)
    return output


def _record_date(record: Mapping[str, Any]) -> str:
    return str(record.get("publication_date") or record.get("adoption_date") or record.get("entry_into_force_date") or "")


def _institution_family(record: Mapping[str, Any]) -> str:
    text = " ".join(str(record.get(field) or "").lower() for field in ("legal_body", "issuing_body", "source_id", "record_type"))
    if "security council" in text or "s/res" in text:
        return "un-security-council"
    if "general assembly" in text or "a/res" in text:
        return "un-general-assembly"
    if "human rights" in text or "ohchr" in text or "treaty body" in text:
        return "human-rights"
    if "international court of justice" in text or "icj" in text:
        return "international-courts"
    if "international law commission" in text or "ilc" in text:
        return "law-development"
    if "ocha" in text or "reliefweb" in text or "humanitarian" in text:
        return "humanitarian"
    if "treaty" in text or "depositary" in text:
        return "treaties"
    return "un-and-global-governance"


def _public_record(record: Mapping[str, Any], taxonomy: Mapping[str, Any] | None = None) -> dict[str, Any]:
    authority = _safe_text(record.get("authority_level"), 100) or "official_report"
    record_type = _safe_text(record.get("record_type"), 100) or "official_document"
    if record_type not in _ALLOWED_RECORD_TYPES:
        record_type = "official_document"
    authority_explanation = _safe_text((taxonomy or {}).get(authority), 1200) or _AUTHORITY_FALLBACK.get(authority, "Official-source legal or governance record; legal effect requires contextual review.")
    countries = [item.upper() if len(item) <= 3 else item for item in _safe_list(record.get("countries"), 80, 120)]
    output = {
        "id": _safe_text(record.get("id"), 180),
        "source_record_id": _safe_text(record.get("source_record_id"), 240),
        "source_id": _safe_text(record.get("source_id"), 140),
        "connector_id": _safe_text(record.get("connector_id"), 180),
        "record_type": record_type,
        "authority_level": authority,
        "authority_label": _AUTHORITY_LABELS.get(authority, authority.replace("_", " ").title()),
        "authority_group": _AUTHORITY_GROUPS.get(authority, "other"),
        "authority_explanation": authority_explanation,
        "title": _safe_text(record.get("title"), 600),
        "official_symbol": _safe_text(record.get("official_symbol"), 180),
        "issuing_body": _safe_text(record.get("issuing_body"), 260),
        "legal_body": _safe_text(record.get("legal_body"), 260),
        "institution_family": "",
        "jurisdiction": _safe_text(record.get("jurisdiction"), 160),
        "legal_status": _safe_text(record.get("legal_status"), 100),
        "adoption_date": _safe_text(record.get("adoption_date"), 80),
        "publication_date": _safe_text(record.get("publication_date"), 80),
        "entry_into_force_date": _safe_text(record.get("entry_into_force_date"), 80),
        "display_date": "",
        "languages": _safe_list(record.get("languages"), 20, 80),
        "countries": countries,
        "subjects": _safe_list(record.get("subjects"), 60, 180),
        "related_instruments": _safe_list(record.get("related_instruments"), 40, 240),
        "related_cases": _safe_list(record.get("related_cases"), 40, 240),
        "related_resolutions": _safe_list(record.get("related_resolutions"), 40, 240),
        "related_sdg_targets": _safe_list(record.get("related_sdg_targets"), 40, 80),
        "canonical_source_url": _public_url(record.get("canonical_source_url")),
        "citation": _safe_text(record.get("citation"), 1000),
        "summary": _safe_text(record.get("summary"), 1800),
        "license_name": _safe_text(record.get("license_name"), 180),
        "attribution": _safe_text(record.get("attribution"), 260),
        "metadata": _safe_mapping(record.get("metadata")),
        "content_hash": _safe_text(record.get("content_hash"), 128),
        "public": bool(record.get("public", True)),
    }
    output["institution_family"] = _institution_family(output)
    output["display_date"] = _record_date(output)
    return output


def _integration_state(settings: Any = None, error: str = "") -> dict[str, Any]:
    config = _core_config(settings)
    if not law_observatory_config(settings).enabled:
        state, message = "disabled", "The international-law observatory is disabled."
    elif not config.configured:
        state, message = "core-unconfigured", "Platform Core is not configured; the legacy source registry remains available without synthetic legal records."
    elif error:
        state, message = "degraded", error
    else:
        state, message = "connected", "Platform Core international-law records are connected."
    return {
        "state": state,
        "message": message,
        "configured": config.configured,
        "enabled": law_observatory_config(settings).enabled,
        "credential_exposed": False,
    }


def _taxonomy(settings: Any = None) -> dict[str, str]:
    config = _core_config(settings)
    if not config.configured:
        return dict(_AUTHORITY_FALLBACK)
    payload = _core_json(config, "/api/v1/international-law/authority-taxonomy", cache_key="law-observatory:taxonomy")
    if isinstance(payload, dict) and isinstance(payload.get("data"), dict):
        payload = payload["data"]
    if not isinstance(payload, dict):
        return dict(_AUTHORITY_FALLBACK)
    return {str(key): _safe_text(value, 1200) for key, value in payload.items() if key and value}


def _core_records_payload(settings: Any, parameters: Mapping[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, str]]:
    config = _core_config(settings)
    if not config.configured:
        return [], {}, dict(_AUTHORITY_FALLBACK)
    taxonomy = _taxonomy(settings)
    payload = _core_json(config, "/api/v1/international-law/records", parameters)
    records = [_public_record(item, taxonomy) for item in _items(payload, "items", "records")]
    meta = payload.get("meta", {}) if isinstance(payload, dict) else {}
    return records, meta if isinstance(meta, dict) else {}, taxonomy


def build_law_overview(settings: Any = None) -> dict[str, Any]:
    integration = _integration_state(settings)
    records: list[dict[str, Any]] = []
    taxonomy = dict(_AUTHORITY_FALLBACK)
    if integration["state"] == "connected":
        try:
            records, _, taxonomy = _core_records_payload(settings, {"limit": MAX_RECORDS})
        except RuntimeError as exc:
            integration = _integration_state(settings, error=str(exc))
    bodies = Counter(item.get("legal_body") or item.get("issuing_body") for item in records if item.get("legal_body") or item.get("issuing_body"))
    countries = {country for item in records for country in item.get("countries", [])}
    subjects = {subject for item in records for subject in item.get("subjects", [])}
    authorities = Counter(item.get("authority_level") for item in records if item.get("authority_level"))
    return {
        "ok": True,
        "schema": RELEASE_SCHEMA,
        "version": "2.3.0",
        "release_name": "International Law and Global Governance Observatory",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "integration": integration,
        "counts": {
            "records_available": len(records),
            "legal_bodies": len(bodies),
            "countries": len(countries),
            "subjects": len(subjects),
            "authority_levels": len(authorities),
            "registered_sources": len(SOURCES),
            "registered_monitors": len(MONITORS),
        },
        "authority_taxonomy": [
            {
                "id": key,
                "label": _AUTHORITY_LABELS.get(key, key.replace("_", " ").title()),
                "group": _AUTHORITY_GROUPS.get(key, "other"),
                "description": value,
                "visible_records": int(authorities.get(key, 0)),
            }
            for key, value in taxonomy.items()
        ],
        "governance_policy": {
            "legal_advice": False,
            "automated_compliance_determination": False,
            "automatic_binding_effect_inference": False,
            "official_source_links_required": True,
            "authority_type_preserved": True,
            "statement": "Official records are displayed with their authority type, procedural status, source, and limitations. Site Intelligence does not infer legal effect from a document symbol alone.",
        },
    }


def build_law_records(
    settings: Any = None,
    *,
    record_type: str = "",
    authority_level: str = "",
    legal_body: str = "",
    country: str = "",
    subject: str = "",
    official_symbol: str = "",
    query: str = "",
    start: str = "",
    end: str = "",
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    parameters = {
        "record_type": record_type,
        "authority_level": authority_level,
        "legal_body": legal_body,
        "country": country.upper() if len(country.strip()) <= 3 else country.strip(),
        "subject": subject,
        "official_symbol": official_symbol,
        "query": query,
        "start": start,
        "end": end,
        "limit": min(max(int(limit), 1), MAX_RECORDS),
        "offset": max(int(offset), 0),
    }
    parameters = {key: value for key, value in parameters.items() if value not in (None, "")}
    try:
        records, meta, _ = _core_records_payload(settings, parameters)
        integration = _integration_state(settings)
    except RuntimeError as exc:
        records, meta = [], {}
        integration = _integration_state(settings, error=str(exc))
    pagination = meta.get("pagination") if isinstance(meta.get("pagination"), dict) else {}
    return {
        "ok": True,
        "schema": RECORDS_SCHEMA,
        "version": "2.3.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "integration": integration,
        "filters": parameters,
        "pagination": {
            "total": int(pagination.get("total") or len(records)),
            "limit": int(parameters.get("limit") or limit),
            "offset": int(parameters.get("offset") or 0),
            "returned": len(records),
        },
        "records": records,
    }


def _count_facets(records: Iterable[dict[str, Any]], field: str) -> list[dict[str, Any]]:
    values = Counter(str(item.get(field) or "") for item in records if item.get(field))
    return [{"id": key, "label": _AUTHORITY_LABELS.get(key, key.replace("_", " ").title()), "count": value} for key, value in values.most_common()]


def build_law_facets(settings: Any = None) -> dict[str, Any]:
    payload = build_law_records(settings, limit=MAX_RECORDS)
    records = payload["records"]
    countries = Counter(country for item in records for country in item.get("countries", []))
    subjects = Counter(subject for item in records for subject in item.get("subjects", []))
    bodies = Counter(item.get("legal_body") or item.get("issuing_body") for item in records if item.get("legal_body") or item.get("issuing_body"))
    return {
        "ok": True,
        "schema": "sc-site-intelligence-international-law-facets/1.0",
        "version": "2.3.0",
        "integration": payload["integration"],
        "record_types": _count_facets(records, "record_type"),
        "authority_levels": _count_facets(records, "authority_level"),
        "institution_families": _count_facets(records, "institution_family"),
        "legal_bodies": [{"id": key, "label": key, "count": value} for key, value in bodies.most_common()],
        "countries": [{"id": key, "label": key, "count": value} for key, value in countries.most_common()],
        "subjects": [{"id": key, "label": key, "count": value} for key, value in subjects.most_common(120)],
    }


def build_law_timeline(settings: Any = None, *, country: str = "", authority_level: str = "", record_type: str = "", limit: int = 160) -> dict[str, Any]:
    payload = build_law_records(
        settings,
        country=country,
        authority_level=authority_level,
        record_type=record_type,
        limit=min(max(limit, 1), MAX_TIMELINE_RECORDS),
    )
    records = sorted(payload["records"], key=lambda item: (_record_date(item), item.get("title") or ""))
    return {
        "ok": True,
        "schema": "sc-site-intelligence-international-law-timeline/1.0",
        "version": "2.3.0",
        "integration": payload["integration"],
        "filters": {"country": country, "authority_level": authority_level, "record_type": record_type},
        "events": [
            {
                "record_id": item["id"],
                "date": _record_date(item),
                "title": item["title"],
                "record_type": item["record_type"],
                "authority_level": item["authority_level"],
                "authority_label": item["authority_label"],
                "legal_body": item.get("legal_body") or item.get("issuing_body"),
                "official_symbol": item.get("official_symbol"),
                "legal_status": item.get("legal_status"),
                "source_url": item.get("canonical_source_url"),
            }
            for item in records
        ],
    }


def build_country_legal_profile(settings: Any = None, *, country: str, limit: int = 160) -> dict[str, Any]:
    country = country.strip().upper() if len(country.strip()) <= 3 else country.strip()
    if not country:
        raise ValueError("country is required.")
    payload = build_law_records(settings, country=country, limit=min(max(limit, 1), MAX_RECORDS))
    records = payload["records"]
    by_authority = Counter(item.get("authority_level") for item in records if item.get("authority_level"))
    by_body = Counter(item.get("legal_body") or item.get("issuing_body") for item in records if item.get("legal_body") or item.get("issuing_body"))
    subjects = Counter(subject for item in records for subject in item.get("subjects", []))
    return {
        "ok": True,
        "schema": "sc-site-intelligence-country-legal-profile/1.0",
        "version": "2.3.0",
        "integration": payload["integration"],
        "country": country,
        "counts": {"records": len(records), "authority_levels": len(by_authority), "legal_bodies": len(by_body), "subjects": len(subjects)},
        "by_authority": [{"id": key, "label": _AUTHORITY_LABELS.get(key, key.replace("_", " ").title()), "count": value} for key, value in by_authority.most_common()],
        "by_legal_body": [{"id": key, "label": key, "count": value} for key, value in by_body.most_common()],
        "top_subjects": [{"id": key, "label": key, "count": value} for key, value in subjects.most_common(20)],
        "latest_records": sorted(records, key=lambda item: _record_date(item), reverse=True)[:20],
        "interpretation": "Record presence shows official-source coverage associated with the selected country. It does not by itself establish treaty applicability, legal responsibility, compliance, or enforceability.",
    }


def build_authority_matrix(settings: Any = None, *, country: str = "", limit: int = MAX_RECORDS) -> dict[str, Any]:
    payload = build_law_records(settings, country=country, limit=min(max(limit, 1), MAX_RECORDS))
    matrix: dict[str, Counter[str]] = defaultdict(Counter)
    for item in payload["records"]:
        body = item.get("legal_body") or item.get("issuing_body") or "Unspecified body"
        matrix[body][item.get("authority_level") or "official_report"] += 1
    return {
        "ok": True,
        "schema": "sc-site-intelligence-legal-authority-matrix/1.0",
        "version": "2.3.0",
        "integration": payload["integration"],
        "country": country,
        "authority_levels": sorted({authority for counts in matrix.values() for authority in counts}),
        "rows": [
            {
                "legal_body": body,
                "total": sum(counts.values()),
                "counts": dict(counts),
            }
            for body, counts in sorted(matrix.items(), key=lambda item: (-sum(item[1].values()), item[0]))
        ],
        "warning": "Counts describe record coverage and authority classification. They are not a score of legal force, institutional importance, or country compliance.",
    }


def build_law_brief(settings: Any = None, *, country: str = "", authority_level: str = "", record_type: str = "", limit: int = 100) -> dict[str, Any]:
    payload = build_law_records(settings, country=country, authority_level=authority_level, record_type=record_type, limit=min(limit, 150))
    records = payload["records"]
    return {
        "ok": True,
        "schema": "sc-site-intelligence-international-law-brief/1.0",
        "version": "2.3.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "integration": payload["integration"],
        "scope": {"country": country, "authority_level": authority_level, "record_type": record_type},
        "summary": {
            "records_reviewed": len(records),
            "sources": sorted({item["source_id"] for item in records if item.get("source_id")}),
            "legal_bodies": sorted({item.get("legal_body") or item.get("issuing_body") for item in records if item.get("legal_body") or item.get("issuing_body")}),
            "authority_levels": dict(Counter(item.get("authority_level") for item in records if item.get("authority_level"))),
            "latest_records": sorted(records, key=lambda item: _record_date(item), reverse=True)[:12],
        },
        "method_note": "This deterministic brief organizes official-source records. It does not provide legal advice, determine binding effect, characterize compliance, or replace review of authoritative texts and procedural context.",
    }


def build_law_diagnostics(settings: Any = None) -> dict[str, Any]:
    overview = build_law_overview(settings)
    return {
        "ok": True,
        "schema": "sc-site-intelligence-international-law-diagnostics/1.0",
        "version": "2.3.0",
        "release_name": "International Law and Global Governance Observatory",
        "integration": overview["integration"],
        "counts": overview["counts"],
        "public_safety": {
            "legal_advice": False,
            "commercial_sanctions_screening": False,
            "automated_compliance_determinations": False,
            "automatic_binding_effect_inference": False,
            "browser_credential_exposure": False,
        },
        "registered_sources": SOURCES,
        "registered_monitors": MONITORS,
    }
