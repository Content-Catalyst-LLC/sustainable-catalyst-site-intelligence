# Site Intelligence v3.25.0 Unified Analytical State Audit

## Scope

This release introduces one normalized state model across six analytical routes:

1. Overview
2. Global Conditions
3. Country Intelligence
4. Compare
5. Spatial Evidence
6. Earth Observation

## Shared state

The contract can preserve primary country, comparison country, indicator, imagery layer and date, spatial area and dataset, Earth-observation layer and dates, event period, and map categories. Canonical links include only the parameters relevant to the destination route.

## Validation findings

- The backend country catalog exposed at least 170 supported ISO3 country codes.
- Invalid routes and countries were replaced with disclosed defaults.
- A comparison country matching the primary country was replaced with a distinct supported country.
- Reversed Earth-observation dates were normalized chronologically.
- Equivalent normalized states produced the same SHA-256 fingerprint.
- Browser tests retained Brazil while moving from Compare to Earth Observation in direct and iframe modes.
- Existing 173-country dropdown, record provenance, control-plane, service-worker, route-soak, and fixed WordPress embed contracts remained operational.

## Boundaries

The state fingerprint detects changes to normalized interface selections. It is not a source checksum, evidence certification, or proof that data exists for the selected country and route.
