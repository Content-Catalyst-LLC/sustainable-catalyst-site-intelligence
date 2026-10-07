from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.live_geospatial_event_fusion_v4490 import (
    EVENT_CLUSTER_SCHEMA,
    EVENT_QUERY_RESULT_SCHEMA,
    EVENT_SCHEMA,
    FUSION_RESULT_SCHEMA,
    GRAPH_FUSION_SCHEMA,
    SNAPSHOT_SCHEMA,
    TRANSITION_SCHEMA,
    build_snapshot,
    fuse_graph,
    fuse_layers,
    normalize_event,
    normalize_source_event,
    query_events,
    reconcile_events,
    transition_event,
)
from app.main import app
from app.route_registry_v4430 import capability_manifest, route_inventory
from app.spatial_relationship_graph_v4480 import build_graph
from app.version import APP_VERSION, RELEASE_NAME

ROOT = Path(__file__).resolve().parents[2]
client = TestClient(app)


def _event(event_id: str = "quake-a", lon: float = -90.20, lat: float = 38.63, *, correlation_keys=None, severity="severe") -> dict:
    return {
        "event_id": event_id,
        "event_type": "earthquake",
        "title": "Test earthquake",
        "lifecycle_state": "active",
        "severity": {"level": severity, "source_value": 6.1},
        "confidence": 0.94,
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
        "observed_at": "2026-10-05T08:00:00Z",
        "updated_at": "2026-10-05T08:05:00Z",
        "source": {
            "feed_id": "usgs_earthquakes",
            "source_id": "usgs_earthquakes",
            "authority": "U.S. Geological Survey",
            "record_id": event_id,
            "url": f"https://example.test/{event_id}",
        },
        "correlation_keys": correlation_keys or [],
        "properties": {"magnitude": 6.1},
    }


def _evidence(layer_id: str, object_id: str, lon: float, lat: float) -> dict:
    return {
        "object_id": object_id,
        "layer_id": layer_id,
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
        "observed_at": "2026-10-05T08:00:00Z",
        "properties": {"name": object_id},
        "source": {"source_id": "fixture", "authority": "Fixture Authority", "record_id": object_id},
    }


def test_release_identity() -> None:
    assert APP_VERSION == "4.55.2"
    assert RELEASE_NAME == "Advanced Domain Intelligence Workspace Expansion"


def test_registry_schema_sources_and_lifecycle_endpoints() -> None:
    registry = client.get("/public/live-geospatial/registry")
    assert registry.status_code == 200
    payload = registry.json()
    assert payload["version"] == APP_VERSION
    assert payload["event_object_schema"] == EVENT_SCHEMA
    assert payload["source_adapter_count"] == 5
    assert payload["lifecycle_state_count"] == 5

    schema = client.get("/public/live-geospatial/event-schema").json()
    assert schema["schema"] == EVENT_SCHEMA
    assert "confidence" in schema["fields"]
    assert "earthquake" in schema["event_types"]

    sources = client.get("/public/live-geospatial/sources").json()
    assert sources["count"] == 5
    ids = {row["feed_id"] for row in sources["sources"]}
    assert {"usgs_earthquakes", "nasa_eonet", "noaa_nws"} <= ids

    lifecycle = client.get("/public/live-geospatial/lifecycle").json()
    assert lifecycle["schema"] == TRANSITION_SCHEMA
    assert "resolved" in lifecycle["states"]
    assert "resolved" in lifecycle["transitions"]["active"]


def test_canonical_event_normalization_is_deterministic_and_embeds_v446_evidence() -> None:
    a = normalize_event(_event())
    b = normalize_event(_event())
    assert a == b
    assert a["schema"] == EVENT_SCHEMA
    assert a["content_digest"].startswith("sha256:")
    assert a["evidence_object"]["schema"] == "sc-site-intelligence-spatial-evidence-object/2.0"
    assert a["evidence_object"]["layer_id"] == "live-events-hazards"
    assert a["bbox"] == [-90.2, 38.63, -90.2, 38.63]
    assert a["severity"]["rank"] == 4
    assert a["confidence"] == 0.94
    assert a["provenance"]["impact_confirmed"] is False
    assert any(key.startswith("strict:") for key in a["correlation_keys"])


def test_normalization_rejects_unknown_event_type_feed_and_invalid_confidence() -> None:
    bad_type = _event(); bad_type["event_type"] = "magic-event"
    with pytest.raises(ValueError): normalize_event(bad_type)
    bad_feed = _event(); bad_feed["source"]["feed_id"] = "unknown-feed"
    with pytest.raises(ValueError): normalize_event(bad_feed)
    bad_confidence = _event(); bad_confidence["confidence"] = 1.2
    with pytest.raises(ValueError): normalize_event(bad_confidence)


def test_usgs_source_adapter_normalizes_geojson_feature() -> None:
    raw = {
        "type": "Feature",
        "id": "us7000test",
        "properties": {
            "mag": 6.2,
            "title": "M 6.2 - Test Region",
            "place": "Test Region",
            "time": 1791187200000,
            "updated": 1791187260000,
            "status": "reviewed",
            "url": "https://earthquake.usgs.gov/example",
            "tsunami": 0,
        },
        "geometry": {"type": "Point", "coordinates": [-90.2, 38.63, 10.0]},
    }
    event = normalize_source_event({"feed_id": "usgs_earthquakes", "record": raw})
    assert event["event_id"] == "us7000test"
    assert event["event_type"] == "earthquake"
    assert event["severity"]["level"] == "severe"
    assert event["source"]["feed_id"] == "usgs_earthquakes"
    assert event["provenance"]["source_adapter"] == "usgs-geojson"


def test_eonet_and_noaa_source_adapters_preserve_source_semantics() -> None:
    eonet = normalize_source_event({
        "feed_id": "nasa_eonet",
        "record": {
            "id": "EONET_1", "title": "Wildfire test", "categories": [{"title": "Wildfires"}],
            "geometry": [{"date": "2026-10-05T08:00:00Z", "type": "Point", "coordinates": [-90.2, 38.63]}],
            "sources": [{"id": "Test", "url": "https://eonet.gsfc.nasa.gov/example"}], "closed": None,
        },
    })
    assert eonet["event_type"] == "wildfire"
    assert eonet["lifecycle_state"] == "active"

    noaa = normalize_source_event({
        "feed_id": "noaa_nws",
        "record": {
            "id": "urn:oid:noaa-test",
            "geometry": {"type": "Polygon", "coordinates": [[[-90.3,38.5],[-90.1,38.5],[-90.1,38.7],[-90.3,38.7],[-90.3,38.5]]]},
            "properties": {"event": "Severe Thunderstorm Warning", "headline": "Test warning", "severity": "Severe", "status": "Actual", "effective": "2026-10-05T08:00:00Z", "expires": "2026-10-05T09:00:00Z", "sent": "2026-10-05T07:58:00Z"},
        },
    })
    assert noaa["event_type"] == "weather-alert"
    assert noaa["severity"]["level"] == "severe"
    assert noaa["valid_time"]["end"] is not None


def test_reconciliation_merges_only_shared_strict_or_explicit_keys() -> None:
    one = _event("source-a", correlation_keys=["incident:alpha"])
    two = _event("source-b", correlation_keys=["incident:alpha"])
    two["source"] = {"feed_id": "nasa_eonet", "source_id": "nasa_eonet", "authority": "NASA EONET", "record_id": "source-b"}
    three = _event("nearby-but-distinct", lon=-90.2001, lat=38.6301)
    result = reconcile_events({"events": [one, two, three]})
    assert result["schema"] == EVENT_CLUSTER_SCHEMA
    assert result["cluster_count"] == 2
    merged = next(row for row in result["clusters"] if row["event_count"] == 2)
    assert merged["source_count"] == 2
    assert "incident:alpha" in merged["shared_correlation_keys"]
    assert result["merged_cluster_count"] == 1


def test_reconciliation_does_not_fuzzy_merge_nearby_events() -> None:
    a = _event("a", lon=-90.2, lat=38.63); a["title"] = "Incident A"
    b = _event("b", lon=-90.20001, lat=38.63001); b["title"] = "Incident B"
    result = reconcile_events({"events": [a, b]})
    assert result["cluster_count"] == 2
    assert result["merged_cluster_count"] == 0
    assert result["identity_semantics"] == "strict-deterministic-no-fuzzy-merge"


def test_event_query_filters_space_time_severity_and_computes_explicit_freshness() -> None:
    severe = _event("severe", severity="severe")
    minor = _event("minor", lon=-91.0, lat=39.0, severity="minor")
    result = query_events({
        "events": [severe, minor],
        "as_of": "2026-10-05T08:20:00Z",
        "query": {"bbox": [-90.4, 38.4, -90.0, 38.8], "minimum_severity_rank": 3, "start": "2026-10-05T07:00:00Z", "end": "2026-10-05T09:00:00Z"},
    })
    assert result["schema"] == EVENT_QUERY_RESULT_SCHEMA
    assert result["count"] == 1
    assert result["events"][0]["event_id"] == "severe"
    assert result["events"][0]["freshness"]["state"] == "fresh"
    assert result["events"][0]["freshness"]["age_minutes"] == 15.0


def test_lifecycle_transition_is_explicit_and_invalid_transition_rejected() -> None:
    event = normalize_event(_event())
    result = transition_event({"event": event, "new_state": "resolved", "transitioned_at": "2026-10-05T09:00:00Z", "reason": "source-marked-closed"})
    assert result["schema"] == TRANSITION_SCHEMA
    assert result["from_state"] == "active"
    assert result["to_state"] == "resolved"
    assert result["event"]["lifecycle_state"] == "resolved"
    assert result["source_event_digest"] == event["content_digest"]
    with pytest.raises(ValueError):
        transition_event({"event": result["event"], "new_state": "detected"})


def test_layer_fusion_preserves_digests_and_never_claims_confirmed_impact() -> None:
    result = fuse_layers({
        "events": [_event()],
        "objects": [
            _evidence("energy-power-systems", "power-a", -90.2, 38.63),
            _evidence("water-sanitation-infrastructure", "water-a", -90.2, 38.63),
            _evidence("human-settlements-built-environment", "far", -91.0, 39.0),
        ],
        "require_temporal_overlap": True,
    })
    assert result["schema"] == FUSION_RESULT_SCHEMA
    assert result["match_count"] == 2
    assert result["layer_match_counts"] == {"energy-power-systems": 1, "water-sanitation-infrastructure": 1}
    assert all(row["relationship_type"] == "potentially-exposed-to-event" for row in result["matches"])
    assert all(row["impact_confirmed"] is False for row in result["matches"])
    assert all(len(row["source_content_digests"]) == 2 for row in result["matches"])


def test_graph_fusion_is_ephemeral_and_does_not_mutate_source_graph() -> None:
    graph = build_graph({
        "objects": [
            _evidence("energy-power-systems", "power-a", -90.2, 38.63),
            _evidence("water-sanitation-infrastructure", "water-a", -90.21, 38.64),
        ],
        "relationships": [{"source_node_id": "power-a", "target_node_id": "water-a", "relationship_type": "supplies"}],
        "derive_spatial_relationships": False,
    })
    original_digest = graph["graph_digest"]
    fused = fuse_graph({"events": [_event()], "graph": graph, "require_temporal_overlap": True})
    assert fused["schema"] == GRAPH_FUSION_SCHEMA
    assert fused["source_graph_digest"] == original_digest
    assert fused["fusion_edge_count"] == 1
    edge = fused["fusion_edges"][0]
    assert edge["source_node_id"] == "power-a"
    assert edge["relationship_type"] == "potentially-exposed-to-event"
    assert edge["impact_confirmed"] is False
    assert edge["ephemeral"] is True
    assert fused["graph_mutated"] is False
    assert graph["graph_digest"] == original_digest


def test_snapshot_combines_query_layer_and_graph_fusion_with_interpretation_boundary() -> None:
    graph_build = {"objects": [_evidence("energy-power-systems", "power-a", -90.2, 38.63)], "derive_spatial_relationships": False}
    snapshot = build_snapshot({
        "events": [_event()],
        "as_of": "2026-10-05T08:20:00Z",
        "query": {"bbox": [-90.3, 38.5, -90.1, 38.7], "lifecycle_states": ["active"]},
        "objects": [_evidence("energy-power-systems", "power-a", -90.2, 38.63)],
        "graph_build": graph_build,
        "require_temporal_overlap": True,
    })
    assert snapshot["schema"] == SNAPSHOT_SCHEMA
    assert snapshot["event_count"] == 1
    assert snapshot["layer_fusion"]["match_count"] == 1
    assert snapshot["graph_fusion"]["fusion_edge_count"] == 1
    assert snapshot["snapshot_digest"].startswith("sha256:")
    assert "does not establish impact" in snapshot["interpretation_boundary"]


def test_http_error_boundary_and_compatibility_contract() -> None:
    bad = client.post("/public/live-geospatial/events/normalize", json={"event_type": "earthquake"})
    assert bad.status_code == 400
    compat = client.get("/public/live-geospatial/compatibility")
    assert compat.status_code == 200
    payload = compat.json()
    assert payload["v4_46_spatial_evidence"]["status"] == "preserved-and-consumed"
    assert payload["v4_47_spatiotemporal"]["status"] == "preserved-and-consumed"
    assert payload["v4_48_spatial_graph"]["status"] == "preserved-and-consumed"
    assert payload["v4_48_spatial_graph"]["graph_mutation"] is False


def test_capability_registry_owns_all_live_geospatial_routes_and_no_duplicates() -> None:
    manifest = capability_manifest(app.routes)
    family = next(row for row in manifest["capabilities"] if row["capability_id"] == "live-geospatial-fusion")
    assert manifest["registry_version"] == "2.3.0"
    assert manifest["unclassified_route_count"] == 0
    assert family["route_count"] == 13
    assert family["modularized_route_count"] == 13
    inventory = route_inventory(app.routes)
    live = [row for row in inventory if row["capability_id"] == "live-geospatial-fusion"]
    assert len(live) == 13
    assert all(row["modularized"] for row in live)
    keys = [(method, row["path"]) for row in inventory for method in row["methods"]]
    assert len(keys) == len(set(keys))


def test_release_bound_fusion_registry_is_current_and_live_source_registry_carried_forward() -> None:
    fusion = json.loads((ROOT / "backend/data/live_geospatial_event_fusion_registry_v4490.json").read_text())
    live = json.loads((ROOT / "backend/data/live_intelligence_source_registry_v320.json").read_text())
    assert fusion["version"] == APP_VERSION
    assert fusion["identity_semantics"] == "strict-deterministic-no-fuzzy-merge"
    assert fusion["event_object_schema"] == EVENT_SCHEMA
    assert live["version"] == APP_VERSION
    assert {row["feed_id"] for row in live["sources"]} >= {"usgs_earthquakes", "nasa_eonet", "noaa_nws"}
