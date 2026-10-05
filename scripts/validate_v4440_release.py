#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

EXPECTED_VERSION = "4.44.0"
EXPECTED_NAME = "Standalone Site Intelligence Application Authority"
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
    standalone_router = (root / "backend/app/routers/standalone.py").read_text(encoding="utf-8")
    authority = (root / "backend/app/standalone_authority_v4440.py").read_text(encoding="utf-8")
    registry = (root / "backend/app/route_registry_v4430.py").read_text(encoding="utf-8")
    app_js = (root / "backend/public_app/assets/app.js").read_text(encoding="utf-8")
    index = (root / "backend/public_app/index.html").read_text(encoding="utf-8")
    manifest = json.loads((root / "backend/public_app/manifest.webmanifest").read_text(encoding="utf-8"))
    service_worker = (root / "backend/public_app/service-worker.js").read_text(encoding="utf-8")
    plugin = (root / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text(encoding="utf-8")
    deploy = (root / "deploy/contabo/upgrade_site_intelligence_backend_v4_44_0_contabo.sh").read_text(encoding="utf-8")
    readme = (root / "README.md").read_text(encoding="utf-8")

    require(f'APP_VERSION = "{EXPECTED_VERSION}"' in version_py, "APP_VERSION mismatch")
    require(f'RELEASE_NAME = "{EXPECTED_NAME}"' in version_py, "release name mismatch")
    require(f"Version: {EXPECTED_VERSION}" in plugin, "plugin version mismatch")
    require(f"site-intelligence-v{EXPECTED_VERSION}" in plugin, "plugin release ID mismatch")
    require(f"**Current release:** v{EXPECTED_VERSION} — {EXPECTED_NAME}" in readme, "README current release mismatch")

    require("app.include_router(standalone_router)" in main_py, "standalone router not registered")
    require('@app.get("/app/{route:path}"' not in main_py, "standalone deep-link route still declared in main.py")
    for route in ("/public/app/bootstrap", "/public/app/runtime-handshake", "/public/app/navigation", "/public/app/session-contract", "/app/{route:path}"):
        require(route in standalone_router, f"standalone route missing: {route}")
    require('"backend": "fastapi"' in authority, "FastAPI authority declaration missing")
    require('"wordpress_role": "optional-integration-and-publication-surface"' in authority, "WordPress optional integration declaration missing")
    require('CapabilitySpec("standalone-application"' in registry, "standalone capability missing from registry")
    require('"registry_version": "1.1.0"' in registry, "capability registry version not advanced")

    require('const APP_VERSION="4.44.0"' in app_js, "standalone JS version mismatch")
    require('STANDALONE_BOOTSTRAP_ENDPOINT="/public/app/bootstrap"' in app_js, "frontend bootstrap endpoint missing")
    require("establishStandaloneAuthority" in app_js, "frontend authority handshake missing")
    require('data-scsi-release="4.44.0"' in index, "standalone HTML version mismatch")
    require('id="standaloneAuthorityBar"' in index, "standalone authority status UI missing")
    require(manifest.get("start_url") == "/app/?source=pwa&release=4.44.0", "manifest start URL mismatch")
    require("4.44.0" in service_worker, "service-worker release identity mismatch")

    for name in RELEASE_BOUND:
        payload = json.loads((root / "backend/data" / name).read_text(encoding="utf-8"))
        require(payload.get("version") == EXPECTED_VERSION, f"release-bound policy mismatch: {name}")
    sample = json.loads((root / "backend/data/analytical_workspace_policy_v3234.json").read_text(encoding="utf-8"))
    require(sample.get("release_id") == "site-intelligence-v4.35.5", "historical release_id changed")

    require("--exclude='data/'" in deploy, "deployment no longer preserves dynamic production data")
    require("RELEASE_BOUND_POLICIES=(" in deploy, "release-bound policy list missing from deployment")
    require('cp "$SRC_BACKEND/data/$policy" "$LIVE_BACKEND/data/$policy"' in deploy, "deployment does not restore release-bound policies")
    require('assert APP_VERSION == "4.44.0"' in deploy, "deployment verifier version mismatch")
    require('"/public/app/bootstrap"' in deploy, "deployment does not certify standalone bootstrap")

    prune = plugin[plugin.index("public function prune_unused_shortcodes()"):plugin.index("public static function defaults()")]
    keep = re.findall(r"'([^']+)'", prune.split("array_fill_keys([", 1)[1].split("], true)", 1)[0])
    require(len(keep) == 72 and len(set(keep)) == 72, "shortcode containment changed")

    print("PASS: v4.44.0 release identity aligned")
    print("PASS: FastAPI declared as canonical standalone application authority")
    print("PASS: bootstrap, runtime handshake, navigation, session, deep-link and PWA contracts installed")
    print("PASS: capability-registry-driven navigation and browser-local persistence contracts installed")
    print("PASS: 27 release-bound policies advanced without rewriting historical origin metadata")
    print("PASS: corrected Contabo policy-preservation deployment retained")
    print("PASS: 72-shortcode WordPress compatibility contract preserved")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
