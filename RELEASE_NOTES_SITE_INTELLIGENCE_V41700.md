# Site Intelligence v4.17.0 — Global Atmosphere, Air Quality & Aerosol Intelligence

## Release purpose

v4.17.0 extends the Earth Observation environment from cryosphere evidence into atmospheric composition and air-quality orientation without adding a new top-level public route family. The established six primary areas and 35 public routes remain unchanged.

## Source families

- EPA AirNow API — current/preliminary observations, AQI and source-issued forecasts. Public API access requires registration/API key. AirNow data remain preliminary and are not substituted for validated AQS regulatory records.
- U.S. EPA Air Quality System (AQS) — ambient monitoring, station metadata and quality-assurance/regulatory-network records. AQS is not a real-time service.
- Copernicus Atmosphere Monitoring Service (CAMS) — global atmospheric-composition analyses and forecasts for gases, particulate matter and aerosol species.
- NASA Earthdata / LANCE aerosol products — satellite-derived aerosol evidence, including near-real-time products and aerosol optical depth.

## Evidence boundary

**ATMOSPHERIC EVIDENCE · NOT A HEALTH, REGULATORY OR EMERGENCY DETERMINATION**

The platform does not treat AirNow preliminary observations as validated regulatory data; forecasts or model analyses as observations; aerosol optical depth as surface PM2.5; a threshold comparison as a regulatory exceedance; an empty query as clean air; or a source-issued AQI/forecast/advisory as a Sustainable Catalyst health or emergency warning.

## Public contracts

- `GET /public/atmosphere`
- `GET /public/atmosphere/catalog`
- `GET /public/atmosphere/state`
- `POST /public/atmosphere/measurement/normalize`
- `POST /public/atmosphere/forecast/normalize`
- `POST /public/atmosphere/threshold/preview`
- `GET /public/atmosphere/export-manifest`
- `GET /public/atmosphere/readiness`

## Interface integration

The atmosphere environment is deferred from the v4.16 cryosphere panel. It adds no new top-level application route. Browser assets are mirrored byte-for-byte between the FastAPI public app and the WordPress plugin.

## Release gates

The v4.17 live promotion verifier independently requires the atmosphere overview, four-source catalog, bounded AirNow state, readiness contract and shipped `atmosphere-v41700.js` asset in addition to all inherited production gates.

Production deployment is not performed by the build environment. Install the WordPress ZIP only after the macOS installer verifies the exact GitHub/Render v4.17.0 live gate.
