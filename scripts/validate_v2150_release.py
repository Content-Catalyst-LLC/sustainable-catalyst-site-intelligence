#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CHECKS = {
    "backend/app/version.py": [
        'APP_VERSION = "2.15.0"',
        'RELEASE_NAME = "Geospatial Analysis and Spatial Evidence Studio"',
    ],
    "backend/app/config.py": [
        "spatial_evidence_enabled",
        "spatial_evidence_root_path",
        "spatial_evidence_areas_path",
        "spatial_evidence_datasets_path",
        "spatial_evidence_analysis_path",
        "spatial_evidence_max_radius_km",
    ],
    "backend/app/spatial_evidence_v2150.py": [
        'RELEASE_VERSION = "2.15.0"',
        'SCHEMA_VERSION = "sc-site-intelligence-spatial-evidence/1.0"',
        'DATASET_SCHEMA = "sc-site-intelligence-spatial-dataset/1.0"',
        'ANALYSIS_SCHEMA = "sc-site-intelligence-spatial-analysis/1.0"',
        "def create_area(",
        "def register_dataset(",
        "def intersection(",
        "def proximity(",
        "def aggregate(",
        "def compare(",
        "def export_evidence(",
        "def control_center(",
    ],
    "backend/app/main.py": [
        '"/public/spatial"',
        '"/public/spatial/layers"',
        '"/public/spatial/methodology"',
        '"/public/spatial/evidence"',
        '"/admin/spatial/control-center"',
        '"/admin/spatial/datasets/register"',
        '"/admin/spatial/analyze/intersection"',
        '"/admin/spatial/analyze/proximity"',
        '"/admin/spatial/analyze/aggregate"',
        '"/admin/spatial/analyze/compare"',
    ],
    "backend/data/spatial_evidence_policy_v2150.json": [
        '"version": "2.15.0"',
        '"public_raw_private_dataset_access": false',
        '"paid_gis_server_required": false',
        "military targeting",
    ],
    "backend/data/spatial_layer_catalog_v2150.json": [
        '"version": "2.15.0"',
        '"id": "earth-observation"',
        '"id": "humanitarian-events"',
        '"id": "custom"',
    ],
    "backend/public_app/index.html": [
        'data-route="spatial"',
        'id="spatialEvidenceStudio"',
        '/app/assets/spatial-v2150.css?v=2.15.0',
        '/app/assets/spatial-v2150.js?v=2.15.0',
    ],
    "backend/public_app/assets/app.js": [
        'spatial:["GEOSPATIAL ANALYSIS AND SPATIAL EVIDENCE STUDIO"',
        'window.SCSpatialV2150',
        'spatial:{label:"Spatial Evidence"',
    ],
    "backend/public_app/assets/spatial-v2150.js": [
        'const VERSION = "2.15.0"',
        'window.SCSpatialV2150',
        '/public/spatial/evidence?',
    ],
    "backend/public_app/assets/spatial-v2150.css": [
        ".spatial-evidence-studio",
        ".spatial-grid",
        "@media(max-width:800px)",
    ],
    "backend/public_app/service-worker.js": [
        'const RELEASE="2.15.0"',
        '"/app/assets/spatial-v2150.css"',
        '"/app/assets/spatial-v2150.js"',
    ],
    "backend/tests/test_geospatial_analysis_spatial_evidence_v2150.py": [
        "test_bbox_polygon_and_radius_areas_are_validated",
        "test_polygon_and_line_intersection_are_segment_aware",
        "test_proximity_uses_exact_point_distance_and_labels_non_point_approximation",
        "test_temporal_layer_comparison_uses_stable_identifiers",
    ],
    "backend/tests/test_geospatial_analysis_release_contract_v2150.py": [
        "test_v2150_policy_and_catalog_define_spatial_governance",
        "test_v2150_public_application_registers_spatial_workspace_and_offline_assets",
        "test_v2150_runtime_spatial_state_is_excluded_from_source_release",
    ],
    "scripts/spatial_evidence_v2150.py": [
        "create-area",
        "intersection",
        "proximity",
        "aggregate",
        "compare",
        "export",
    ],
    "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php": [
        "Version: 2.15.0",
        "sc_public_spatial_evidence",
        "sc_spatial_evidence_control_center",
        "public-spatial-evidence",
        "public/spatial",
    ],
    "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js": [
        "spatial-evidence",
        "/public-spatial-evidence",
    ],
    "docs/V2150_GEOSPATIAL_ANALYSIS_SPATIAL_EVIDENCE_STUDIO.md": [
        "Exact point-in-polygon analysis",
        "Segment-aware line and polygon intersection",
        "EPSG:4326",
        "military targeting",
        "persistent Render disk",
    ],
    "docs/RELEASE_MANIFEST_V2150.json": [
        '"coordinate_reference_system": "EPSG:4326"',
        '"silent_reprojection": false',
        '"silent_imputation": false',
        '"paid_gis_server_required": false',
        '"public_raw_private_dataset_access": false',
    ],
    "README.md": [
        "Current release:** v2.15.0 — Geospatial Analysis and Spatial Evidence Studio",
        "/app/?view=spatial",
        "spatial_evidence_v2150.py",
    ],
    "CHANGELOG.md": [
        "## 2.15.0 — Geospatial Analysis and Spatial Evidence Studio",
    ],
}

for relative, markers in CHECKS.items():
    path = ROOT / relative
    if not path.exists():
        raise SystemExit(f"Missing release file: {relative}")
    text = path.read_text(encoding="utf-8")
    for marker in markers:
        if marker not in text:
            raise SystemExit(f"Missing release marker {marker!r} in {relative}")

policy = json.loads((ROOT / "backend/data/spatial_evidence_policy_v2150.json").read_text(encoding="utf-8"))
catalog = json.loads((ROOT / "backend/data/spatial_layer_catalog_v2150.json").read_text(encoding="utf-8"))
release = json.loads((ROOT / "docs/RELEASE_MANIFEST_V2150.json").read_text(encoding="utf-8"))

if policy.get("schema") != "sc-site-intelligence-spatial-evidence/1.0":
    raise SystemExit("Spatial evidence policy schema is invalid.")
if policy.get("public_raw_private_dataset_access") is not False:
    raise SystemExit("Spatial policy must prohibit public access to private raw datasets.")
if policy.get("paid_gis_server_required") is not False:
    raise SystemExit("The release must preserve zero-cost operation without a paid GIS server.")
if len(catalog.get("layers", [])) < 6:
    raise SystemExit("Spatial layer catalog is incomplete.")
if release.get("coordinate_reference_system") != "EPSG:4326":
    raise SystemExit("Release CRS declaration must be EPSG:4326.")
if release.get("silent_reprojection") is not False or release.get("silent_imputation") is not False:
    raise SystemExit("Spatial release must prohibit silent reprojection and imputation.")

required_public = {
    "/public/spatial",
    "/public/spatial/layers",
    "/public/spatial/methodology",
    "/public/spatial/areas",
    "/public/spatial/datasets",
    "/public/spatial/evidence",
}
if not required_public.issubset(set(release.get("public_endpoints", []))):
    raise SystemExit("Spatial public endpoint manifest is incomplete.")

runtime_paths = [
    "backend/data/spatial_evidence_v2150",
    "backend/data/historical_archive_v2140",
    "backend/data/country_last_known_good.json",
    "backend/data/platform_core_queue.jsonl",
    "backend/data/connector_operations_state_v2130.json",
    "backend/data/connector_operations_history_v2130.jsonl",
    "backend/data/connector_operations_quarantine_v2130.jsonl",
]
for relative in runtime_paths:
    if (ROOT / relative).exists():
        raise SystemExit(f"Runtime artifact must not be present in the release: {relative}")

for path in ROOT.rglob("*"):
    if path.is_dir() and path.name in {"__pycache__", ".pytest_cache"}:
        raise SystemExit(f"Generated cache directory must not be packaged: {path.relative_to(ROOT)}")

print("Site Intelligence v2.15.0 release contract passed.")
