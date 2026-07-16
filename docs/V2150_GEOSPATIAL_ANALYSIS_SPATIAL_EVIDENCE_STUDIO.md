# Site Intelligence v2.15.0

## Geospatial Analysis and Spatial Evidence Studio

Site Intelligence v2.15.0 adds a governed geospatial analysis layer to the existing public observatories, historical archive, and connector operations system. The studio accepts validated WGS84 GeoJSON and turns it into inspectable spatial evidence without requiring a proprietary GIS server.

## Core capabilities

- Bounding-box, polygon, and radius areas of interest
- Longitude/latitude validation for EPSG:4326
- Versioned GeoJSON datasets with stable identifiers and SHA-256 digests
- Exact point-in-polygon analysis
- Segment-aware line and polygon intersection checks
- Great-circle point proximity using the haversine formula
- Explicit vertex/centroid approximation labels for non-point proximity
- Geographic counts and numeric aggregation without imputation
- Temporal comparison across spatial dataset versions
- Added, removed, moved, changed, and unchanged feature receipts
- JSON, GeoJSON, CSV, and evidence-packet exports
- Public-safe layer, area, dataset, methodology, and evidence endpoints
- Token-protected administrator operations and analysis history

## Coordinate-reference-system boundary

The studio requires GeoJSON longitude/latitude coordinates in EPSG:4326. It does not silently reproject coordinates. A dataset with another coordinate system must be transformed and documented before registration.

## Spatial methods

### Areas of interest

Areas can be represented as:

- a minimum/maximum longitude and latitude bounding box;
- a GeoJSON polygon; or
- a center point and radius in kilometres.

The registered area retains its type, geometry, visibility, creation time, method declaration, and stable identifier.

### Intersection

Point records are tested directly against the selected area. Line and polygon records use segment-aware checks so an edge crossing an area can be detected even when no feature vertex falls inside it. Radius-area checks use representative points and disclose that boundary-distance precision is limited by the dependency-light implementation.

### Proximity

Point-to-point distance uses the haversine formula. Complex geometries use a clearly labeled minimum vertex/centroid approximation. The result does not claim cadastral, surveying, navigation, or emergency-response precision.

### Aggregation

Only features that intersect the selected area are included. Counts are always explicit. Numeric metrics report observed values, missing values, minimum, maximum, sum, and mean without inserting or estimating missing observations.

### Temporal layer comparison

Stable feature identifiers are compared between two immutable versions of the same dataset. Geometry and property digests identify added, removed, moved, changed, and unchanged records. Spatial or temporal coincidence does not establish causation.

## Responsible-use boundaries

The studio must not be used for:

- military targeting or weapons deployment;
- operational tracking of people;
- precise personal-location profiling;
- inferring protected characteristics from spatial records;
- hidden place rankings or individual risk scores; or
- unsupported causal, legal, severity, or responsibility claims.

Human review is required before publishing consequential spatial conclusions.

## Storage

The zero-cost default is file-backed under `backend/data/spatial_evidence_v2150/`. That writable directory is excluded from Git and immutable release manifests. A hosted deployment requires a persistent Render disk or another durable configured path if registered areas, datasets, versions, and analyses must survive replacement or redeployment.

## Public application

```text
/app/?view=spatial
```

## Endpoints

### Public

- `GET /public/spatial`
- `GET /public/spatial/layers`
- `GET /public/spatial/methodology`
- `GET /public/spatial/areas`
- `GET /public/spatial/datasets`
- `GET /public/spatial/evidence?area_id=...&dataset_id=...`

### Private administrator

- `GET /admin/spatial/control-center`
- `GET /admin/spatial/areas`
- `POST /admin/spatial/areas`
- `GET /admin/spatial/datasets`
- `POST /admin/spatial/datasets/register`
- `POST /admin/spatial/analyze/intersection`
- `POST /admin/spatial/analyze/proximity`
- `POST /admin/spatial/analyze/aggregate`
- `POST /admin/spatial/analyze/compare`
- `GET /admin/spatial/analyses`
- `GET /admin/spatial/export`

## WordPress

- Public spatial summary and evidence interface: `[sc_public_spatial_evidence]`
- Administrator control center: `[sc_spatial_evidence_control_center]`

## Command line

```bash
python scripts/spatial_evidence_v2150.py summary
python scripts/spatial_evidence_v2150.py layers
python scripts/spatial_evidence_v2150.py areas --public
python scripts/spatial_evidence_v2150.py datasets --public
```
