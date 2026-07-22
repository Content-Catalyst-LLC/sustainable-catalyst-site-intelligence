from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import app
from app.spatial_evidence_v2150 import SpatialEvidenceStudio, SCHEMA_VERSION

ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "backend/data/spatial_evidence_policy_v2150.json"
CATALOG = ROOT / "backend/data/spatial_layer_catalog_v2150.json"


class Clock:
    def __init__(self) -> None:
        self.value = datetime(2026, 7, 16, 12, 0, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        return self.value

    def advance(self, **kwargs) -> None:
        self.value += timedelta(**kwargs)


def _settings(tmp_path: Path, **overrides) -> Settings:
    root = tmp_path / "spatial"
    values = {
        "version": "3.17.0",
        "spatial_evidence_policy_path": str(POLICY),
        "spatial_evidence_layer_catalog_path": str(CATALOG),
        "spatial_evidence_root_path": str(root),
        "spatial_evidence_areas_path": str(root / "areas.jsonl"),
        "spatial_evidence_datasets_path": str(root / "datasets.jsonl"),
        "spatial_evidence_analysis_path": str(root / "analyses.jsonl"),
    }
    values.update(overrides)
    return Settings(**values)


def _features(points):
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "id": identifier,
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
                "properties": properties,
            }
            for identifier, lon, lat, properties in points
        ],
    }


def test_bbox_polygon_and_radius_areas_are_validated(tmp_path):
    studio = SpatialEvidenceStudio(_settings(tmp_path))
    bbox = studio.create_area({"area_id": "chicago-box", "name": "Chicago box", "mode": "bbox", "bbox": [-88, 41, -87, 42], "visibility": "public"})
    polygon = studio.create_area({"area_id": "lake-polygon", "name": "Lake area", "mode": "polygon", "geometry": {"type": "Polygon", "coordinates": [[[-88, 41], [-87, 41], [-87, 42], [-88, 42], [-88, 41]]]}})
    radius = studio.create_area({"area_id": "loop-radius", "name": "Loop radius", "mode": "radius", "center": [-87.6298, 41.8781], "radius_km": 25})
    assert bbox["area"]["approximate_area_sq_km"] > 0
    assert polygon["area"]["mode"] == "polygon"
    assert radius["area"]["radius_km"] == 25
    assert studio.areas(public=True)["count"] == 1


def test_spatial_dataset_registration_redacts_secrets_and_deduplicates(tmp_path):
    studio = SpatialEvidenceStudio(_settings(tmp_path))
    request = {
        "dataset_id": "events",
        "title": "Events",
        "source": "Public source",
        "visibility": "public",
        "feature_collection": _features([("a", -87.63, 41.88, {"value": 2, "api_token": "hidden"})]),
    }
    first = studio.register_dataset(request)
    duplicate = studio.register_dataset(request)
    assert first["status"] == "registered"
    assert duplicate["status"] == "unchanged" and duplicate["deduplicated"] is True
    _, payload = studio._dataset("events", public=True)
    assert payload["features"][0]["properties"]["api_token"] == "[redacted]"


def test_intersection_and_aggregation_are_source_aware_without_imputation(tmp_path):
    studio = SpatialEvidenceStudio(_settings(tmp_path))
    studio.create_area({"area_id": "city", "mode": "bbox", "bbox": [-88, 41, -87, 42], "visibility": "public"})
    studio.register_dataset({
        "dataset_id": "observations",
        "source": "Example observations",
        "visibility": "public",
        "feature_collection": _features([
            ("inside", -87.63, 41.88, {"score": 10}),
            ("missing", -87.7, 41.9, {}),
            ("outside", -90, 40, {"score": 100}),
        ]),
    })
    intersection = studio.intersection("city", "observations", public=True)
    assert intersection["matched_feature_count"] == 2
    aggregate = studio.aggregate("city", "observations", metric="score", public=True)
    assert aggregate["summary"]["feature_count"] == 2
    assert aggregate["summary"]["mean"] == 10
    assert aggregate["summary"]["missing_metric_count"] == 1
    assert aggregate["summary"]["imputation_applied"] is False


def test_polygon_and_line_intersection_are_segment_aware(tmp_path):
    studio = SpatialEvidenceStudio(_settings(tmp_path))
    studio.create_area({"area_id": "square", "mode": "bbox", "bbox": [0, 0, 1, 1]})
    collection = {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "id": "crossing-line", "geometry": {"type": "LineString", "coordinates": [[-1, 0.5], [2, 0.5]]}, "properties": {}},
            {"type": "Feature", "id": "covering-polygon", "geometry": {"type": "Polygon", "coordinates": [[[-1, -1], [2, -1], [2, 2], [-1, 2], [-1, -1]]]}, "properties": {}},
        ],
    }
    studio.register_dataset({"dataset_id": "geometry", "source": "Geometry fixture", "feature_collection": collection})
    result = studio.intersection("square", "geometry")
    assert {item["id"] for item in result["feature_collection"]["features"]} == {"crossing-line", "covering-polygon"}


def test_proximity_uses_exact_point_distance_and_labels_non_point_approximation(tmp_path):
    studio = SpatialEvidenceStudio(_settings(tmp_path))
    collection = {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "id": "point", "geometry": {"type": "Point", "coordinates": [0, 0]}, "properties": {}},
            {"type": "Feature", "id": "line", "geometry": {"type": "LineString", "coordinates": [[0.1, 0], [0.2, 0]]}, "properties": {}},
        ],
    }
    studio.register_dataset({"dataset_id": "nearby", "source": "Fixture", "feature_collection": collection})
    result = studio.proximity("nearby", 0, 0, max_distance_km=30)
    assert result["matches"][0]["feature_id"] == "point"
    assert result["matches"][0]["distance_method"] == "exact point distance"
    assert result["approximate_non_point_count"] == 1


def test_temporal_layer_comparison_uses_stable_identifiers(tmp_path):
    clock = Clock()
    studio = SpatialEvidenceStudio(_settings(tmp_path), now_fn=clock)
    first = studio.register_dataset({"dataset_id": "changing", "source": "Fixture", "observed_at": "2026-07-01", "feature_collection": _features([("a", 0, 0, {"value": 1}), ("b", 1, 1, {"value": 2})])})
    clock.advance(days=1)
    second = studio.register_dataset({"dataset_id": "changing", "source": "Fixture", "observed_at": "2026-07-02", "feature_collection": _features([("a", 0.5, 0, {"value": 3}), ("c", 2, 2, {"value": 4})])})
    comparison = studio.compare("changing", first["dataset"]["version_id"], second["dataset"]["version_id"], metric="value")
    assert comparison["counts"]["added"] == 1
    assert comparison["counts"]["removed"] == 1
    assert comparison["counts"]["geometry_changed"] == 1
    assert comparison["metric_changes"][0]["delta"] == 2


def test_public_evidence_export_requires_public_area_and_dataset(tmp_path):
    studio = SpatialEvidenceStudio(_settings(tmp_path))
    studio.create_area({"area_id": "public-area", "mode": "bbox", "bbox": [-1, -1, 1, 1], "visibility": "public"})
    studio.register_dataset({"dataset_id": "public-data", "source": "Fixture", "visibility": "public", "feature_collection": _features([("a", 0, 0, {"value": 1})])})
    packet = studio.export_evidence("public-area", "public-data", public=True)
    assert packet["packet"]["packet_sha256"]
    assert "feature_id,geometry_type,value" in packet["csv"]
    assert packet["geojson"]["features"][0]["id"] == "a"


def test_public_summary_and_methodology_expose_safety_boundaries(tmp_path):
    studio = SpatialEvidenceStudio(_settings(tmp_path))
    summary = studio.public_summary()
    methodology = studio.methodology()
    assert summary["schema"] == SCHEMA_VERSION
    assert summary["version"] == "3.17.0"
    assert summary["recommended_shortcode"] == "[sc_public_spatial_evidence]"
    assert methodology["privacy"]["individual_tracking"] is False
    assert methodology["coordinate_reference_system"] == "WGS84 / EPSG:4326 only"


def test_spatial_routes_are_registered_and_private_payloads_stay_admin_only(tmp_path):
    settings = _settings(tmp_path)
    app.dependency_overrides[get_settings] = lambda: settings
    try:
        client = TestClient(app)
        for path in ["/public/spatial", "/public/spatial/layers", "/public/spatial/methodology", "/public/spatial/areas", "/public/spatial/datasets", "/admin/spatial/control-center", "/admin/spatial/areas", "/admin/spatial/datasets", "/admin/spatial/analyses"]:
            response = client.get(path)
            assert response.status_code == 200, (path, response.text)
            assert response.json()["ok"] is True
        area = client.post("/admin/spatial/areas", json={"area_id": "route-area", "mode": "bbox", "bbox": [-1, -1, 1, 1], "visibility": "public"})
        assert area.status_code == 200
        dataset = client.post("/admin/spatial/datasets/register", json={"dataset_id": "route-data", "source": "Fixture", "visibility": "public", "feature_collection": _features([("a", 0, 0, {"value": 1})])})
        assert dataset.status_code == 200
        intersection = client.post("/admin/spatial/analyze/intersection", json={"area_id": "route-area", "dataset_id": "route-data"})
        assert intersection.status_code == 200 and intersection.json()["matched_feature_count"] == 1
        public = client.get("/public/spatial/evidence?area_id=route-area&dataset_id=route-data")
        assert public.status_code == 200 and public.json()["packet"]["matched_feature_count"] == 1
    finally:
        app.dependency_overrides.clear()
