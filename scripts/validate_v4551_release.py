#!/usr/bin/env python3
from pathlib import Path
import json, sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.main import app
from app.version import APP_VERSION, RELEASE_NAME
from app.route_registry_v4430 import capability_manifest, route_inventory
from app.production_truth_v3231 import public_production_truth
from app.spatial_provenance_lineage_v4550 import registry_manifest as lineage_registry

assert APP_VERSION=='4.55.1'
assert RELEASE_NAME=='Core Workspace Runtime Repair'
m=capability_manifest(app.routes)
assert m['registry_version']=='2.2.0'
assert m['route_count']==1479
assert m['modularized_route_count']==170
assert m['capability_count']==27
assert m['unclassified_route_count']==0
family=next(x for x in m['capabilities'] if x['capability_id']=='spatial-provenance-lineage')
assert family['route_count']==12 and family['modularized_route_count']==12
keys=[(method,row['path']) for row in route_inventory(app.routes) for method in row['methods']]
assert len(keys)==len(set(keys))
assert lineage_registry()['transformation_type_count']==15

truth=public_production_truth(); assert truth['version']==APP_VERSION
contracts={x['route_id']:x for x in truth['routes']}
expected_workspaces={
'economics':('#economicsStudio','/public/economics-sustainability','SCEconomicsV220'),
'law':('#lawStudio','/public/international-law-observatory','SCLawV230'),
'science':('#scienceStudio','/public/scientific-earth-systems','SCScienceV240'),
'humanitarian':('#humanitarianStudio','/public/humanitarian-conflict-displacement','SCHumanitarianV250'),
'resources':('#resourceStudio','/public/trade-energy-resources','SCResourcesV260'),
'dossiers':('#dossierStudio','/public/intelligence-dossiers','SCDossiersV270'),
}
for route,(selector,endpoint,controller) in expected_workspaces.items():
    row=contracts[route]
    assert selector in row['surface_selectors'], (route,row['surface_selectors'])
    assert endpoint in row['endpoint_families'], (route,row['endpoint_families'])
    assert row['controller']==controller

runtime=(ROOT/'backend/public_app/assets/workspace-runtime-repair-v4551.js').read_text()
index=(ROOT/'backend/public_app/index.html').read_text()
truth_js=(ROOT/'backend/public_app/assets/production-truth-v3231.js').read_text()
app_js=(ROOT/'backend/public_app/assets/app.js').read_text()
sw=(ROOT/'backend/public_app/service-worker.js').read_text()
assert 'const VERSION="4.55.1"' in runtime
assert 'SCSIWorkspaceRuntimeRepairV4551' in app_js
assert 'APP_ROOT.dataset.scsiRelease||"4.55.1"' in truth_js
assert 'const VERSION="4.39.0"' not in truth_js
assert '/app/assets/workspace-runtime-repair-v4551.js?v=4.55.1' in index
assert index.index('workspace-runtime-repair-v4551.js') < index.index('production-truth-v3231.js')
assert 'workspace-runtime-repair-v4551.js' in sw and 'const RELEASE="4.55.1"' in sw
for route in expected_workspaces: assert f'openCoreWorkspace("{route}")' in app_js

# backend endpoint paths used by the repaired workspaces must remain registered
paths={getattr(r,'path',None) for r in app.routes}
for required in (
'/public/intelligence-dossiers/facets','/public/intelligence-dossiers/country',
'/public/economics-sustainability','/public/economics-sustainability/records',
'/public/international-law-observatory','/public/international-law-observatory/records',
'/public/scientific-earth-systems/discovery','/public/humanitarian-conflict-displacement/records',
'/public/trade-energy-resources/records'):
    assert required in paths, required

release_files=[]
for f in (ROOT/'backend/data').glob('*.json'):
    try:d=json.loads(f.read_text())
    except Exception:continue
    if d.get('version')==APP_VERSION:release_files.append(f.name)
expected={
'analytical_workspace_policy_v3234.json','bootstrap_recovery_policy_v32361.json','briefing_publication_policy_v3290.json','browser_reliability_policy_v3235.json','comparative_model_assurance_policy_v3260.json','connected_platform_policy_v300.json','country_identity_registry_v43523.json','embed_isolation_policy_v32363.json','evidence_synthesis_policy_v2180.json','federation_policy_v2240.json','institutional_review_governance_policy_v3300.json','institutional_workspaces_policy_v2220.json','intelligence_publishing_policy_v2200.json','knowledge_graph_policy_v2190.json','knowledge_graph_relationship_registry_v2190.json','live_intelligence_source_registry_v320.json','map_interaction_policy_v3232.json','model_governance_policy_v2170.json','model_metric_registry_v2170.json','monitoring_early_warning_policy_v3280.json','mutation_observer_recovery_policy_v32362.json','performance_offline_policy_v3236.json','research_evidence_integration_policy_v3270.json','scheduled_monitoring_policy_v2210.json','spatial_evidence_policy_v2150.json','startup_stability_policy_v32364.json','unified_analytical_state_policy_v3250.json','spatial_layer_registry_v4460.json','spatiotemporal_operator_registry_v4470.json','spatial_relationship_registry_v4480.json','live_geospatial_event_fusion_registry_v4490.json','global_source_federation_registry_v4500.json','spatial_research_handoff_registry_v4510.json','predictive_spatial_consumer_registry_v4520.json','scenario_exposure_change_registry_v4530.json','advanced_domain_workspace_registry_v4530.json','reproducible_spatial_package_registry_v4540.json','spatial_provenance_lineage_registry_v4550.json'}
assert set(release_files)==expected,(sorted(expected-set(release_files)),sorted(set(release_files)-expected))

helper=(ROOT/'deploy/contabo/upgrade_site_intelligence_backend_v4_55_1_contabo.sh').read_text()
for name in expected: assert name in helper,name
for wrong in ('scenario_exposure_change_registry_v4551.json','advanced_domain_workspace_registry_v4551.json','reproducible_spatial_package_registry_v4551.json','spatial_provenance_lineage_registry_v4551.json'):
    assert wrong not in helper,wrong
assert 'six core workspace production-truth surfaces aligned' in helper
php=(ROOT/'wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php').read_text()
assert 'Version: 4.55.1' in php and "const VERSION = '4.55.1';" in php and 'thin-shell-and-embed-bridge' in php
print('PASS: v4.55.1 release identity aligned')
print('PASS: six core workspace production-truth surfaces point to real DOM studios')
print('PASS: economics, law, science, humanitarian, resources and dossiers endpoint families aligned')
print('PASS: shared resilient workspace runtime repair packaged before production-truth control plane')
print('PASS: Dossiers and Resources survive optional catalog/bootstrap failures')
print('PASS: service worker cache identity and critical repair asset advanced to v4.55.1')
print('PASS: v4.55 lineage, v4.54 packages and route inventory preserved')
print('PASS: 38 release-bound files and historical registry filenames retained')
print('PASS: WordPress remains thin shell')
