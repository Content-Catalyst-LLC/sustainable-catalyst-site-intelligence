#!/usr/bin/env python3
"""Deterministic static release validator for Site Intelligence v4.42.1."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

EXPECTED_VERSION = "4.42.1"
EXPECTED_NAME = "Release Identity, Static Policy & Certification Reconciliation"
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
PROTECTED = {
    "sc_earth_observation_studio", "sc_live_event_intelligence",
    "sc_global_country_intelligence", "sc_site_intelligence_embed",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    version_py = (root / "backend/app/version.py").read_text(encoding="utf-8")
    plugin = (root / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text(encoding="utf-8")
    readme = (root / "README.md").read_text(encoding="utf-8")
    runtime = (root / "backend/public_app/assets/runtime-v3230.js").read_text(encoding="utf-8")
    app_js = (root / "backend/public_app/assets/app.js").read_text(encoding="utf-8")
    standalone = (root / "backend/public_app/index.html").read_text(encoding="utf-8")
    render_root = (root / "render.yaml").read_text(encoding="utf-8")
    render_backend = (root / "backend/render.yaml").read_text(encoding="utf-8")

    require(f'APP_VERSION = "{EXPECTED_VERSION}"' in version_py, "backend APP_VERSION mismatch")
    require(f'RELEASE_NAME = "{EXPECTED_NAME}"' in version_py, "backend release name mismatch")
    require(f"Version: {EXPECTED_VERSION}" in plugin, "WordPress plugin header mismatch")
    require(f"const VERSION = '{EXPECTED_VERSION}';" in plugin, "WordPress VERSION mismatch")
    require(f"site-intelligence-v{EXPECTED_VERSION}" in plugin, "WordPress RELEASE_ID mismatch")
    require(f"**Current release:** v{EXPECTED_VERSION} — {EXPECTED_NAME}" in readme, "README release mismatch")
    require(f'const VERSION = "{EXPECTED_VERSION}";' in runtime, "standalone runtime version mismatch")
    require(f'const APP_VERSION="{EXPECTED_VERSION}";' in app_js, "standalone application version mismatch")
    require(f'const RELEASE_LINEAGE="v{EXPECTED_VERSION}";' in app_js, "standalone application release lineage mismatch")
    require(f"plugin_version={EXPECTED_VERSION}" in runtime, "standalone release-gate plugin version mismatch")
    require(f"expected_release_id=site-intelligence-v{EXPECTED_VERSION}" in runtime, "standalone release-gate ID mismatch")
    require(f'data-scsi-release="{EXPECTED_VERSION}"' in standalone, "standalone shell release marker mismatch")
    require(f"site-intelligence-v{EXPECTED_VERSION}" in render_root, "root Render release ID mismatch")
    require(f"site-intelligence-v{EXPECTED_VERSION}" in render_backend, "backend Render release ID mismatch")

    for name in RELEASE_BOUND:
        payload = json.loads((root / "backend/data" / name).read_text(encoding="utf-8"))
        require(payload.get("version") == EXPECTED_VERSION, f"static policy version mismatch: {name}")
    sample = json.loads((root / "backend/data/analytical_workspace_policy_v3234.json").read_text(encoding="utf-8"))
    require(sample.get("release_id") == "site-intelligence-v4.35.5", "historical origin release_id was rewritten")

    prune_start = plugin.index("public function prune_unused_shortcodes()")
    prune_end = plugin.index("public static function defaults()", prune_start)
    prune = plugin[prune_start:prune_end]
    keep_source = prune.split("array_fill_keys([", 1)[1].split("], true)", 1)[0]
    keep = re.findall(r"'([^']+)'", keep_source)
    require(len(keep) == 72, f"expected 72 retained shortcodes, got {len(keep)}")
    require(len(set(keep)) == 72, "retained shortcode list contains duplicates")
    require(PROTECTED.issubset(keep), "protected canonical shortcode missing")
    require(len(set(keep) - PROTECTED) == 68, "published shortcode base is not 68")
    require("add_action('init', [$this, 'prune_unused_shortcodes'], PHP_INT_MAX);" in plugin, "late prune hook missing")

    consumer = (root / "backend/app/energy_runtime_consumer.py").read_text(encoding="utf-8")
    require("CONSUMER_VERSION = APP_VERSION" in consumer, "Energy runtime consumer is not tied to APP_VERSION")

    print(f"PASS: Site Intelligence v{EXPECTED_VERSION} canonical identity reconciled")
    print("PASS: 27 release-bound static policies match APP_VERSION")
    print("PASS: historical origin release_id metadata preserved")
    print("PASS: shortcode containment preserved at 68 published + 4 protected = 72")
    print("PASS: standalone runtime and deployment manifests match release identity")
    print("PASS: Energy Systems consumer follows canonical APP_VERSION")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
