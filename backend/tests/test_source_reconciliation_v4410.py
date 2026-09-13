from __future__ import annotations

import importlib
import json
from pathlib import Path

from app.version import APP_VERSION

RELEASE_BOUND_STATIC_FILES = ('analytical_workspace_policy_v3234.json', 'bootstrap_recovery_policy_v32361.json', 'briefing_publication_policy_v3290.json', 'browser_reliability_policy_v3235.json', 'comparative_model_assurance_policy_v3260.json', 'connected_platform_policy_v300.json', 'country_identity_registry_v43523.json', 'embed_isolation_policy_v32363.json', 'evidence_synthesis_policy_v2180.json', 'federation_policy_v2240.json', 'institutional_review_governance_policy_v3300.json', 'institutional_workspaces_policy_v2220.json', 'intelligence_publishing_policy_v2200.json', 'knowledge_graph_policy_v2190.json', 'knowledge_graph_relationship_registry_v2190.json', 'live_intelligence_source_registry_v320.json', 'map_interaction_policy_v3232.json', 'model_governance_policy_v2170.json', 'model_metric_registry_v2170.json', 'monitoring_early_warning_policy_v3280.json', 'mutation_observer_recovery_policy_v32362.json', 'performance_offline_policy_v3236.json', 'research_evidence_integration_policy_v3270.json', 'scheduled_monitoring_policy_v2210.json', 'spatial_evidence_policy_v2150.json', 'startup_stability_policy_v32364.json', 'unified_analytical_state_policy_v3250.json')

def _data_root() -> Path:
    return Path(__file__).resolve().parents[1] / "data"

def test_release_bound_static_versions_match_application_release() -> None:
    assert APP_VERSION == "4.41.0"
    for name in RELEASE_BOUND_STATIC_FILES:
        payload = json.loads((_data_root() / name).read_text(encoding="utf-8"))
        assert payload.get("version") == APP_VERSION, name

def test_reconciliation_preserves_historical_origin_metadata() -> None:
    payload = json.loads((_data_root() / "analytical_workspace_policy_v3234.json").read_text(encoding="utf-8"))
    assert payload["version"] == APP_VERSION
    assert payload["release_id"] == "site-intelligence-v4.35.5"

def test_application_imports_after_static_policy_reconciliation() -> None:
    module = importlib.import_module("app.main")
    assert module.app.title == "Sustainable Catalyst Site Intelligence"
