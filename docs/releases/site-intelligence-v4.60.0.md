# Site Intelligence v4.60.0 — Chlorophyll & Ocean Biology Intelligence

## Delivered
- NOAA OceanWatch PIFSC S-NPP monthly chlorophyll-a adapter. Official dataset ID `noaa_snpp_chla_monthly`, field `chlor_a`, satellite-derived ocean color, units mg/m3. Monthly composite timestamps are preserved and verified against the selected calendar month. Dataset description: https://oceanwatch.pifsc.noaa.gov/erddap/griddap/noaa_snpp_chla_monthly.html
- Bounded 1° regional query, read-only upstream CSV, source-side spatial stride, max 256 KiB / 2500 records, invalid/missing handling, SHA256 response receipt.
- `GET /public/ocean-intelligence/noaa/chlorophyll/grid?latitude=12&longitude=-65&date=2026-09-01`.
- Expandable independent ocean-biology workbench panel with source-backed cells, log-scaled color rendering, hover evidence, and JSON export. No synthetic observations or claims of organism counts.
- Source registered in v4.59.0 registry as `integration-pending` (not live-verified) until live upstream verification. The live-verified NOAA SST source remains unchanged.
- Regression tests for mocked observations, wrong-month rejection, registry truth and frontend assets.

## Safe deployment
Do not overwrite customized live backend main.py. After pulling the clean repository and passing tests, copy only the new `backend/app/chlorophyll_v4600.py` and updated `backend/app/ocean_contracts_v4590.py` into live backend. Back up live main.py and insert exact route code from this release in the clean GitHub main.py before the existing `from .ocean_contracts_v4590 import registry as ocean_variable_registry` anchor. Compile, rebuild only backend service, verify API with a month known to exist upstream. Then copy the new JS asset and updated frontend index.html into live static frontend, rebuild only frontend container. No DB migration.

## Certification gates
1. Tests PASS and backend syntax PASS.
2. Existing NOAA SST grid still retrieves.
3. New chlorophyll endpoint returns `ok: true` with nonzero measured cells for an actual available month, valid `chlor_a` units and response SHA-256 receipt. Upstream may reject dates or have missing records; report as unavailable rather than asserting success.
4. Browser renders measured cells and exports JSON with receipt, correct month and `mg/m3`.
5. Ocean registry chlorophyll source can be promoted from `integration-pending` to `live-verified` in a later change only after successful upstream validation.
6. Country and Earth routes remain functional.

Scientific caution: chlorophyll-a is a satellite ocean-color proxy for phytoplankton biomass, not a directly observed ecological productivity or causal explanation. Monthly composite timestamps are not daily measurements.
