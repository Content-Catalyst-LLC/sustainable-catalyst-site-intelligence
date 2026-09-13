# Site Intelligence v4.41.0 — Spatial & Global Energy Intelligence

This feature release is rebased on the production v4.40.0.3 source line so the
Live Intelligence ticker pace/readability repair and all current Site
Intelligence capabilities are preserved.

## Energy Systems v1.5.0

New routes:

- `GET /v1/energy-spatial/framework`
- `GET /v1/energy-spatial/source-registry`
- `POST /v1/energy-spatial/profile`
- `POST /v1/energy-spatial/compare`
- `POST /v1/energy-spatial/validate-result`

The runtime builds provenance-bound geographic energy profiles from explicit
records. It summarizes exact-unit observations, source coverage, time coverage,
geographic extent, and optional focus-point distances. Cross-geography
comparison remains neutral and does not produce a technology/site ranking.

## Release-bound compatibility state

The same 27 immutable policy/registry compatibility files already reconciled
through v4.40.0.3 advance to v4.41.0. Historical filenames, schemas,
`release_id` values, and origin metadata are retained.

## Boundaries

The release does not infer site suitability, renewable technical potential,
grid reliability, outage status, current-year status, causal attribution,
technology ranking, a preferred site, or a recommendation. The new analysis
routes do not silently fetch or persist external data.
