# Site Intelligence v4.35.4 — Authoritative Connector Expansion II

Site Intelligence v4.35.4 continues the authoritative-data integration branch by turning five additional public machine interfaces into bounded, provenance-preserving server-side connectors while retaining the v4.35.3.1 release-gate hardening.

## Added authoritative connectors

1. **NOAA CO-OPS Data API** — station observations and predictions for supported coastal/tide/current/meteorological products. Explicit date ranges are capped at 31 days; datum, units, time zone, source metadata and source quality/error fields remain visible.
2. **NOAA NCEI Access Data Service** — bounded dataset/date/station/datatype retrieval through the public Access Data service. Requests are capped to 366 days and remain distinct from the token-gated Climate Data Online v2 API.
3. **IOC-UNESCO OBIS API v3** — marine-biodiversity occurrence retrieval using scientific-name, AphiaID, geometry and/or date filters. Occurrence evidence is not converted into abundance, census or absence claims.
4. **Eurostat Statistics API** — bounded dataset/dimension retrieval with JSON-stat metadata, dimensions, units, time and status preserved.
5. **USDA-NRCS Soil Data Access** — bounded SSURGO map-unit retrieval using fixed query templates. Arbitrary user SQL is not accepted; map-unit records remain generalized soil-survey evidence rather than parcel/site-specific engineering determinations.

## Public routes

- `/public/authoritative-connectors/noaa-coops/data`
- `/public/coastal-change/live/noaa-coops`
- `/public/authoritative-connectors/noaa-ncei/data`
- `/public/climate/live/noaa-ncei`
- `/public/authoritative-connectors/obis/occurrences`
- `/public/biodiversity/live/obis`
- `/public/authoritative-connectors/eurostat/statistics`
- `/public/solid-waste-circular-materials/live/eurostat`
- `/public/authoritative-connectors/usda-soils/mapunits`
- `/public/soils-land/live/usda-nrcs`

The combined `/public/authoritative-connectors` catalog now exposes ten Expansion I + II interfaces: nine LIVE retrieval interfaces and one NASA CMR DISCOVERY interface.

## Audit precision repair

v4.35.4 makes NOAA NCEI classification interface-specific. A live NCEI Access Data Service client no longer causes unrelated NCEI catalog/product pages on the same host to be labeled LIVE.

The current audit reports:

- 179 source registrations
- 120 unique source endpoint/records
- 39 source-bearing workspace inventories
- 96 machine-readable registrations
- 56 implemented/discovery/configuration-gated registrations
- 38 LIVE registrations
- 8 DISCOVERY registrations
- 50 REGISTERED machine-readable/source registrations not yet retrieved
- 10 AUTH_REQUIRED registrations
- 4 BULK registrations
- 0 STALE implemented connectors
- 69 UNAVAILABLE/non-machine-live registrations under the current audit taxonomy

## Release-gate preservation

The v4.35.3.1 production reliability contract remains intact. GitHub/Render promotion depends on release identity, expected commit, first-party health/runtime, the 35-route structural contract, connector-router readiness and packaged app assets. External source health remains non-blocking and is reported separately by `/public/source-health-policy`.

## Evidence boundaries

- Missing upstream values remain missing and are never silently converted to zero.
- Source records retain raw values and available quality/status metadata.
- Zero occurrence/search results do not establish absence.
- Predictions remain distinct from observations.
- Statistical series retain source dimensions, units, geography and time semantics.
- Soil survey records are not parcel boundaries or site-specific engineering findings.
- The connector layer does not proxy arbitrary upstream URLs, arbitrary SQL, or unbounded data requests.
