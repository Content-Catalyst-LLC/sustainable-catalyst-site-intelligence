# Site Intelligence v4.40.0.1 — Homepage Live Intelligence Runtime Repair

## Purpose

v4.40.0.1 is a surgical production repair for the Site Intelligence homepage experience. It does not redesign the approved widget, change the Earth / Space / Ocean entry structure, or remove v4.40.0 Energy Systems integration.

The repair addresses two production symptoms:

1. the homepage summary displayed `172` country profiles while the registered-live-feed, enabled-by-default, and current-signal slots remained `—`; and
2. the Live Intelligence ticker rendered current signals but did not move reliably.

## Metric contract repair

- The backend homepage summary now receives registered-feed and default-enabled-feed counts from the active Live Intelligence runtime registry used by the production feed itself.
- The WordPress renderer accepts the canonical v4.40.0.1 metric ids and the v4.39.1 compatibility alias `live_feeds`.
- If source-count metrics are absent from the summary payload, WordPress requests the public Live Intelligence status endpoint and derives only the two registry counts from `available_feeds` and `default_feeds`.
- `current_signals` falls back only to the bounded homepage response (`featured_signal_count` or returned highlights), never to an unrelated global count.
- Numeric zero is preserved as `0`; it is not converted to an unavailable dash.
- No counts are fabricated when neither the canonical payload nor an authoritative fallback provides them.

## Ticker runtime repair

- Replaces the fixed `translateX(-50%)` assumption with a measured travel distance based on the actual rendered signal set.
- Builds enough inert duplicate sets to cover the viewport and prevent blank gaps on wide layouts.
- Re-measures after live refreshes and viewport geometry changes using `ResizeObserver`, with a window-resize fallback.
- Restarts animation from the canonical origin after a refresh or re-measurement.
- Preserves hover/focus pause, manual pause, reduced-motion behavior, links, analytics, desktop/mobile presentation rules, and existing visual design.
- Hidden duplicate ticker controls are removed from keyboard focus and pointer interaction.

## Release identity

- Backend: `4.40.0.1`
- WordPress plugin: `4.40.0.1`
- Release id: `site-intelligence-v4.40.0.1`
- Release name: `Homepage Live Intelligence Runtime Repair`

## Deployment order

1. Apply the repository patch and push `main` plus tag `v4.40.0.1` to GitHub.
2. Deploy and verify the backend on the Contabo VPS.
3. Only after backend verification passes, install the v4.40.0.1 WordPress plugin.
4. Clear WordPress/transient caches and hard-refresh the homepage.
5. Complete browser acceptance on desktop and mobile.
