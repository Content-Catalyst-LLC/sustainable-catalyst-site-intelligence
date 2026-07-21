# v3.6.1 — Live Intelligence Reliability and Freshness

## Purpose

This release places a reliability boundary around the existing v3.5.0 channel, source, clustering, ranking, context, and evidence pipeline. It does not create a second ticker engine.

## Reliability contract

- Every public signal is validated before delivery.
- Freshness is classified as `live`, `recently_updated`, `delayed`, `stale`, `historical`, or `unknown`.
- Malformed, duplicate, and expired signals are isolated without breaking valid signals.
- Last-known-good recovery is allowed only for the exact same channel, geography, feed selection, exclusions, source cap, category, and limit query.
- An empty regional or country result remains empty and is never replaced with unrelated global signals.
- No failed or missing measurement is converted to zero or a fabricated value.

## Public health route

`GET /public/live-intelligence/status` returns the active delivery state, signal count, freshness counts, rejection count, partial-feed state, configured thresholds, and public-safe last-known-good availability. File-system paths and connector error details are not exposed.

## WordPress delivery

The WordPress proxy has bounded timeouts, a short fresh-cache interval, and an administrator-configured stale-cache window. The ticker displays an explicit delivery badge, keeps its reserved layout space, refreshes at a controlled interval, and preserves reduced-motion, keyboard, mobile rotator, and no-JavaScript behavior.

## Boundaries

Freshness describes time, not truth. Last-known-good delivery preserves availability, not independent verification. Source lineage, context pages, evidence records, official warnings, and human editorial judgment remain authoritative for interpretation.
