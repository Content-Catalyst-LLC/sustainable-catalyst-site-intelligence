# Site Intelligence v4.58.0 — Ocean Intelligence Production Consolidation & Certification

## Implemented scope

This is a **consolidation and verifiability release**, not a new dataset release.

1. A unified Ocean Surface scientific workbench title and evidence-readiness indicator now distinguish no-data, one-grid, and two-grid workflows. Existing locator, point retrieval, scientific grid, cell inspector, zoom, date comparison, and JSON export are preserved.
2. Client assets are cache-busted to v4.58.0 in both standalone HTML entrypoints.
3. The new `scripts/certify-ocean-evidence-v4580.py` checks exported evidence packages offline: required retrieval receipts and source URLs, finite SST cell values, coordinate uniqueness, matching coordinates, second-minus-first differences, unmatched counts, and recomputed mean. The checker exits nonzero on failure.
4. `tests/test_ocean_consolidation_v4580.py` includes valid export, forged difference, invalid mean, and invalid receipt tests.

## Limitations and certification terminology

- **Offline package consistency PASS** is not independent NOAA science certification. Source SHA-256 hashes are recorded by the backend but raw upstream NOAA CSV payloads are not currently bundled; thus this tool cannot independently recompute NOAA response hashes.
- Tests must actually pass in a Python environment. Git commits alone do not certify production.
- Cross-browser acceptance, live API testing, service-worker cache validation, and rollback demonstration remain production gates.
- This release does not add coastlines, continuous raster coverage, land masks, alternate NOAA datasets, or scientific uncertainty quantification.

## Local and Contabo tests

```bash
cd /opt/sustainable-catalyst/site-intelligence-v4563
git status --short
git pull --ff-only origin main

PYTHONPATH=. /tmp/scsi-v4575-test/bin/python -m pytest -q \
  tests/test_ocean_consolidation_v4580.py \
  tests/test_noaa_grid_v4577.py \
  tests/test_noaa_erddap_v4576.py \
  tests/test_ocean_surface_visualization_v4575.py \
  -o addopts=""
```

To verify the already exported package:

```bash
python3 scripts/certify-ocean-evidence-v4580.py /path/to/scsi-noaa-sst-evidence-2026-10-01.json
```

## Standalone frontend deployment

After test PASS, back up live `/opt/sustainable-catalyst/site-intelligence-web/index.html` and live `app/assets/ocean-surface-visualization-v4575.js`. Copy those two corresponding files from the clean repository `/opt/sustainable-catalyst/site-intelligence-v4563/web/`. Then run `docker compose up -d --build site-intelligence-web` from the live frontend directory. **Do not replace the live backend main.py** or restart unrelated services. A database migration is not required.

## Browser certification gates

1. Confirm HTML references `ocean-surface-visualization-v4575.js?v=4.58.0` and no script error.
2. Select NOAA SST and retrieve an actual bounded grid: 121 cells were previously observed at latitude 0, longitude 0, date 2026-10-01; retrieval results may vary.
3. Confirm evidence readiness changes from no-grid to one-grid and then two-grid once a different date's data is retrieved.
4. Click a geographic cell and inspect its temperature, coordinates, dataset, and retrieval receipt; zoom in/out/reset.
5. Confirm date-2 matched cells, delta map, export JSON. Check export with `certify-ocean-evidence-v4580.py`.
6. Confirm missing second-date responses fail closed, and changing primary query clears the old grid and comparison.
7. Confirm other Site Intelligence country/earth/map routes still work.

Only after these steps, mark **v4.58.0 production certified for NOAA SST evidence retrieval and comparison**. No broader ocean-science certification is implied.
