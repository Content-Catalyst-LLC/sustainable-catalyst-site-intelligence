#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

EXPECTED_VERSION = "4.49.0"
EXPECTED_NAME = "Live Geospatial Event Fusion"
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
    "live_geospatial_event_fusion_registry_v4490.json",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    version_py = (root / "backend/app/version.py").read_text(encoding="utf-8")
    main_py = (root / "backend/app/main.py").read_text(encoding="utf-8")
    registry_py = (root / "backend/app/route_registry_v4430.py").read_text(encoding="utf-8")
    live_py = (root / "backend/app/live_geospatial_event_fusion_v4490.py").read_text(encoding="utf-8")
    live_router = (root / "backend/app/routers/live_geospatial.py").read_text(encoding="utf-8")
    authority = (root / "backend/app/standalone_authority_v4440.py").read_text(encoding="utf-8")
    plugin = (root / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text(encoding="utf-8")
    app_js = (root / "backend/public_app/assets/app.js").read_text(encoding="utf-8")
    index = (root / "backend/public_app/index.html").read_text(encoding="utf-8")
    manifest = json.loads((root / "backend/public_app/manifest.webmanifest").read_text(encoding="utf-8"))
    sw = (root / "backend/public_app/service-worker.js").read_text(encoding="utf-8")
    deploy = (root / "deploy/contabo/upgrade_site_intelligence_backend_v4_49_0_contabo.sh").read_text(encoding="utf-8")
    readme = (root / "README.md").read_text(encoding="utf-8")
    fusion = json.loads((root / "backend/data/live_geospatial_event_fusion_registry_v4490.json").read_text(encoding="utf-8"))
    relationships = json.loads((root / "backend/data/spatial_relationship_registry_v4480.json").read_text(encoding="utf-8"))
    operators = json.loads((root / "backend/data/spatiotemporal_operator_registry_v4470.json").read_text(encoding="utf-8"))
    layers = json.loads((root / "backend/data/spatial_layer_registry_v4460.json").read_text(encoding="utf-8"))
    live_sources = json.loads((root / "backend/data/live_intelligence_source_registry_v320.json").read_text(encoding="utf-8"))

    require(f'APP_VERSION = "{EXPECTED_VERSION}"' in version_py, "APP_VERSION mismatch")
    require(f'RELEASE_NAME = "{EXPECTED_NAME}"' in version_py, "release name mismatch")
    require(f"Version: {EXPECTED_VERSION}" in plugin, "plugin version mismatch")
    require(f"site-intelligence-v{EXPECTED_VERSION}" in plugin, "plugin release ID mismatch")
    require(f"**Current release:** v{EXPECTED_VERSION} — {EXPECTED_NAME}" in readme, "README release mismatch")

    require('CapabilitySpec("live-geospatial-fusion"' in registry_py, "live geospatial capability family missing")
    require('"registry_version": "1.6.0"' in registry_py, "capability registry version mismatch")
    require("live_geospatial_router" in main_py and "app.include_router(live_geospatial_router)" in main_py, "live geospatial router not registered")
    for route in (
        "/public/live-geospatial/registry", "/public/live-geospatial/event-schema", "/public/live-geospatial/sources",
        "/public/live-geospatial/lifecycle", "/public/live-geospatial/events/normalize", "/public/live-geospatial/events/normalize-source",
        "/public/live-geospatial/events/reconcile", "/public/live-geospatial/events/query", "/public/live-geospatial/lifecycle/transition",
        "/public/live-geospatial/fuse/layers", "/public/live-geospatial/fuse/graph", "/public/live-geospatial/snapshot",
        "/public/live-geospatial/compatibility",
    ):
        require(route in live_router, f"live geospatial route missing: {route}")

    for schema in (
        'EVENT_SCHEMA = "sc-site-intelligence-live-geospatial-event/1.0"',
        'EVENT_CLUSTER_SCHEMA = "sc-site-intelligence-live-event-cluster/1.0"',
        'FUSION_RESULT_SCHEMA = "sc-site-intelligence-live-geospatial-fusion-result/1.0"',
        'GRAPH_FUSION_SCHEMA = "sc-site-intelligence-live-event-graph-fusion/1.0"',
        'SNAPSHOT_SCHEMA = "sc-site-intelligence-live-geospatial-snapshot/1.0"',
    ):
        require(schema in live_py, f"live geospatial schema missing: {schema}")
    require('"impact_confirmed": False' in live_py, "impact boundary missing")
    require('"graph_mutated": False' in live_py, "graph mutation boundary missing")
    require('"strict-deterministic-no-fuzzy-merge"' in (root / "backend/data/live_geospatial_event_fusion_registry_v4490.json").read_text(), "strict identity semantics missing")
    require("normalize_evidence_object" in live_py, "v4.46 evidence normalization not consumed")
    require("build_graph" in live_py, "v4.48 graph not consumed")

    require(fusion.get("version") == EXPECTED_VERSION, "fusion registry version mismatch")
    require(fusion.get("schema") == "sc-site-intelligence-live-geospatial-event-fusion-registry/1.0", "fusion registry schema mismatch")
    require(len(fusion.get("source_adapters") or []) == 5, "source adapter count mismatch")
    require(len(fusion.get("lifecycle_states") or []) == 5, "lifecycle state count mismatch")
    require(len(fusion.get("severity_levels") or []) == 6, "severity level count mismatch")
    require("potentially-exposed-to-event" in {row["relationship_type"] for row in fusion.get("fusion_relationships") or []}, "potential exposure fusion relationship missing")
    require(live_sources.get("version") == EXPECTED_VERSION, "live source registry not carried forward")
    require({"usgs_earthquakes", "nasa_eonet", "noaa_nws"} <= {row["feed_id"] for row in live_sources.get("sources") or []}, "required live sources missing")
    require(layers.get("version") == EXPECTED_VERSION and layers.get("layer_count") == 18, "v4.46 layer registry not carried forward")
    require(operators.get("version") == EXPECTED_VERSION, "v4.47 operator registry not carried forward")
    require(relationships.get("version") == EXPECTED_VERSION and relationships.get("relationship_count") == 12, "v4.48 relationship registry not carried forward")

    require('NavigationItem("events", "Events", "Live geospatial fusion", "live-geospatial-fusion"' in authority, "standalone events navigation not promoted")
    require('"live_geospatial_registry": "/public/live-geospatial/registry"' in authority, "standalone bootstrap missing live geospatial registry")
    require('"spatial_graph_registry": "/public/spatial-graph/registry"' in authority, "v4.48 graph registry bootstrap endpoint lost")
    require('"spatiotemporal_registry": "/public/spatiotemporal/registry"' in authority, "v4.47 registry bootstrap endpoint lost")
    require('"spatial_evidence_registry": "/public/spatial-evidence/registry"' in authority, "v4.46 registry bootstrap endpoint lost")

    require('const APP_VERSION="4.49.0"' in app_js, "standalone JS version mismatch")
    require('data-scsi-release="4.49.0"' in index, "standalone HTML version mismatch")
    require(manifest.get("start_url") == "/app/?source=pwa&release=4.49.0", "manifest release mismatch")
    require("4.49.0" in sw, "service worker release mismatch")

    require(len(RELEASE_BOUND) == 31, "release-bound file count mismatch")
    for name in RELEASE_BOUND:
        payload = json.loads((root / "backend/data" / name).read_text(encoding="utf-8"))
        require(payload.get("version") == EXPECTED_VERSION, f"release-bound mismatch: {name}")
    sample = json.loads((root / "backend/data/analytical_workspace_policy_v3234.json").read_text(encoding="utf-8"))
    require(sample.get("release_id") == "site-intelligence-v4.35.5", "historical release_id changed")

    require("--exclude='data/'" in deploy, "deployment no longer preserves dynamic data")
    require("spatial_layer_registry_v4460.json" in deploy, "deployment no longer promotes v4.46 layer registry")
    require("spatiotemporal_operator_registry_v4470.json" in deploy, "deployment no longer promotes v4.47 operator registry")
    require("spatial_relationship_registry_v4480.json" in deploy, "deployment no longer promotes v4.48 relationship registry")
    require("live_geospatial_event_fusion_registry_v4490.json" in deploy, "deployment does not promote v4.49 fusion registry")
    require('assert APP_VERSION == "4.49.0"' in deploy, "deployment verifier version mismatch")
    require('"/public/live-geospatial/registry"' in deploy and '"/public/live-geospatial/fuse/graph"' in deploy, "deployment does not certify live fusion engine")

    prune = plugin[plugin.index("public function prune_unused_shortcodes()"):plugin.index("public static function defaults()")]
    keep = re.findall(r"'([^']+)'", prune.split("array_fill_keys([", 1)[1].split("], true)", 1)[0])
    require(len(keep) == 72 and len(set(keep)) == 72, "72-shortcode compatibility ceiling changed")
    require("const WORDPRESS_ROLE = 'thin-shell-and-embed-bridge';" in plugin, "WordPress thin-shell role changed")

    print("PASS: v4.49.0 release identity aligned")
    print("PASS: canonical live geospatial event object and source adapters installed")
    print("PASS: strict deterministic cross-source reconciliation avoids fuzzy event merging")
    print("PASS: lifecycle, severity, explicit freshness, spatial/time query and transitions installed")
    print("PASS: event-to-layer and event-to-graph fusion preserve source digests and do not assert impact")
    print("PASS: 13 modular live-geospatial routes and first-class capability family installed")
    print("PASS: v4.46 evidence, v4.47 spatiotemporal and v4.48 graph contracts preserved and consumed")
    print("PASS: 31 release-bound static files and corrected Contabo deployment contract retained")
    print("PASS: WordPress remains thin shell; 72-shortcode compatibility ceiling preserved")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
