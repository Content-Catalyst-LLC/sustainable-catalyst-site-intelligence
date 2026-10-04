from __future__ import annotations

import json
import re
from pathlib import Path

from fastapi.testclient import TestClient

from app.energy_runtime_consumer import framework as energy_consumer_framework
from app.main import app
from app.version import APP_VERSION, EXPECTED_WORDPRESS_PLUGIN_VERSION, RELEASE_NAME

EXPECTED_VERSION = "4.42.1"
EXPECTED_RELEASE_NAME = "Release Identity, Static Policy & Certification Reconciliation"
RELEASE_BOUND_STATIC_FILES = (
    "analytical_workspace_policy_v3234.json",
    "bootstrap_recovery_policy_v32361.json",
    "briefing_publication_policy_v3290.json",
    "browser_reliability_policy_v3235.json",
    "comparative_model_assurance_policy_v3260.json",
    "connected_platform_policy_v300.json",
    "country_identity_registry_v43523.json",
    "embed_isolation_policy_v32363.json",
    "evidence_synthesis_policy_v2180.json",
    "federation_policy_v2240.json",
    "institutional_review_governance_policy_v3300.json",
    "institutional_workspaces_policy_v2220.json",
    "intelligence_publishing_policy_v2200.json",
    "knowledge_graph_policy_v2190.json",
    "knowledge_graph_relationship_registry_v2190.json",
    "live_intelligence_source_registry_v320.json",
    "map_interaction_policy_v3232.json",
    "model_governance_policy_v2170.json",
    "model_metric_registry_v2170.json",
    "monitoring_early_warning_policy_v3280.json",
    "mutation_observer_recovery_policy_v32362.json",
    "performance_offline_policy_v3236.json",
    "research_evidence_integration_policy_v3270.json",
    "scheduled_monitoring_policy_v2210.json",
    "spatial_evidence_policy_v2150.json",
    "startup_stability_policy_v32364.json",
    "unified_analytical_state_policy_v3250.json",
)
PROTECTED_CANONICAL_SHORTCODES = {
    "sc_earth_observation_studio",
    "sc_live_event_intelligence",
    "sc_global_country_intelligence",
    "sc_site_intelligence_embed",
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _plugin_source() -> str:
    return (
        _repo_root()
        / "wordpress-plugin"
        / "sustainable-catalyst-site-intelligence"
        / "sustainable-catalyst-site-intelligence.php"
    ).read_text(encoding="utf-8")


def _retained_shortcodes() -> list[str]:
    php = _plugin_source()
    start = php.index("public function prune_unused_shortcodes()")
    end = php.index("public static function defaults()", start)
    block = php[start:end]
    keep = block.split("array_fill_keys([", 1)[1].split("], true)", 1)[0]
    return re.findall(r"'([^']+)'", keep)


def test_v4421_canonical_release_identity_is_coherent() -> None:
    assert APP_VERSION == EXPECTED_VERSION
    assert EXPECTED_WORDPRESS_PLUGIN_VERSION == EXPECTED_VERSION
    assert RELEASE_NAME == EXPECTED_RELEASE_NAME

    root = _repo_root()
    readme = (root / "README.md").read_text(encoding="utf-8")
    plugin = _plugin_source()
    runtime = (root / "backend/public_app/assets/runtime-v3230.js").read_text(encoding="utf-8")
    app_js = (root / "backend/public_app/assets/app.js").read_text(encoding="utf-8")
    standalone = (root / "backend/public_app/index.html").read_text(encoding="utf-8")

    assert f"**Current release:** v{EXPECTED_VERSION} — {EXPECTED_RELEASE_NAME}" in readme
    assert f"Version: {EXPECTED_VERSION}" in plugin
    assert f"const VERSION = '{EXPECTED_VERSION}';" in plugin
    assert f"site-intelligence-v{EXPECTED_VERSION}" in plugin
    assert f'const VERSION = "{EXPECTED_VERSION}";' in runtime
    assert f'const APP_VERSION="{EXPECTED_VERSION}";' in app_js
    assert f'const RELEASE_LINEAGE="v{EXPECTED_VERSION}";' in app_js
    assert f"plugin_version={EXPECTED_VERSION}" in runtime
    assert f"expected_release_id=site-intelligence-v{EXPECTED_VERSION}" in runtime
    assert f'data-scsi-release="{EXPECTED_VERSION}"' in standalone


def test_v4421_release_bound_static_policy_versions_match_application() -> None:
    data_root = _repo_root() / "backend/data"
    assert len(RELEASE_BOUND_STATIC_FILES) == 27
    for name in RELEASE_BOUND_STATIC_FILES:
        payload = json.loads((data_root / name).read_text(encoding="utf-8"))
        assert payload.get("version") == APP_VERSION, name


def test_v4421_reconciliation_preserves_historical_origin_metadata() -> None:
    data_root = _repo_root() / "backend/data"
    payload = json.loads((data_root / "analytical_workspace_policy_v3234.json").read_text(encoding="utf-8"))
    assert payload["version"] == APP_VERSION
    assert payload["release_id"] == "site-intelligence-v4.35.5"


def test_v4421_shortcode_containment_contract_is_preserved_exactly() -> None:
    retained = _retained_shortcodes()
    assert len(retained) == 72
    assert len(set(retained)) == 72
    assert PROTECTED_CANONICAL_SHORTCODES.issubset(retained)
    assert len(set(retained) - PROTECTED_CANONICAL_SHORTCODES) == 68

    php = _plugin_source()
    assert "add_action('init', [$this, 'prune_unused_shortcodes'], PHP_INT_MAX);" in php
    assert "if ($ours && !isset($keep[$tag]))" in php
    assert "remove_shortcode($tag);" in php


def test_v4421_runtime_contracts_report_current_release() -> None:
    client = TestClient(app)
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["version"] == APP_VERSION

    build = client.get("/public/build-info")
    assert build.status_code == 200
    payload = build.json()
    assert payload["backend_version"] == APP_VERSION
    assert payload["expected_wordpress_plugin_version"] == APP_VERSION
    assert payload["release_name"] == RELEASE_NAME

    consumer = energy_consumer_framework()
    assert consumer["consumer_version"] == APP_VERSION
    assert consumer["target_key"] == "site-intelligence"
    assert consumer["capabilities"]["automatic_execution"] is False
    assert consumer["capabilities"]["persistence"] is False

    energy = client.get("/v1/energy-spatial/framework")
    assert energy.status_code == 200
    assert energy.json()["site_intelligence_version"] == APP_VERSION
