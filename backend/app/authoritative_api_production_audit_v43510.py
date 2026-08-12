from __future__ import annotations

"""Site Intelligence v4.35.16 authoritative API coverage closure & production audit after Expansion IV.

The audit is deterministic and network-free.  It reconciles source registrations,
implemented connector evidence, configuration-gated connectors, workspace gaps,
and the evidence/truth control plane without treating upstream availability as a
release blocker.
"""

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from typing import Any

from .version import APP_VERSION
from . import authoritative_api_audit_v43510 as prior
from .authoritative_connectors_v43510 import connector_readiness
from .evidence_intelligence_v4357 import readiness as evidence_readiness
from .workspace_evidence_unification_v4358 import readiness as workspace_evidence_readiness

VERSION = APP_VERSION
CONTRACT = "authoritative-api-coverage-closure-production-audit"
AUDIT_DATE = "2026-08-11"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _pct(num: int, den: int) -> float:
    return round((100.0 * num / den), 2) if den else 0.0


def _gap_tier(row: dict[str, Any]) -> str:
    gap = int(row.get("connector_gap") or 0)
    machine = int(row.get("machine_readable_registrations") or 0)
    counts = row.get("counts") or {}
    active = int(counts.get("LIVE") or 0) + int(counts.get("DISCOVERY") or 0)
    if gap >= 3 or (machine > 0 and active == 0 and gap > 0):
        return "HIGH"
    if gap == 2:
        return "MEDIUM"
    if gap == 1:
        return "LOW"
    return "CLOSED"


def closure_ledger(settings: Any = None) -> dict[str, Any]:
    inventory = prior.source_inventory(settings)
    matrix = prior.workspace_matrix(settings)["workspaces"]
    gap_rows = []
    for row in inventory:
        if not row.get("machine_readable"):
            continue
        state = str(row.get("access_class") or "UNAVAILABLE")
        if state not in {"REGISTERED", "AUTH_REQUIRED", "BULK", "STALE"}:
            continue
        gap_rows.append({
            "workspace": row.get("workspace"),
            "source_id": row.get("source_id"),
            "title": row.get("title"),
            "organization": row.get("organization"),
            "host": row.get("host"),
            "protocol": row.get("protocol"),
            "access_class": state,
            "configuration_key": row.get("configuration_key"),
            "implementation_evidence": row.get("implementation_evidence"),
            "limitations": row.get("limitations"),
        })
    gap_rows.sort(key=lambda x: (x["access_class"], str(x["workspace"]), str(x["organization"]), str(x["source_id"])))
    workspace_rows = []
    for row in matrix:
        item = dict(row)
        item["priority_tier"] = _gap_tier(row)
        implemented = int(row["counts"].get("LIVE") or 0) + int(row["counts"].get("DISCOVERY") or 0) + int(row["counts"].get("AUTH_REQUIRED") or 0)
        item["implemented_or_gated_coverage_pct"] = _pct(implemented, int(row.get("machine_readable_registrations") or 0))
        workspace_rows.append(item)
    workspace_rows.sort(key=lambda x: ({"HIGH": 0, "MEDIUM": 1, "LOW": 2, "CLOSED": 3}[x["priority_tier"]], -int(x.get("connector_gap") or 0), x["workspace"]))
    summary = Counter(row["access_class"] for row in gap_rows)
    payload = {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "network_calls_performed": False,
        "summary": {
            "machine_readable_gap_records": len(gap_rows),
            "registered_not_retrieved": summary["REGISTERED"],
            "configuration_required": summary["AUTH_REQUIRED"],
            "bulk_only": summary["BULK"],
            "stale": summary["STALE"],
            "workspaces_with_any_connector_gap": sum(1 for row in workspace_rows if row["connector_gap"] > 0),
            "high_priority_workspaces": sum(1 for row in workspace_rows if row["priority_tier"] == "HIGH"),
            "medium_priority_workspaces": sum(1 for row in workspace_rows if row["priority_tier"] == "MEDIUM"),
            "low_priority_workspaces": sum(1 for row in workspace_rows if row["priority_tier"] == "LOW"),
        },
        "workspace_ledger": workspace_rows,
        "gap_records": gap_rows,
        "generated_at": _now(),
    }
    payload["ledger_sha256"] = _digest({"summary": payload["summary"], "workspace_ledger": workspace_rows, "gap_records": gap_rows})
    return payload


def production_audit(settings: Any = None) -> dict[str, Any]:
    base = prior.audit_overview(settings)
    summary = dict(base["summary"])
    counts = dict(summary["counts"])
    machine_rows = [row for row in prior.source_inventory(settings) if row.get("machine_readable")]
    machine_counts = Counter(str(row.get("access_class") or "UNAVAILABLE") for row in machine_rows)
    machine = len(machine_rows)
    active = int(machine_counts.get("LIVE", 0)) + int(machine_counts.get("DISCOVERY", 0))
    implemented_or_gated = active + int(machine_counts.get("AUTH_REQUIRED", 0))
    ledger = closure_ledger(settings)
    connectors = connector_readiness(settings)
    evidence = evidence_readiness()
    workspace_evidence = workspace_evidence_readiness()
    checks = {
        "source_inventory_reconciles": sum(int(counts.get(k, 0)) for k in prior.ACCESS_CLASSES) == int(summary["source_registrations"]),
        "machine_readable_inventory_present": machine >= 100,
        "connector_catalog_ready": bool(connectors.get("ok")) and connectors.get("network_calls_performed") is False,
        "metric_semantics_and_precedence_ready": bool(evidence.get("ok")) and evidence.get("network_calls_performed") is False,
        "workspace_truth_unification_ready": bool(workspace_evidence.get("ok")) and workspace_evidence.get("network_calls_performed") is False,
        "no_known_stale_implemented_connectors": int(counts.get("STALE", 0)) == 0,
        "external_source_health_not_used_as_release_blocker": True,
        "remaining_connector_backlog_is_explicit": int(machine_counts.get("REGISTERED", 0)) == int(ledger["summary"]["registered_not_retrieved"]),
    }
    controls_ready = all(checks.values())
    coverage_complete = int(machine_counts.get("REGISTERED", 0)) == 0
    payload = {
        "ok": controls_ready,
        "version": VERSION,
        "contract": CONTRACT,
        "audit_date": AUDIT_DATE,
        "network_calls_performed": False,
        "production_controls_ready": controls_ready,
        "coverage_closure_complete": coverage_complete,
        "closure_status": "complete" if coverage_complete else ("production-controls-ready-backlog-open" if controls_ready else "blocked"),
        "summary": summary,
        "machine_readable_summary": {
            "registrations": machine,
            "counts": {name: int(machine_counts.get(name, 0)) for name in prior.ACCESS_CLASSES},
            "implemented_discovery_or_configuration_gated": implemented_or_gated,
            "registered_not_retrieved": int(machine_counts.get("REGISTERED", 0)),
        },
        "coverage": {
            "live_or_discovery_pct_of_machine_readable": _pct(active, machine),
            "implemented_discovery_or_configuration_gated_pct_of_machine_readable": _pct(implemented_or_gated, machine),
            "registered_not_retrieved_pct_of_machine_readable": _pct(int(machine_counts.get("REGISTERED", 0)), machine),
            "bulk_only_pct_of_machine_readable": _pct(int(machine_counts.get("BULK", 0)), machine),
        },
        "checks": checks,
        "closure_ledger_summary": ledger["summary"],
        "next_connector_targets": list(base.get("priority_connector_targets") or []),
        "boundaries": [
            "Production readiness means the Site Intelligence control plane is internally coherent; it does not mean every registered source has been connected.",
            "LIVE/DISCOVERY status is awarded only when repository implementation evidence matches the registered interface, not merely the same agency host.",
            "AUTH_REQUIRED is implemented but not operational until server-side configuration is present.",
            "A remaining REGISTERED source is an explicit connector backlog item and must never be presented as live retrieval.",
            "External provider outages are operational source-health events and do not invalidate a correct first-party deployment.",
        ],
        "generated_at": _now(),
    }
    payload["production_audit_sha256"] = _digest({"summary": summary, "machine_readable_summary": payload["machine_readable_summary"], "coverage": payload["coverage"], "checks": checks, "ledger": ledger["summary"]})
    return payload


def production_readiness(settings: Any = None) -> dict[str, Any]:
    audit = production_audit(settings)
    return {
        "ok": audit["production_controls_ready"],
        "version": VERSION,
        "contract": CONTRACT,
        "network_calls_performed": False,
        "coverage_closure_complete": audit["coverage_closure_complete"],
        "closure_status": audit["closure_status"],
        "checks": audit["checks"],
        "summary": audit["closure_ledger_summary"],
        "generated_at": _now(),
    }


def audit_overview(settings: Any = None) -> dict[str, Any]:
    payload = prior.audit_overview(settings)
    payload["version"] = VERSION
    payload["production_audit"] = production_audit(settings)
    payload["closure_ledger"] = closure_ledger(settings)["summary"]
    payload["principles"] = list(payload.get("principles") or []) + [
        "Coverage closure is explicit: remaining machine-readable registrations stay visible until retrieval is actually implemented.",
        "Production audit status measures control-plane integrity separately from upstream provider availability and total connector completion.",
    ]
    return payload


def audit_catalog(settings: Any = None, workspace: str = "", access_class: str = "", query: str = "") -> dict[str, Any]:
    payload = prior.audit_catalog(settings, workspace=workspace, access_class=access_class, query=query)
    payload["version"] = VERSION
    return payload


def workspace_matrix(settings: Any = None) -> dict[str, Any]:
    payload = prior.workspace_matrix(settings)
    payload["version"] = VERSION
    ledger = closure_ledger(settings)
    tiers = {row["workspace"]: row["priority_tier"] for row in ledger["workspace_ledger"]}
    for row in payload["workspaces"]:
        row["priority_tier"] = tiers.get(row["workspace"], "CLOSED")
    return payload


def audit_readiness(settings: Any = None) -> dict[str, Any]:
    payload = prior.audit_readiness(settings)
    production = production_readiness(settings)
    payload["version"] = VERSION
    payload.setdefault("checks", {})["production_coverage_audit_ready"] = production["ok"]
    payload["ok"] = all(payload["checks"].values())
    payload["production_audit"] = production
    return payload
