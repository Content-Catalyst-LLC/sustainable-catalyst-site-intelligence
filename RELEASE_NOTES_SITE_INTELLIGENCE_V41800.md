# Site Intelligence v4.18.0 — Global Hydrology, Rivers, Flood & Drought Intelligence

## Release purpose

v4.18.0 extends Earth Observation from atmospheric evidence into rivers, precipitation, modeled flood-awareness products, and drought indicators without adding a new top-level public route family. The established six primary areas and 35 public routes remain unchanged.

## Source families

- **USGS Water Data APIs** — modern OGC/STAC/REST access to continuous and daily streamflow, gage-height, groundwater and monitoring-location data. v4.18 targets `api.waterdata.usgs.gov`, not the legacy WaterServices endpoints scheduled for retirement.
- **NASA GPM IMERG** — global multi-satellite precipitation estimates with Early, Late and Final processing streams.
- **Copernicus GloFAS / Global Flood Monitoring** — modeled river discharge, reanalysis, forecasts, thresholds and flood-awareness products.
- **NOAA/NIDIS Drought.gov** — standardized drought indices and source-published drought-status context.

## Evidence boundary

**HYDROLOGIC EVIDENCE · NOT AN OFFICIAL FLOOD, DROUGHT OR SAFETY WARNING**

The platform does not treat satellite precipitation as a rain-gauge observation; modeled river discharge as a gauge observation; forecasts as observations; near-real-time products as final products; threshold crossings as official flood warnings; drought indices as platform-issued drought declarations; or empty results as evidence of no flood or drought.

## Public contracts

- `GET /public/hydrology`
- `GET /public/hydrology/catalog`
- `GET /public/hydrology/state`
- `POST /public/hydrology/measurement/normalize`
- `POST /public/hydrology/forecast/normalize`
- `POST /public/hydrology/threshold/preview`
- `GET /public/hydrology/export-manifest`
- `GET /public/hydrology/readiness`

## Interface integration

The Hydrology environment is deferred from the v4.17 Atmosphere panel. Browser assets are mirrored byte-for-byte between the FastAPI public app and the WordPress plugin. No v4 public route is removed or reassigned.

## Release gates

The v4.18 live promotion verifier independently requires the Hydrology overview, four-source catalog, bounded USGS state, readiness contract, and shipped `hydrology-v41800.js` asset in addition to all inherited production gates.

Production deployment is not performed by the build environment. Install the WordPress ZIP only after the macOS installer verifies the exact GitHub/Render v4.18.0 live gate.
