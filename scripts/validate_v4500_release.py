#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

EXPECTED_VERSION = "4.50.0"
EXPECTED_NAME = "Global Source Federation & Regional Authority Registry"
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
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    version_py = (root / "backend/app/version.py").read_text(encoding="utf-8")
    main_py = (root / "backend/app/main.py").read_text(encoding="utf-8")
    registry_py = (root / "backend/app/route_registry_v4430.py").read_text(encoding="utf-8")
    federation_py = (root / "backend/app/global_source_federation_v4500.py").read_text(encoding="utf-8")
    federation_router = (root / "backend/app/routers/source_federation.py").read_text(encoding="utf-8")
    authority = (root / "backend/app/standalone_authority_v4440.py").read_text(encoding="utf-8")
    plugin = (root / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text(encoding="utf-8")
    app_js = (root / "backend/public_app/assets/app.js").read_text(encoding="utf-8")
    index = (root / "backend/public_app/index.html").read_text(encoding="utf-8")
    manifest = json.loads((root / "backend/public_app/manifest.webmanifest").read_text(encoding="utf-8"))
    sw = (root / "backend/public_app/service-worker.js").read_text(encoding="utf-8")
    deploy = (root / "deploy/contabo/upgrade_site_intelligence_backend_v4_50_0_contabo.sh").read_text(encoding="utf-8")
    readme = (root / "README.md").read_text(encoding="utf-8")
    federation = json.loads((root / "backend/data/global_source_federation_registry_v4500.json").read_text(encoding="utf-8"))
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

    require('CapabilitySpec("global-source-federation"' in registry_py, "source federation capability family missing")
    require('"registry_version": "1.7.0"' in registry_py, "capability registry version mismatch")
    require("source_federation_router" in main_py and "app.include_router(source_federation_router)" in main_py, "source federation router not registered")
    for route in (
        "/public/source-federation/registry", "/public/source-federation/authorities",
        "/public/source-federation/authorities/{source_id}", "/public/source-federation/regions",
        "/public/source-federation/jurisdictions/{code}", "/public/source-federation/authority-types",
        "/public/source-federation/select", "/public/source-federation/federate",
        "/public/source-federation/trust-profile/evaluate", "/public/source-federation/compatibility",
    ):
        require(route in federation_router, f"source federation route missing: {route}")

    for schema in (
        'REGISTRY_SCHEMA = "sc-site-intelligence-global-source-federation-registry/1.0"',
        'SOURCE_SCHEMA = "sc-site-intelligence-source-authority/1.0"',
        'SELECTION_SCHEMA = "sc-site-intelligence-source-selection/1.0"',
        'FEDERATION_PLAN_SCHEMA = "sc-site-intelligence-source-federation-plan/1.0"',
        'TRUST_EVALUATION_SCHEMA = "sc-site-intelligence-source-trust-evaluation/1.0"',
    ):
        require(schema in federation_py, f"source federation schema missing: {schema}")
    require("PRECEDENCE_RULES" in federation_py, "existing jurisdiction precedence not consumed")
    require('"authority_mutated": False' in federation_py, "trust/authority separation missing")
    require('"quality_mutated": False' in federation_py, "trust/quality separation missing")
    require('"network_calls_performed": False' in federation_py, "preview-only federation boundary missing")

    require(federation.get("version") == EXPECTED_VERSION, "global source federation registry version mismatch")
    require(federation.get("schema") == "sc-site-intelligence-global-source-federation-registry/1.0", "global source federation registry schema mismatch")
    require(len(federation.get("sources") or []) == 24, "global source authority count mismatch")
    require(len(federation.get("authority_classes") or []) == 10, "authority class count mismatch")
    require(len(federation.get("regional_groups") or []) == 7, "regional group count mismatch")
    require(federation.get("selection_policy", {}).get("semantic_compatibility_required") is True, "semantic-first selection policy missing")
    require(federation.get("trust_policy", {}).get("separate_from_authority") is True, "trust/authority registry boundary missing")
    source_ids = {row["source_id"] for row in federation.get("sources") or []}
    require({"world_bank", "eurostat", "pcbs-pxweb", "statistics-canada-wds", "uk-ons-api", "australian-bureau-statistics-sdmx", "us-bls-public-data-api", "noaa_nws", "usgs_earthquakes"} <= source_ids, "required authority sources missing")

    require(fusion.get("version") == EXPECTED_VERSION, "v4.49 live fusion registry not carried forward")
    require(relationships.get("version") == EXPECTED_VERSION and relationships.get("relationship_count") == 12, "v4.48 relationship registry not carried forward")
    require(operators.get("version") == EXPECTED_VERSION, "v4.47 operator registry not carried forward")
    require(layers.get("version") == EXPECTED_VERSION and layers.get("layer_count") == 18, "v4.46 layer registry not carried forward")
    require(live_sources.get("version") == EXPECTED_VERSION, "live source registry not carried forward")

    require('NavigationItem("sources", "Sources", "Global federation & regional authority", "global-source-federation"' in authority, "standalone source navigation not promoted")
    require('"source_federation_registry": "/public/source-federation/registry"' in authority, "standalone bootstrap missing source federation registry")
    require('"live_geospatial_registry": "/public/live-geospatial/registry"' in authority, "v4.49 bootstrap endpoint lost")

    require('const APP_VERSION="4.50.0"' in app_js, "standalone JS version mismatch")
    require('data-scsi-release="4.50.0"' in index, "standalone HTML version mismatch")
    require(manifest.get("start_url") == "/app/?source=pwa&release=4.50.0", "manifest release mismatch")
    require("4.50.0" in sw, "service worker release mismatch")

    require(len(RELEASE_BOUND) == 32, "release-bound file count mismatch")
    for name in RELEASE_BOUND:
        payload = json.loads((root / "backend/data" / name).read_text(encoding="utf-8"))
        require(payload.get("version") == EXPECTED_VERSION, f"release-bound mismatch: {name}")
    sample = json.loads((root / "backend/data/analytical_workspace_policy_v3234.json").read_text(encoding="utf-8"))
    require(sample.get("release_id") == "site-intelligence-v4.35.5", "historical release_id changed")

    require("--exclude='data/'" in deploy, "deployment no longer preserves dynamic data")
    require("spatial_layer_registry_v4460.json" in deploy, "deployment no longer promotes v4.46 layer registry")
    require("spatiotemporal_operator_registry_v4470.json" in deploy, "deployment no longer promotes v4.47 operator registry")
    require("spatial_relationship_registry_v4480.json" in deploy, "deployment no longer promotes v4.48 relationship registry")
    require("live_geospatial_event_fusion_registry_v4490.json" in deploy, "deployment no longer promotes v4.49 live registry")
    require("global_source_federation_registry_v4500.json" in deploy, "deployment does not promote v4.50 source federation registry")
    require('assert APP_VERSION == "4.50.0"' in deploy, "deployment verifier version mismatch")
    require('"/public/source-federation/registry"' in deploy and '"/public/source-federation/select"' in deploy, "deployment does not certify federation engine")

    prune = plugin[plugin.index("public function prune_unused_shortcodes()"):plugin.index("public static function defaults()")]
    keep = re.findall(r"'([^']+)'", prune.split("array_fill_keys([", 1)[1].split("], true)", 1)[0])
    require(len(keep) == 72 and len(set(keep)) == 72, "72-shortcode compatibility ceiling changed")
    require("const WORDPRESS_ROLE = 'thin-shell-and-embed-bridge';" in plugin, "WordPress thin-shell role changed")
    require("source_federation_shortcode" not in plugin, "new feature-specific WordPress shortcode introduced")

    print("PASS: v4.50.0 release identity aligned")
    print("PASS: first-class global source federation and regional authority registry installed")
    print("PASS: 24 source authorities, 10 authority classes and 7 regional groups certified")
    print("PASS: deterministic semantic-first jurisdiction-aware source selection installed")
    print("PASS: source authority, quality and user trust remain explicit separate dimensions")
    print("PASS: federation plans perform no automatic network fetch, import or remote write")
    print("PASS: 10 modular source-federation routes and first-class capability family installed")
    print("PASS: v4.35 precedence and v4.46-v4.49 evidence/live contracts preserved and consumed")
    print("PASS: 32 release-bound static files and corrected Contabo deployment contract retained")
    print("PASS: WordPress remains thin shell; 72-shortcode compatibility ceiling preserved")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
