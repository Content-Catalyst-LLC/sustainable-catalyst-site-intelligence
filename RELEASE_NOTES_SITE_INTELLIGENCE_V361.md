# Site Intelligence v3.6.1 — Live Intelligence Reliability and Freshness

Site Intelligence v3.6.1 begins the production build of the Live Intelligence homepage ticker by hardening the existing v3.5.0 feed and channel system.

## Included

- Canonical validation for every public signal.
- Explicit `live`, `recently updated`, `delayed`, `stale`, `historical`, and `unknown` freshness states.
- Isolation of malformed signals so one bad source record cannot break the feed.
- Duplicate and expired-signal suppression with aggregate diagnostics.
- Same-query last-known-good recovery with atomic file persistence and bounded retention.
- Honest empty regional and country feeds with no unrelated global fallback.
- Public `/public/live-intelligence/status` health contract.
- WordPress proxy timeout, fresh-cache, stale-cache, refresh-interval, and freshness-label controls.
- A restrained delivery badge integrated into the existing ticker without changing Astra navigation or breadcrumb styling.
- Static syntax checks and 635-test regression coverage.

## Preserved

Source operations, feed selection, topic and regional channels, event clustering, transparent ranking, signal context, evidence records, mobile navigation, reduced motion, keyboard pause, placement reliability, and public-safe source lineage remain intact.

## Boundaries

Freshness does not certify accuracy. Last-known-good recovery does not independently verify a source. No missing value is replaced with zero or fabricated data, and cached signals are never reused across different channel, geography, feed, category, or limit queries.
