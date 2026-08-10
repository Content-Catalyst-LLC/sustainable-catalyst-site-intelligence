# Site Intelligence v4.13.0 — Global Ocean Intelligence & Surface Conditions

Ocean Surface extends the existing Earth Observation route without creating a 36th public route. The consolidated v4 platform remains six primary areas and 35 routes.

## Added
- NOAA CoastWatch/OceanWatch ERDDAP, U.S. IOOS, and Copernicus Marine source contracts.
- Nine initial surface variables: sea-surface temperature, chlorophyll-a, sea-surface height, sea-surface salinity, surface currents, surface wind, significant wave height, sea-ice concentration, and SST anomaly.
- Source/date/point query planning that returns no synthetic surface value and makes no coverage claim without a record.
- Evidence-class separation across in-situ observations, satellite-derived products, analysis, reanalysis, models, forecasts, and derived products.
- Source-attributed record normalization with recognized-source validation and explicit non-verification status for locally supplied records.
- SHA-256 evidence manifests for selected ocean state and source context.
- Deferred Ocean Surface browser shell for direct and WordPress-iframe operation while preserving the inherited first-load HTML budget.
- Independent live-deployment checks for Ocean overview, catalog, readiness, and shipped v4.5 browser asset.

## Scientific boundaries
- Global source eligibility is not verified spatial or temporal coverage.
- IOOS remains U.S. coastal/regional rather than a global source claim.
- Copernicus credentials are never embedded in public browser state, fixtures, or evidence manifests.
- Missing ocean data remains missing and is not converted to zero or silently replaced by another source.
- Forecast, model, reanalysis, analysis, satellite-derived, and in-situ records are not presented as interchangeable observations.
