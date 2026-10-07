from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.version import APP_VERSION, RELEASE_NAME
from app.route_registry_v4430 import capability_manifest, route_inventory
from app.scenario_exposure_change_v4530 import normalize_scenario, compare_scenarios, derive_change, evaluate_exposure, evaluate_thresholds, graph_context, live_context, registry_manifest as scenario_registry
from app.advanced_domain_workspaces_v4530 import domain_profile, law_analysis, economics_analysis, ocean_analysis, space_analysis, parity_audit, registry_manifest as domain_registry

client=TestClient(app)

def test_release_identity_and_capability_inventory():
    assert APP_VERSION=="4.55.0"
    assert RELEASE_NAME=="Spatial Provenance & Transformation Lineage"
    m=capability_manifest(app.routes)
    assert m["registry_version"]=="2.2.0"
    assert m["unclassified_route_count"]==0
    scenario=next(x for x in m["capabilities"] if x["capability_id"]=="scenario-exposure-change")
    domains=next(x for x in m["capabilities"] if x["capability_id"]=="advanced-domain-workspaces")
    assert scenario["route_count"]==12 and scenario["modularized_route_count"]==12
    assert domains["route_count"]==12 and domains["modularized_route_count"]==12
    keys=[(method,row["path"]) for row in route_inventory(app.routes) for method in row["methods"]]
    assert len(keys)==len(set(keys))

def test_registries_current_and_parity_complete():
    assert scenario_registry()["version"]==APP_VERSION
    r=domain_registry(); assert len(r["domains"])==4
    audit=parity_audit(); assert audit["ok"] is True
    assert {x["domain_id"] for x in audit["domains"]}=={"international-law","economics","ocean","space"}

def test_scenario_normalization_deterministic():
    req={"scenario_id":"flood-high","label":"High flood","bbox":[-91,38,-89,39],"assumptions":["high precipitation"],"prediction_digests":["sha256:"+"a"*64]}
    a=normalize_scenario(req)["scenario"]; b=normalize_scenario(req)["scenario"]
    assert a["scenario_digest"]==b["scenario_digest"]
    assert a["observed_fact"] is False and a["model_conditional"] is True

def test_scenario_comparison_no_ranking():
    a=normalize_scenario({"scenario_id":"base","bbox":[0,0,1,1]})["scenario"]
    b=normalize_scenario({"scenario_id":"alt","bbox":[0,0,1,1]})["scenario"]
    out=compare_scenarios({"scenarios":[a,b]})["comparison"]
    assert out["scenario_count"]==2 and out["preferred_scenario"] is None and out["automatic_scenario_ranking"] is False

def test_change_derivation_preserves_noncausal_boundary():
    out=derive_change({"baseline":{"temperature":10,"status":"a"},"alternative":{"temperature":12,"status":"b"}})["change"]
    row=next(x for x in out["changes"] if x["metric"]=="temperature")
    assert row["delta"]==2 and row["percent_change"]==20
    assert out["causal_attribution"] is False and out["observed_change_confirmed"] is False

def test_exposure_is_potential_not_impact():
    out=evaluate_exposure({"scenario":{"scenario_id":"s","bbox":[0,0,2,2]},"assets":[{"object_id":"a","layer_id":"energy-power-systems","bbox":[1,1,1.5,1.5],"content_digest":"sha256:"+"b"*64},{"object_id":"b","bbox":[4,4,5,5]}]})["exposure"]
    assert out["potential_exposure_count"]==1
    assert out["exposures"][0]["impact_confirmed"] is False
    assert out["causality_inferred"] is False

def test_thresholds_are_rules_not_impacts():
    out=evaluate_thresholds({"metrics":{"level":8},"rules":[{"rule_id":"high","metric":"level","operator":"gte","threshold":7}]})["thresholds"]
    assert out["crossed_count"]==1
    assert out["results"][0]["interpretation"]=="rule-evaluation-only-not-impact-confirmation"

def test_graph_context_does_not_infer_propagation():
    out=graph_context({"exposed_node_ids":["a"],"graph":{"edges":[{"source_node_id":"a","target_node_id":"b","relationship_type":"supplies"}]}})["graph_context"]
    assert out["adjacent_edge_count"]==1 and out["automatic_failure_propagation"] is False

def test_live_context_only_intersection():
    out=live_context({"bbox":[0,0,2,2],"events":[{"event_id":"e","event_type":"storm","bbox":[1,1,1.1,1.1]}]})["live_context"]
    assert out["intersecting_event_count"]==1 and out["events"][0]["impact_confirmed"] is False

def test_domain_profiles_have_advanced_parity():
    for domain in ("international-law","economics","ocean","space"):
        p=domain_profile(domain)["domain"]
        assert set(["evidence","comparison","scenario","provenance","research-handoff","export","diagnostics"]).issubset(p["advanced_capabilities"])
        assert len(p["research_tools"])>=6

def test_law_analysis_is_descriptive_not_legal_conclusion():
    out=law_analysis({"records":[{"authority_level":"binding_treaty_obligation","legal_body":"UN","countries":["USA"],"subjects":["climate"]}]})["analysis"]
    assert out["record_count"]==1 and out["binding_candidate_count"]==1
    assert out["legal_conclusion"] is False and out["automatic_authority_ranking"] is False

def test_economics_analysis_preserves_comparability():
    out=economics_analysis({"records":[{"indicator_code":"GDP","unit":"USD","frequency":"annual","value_number":10,"geography_code":"USA","source_id":"a"},{"indicator_code":"GDP","unit":"USD","frequency":"annual","value_number":12,"geography_code":"CAN","source_id":"a"}]})["analysis"]
    assert out["comparability_groups"][0]["mean"]==11
    assert out["silent_unit_normalization"] is False and out["investment_advice"] is False

def test_ocean_analysis_depth_and_variable_context():
    out=ocean_analysis({"observations":[{"variable":"temperature","unit":"C","value":10,"depth_m":5,"source_id":"x"},{"variable":"temperature","unit":"C","value":4,"depth_m":500,"source_id":"x"}]})["analysis"]
    assert out["depth_distribution"]["surface"]==1 and out["depth_distribution"]["mesopelagic"]==1
    assert out["automatic_interpolation"] is False and "governance" in out["cross_system_tools"]

def test_space_analysis_cross_system_and_no_inference():
    out=space_analysis({"records":[{"record_type":"mission","mission_id":"voyager","target_id":"jupiter","source_id":"nasa"}]})["analysis"]
    assert out["mission_count"]==1 and out["target_count"]==1
    assert out["automatic_orbit_inference"] is False and out["automatic_habitability_claim"] is False

def test_http_surface_all_new_routes():
    gets=["/public/scenario-exposure/registry","/public/scenario-exposure/schema","/public/scenario-exposure/compatibility","/public/advanced-workspaces/registry","/public/advanced-workspaces/international-law","/public/advanced-workspaces/economics","/public/advanced-workspaces/ocean","/public/advanced-workspaces/space","/public/advanced-workspaces/parity-audit","/public/advanced-workspaces/compatibility"]
    for path in gets: assert client.get(path).status_code==200, path

def test_frontend_advanced_parity_assets_and_resilient_initializers():
    root=Path(__file__).resolve().parents[2]
    index=(root/"backend/public_app/index.html").read_text()
    js=(root/"backend/public_app/assets/advanced-domain-workspaces-v4530.js").read_text()
    econ=(root/"backend/public_app/assets/economics-v220.js").read_text()
    law=(root/"backend/public_app/assets/law-v230.js").read_text()
    assert "advanced-domain-workspaces-v4530.js?v=4.55.0" in index
    assert 'wrap("SCEconomicsV220","economics")' in js and 'wrap("SCLawV230","international-law")' in js
    assert 'wrap("SCSIOceanObservationV4360","ocean")' in js and 'open("space")' in js
    assert "Promise.allSettled" in econ and "Promise.allSettled" in law
