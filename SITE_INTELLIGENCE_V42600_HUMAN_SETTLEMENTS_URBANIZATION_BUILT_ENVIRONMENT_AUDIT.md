# v4.26.0 Human Settlements / Urbanization / Built Environment Audit

## Source/evidence separation
- GHSL Earth-observation and modeled settlement grids remain distinct from parcel building inventories and zoning.
- WorldPop modeled population surfaces remain distinct from census counts and individual occupancy records.
- NASA Black Marble nighttime radiance remains an optical remote-sensing signal, not an electricity-service, population or economic-output measurement.
- World Bank urban indicators remain harmonized statistical series, not geospatial urban-boundary or local planning determinations.

## Non-inference controls
The release forbids automatic census, occupancy, property, zoning, infrastructure-service, economic-output, emergency-condition and uninhabited-area determinations.

## Release architecture
- Existing six-area / 35-route navigation preserved.
- Backend and WordPress assets are byte-identical.
- v4.12 nested runtime-state exclusion preserved.
- Bounded visible Render verification loop preserved.
