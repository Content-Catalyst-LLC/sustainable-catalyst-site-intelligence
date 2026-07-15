"""Unified Country and Regional Intelligence Dossiers for Site Intelligence v2.7.0.

This module composes existing public Site Intelligence workspaces into one
source-aware country or regional dossier. It preserves each domain's source
identity, reporting state, dates, units, authority categories, and responsible-
use boundaries. It does not create a composite country score, ranking, causal
claim, legal conclusion, humanitarian priority, or national-security rating.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
import os
from typing import Any, Callable, Mapping

from .live_country_intelligence import country_catalog, country_profile, country_regions

RELEASE_SCHEMA = "sc-site-intelligence-unified-dossiers/1.0"
COUNTRY_SCHEMA = "sc-site-intelligence-country-dossier/1.0"
REGION_SCHEMA = "sc-site-intelligence-regional-dossier/1.0"
COMPARISON_SCHEMA = "sc-site-intelligence-dossier-comparison/1.0"
VERSION = "2.7.0"
MAX_DOMAIN_RECORDS = 60

DOMAIN_LABELS = {
    "baseline": "Country indicators and trends",
    "conditions": "Global conditions and live observations",
    "economics": "Economics, markets, and sustainability",
    "law": "International law and governance",
    "science": "Scientific and Earth systems",
    "humanitarian": "Humanitarian, conflict, and displacement",
    "resources": "Trade, energy, and resources",
}

EVIDENCE_CLASSES = {
    "current_condition": "Current condition",
    "historical_trend": "Historical trend",
    "official_statistic": "Official statistic",
    "forecast": "Forecast",
    "legal_record": "Legal record",
    "humanitarian_report": "Humanitarian report",
    "scientific_observation": "Scientific observation",
    "derived_analysis": "Derived Sustainable Catalyst analysis",
}

@dataclass(frozen=True)
class DossierConfig:
    enabled: bool
    max_records_per_domain: int


def _as_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on", "enabled"}


def dossier_config(settings: Any = None) -> DossierConfig:
    enabled = getattr(settings, "unified_dossiers_enabled", None)
    if enabled is None:
        enabled = os.getenv("SC_SI_UNIFIED_DOSSIERS_ENABLED", "true")
    limit = getattr(settings, "unified_dossiers_max_records_per_domain", None)
    if limit is None:
        limit = os.getenv("SC_SI_UNIFIED_DOSSIERS_MAX_RECORDS_PER_DOMAIN", "40")
    return DossierConfig(_as_bool(enabled, True), max(5, min(int(limit), MAX_DOMAIN_RECORDS)))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _catalog() -> dict[str, Any]:
    payload = country_catalog()
    return payload if isinstance(payload, dict) else {"countries": [], "data_state": "unavailable"}


def _country(code: str) -> dict[str, Any]:
    token = str(code or "").strip().upper()
    match = next(
        (
            item
            for item in _catalog().get("countries", [])
            if str(item.get("code") or "").upper() == token
            or str(item.get("iso2") or "").upper() == token
        ),
        None,
    )
    if not match:
        raise ValueError("unsupported_country")
    return dict(match)


def _regions() -> list[dict[str, Any]]:
    payload = country_regions()
    return list(payload.get("regions") or []) if isinstance(payload, dict) else []


def _region_countries(region: str) -> list[dict[str, Any]]:
    wanted = str(region or "").strip().casefold()
    if not wanted:
        raise ValueError("region is required")
    countries = [
        dict(item)
        for item in _catalog().get("countries", [])
        if str(item.get("region") or "Unclassified").strip().casefold() == wanted
    ]
    if not countries:
        raise ValueError("unsupported_region")
    return sorted(countries, key=lambda item: str(item.get("name") or item.get("code") or ""))


def _state(payload: Mapping[str, Any]) -> str:
    integration = payload.get("integration")
    if isinstance(integration, Mapping) and integration.get("state"):
        return str(integration.get("state"))
    for key in ("state", "data_state", "status"):
        value = payload.get(key)
        if value:
            return str(value)
    return "unavailable"


def _records(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    for key in ("records", "features", "indicators", "highlights"):
        rows = payload.get(key)
        if isinstance(rows, list):
            return [dict(row) for row in rows if isinstance(row, Mapping)]
    return []


def _sources(rows: list[dict[str, Any]]) -> list[str]:
    values = set()
    for row in rows:
        for key in ("source_id", "source", "attribution"):
            value = row.get(key)
            if isinstance(value, str) and value.strip():
                values.add(value.strip())
                break
    return sorted(values)


def _date_value(row: Mapping[str, Any]) -> str:
    for key in ("observed_at", "published_at", "date", "period", "display_date", "observation_start", "year"):
        value = row.get(key)
        if value not in (None, ""):
            return str(value)
    latest = row.get("latest")
    if isinstance(latest, Mapping) and latest.get("year") is not None:
        return str(latest.get("year"))
    return ""


def _title(row: Mapping[str, Any]) -> str:
    for key in ("title", "indicator_name", "label", "summary", "record_type_label", "metric"):
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()[:500]
    return "Public evidence record"


def _value(row: Mapping[str, Any]) -> dict[str, Any] | None:
    latest = row.get("latest")
    if isinstance(latest, Mapping) and latest.get("value") is not None:
        return {"value": latest.get("value"), "unit": row.get("unit") or latest.get("unit") or "", "period": latest.get("year")}
    for key in ("value_number", "value", "value_text"):
        if row.get(key) not in (None, ""):
            return {"value": row.get(key), "unit": row.get("unit") or "", "period": _date_value(row)}
    return None


def _sample(domain: str, rows: list[dict[str, Any]], limit: int = 8) -> list[dict[str, Any]]:
    items = []
    for row in rows[: max(0, limit)]:
        items.append(
            {
                "domain": domain,
                "id": str(row.get("id") or row.get("record_id") or row.get("source_record_id") or "")[:220],
                "title": _title(row),
                "record_type": str(row.get("record_type") or row.get("family") or row.get("category") or domain)[:120],
                "source_id": str(row.get("source_id") or row.get("source") or "")[:180],
                "date": _date_value(row)[:80],
                "status": str(row.get("status") or row.get("data_state") or row.get("quality_label") or "")[:100],
                "value": _value(row),
                "source_url": str(row.get("source_url") or row.get("landing_page_url") or row.get("access_url") or "")[:1000],
            }
        )
    return items


def _domain_payload(domain: str, payload: Mapping[str, Any], *, sample_limit: int = 8, interpretation: str = "") -> dict[str, Any]:
    rows = _records(payload)
    sources = _sources(rows)
    return {
        "id": domain,
        "label": DOMAIN_LABELS[domain],
        "state": _state(payload),
        "record_count": len(rows),
        "source_count": len(sources),
        "sources": sources,
        "sample_records": _sample(domain, rows, sample_limit),
        "interpretation": interpretation,
    }


def _safe_call(domain: str, func: Callable[[], Mapping[str, Any]], *, interpretation: str, sample_limit: int) -> dict[str, Any]:
    try:
        payload = func()
        if not isinstance(payload, Mapping):
            raise RuntimeError("invalid domain response")
        return _domain_payload(domain, payload, sample_limit=sample_limit, interpretation=interpretation)
    except Exception as exc:
        return {
            "id": domain,
            "label": DOMAIN_LABELS[domain],
            "state": "unavailable",
            "record_count": 0,
            "source_count": 0,
            "sources": [],
            "sample_records": [],
            "interpretation": interpretation,
            "message": str(exc)[:300],
        }


def _bbox(country: Mapping[str, Any]) -> str:
    try:
        lat = float(country.get("latitude"))
        lng = float(country.get("longitude"))
    except (TypeError, ValueError):
        return ""
    return f"{lng - 5:.4f},{lat - 5:.4f},{lng + 5:.4f},{lat + 5:.4f}"


def _country_domains(settings: Any, country: Mapping[str, Any], limit: int) -> dict[str, dict[str, Any]]:
    from .economics_markets_sustainability import build_economic_records
    from .global_conditions_observatory import build_global_conditions_features
    from .humanitarian_conflict_displacement_observatory import build_country_profile as build_humanitarian_profile
    from .international_law_observatory import build_law_records
    from .scientific_earth_systems_observatory import build_science_records
    from .trade_energy_resource_security_observatory import build_country_profile as build_resource_profile

    code = str(country.get("code") or "").upper()
    name = str(country.get("name") or code)
    baseline = _safe_call(
        "baseline",
        lambda: country_profile(code),
        interpretation="Indicators retain their original reporting years, units, source states, and missing values.",
        sample_limit=limit,
    )
    conditions = _safe_call(
        "conditions",
        lambda: build_global_conditions_features(settings, bbox=_bbox(country), domain="", source_id="", connector_id="", observed_after="", limit=limit),
        interpretation="Mapped observations near a country centroid do not imply complete national coverage or current ground conditions.",
        sample_limit=limit,
    )
    economics = _safe_call(
        "economics",
        lambda: build_economic_records(settings, geography_code=code, limit=limit),
        interpretation="Official statistics may use different frequencies, vintages, units, price bases, and geographic definitions.",
        sample_limit=limit,
    )
    law = _safe_call(
        "law",
        lambda: build_law_records(settings, country=code, limit=limit),
        interpretation="Record presence does not establish legal effect, compliance, responsibility, or enforceability.",
        sample_limit=limit,
    )
    science = _safe_call(
        "science",
        lambda: build_science_records(settings, query=name, limit=limit),
        interpretation="Country-name discovery is metadata search, not proof that every scientific record has national geographic coverage.",
        sample_limit=limit,
    )
    humanitarian = _safe_call(
        "humanitarian",
        lambda: build_humanitarian_profile(settings, country=code, limit=limit),
        interpretation="Public humanitarian records are incomplete and do not determine severity, responsibility, eligibility, or operational priority.",
        sample_limit=limit,
    )
    resources = _safe_call(
        "resources",
        lambda: build_resource_profile(settings, country=code, limit=limit),
        interpretation="Trade and resource coverage is not a dependency, resilience, vulnerability, sanctions, or national-security score.",
        sample_limit=limit,
    )
    return {
        "baseline": baseline,
        "conditions": conditions,
        "economics": economics,
        "law": law,
        "science": science,
        "humanitarian": humanitarian,
        "resources": resources,
    }


def _dossier_state(domains: Mapping[str, Mapping[str, Any]]) -> str:
    states = [str(item.get("state") or "unavailable") for item in domains.values()]
    counts = [int(item.get("record_count") or 0) for item in domains.values()]
    if not any(counts):
        return "unavailable"
    if all(state in {"connected", "live", "partial-live", "cached", "reference-snapshot"} for state in states):
        return "connected"
    return "degraded"


def _coverage(domains: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "domain": key,
            "label": DOMAIN_LABELS[key],
            "state": value.get("state") or "unavailable",
            "record_count": int(value.get("record_count") or 0),
            "source_count": int(value.get("source_count") or 0),
        }
        for key, value in domains.items()
    ]


def build_country_dossier(settings: Any = None, *, country: str, limit_per_domain: int | None = None) -> dict[str, Any]:
    config = dossier_config(settings)
    if not config.enabled:
        return {"ok": True, "schema": COUNTRY_SCHEMA, "version": VERSION, "generated_at": _now(), "state": "disabled", "domains": {}, "coverage": []}
    country_meta = _country(country)
    limit = max(5, min(int(limit_per_domain or config.max_records_per_domain), MAX_DOMAIN_RECORDS))
    domains = _country_domains(settings, country_meta, limit)
    samples = [record for domain in domains.values() for record in domain.get("sample_records", [])]
    sources = sorted({source for domain in domains.values() for source in domain.get("sources", []) if source})
    return {
        "ok": True,
        "schema": COUNTRY_SCHEMA,
        "version": VERSION,
        "generated_at": _now(),
        "state": _dossier_state(domains),
        "country": country_meta,
        "counts": {
            "domains": len(domains),
            "domains_with_records": sum(1 for item in domains.values() if item.get("record_count")),
            "evidence_records": sum(int(item.get("record_count") or 0) for item in domains.values()),
            "sources": len(sources),
        },
        "coverage": _coverage(domains),
        "domains": domains,
        "evidence_classes": [{"id": key, "label": label} for key, label in EVIDENCE_CLASSES.items()],
        "evidence_samples": samples,
        "source_ids": sources,
        "boundaries": [
            "The dossier is a cross-domain evidence organizer, not a country score or ranking.",
            "Domains retain different dates, units, methods, geographic definitions, and levels of authority.",
            "Record absence does not establish that a condition, obligation, event, or risk is absent.",
            "This public research product is not legal, financial, medical, engineering, emergency-response, sanctions, or national-security advice.",
        ],
    }


def _row_country_codes(row: Mapping[str, Any]) -> set[str]:
    values: set[str] = set()
    for key in ("geography_code", "country_code", "counterpart_code"):
        value = row.get(key)
        if isinstance(value, str) and 2 <= len(value.strip()) <= 3:
            values.add(value.strip().upper())
    countries = row.get("countries")
    if isinstance(countries, list):
        values.update(str(value).strip().upper() for value in countries if 2 <= len(str(value).strip()) <= 3)
    return values


def _region_domain(domain: str, payload: Mapping[str, Any], member_codes: set[str], interpretation: str, limit: int) -> dict[str, Any]:
    rows = _records(payload)
    filtered = [row for row in rows if _row_country_codes(row) & member_codes]
    local = dict(payload)
    local["records"] = filtered
    local.pop("features", None)
    return _domain_payload(domain, local, sample_limit=limit, interpretation=interpretation)


def build_regional_dossier(settings: Any = None, *, region: str, limit_per_domain: int | None = None) -> dict[str, Any]:
    config = dossier_config(settings)
    if not config.enabled:
        return {"ok": True, "schema": REGION_SCHEMA, "version": VERSION, "generated_at": _now(), "state": "disabled", "domains": {}, "coverage": []}
    members = _region_countries(region)
    codes = {str(item.get("code") or "").upper() for item in members}
    limit = max(5, min(int(limit_per_domain or config.max_records_per_domain), MAX_DOMAIN_RECORDS))

    from .economics_markets_sustainability import build_economic_records
    from .humanitarian_conflict_displacement_observatory import build_records as build_humanitarian_records
    from .international_law_observatory import build_law_records
    from .scientific_earth_systems_observatory import build_science_records
    from .trade_energy_resource_security_observatory import build_records as build_resource_records

    domains: dict[str, dict[str, Any]] = {}
    domains["baseline"] = {
        "id": "baseline", "label": DOMAIN_LABELS["baseline"], "state": _catalog().get("data_state") or "available",
        "record_count": len(members), "source_count": 1, "sources": ["Site Intelligence country catalog"],
        "sample_records": [
            {"domain": "baseline", "id": item.get("code"), "title": item.get("name"), "record_type": "country", "source_id": "country-catalog", "date": "", "status": "catalog", "value": None, "source_url": ""}
            for item in members[:limit]
        ],
        "interpretation": "Regional membership follows the current country catalog and does not imply political, legal, economic, or cultural uniformity.",
    }
    domains["economics"] = _region_domain("economics", build_economic_records(settings, limit=300), codes, "Regional record counts are coverage summaries; incompatible values are not added together.", limit)
    domains["law"] = _region_domain("law", build_law_records(settings, limit=300), codes, "Regional legal records retain their distinct authority, parties, procedural status, and source context.", limit)
    domains["science"] = _domain_payload("science", build_science_records(settings, query=region, limit=limit), sample_limit=limit, interpretation="Region-name scientific discovery is metadata search and may not represent complete geographic coverage.")
    domains["humanitarian"] = _region_domain("humanitarian", build_humanitarian_records(settings, limit=300, include_hazards=True), codes, "Regional humanitarian evidence is incomplete and is not an operational prioritization or severity score.", limit)
    domains["resources"] = _region_domain("resources", build_resource_records(settings, limit=300), codes, "Trade, energy, water, food, and materials records remain unit- and direction-specific and are not aggregated into a security score.", limit)
    domains["conditions"] = {
        "id": "conditions", "label": DOMAIN_LABELS["conditions"], "state": "available", "record_count": 0,
        "source_count": 0, "sources": [], "sample_records": [],
        "interpretation": "Regional live conditions are available through the Global Conditions and Scientific workspaces; this dossier does not infer a single regional condition.",
    }
    sources = sorted({source for domain in domains.values() for source in domain.get("sources", []) if source})
    return {
        "ok": True,
        "schema": REGION_SCHEMA,
        "version": VERSION,
        "generated_at": _now(),
        "state": _dossier_state(domains),
        "region": str(region).strip(),
        "countries": members,
        "country_codes": sorted(codes),
        "counts": {
            "countries": len(members),
            "domains": len(domains),
            "domains_with_records": sum(1 for item in domains.values() if item.get("record_count")),
            "evidence_records": sum(int(item.get("record_count") or 0) for item in domains.values()),
            "sources": len(sources),
        },
        "coverage": _coverage(domains),
        "domains": domains,
        "source_ids": sources,
        "boundaries": [
            "The regional dossier reports source coverage and selected records; it does not calculate a regional score or ranking.",
            "Countries within a named region can use different definitions, reporting periods, classifications, and data availability.",
            "Regional membership is a catalog convention and is not a statement about sovereignty, recognition, identity, or institutional membership.",
        ],
    }


def _aligned_indicators(left: Mapping[str, Any], right: Mapping[str, Any]) -> list[dict[str, Any]]:
    def mapping(payload: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
        baseline = payload.get("domains", {}).get("baseline", {}) if isinstance(payload.get("domains"), Mapping) else {}
        samples = baseline.get("sample_records", []) if isinstance(baseline, Mapping) else []
        return {str(row.get("id") or row.get("title")): row for row in samples if isinstance(row, Mapping)}
    a, b = mapping(left), mapping(right)
    keys = sorted(set(a) | set(b))
    return [{"indicator": key, "country_a": a.get(key), "country_b": b.get(key), "difference_calculated": False} for key in keys[:20]]


def build_dossier_comparison(settings: Any = None, *, country_a: str, country_b: str, limit_per_domain: int = 12) -> dict[str, Any]:
    left = build_country_dossier(settings, country=country_a, limit_per_domain=limit_per_domain)
    right = build_country_dossier(settings, country=country_b, limit_per_domain=limit_per_domain)
    left_cov = {item["domain"]: item for item in left.get("coverage", [])}
    right_cov = {item["domain"]: item for item in right.get("coverage", [])}
    matrix = [
        {
            "domain": domain,
            "label": DOMAIN_LABELS[domain],
            "country_a": left_cov.get(domain, {"state": "unavailable", "record_count": 0, "source_count": 0}),
            "country_b": right_cov.get(domain, {"state": "unavailable", "record_count": 0, "source_count": 0}),
        }
        for domain in DOMAIN_LABELS
    ]
    return {
        "ok": True,
        "schema": COMPARISON_SCHEMA,
        "version": VERSION,
        "generated_at": _now(),
        "country_a": left.get("country"),
        "country_b": right.get("country"),
        "coverage_matrix": matrix,
        "aligned_indicators": _aligned_indicators(left, right),
        "methodology": {
            "ranking_created": False,
            "composite_score_created": False,
            "silent_normalization": False,
            "differences_calculated": False,
            "statement": "The comparison aligns coverage and selected evidence without subtracting incompatible values or assigning a winner.",
        },
    }


def build_dossier_facets(settings: Any = None) -> dict[str, Any]:
    config = dossier_config(settings)
    catalog = _catalog()
    return {
        "ok": True,
        "schema": RELEASE_SCHEMA,
        "version": VERSION,
        "enabled": config.enabled,
        "countries": catalog.get("countries", []),
        "regions": _regions(),
        "domains": [{"id": key, "label": label} for key, label in DOMAIN_LABELS.items()],
        "evidence_classes": [{"id": key, "label": label} for key, label in EVIDENCE_CLASSES.items()],
    }


def build_dossier_overview(settings: Any = None) -> dict[str, Any]:
    config = dossier_config(settings)
    catalog = _catalog()
    return {
        "ok": True,
        "schema": RELEASE_SCHEMA,
        "version": VERSION,
        "release_name": "Unified Country and Regional Intelligence Dossiers",
        "generated_at": _now(),
        "state": "ready" if config.enabled else "disabled",
        "counts": {"countries": len(catalog.get("countries", [])), "regions": len(_regions()), "domains": len(DOMAIN_LABELS)},
        "domains": [{"id": key, "label": label} for key, label in DOMAIN_LABELS.items()],
        "principles": [
            "One dossier preserves multiple evidence classes rather than collapsing them into a score.",
            "Original units, reporting periods, legal authority categories, source states, and uncertainty remain visible.",
            "Country and regional coverage describes available records, not completeness, performance, risk, or responsibility.",
        ],
        "paid_provider_required": False,
    }


def build_dossier_brief(settings: Any = None, *, country: str = "", region: str = "", limit_per_domain: int = 10) -> dict[str, Any]:
    if bool(country) == bool(region):
        raise ValueError("Provide exactly one of country or region")
    dossier = build_country_dossier(settings, country=country, limit_per_domain=limit_per_domain) if country else build_regional_dossier(settings, region=region, limit_per_domain=limit_per_domain)
    subject = dossier.get("country", {}).get("name") if country else dossier.get("region")
    return {
        "ok": True,
        "schema": "sc-site-intelligence-dossier-brief/1.0",
        "version": VERSION,
        "generated_at": _now(),
        "title": f"{subject} — Unified Intelligence Dossier",
        "state": dossier.get("state"),
        "subject": dossier.get("country") if country else {"region": dossier.get("region"), "countries": dossier.get("country_codes", [])},
        "coverage": dossier.get("coverage", []),
        "evidence_samples": [record for domain in dossier.get("domains", {}).values() for record in domain.get("sample_records", [])][:80],
        "source_ids": dossier.get("source_ids", []),
        "limitations": dossier.get("boundaries", []),
    }


def build_dossier_diagnostics(settings: Any = None) -> dict[str, Any]:
    config = dossier_config(settings)
    return {
        "ok": True,
        "schema": RELEASE_SCHEMA,
        "version": VERSION,
        "enabled": config.enabled,
        "catalog_state": _catalog().get("data_state") or "unavailable",
        "credential_exposed": False,
        "fabricated_records": False,
        "composite_score": False,
        "country_ranking": False,
        "causal_inference": False,
        "legal_determination": False,
        "humanitarian_priority": False,
        "national_security_rating": False,
        "routes": [
            "/public/intelligence-dossiers",
            "/public/intelligence-dossiers/facets",
            "/public/intelligence-dossiers/country",
            "/public/intelligence-dossiers/region",
            "/public/intelligence-dossiers/compare",
            "/public/intelligence-dossiers/brief",
        ],
    }
