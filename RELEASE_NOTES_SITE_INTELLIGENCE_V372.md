# Site Intelligence v3.7.2 — Analytics and Public-Value Measurement

Site Intelligence v3.7.2 measures whether Live Intelligence helps visitors reach evidence, sources, maps, Site Intelligence workspaces, and Decision Studio without building visitor profiles.

## Delivered

- Aggregate component and signal impressions.
- Signal-context, source, evidence-record, map, Site Intelligence, and Decision Studio handoffs.
- Engagement summaries by signal family, freshness, destination type, viewport, motion mode, delivery state, and source.
- Reduced-motion and manual-control usage counters.
- Successful-load, failed-load, and empty-feed counters.
- Source reliability reporting that combines registered operational health with aggregate public engagement.
- Public analytics policy, summary, and source-reliability contracts.
- Protected aggregate-by-signal administrative summary.
- WordPress telemetry that sends only approved dimensions and bypasses the older page-path/href event bridge.

## Privacy boundaries

The analytics endpoint rejects IP addresses, visitor IDs, session IDs, cookies, user agents, referrers, page paths, page titles, URLs, free text, and arbitrary metadata. Raw events are never stored. Day-level aggregate counters are retained for a bounded period, and the public summary omits signal-level counters.

## Routes

- `POST /public/live-intelligence/analytics/events`
- `GET /public/live-intelligence/analytics-policy`
- `GET /public/live-intelligence/analytics/summary`
- `GET /public/live-intelligence/analytics/source-reliability`
- `GET /admin/live-intelligence/analytics`

## Preserved

v3.7.1 rotation governance, v3.7.0 gateway destinations, v3.6.2 accessibility controls, v3.6.1 reliability, channels, signal context, source operations, and human-controlled publication boundaries remain active.
