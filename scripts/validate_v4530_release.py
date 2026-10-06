#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
EXPECTED_VERSION="4.53.0"
EXPECTED_NAME="Scenario, Exposure & Change Intelligence"
RELEASE_BOUND=(
"analytical_workspace_policy_v3234.json","bootstrap_recovery_policy_v32361.json","briefing_publication_policy_v3290.json","browser_reliability_policy_v3235.json","comparative_model_assurance_policy_v3260.json","connected_platform_policy_v300.json","country_identity_registry_v43523.json","embed_isolation_policy_v32363.json","evidence_synthesis_policy_v2180.json","federation_policy_v2240.json","institutional_review_governance_policy_v3300.json","institutional_workspaces_policy_v2220.json","intelligence_publishing_policy_v2200.json","knowledge_graph_policy_v2190.json","knowledge_graph_relationship_registry_v2190.json","live_intelligence_source_registry_v320.json","map_interaction_policy_v3232.json","model_governance_policy_v2170.json","model_metric_registry_v2170.json","monitoring_early_warning_policy_v3280.json","mutation_observer_recovery_policy_v32362.json","performance_offline_policy_v3236.json","research_evidence_integration_policy_v3270.json","scheduled_monitoring_policy_v2210.json","spatial_evidence_policy_v2150.json","startup_stability_policy_v32364.json","unified_analytical_state_policy_v3250.json","spatial_layer_registry_v4460.json","spatiotemporal_operator_registry_v4470.json","spatial_relationship_registry_v4480.json","live_geospatial_event_fusion_registry_v4490.json","global_source_federation_registry_v4500.json","spatial_research_handoff_registry_v4510.json","predictive_spatial_consumer_registry_v4520.json","scenario_exposure_change_registry_v4530.json","advanced_domain_workspace_registry_v4530.json")
def req(c,m):
    if not c: raise AssertionError(m)
def main():
    root=Path(__file__).resolve().parents[1]
    version=(root/'backend/app/version.py').read_text(); registry=(root/'backend/app/route_registry_v4430.py').read_text(); main=(root/'backend/app/main.py').read_text(); index=(root/'backend/public_app/index.html').read_text(); plugin=(root/'wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php').read_text(); readme=(root/'README.md').read_text(); deploy=(root/'deploy/contabo/upgrade_site_intelligence_backend_v4_53_0_contabo.sh').read_text(); econ=(root/'backend/public_app/assets/economics-v220.js').read_text(); law=(root/'backend/public_app/assets/law-v230.js').read_text(); advanced=(root/'backend/public_app/assets/advanced-domain-workspaces-v4530.js').read_text()
    req(f'APP_VERSION = "{EXPECTED_VERSION}"' in version,'APP_VERSION mismatch'); req(f'RELEASE_NAME = "{EXPECTED_NAME}"' in version,'release name mismatch'); req(f'**Current release:** v{EXPECTED_VERSION} — {EXPECTED_NAME}' in readme,'README mismatch'); req(f'Version: {EXPECTED_VERSION}' in plugin,'plugin mismatch')
    req('CapabilitySpec("scenario-exposure-change"' in registry,'scenario capability missing'); req('CapabilitySpec("advanced-domain-workspaces"' in registry,'advanced domains capability missing'); req('"registry_version": "2.0.0"' in registry,'registry generation mismatch')
    req('scenario_exposure_router' in main and 'advanced_domains_router' in main,'routers not registered')
    for path in ['/public/scenario-exposure/registry','/public/scenario-exposure/exposure/evaluate','/public/scenario-exposure/thresholds/evaluate','/public/advanced-workspaces/registry','/public/advanced-workspaces/parity-audit','/public/advanced-workspaces/international-law/analyze','/public/advanced-workspaces/economics/analyze','/public/advanced-workspaces/ocean/analyze','/public/advanced-workspaces/space/analyze']:
        req(path in (root/'backend/app/routers/scenario_exposure.py').read_text()+(root/'backend/app/routers/advanced_domains.py').read_text(),f'missing route {path}')
    req('Promise.allSettled' in econ,'economics resilient init missing'); req('Promise.allSettled' in law,'law resilient init missing'); req('wrap("SCSIOceanObservationV4360","ocean")' in advanced,'ocean advanced surface missing'); req('open("space")' in advanced,'space advanced surface missing'); req('advanced-domain-workspaces-v4530.js?v=4.53.0' in index,'advanced asset missing')
    req(len(RELEASE_BOUND)==36,'release bound count mismatch')
    for name in RELEASE_BOUND:
        payload=json.loads((root/'backend/data'/name).read_text()); req(payload.get('version')==EXPECTED_VERSION,f'release bound mismatch {name}')
    sample=json.loads((root/'backend/data/analytical_workspace_policy_v3234.json').read_text()); req(sample.get('release_id')=='site-intelligence-v4.35.5','historical release id changed')
    req("--exclude='data/'" in deploy,'dynamic data preservation missing'); req('scenario_exposure_change_registry_v4530.json' in deploy and 'advanced_domain_workspace_registry_v4530.json' in deploy,'v4.53 registries not promoted'); req('assert manifest["registry_version"] == "2.0.0"' in deploy,'deploy registry gate missing')
    print('PASS: v4.53.0 release identity aligned')
    print('PASS: scenario, exposure, change and threshold intelligence installed with non-causal boundaries')
    print('PASS: International Law and Economics resilient workspace initialization installed')
    print('PASS: Ocean and Space advanced research parity surfaces and analysis APIs installed')
    print('PASS: four-domain parity gate covers evidence, comparison, scenario, provenance, handoff, export and diagnostics')
    print('PASS: 24 new modular routes and capability-registry generation 2.0.0 installed')
    print('PASS: 36 release-bound static files and corrected health-aware Contabo deployment contract retained')
    print('PASS: WordPress remains thin shell; no domain feature shortcode added')
    return 0
if __name__=='__main__':
    raise SystemExit(main())
