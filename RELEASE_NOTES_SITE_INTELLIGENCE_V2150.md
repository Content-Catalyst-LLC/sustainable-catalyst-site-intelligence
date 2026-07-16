# Site Intelligence v2.15.0

## Geospatial Analysis and Spatial Evidence Studio

Site Intelligence v2.15.0 advances the public observatory from map presentation into transparent spatial analysis. The release adds governed areas of interest, versioned spatial datasets, intersection, proximity, geographic aggregation, temporal layer comparison, and source-preserving evidence exports while retaining the zero-cost, public-first architecture.

## Added

- Bounding-box, polygon, and radius areas of interest
- EPSG:4326 longitude/latitude validation
- Versioned GeoJSON datasets with stable IDs and SHA-256 digests
- Exact point-in-polygon analysis
- Segment-aware line and polygon intersection
- Haversine point proximity
- Explicit vertex/centroid approximation labels for non-point features
- Geographic counts and numeric aggregation without silent imputation
- Temporal dataset comparison across stable feature identifiers
- Added, removed, moved, changed, and unchanged feature receipts
- Public spatial summary, catalog, methodology, areas, datasets, and evidence endpoints
- Token-protected spatial administration and analysis history
- JSON, GeoJSON, CSV, and evidence-packet exports
- Dedicated `/app/?view=spatial` workspace
- Offline application-shell coverage for the new spatial assets
- Public and administrator-only WordPress interfaces
- `scripts/spatial_evidence_v2150.py` command-line utility

## Public endpoints

- `GET /public/spatial`
- `GET /public/spatial/layers`
- `GET /public/spatial/methodology`
- `GET /public/spatial/areas`
- `GET /public/spatial/datasets`
- `GET /public/spatial/evidence`

## Administrator endpoints

- `GET /admin/spatial/control-center`
- `GET|POST /admin/spatial/areas`
- `GET /admin/spatial/datasets`
- `POST /admin/spatial/datasets/register`
- `POST /admin/spatial/analyze/intersection`
- `POST /admin/spatial/analyze/proximity`
- `POST /admin/spatial/analyze/aggregate`
- `POST /admin/spatial/analyze/compare`
- `GET /admin/spatial/analyses`
- `GET /admin/spatial/export`

## WordPress shortcodes

```text
[sc_public_spatial_evidence]
```

```text
[sc_spatial_evidence_control_center]
```

The control-center shortcode is restricted to WordPress administrators.

## Governance

- No silent coordinate reprojection
- No silent imputation
- No proprietary place ranking
- No military targeting or weapons deployment
- No operational tracking of individuals
- No precise personal-location profiling
- No automatic causal, legal, severity, or responsibility conclusions
- Human review required for consequential spatial claims

## Storage

Writable spatial state is file-backed by default and excluded from Git and release manifests. Use a persistent Render disk or another durable path when registered areas, datasets, versions, and analyses must survive redeployment.
