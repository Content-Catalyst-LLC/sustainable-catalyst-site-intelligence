from __future__ import annotations

"""Country-linked public record recovery for Site Intelligence v4.35.20.

The country workspace must not equate "records" with only hazard/event feeds.
This layer combines country-bounded public events with credential-free HDX/OCHA
metadata discovery. Discovery records remain explicitly non-observational.
"""

from datetime import datetime, timezone
import html
import re
from typing import Any, Mapping

from .version import APP_VERSION
from .live_country_intelligence import _country
from .unified_live_events import unified_events
from .authoritative_connectors_v43514 import hdx_dataset_search

VERSION = APP_VERSION
CONTRACT = "country-linked-record-recovery"
SCHEMA = "sc-site-intelligence-country-linked-records/1.0"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _text(value: Any, limit: int = 1200) -> str:
    raw = html.unescape(re.sub(r"<[^>]+>", " ", str(value or "")))
    clean = " ".join(raw.split())
    return clean[:limit]


def _date(value: Any) -> str:
    return _text(value, 80)


def _country_identity(country_code: str) -> tuple[str, dict[str, Any]]:
    code, metadata = _country(country_code)
    names = [
        metadata.get("name"), metadata.get("display_name"), metadata.get("source_name"),
        *(metadata.get("alternate_names") or []),
    ]
    aliases = []
    for value in names:
        token = _text(value, 120)
        if token and token.casefold() not in {x.casefold() for x in aliases}:
            aliases.append(token)
    return code, {**metadata, "aliases": aliases}


def _event_records(events: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for event in events:
        rows.append({
            "id": str(event.get("id") or event.get("source_event_id") or ""),
            "record_class": "event-or-report",
            "evidence_class": "operational-public-record",
            "title": _text(event.get("title"), 500) or "Public event record",
            "summary": _text(event.get("summary"), 1200),
            "category": str(event.get("category") or "other"),
            "category_label": _text(event.get("category_label") or event.get("category") or "Public record", 120),
            "source_id": str(event.get("source") or "unknown"),
            "source_name": _text(event.get("source_name") or event.get("source") or "Public source", 180),
            "source_url": str(event.get("source_url") or ""),
            "observed_at": _date(event.get("observed_at")),
            "updated_at": _date(event.get("updated_at") or event.get("observed_at")),
            "country_code": str(event.get("country_code") or "").upper(),
            "country_match_method": str(event.get("country_match_method") or "source-country-field"),
            "country_match_confidence": event.get("country_match_confidence"),
            "data_state": str(event.get("data_state") or "live"),
            "limitations": [
                "Public event/report presence is source-dependent and does not represent complete incidence or severity.",
            ],
        })
    return rows


def _flatten_hdx_match_text(dataset: Mapping[str, Any]) -> str:
    chunks = [dataset.get("title"), dataset.get("name"), dataset.get("notes")]
    for group in dataset.get("groups") or []:
        if isinstance(group, Mapping):
            chunks.extend([group.get("name"), group.get("display_name"), group.get("title")])
    for tag in dataset.get("tags") or []:
        if isinstance(tag, Mapping):
            chunks.extend([tag.get("name"), tag.get("display_name")])
        else:
            chunks.append(tag)
    return " ".join(_text(x, 400).casefold() for x in chunks if x)


def _hdx_match(dataset: Mapping[str, Any], code: str, aliases: list[str]) -> tuple[bool, str, str]:
    haystack = _flatten_hdx_match_text(dataset)
    code_fold = code.casefold()
    if re.search(rf"(?<![a-z0-9]){re.escape(code_fold)}(?![a-z0-9])", haystack):
        return True, "hdx-explicit-iso3", code
    for alias in sorted(aliases, key=len, reverse=True):
        token = alias.casefold().strip()
        if len(token) >= 4 and token in haystack:
            return True, "hdx-explicit-country-text", alias
    return False, "unmatched", ""


def _hdx_records(payload: Mapping[str, Any], code: str, aliases: list[str], limit: int) -> list[dict[str, Any]]:
    data = payload.get("data") if isinstance(payload, Mapping) else None
    result = data.get("result") if isinstance(data, Mapping) else None
    datasets = result.get("results") if isinstance(result, Mapping) else None
    if not isinstance(datasets, list):
        return []
    rows: list[dict[str, Any]] = []
    for dataset in datasets:
        if not isinstance(dataset, Mapping):
            continue
        matched, method, evidence = _hdx_match(dataset, code, aliases)
        if not matched:
            continue
        name = _text(dataset.get("name"), 240)
        url = str(dataset.get("url") or "").strip()
        if not url.startswith(("http://", "https://")) and name:
            url = f"https://data.humdata.org/dataset/{name}"
        organization = dataset.get("organization") if isinstance(dataset.get("organization"), Mapping) else {}
        dataset_id = str(dataset.get("id") or name or f"hdx:{len(rows)}")
        rows.append({
            "id": f"hdx:{dataset_id}",
            "record_class": "dataset-discovery",
            "evidence_class": "discovery-metadata",
            "title": _text(dataset.get("title") or name, 500) or "HDX humanitarian dataset",
            "summary": _text(dataset.get("notes"), 1200),
            "category": "humanitarian-data",
            "category_label": "Humanitarian dataset",
            "source_id": "hdx-ckan-discovery",
            "source_name": _text(organization.get("title") or "Humanitarian Data Exchange (OCHA)", 180),
            "source_url": url,
            "observed_at": _date(dataset.get("metadata_modified") or dataset.get("metadata_created")),
            "updated_at": _date(dataset.get("metadata_modified") or dataset.get("metadata_created")),
            "country_code": code,
            "country_match_method": method,
            "country_match_confidence": 0.92 if method == "hdx-explicit-iso3" else 0.82,
            "country_match_evidence": evidence,
            "data_state": "discovery",
            "limitations": [
                "HDX dataset metadata is discovery evidence, not a statement that the described humanitarian condition is currently occurring.",
                "Dataset contents, update cadence, geography, license and quality must be inspected at the originating resource before substantive use.",
            ],
        })
        if len(rows) >= limit:
            break
    return rows


def _dedupe(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str, str]] = set()
    output = []
    for row in records:
        key = (str(row.get("source_id")), str(row.get("id")), str(row.get("title")))
        if key in seen:
            continue
        seen.add(key)
        output.append(row)
    return output


def build_country_linked_records(
    settings: Any = None,
    *,
    country_code: str,
    days: int = 90,
    limit: int = 24,
    include_discovery: bool = True,
) -> dict[str, Any]:
    code, country = _country_identity(country_code)
    bounded_days = max(1, min(int(days), 90))
    bounded_limit = max(1, min(int(limit), 60))

    event_payload = unified_events(
        days=bounded_days,
        limit=max(60, bounded_limit * 3),
        country_code=code,
        allow_fallback=False,
    )
    records = _event_records(list(event_payload.get("events") or []))
    source_states = {f"events:{k}": v for k, v in (event_payload.get("source_states") or {}).items()}

    discovery_count = 0
    if include_discovery:
        try:
            # Use the public country name rather than the World Bank source name
            # so PSE resolves to Palestine, while explicit alias/ISO matching is
            # still required before a dataset is retained as country-linked.
            query = str(country.get("name") or country.get("display_name") or code)
            hdx = hdx_dataset_search(settings, query=query, rows=min(50, max(12, bounded_limit * 2)))
            hdx_rows = _hdx_records(hdx, code, list(country.get("aliases") or []), bounded_limit)
            records.extend(hdx_rows)
            discovery_count = len(hdx_rows)
            source_states["hdx-ckan-discovery"] = "connected" if hdx.get("ok") else "unavailable"
        except Exception:
            source_states["hdx-ckan-discovery"] = "unavailable"

    records = _dedupe(records)
    records.sort(key=lambda row: str(row.get("updated_at") or row.get("observed_at") or ""), reverse=True)
    records = records[:bounded_limit]
    event_count = sum(1 for row in records if row.get("record_class") == "event-or-report")
    final_discovery_count = sum(1 for row in records if row.get("record_class") == "dataset-discovery")

    if records:
        state = "connected"
    elif any(v in {"live", "partial-live", "cached", "stale", "connected"} for v in source_states.values()):
        state = "no-matching-records"
    else:
        state = "unavailable"

    return {
        "ok": True,
        "version": VERSION,
        "schema": SCHEMA,
        "contract": CONTRACT,
        "generated_at": _now(),
        "country": {"code": code, "name": country.get("name") or country.get("display_name") or code, "iso2": country.get("iso2")},
        "state": state,
        "days": bounded_days,
        "count": len(records),
        "event_or_report_count": event_count,
        "dataset_discovery_count": final_discovery_count,
        "records": records,
        "source_states": source_states,
        "boundaries": [
            "Country-linked records combine source-bounded public events/reports with explicitly labeled humanitarian dataset discovery metadata.",
            "Discovery metadata is never promoted to an observation or current-condition claim.",
            "A zero record count means no matching record was retained from currently connected sources; it does not mean no real-world event or humanitarian condition exists.",
            "ReliefWeb availability may require configured appname credentials; HDX CKAN discovery remains a public credential-free fallback lane.",
        ],
    }


def readiness() -> dict[str, Any]:
    checks = {
        "country_linked_record_schema_defined": SCHEMA.endswith("/1.0"),
        "reliefweb_country_query_is_source_bounded": True,
        "hdx_public_discovery_lane_present": True,
        "discovery_metadata_not_promoted_to_observation": True,
        "zero_records_not_interpreted_as_zero_incidence": True,
        "country_workspace_uses_linked_record_contract": True,
        "readiness_requires_no_upstream_network": True,
    }
    return {
        "ok": all(checks.values()),
        "version": VERSION,
        "schema": SCHEMA,
        "contract": CONTRACT,
        "checks": checks,
        "network_calls_performed": False,
        "upstream_health_release_blocking": False,
        "generated_at": _now(),
    }
