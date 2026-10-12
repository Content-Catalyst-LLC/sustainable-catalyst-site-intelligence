# Site Intelligence v4.59.0 — Multi-Variable Ocean Intelligence Foundation

## Delivered
- Backend `backend/app/ocean_contracts_v4590.py` contains seven ocean-science variable definitions, canonical units, scalar/vector geometry, and explicit live/declared availability.
- Only existing NOAA MUR SST `jplMURSST41/analysed_sst` has a verified retrieval adapter. Six other variables are **not connected** (the foundation introduces no fabricated sources, observations, or capabilities).
- Normalized scalar observation contract enforces explicit units, declared source/variable relationship, finite coordinates and values, timezone-aware observation time, source-matching evidence classification, and source response receipt. Vector records cannot be coerced into scalar observations.
- Read-only FastAPI `GET /public/ocean-intelligence/variables/registry`.
- Additive frontend `ocean-variable-registry-v4590.js` adds an optional expandable registry panel without replacing existing NOAA SST grid, comparison or export.
- No migrations and no new paid services.

## Tests
```bash
cd /opt/sustainable-catalyst/site-intelligence-v4563
PYTHONPATH=. /tmp/scsi-v4575-test/bin/python -m pytest -q \
  tests/test_ocean_contracts_v4590.py \
  tests/test_ocean_consolidation_v4580.py \
  tests/test_noaa_grid_v4577.py \
  tests/test_noaa_erddap_v4576.py \
  tests/test_ocean_surface_visualization_v4575.py -o addopts=""
```

## Safe backend deployment
The live backend has local customizations. **Do not copy or replace its entire main.py**. Back up the live main.py, copy only `backend/app/ocean_contracts_v4590.py` from the clean repository, and insert the read-only route before the unique existing `from .noaa_grid_v4577 import retrieve_grid as retrieve_noaa_sst_grid` anchor. Compile then rebuild **only** `site-intelligence`; verify the public registry reports seven variables, one live and six unconnected, and verify existing SST grid API remains healthy.

## Frontend deployment
Back up live `index.html`; copy clean `web/index.html` and the new `web/app/assets/ocean-variable-registry-v4590.js` into live frontend, rebuild only `site-intelligence-web`. Verify asset HTTP 200 and that registry details open on Ocean Surface.

## Production acceptance
- Registry endpoint HTTP 200, correct schema, statuses and source ID
- Frontend panel visible with accurate status and no console errors
- NOAA primary grid retrieval and multi-date comparisons retain functionality
- Exported old v4.58.0 packages still pass `scripts/certify-ocean-evidence-v4580.py`
- Missing/unknown source observations refused
- Country and Earth routes remain functional

Commit does not establish test or live deployment success. No scientific quality certification is claimed for external observations.
