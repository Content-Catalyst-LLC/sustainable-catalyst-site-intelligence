# Site Intelligence v1.6.1 Connector Reliability

This release adds bounded retries, exponential backoff, circuit breakers, rate-limit metadata, response-schema checks, stale-while-revalidate cache behavior, last-known-good fallbacks, explicit freshness thresholds, and public-safe diagnostics for sustainable-development sources.

## Public endpoints

- `/public/sustainable-development/reliability`
- `/public/sustainable-development/freshness`
- `/public/sustainable-development/schema-validation`
- `/public/sustainable-development/cache`

Live checks remain opt-in through `SC_SI_SUSTAINABLE_DEVELOPMENT_LIVE_CHECKS=true`. Registry-only mode is network safe and remains the default.
