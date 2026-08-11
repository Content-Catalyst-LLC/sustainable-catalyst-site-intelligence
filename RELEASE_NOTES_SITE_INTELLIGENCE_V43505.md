# Site Intelligence v4.35.5 — Authoritative Connector Expansion III

Site Intelligence v4.35.5 continues the authoritative-data integration branch by adding five more official machine interfaces while preserving v4.35.3.1 deployment/source-health separation.

## Added authoritative interfaces

1. **USFWS National Wetlands Inventory REST** — bounded point/envelope GeoJSON queries against the NWI Wetlands feature layer. NWI inventory polygons are not converted into jurisdictional wetland determinations or proof of absence.
2. **EPA ECHO Facility Web Services** — bounded all-media, Clean Water Act, and RCRA facility-search access. ECHO records remain regulatory/administrative evidence and are not converted into new legal, exposure, compliance, or current-operation findings.
3. **NASA LANCE FIRMS Area API** — bounded active-fire/thermal-anomaly retrieval. This connector remains AUTH_REQUIRED until `SC_SI_NASA_FIRMS_MAP_KEY` is configured server-side.
4. **USDA NASS Quick Stats API** — official aggregate agricultural statistics with a documented `get_counts` preflight before retrieval. This connector remains AUTH_REQUIRED until `SC_SI_USDA_NASS_API_KEY` is configured server-side.
5. **NASA CMR GraphQL** — bounded collection metadata discovery through NASA EOSDIS CMR GraphQL. It remains DISCOVERY because CMR metadata is not itself an underlying scientific observation.

## Public routes

- `/public/authoritative-connectors/usfws-nwi/wetlands`
- `/public/wetlands-inland-water/live/usfws-nwi`
- `/public/authoritative-connectors/epa-echo/facilities`
- `/public/industrial-manufacturing/live/epa-echo`
- `/public/water-sanitation/live/epa-echo`
- `/public/authoritative-connectors/nasa-firms/area`
- `/public/terrestrial-ecosystems/live/nasa-firms`
- `/public/authoritative-connectors/usda-nass/quick-stats`
- `/public/agriculture-food-systems/live/usda-nass`
- `/public/authoritative-connectors/nasa-cmr/graphql/collections`
- `/public/science-discovery/nasa-cmr-graphql`

## Combined connector catalog

The public authoritative connector catalog now exposes **15 interfaces: 11 LIVE, 2 DISCOVERY, and 2 AUTH_REQUIRED**. Credential-gated sources are never reported as LIVE until their required server-side credential exists.

## Audit coverage after v4.35.5

- 179 source registrations
- 120 unique source endpoint/records
- 39 source-bearing workspace inventories
- 96 machine-readable registrations
- 61 implemented/discovery/configuration-gated registrations
- 41 LIVE registrations
- 8 DISCOVERY registrations
- 45 REGISTERED/not-yet-retrieved registrations
- 12 AUTH_REQUIRED registrations
- 4 BULK registrations
- 0 STALE implemented connectors

## Integrity controls

- Missing/null source values remain missing.
- NWI queries require a point or a bounded envelope.
- ECHO queries require a facility/geographic filter and capped response set.
- FIRMS queries require a configured MAP_KEY, an approved source, a bounded area, and a 1–5 day range.
- NASS queries use allowlisted dimensions and `get_counts` preflight; queries matching more than the requested bounded limit are rejected before the data call.
- CMR GraphQL requires at least one bounded discovery filter and never promotes collection metadata to an observation.
- External source health remains non-blocking for release promotion.
