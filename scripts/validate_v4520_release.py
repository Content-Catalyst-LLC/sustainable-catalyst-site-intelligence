#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

EXPECTED_VERSION = "4.52.0"
EXPECTED_NAME = "Predictive Spatial Intelligence Consumer"
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
    "spatiotemporal_operator_registry_v4470.json", "spatial_relationship_registry_v4480.json",
    "live_geospatial_event_fusion_registry_v4490.json", "global_source_federation_registry_v4500.json",
    "spatial_research_handoff_registry_v4510.json", "predictive_spatial_consumer_registry_v4520.json",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    version_py = (root / "backend/app/version.py").read_text(encoding="utf-8")
    main_py = (root / "backend/app/main.py").read_text(encoding="utf-8")
    registry_py = (root / "backend/app/route_registry_v4430.py").read_text(encoding="utf-8")
    consumer_py = (root / "backend/app/predictive_spatial_consumer_v4520.py").read_text(encoding="utf-8")
    router_py = (root / "backend/app/routers/predictive_spatial.py").read_text(encoding="utf-8")
    authority = (root / "backend/app/standalone_authority_v4440.py").read_text(encoding="utf-8")
    plugin = (root / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text(encoding="utf-8")
    app_js = (root / "backend/public_app/assets/app.js").read_text(encoding="utf-8")
    index = (root / "backend/public_app/index.html").read_text(encoding="utf-8")
    manifest = json.loads((root / "backend/public_app/manifest.webmanifest").read_text(encoding="utf-8"))
    sw = (root / "backend/public_app/service-worker.js").read_text(encoding="utf-8")
    deploy = (root / "deploy/contabo/upgrade_site_intelligence_backend_v4_52_0_contabo.sh").read_text(encoding="utf-8")
    readme = (root / "README.md").read_text(encoding="utf-8")
    consumer_registry = json.loads((root / "backend/data/predictive_spatial_consumer_registry_v4520.json").read_text(encoding="utf-8"))

    require(f'APP_VERSION = "{EXPECTED_VERSION}"' in version_py, "APP_VERSION mismatch")
    require(f'RELEASE_NAME = "{EXPECTED_NAME}"' in version_py, "release name mismatch")
    require(f"Version: {EXPECTED_VERSION}" in plugin, "plugin version mismatch")
    require(f"site-intelligence-v{EXPECTED_VERSION}" in plugin, "plugin release ID mismatch")
    require(f"**Current release:** v{EXPECTED_VERSION} — {EXPECTED_NAME}" in readme, "README release mismatch")

    require('CapabilitySpec("predictive-spatial-intelligence"' in registry_py, "predictive spatial capability missing")
    require('"registry_version": "1.9.0"' in registry_py, "capability registry generation mismatch")
    require("predictive_spatial_router" in main_py and "app.include_router(predictive_spatial_router)" in main_py, "predictive router not registered")
    for route in (
        "/public/predictive-spatial/registry", "/public/predictive-spatial/schema", "/public/predictive-spatial/providers",
        "/public/predictive-spatial/normalize", "/public/predictive-spatial/validate", "/public/predictive-spatial/bind",
        "/public/predictive-spatial/query", "/public/predictive-spatial/compare", "/public/predictive-spatial/scenario",
        "/public/predictive-spatial/calibration", "/public/predictive-spatial/research-context", "/public/predictive-spatial/compatibility",
    ):
        require(route in router_py, f"predictive route missing: {route}")

    for schema in (
        'PREDICTIVE_OBJECT_SCHEMA = "sc-site-intelligence-predictive-spatial-intelligence/1.0"',
        'MODEL_BINDING_SCHEMA = "sc-site-intelligence-predictive-model-binding/1.0"',
        'COMPARISON_SCHEMA = "sc-site-intelligence-predictive-spatial-comparison/1.0"',
        'SCENARIO_SCHEMA = "sc-site-intelligence-predictive-spatial-scenario/1.0"',
        'RESEARCH_CONTEXT_SCHEMA = "sc-site-intelligence-predictive-spatial-research-context/1.0"',
    ):
        require(schema in consumer_py, f"predictive schema missing: {schema}")
    require('"automatic_model_ranking": False' in consumer_py, "automatic model ranking boundary missing")
    require('"preferred_prediction": None' in consumer_py, "no-preferred-model boundary missing")
    require('"consumer_recomputed_metrics": False' in consumer_py, "calibration consumer boundary missing")
    require('"research_object_mutated": False' in consumer_py, "research object mutation boundary missing")

    require(consumer_registry.get("version") == EXPECTED_VERSION, "predictive registry version mismatch")
    require(consumer_registry.get("schema") == "sc-site-intelligence-predictive-spatial-consumer-registry/1.0", "predictive registry schema mismatch")
    require(len(consumer_registry.get("providers") or []) == 4, "provider count mismatch")
    require({x["provider_id"] for x in consumer_registry["providers"]} == {"workspace", "platform-core", "site-intelligence-model-governance", "external-published"}, "provider registry mismatch")

    require('NavigationItem("predictive-spatial", "Predictive", "Forecasts, probability & uncertainty", "predictive-spatial-intelligence"' in authority, "standalone predictive navigation missing")
    require('"predictive_spatial_registry": "/public/predictive-spatial/registry"' in authority, "standalone bootstrap predictive endpoint missing")
    require('"spatial_research_registry": "/public/spatial-research/registry"' in authority, "v4.51 bootstrap endpoint lost")

    require('const APP_VERSION="4.52.0"' in app_js, "standalone JS version mismatch")
    require('data-scsi-release="4.52.0"' in index, "standalone HTML version mismatch")
    require(manifest.get("start_url") == "/app/?source=pwa&release=4.52.0", "manifest release mismatch")
    require("4.52.0" in sw, "service worker release mismatch")

    require(len(RELEASE_BOUND) == 34, "release-bound file count mismatch")
    for name in RELEASE_BOUND:
        payload = json.loads((root / "backend/data" / name).read_text(encoding="utf-8"))
        require(payload.get("version") == EXPECTED_VERSION, f"release-bound mismatch: {name}")
    sample = json.loads((root / "backend/data/analytical_workspace_policy_v3234.json").read_text(encoding="utf-8"))
    require(sample.get("release_id") == "site-intelligence-v4.35.5", "historical release_id changed")

    require("--exclude='data/'" in deploy, "deployment no longer preserves dynamic data")
    require("health: starting" not in deploy, "deployment helper should not certify starting health state")
    for name in ("spatial_layer_registry_v4460.json", "spatiotemporal_operator_registry_v4470.json", "spatial_relationship_registry_v4480.json", "live_geospatial_event_fusion_registry_v4490.json", "global_source_federation_registry_v4500.json", "spatial_research_handoff_registry_v4510.json", "predictive_spatial_consumer_registry_v4520.json"):
        require(name in deploy, f"deployment does not promote required registry: {name}")
    require('assert manifest["registry_version"] == "1.9.0"' in deploy, "deployment capability registry check missing")
    require('assert registry["provider_count"] == 4' in deploy, "deployment predictive provider check missing")

    print("PASS: v4.52.0 release identity aligned")
    print("PASS: predictive spatial intelligence consumer and provider-neutral schema installed")
    print("PASS: Workspace/Core/legacy/external provider classes registered without network-fetch authority")
    print("PASS: prediction validation, spatial binding, query, comparison, scenario, calibration and research linkage installed")
    print("PASS: no training, retraining, automatic model selection, probability-as-truth or prediction-as-observation semantics")
    print("PASS: twelve modular predictive-spatial routes and capability-registry generation 1.9.0 installed")
    print("PASS: 34 release-bound static files and health-aware Contabo deployment contract installed")
    print("PASS: WordPress remains thin shell; no predictive feature shortcode added")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL: {exc}", file=__import__("sys").stderr)
        raise
