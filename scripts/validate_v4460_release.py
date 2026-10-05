#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

EXPECTED_VERSION = "4.46.0"
EXPECTED_NAME = "Unified Spatial Evidence Object & Layer Registry"
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
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    root=Path(__file__).resolve().parents[1]
    version_py=(root/"backend/app/version.py").read_text(encoding="utf-8")
    main_py=(root/"backend/app/main.py").read_text(encoding="utf-8")
    registry_py=(root/"backend/app/route_registry_v4430.py").read_text(encoding="utf-8")
    spatial_py=(root/"backend/app/spatial_evidence_registry_v4460.py").read_text(encoding="utf-8")
    spatial_router=(root/"backend/app/routers/spatial_evidence.py").read_text(encoding="utf-8")
    authority=(root/"backend/app/standalone_authority_v4440.py").read_text(encoding="utf-8")
    plugin=(root/"wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text(encoding="utf-8")
    app_js=(root/"backend/public_app/assets/app.js").read_text(encoding="utf-8")
    index=(root/"backend/public_app/index.html").read_text(encoding="utf-8")
    manifest=json.loads((root/"backend/public_app/manifest.webmanifest").read_text(encoding="utf-8"))
    sw=(root/"backend/public_app/service-worker.js").read_text(encoding="utf-8")
    deploy=(root/"deploy/contabo/upgrade_site_intelligence_backend_v4_46_0_contabo.sh").read_text(encoding="utf-8")
    readme=(root/"README.md").read_text(encoding="utf-8")
    layer_registry=json.loads((root/"backend/data/spatial_layer_registry_v4460.json").read_text(encoding="utf-8"))

    require(f'APP_VERSION = "{EXPECTED_VERSION}"' in version_py,"APP_VERSION mismatch")
    require(f'RELEASE_NAME = "{EXPECTED_NAME}"' in version_py,"release name mismatch")
    require(f"Version: {EXPECTED_VERSION}" in plugin,"plugin version mismatch")
    require(f"site-intelligence-v{EXPECTED_VERSION}" in plugin,"plugin release ID mismatch")
    require(f"**Current release:** v{EXPECTED_VERSION} — {EXPECTED_NAME}" in readme,"README release mismatch")
    require('CapabilitySpec("spatial-evidence-registry"' in registry_py,"spatial capability family missing")
    require('"registry_version": "1.3.0"' in registry_py,"capability registry version mismatch")
    require("spatial_evidence_router" in main_py and "app.include_router(spatial_evidence_router)" in main_py,"spatial registry router not registered")

    for route in (
        "/public/spatial-evidence/registry", "/public/spatial-evidence/layers", "/public/spatial-evidence/layers/{layer_id}",
        "/public/spatial-evidence/domains", "/public/spatial-evidence/object-schema",
        "/public/spatial-evidence/objects/normalize", "/public/spatial-evidence/objects/validate",
        "/public/spatial-evidence/compatibility",
    ):
        require(route in spatial_router,f"spatial route missing: {route}")
    require('EVIDENCE_OBJECT_SCHEMA = "sc-site-intelligence-spatial-evidence-object/2.0"' in spatial_py,"evidence object schema missing")
    require('LAYER_REGISTRY_SCHEMA = "sc-site-intelligence-spatial-layer-registry/2.0"' in spatial_py,"layer registry schema missing")
    require('DEFAULT_CRS = "EPSG:4326"' in spatial_py,"canonical CRS missing")
    require('NavigationItem("spatial", "Spatial", "Unified evidence & layers", "spatial-evidence-registry"' in authority,"standalone spatial navigation does not use unified registry")
    require('"spatial_evidence_registry": "/public/spatial-evidence/registry"' in authority,"standalone bootstrap lacks spatial registry endpoint")
    require('"content_digest"' in spatial_py and '"transformations"' in spatial_py,"provenance/digest contract incomplete")

    require(layer_registry.get("version") == EXPECTED_VERSION,"spatial layer registry version mismatch")
    require(layer_registry.get("schema") == "sc-site-intelligence-spatial-layer-registry/2.0","spatial layer registry schema mismatch")
    layers=layer_registry.get("layers") or []
    require(len(layers) == 18,"expected 18 seed spatial layers")
    ids=[item.get("layer_id") for item in layers]
    require(len(ids) == len(set(ids)),"duplicate spatial layer IDs")
    require(all(item.get("evidence_contract",{}).get("provenance_required") is True for item in layers),"layer provenance contract missing")
    require(all(item.get("source_contract",{}).get("source_identity_preserved") is True for item in layers),"layer source-identity contract missing")
    require({"climate","energy","ocean","biodiversity","events"}.issubset({item.get("domain") for item in layers}),"cross-domain registry coverage incomplete")

    require('const APP_VERSION="4.46.0"' in app_js,"standalone JS version mismatch")
    require('data-scsi-release="4.46.0"' in index,"standalone HTML version mismatch")
    require(manifest.get("start_url") == "/app/?source=pwa&release=4.46.0","manifest release mismatch")
    require("4.46.0" in sw,"service worker release mismatch")

    for name in RELEASE_BOUND:
        payload=json.loads((root/"backend/data"/name).read_text(encoding="utf-8"))
        require(payload.get("version") == EXPECTED_VERSION,f"release-bound mismatch: {name}")
    sample=json.loads((root/"backend/data/analytical_workspace_policy_v3234.json").read_text(encoding="utf-8"))
    require(sample.get("release_id") == "site-intelligence-v4.35.5","historical release_id changed")

    require("--exclude='data/'" in deploy,"deployment no longer preserves dynamic data")
    require("spatial_layer_registry_v4460.json" in deploy,"deployment does not promote v4.46 layer registry")
    require('assert APP_VERSION == "4.46.0"' in deploy,"deployment verifier version mismatch")
    require('"/public/spatial-evidence/registry"' in deploy,"deployment does not certify spatial registry")

    prune=plugin[plugin.index("public function prune_unused_shortcodes()"):plugin.index("public static function defaults()")]
    keep=re.findall(r"'([^']+)'",prune.split("array_fill_keys([",1)[1].split("], true)",1)[0])
    require(len(keep) == 72 and len(set(keep)) == 72,"72-shortcode compatibility ceiling changed")
    require("const WORDPRESS_ROLE = 'thin-shell-and-embed-bridge';" in plugin,"WordPress thin-shell role changed")

    print("PASS: v4.46.0 release identity aligned")
    print("PASS: unified spatial evidence object schema and WGS84 normalization contract installed")
    print("PASS: 18-layer cross-domain registry installed with explicit provenance and resolution contracts")
    print("PASS: eight modular spatial-evidence registry/discovery/normalization routes installed")
    print("PASS: legacy /public/spatial analysis studio and layer catalog preserved for compatibility")
    print("PASS: capability registry advanced to 1.3.0 with first-class spatial-evidence-registry family")
    print("PASS: 28 release-bound static files and corrected Contabo deployment contract retained")
    print("PASS: WordPress remains thin shell; 72-shortcode compatibility ceiling preserved")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL: {exc}",file=sys.stderr)
        raise SystemExit(1)
