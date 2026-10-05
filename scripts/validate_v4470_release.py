#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

EXPECTED_VERSION = "4.47.0"
EXPECTED_NAME = "Spatiotemporal Query & Cross-Layer Analysis Engine"
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
    "unified_analytical_state_policy_v3250.json", "spatial_layer_registry_v4460.json",
    "spatiotemporal_operator_registry_v4470.json",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    version_py = (root / "backend/app/version.py").read_text(encoding="utf-8")
    main_py = (root / "backend/app/main.py").read_text(encoding="utf-8")
    registry_py = (root / "backend/app/route_registry_v4430.py").read_text(encoding="utf-8")
    engine_py = (root / "backend/app/spatiotemporal_query_v4470.py").read_text(encoding="utf-8")
    router_py = (root / "backend/app/routers/spatiotemporal.py").read_text(encoding="utf-8")
    authority = (root / "backend/app/standalone_authority_v4440.py").read_text(encoding="utf-8")
    plugin = (root / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text(encoding="utf-8")
    app_js = (root / "backend/public_app/assets/app.js").read_text(encoding="utf-8")
    index = (root / "backend/public_app/index.html").read_text(encoding="utf-8")
    manifest = json.loads((root / "backend/public_app/manifest.webmanifest").read_text(encoding="utf-8"))
    sw = (root / "backend/public_app/service-worker.js").read_text(encoding="utf-8")
    deploy = (root / "deploy/contabo/upgrade_site_intelligence_backend_v4_47_0_contabo.sh").read_text(encoding="utf-8")
    readme = (root / "README.md").read_text(encoding="utf-8")
    operators = json.loads((root / "backend/data/spatiotemporal_operator_registry_v4470.json").read_text(encoding="utf-8"))
    layers = json.loads((root / "backend/data/spatial_layer_registry_v4460.json").read_text(encoding="utf-8"))

    require(f'APP_VERSION = "{EXPECTED_VERSION}"' in version_py, "APP_VERSION mismatch")
    require(f'RELEASE_NAME = "{EXPECTED_NAME}"' in version_py, "release name mismatch")
    require(f"Version: {EXPECTED_VERSION}" in plugin, "plugin version mismatch")
    require(f"site-intelligence-v{EXPECTED_VERSION}" in plugin, "plugin release ID mismatch")
    require(f"**Current release:** v{EXPECTED_VERSION} — {EXPECTED_NAME}" in readme, "README release mismatch")

    require('CapabilitySpec("spatiotemporal-analysis"' in registry_py, "spatiotemporal capability family missing")
    require('"registry_version": "1.4.0"' in registry_py, "capability registry version mismatch")
    require("spatiotemporal_router" in main_py and "app.include_router(spatiotemporal_router)" in main_py, "spatiotemporal router not registered")
    for route in (
        "/public/spatiotemporal/registry", "/public/spatiotemporal/query-schema", "/public/spatiotemporal/operators",
        "/public/spatiotemporal/query/plan", "/public/spatiotemporal/query/execute",
        "/public/spatiotemporal/cross-layer/join", "/public/spatiotemporal/cross-layer/analyze",
        "/public/spatiotemporal/compatibility",
    ):
        require(route in router_py, f"spatiotemporal route missing: {route}")

    require('QUERY_SCHEMA = "sc-site-intelligence-spatiotemporal-query/1.0"' in engine_py, "query schema missing")
    require('QUERY_PLAN_SCHEMA = "sc-site-intelligence-spatiotemporal-query-plan/1.0"' in engine_py, "query-plan schema missing")
    require('JOIN_RESULT_SCHEMA = "sc-site-intelligence-cross-layer-join-result/1.0"' in engine_py, "join schema missing")
    require('ANALYSIS_RESULT_SCHEMA = "sc-site-intelligence-cross-layer-analysis-result/1.0"' in engine_py, "analysis schema missing")
    require('"bounding-box-first"' in (root / "backend/data/spatiotemporal_operator_registry_v4470.json").read_text(encoding="utf-8"), "bbox semantics not declared")
    require('"source_object_digests"' in engine_py and '"query_plan_digest"' in engine_py, "derived-result provenance incomplete")
    require('"content_digest"' in engine_py, "evidence digest lineage missing")

    require(operators.get("version") == EXPECTED_VERSION, "operator registry version mismatch")
    require(operators.get("schema") == "sc-site-intelligence-spatiotemporal-operator-registry/1.0", "operator registry schema mismatch")
    require({row["operator"] for row in operators["spatial_predicates"]} == {"intersects", "within", "contains", "disjoint"}, "spatial operator set mismatch")
    require("overlaps" in {row["operator"] for row in operators["temporal_predicates"]}, "temporal overlap operator missing")
    require(set(operators["aggregate_operators"]) == {"count", "sum", "mean", "min", "max"}, "aggregate operator set mismatch")
    require(layers.get("version") == EXPECTED_VERSION and layers.get("layer_count") == 18, "v4.46 layer registry not carried forward")

    require('NavigationItem("spatial", "Spatial", "Cross-layer space-time analysis", "spatiotemporal-analysis"' in authority, "standalone spatial nav not promoted to v4.47")
    require('"spatiotemporal_registry": "/public/spatiotemporal/registry"' in authority, "standalone bootstrap missing spatiotemporal registry")
    require('"spatial_evidence_registry": "/public/spatial-evidence/registry"' in authority, "v4.46 spatial registry bootstrap endpoint lost")

    require('const APP_VERSION="4.47.0"' in app_js, "standalone JS version mismatch")
    require('data-scsi-release="4.47.0"' in index, "standalone HTML version mismatch")
    require(manifest.get("start_url") == "/app/?source=pwa&release=4.47.0", "manifest release mismatch")
    require("4.47.0" in sw, "service worker release mismatch")

    require(len(RELEASE_BOUND) == 29, "release-bound file count mismatch")
    for name in RELEASE_BOUND:
        payload = json.loads((root / "backend/data" / name).read_text(encoding="utf-8"))
        require(payload.get("version") == EXPECTED_VERSION, f"release-bound mismatch: {name}")
    sample = json.loads((root / "backend/data/analytical_workspace_policy_v3234.json").read_text(encoding="utf-8"))
    require(sample.get("release_id") == "site-intelligence-v4.35.5", "historical release_id changed")

    require("--exclude='data/'" in deploy, "deployment no longer preserves dynamic data")
    require("spatial_layer_registry_v4460.json" in deploy, "deployment no longer promotes spatial layer registry")
    require("spatiotemporal_operator_registry_v4470.json" in deploy, "deployment does not promote v4.47 operator registry")
    require('assert APP_VERSION == "4.47.0"' in deploy, "deployment verifier version mismatch")
    require('"/public/spatiotemporal/registry"' in deploy, "deployment does not certify spatiotemporal engine")
    require('"/public/spatiotemporal/query/execute"' in deploy, "deployment does not certify query execution")

    prune = plugin[plugin.index("public function prune_unused_shortcodes()"):plugin.index("public static function defaults()")]
    keep = re.findall(r"'([^']+)'", prune.split("array_fill_keys([", 1)[1].split("], true)", 1)[0])
    require(len(keep) == 72 and len(set(keep)) == 72, "72-shortcode compatibility ceiling changed")
    require("const WORDPRESS_ROLE = 'thin-shell-and-embed-bridge';" in plugin, "WordPress thin-shell role changed")

    print("PASS: v4.47.0 release identity aligned")
    print("PASS: deterministic spatiotemporal query planning/execution contract installed")
    print("PASS: bbox spatial + interval temporal + property filter operator registry installed")
    print("PASS: cross-layer joins and grouped analysis preserve source evidence digests")
    print("PASS: eight modular spatiotemporal routes and first-class capability family installed")
    print("PASS: v4.46 spatial evidence registry and legacy spatial routes preserved")
    print("PASS: 29 release-bound static files and corrected Contabo deployment contract retained")
    print("PASS: WordPress remains thin shell; 72-shortcode compatibility ceiling preserved")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
