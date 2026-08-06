# Site Intelligence v3.23.6.3 — Data Freshness, Coverage, and Source Truth

v3.23.6.3 makes public data condition explicit. Each canonical source now discloses its publisher, public endpoint, license, geographic and temporal coverage, refresh interval, cache lifetime, stale threshold, retrieval timestamps, current condition, declared record class, completeness, schema contract, retry policy, and circuit-breaker state.

Cached, stale, historical, demonstration, context-only, and unavailable records are never presented as live. Last-known-good recovery requires a visible stale marker. Missing fields remain visible, schema changes require review, and fallback data cannot silently replace a failed source.

Public endpoints:

- `/public/data-truth`
- `/public/data-truth/{feed_id}`

The application includes an app-scoped Data truth panel. Its JavaScript is packaged in WordPress for embed parity but is not enqueued into the WordPress host document.
