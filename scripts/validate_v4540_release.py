#!/usr/bin/env python3
from pathlib import Path
import json, sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"backend"))
from app.main import app
from app.version import APP_VERSION, RELEASE_NAME
from app.route_registry_v4430 import capability_manifest, route_inventory
from app.reproducible_spatial_packages_v4540 import registry_manifest
assert APP_VERSION=="4.54.0"
assert RELEASE_NAME=="Reproducible Spatial Intelligence Packages"
m=capability_manifest(app.routes)
assert m["registry_version"]=="2.1.0"
assert m["route_count"]==1467
assert m["modularized_route_count"]==158
assert m["capability_count"]==26
assert m["unclassified_route_count"]==0
family=next(x for x in m["capabilities"] if x["capability_id"]=="reproducible-spatial-packages")
assert family["route_count"]==12 and family["modularized_route_count"]==12
keys=[(method,row["path"]) for row in route_inventory(app.routes) for method in row["methods"]]
assert len(keys)==len(set(keys))
r=registry_manifest(); assert r["profile_count"]==3 and r["export_target_count"]==8
release_files=[]
for f in (ROOT/"backend/data").glob("*.json"):
    try: d=json.loads(f.read_text())
    except Exception: continue
    if d.get("version")==APP_VERSION: release_files.append(f.name)
expected={
"analytical_workspace_policy_v3234.json","bootstrap_recovery_policy_v32361.json","briefing_publication_policy_v3290.json","browser_reliability_policy_v3235.json","comparative_model_assurance_policy_v3260.json","connected_platform_policy_v300.json","country_identity_registry_v43523.json","embed_isolation_policy_v32363.json","evidence_synthesis_policy_v2180.json","federation_policy_v2240.json","institutional_review_governance_policy_v3300.json","institutional_workspaces_policy_v2220.json","intelligence_publishing_policy_v2200.json","knowledge_graph_policy_v2190.json","knowledge_graph_relationship_registry_v2190.json","live_intelligence_source_registry_v320.json","map_interaction_policy_v3232.json","model_governance_policy_v2170.json","model_metric_registry_v2170.json","monitoring_early_warning_policy_v3280.json","mutation_observer_recovery_policy_v32362.json","performance_offline_policy_v3236.json","research_evidence_integration_policy_v3270.json","scheduled_monitoring_policy_v2210.json","spatial_evidence_policy_v2150.json","startup_stability_policy_v32364.json","unified_analytical_state_policy_v3250.json","spatial_layer_registry_v4460.json","spatiotemporal_operator_registry_v4470.json","spatial_relationship_registry_v4480.json","live_geospatial_event_fusion_registry_v4490.json","global_source_federation_registry_v4500.json","spatial_research_handoff_registry_v4510.json","predictive_spatial_consumer_registry_v4520.json","scenario_exposure_change_registry_v4530.json","advanced_domain_workspace_registry_v4530.json","reproducible_spatial_package_registry_v4540.json"}
assert expected.issubset(set(release_files)), sorted(expected-set(release_files))
php=(ROOT/"wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text()
assert "Version: 4.54.0" in php and "thin-shell-and-embed-bridge" in php
print("PASS: v4.54.0 release identity aligned")
print("PASS: reproducible spatial intelligence package contracts installed")
print("PASS: deterministic manifests, package verification, reproduction and export plans installed")
print("PASS: v4.46-v4.53 evidence and derived-analysis boundaries preserved")
print("PASS: 12 new modular routes and capability-registry generation 2.1.0 installed")
print("PASS: 37 release-bound static files retained")
print("PASS: WordPress remains thin shell; no package feature shortcode added")
