# Site Intelligence v4.17.0 — Atmosphere, Air Quality & Aerosol Audit

## Architecture

- Primary areas: unchanged (6)
- Public route architecture: unchanged (35)
- New capability location: Earth Observation deferred environment
- Predecessor environment: v4.16.0 Cryosphere

## Registered source families

### EPA AirNow
Purpose: current/preliminary AQI, observations and forecasts.
Truth constraints: preliminary; source forecasts/advisories remain source-issued; not a regulatory archive; no platform health advisory is generated.

### EPA AQS
Purpose: ambient regulatory-monitoring records, station metadata and QA information.
Truth constraints: not real-time; monitor purpose, method, certification and aggregation remain source metadata; no platform regulatory exceedance finding.

### CAMS Global Atmospheric Composition
Purpose: globally complete analyses and forecasts for atmospheric composition and aerosols.
Truth constraints: model/data-assimilation evidence remains distinct from ground observations; forecast remains forecast.

### NASA Earthdata / LANCE Aerosol
Purpose: satellite-derived aerosol loading and related near-real-time products.
Truth constraints: AOD is column aerosol loading and is not silently converted to surface PM2.5; retrieval quality, cloud screening, resolution and product maturity remain visible.

## Indicator registry

AQI; PM2.5; PM10; ozone; nitrogen dioxide; sulfur dioxide; carbon monoxide; lead; aerosol optical depth; dust aerosol; smoke aerosol; black carbon.

## Evidence classes

Preliminary observation; quality-assured observation; regulatory monitor; forecast; model analysis; satellite-derived; near-real-time satellite.

## Safety and truth assertions

- AirNow preliminary = regulatory data: false
- Forecast = observation: false
- Model analysis = observation: false
- AOD = surface PM2.5: false
- Zero records = clean air: false
- Threshold comparison = regulatory exceedance: false
- Platform health advisory issued: false
- Platform emergency warning issued: false
- Automatic action authorized: false

## Credential boundary

AirNow and AQS programmatic services may require free registration/API credentials. Credentials are not embedded in browser state, repository fixtures, exports, WordPress assets or the immutable release package.
