# Site Intelligence v4.18.0 — Hydrology / Rivers / Flood / Drought Audit

## Registered source contracts

1. USGS Water Data APIs — https://api.waterdata.usgs.gov/
2. NASA GPM IMERG — https://gpm.nasa.gov/data/imerg
3. Copernicus GloFAS / Global Flood Monitoring — https://global-flood.emergency.copernicus.eu/
4. NOAA/NIDIS Drought.gov — https://www.drought.gov/data-download

## Evidence classes

- in-situ observation
- daily statistic
- satellite estimate
- near-real-time satellite estimate
- model analysis
- forecast
- reanalysis
- drought index
- source-issued category

## Truth and safety findings

- Satellite-estimated precipitation is never converted into a rain-gauge observation.
- Modeled GloFAS discharge is never converted into a USGS gauge observation.
- Forecasts remain forecasts and reanalyses remain reanalyses.
- Near-real-time product maturity is retained and is not silently upgraded to final.
- Flood thresholds and return-period context do not create a Sustainable Catalyst flood warning.
- Drought indices do not create a Sustainable Catalyst drought declaration or emergency determination.
- Zero returned records do not establish absence of flood, drought, precipitation, or streamflow conditions.
- Source URLs are HTTPS allow-listed to the registered source families.
- No API key or credential is embedded in public state, fixtures, browser assets, exports, or the repository.

## Architecture finding

v4.18.0 remains additive inside Earth Observation. Primary areas: 6. Preserved public routes: 35. Public-route delta: 0.
