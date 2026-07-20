# Site Intelligence v3.3.0 — Signal Source Operations

## Summary

v3.3.0 turns the Live Intelligence collectors into an inspectable source-operations system. It adds public-safe source metadata and a protected control center without replacing the established ticker, feed selection, placement, readability, or mobile navigation behavior.

## Source registry

- Eight Live Intelligence sources are registered with stable feed IDs.
- Each source carries provider, category, collector, priority, refresh, cache, rate, rights, attribution, geographic coverage, temporal coverage, quality status, limitations, and a public note.
- Public payloads exclude API keys, authorization headers, raw upstream payloads, and private error detail.

## Operations

- Operational source enablement is separate from the WordPress displayed-feed selection.
- Priority, refresh minutes, and cache TTL can be updated through protected admin endpoints.
- File-backed state records last attempt, last success, data state, record count, duration, daily request count, failures, and test status.
- JSONL history stores bounded operational receipts without complete source payloads.
- Manual configuration checks do not contact upstream providers.
- Manual live tests are explicit and protected by the Site Intelligence API token.

## WordPress

The Live Intelligence settings page now includes a source-operations dashboard with health, freshness, rate use, last success, rights, coverage, operational configuration, save, configuration-check, and live-test controls.

## Boundaries

Source health describes retrieval operations and freshness, not a certification of source accuracy. Source-level licensing notes do not replace checking the rights attached to a specific upstream record. Astra navigation and breadcrumb styling remain untouched.
