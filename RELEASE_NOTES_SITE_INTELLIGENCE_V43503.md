# Site Intelligence v4.35.3 — Authoritative Connector Expansion I

## Purpose

Convert the first high-value set of authoritative source registrations into genuine server-side retrieval clients while preserving the evidence boundaries established by v4.35.2.

## Added authoritative connectors

1. **USGS Water Data OGC API** — latest continuous monitoring observations near a bounded point/bbox; raw values, units, timestamps, monitoring-location IDs, parameter codes, approval status, qualifiers and last-modified metadata remain visible.
2. **NOAA CoastWatch ERDDAP** — public dataset search plus constrained tabledap JSON retrieval. Dataset identifiers, variable names and query constraints are validated before network access.
3. **NASA Exoplanet Archive TAP** — fixed-table ADQL queries against `pscomppars`, returning published planetary and stellar context without converting equilibrium temperature into a habitability claim.
4. **UNHCR Refugee Statistics API** — official periodic aggregate population records with year and ISO3 country-of-origin/country-of-asylum filters.
5. **NASA EOSDIS CMR Search** — collection discovery for Earth/science/space datasets. CMR is classified as **DISCOVERY** because collection metadata is not an observation value.

## Public routes

- `/public/authoritative-connectors`
- `/public/authoritative-connectors/readiness`
- `/public/authoritative-connectors/usgs-water/latest`
- `/public/authoritative-connectors/noaa-erddap/search`
- `/public/authoritative-connectors/noaa-erddap/data`
- `/public/authoritative-connectors/nasa-exoplanets`
- `/public/authoritative-connectors/unhcr-population`
- `/public/authoritative-connectors/nasa-cmr/collections`

Workspace aliases are also provided under Hydrology, Ocean Intelligence, Exoplanet Habitability, Humanitarian Intelligence and Science Discovery.

## Integrity rules

- Missing upstream observations remain missing.
- No connector substitutes zero for `null`.
- USGS provisional/approved state and qualifiers are preserved.
- ERDDAP data retrieval requires a bounded constraint for ordinary datasets.
- Exoplanet archive parameters retain published semantics and units.
- UNHCR population records are explicitly periodic aggregate statistics, not real-time movement tracking or individual legal-status evidence.
- NASA CMR collection metadata is not promoted to an Earth observation.
- Deterministic readiness performs no upstream network calls.

## Configuration

All five connectors have safe official public endpoint defaults. An optional `SC_SI_USGS_WATER_API_KEY` can be configured server-side where higher USGS Water Data rate limits are desired. No public browser payload exposes that key.

ReliefWeb V2 remains separately configuration-gated by `SC_SI_RELIEFWEB_APPNAME`.
