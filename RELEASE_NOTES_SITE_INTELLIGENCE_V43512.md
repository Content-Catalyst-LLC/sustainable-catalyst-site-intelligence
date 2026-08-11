# Site Intelligence v4.35.12 — High-Priority Workspace Connector Closure II: Climate & Atmosphere

v4.35.12 continues the workspace-by-workspace “simply works” closure program by eliminating ambiguous REGISTERED machine-interface gaps in Climate and Atmosphere/Air Quality.

## Added
- EPA AirNow current-observation connector with explicit API-key configuration and credential redaction.
- Copernicus CDS / ERA5 public STAC catalogue discovery.
- Copernicus ADS / CAMS public STAC catalogue discovery.
- Climate and Atmosphere closure accounting in the production audit and closure ledger.
- Render configuration slot for `SC_SI_AIRNOW_API_KEY`.
- Six public API/workspace routes for AirNow, ERA5 and CAMS.

## Evidence semantics
- AirNow is preliminary current public-reporting/forecasting data; it is not a regulatory AQS determination.
- EPA AQS remains distinct quality-assured/regulatory monitoring evidence.
- ERA5 is reanalysis; catalogue discovery is not direct observation retrieval.
- CAMS is modeled/analysis/forecast evidence; catalogue discovery is not a ground-monitor measurement.
- Missing or unavailable source values remain missing.
- External upstream health remains non-blocking for deployment.

## Coverage
Machine-readable registrations: 106; LIVE: 43; DISCOVERY: 10; AUTH_REQUIRED: 14; REGISTERED/not retrieved: 35; BULK: 4; STALE: 0.

Public connector catalogue: 35 interfaces — 23 LIVE, 6 DISCOVERY, 6 AUTH_REQUIRED.

Climate REGISTERED backlog: 0. Atmosphere REGISTERED backlog: 0.

## Validation
Complete deterministic suite: 1,527 tests. Release-specific regressions: 12. Final manifest/static/security/browser results are recorded in `SITE_INTELLIGENCE_V43512_BUILD_VALIDATION.txt`.
