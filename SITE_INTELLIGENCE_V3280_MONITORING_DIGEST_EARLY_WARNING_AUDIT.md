# Site Intelligence v4.6.0 Monitoring, Digest, and Early-Warning Audit

## Scope

This audit covers the public-safe monitoring layer introduced in v4.6.0.

### Watchlists

The watchlist preview normalizes public countries, geographic areas, source identifiers, explicit threshold rules, and cadence. The public preview performs no server write and contains no individual-tracking contract.

### Threshold evaluation

Numeric threshold matching is deterministic. A match records the rule, signal, comparison trigger, freshness state, limitations, and a stable fingerprint. Unsupported or missing numeric values are not silently coerced into matches.

### Alert-state history

The normalized states are `new`, `continuing`, `changed`, `resolved`, and `withdrawn`. A resolved state only means that a previous supplied match is absent from the current supplied evaluation. It does not prove a hazard or condition has ended.

### Source-change monitoring

Schema fingerprints, operational states, freshness labels, and coverage fingerprints can be compared across supplied source snapshots. Site Intelligence reports observed changes without claiming a publisher-wide outage has been independently verified.

### Modeled warnings

Modeled-warning previews are explicitly labeled as modeled analytical signals. They remain distinct from source alerts, do not claim probabilities, do not trigger automatic action, and are not emergency instructions.

### Digests and feeds

Digest outputs remain drafts with `human_review_required=true`, `publication_allowed=false`, and `automatic_publication=false`. The reviewed-feed contract supports JSON, Atom, and RSS only after human approval and does not require subscriber profiling.

### Safety and governance

The release prohibits automatic emergency dispatch, individual tracking, hidden risk scoring, automatic consequential action, fabricated events, and automatic publication.
