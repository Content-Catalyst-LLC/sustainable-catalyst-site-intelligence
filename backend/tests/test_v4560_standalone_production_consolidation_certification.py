from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.production_consolidation_v4560 import checklist, manifest, release_snapshot
from app.route_registry_v4430 import capability_manifest
from app.version import APP_VERSION, RELEASE_NAME

ROOT = Path(__file__).resolve().parents[2]
client = TestClient(app)

RELEASE_BOUND_POLICIES = (
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
    "spatial_research_handoff_registry_v4510.json", "predictive_spatial_consumer_registry_v4520.json",
    "scenario_exposure_change_registry_v4530.json", "advanced_domain_workspace_registry_v4530.json",
    "reproducible_spatial_package_registry_v4540.json", "spatial_provenance_lineage_registry_v4550.json",
    "advanced_domain_intelligence_registry_v4552.json", "standalone_web_application_registry_v4553.json",
    "api_reliability_contract_v45531.json", "live_probe_consistency_registry_v455311.json",
    "standalone_functional_parity_registry_v45532.json", "runtime_health_domain_context_registry_v455321.json",
    "browser_api_transport_registry_v455322.json", "production_consolidation_registry_v4560.json",
)


def test_release_identity_and_inventory_are_consolidated():
    assert APP_VERSION == "4.56.0"
    assert RELEASE_NAME == "Standalone Production Consolidation & Certification"
    inventory = capability_manifest(app.routes)
    assert inventory["registry_version"] == "2.7.0"
    assert inventory["route_count"] == 1521
    assert inventory["modularized_route_count"] == 212
    assert inventory["capability_count"] == 32
    assert inventory["unclassified_route_count"] == 0
    family = next(x for x in inventory["capabilities"] if x["capability_id"] == "production-certification")
    assert family["route_count"] == 3
    assert family["modularized_route_count"] == 3


def test_static_production_contract_is_certified_without_claiming_live_dependency_state():
    data = manifest()
    result = checklist()
    assert data["version"] == APP_VERSION
    assert result["ok"] is True
    assert result["contract_status"] == "contract-certified"
    assert result["live_runtime_asserted"] is False
    assert result["workspace_count"] == 33
    assert result["functional_control_count"] == 12
    assert result["deep_link_alias_count"] == 11
    assert all(row["pass"] for row in result["checks"])


def test_release_snapshot_is_deterministic_and_content_addressed():
    a = release_snapshot()
    b = release_snapshot()
    assert a == b
    assert len(a["sha256"]) == 64
    assert a["payload"]["deployment_order"] == ["backend", "web"]


def test_production_certification_routes_are_public_and_machine_readable():
    for path in (
        "/public/production-certification",
        "/public/production-certification/checklist",
        "/public/production-certification/release",
    ):
        response = client.get(path)
        assert response.status_code == 200, response.text
        assert response.json()["version"] == APP_VERSION


def test_all_release_bound_policy_versions_are_aligned():
    assert len(RELEASE_BOUND_POLICIES) == 46
    data_root = ROOT / "backend" / "data"
    for name in RELEASE_BOUND_POLICIES:
        payload = json.loads((data_root / name).read_text(encoding="utf-8"))
        assert payload.get("version") == APP_VERSION, name


def test_public_surfaces_share_release_identity_and_wordpress_remains_non_authoritative():
    web_config = (ROOT / "web" / "config.js").read_text(encoding="utf-8")
    legacy_index = (ROOT / "backend" / "public_app" / "index.html").read_text(encoding="utf-8")
    plugin = (ROOT / "wordpress-plugin" / "sustainable-catalyst-site-intelligence" / "sustainable-catalyst-site-intelligence.php").read_text(encoding="utf-8")
    assert 'release: "4.56.0"' in web_config
    assert 'runtimeMode: "standalone-production-certified"' in web_config
    assert 'v=4.56.0' in legacy_index
    assert "const VERSION = '4.56.0';" in plugin
    assert "const WORDPRESS_ROLE = 'public-site-launch-bridge';" in plugin
    assert "const STANDALONE_WEB_APP_URL = 'https://intelligence.sustainablecatalyst.com';" in plugin


def test_release_does_not_claim_domain_data_activation():
    boundaries = manifest()["scope_boundaries"]
    assert "No new domain-data activation." in boundaries
    assert "No fabricated records or synthetic readiness." in boundaries
