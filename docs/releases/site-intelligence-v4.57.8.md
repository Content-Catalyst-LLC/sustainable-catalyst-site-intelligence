# Site Intelligence v4.57.8 — Interactive NOAA Spatial Evidence Exploration

**Scope:** frontend-only improvement over the production-tested v4.57.7 NOAA SST grid. Existing backend `/public/ocean-intelligence/noaa/sst/grid` and single-point retrieval are unchanged.

- NOAA grid records render as discrete selectable SVG cells, with keyboard Enter/Space access and tooltips.
- Selected cell details expose sea-surface temperature (°C), latitude, longitude, NOAA dataset/variable ID, observation query date and response SHA-256 receipt.
- Temperature legend shows five source-sample-derived numerical color ticks and specifies °C.
- Zoom in/out/reset operates on the source grid; not a pan-enabled cartographic map and not a satellite raster.
- Prior schematic latitude/longitude locator moved into a collapsed disclosure so real retrieved data is more prominent.
- Changing a query control clears the previously loaded grid and selected cell; missing measurements remain unfilled.
- A NOAA grid remains an approximately one-degree sampled subset; this build does **not** establish a coastline basemap, land mask, area-wide ocean coverage, spatial interpolation, independent scientific quality validation or map panning.

## Regression
Run:
```bash
cd /opt/sustainable-catalyst/site-intelligence-v4563
PYTHONPATH=. /tmp/scsi-v4575-test/bin/python -m pytest -q tests/test_noaa_grid_v4577.py tests/test_noaa_erddap_v4576.py tests/test_ocean_surface_visualization_v4575.py -o addopts=""
```
These are static and mocked backend tests; browser acceptance is required.

## Deployment
Only copy the clean checkout's `web/index.html` and `web/app/assets/ocean-surface-visualization-v4575.js` into the **live** `/opt/sustainable-catalyst/site-intelligence-web`, after backing both up. Rebuild the existing `site-intelligence-web` compose service. Do not replace the production backend or the live WordPress integration.

## Acceptance
Open `https://intelligence.sustainablecatalyst.com/?view=earth&country=DEU&oceanMode=hub&oceanSystem=surface`; choose NOAA ERDDAP, SST, 2026-10-01, latitude 12, longitude -65; click **Retrieve NOAA SST geographic grid**. Verify nonempty source-backed cells, select a cell, confirm numerical value, coordinates, NOAA dataset and receipt, use zoom/reset and inspect the numeric °C legend. The orientation locator should be initially collapsed. Keep a failed/missing upstream query explicitly empty.
