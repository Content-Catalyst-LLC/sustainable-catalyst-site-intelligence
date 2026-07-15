# Sustainable Catalyst Site Intelligence v2.4.0

## Scientific and Earth Systems Observatory

Site Intelligence v2.4.0 adds a dedicated public scientific-data workspace connected to the scientific records and geospatial, time-series, asset, map-layer, and STAC capabilities provided by Sustainable Catalyst Core v2.7.2 and v2.8.0.

## Public workspace

`/app/?view=science`

The workspace provides:

- Scientific record discovery across Earth systems, atmosphere, ocean, hazards, astronomy, biology, chemistry, biodiversity, and materials science
- Record-type, discipline, source, mission, domain, keyword, and asset-format filtering
- Mission, instrument, collection, target, dataset, variable, quality, observation-date, license, and attribution context
- Geographic visualization of public scientific records and STAC items
- Remote scientific asset and map-layer discovery
- STAC catalog search
- Scientific time-series selection and charting
- Source-aware CSV export
- Shareable filter state and Saved View integration
- Workbench handoff
- Explicit connected, degraded, disabled, unavailable, and stale states

## Public endpoints

- `GET /public/scientific-earth-systems`
- `GET /public/scientific-earth-systems/records`
- `GET /public/scientific-earth-systems/facets`
- `GET /public/scientific-earth-systems/assets`
- `GET /public/scientific-earth-systems/map-layers`
- `GET /public/scientific-earth-systems/stac`
- `GET /public/scientific-earth-systems/timeseries`
- `GET /public/scientific-earth-systems/timeseries/{series_id}/points`
- `GET /public/scientific-earth-systems/brief`
- `GET /public/scientific-earth-systems/diagnostics`

## WordPress shortcode

`[sc_scientific_earth_systems_observatory height="1400"]`

## Scientific integrity boundaries

The observatory does not treat metadata discovery as peer review or scientific validation. It preserves the distinction between observations, forecasts, catalogs, computed records, telescope products, materials records, and other scientific record types.

The release also states that:

- Forecasts are not observations.
- Remote-sensing products may require ground validation and domain interpretation.
- Computed material properties are not automatically experimental findings.
- Biomedical records are not patient-specific medical advice.
- No scientific records are fabricated when Core is unavailable.
- No paid data provider is required.

## Configuration

- `SC_SI_PLATFORM_CORE_ENABLED=true`
- `SC_SI_PLATFORM_CORE_URL=https://YOUR-CORE-SERVICE.onrender.com`
- `SC_SI_PLATFORM_CORE_PUBLIC_API_KEY=<set securely in Render>`
- `SC_SI_SCIENTIFIC_EARTH_SYSTEMS_ENABLED=true`
- `SC_SI_SCIENTIFIC_EARTH_SYSTEMS_TIMEOUT_SECONDS=9`
- `SC_SI_SCIENTIFIC_EARTH_SYSTEMS_CACHE_TTL_SECONDS=120`

## Validation

- 345 backend tests passed
- Release contract passed
- Python compilation passed
- JavaScript syntax passed
- WordPress PHP syntax passed
- Bash syntax passed
- JSON and YAML validation passed
- Public route smoke tests passed
- 367 HTML IDs checked with no duplicates
- Push-safe secret scan passed
- Repository and WordPress ZIP integrity passed
- Clean-room manifest and installer validation completed
