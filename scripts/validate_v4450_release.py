#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

EXPECTED_VERSION = "4.45.0"
EXPECTED_NAME = "WordPress Thin-Shell & Embed Bridge"
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
    registry = (root / "backend/app/route_registry_v4430.py").read_text(encoding="utf-8")
    bridge = (root / "backend/app/wordpress_bridge_v4450.py").read_text(encoding="utf-8")
    bridge_router = (root / "backend/app/routers/wordpress_bridge.py").read_text(encoding="utf-8")
    authority = (root / "backend/app/standalone_authority_v4440.py").read_text(encoding="utf-8")
    plugin = (root / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text(encoding="utf-8")
    wp_js = (root / "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js").read_text(encoding="utf-8")
    app_js = (root / "backend/public_app/assets/app.js").read_text(encoding="utf-8")
    index = (root / "backend/public_app/index.html").read_text(encoding="utf-8")
    manifest = json.loads((root / "backend/public_app/manifest.webmanifest").read_text(encoding="utf-8"))
    service_worker = (root / "backend/public_app/service-worker.js").read_text(encoding="utf-8")
    deploy = (root / "deploy/contabo/upgrade_site_intelligence_backend_v4_45_0_contabo.sh").read_text(encoding="utf-8")
    readme = (root / "README.md").read_text(encoding="utf-8")

    require(f'APP_VERSION = "{EXPECTED_VERSION}"' in version_py, "APP_VERSION mismatch")
    require(f'RELEASE_NAME = "{EXPECTED_NAME}"' in version_py, "release name mismatch")
    require(f"Version: {EXPECTED_VERSION}" in plugin, "plugin version mismatch")
    require(f"site-intelligence-v{EXPECTED_VERSION}" in plugin, "plugin release ID mismatch")
    require(f"**Current release:** v{EXPECTED_VERSION} — {EXPECTED_NAME}" in readme, "README release mismatch")

    require("wordpress_bridge_router" in main_py and "app.include_router(wordpress_bridge_router)" in main_py, "WordPress bridge router not registered")
    for route in (
        "/public/integrations/wordpress/bridge",
        "/public/integrations/wordpress/embed-contract",
        "/public/integrations/wordpress/auth-handoff",
        "/public/integrations/wordpress/compatibility",
    ):
        require(route in bridge_router, f"bridge route missing: {route}")
    require('WORDPRESS_ROLE = "thin-shell-and-embed-bridge"' in bridge, "thin-shell role missing")
    require('"wordpress_feature_authority": False' in bridge, "WordPress feature-authority boundary missing")
    require('"wordpress_new_feature_shortcodes": False' in bridge, "new-feature shortcode boundary missing")
    require('"token_transport": "not-enabled"' in bridge, "auth handoff boundary missing")
    require('CapabilitySpec("wordpress-integration"' in registry, "WordPress capability family missing")
    require('"registry_version": "1.2.0"' in registry, "capability registry version mismatch")
    require('"wordpress_role": "thin-shell-and-embed-bridge"' in authority, "standalone bootstrap thin-shell role missing")
    require('STANDALONE_CONTRACT_VERSION = "1.1.0"' in authority, "standalone contract not advanced")

    require("const BRIDGE_CONTRACT_VERSION = '1.0.0';" in plugin, "plugin bridge contract constant missing")
    require("const WORDPRESS_ROLE = 'thin-shell-and-embed-bridge';" in plugin, "plugin role constant missing")
    for route in ("/bridge", "/bridge/bootstrap", "/bridge/navigation", "/bridge/embed-contract", "/bridge/auth-handoff", "/bridge/compatibility"):
        require(f"'{route}'" in plugin, f"WordPress bridge REST route missing: {route}")
    require("$query['surface'] = 'wordpress-embed';" in plugin, "embed surface marker missing")
    require("$query['bridge'] = 'wordpress';" in plugin, "embed bridge marker missing")
    require("$query['bridge_version'] = self::BRIDGE_CONTRACT_VERSION;" in plugin, "embed bridge version missing")
    generic = plugin[plugin.index("function scsi_site_intelligence_embed_shortcode_v2110"):plugin.index("add_shortcode('sc_site_intelligence_embed'", plugin.index("function scsi_site_intelligence_embed_shortcode_v2110"))]
    require("$this->app_embed_url" not in generic, "protected generic embed still depends on invalid $this context")
    require("SC_Site_Intelligence_Plugin::options()" in generic, "protected generic embed does not use canonical plugin options")

    require('const APP_VERSION="4.45.0"' in app_js, "standalone JS version mismatch")
    require('type:"scsi-wordpress-bridge-ready"' in app_js, "standalone bridge-ready message missing")
    require("scsi-wordpress-bridge-ready" in wp_js, "WordPress bridge listener missing")
    require("event.origin !== record.origin" in wp_js, "WordPress message origin validation missing")
    require('data-scsi-release="4.45.0"' in index, "standalone HTML version mismatch")
    require(manifest.get("start_url") == "/app/?source=pwa&release=4.45.0", "manifest release mismatch")
    require("4.45.0" in service_worker, "service worker release mismatch")

    for name in RELEASE_BOUND:
        payload = json.loads((root / "backend/data" / name).read_text(encoding="utf-8"))
        require(payload.get("version") == EXPECTED_VERSION, f"policy mismatch: {name}")
    sample = json.loads((root / "backend/data/analytical_workspace_policy_v3234.json").read_text(encoding="utf-8"))
    require(sample.get("release_id") == "site-intelligence-v4.35.5", "historical release_id changed")

    require("--exclude='data/'" in deploy, "deployment no longer preserves dynamic data")
    require("RELEASE_BOUND_POLICIES=(" in deploy, "release-bound policy deployment missing")
    require('assert APP_VERSION == "4.45.0"' in deploy, "deployment verifier version mismatch")
    require('"/public/integrations/wordpress/bridge"' in deploy, "deployment does not certify WordPress bridge")

    prune = plugin[plugin.index("public function prune_unused_shortcodes()"):plugin.index("public static function defaults()")]
    keep = re.findall(r"'([^']+)'", prune.split("array_fill_keys([", 1)[1].split("], true)", 1)[0])
    require(len(keep) == 72 and len(set(keep)) == 72, "72-shortcode compatibility ceiling changed")

    print("PASS: v4.45.0 release identity aligned")
    print("PASS: FastAPI remains product authority; WordPress declared thin shell/embed bridge")
    print("PASS: four backend WordPress integration contracts installed and modularized")
    print("PASS: WordPress bridge/bootstrap/navigation/embed compatibility REST surfaces installed")
    print("PASS: canonical iframe bridge carries release/surface/bridge contract markers")
    print("PASS: protected generic embed repaired and browser bridge is origin/version checked")
    print("PASS: 27 release-bound policies and corrected Contabo deployment contract retained")
    print("PASS: 72-shortcode published compatibility ceiling preserved; new feature shortcodes prohibited")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
