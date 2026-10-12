# Site Intelligence v4.57.7 — NOAA SST Geographic Grid

Backend: bounded GET /public/ocean-intelligence/noaa/sst/grid?latitude=12&longitude=-65&date=2026-10-01. NOAA MUR SST `jplMURSST41` `analysed_sst` source queried with explicit ERDDAP axis strides, 256 KiB response cap, 2500-row cap, observed-unit validation, raw response SHA-256 receipt. Failed and missing data remain missing. No quality assurance beyond source retrieval/shape validation.

Frontend: button under Ocean Surface Geographic & Evidence Visualization retrieves source-backed georeferenced cells, renders discrete colored rects (not an interpolated raster), and labels min/max values and provenance. Old standalone locator remains explicitly illustrative. Point SST retrieval and data truth panels remain unchanged.

Tests: `PYTHONPATH=. /tmp/scsi-v4575-test/bin/python -m pytest -q tests/test_noaa_grid_v4577.py tests/test_noaa_erddap_v4576.py tests/test_ocean_surface_visualization_v4575.py -o addopts=""`

Deploy backend first; protect live customizations in `backend/app/main.py`, copying only the new route from clean GitHub source and `backend/app/noaa_grid_v4577.py`. Restart backend compose service `site-intelligence`; verify health and actual grid API JSON. Deploy updated `web/index.html` and `web/app/assets/ocean-surface-visualization-v4575.js` to live standalone frontend and rebuild only `site-intelligence-web`. Test from Chrome after selecting NOAA SST, October 1 2026, 12,-65 and clicking **Retrieve NOAA SST geographic grid**.

Live NOAA grid response has NOT been validated for this release. Do not certify the visualization until real cells with NOAA receipt render. In particular test upstream ERDDAP stride constraints against actual service and ensure source coverage. No database migration.
