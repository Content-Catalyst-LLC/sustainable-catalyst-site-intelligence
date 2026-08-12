from __future__ import annotations

"""v4.35.23 authoritative-source audit enriched with evidence-selection intelligence."""

from typing import Any
from .version import APP_VERSION
from . import authoritative_api_audit_v4356 as prior
from .evidence_intelligence_v4357 import overview as evidence_overview, readiness as evidence_readiness

VERSION = APP_VERSION
CONTRACT = prior.CONTRACT
ACCESS_CLASSES = prior.ACCESS_CLASSES
VERIFIED_MACHINE_INTERFACES = prior.VERIFIED_MACHINE_INTERFACES
COMPLETED_CONNECTOR_TARGETS = prior.COMPLETED_CONNECTOR_TARGETS
PRIORITY_CONNECTOR_TARGETS = prior.PRIORITY_CONNECTOR_TARGETS
source_inventory = prior.source_inventory
_counts = prior._counts
_unique_source_key = prior._unique_source_key


def audit_overview(settings: Any = None) -> dict[str, Any]:
    payload = prior.audit_overview(settings)
    payload["version"] = VERSION
    payload["evidence_intelligence"] = evidence_overview()
    payload["principles"] = list(payload.get("principles") or []) + [
        "Source coverage is not source precedence: the selected source must match the requested metric concept and jurisdiction.",
        "Freshness is cadence-aware and can never override a metric-semantics mismatch.",
        "Conflicting exact-concept observations are disclosed for review instead of automatically blended.",
    ]
    return payload


def audit_catalog(settings: Any = None, workspace: str = "", access_class: str = "", query: str = "") -> dict[str, Any]:
    payload = prior.audit_catalog(settings, workspace=workspace, access_class=access_class, query=query)
    payload["version"] = VERSION
    return payload


def workspace_matrix(settings: Any = None) -> dict[str, Any]:
    payload = prior.workspace_matrix(settings)
    payload["version"] = VERSION
    return payload


def audit_readiness(settings: Any = None) -> dict[str, Any]:
    payload = prior.audit_readiness(settings)
    evidence = evidence_readiness()
    payload["version"] = VERSION
    payload.setdefault("checks", {})["evidence_intelligence_ready"] = evidence["ok"]
    payload["ok"] = all(payload["checks"].values())
    payload["evidence_intelligence"] = evidence
    return payload
