#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "4.56.0"
RELEASE = "Standalone Production Consolidation & Certification"
POLICIES = [
  "analytical_workspace_policy_v3234.json","bootstrap_recovery_policy_v32361.json","briefing_publication_policy_v3290.json","browser_reliability_policy_v3235.json","comparative_model_assurance_policy_v3260.json","connected_platform_policy_v300.json","country_identity_registry_v43523.json","embed_isolation_policy_v32363.json","evidence_synthesis_policy_v2180.json","federation_policy_v2240.json","institutional_review_governance_policy_v3300.json","institutional_workspaces_policy_v2220.json","intelligence_publishing_policy_v2200.json","knowledge_graph_policy_v2190.json","knowledge_graph_relationship_registry_v2190.json","live_intelligence_source_registry_v320.json","map_interaction_policy_v3232.json","model_governance_policy_v2170.json","model_metric_registry_v2170.json","monitoring_early_warning_policy_v3280.json","mutation_observer_recovery_policy_v32362.json","performance_offline_policy_v3236.json","research_evidence_integration_policy_v3270.json","scheduled_monitoring_policy_v2210.json","spatial_evidence_policy_v2150.json","startup_stability_policy_v32364.json","unified_analytical_state_policy_v3250.json","spatial_layer_registry_v4460.json","spatiotemporal_operator_registry_v4470.json","spatial_relationship_registry_v4480.json","live_geospatial_event_fusion_registry_v4490.json","global_source_federation_registry_v4500.json","spatial_research_handoff_registry_v4510.json","predictive_spatial_consumer_registry_v4520.json","scenario_exposure_change_registry_v4530.json","advanced_domain_workspace_registry_v4530.json","reproducible_spatial_package_registry_v4540.json","spatial_provenance_lineage_registry_v4550.json","advanced_domain_intelligence_registry_v4552.json","standalone_web_application_registry_v4553.json","api_reliability_contract_v45531.json","live_probe_consistency_registry_v455311.json","standalone_functional_parity_registry_v45532.json","runtime_health_domain_context_registry_v455321.json","browser_api_transport_registry_v455322.json","production_consolidation_registry_v4560.json"
]

def need(path: str) -> Path:
    p=ROOT/path
    assert p.is_file(), f"missing: {path}"
    print(f"PASS: file exists: {path}")
    return p

def main() -> None:
    version=need("backend/app/version.py").read_text()
    assert f'APP_VERSION = "{VERSION}"' in version
    assert f'RELEASE_NAME = "{RELEASE}"' in version
    print("PASS: release identity 4.56.0")
    registry=json.loads(need("backend/data/production_consolidation_registry_v4560.json").read_text())
    assert registry["version"]==VERSION and registry["release_name"]==RELEASE
    assert registry["expected_inventory"]=={"registry_version":"2.7.0","route_count":1521,"modularized_route_count":212,"capability_count":32,"unclassified_route_count":0}
    print("PASS: production consolidation registry aligned")
    rr=need("backend/app/route_registry_v4430.py").read_text()
    assert 'CapabilitySpec("production-certification"' in rr
    assert '"registry_version": "2.7.0"' in rr
    main_src=need("backend/app/main.py").read_text()
    assert "production_certification_router" in main_src
    routers=need("backend/app/routers/__init__.py").read_text()
    assert "production_certification_router" in routers
    for name in POLICIES:
        payload=json.loads(need(f"backend/data/{name}").read_text())
        assert payload.get("version")==VERSION, (name,payload.get("version"))
    assert len(POLICIES)==46
    print("PASS: 46 release-bound policies aligned to 4.56.0")
    web=need("web/config.js").read_text()
    assert 'release: "4.56.0"' in web
    assert 'runtimeMode: "standalone-production-certified"' in web
    legacy_index=need("backend/public_app/index.html").read_text()
    assert 'v=4.56.0' in legacy_index
    plugin=need("wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text()
    assert "Version: 4.56.0" in plugin
    assert "const VERSION = '4.56.0';" in plugin
    assert "const WORDPRESS_ROLE = 'public-site-launch-bridge';" in plugin
    for path in [
      "backend/app/production_consolidation_v4560.py",
      "backend/app/routers/production_certification.py",
      "backend/tests/test_v4560_standalone_production_consolidation_certification.py",
      "scripts/browser_certify_v4560.py",
      "deploy/contabo/upgrade_site_intelligence_backend_v4_56_0_contabo.sh",
      "deploy/contabo/upgrade_site_intelligence_web_v4_56_0_contabo.sh",
      "deploy/contabo/site-intelligence-web-v4560.Caddyfile",
      "docs/V4560_RELEASE_NOTES.md","docs/V4560_RELEASE_CERTIFICATION.md","docs/V4560_INSTALL_AND_VERIFY.md"
    ]: need(path)
    print("V4560_RELEASE_VALIDATION=PASS")

if __name__=="__main__": main()
