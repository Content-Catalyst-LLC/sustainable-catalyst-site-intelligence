# Site Intelligence v3.4.0 — Signal Context and Drill-Down

Site Intelligence v3.4.0 turns Live Intelligence signals into source-aware research entry points rather than sending every click directly to an upstream page.

## Signal context

- Public context endpoint for each current signal.
- Source lineage with primary and represented-source roles.
- Observed, updated, and selected timeline.
- Map handoff when source coordinates are available.
- Transparent ranking score, component, and selection-reason display.
- Related Site Intelligence workspace routes.
- Bounded research suggestions based only on visible term overlap.
- Explicit methodology, precision, and responsible-use limits.

## Evidence and portability

- Public evidence endpoint for each signal.
- Canonical SHA-256 digest over the public-safe evidence packet.
- Preserved source names, links, data state, timestamps, cluster lineage, and selection context.
- Integrity digests verify packet consistency; they do not certify factual truth.

## WordPress integration

- Public detail route: `/live-intelligence/signal/{signal_id}/`.
- Ticker links can open context pages before the original source.
- Actions to open the primary source, Site Intelligence, Decision Studio, and the evidence record.
- Existing feed, source-operations, clustering, ranking, desktop ticker, mobile rotator, placement, cache, and shortcode behavior remain intact.
- Astra navigation and breadcrumb colors remain under the theme's control.

## Public endpoints

- `/public/live-intelligence/context-policy`
- `/public/live-intelligence/signals/{signal_id}`
- `/public/live-intelligence/signals/{signal_id}/evidence`
- `/public/live-intelligence/signals/{signal_id}/view`

## Boundaries

Context pages do not independently verify source claims, improve geographic precision, establish causation, or replace official emergency, legal, medical, or financial guidance. Related research is a transparent term-overlap suggestion, not an endorsement or completeness claim.
