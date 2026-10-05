#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

EXPECTED_VERSION = "4.43.0"
EXPECTED_NAME = "Modular FastAPI Route & Capability Registry"
RELEASE_BOUND = (
    "analytical_workspace_policy_v3234.json", "bootstrap_recovery_policy_v32361.json",
    "briefing_publication_policy_v3290.json", "browser_reliability_policy_v3235.json",
    "comparative_model_assurance_policy_v3260.json", "connected_platform_policy_v300.json",
    "country_identity_registry_v43523.json", "embed_isolation_policy_v32363.json",
    "evidence_synthesis_policy_v2180.json", "federation_policy_v2240.json",
    "institutional_review_governance_policy_v3300.json", "institutional_workspaces_policy_v2220.json",
    "intelligence_publishing_policy_v2200.json", "knowledge_graph_policy_v2190.json",
    "knowledge_graph_relationship_registry_v2190.json", "live_intelligence_source_registry_v320.json",
    "map_interaction_policy_v3232.json", "model_governance_policy_v2170.json",
    "model_metric_registry_v2170.json", "monitoring_early_warning_policy_v3280.json",
    "mutation_observer_recovery_policy_v32362.json", "performance_offline_policy_v3236.json",
    "research_evidence_integration_policy_v3270.json", "scheduled_monitoring_policy_v2210.json",
    "spatial_evidence_policy_v2150.json", "startup_stability_policy_v32364.json",
    "unified_analytical_state_policy_v3250.json",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    version_py = (root / "backend/app/version.py").read_text(encoding="utf-8")
    main_py = (root / "backend/app/main.py").read_text(encoding="utf-8")
    system_router = (root / "backend/app/routers/system.py").read_text(encoding="utf-8")
    data_router = (root / "backend/app/routers/data_truth.py").read_text(encoding="utf-8")
    capability_router = (root / "backend/app/routers/capabilities.py").read_text(encoding="utf-8")
    registry = (root / "backend/app/route_registry_v4430.py").read_text(encoding="utf-8")
    plugin = (root / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text(encoding="utf-8")
    deploy = (root / "deploy/contabo/upgrade_site_intelligence_backend_v4_43_0_contabo.sh").read_text(encoding="utf-8")
    readme = (root / "README.md").read_text(encoding="utf-8")

    require(f'APP_VERSION = "{EXPECTED_VERSION}"' in version_py, "APP_VERSION mismatch")
    require(f'RELEASE_NAME = "{EXPECTED_NAME}"' in version_py, "release name mismatch")
    require(f"Version: {EXPECTED_VERSION}" in plugin, "plugin version mismatch")
    require(f"site-intelligence-v{EXPECTED_VERSION}" in plugin, "plugin release ID mismatch")
    require(f"**Current release:** v{EXPECTED_VERSION} — {EXPECTED_NAME}" in readme, "README current release mismatch")

    require("app.include_router(system_router)" in main_py, "system router not registered")
    require("app.include_router(data_truth_router)" in main_py, "data-truth router not registered")
    require("app.include_router(capabilities_router)" in main_py, "capability router not registered")
    require('@app.get("/health")' not in main_py, "health route still declared in main.py")
    require('@app.get("/public/data-truth")' not in main_py, "data-truth route still declared in main.py")
    require('@router.get("/health")' in system_router, "health route missing from modular router")
    require('@router.get("/public/data-truth")' in data_router, "data-truth route missing from modular router")
    require('@router.get("/public/capabilities")' in capability_router, "capability manifest endpoint missing")
    require('@router.get("/public/routes/registry")' in capability_router, "route registry endpoint missing")
    require("CAPABILITIES:" in registry and "route_inventory" in registry, "capability registry implementation missing")

    for name in RELEASE_BOUND:
        payload = json.loads((root / "backend/data" / name).read_text(encoding="utf-8"))
        require(payload.get("version") == EXPECTED_VERSION, f"release-bound policy mismatch: {name}")
    sample = json.loads((root / "backend/data/analytical_workspace_policy_v3234.json").read_text(encoding="utf-8"))
    require(sample.get("release_id") == "site-intelligence-v4.35.5", "historical release_id changed")

    require("--exclude='data/'" in deploy, "deployment no longer preserves dynamic production data")
    require("RELEASE_BOUND_POLICIES=(" in deploy, "release-bound policy list missing from deployment")
    require('cp "$SRC_BACKEND/data/$policy" "$LIVE_BACKEND/data/$policy"' in deploy, "deployment does not restore release-bound policies")

    prune = plugin[plugin.index("public function prune_unused_shortcodes()"):plugin.index("public static function defaults()")]
    keep = re.findall(r"'([^']+)'", prune.split("array_fill_keys([", 1)[1].split("], true)", 1)[0])
    require(len(keep) == 72 and len(set(keep)) == 72, "shortcode containment changed")

    print("PASS: v4.43.0 release identity aligned")
    print("PASS: system/runtime and data-truth/provenance routes modularized")
    print("PASS: machine-readable capability and route registry installed")
    print("PASS: 27 release-bound policies advanced without rewriting historical origin metadata")
    print("PASS: Contabo deployment preserves dynamic data and restores release-bound policies")
    print("PASS: 72-shortcode containment contract preserved")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
