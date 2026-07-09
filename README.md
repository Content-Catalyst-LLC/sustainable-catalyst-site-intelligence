# Sustainable Catalyst Site Intelligence v0.6.0

Site Intelligence is the analytics, search, publishing, public dashboard, and external data intelligence layer for Sustainable Catalyst.

## v0.6.0 Advanced External Data Connectors

This release expands the external data layer beyond the Climate + Energy pilot. It adds connector scaffolding, stable fallback data, cache-aware health checks, and dashboard endpoints for:

- NOAA / National Weather Service climate and weather context
- EIA energy data
- EPA AQS air-quality context
- U.S. Census population/place context
- USGS land-cover context
- GBIF biodiversity occurrence context

## New endpoints

```text
/external/advanced/health
/external/noaa/climate
/external/eia/energy
/external/epa/air-quality
/external/census/context
/external/usgs/land-cover
/external/gbif/biodiversity
/intelligence/dashboards/environmental-monitoring
/intelligence/dashboards/urban-resilience
/intelligence/dashboards/biodiversity-land-use
/intelligence/dashboards/energy-systems
```

## New WordPress shortcodes

```text
[sc_advanced_external_data_health]
[sc_environmental_monitoring_intelligence]
[sc_urban_resilience_intelligence]
[sc_biodiversity_land_use_intelligence]
[sc_energy_systems_intelligence]
```

## Optional environment variables

Most connectors work with fallback/sample context unless credentials are configured. Optional variables:

```text
SC_SI_EIA_API_KEY=
SC_SI_EPA_AQS_EMAIL=
SC_SI_EPA_AQS_KEY=
SC_SI_NOAA_WEATHER_BASE_URL=https://api.weather.gov
SC_SI_EIA_BASE_URL=https://api.eia.gov/v2
SC_SI_EPA_AQS_BASE_URL=https://aqs.epa.gov/data/api
SC_SI_CENSUS_BASE_URL=https://api.census.gov
SC_SI_GBIF_BASE_URL=https://api.gbif.org
```

No new variables are required for deployment. Without optional keys, dashboards remain stable and source-labeled using fallback or registry-context data.
