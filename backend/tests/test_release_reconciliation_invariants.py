from __future__ import annotations

import json
import re
from pathlib import Path

from fastapi.testclient import TestClient

from app.energy_runtime_consumer import framework as energy_consumer_framework
from app.main import app
from app.version import APP_VERSION, EXPECTED_WORDPRESS_PLUGIN_VERSION, RELEASE_NAME

RELEASE_BOUND_STATIC_FILES = (
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
PROTECTED_CANONICAL_SHORTCODES = {
    "sc_earth_observation_studio", "sc_live_event_intelligence",
    "sc_global_country_intelligence", "sc_site_intelligence_embed",
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _plugin_source() -> str:
    return (_repo_root() / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text(encoding="utf-8")


def _retained_shortcodes() -> list[str]:
    php = _plugin_source()
    start = php.index("public function prune_unused_shortcodes()")
    end = php.index("public static function defaults()", start)
    block = php[start:end]
    keep = block.split("array_fill_keys([", 1)[1].split("], true)", 1)[0]
    return re.findall(r"'([^']+)'", keep)


def test_release_identity_remains_coherent() -> None:
    root = _repo_root()
    readme = (root / "README.md").read_text(encoding="utf-8")
    plugin = _plugin_source()
    runtime = (root / "backend/public_app/assets/runtime-v3230.js").read_text(encoding="utf-8")
    app_js = (root / "backend/public_app/assets/app.js").read_text(encoding="utf-8")
    standalone = (root / "backend/public_app/index.html").read_text(encoding="utf-8")

    assert EXPECTED_WORDPRESS_PLUGIN_VERSION == APP_VERSION
    assert f"**Current release:** v{APP_VERSION} — {RELEASE_NAME}" in readme
    assert f"Version: {APP_VERSION}" in plugin
    assert f"const VERSION = '{APP_VERSION}';" in plugin
    assert f"site-intelligence-v{APP_VERSION}" in plugin
    assert f'const VERSION = "{APP_VERSION}";' in runtime
    assert f'const APP_VERSION="{APP_VERSION}";' in app_js
    assert f'const RELEASE_LINEAGE="v{APP_VERSION}";' in app_js
    assert f"plugin_version={APP_VERSION}" in runtime
    assert f"expected_release_id=site-intelligence-v{APP_VERSION}" in runtime
    assert f'data-scsi-release="{APP_VERSION}"' in standalone


def test_release_bound_static_policy_versions_follow_application() -> None:
    data_root = _repo_root() / "backend/data"
    assert len(RELEASE_BOUND_STATIC_FILES) == 27
    for name in RELEASE_BOUND_STATIC_FILES:
        payload = json.loads((data_root / name).read_text(encoding="utf-8"))
        assert payload.get("version") == APP_VERSION, name
    sample = json.loads((data_root / "analytical_workspace_policy_v3234.json").read_text(encoding="utf-8"))
    assert sample["release_id"] == "site-intelligence-v4.35.5"


def test_shortcode_containment_contract_remains_exact() -> None:
    retained = _retained_shortcodes()
    assert len(retained) == 72
    assert len(set(retained)) == 72
    assert PROTECTED_CANONICAL_SHORTCODES.issubset(retained)
    assert len(set(retained) - PROTECTED_CANONICAL_SHORTCODES) == 68


def test_runtime_contracts_report_current_release() -> None:
    client = TestClient(app)
    assert client.get("/health").json()["version"] == APP_VERSION
    build = client.get("/public/build-info").json()
    assert build["backend_version"] == APP_VERSION
    assert build["expected_wordpress_plugin_version"] == APP_VERSION
    assert build["release_name"] == RELEASE_NAME
    consumer = energy_consumer_framework()
    assert consumer["consumer_version"] == APP_VERSION
