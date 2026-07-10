# Live API Connectors, Caching, and Public Source Status — v1.3.0

Site Intelligence v1.3.0 adds a public-safe connector status layer for API/source families that may support the public dashboard system.

## Public purpose

The connector layer explains whether source families are live-ready, cache-ready, fallback-ready, or planned. It is intended for public source awareness and methodology, not raw operational diagnostics or professional assurance.

## Public endpoints

- `/public/connectors/status`
- `/public/connectors/cache`
- `/public/connectors/freshness`
- `/public/connectors/world-bank`
- `/public/connectors/openalex`
- `/public/connectors/crossref`
- `/public/connectors/github`
- `/public/connectors/environmental`

## WordPress shortcodes

- `[sc_public_connector_status]`
- `[sc_public_cache_status]`
- `[sc_public_source_freshness]`
- `[sc_public_world_bank_connector]`
- `[sc_public_openalex_connector]`
- `[sc_public_crossref_connector]`
- `[sc_public_github_connector]`
- `[sc_public_environmental_connectors]`

## Safety boundary

Public connector panels do not expose API keys, service account JSON, raw upstream payloads, backend logs, private analytics, admin-only diagnostics, or unreleased reports.

## Admin diagnostics

The endpoint `/admin/connectors/diagnostics` provides admin-safe configuration status and connector-readiness summaries. It returns boolean configuration flags only and does not reveal secret values.
