# Site Intelligence v2.8.0 — Alerts, Monitoring, and Live Intelligence Streams

## Purpose

Provide source-aware public monitoring without introducing paid infrastructure, persistent user profiles, operational emergency claims, or automated risk decisions.

## Architecture

- Existing public observatories provide sanitized records.
- `/public/live-intelligence-stream/events` emits one bounded SSE snapshot plus a heartbeat and reconnect interval.
- EventSource reconnects automatically; `/public/live-intelligence-stream` is the JSON fallback.
- Alert rules and watched places stay in browser local storage.
- `/public/alerts-monitoring/evaluate` performs stateless matching.
- `/public/alerts-monitoring/sources` reports public-record recency and workspace availability.
- `/public/alerts-monitoring/digest` creates a deterministic, non-AI summary.

## Responsible-use boundaries

The workspace is not an emergency service, trading system, legal determination, sanctions screener, eligibility engine, individual risk score, or military targeting product. Source records may be delayed, incomplete, revised, or unavailable.
