# Site Intelligence v4.35.24 — Palestine-First Country Navigation Integrity Repair

v4.35.24 repairs the remaining Palestine/Israel navigation defect that survived v4.35.23. The earlier release protected identity inside the dedicated Country workspace, but the top-level Overview selector still used a legacy path and both frontend/backend catalog merge order could allow live metadata to overwrite first-party identity-bearing fields.

## What changed

- Made the first-party country registry authoritative for ISO3, ISO2, display name, canonical coordinates, capital/entity identity, and other identity-bearing fields.
- External country catalogs may enrich non-identity metadata but cannot overwrite `PSE / PS / Palestine` or `ISR / IL / Israel`.
- Repaired the Overview `loadCountry()` path: it commits the selected ISO3 and focuses the map from canonical coordinates before any external evidence request finishes.
- Added a hard cross-identity response guard to the Overview path. An `ISR` request cannot render a `PSE` response and vice versa.
- Repaired the cartographic workspace merge order so delayed live catalog hydration cannot move the map from the selected canonical country.
- Added a hostile-catalog browser regression that deliberately swaps Palestine and Israel in simulated external metadata and verifies the UI still lands on the selected canonical country.
- Added `/public/country-navigation-integrity/readiness` to deployment verification. It is network-free and external-provider health remains non-blocking.

## Identity policy

- `PSE -> PS -> Palestine`
- `ISR -> IL -> Israel`
- external metadata: enrichment only
- cross-identity response: blocked

The repair does not relabel Israel as Palestine or merge the two identities. It removes the exception by making both resolve independently through the same canonical mechanism.

## Validation

- 1,650/1,650 deterministic tests passed.
- Hostile Palestine/Israel Overview browser regression passed.
- 35/35 desktop, 35/35 mobile, and 35/35 iframe workspace routes ready with zero degraded routes.
- Application HTML 171,981/172,000 bytes; CSS 101,860/102,000 bytes; HTML+CSS+application JS 488,948/500,000 bytes.
