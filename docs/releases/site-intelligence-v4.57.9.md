# Site Intelligence v4.57.9 — Multi-Date Comparison, Scientific Export & Provenance Validation

Frontend-only release over the production-tested v4.57.7 NOAA grid and v4.57.8 cell inspector.

## Capability
- Select a different comparison date; request the second grid independently via existing read-only backend NOAA endpoint.
- Match by exact rounded four-decimal latitude/longitude keys, with identical dataset ID, variable ID and units required.
- Compute signed SST difference (second date minus first) and mean across matched cells only.
- Report unmatched cells separately. No spatial/temporal interpolation, forecast attribution, or imputation.
- Render a separate discrete change display (teal cooling, orange warming) with a numeric summary.
- Download a reproducible JSON evidence package containing the two raw *parsed* grid responses, their upstream source URLs and SHA-256 response receipts, method, query configuration, cell-wise differences, unmatched counts, and provenance assessment.
- Export validation indicates which retrieval receipts are present, and whether geographic coordinates matched across dates. **This is evidence-package completeness validation, not independent certification of NOAA's data or signing a verified attestation**.
- Keep initial NOAA point/chart and ocean data-truth modules intact. No migration, backend change, or new paid service.

## Testing
```bash
cd /opt/sustainable-catalyst/site-intelligence-v4563
PYTHONPATH=. /tmp/scsi-v4575-test/bin/python -m pytest -q tests/test_noaa_grid_v4577.py tests/test_noaa_erddap_v4576.py tests/test_ocean_surface_visualization_v4575.py -o addopts=""
```

## Deployment
Backup and copy just clean checkout `web/index.html` and `web/app/assets/ocean-surface-visualization-v4575.js` into live `/opt/sustainable-catalyst/site-intelligence-web`. Rebuild only `site-intelligence-web`.

## Browser acceptance
Open Ocean Surface. Retrieve first NOAA SST grid at latitude 12, longitude -65, 2026-10-01. Choose another date with source coverage (e.g. 2026-10-02) and click Compare NOAA SST dates. Verify matched cells/deltas, retrieve receipts for **both** dates, difference SVG, and JSON download with both responses; negative-path missing date or unavailable NOAA response must not fabricate values. Browser checks necessary before production certification.

## Known limits
Two NOAA gridded samples are not an independently validated continuous raster; no land mask, no scientific uncertainty quantification, no cryptographic package signature. Response SHA-256 relates to raw upstream bytes, but raw response bodies are not included in JSON; independent rehash verification of NOAA's original response is therefore not possible from the export alone. No temporal causal attribution.
