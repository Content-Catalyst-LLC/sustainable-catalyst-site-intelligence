# Site Intelligence v4.22.0 — Global Climate Baselines, Anomalies & Extremes Intelligence

## Purpose

Extend Earth Observation from cryosphere, atmosphere, hydrology, terrestrial systems, geosphere, and soils into long-period climate context without creating a new top-level route family.

## Source registry

1. **NOAA NCEI Climate Data Online** — historical station/location climate observations, summaries, and 30-year Climate Normals. CDO API v2 requires a token and publishes request limits.
2. **Copernicus Climate Change Service ERA5** — global reanalysis from 1940 onward. Reanalysis and preliminary ERA5T remain distinct from direct observations and final processing.
3. **NASA GISTEMP v4** — global, zonal, and gridded surface-temperature anomaly analyses with stated baseline periods and revision history.
4. **WMO Weather & Climate Extremes framework** — source-calculated extreme indices and formally evaluated/certified weather-climate records kept as separate evidence classes.

## Truth boundary

**CLIMATE EVIDENCE · NOT A WEATHER FORECAST, ATTRIBUTION FINDING OR RECORD CERTIFICATION**

- A climate normal is a reference climatology, not a forecast.
- ERA5 is reanalysis, not a direct observation at every grid cell.
- ERA5T preliminary values are not silently represented as final ERA5.
- A GISTEMP anomaly is not an absolute local temperature.
- An anomaly or extreme index does not establish causal attribution.
- A calculated extreme index is not automatically a WMO-certified record.
- Site Intelligence does not certify climate records or issue emergency warnings.
- Empty results do not mean absence of climate risk.

## Public contracts

- `GET /public/climate`
- `GET /public/climate/catalog`
- `GET /public/climate/state`
- `POST /public/climate/measurement/normalize`
- `POST /public/climate/extreme/normalize`
- `POST /public/climate/threshold/preview`
- `GET /public/climate/export-manifest`
- `GET /public/climate/readiness`

The six-primary-area / 35-public-route architecture is preserved.

## Deployment verifier repair

v4.22.0 repairs the long-running v4.21 Render verifier by:

- correcting the inherited geosphere symbol check from the impossible `SCSIGeosphereV42100` to `SCSIGeosphereV42000`;
- printing each Render release-gate poll with observed version, gate state, and commit;
- bounding the default poll count and interval;
- reducing per-request connect/read timeouts;
- printing current-release deep-gate status if the backend version is live but a required contract remains unsatisfied.
