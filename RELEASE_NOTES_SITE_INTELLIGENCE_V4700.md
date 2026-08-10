# Site Intelligence v4.15.0 — Seafloor & Bathymetric Intelligence

v4.15.0 extends the Earth Observation ocean sequence from the water column to the seabed while preserving the v4 six-area / 35-route platform architecture.

## New capability

- Seafloor & Bathymetric Intelligence remains inside the existing Earth Observation route.
- Registered source contracts:
  - GEBCO_2026 global gridded bathymetry and web-map/download services.
  - EMODnet Bathymetry harmonised Digital Terrain Model and OGC web-service discovery for European sea regions.
  - NOAA NCEI Bathymetry & Seafloor Mapping archives for multibeam, singlebeam, lidar, crowdsourced bathymetry, DEMs, and survey footprints.
- Eight initial layers: bathymetric elevation/depth, terrain relief, grid source type/provenance class, multibeam coverage, singlebeam tracklines, bathymetric lidar, crowdsourced bathymetry, and survey/dataset footprints.
- Source-attributed bathymetry sample normalization with explicit vertical datum, resolution, source type, evidence class, and SHA-256 fingerprint.
- Survey-footprint normalization that never promotes polygon coverage into a point measurement or uniform-density claim.
- Evidence-manifest export for reproducible seafloor state.
- Deferred browser shell loaded from Water Column so the base application does not absorb another heavy observation interface.

## Scientific boundaries

v4.15.0 does not treat a terrain grid as a sounding archive. Grid spacing is not represented as measurement spacing, positional accuracy, or uncertainty. Survey footprints do not prove uniform sounding density. Hillshade and terrain-relief rendering are presentation derivatives, not independent bathymetric observations. Depth/elevation sign conventions and vertical datums are never silently transformed.

The local seabed visualization is labeled `ORIENTATION TERRAIN · NOT BATHYMETRIC PIXELS` until an explicit source terrain record is loaded.

## Public contracts

- `GET /public/seafloor-intelligence`
- `GET /public/seafloor-intelligence/catalog`
- `GET /public/seafloor-intelligence/state`
- `POST /public/seafloor-intelligence/sample/normalize`
- `POST /public/seafloor-intelligence/footprint/normalize`
- `GET /public/seafloor-intelligence/export-manifest`
- `GET /public/seafloor-intelligence/readiness`

## Upstream references

- GEBCO gridded bathymetry: https://www.gebco.net/data-products/gridded-bathymetry-data
- GEBCO web-map services: https://www.gebco.net/data-products/gebco-web-services/web-map-service
- EMODnet Bathymetry: https://emodnet.ec.europa.eu/en/bathymetry
- EMODnet web-service documentation: https://emodnet.ec.europa.eu/en/emodnet-web-service-documentation
- NOAA NCEI Bathymetry: https://www.ncei.noaa.gov/products/bathymetry
- NOAA NCEI maps and geospatial products: https://www.ncei.noaa.gov/maps-and-geospatial-products

Production deployment is performed only by the release installer after package validation and the live GitHub/Render gate.
