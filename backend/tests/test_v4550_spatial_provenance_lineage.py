from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.version import APP_VERSION, RELEASE_NAME
from app.route_registry_v4430 import capability_manifest, route_inventory
from app.reproducible_spatial_packages_v4540 import compose_package
from app.spatial_provenance_lineage_v4550 import (
    registry_manifest, schema_manifest, transformation_types_manifest, record_transformation,
    validate_transformation, build_lineage_chain, lineage_graph, trace_lineage,
    verify_lineage_chain, package_context, compare_lineages, compatibility_manifest,
)
client=TestClient(app)

def artifact(name, ch):
    return {"artifact_id":name,"digest":"sha256:"+ch*64,"schema":"sc-test-artifact/1.0"}

def event_one():
    return record_transformation({
        "transformation_type":"reprojection",
        "inputs":[artifact("raw","a")],
        "outputs":[artifact("reprojected","b")],
        "operator":{"operator_id":"proj","operator_version":"9.5"},
        "parameters":{"source_crs":"EPSG:4326","target_crs":"EPSG:3857"},
        "uncertainties":["Projection choice may affect geometry."],
    })["transformation"]

def event_two():
    return record_transformation({
        "transformation_type":"spatial-join",
        "inputs":[artifact("reprojected","b"),artifact("assets","c")],
        "outputs":[artifact("joined","d")],
        "operator":{"operator_id":"spatial-join"},
        "parameters":{"predicate":"intersects"},
    })["transformation"]

def chain_fixture():
    return build_lineage_chain({"transformations":[event_one(),event_two()]})["chain"]

def package_fixture():
    return compose_package({
        "title":"Lineage package",
        "profile":"reference-first",
        "evidence_objects":[{"object_id":"joined","content_digest":"sha256:"+"d"*64}],
        "lineage_chains":[chain_fixture()],
    })["package"]

def test_release_identity_and_inventory():
    assert APP_VERSION=="4.56.0"
    assert RELEASE_NAME=="Standalone Production Consolidation & Certification"
    m=capability_manifest(app.routes)
    assert m["registry_version"]=="2.7.0"
    assert m["route_count"]==1521
    assert m["modularized_route_count"]==212
    assert m["capability_count"]==32
    assert m["unclassified_route_count"]==0
    family=next(x for x in m["capabilities"] if x["capability_id"]=="spatial-provenance-lineage")
    assert family["route_count"]==12 and family["modularized_route_count"]==12
    keys=[(method,row["path"]) for row in route_inventory(app.routes) for method in row["methods"]]
    assert len(keys)==len(set(keys))

def test_registry_and_schema():
    r=registry_manifest(); assert r["transformation_type_count"]==15
    s=schema_manifest(); assert s["schemas"]["transformation"].endswith("/1.0")

def test_transformation_type_surface():
    t=transformation_types_manifest(); assert t["count"]==15 and any(x["type_id"]=="manual-annotation" for x in t["transformation_types"])

def test_record_is_deterministic():
    a=event_one(); b=event_one(); assert a["event_digest"]==b["event_digest"] and a["event_id"]==b["event_id"]

def test_validation_and_tamper_detection():
    e=event_one(); assert validate_transformation({"transformation":e})["validation"]["valid"] is True
    e["parameters"]["target_crs"]="EPSG:3395"
    assert validate_transformation({"transformation":e})["validation"]["valid"] is False

def test_sensitive_fields_rejected():
    try: record_transformation({"transformation_type":"normalization","inputs":[artifact("a","a")],"outputs":[artifact("b","b")],"api_key":"x"})
    except ValueError as exc: assert "Sensitive field" in str(exc)
    else: raise AssertionError("expected sensitive field rejection")

def test_chain_is_deterministic_and_explicit():
    a=chain_fixture(); b=chain_fixture(); assert a["chain_digest"]==b["chain_digest"]
    assert a["event_count"]==2 and len(a["edges"])==1 and a["lineage_inferred"] is False

def test_graph_has_artifact_and_event_nodes():
    g=lineage_graph({"chain":chain_fixture()})["graph"]
    kinds={x["node_type"] for x in g["nodes"]}; assert kinds=={"artifact","transformation"}

def test_trace_ancestors_and_descendants():
    c=chain_fixture()
    t=trace_lineage({"chain":c,"artifact_digest":"sha256:"+"b"*64,"direction":"both"})["trace"]
    assert t["node_count"]>=4 and t["lineage_inferred"] is False

def test_chain_verification_and_tamper_detection():
    c=chain_fixture(); assert verify_lineage_chain({"chain":c})["verification"]["valid"] is True
    c["events"][0]["parameters"]["target_crs"]="EPSG:3395"
    assert verify_lineage_chain({"chain":c})["verification"]["valid"] is False

def test_package_context_does_not_mutate():
    p=package_fixture(); c=chain_fixture(); ctx=package_context({"package":p,"chain":c})["package_context"]
    assert ctx["package_valid"] is True and ctx["lineage_valid"] is True
    assert ctx["shared_artifact_count"] >= 1
    assert ctx["package_mutated"] is False and ctx["chain_mutated"] is False

def test_compare_never_ranks_or_merges():
    c=chain_fixture(); d=build_lineage_chain({"transformations":[event_one()]})["chain"]
    comp=compare_lineages({"chains":[c,d]})["comparison"]
    assert comp["preferred_chain"] is None and comp["automatic_lineage_ranking"] is False and comp["automatic_merge"] is False

def test_compatibility_preserves_v454():
    c=compatibility_manifest(); assert "v4.54-reproducible-spatial-intelligence-packages" in c["preserves"]
    assert c["automatic_lineage_inference"] is False and c["automatic_chain_repair"] is False

def test_http_surface_all_12_routes():
    for path in ["/public/spatial-lineage/registry","/public/spatial-lineage/schema","/public/spatial-lineage/transformation-types","/public/spatial-lineage/compatibility"]:
        assert client.get(path).status_code==200,path
    e1=event_one(); e2=event_two(); c=chain_fixture(); p=package_fixture()
    posts={
        "/public/spatial-lineage/record":{"transformation_type":"normalization","inputs":[artifact("a","a")],"outputs":[artifact("b","b")]},
        "/public/spatial-lineage/validate":{"transformation":e1},
        "/public/spatial-lineage/chain":{"transformations":[e1,e2]},
        "/public/spatial-lineage/graph":{"chain":c},
        "/public/spatial-lineage/trace":{"chain":c,"artifact_digest":"sha256:"+"b"*64,"direction":"both"},
        "/public/spatial-lineage/verify":{"chain":c},
        "/public/spatial-lineage/package-context":{"package":p,"chain":c},
        "/public/spatial-lineage/compare":{"chains":[c,c]},
    }
    for path,payload in posts.items(): assert client.post(path,json=payload).status_code==200,path

def test_standalone_and_wordpress_identity():
    root=Path(__file__).resolve().parents[2]
    standalone=(root/"backend/app/standalone_authority_v4440.py").read_text()
    php=(root/"wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text()
    assert "spatial_lineage_registry" in standalone and 'NavigationItem("lineage"' in standalone
    assert "Version: 4.56.0" in php and "const VERSION = '4.56.1';" in php
    assert "const WORDPRESS_ROLE = 'public-site-launch-bridge';" in php
