# Site Intelligence v3.23.7 source-truth audit

## Production problem addressed

A functioning connector could expose records without one consistent public statement of whether the record was live, cached, stale, historical, demonstration-only, or context-only. Source-level licensing and coverage existed in parts of the platform but was not enforced as one visible presentation contract.

## Release contract

- Eight canonical public sources disclose publisher, endpoint, license, geographic coverage, temporal coverage, refresh interval, cache lifetime, stale threshold, record schema, and retry policy.
- `/public/data-truth` provides the complete public directory.
- `/public/data-truth/{feed_id}` provides a source-specific disclosure.
- No successful retrieval means demonstration or unavailable—not live.
- A failed source using last-known-good data is recently cached and requires a stale marker.
- Periodic indicator and observational records remain historical snapshots.
- Research metadata remains context-only.
- Schema fingerprints are disclosed as matched, changed, or not yet observed.
- Three consecutive failures open the public circuit-breaker state.
- Missing metadata and coverage remain visible; values are not silently imputed.
- The Data truth interface runs only inside the Site Intelligence application and is not enqueued into the WordPress host page.
