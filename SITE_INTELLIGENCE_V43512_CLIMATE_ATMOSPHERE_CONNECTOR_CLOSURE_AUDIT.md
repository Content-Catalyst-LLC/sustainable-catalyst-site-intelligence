# Site Intelligence v4.35.14 — Climate & Atmosphere Connector Closure Audit

## Purpose
Close the ambiguous machine-interface backlog in the Climate Baselines, Anomalies & Extremes and Atmosphere, Air Quality & Aerosols workspaces without overstating catalogues, model products, preliminary observations, or credential-gated services.

## Climate closure
- NOAA NCEI Access Data Service remains a LIVE bounded retrieval path.
- Copernicus ERA5 is represented through the public CDS STAC catalogue as DISCOVERY.
- ERA5 catalogue discovery is not treated as reanalysis observation retrieval; authenticated CDS data-store execution remains a separate operation.
- Climate REGISTERED machine-interface backlog: 0.

## Atmosphere / Air Quality closure
- EPA AirNow current observations are implemented as AUTH_REQUIRED using `SC_SI_AIRNOW_API_KEY`.
- AirNow current observations are explicitly preliminary / subject to change and are not regulatory AQS records, medical advice, or Site Intelligence-issued advisories.
- EPA AQS remains the quality-assured / regulatory monitoring path and retains its existing credential requirements (`SC_SI_EPA_AQS_EMAIL`, `SC_SI_EPA_AQS_KEY`).
- Copernicus CAMS catalogue access is represented as DISCOVERY. CAMS model, analysis and forecast products are not relabeled as ground-monitor observations or regulatory measurements.
- Atmosphere REGISTERED machine-interface backlog: 0.

## Machine-readable production audit
- Registrations: 106
- LIVE: 43
- DISCOVERY: 10
- AUTH_REQUIRED: 14
- REGISTERED, not retrieved: 35
- BULK: 4
- STALE: 0
- Implemented / discovery / configuration-gated: 67

## Public connector catalogue
- Interfaces: 35
- LIVE: 23
- DISCOVERY: 6
- AUTH_REQUIRED: 6

## Deployment boundary
Connector/readiness and production-readiness checks are deterministic and make no upstream calls. External provider availability is operational source health and is non-blocking for release promotion.
