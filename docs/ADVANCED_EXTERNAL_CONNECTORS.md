# Advanced External Data Connectors

Site Intelligence v0.6.0 adds the advanced external data connector layer for environmental monitoring, urban resilience, biodiversity/land use, and energy systems dashboards.

The connectors are designed to degrade safely. Optional API keys unlock more live data, but dashboards continue to return source-labeled fallback or registry-context outputs when keys are not configured.

## Optional credentials

- `SC_SI_EIA_API_KEY` for EIA Open Data.
- `SC_SI_EPA_AQS_EMAIL` and `SC_SI_EPA_AQS_KEY` for EPA AQS.

NOAA/NWS, Census, and GBIF can operate without keys. USGS land-cover is a registry/context connector in v0.6.0 and should be expanded with raster/STAC/tile services in a later build.
