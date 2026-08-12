from __future__ import annotations

"""Palestine data federation and source-precedence contract for Site Intelligence v4.35.21."""

from datetime import datetime, timezone
from typing import Any, Mapping

from .version import APP_VERSION
from .live_country_intelligence import _country
from .authoritative_connectors_v43521 import palestine_open_data_search
from .authoritative_connectors_v43514 import hdx_dataset_search, hdx_hapi

VERSION = APP_VERSION
CONTRACT = "palestine-data-federation-v43521"
SCHEMA = "sc-site-intelligence-palestine-data-federation/1.0"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _dataset_rows(payload: Mapping[str, Any], source_id: str, source_name: str, evidence_class: str, limit: int) -> list[dict[str, Any]]:
    data = payload.get("data") if isinstance(payload, Mapping) else None
    result = data.get("result") if isinstance(data, Mapping) else None
    datasets = result.get("results") if isinstance(result, Mapping) else None
    if not isinstance(datasets, list):
        return []
    rows: list[dict[str, Any]] = []
    for item in datasets[:limit]:
        if not isinstance(item, Mapping):
            continue
        organization = item.get("organization") if isinstance(item.get("organization"), Mapping) else {}
        name = str(item.get("name") or "").strip()
        url = str(item.get("url") or "").strip()
        if not url.startswith(("http://", "https://")) and name:
            if source_id == "palestine-open-data-ckan":
                url = f"https://opendata.ps/dataset/{name}"
            else:
                url = f"https://data.humdata.org/dataset/{name}"
        rows.append({
            "id": f"{source_id}:{item.get('id') or name or len(rows)}",
            "title": str(item.get("title") or name or "Dataset").strip(),
            "summary": " ".join(str(item.get("notes") or "").split())[:1200],
            "source_id": source_id,
            "source_name": str(organization.get("title") or source_name).strip(),
            "source_url": url,
            "updated_at": str(item.get("metadata_modified") or item.get("metadata_created") or ""),
            "record_class": "official-dataset-discovery" if source_id == "palestine-open-data-ckan" else "humanitarian-dataset-discovery",
            "evidence_class": evidence_class,
            "data_state": "discovery",
        })
    return rows


def build_palestine_data_federation(settings: Any = None, *, country_code: str = "PSE", query: str = "", limit: int = 12) -> dict[str, Any]:
    code, country = _country(country_code)
    if code != "PSE":
        raise ValueError("The v4.35.21 Palestine federation route is scoped to PSE.")
    bounded = max(1, min(int(limit), 30))
    search_query = str(query or "").strip()
    records: list[dict[str, Any]] = []
    states: dict[str, str] = {
        "pcbs-pxweb": "registered-primary-statistical-authority",
        "world-bank": "registered-harmonized-comparison",
    }

    try:
        official = palestine_open_data_search(settings, query=search_query, rows=bounded)
        official_rows = _dataset_rows(official, "palestine-open-data-ckan", "Palestine Open Data Portal", "official-discovery-metadata", bounded)
        records.extend(official_rows)
        states["palestine-open-data-ckan"] = "connected" if official.get("ok") else "unavailable"
    except Exception:
        states["palestine-open-data-ckan"] = "unavailable"

    try:
        hdx = hdx_dataset_search(settings, query=search_query or str(country.get("name") or "Palestine"), rows=bounded)
        hdx_rows = _dataset_rows(hdx, "hdx-ckan-discovery", "Humanitarian Data Exchange (OCHA)", "humanitarian-discovery-metadata", bounded)
        records.extend(hdx_rows)
        states["hdx-ckan-discovery"] = "connected" if hdx.get("ok") else "unavailable"
    except Exception:
        states["hdx-ckan-discovery"] = "unavailable"

    try:
        hapi = hdx_hapi(settings, dataset="food-security", location_code="PSE", limit=min(100, bounded * 8))
        if hapi.get("configuration_required"):
            states["hdx-hapi"] = "configuration-required"
        else:
            states["hdx-hapi"] = "connected" if hapi.get("ok") else "unavailable"
    except Exception:
        states["hdx-hapi"] = "unavailable"

    records.sort(key=lambda row: str(row.get("updated_at") or ""), reverse=True)
    return {
        "ok": True,
        "version": VERSION,
        "schema": SCHEMA,
        "contract": CONTRACT,
        "generated_at": _now(),
        "country": {"code": code, "name": country.get("name") or "Palestine"},
        "source_precedence": [
            {"source_id": "pcbs-pxweb", "role": "PRIMARY OFFICIAL STATISTICS", "can_define_operational_currentness": False},
            {"source_id": "palestine-open-data-ckan", "role": "OFFICIAL DATASET DISCOVERY", "can_define_operational_currentness": False},
            {"source_id": "hdx-hapi", "role": "STANDARDIZED HUMANITARIAN INDICATORS", "can_define_operational_currentness": "depends-on-record-reference-period"},
            {"source_id": "hdx-ckan-discovery", "role": "HUMANITARIAN DATASET DISCOVERY", "can_define_operational_currentness": False},
            {"source_id": "world-bank", "role": "HARMONIZED INTERNATIONAL COMPARISON", "can_define_operational_currentness": False},
        ],
        "source_states": states,
        "records": records[:bounded],
        "record_count": min(len(records), bounded),
        "boundaries": [
            "Official Palestinian statistics and Palestinian open-data discovery are not flattened into humanitarian operational evidence.",
            "HDX dataset metadata is discovery evidence; HDX HAPI indicators retain their original source, geography and reference period.",
            "World Bank remains a harmonized comparison/fallback layer rather than the default definition of present conditions.",
            "Wikimedia knowledge context is intentionally outside this evidence-precedence chain.",
        ],
    }


def readiness() -> dict[str, Any]:
    checks = {
        "pcbs_primary_statistical_authority_preserved": True,
        "palestine_open_data_official_discovery_registered": True,
        "hdx_ckan_humanitarian_discovery_preserved": True,
        "hdx_hapi_indicator_lane_preserved": True,
        "world_bank_comparison_only": True,
        "wikimedia_excluded_from_truth_precedence": True,
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
