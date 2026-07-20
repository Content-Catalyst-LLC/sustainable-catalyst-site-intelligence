# Site Intelligence v3.3.0 — Event Clustering and Intelligence Ranking

## Summary

v3.3.0 reduces repetitive Live Intelligence stories by grouping event records that align by event type, time, location, and meaningful language. Each group produces one canonical event while preserving represented sources, member record IDs, source links, and explicit clustering boundaries.

The release also replaces simple priority ordering with transparent display-relevance ranking. Every selected signal receives a bounded score, component breakdown, development state, selection rank, and plain-language selection reasons.

## Event clustering

- Cross-source duplicate suppression for event records.
- Category boundaries prevent unrelated event types from being merged.
- Time, geographic distance, country, and title-language alignment are used conservatively.
- One canonical event represents a cluster while retaining all represented source names and links.
- Cluster size, represented-source count, confidence, member IDs, and clustering reason are public-safe metadata.
- Single-source records remain valid and are explicitly labeled as such.

## Intelligence ranking

Ranking considers significance, freshness, registered source priority, represented-source corroboration, explicit signal priority, and stale or degraded data penalties.

Category diversity and per-source caps remain in force after ranking. Each signal exposes its selection reasons and scoring components through the public API. The ticker tooltip includes the development state and reasons without making the board visually denser.

## Public transparency

A new endpoint documents the method and its boundaries:

`GET /public/live-intelligence/ranking-policy`

Scores rank display relevance. They do not measure truth, danger, urgency for a specific person, source accuracy, or institutional importance. Multiple represented sources do not automatically constitute independent verification.

## Preserved behavior

- Feed-selection controls
- Signal Source Operations
- Desktop electronic marquee
- Mobile rotator, swipe, and previous/next controls
- Shortcode overrides
- Source attribution and freshness
- Placement fallback and duplicate guard
- Astra navigation and breadcrumb styling boundaries
