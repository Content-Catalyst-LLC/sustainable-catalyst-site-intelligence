# v4.57.6 — NOAA ERDDAP Verified Observation Retrieval

## Scope
Introduces a bounded read-only backend connector `GET /public/ocean-intelligence/noaa/sst?latitude=12&longitude=-65&date=2026-10-01` using a fixed NOAA ERDDAP griddap dataset `jplMURSST41` and variable `analysed_sst`. This is a first implementation for one grid-point/date; it does not implement automatic multi-date discovery, arbitrary ERDDAP products, remote dataset listing or authoritative source identity attestation.

## Truth boundaries
The endpoint returns `retrieved`, `no_data`, or `unavailable`, with `observation: null` whenever it cannot return a finite value. Returned observations have the requested latitude/longitude, NOAA-returned time, unit conversion when needed, evidence type and raw response SHA-256 receipt. A successful HTTPS response is proof of a network retrieval from the configured host, **not independent scientific verification of the upstream dataset's authenticity, geospatial coverage or quality flags**. NOAA upstream dataset availability has not yet been live-verified during this build; API calls can return `unavailable` and must not substitute guessed values.

## Tests
`PYTHONPATH=. python -m pytest -q tests/test_noaa_erddap_v4576.py tests/test_ocean_surface_visualization_v4575.py -o addopts=""`
These are deterministic mocked-network and static tests, not a live-data certification.

## Deployment
1. Pull clean repository to the VPS; run tests using an isolated Python environment.
2. Back up live backend file `backend/app/main.py` and new connector destination. Copy updated `backend/app/main.py` and `backend/app/noaa_erddap_v4576.py` into the live backend only after comparing local customizations. Rebuild/restart only `site-intelligence` backend compose service. Verify `/public/ocean-intelligence/noaa/sst` and `/health`.
3. Back up live frontend `index.html` and `app/assets/ocean-surface-visualization-v4575.js`; copy changed files, then rebuild `site-intelligence-web`.
4. In Ocean Surface choose NOAA CoastWatch ERDDAP, sea-surface temperature, a past date and an ocean coordinate; click Retrieve NOAA SST observation. Confirm receipt on success, or explicit no-data/unavailable. No chart value should appear on upstream failure.
5. The API remains read-only. No database migration.
