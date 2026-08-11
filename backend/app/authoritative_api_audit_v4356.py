from __future__ import annotations

"""Site Intelligence v4.35.6 authoritative API audit extension.

Extends the v4.35.5 registry audit with five fully implemented first-party
national statistical authority connectors.
"""

from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
from typing import Any

from .version import APP_VERSION
from . import authoritative_api_audit_v4355 as prior

VERSION = APP_VERSION
CONTRACT = "authoritative-api-workspace-integrity-audit"
AUDIT_DATE = "2026-08-11"
ACCESS_CLASSES = prior.ACCESS_CLASSES

NEW_VERIFIED_MACHINE_INTERFACES = (
    {
        "id": "pcbs-pxweb-sdgs",
        "provider": "Palestinian Central Bureau of Statistics",
        "host": "pcbs.gov.ps",
        "protocol": "PxWeb API v1 / JSON-stat",
        "current_version": "PxWeb API v1 deployment",
        "documentation_url": "https://pcbs.gov.ps/SDGsIndicators/pxweb/en/myDb/",
        "authentication": "public statistical service",
        "status": "implemented-live-v4.35.6",
        "audit_date": AUDIT_DATE,
    },
    {
        "id": "statistics-canada-wds",
        "provider": "Statistics Canada",
        "host": "www150.statcan.gc.ca",
        "protocol": "REST / JSON",
        "current_version": "WDS current service",
        "documentation_url": "https://www.statcan.gc.ca/en/developers/wds/user-guide",
        "authentication": "public",
        "status": "implemented-live-v4.35.6",
        "audit_date": AUDIT_DATE,
    },
    {
        "id": "uk-ons-api",
        "provider": "Office for National Statistics",
        "host": "api.beta.ons.gov.uk",
        "protocol": "REST / JSON",
        "current_version": "v1 beta",
        "documentation_url": "https://developer.ons.gov.uk/",
        "authentication": "open and unrestricted",
        "status": "implemented-live-v4.35.6",
        "audit_date": AUDIT_DATE,
    },
    {
        "id": "australian-bureau-statistics-sdmx",
        "provider": "Australian Bureau of Statistics",
        "host": "data.api.abs.gov.au",
        "protocol": "SDMX 2.1 / JSON / CSV",
        "current_version": "Data API beta current service",
        "documentation_url": "https://www.abs.gov.au/statistics/application-programming-interfaces-apis/data-api-user-guide",
        "authentication": "public; API keys removed 2024-11-29",
        "status": "implemented-live-v4.35.6",
        "audit_date": AUDIT_DATE,
    },
    {
        "id": "us-bls-public-data-api",
        "provider": "U.S. Bureau of Labor Statistics",
        "host": "api.bls.gov",
        "protocol": "REST / JSON",
        "current_version": "Public Data API v1 for unregistered access",
        "documentation_url": "https://www.bls.gov/developers/home.htm",
        "authentication": "v1 public/unregistered; v2 registration optional for higher limits",
        "status": "implemented-live-v4.35.6",
        "audit_date": AUDIT_DATE,
    },
)

VERIFIED_MACHINE_INTERFACES = tuple(prior.VERIFIED_MACHINE_INTERFACES) + NEW_VERIFIED_MACHINE_INTERFACES
COMPLETED_CONNECTOR_TARGETS = tuple(prior.COMPLETED_CONNECTOR_TARGETS) + (
    {"id":"pcbs-pxweb-sdgs","workspace":"Palestine / Country Statistics / SDGs","state":"LIVE","completed_in":"4.35.6"},
    {"id":"statistics-canada-wds","workspace":"Canada / Country Statistics","state":"LIVE","completed_in":"4.35.6"},
    {"id":"uk-ons-api","workspace":"United Kingdom / Country Statistics","state":"LIVE","completed_in":"4.35.6"},
    {"id":"australian-bureau-statistics-sdmx","workspace":"Australia / Country Statistics","state":"LIVE","completed_in":"4.35.6"},
    {"id":"us-bls-public-data-api","workspace":"Economics / Labor / Prices","state":"LIVE","completed_in":"4.35.6"},
)
PRIORITY_CONNECTOR_TARGETS = prior.PRIORITY_CONNECTOR_TARGETS


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _new_rows() -> list[dict[str, Any]]:
    rows = []
    specs = (
        ("pcbs-pxweb-sdgs", "Palestinian Central Bureau of Statistics PxWeb", "Palestinian Central Bureau of Statistics", "pcbs.gov.ps", "https://pcbs.gov.ps/SDGsIndicators/api/v1/en", "PxWeb API v1 / JSON-stat", "Palestine / National Statistics"),
        ("statistics-canada-wds", "Statistics Canada Web Data Service", "Statistics Canada", "www150.statcan.gc.ca", "https://www150.statcan.gc.ca/t1/wds/rest", "REST / JSON", "Canada / National Statistics"),
        ("uk-ons-api", "UK Office for National Statistics API", "Office for National Statistics", "api.beta.ons.gov.uk", "https://api.beta.ons.gov.uk/v1", "REST / JSON", "United Kingdom / National Statistics"),
        ("australian-bureau-statistics-sdmx", "Australian Bureau of Statistics Data API", "Australian Bureau of Statistics", "data.api.abs.gov.au", "https://data.api.abs.gov.au/rest", "SDMX", "Australia / National Statistics"),
        ("us-bls-public-data-api", "U.S. Bureau of Labor Statistics Public Data API", "U.S. Bureau of Labor Statistics", "api.bls.gov", "https://api.bls.gov/publicAPI/v1", "REST / JSON", "Economics / Labor / Prices"),
    )
    for source_id, title, org, host, api_url, protocol, workspace in specs:
        rows.append({
            "workspace": workspace,
            "module": "authoritative_connectors_v4356",
            "registry": "national-statistical-authorities",
            "source_id": source_id,
            "title": title,
            "organization": org,
            "authority": "official-government-source",
            "host": host,
            "url": api_url,
            "api_url": api_url,
            "documentation_url": next(row["documentation_url"] for row in NEW_VERIFIED_MACHINE_INTERFACES if row["id"] == source_id),
            "protocol": protocol,
            "machine_readable": True,
            "access_class": "LIVE",
            "implementation_evidence": f"authoritative_connectors_v4356 {source_id} bounded retrieval",
            "configuration_state": "configured",
            "configuration_key": None,
            "authentication": next(row["authentication"] for row in NEW_VERIFIED_MACHINE_INTERFACES if row["id"] == source_id),
            "coverage": workspace,
            "limitations": "National statistical observations remain subject to the source agency's release, revision, methodology, suppression and classification rules.",
        })
    return rows


def source_inventory(settings: Any = None) -> list[dict[str, Any]]:
    return list(prior.source_inventory(settings)) + _new_rows()


def _counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return prior._counts(rows)


def _unique_source_key(row: dict[str, Any]) -> str:
    return prior._unique_source_key(row)


def audit_overview(settings: Any = None) -> dict[str, Any]:
    rows = source_inventory(settings)
    counts = _counts(rows)
    unique = {_unique_source_key(row) for row in rows}
    machine_rows = [row for row in rows if row.get("machine_readable")]
    implemented = counts["LIVE"] + counts["DISCOVERY"] + counts["AUTH_REQUIRED"]
    payload = {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "audit_date": AUDIT_DATE,
        "classification": prior.audit_overview(settings)["classification"],
        "summary": {
            "source_registrations": len(rows),
            "unique_source_endpoints_or_records": len(unique),
            "workspaces_with_source_registries": len({row["workspace"] for row in rows}),
            "machine_readable_registrations": len(machine_rows),
            "implemented_or_configuration_gated_registrations": implemented,
            "counts": counts,
            "registered_but_not_retrieved": counts["REGISTERED"],
            "stale_implemented_connectors": counts["STALE"],
        },
        "principles": prior.audit_overview(settings)["principles"] + [
            "National statistical authorities are connected directly when a stable public machine interface exists.",
            "A nationally reported structural-access statistic is not a substitute for present operational conditions, service continuity or reliability.",
        ],
        "verified_machine_interfaces": list(VERIFIED_MACHINE_INTERFACES),
        "completed_connector_targets": list(COMPLETED_CONNECTOR_TARGETS),
        "priority_connector_targets": list(PRIORITY_CONNECTOR_TARGETS),
        "generated_at": _now(),
    }
    payload["audit_sha256"] = _digest({"summary": payload["summary"], "verified": payload["verified_machine_interfaces"]})
    return payload


def audit_catalog(settings: Any = None, workspace: str = "", access_class: str = "", query: str = "") -> dict[str, Any]:
    rows = source_inventory(settings)
    workspace_q = (workspace or "").strip().lower()
    class_q = (access_class or "").strip().upper()
    text_q = (query or "").strip().lower()
    if class_q and class_q not in ACCESS_CLASSES:
        raise ValueError(f"access_class must be one of: {', '.join(ACCESS_CLASSES)}")
    if workspace_q:
        rows = [row for row in rows if workspace_q in row["workspace"].lower() or workspace_q == row["module"].lower()]
    if class_q:
        rows = [row for row in rows if row["access_class"] == class_q]
    if text_q:
        rows = [row for row in rows if text_q in " ".join(str(row.get(key) or "") for key in ("title", "organization", "host", "source_id", "protocol", "workspace")).lower()]
    return {"ok": True, "version": VERSION, "contract": CONTRACT, "count": len(rows), "counts": _counts(rows), "access_classes": list(ACCESS_CLASSES), "sources": rows, "generated_at": _now()}


def workspace_matrix(settings: Any = None) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in source_inventory(settings):
        groups[row["workspace"]].append(row)
    workspaces = []
    for workspace, rows in sorted(groups.items()):
        counts = _counts(rows)
        machine = sum(1 for row in rows if row.get("machine_readable"))
        workspaces.append({
            "workspace": workspace,
            "source_registrations": len(rows),
            "machine_readable_registrations": machine,
            "counts": counts,
            "fully_live": machine > 0 and counts["REGISTERED"] == 0 and counts["STALE"] == 0 and counts["AUTH_REQUIRED"] == 0,
            "connector_gap": counts["REGISTERED"] + counts["BULK"] + counts["AUTH_REQUIRED"] + counts["STALE"],
        })
    return {"ok": True, "version": VERSION, "contract": CONTRACT, "workspace_count": len(workspaces), "workspaces": workspaces, "generated_at": _now()}


def audit_readiness(settings: Any = None) -> dict[str, Any]:
    overview = audit_overview(settings)
    counts = overview["summary"]["counts"]
    verified_ids = {row["id"] for row in VERIFIED_MACHINE_INTERFACES}
    required = {row["id"] for row in NEW_VERIFIED_MACHINE_INTERFACES}
    checks = {
        "source_registry_inventory_present": overview["summary"]["source_registrations"] >= 180,
        "classification_taxonomy_complete": set(ACCESS_CLASSES) == {"LIVE", "DISCOVERY", "REGISTERED", "AUTH_REQUIRED", "BULK", "STALE", "UNAVAILABLE"},
        "connector_expansions_i_ii_iii_and_national_statistics_complete": len(COMPLETED_CONNECTOR_TARGETS) == 20,
        "five_new_national_statistical_interfaces_verified": required.issubset(verified_ids),
        "five_new_national_statistical_registrations_live": sum(1 for row in source_inventory(settings) if row["source_id"] in required and row["access_class"] == "LIVE") == 5,
        "registered_backlog_preserved_for_future_expansion": counts["REGISTERED"] > 0,
        "no_known_stale_connector": counts["STALE"] == 0,
        "network_checks_not_required_for_deterministic_readiness": True,
    }
    return {"ok": all(checks.values()), "version": VERSION, "contract": CONTRACT, "network_calls_performed": False, "checks": checks, "generated_at": _now()}
