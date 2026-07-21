# Site Intelligence v3.7.2 — Signal Relevance and Rotation Intelligence

## Summary

v3.7.2 adds a governed rotation layer to the Live Intelligence homepage gateway. It evaluates a larger validated candidate pool, returns transparent relevance components, balances families, sources, and geographies, limits repeated exposure, and records aggregate signal-display history without profiling visitors.

## Capabilities

- Composite public relevance scoring using freshness, source health, public context, underlying rank, and editorial priority.
- Greedy family, geography, and source diversity adjustments.
- Repetition penalties based on aggregate signal exposure within a bounded rotation window.
- Deterministic fallback ordering and per-signal selection explanations.
- Configurable minimum display duration and maximum continuous exposure.
- Human-approved boost, pin, and suppress overrides with optional expiry.
- Public rotation policy and operational status endpoints.
- Protected rotation state and override endpoints.
- WordPress proxy routes and public data attributes for rotation rank, score, and override mode.

## Public routes

- `/public/live-intelligence/homepage`
- `/public/live-intelligence/rotation-policy`
- `/public/live-intelligence/rotation-status`

## Protected routes

- `/admin/live-intelligence/rotation`
- `/admin/live-intelligence/rotation/signals/{signal_id}`

## Governance boundaries

- Rotation scores rank display relevance; they do not measure truth, danger, or social importance.
- Display history contains aggregate signal exposure only and does not track or profile individual visitors.
- Human overrides cannot change source observations, evidence, source lineage, or freshness.
- High-impact or emergency claims are never published automatically by the rotation engine.
