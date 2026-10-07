from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.version import APP_VERSION, RELEASE_NAME
from app.route_registry_v4430 import capability_manifest, route_inventory
from app.spatial_research_handoffs_v4510 import compose_research_object
from app.reproducible_spatial_packages_v4540 import (
    registry_manifest, schema_manifest, profiles_manifest, compose_package, verify_package,
    inspect_package, build_manifest, reproduction_plan, export_plan, compare_packages,
    research_context, compatibility_manifest,
)

client=TestClient(app)

def fixture_research():
    return compose_research_object({
        "title":"Flood infrastructure investigation",
        "research_question":"Which assets intersect modeled flood exposure?",
        "scope":{"bbox":[-90.5,38.4,-89.8,38.9],"countries":["USA"]},
        "evidence_objects":[{"object_id":"asset-a","content_digest":"sha256:"+"a"*64}],
        "uncertainties":["Modeled exposure is not confirmed impact."],
    })["research_object"]

def fixture_request(profile="reference-first"):
    return {
        "title":"St. Louis flood spatial package",
        "profile":profile,
        "research_object":fixture_research(),
        "evidence_objects":[{"object_id":"asset-a","schema":"sc-site-intelligence-spatial-evidence/1.0","content_digest":"sha256:"+"a"*64}],
        "query_results":[{"result_id":"q1","result_digest":"sha256:"+"b"*64}],
        "graphs":[{"graph_id":"g1","graph_digest":"sha256:"+"c"*64}],
        "live_events":[{"event_id":"e1","event_digest":"sha256:"+"d"*64}],
        "federation_context":{"plan_id":"f1","plan_digest":"sha256:"+"e"*64},
        "predictions":[{"prediction_id":"p1","prediction_digest":"sha256:"+"f"*64}],
        "scenarios":[{"scenario_id":"s1","scenario_digest":"sha256:"+"1"*64}],
        "changes":[{"change_id":"c1","change_digest":"sha256:"+"2"*64}],
        "exposures":[{"exposure_id":"x1","exposure_digest":"sha256:"+"3"*64}],
        "thresholds":[{"threshold_id":"t1","threshold_digest":"sha256:"+"4"*64}],
        "advanced_domain_context":{"domain_id":"economics","analysis_digest":"sha256:"+"5"*64},
    }

def test_release_identity_and_inventory():
    assert APP_VERSION=="4.55.0"
    assert RELEASE_NAME=="Spatial Provenance & Transformation Lineage"
    m=capability_manifest(app.routes)
    assert m["registry_version"]=="2.2.0"
    assert m["route_count"]==1479
    assert m["modularized_route_count"]==170
    assert m["capability_count"]==27
    assert m["unclassified_route_count"]==0
    family=next(x for x in m["capabilities"] if x["capability_id"]=="reproducible-spatial-packages")
    assert family["route_count"]==12 and family["modularized_route_count"]==12
    keys=[(method,row["path"]) for row in route_inventory(app.routes) for method in row["methods"]]
    assert len(keys)==len(set(keys))

def test_registry_profiles_and_targets():
    r=registry_manifest(); assert r["profile_count"]==3 and r["export_target_count"]==8
    assert r["default_profile"]=="reference-first"

def test_schema_manifest_boundaries():
    s=schema_manifest(); assert s["schemas"]["package"].endswith("/1.0")
    assert "predictions" in s["component_groups"]

def test_profiles_surface():
    p=profiles_manifest(); assert len(p["profiles"])==3

def test_compose_is_deterministic():
    a=compose_package(fixture_request())["package"]; b=compose_package(fixture_request())["package"]
    assert a["package_digest"]==b["package_digest"] and a["manifest"]["manifest_digest"]==b["manifest"]["manifest_digest"]

def test_compose_preserves_all_context_groups():
    p=compose_package(fixture_request())["package"]
    assert p["manifest"]["entry_count"]==12
    assert {e["group"] for e in p["manifest"]["entries"]}.issuperset({"research_object","predictions","scenarios","exposures","advanced_domain_context"})

def test_portable_snapshot_profile():
    p=compose_package(fixture_request("portable-snapshot"))["package"]
    assert all(e["inclusion_mode"]=="embedded-snapshot" for e in p["manifest"]["entries"])

def test_sensitive_fields_rejected():
    req=fixture_request(); req["api_key"]="secret"
    try: compose_package(req)
    except ValueError as exc: assert "Sensitive field" in str(exc)
    else: raise AssertionError("expected sensitive field rejection")

def test_package_verification_valid():
    p=compose_package(fixture_request())["package"]
    v=verify_package({"package":p})["verification"]
    assert v["valid"] is True and v["automatic_execution"] is False

def test_tamper_detection():
    p=compose_package(fixture_request())["package"]
    p["title"]="tampered"
    v=verify_package({"package":p})["verification"]
    assert v["valid"] is False and "package digest mismatch" in v["errors"]

def test_inspection_reports_groups():
    p=compose_package(fixture_request())["package"]
    i=inspect_package({"package":p})["inspection"]
    assert i["valid"] is True and i["groups"]["evidence_objects"]==1

def test_manifest_endpoint_function():
    p=compose_package(fixture_request())["package"]
    m=build_manifest({"package":p})["manifest"]
    assert m["entry_count"]==12 and m["manifest_digest"].startswith("sha256:")

def test_reproduction_plan_requires_human_authorization():
    p=compose_package(fixture_request())["package"]
    plan=reproduction_plan({"package":p})["reproduction_plan"]
    assert plan["automatic_execution"] is False and plan["human_authorization_required"] is True
    assert len(plan["required_source_digests"])==12

def test_export_plan_preview_only():
    p=compose_package(fixture_request())["package"]
    plan=export_plan({"package":p,"target":"workspace"})["export_plan"]
    assert plan["preview_only"] is True and plan["delivery_attempted"] is False and plan["remote_write_attempted"] is False

def test_all_export_targets_supported():
    p=compose_package(fixture_request())["package"]
    for target in ("workspace","knowledge-library","research-librarian","research-lab","workbench","decision-studio","platform-core","filesystem"):
        assert export_plan({"package":p,"target":target})["export_plan"]["target"]==target

def test_package_comparison_never_ranks():
    a=compose_package(fixture_request())["package"]
    req=fixture_request(); req["title"]="Alternative package"; b=compose_package(req)["package"]
    c=compare_packages({"packages":[a,b]})["comparison"]
    assert c["package_count"]==2 and c["preferred_package"] is None and c["automatic_package_ranking"] is False

def test_research_context_preserves_identity():
    p=compose_package(fixture_request())["package"]
    c=research_context({"package":p})["research_context"]
    assert c["research_object_id"]==p["research_object"]["research_object_id"] and c["research_object_mutated"] is False

def test_compatibility_preserves_v453():
    c=compatibility_manifest(); assert "v4.53-scenario-exposure-change" in c["preserves"] and c["site_intelligence_automatic_execution"] is False

def test_http_surface_all_12_routes():
    gets=["/public/reproducible-spatial-packages/registry","/public/reproducible-spatial-packages/schema","/public/reproducible-spatial-packages/profiles","/public/reproducible-spatial-packages/compatibility"]
    for path in gets: assert client.get(path).status_code==200,path
    p=compose_package(fixture_request())["package"]
    posts={
      "/public/reproducible-spatial-packages/compose":fixture_request(),
      "/public/reproducible-spatial-packages/verify":{"package":p},
      "/public/reproducible-spatial-packages/inspect":{"package":p},
      "/public/reproducible-spatial-packages/manifest":{"package":p},
      "/public/reproducible-spatial-packages/reproduction-plan":{"package":p},
      "/public/reproducible-spatial-packages/export-plan":{"package":p,"target":"workspace"},
      "/public/reproducible-spatial-packages/compare":{"packages":[p,p]},
      "/public/reproducible-spatial-packages/research-context":{"package":p},
    }
    for path,payload in posts.items(): assert client.post(path,json=payload).status_code==200,path

def test_standalone_bootstrap_and_wordpress_thin_shell():
    root=Path(__file__).resolve().parents[2]
    standalone=(root/"backend/app/standalone_authority_v4440.py").read_text()
    php=(root/"wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text()
    assert "reproducible_spatial_package_registry" in standalone and 'NavigationItem("packages"' in standalone
    assert "Version: 4.55.0" in php and "const VERSION = '4.55.0';" in php
    assert "const WORDPRESS_ROLE = 'thin-shell-and-embed-bridge';" in php
