# Site Intelligence v1.18.3 — Global Country Reliability, Data Coverage, and Release Integrity

## Purpose

v1.18.3 stabilizes the global country product introduced in v1.18.0 and locks backend, WordPress, tests, and public metadata to one release identity.

## Release integrity

The canonical release value is defined in `backend/app/version.py`.

Public compatibility endpoint:

`/public/build-info`

The WordPress plugin checks this endpoint from the administrator interface and displays a warning when the backend and plugin versions differ.

## Catalog normalization

Source records are not rewritten. Public output adds:

- `name` / `display_name`
- `source_name`
- `alternate_names`
- normalized `region`
- `source_region`
- `entity_type`

This lets the interface display familiar country names while preserving the original provider terminology.

## Cache architecture

The country layer uses an in-memory plus JSON last-known-good cache. Writes are atomic: data is written to a temporary file and then moved into place.

The JSON cache is best-effort on Render's ephemeral filesystem. It is not a substitute for durable funded persistence, but it improves continuity without Redis, PostgreSQL, or another paid service.

## Indicator states

- `live`
- `partial-live`
- `cached`
- `stale`
- `reference-snapshot`
- `unavailable`

Every available indicator retains value, unit, reporting year, source, source ID, source URL, retrieval time, cache state, and stale state.

## Frontend request safety

The standalone app cancels superseded requests with `AbortController`, rejects stale response sequences, times out slow requests, debounces search, clears previous-country output before loading, and guarantees only one country marker remains on the overview map.

## Event matching

Country-linked events retain:

- `country_code`
- `country_match_method`
- `country_match_confidence`
- `country_match_evidence`

The application does not present a country match without retaining the basis for that match.

## Diagnostics

- `/public/countries/diagnostics`
- `/public/country/{ISO3}/diagnostics`

Diagnostics are public-safe and do not expose credentials, private URLs, stack traces, or raw internal queues.

## Validation

- 199 backend tests pass
- Python compilation passes
- standalone JavaScript syntax check passes
- WordPress PHP syntax check passes
- archive and secret scans are part of release packaging
