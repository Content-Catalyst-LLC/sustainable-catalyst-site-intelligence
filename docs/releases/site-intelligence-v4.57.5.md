# Site Intelligence v4.57.5 — Ocean Surface Visualization & Scientific Data Rendering

## Delivered
- Geographic latitude/longitude SVG locator, explicitly labelled as not a measured ocean raster.
- Source-attributed observation SVG plotting and JSON import (1–100 records); backend validates records through `POST /public/ocean-intelligence/observation/normalize`.
- No line interpolation across evidence classes or claim of automatic retrieval. Plot markers show original observation metadata on hover.
- Source/variable filtering and missing-data messages.
- Works within existing Ocean Surface panel, standalone frontend and Earth/Ocean router. No production backend migration.

## Scientific truth boundaries
- Current backend provides source catalog/query plan and registration-based record normalization; **it does not fetch NOAA, IOOS, or Copernicus measurements automatically**.
- Normalization verifies registered source host/evidence class and input shape, **not** source-document authenticity or live network retrieval.
- Imported records may be attributed but are not independently verified. Public ocean observations must not be inferred from a locator, source registration, or empty plot.
- Next backend milestone: dataset-specific verified retrieval receipts for NOAA ERDDAP, source products, observation times, units, flags, spatial/temporal coverage and forecasts.

## Deploy
In clean VPS GitHub checkout, pull current main. Run `python3 -m pytest -q tests/test_ocean_surface_visualization_v4575.py -o addopts=""` if pytest is installed; then optionally `node --check web/app/assets/ocean-surface-visualization-v4575.js` if Node.js is available.

Back up `site-intelligence-web/index.html` and copy updated `web/index.html` plus new `web/app/assets/ocean-surface-visualization-v4575.js` to live frontend; rebuild only `site-intelligence-web`. Do not overwrite backend or other local frontend assets.

## Browser acceptance
Visit `/?view=earth&country=DEU&oceanMode=hub&oceanSystem=surface`. Confirm `#ocean4575Map svg` exists, `#ocean4575Chart` says no observation records initially, and import accepted records from an independently reviewed source. Confirm no values are fabricated from coordinates alone.
