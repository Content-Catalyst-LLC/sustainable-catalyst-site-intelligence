from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.route_registry_v4430 import capability_manifest, route_inventory
from app.spatial_research_handoffs_v4510 import (
    HANDOFF_SCHEMA,
    MANIFEST_SCHEMA,
    PACKAGE_SCHEMA,
    RESEARCH_OBJECT_SCHEMA,
    build_package,
    compose_research_object,
    create_handoff,
    registry_manifest,
    research_manifest,
    validate_handoff,
    validate_research_object,
)
from app.version import APP_VERSION, RELEASE_NAME

ROOT = Path(__file__).resolve().parents[2]
client = TestClient(app)


def _research_request() -> dict:
    return {
        "title": "St. Louis infrastructure exposure study",
        "research_question": "Which critical infrastructure assets intersect the event footprint and what evidence supports the assessment?",
        "scope": {
            "crs": "EPSG:4326",
            "bbox": [-90.5, 38.4, -89.8, 38.9],
            "countries": ["USA"],
            "date_start": "2026-10-05T00:00:00Z",
            "date_end": "2026-10-06T00:00:00Z",
        },
        "evidence_objects": [
            {
                "schema": "sc-site-intelligence-spatial-evidence-object/2.0",
                "object_id": "power-a",
                "layer_id": "energy-power-systems",
                "geometry": {"type": "Point", "coordinates": [-90.2, 38.63]},
                "content_digest": "sha256:" + "a" * 64,
                "source": {"source_id": "example-energy-source"},
            }
        ],
        "query_results": [
            {
                "schema": "sc-site-intelligence-spatiotemporal-query-result/1.0",
                "result_id": "query-result-a",
                "result_digest": "sha256:" + "b" * 64,
            }
        ],
        "graphs": [
            {
                "schema": "sc-site-intelligence-spatial-relationship-graph/1.0",
                "graph_id": "graph-a",
                "graph_digest": "sha256:" + "c" * 64,
            }
        ],
        "live_events": [
            {
                "schema": "sc-site-intelligence-live-geospatial-event/1.0",
                "event_id": "event-a",
                "event_digest": "sha256:" + "d" * 64,
                "source": {"source_id": "usgs_earthquakes"},
            }
        ],
        "federation_context": {
            "schema": "sc-site-intelligence-source-selection/1.0",
            "source_id": "usgs_earthquakes",
            "digest": "sha256:" + "e" * 64,
        },
        "findings": [{"finding_id": "f1", "text": "Power asset is spatially intersecting the event footprint."}],
        "assumptions": ["Bounding-box semantics are used for spatial intersection."],
        "uncertainties": ["Spatial overlap does not establish damage or causality."],
        "evidence_gaps": ["No confirmed outage observation is present."],
    }


def test_release_identity() -> None:
    assert APP_VERSION == "4.55.3"
    assert RELEASE_NAME == "Standalone Web Application Foundation & WordPress Decoupling"


def test_registry_declares_seven_provider_neutral_targets() -> None:
    payload = registry_manifest()
    assert payload["target_count"] == 7
    ids = {row["target_id"] for row in payload["targets"]}
    assert ids == {"workspace", "knowledge-library", "research-librarian", "research-lab", "workbench", "decision-studio", "platform-core"}
    assert "no-target-delivery-is-attempted-by-site-intelligence" in payload["boundaries"]


def test_research_object_preserves_component_digests_and_is_deterministic() -> None:
    first = compose_research_object(_research_request())["research_object"]
    second = compose_research_object(_research_request())["research_object"]
    assert first["schema"] == RESEARCH_OBJECT_SCHEMA
    assert first["research_digest"] == second["research_digest"]
    assert first["research_object_id"] == second["research_object_id"]
    assert "sha256:" + "a" * 64 in first["source_component_digests"]
    assert "sha256:" + "d" * 64 in first["source_component_digests"]
    assert len(first["lineage"]) == 5
    assert first["persistence"]["server_persistence"] is False


def test_research_object_validation_recomputes_integrity() -> None:
    obj = compose_research_object(_research_request())["research_object"]
    good = validate_research_object(obj)
    assert good["valid"] is True
    obj["title"] = "Tampered"
    bad = validate_research_object(obj)
    assert bad["valid"] is False
    assert "research-digest-mismatch" in bad["errors"]


def test_manifest_summarizes_sources_components_and_lineage() -> None:
    obj = compose_research_object(_research_request())["research_object"]
    manifest = research_manifest({"research_object": obj})
    assert manifest["schema"] == MANIFEST_SCHEMA
    assert manifest["component_counts"] == {
        "evidence_objects": 1,
        "query_results": 1,
        "graphs": 1,
        "live_events": 1,
        "federation_context": 1,
    }
    assert {"example-energy-source", "usgs_earthquakes"} <= set(manifest["source_ids"])
    assert manifest["manifest_digest"].startswith("sha256:")


@pytest.mark.parametrize("target", ["workspace", "knowledge-library", "research-librarian", "research-lab", "workbench", "decision-studio", "platform-core"])
def test_each_cross_product_handoff_is_preview_only_and_valid(target: str) -> None:
    packet = create_handoff(target, _research_request())["packet"]
    assert packet["schema"] == HANDOFF_SCHEMA
    assert packet["target"] == target
    assert packet["preview_only"] is True
    assert packet["delivery_attempted"] is False
    assert packet["delivery_verified"] is False
    assert packet["handoff_digest"].startswith("sha256:")
    assert validate_handoff(target, packet)["valid"] is True


def test_target_specific_payloads_are_meaningful() -> None:
    workspace = create_handoff("workspace", _research_request())["packet"]["payload"]
    assert workspace["project_type"] == "spatial-research"
    assert workspace["resume_supported"] is True
    library = create_handoff("knowledge-library", _research_request())["packet"]["payload"]
    assert library["automatic_publication"] is False
    librarian = create_handoff("research-librarian", _research_request())["packet"]["payload"]
    assert librarian["guidance_only"] is True
    lab = create_handoff("research-lab", {**_research_request(), "hypotheses": ["Infrastructure exposure is clustered."]})["packet"]["payload"]
    assert lab["reproducible"] is True
    workbench = create_handoff("workbench", _research_request())["packet"]["payload"]
    assert workbench["derived_results_must_preserve_lineage"] is True
    decision = create_handoff("decision-studio", {**_research_request(), "scenarios": [{"id": "baseline"}]})["packet"]["payload"]
    assert decision["decision_not_automated"] is True
    core = create_handoff("platform-core", _research_request())["packet"]["payload"]
    assert "v4.50-source-federation" in core["contract_refs"]


def test_package_contains_all_targets_and_is_deterministic() -> None:
    a = build_package(_research_request())["package"]
    b = build_package(_research_request())["package"]
    assert a["schema"] == PACKAGE_SCHEMA
    assert a["target_count"] == 7
    assert a["package_digest"] == b["package_digest"]
    assert a["package_id"] == b["package_id"]
    assert a["server_persistence"] is False
    assert a["delivery_attempted"] is False


def test_sensitive_fields_are_rejected() -> None:
    with pytest.raises(ValueError):
        compose_research_object({"title": "Bad", "notes": [{"api_key": "secret"}]})


def test_http_routes_and_errors() -> None:
    assert client.get("/public/spatial-research/registry").status_code == 200
    assert client.get("/public/spatial-research/object-schema").json()["schema"] == RESEARCH_OBJECT_SCHEMA
    composed = client.post("/public/spatial-research/objects/compose", json=_research_request())
    assert composed.status_code == 200
    obj = composed.json()["research_object"]
    assert client.post("/public/spatial-research/objects/validate", json=obj).json()["valid"] is True
    assert client.post("/public/spatial-research/objects/manifest", json={"research_object": obj}).status_code == 200
    assert client.get("/public/spatial-research/handoffs").json()["targets"]
    handoff = client.post("/public/spatial-research/handoff/workspace", json={"research_object": obj})
    assert handoff.status_code == 200
    validation = client.post("/public/spatial-research/handoff/workspace/validate", json=handoff.json()["packet"])
    assert validation.json()["valid"] is True
    assert client.post("/public/spatial-research/handoff/not-a-target", json=_research_request()).status_code == 400
    assert client.post("/public/spatial-research/package", json=_research_request()).status_code == 200


def test_compatibility_preserves_v446_through_v450_and_legacy_handoffs() -> None:
    compat = client.get("/public/spatial-research/compatibility").json()
    assert compat["v4_46_spatial_evidence"]["status"] == "preserved-and-consumed"
    assert compat["v4_47_spatiotemporal"]["status"] == "preserved-and-consumed"
    assert compat["v4_48_spatial_graph"]["status"] == "preserved-and-consumed"
    assert compat["v4_49_live_geospatial"]["impact_semantics"] == "potential-exposure-not-confirmed-impact"
    assert compat["v4_50_source_federation"]["trust_separate_from_authority"] is True
    assert compat["legacy_research_handoffs"]["status"] == "preserved"
    assert compat["wordpress_role"] == "public-site-launch-bridge"


def test_capability_registry_owns_all_spatial_research_routes() -> None:
    manifest = capability_manifest(app.routes)
    family = next(row for row in manifest["capabilities"] if row["capability_id"] == "spatial-research-handoffs")
    assert manifest["registry_version"] == "2.4.0"
    assert manifest["route_count"] == 1506
    assert manifest["modularized_route_count"] == 197
    assert manifest["capability_count"] == 29
    assert manifest["unclassified_route_count"] == 0
    assert family["route_count"] == 10
    assert family["modularized_route_count"] == 10
    inventory = route_inventory(app.routes)
    rows = [row for row in inventory if row["capability_id"] == "spatial-research-handoffs"]
    assert len(rows) == 10
    assert all(row["modularized"] for row in rows)
    keys = [(method, row["path"]) for row in inventory for method in row["methods"]]
    assert len(keys) == len(set(keys))


def test_release_bound_registry_and_carried_forward_registries_are_current() -> None:
    names = [
        "spatial_research_handoff_registry_v4510.json",
        "global_source_federation_registry_v4500.json",
        "live_geospatial_event_fusion_registry_v4490.json",
        "spatial_relationship_registry_v4480.json",
        "spatiotemporal_operator_registry_v4470.json",
        "spatial_layer_registry_v4460.json",
    ]
    for name in names:
        payload = json.loads((ROOT / "backend/data" / name).read_text())
        assert payload["version"] == APP_VERSION, name
    registry = json.loads((ROOT / "backend/data/spatial_research_handoff_registry_v4510.json").read_text())
    assert registry["schema"] == "sc-site-intelligence-spatial-research-handoff-registry/1.0"
    assert len(registry["targets"]) == 7


def test_wordpress_remains_thin_shell_with_no_spatial_research_shortcode() -> None:
    php = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text()
    assert "Version: 4.55.3" in php
    assert "const VERSION = '4.55.3';" in php
    assert "const WORDPRESS_ROLE = 'public-site-launch-bridge';" in php
    assert "spatial_research_shortcode" not in php
