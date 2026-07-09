# External Data Connectors

Site Intelligence v0.2.1 adds an external data layer for climate, energy, emissions, Earth observation, and environmental monitoring dashboards.

## Connectors

### NASA POWER

Used for location-based solar and meteorological time-series indicators:

- mean 2m temperature
- maximum/minimum 2m temperature
- precipitation
- 10m wind speed
- all-sky surface solar irradiance

### NASA GIBS

Used for Earth observation layer metadata and future map dashboards. The connector reads WMTS capabilities and classifies layers into categories such as Earth observation, heat, hydrology, and air quality.

### Climate TRACE

Used for emissions intelligence. The public API is treated as beta/unstable, so the connector has schema-tolerant parsing and fallback behavior.

## Endpoints

```text
/external/connectors
/external/health
/external/nasa-power/timeseries
/external/nasa-gibs/layers
/external/climate-trace/emissions
/intelligence/dashboards/climate-energy
```

## Public dashboard direction

This version is a pilot. Use the dashboard privately first. Once connector health and interpretations are stable, these can become the foundation for:

- Climate Change Map Intelligence
- Energy Systems Data Intelligence
- Environmental Monitoring Intelligence
- NASA Earth Observation Intelligence
- Urban Resilience Dashboard
- Biodiversity / Land Use Dashboard
