from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

RELEASE_VERSION = "4.0.0"
CONTRACT = "unified-public-intelligence-platform"
ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "backend/data/unified_public_intelligence_policy_v4000.json"


def _policy() -> dict[str, Any]:
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def _digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _route_directory() -> list[dict[str, Any]]:
    policy = _policy()
    rows: list[dict[str, Any]] = []
    for area_index, area in enumerate(policy["primary_areas"], start=1):
        for route_index, route in enumerate(area["routes"], start=1):
            rows.append({
                "route_id": route,
                "primary_area_id": area["id"],
                "primary_area_label": area["label"],
                "primary_area_order": area_index,
                "route_order": route_index,
                "preserved": True,
            })
    return rows


def public_unified_platform() -> dict[str, Any]:
    policy = _policy()
    routes = _route_directory()
    payload = {
        "ok": True,
        "version": RELEASE_VERSION,
        "contract": CONTRACT,
        "release_name": "Unified Public Intelligence Platform",
        "primary_area_count": len(policy["primary_areas"]),
        "route_count": len(routes),
        "primary_areas": policy["primary_areas"],
        "canonical_contract_count": len(policy["canonical_contracts"]),
        "compatibility": policy["compatibility"],
        "boundaries": policy["boundaries"],
    }
    payload["platform_sha256"] = _digest(payload)
    return payload


def public_unified_navigation() -> dict[str, Any]:
    policy = _policy()
    routes = _route_directory()
    return {
        "ok": True,
        "version": RELEASE_VERSION,
        "primary_area_count": len(policy["primary_areas"]),
        "route_count": len(routes),
        "areas": policy["primary_areas"],
        "routes": routes,
        "all_routes_unique": len({row["route_id"] for row in routes}) == len(routes),
    }


def public_unified_contracts() -> dict[str, Any]:
    policy = _policy()
    contracts = policy["canonical_contracts"]
    return {
        "ok": True,
        "version": RELEASE_VERSION,
        "contract_count": len(contracts),
        "contracts": contracts,
        "single_truth_contract": True,
        "single_route_state_contract": True,
        "single_publication_export_contract": True,
        "human_review_preserved": True,
        "contracts_sha256": _digest(contracts),
    }


def public_v4_readiness() -> dict[str, Any]:
    policy = _policy()
    routes = _route_directory()
    route_ids = [row["route_id"] for row in routes]
    checks = {
        "six_primary_areas": len(policy["primary_areas"]) == 6,
        "all_35_routes_preserved": len(route_ids) == 35 and len(set(route_ids)) == 35,
        "canonical_contracts_present": len(policy["canonical_contracts"]) == 6,
        "legacy_routes_preserved": policy["compatibility"].get("legacy_routes_preserved") is True,
        "deep_links_preserved": policy["compatibility"].get("deep_links_preserved") is True,
        "automatic_migrations_disabled": policy["compatibility"].get("automatic_migrations") is False,
    }
    return {
        "ok": all(checks.values()),
        "version": RELEASE_VERSION,
        "release_name": "Unified Public Intelligence Platform",
        "checks": checks,
        "summary": {
            "primary_areas": len(policy["primary_areas"]),
            "preserved_routes": len(route_ids),
            "canonical_contracts": len(policy["canonical_contracts"]),
        },
        "readiness_sha256": _digest(checks),
    }
