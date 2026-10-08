"""v4.56.0 standalone production consolidation and certification contract.

This release certifies the independent Site Intelligence runtime architecture.
Static certification never claims that optional external domain dependencies are
currently available; live deployment helpers verify those separately and retain
truthful degraded readiness semantics.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .browser_api_transport_v455322 import manifest as transport_manifest
from .runtime_context_repair_v455321 import manifest as runtime_manifest
from .standalone_functional_parity_v45532 import (
    certification as parity_certification,
    manifest as parity_manifest,
    routes as parity_routes,
)
from .version import APP_VERSION, RELEASE_NAME

REGISTRY_PATH = Path(__file__).resolve().parents[1] / "data" / "production_consolidation_registry_v4560.json"


def manifest() -> dict[str, Any]:
    payload = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    if payload.get("version") != APP_VERSION:
        raise RuntimeError("production consolidation registry release mismatch")
    if payload.get("release_name") != RELEASE_NAME:
        raise RuntimeError("production consolidation registry release-name mismatch")
    return payload


def checklist() -> dict[str, Any]:
    registry = manifest()
    parity = parity_manifest()
    routes = parity_routes()
    parity_cert = parity_certification()
    runtime = runtime_manifest()
    transport = transport_manifest()
    targets = registry["certification_targets"]
    authority = parity["authority"]

    checks = [
        ("release-identity", registry["version"] == APP_VERSION and registry["release_name"] == RELEASE_NAME),
        ("standalone-web-authority", authority.get("web_origin") == registry["authority"]["web_origin"]),
        ("machine-api-authority", authority.get("api_origin") == registry["authority"]["api_origin"]),
        ("wordpress-non-authority", authority.get("wordpress_runtime_dependency") is False and registry["authority"]["wordpress_runtime_authority"] is False),
        ("workspace-parity", parity.get("workspace_count") == targets["required_workspace_count"]),
        ("functional-control-parity", parity.get("functional_control_count") == targets["required_functional_control_count"]),
        ("deep-link-parity", len(routes.get("deep_link_aliases", {})) == targets["required_deep_link_alias_count"]),
        ("browser-functional-certification", parity_cert.get("certification", {}).get("browser_interaction_required") is True),
        ("runtime-health-truth", runtime.get("runtime_health", {}).get("primary_health_path") == registry["runtime_truth"]["primary_health_path"]),
        ("browser-transport-truth", transport.get("primary_health_path") == registry["runtime_truth"]["primary_health_path"] and transport.get("runtime_transport", {}).get("ordinary_public_gets_require_custom_header") is False),
        ("deployment-order", registry.get("deployment_order") == ["backend", "web"]),
        ("rollback-contract", registry.get("rollback", {}).get("backup_required") is True),
    ]
    rows = [{"check": name, "pass": bool(passed)} for name, passed in checks]
    ok = all(row["pass"] for row in rows)
    return {
        "ok": ok,
        "version": APP_VERSION,
        "schema": registry["schema"],
        "release_name": RELEASE_NAME,
        "contract_status": "contract-certified" if ok else "contract-failed",
        "live_runtime_asserted": False,
        "live_runtime_note": "Live dependency availability is certified by deployment probes, not by this static contract.",
        "checks": rows,
        "workspace_count": parity["workspace_count"],
        "functional_control_count": parity["functional_control_count"],
        "deep_link_alias_count": len(routes["deep_link_aliases"]),
    }


def release_snapshot() -> dict[str, Any]:
    registry = manifest()
    result = checklist()
    payload = {
        "version": APP_VERSION,
        "release_name": RELEASE_NAME,
        "authority": registry["authority"],
        "expected_inventory": registry["expected_inventory"],
        "certification_targets": registry["certification_targets"],
        "runtime_truth": registry["runtime_truth"],
        "deployment_order": registry["deployment_order"],
        "checks": result["checks"],
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        "ok": result["ok"],
        "version": APP_VERSION,
        "release_name": RELEASE_NAME,
        "schema": "sc-site-intelligence-production-release-snapshot/1.0",
        "sha256": hashlib.sha256(canonical).hexdigest(),
        "payload": payload,
    }


def assert_contract() -> None:
    result = checklist()
    failed = [row["check"] for row in result["checks"] if not row["pass"]]
    if failed:
        raise RuntimeError(f"production consolidation contract failed: {failed}")
