#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
VERSION = "4.55.2"
RELEASE = "Advanced Domain Intelligence Workspace Expansion"
POLICIES = [
  "analytical_workspace_policy_v3234.json","bootstrap_recovery_policy_v32361.json","briefing_publication_policy_v3290.json","browser_reliability_policy_v3235.json","comparative_model_assurance_policy_v3260.json","connected_platform_policy_v300.json","country_identity_registry_v43523.json","embed_isolation_policy_v32363.json","evidence_synthesis_policy_v2180.json","federation_policy_v2240.json","institutional_review_governance_policy_v3300.json","institutional_workspaces_policy_v2220.json","intelligence_publishing_policy_v2200.json","knowledge_graph_policy_v2190.json","knowledge_graph_relationship_registry_v2190.json","live_intelligence_source_registry_v320.json","map_interaction_policy_v3232.json","model_governance_policy_v2170.json","model_metric_registry_v2170.json","monitoring_early_warning_policy_v3280.json","mutation_observer_recovery_policy_v32362.json","performance_offline_policy_v3236.json","research_evidence_integration_policy_v3270.json","scheduled_monitoring_policy_v2210.json","spatial_evidence_policy_v2150.json","startup_stability_policy_v32364.json","unified_analytical_state_policy_v3250.json","spatial_layer_registry_v4460.json","spatiotemporal_operator_registry_v4470.json","spatial_relationship_registry_v4480.json","live_geospatial_event_fusion_registry_v4490.json","global_source_federation_registry_v4500.json","spatial_research_handoff_registry_v4510.json","predictive_spatial_consumer_registry_v4520.json","scenario_exposure_change_registry_v4530.json","advanced_domain_workspace_registry_v4530.json","reproducible_spatial_package_registry_v4540.json","spatial_provenance_lineage_registry_v4550.json","advanced_domain_intelligence_registry_v4552.json",
]

def check(cond: bool, msg: str):
    if not cond: raise SystemExit(f"FAIL: {msg}")
    print(f"PASS: {msg}")

version = (ROOT/"backend/app/version.py").read_text()
check(f'APP_VERSION = "{VERSION}"' in version and RELEASE in version, "v4.55.2 release identity aligned")

registry = json.loads((ROOT/"backend/data/advanced_domain_intelligence_registry_v4552.json").read_text())
check(registry["version"] == VERSION and len(registry["domains"]) == 6, "six-domain advanced intelligence registry installed")
check(all(len(d.get("analysis_modes",[])) >= 5 for d in registry["domains"]), "domain-specific advanced analysis modes installed")
check(all(len(d.get("research_workflow",[])) >= 6 for d in registry["domains"]), "domain research workflows installed")

router=(ROOT/"backend/app/routers/domain_intelligence.py").read_text()
for domain in ("dossiers","economics","international-law","science","humanitarian","resources"):
    for suffix in ("profile","analyze","packet"):
        check(f'/public/domain-intelligence/{domain}/{suffix}' in router, f"{domain} {suffix} route installed")

cap=(ROOT/"backend/app/route_registry_v4430.py").read_text()
check('"registry_version": "2.3.0"' in cap and 'advanced-domain-intelligence' in cap, "capability registry 2.3.0 owns advanced domain intelligence")

index=(ROOT/"backend/public_app/index.html").read_text()
js=(ROOT/"backend/public_app/assets/advanced-domain-intelligence-v4552.js").read_text()
css=(ROOT/"backend/public_app/assets/advanced-domain-intelligence-v4552.css").read_text()
check('advanced-domain-intelligence-v4552.js?v=4.55.2' in index and 'advanced-domain-intelligence-v4552.css?v=4.55.2' in index, "advanced research browser assets loaded")
check('Analyze current records' in js and 'Build research packet' in js and '.advanced-domain-intelligence-v4552' in css, "advanced research browser workflow installed")
check('data-scsi-release="4.55.2"' in index, "standalone shell release identity current")

for name in POLICIES:
    path=ROOT/"backend/data"/name
    check(path.exists(), f"release-bound file exists: {name}")
    check(json.loads(path.read_text()).get("version") == VERSION, f"release-bound file aligned: {name}")
check(len(POLICIES)==39, "39 release-bound files declared")

deploy=(ROOT/"deploy/contabo/upgrade_site_intelligence_backend_v4_55_2_contabo.sh").read_text()
for name in POLICIES:
    check(name in deploy, f"deployment promotes {name}")
check('assert manifest["route_count"] == 1500' in deploy and 'assert manifest["modularized_route_count"] == 191' in deploy and 'assert manifest["capability_count"] == 28' in deploy, "deployment inventory assertions current")
check('advanced_domain_intelligence_registry_v4552.json' in deploy, "deployment promotes new v4.55.2 registry")

plugin=(ROOT/"wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text()
check('Version: 4.55.2' in plugin and "const VERSION = '4.55.2';" in plugin and "const WORDPRESS_ROLE = 'thin-shell-and-embed-bridge';" in plugin, "WordPress thin-shell identity aligned")
check('advanced_domain_intelligence' not in plugin.lower(), "no domain feature shortcode added to WordPress")

sw=(ROOT/"backend/public_app/service-worker.js").read_text()
check('const RELEASE="4.55.2";' in sw and 'advanced-domain-intelligence-v4552.js' in sw, "service-worker cache generation includes v4.55.2 advanced workspace assets")
print("V4552_RELEASE_VALIDATION=PASS")
