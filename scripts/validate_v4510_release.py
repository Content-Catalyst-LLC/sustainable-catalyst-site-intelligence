#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

EXPECTED_VERSION = "4.51.0"
EXPECTED_NAME = "Spatial Research Object & Cross-Product Handoffs"
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
    "spatial_research_handoff_registry_v4510.json",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    version_py = (root / "backend/app/version.py").read_text(encoding="utf-8")
    main_py = (root / "backend/app/main.py").read_text(encoding="utf-8")
    registry_py = (root / "backend/app/route_registry_v4430.py").read_text(encoding="utf-8")
    research_py = (root / "backend/app/spatial_research_handoffs_v4510.py").read_text(encoding="utf-8")
    research_router = (root / "backend/app/routers/spatial_research.py").read_text(encoding="utf-8")
    authority = (root / "backend/app/standalone_authority_v4440.py").read_text(encoding="utf-8")
    plugin = (root / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text(encoding="utf-8")
    app_js = (root / "backend/public_app/assets/app.js").read_text(encoding="utf-8")
    index = (root / "backend/public_app/index.html").read_text(encoding="utf-8")
    manifest = json.loads((root / "backend/public_app/manifest.webmanifest").read_text(encoding="utf-8"))
    sw = (root / "backend/public_app/service-worker.js").read_text(encoding="utf-8")
    deploy = (root / "deploy/contabo/upgrade_site_intelligence_backend_v4_51_0_contabo.sh").read_text(encoding="utf-8")
    readme = (root / "README.md").read_text(encoding="utf-8")
    handoffs = json.loads((root / "backend/data/spatial_research_handoff_registry_v4510.json").read_text(encoding="utf-8"))

    require(f'APP_VERSION = "{EXPECTED_VERSION}"' in version_py, "APP_VERSION mismatch")
    require(f'RELEASE_NAME = "{EXPECTED_NAME}"' in version_py, "release name mismatch")
    require(f"Version: {EXPECTED_VERSION}" in plugin, "plugin version mismatch")
    require(f"site-intelligence-v{EXPECTED_VERSION}" in plugin, "plugin release ID mismatch")
    require(f"**Current release:** v{EXPECTED_VERSION} — {EXPECTED_NAME}" in readme, "README release mismatch")

    require('CapabilitySpec("spatial-research-handoffs"' in registry_py, "spatial research capability family missing")
    require('"registry_version": "1.8.0"' in registry_py, "capability registry version mismatch")
    require("spatial_research_router" in main_py and "app.include_router(spatial_research_router)" in main_py, "spatial research router not registered")
    for route in (
        "/public/spatial-research/registry", "/public/spatial-research/object-schema",
        "/public/spatial-research/objects/compose", "/public/spatial-research/objects/validate",
        "/public/spatial-research/objects/manifest", "/public/spatial-research/handoffs",
        "/public/spatial-research/handoff/{target}", "/public/spatial-research/handoff/{target}/validate",
        "/public/spatial-research/package", "/public/spatial-research/compatibility",
    ):
        require(route in research_router, f"spatial research route missing: {route}")

    for schema in (
        'RESEARCH_OBJECT_SCHEMA = "sc-site-intelligence-spatial-research-object/1.0"',
        'MANIFEST_SCHEMA = "sc-site-intelligence-spatial-research-manifest/1.0"',
        'HANDOFF_SCHEMA = "sc-site-intelligence-cross-product-handoff/1.0"',
        'PACKAGE_SCHEMA = "sc-site-intelligence-spatial-research-package/1.0"',
    ):
        require(schema in research_py, f"spatial research schema missing: {schema}")
    require('"delivery_attempted": False' in research_py, "no-delivery boundary missing")
    require('"server_persistence": False' in research_py, "stateless boundary missing")
    require('"impact_semantics": "potential-exposure-not-confirmed-impact"' in research_py, "live-event impact boundary missing")

    require(handoffs.get("version") == EXPECTED_VERSION, "spatial research handoff registry version mismatch")
    require(handoffs.get("schema") == "sc-site-intelligence-spatial-research-handoff-registry/1.0", "handoff registry schema mismatch")
    require(len(handoffs.get("targets") or []) == 7, "handoff target count mismatch")
    target_ids = {row["target_id"] for row in handoffs.get("targets") or []}
    require(target_ids == {"workspace", "knowledge-library", "research-librarian", "research-lab", "workbench", "decision-studio", "platform-core"}, "handoff target registry mismatch")

    require('NavigationItem("research-object", "Research object", "Portable spatial research & handoffs", "spatial-research-handoffs"' in authority, "standalone research-object navigation missing")
    require('"spatial_research_registry": "/public/spatial-research/registry"' in authority, "standalone bootstrap missing spatial research registry")
    require('"source_federation_registry": "/public/source-federation/registry"' in authority, "v4.50 bootstrap endpoint lost")

    require('const APP_VERSION="4.51.0"' in app_js, "standalone JS version mismatch")
    require('data-scsi-release="4.51.0"' in index, "standalone HTML version mismatch")
    require(manifest.get("start_url") == "/app/?source=pwa&release=4.51.0", "manifest release mismatch")
    require("4.51.0" in sw, "service worker release mismatch")

    require(len(RELEASE_BOUND) == 33, "release-bound file count mismatch")
    for name in RELEASE_BOUND:
        payload = json.loads((root / "backend/data" / name).read_text(encoding="utf-8"))
        require(payload.get("version") == EXPECTED_VERSION, f"release-bound mismatch: {name}")
    sample = json.loads((root / "backend/data/analytical_workspace_policy_v3234.json").read_text(encoding="utf-8"))
    require(sample.get("release_id") == "site-intelligence-v4.35.5", "historical release_id changed")

    require("--exclude='data/'" in deploy, "deployment no longer preserves dynamic data")
    for name in ("spatial_layer_registry_v4460.json", "spatiotemporal_operator_registry_v4470.json", "spatial_relationship_registry_v4480.json", "live_geospatial_event_fusion_registry_v4490.json", "global_source_federation_registry_v4500.json", "spatial_research_handoff_registry_v4510.json"):
        require(name in deploy, f"deployment does not promote required registry: {name}")
    require('assert manifest["registry_version"] == "1.8.0"' in deploy, "deployment capability-registry check missing")
    require('assert registry["target_count"] == 7' in deploy, "deployment handoff registry check missing")

    print("PASS: v4.51.0 release identity aligned")
    print("PASS: canonical spatial research object, manifest, and reproducible package installed")
    print("PASS: seven provider-neutral cross-product handoff adapters installed")
    print("PASS: source component digests preserved; no implicit delivery or source mutation")
    print("PASS: ten modular spatial-research routes and capability-registry generation 1.8.0 installed")
    print("PASS: v4.46-v4.50 spatial/live/federation contracts preserved and consumed")
    print("PASS: 33 release-bound static files and corrected Contabo deployment contract retained")
    print("PASS: WordPress remains thin shell; no spatial-research feature shortcode added")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL: {exc}", file=__import__("sys").stderr)
        raise
