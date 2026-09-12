# Site Intelligence v4.40.0.2 — Homepage Intelligence Contract & Ticker Recovery

## Why this repair exists

v4.40.0.1 successfully restored numeric homepage telemetry, but production acceptance showed that the new metric binding changed the meaning of the four capability cards and the Live Intelligence ticker was still absent from the Site Intelligence homepage widget.

The screenshot captured during acceptance showed **172 country profiles / 8 registered live feeds / 8 enabled by default / 4 current signals**. Those values were internally consistent with the Live Intelligence feed registry, but they were not the established homepage capability contract. The bounded signal count also does not belong in the capability strip.

## v4.40.0.2 repair scope

- Restores the established homepage capability contract:
  - **172 country profiles**
  - **14 enabled connectors**
  - **35 public workspaces**
  - **8 live ticker feeds**
- Keeps `featured_signal_count` separate from the four capability metrics.
- Sources enabled connector count from the connector operations registry.
- Sources public workspace count from the six-area public intelligence route policy.
- Keeps live ticker feeds bound to the governed runtime feed registry.
- Embeds the governed Live Intelligence ticker directly inside `[sc_site_intelligence_home]` so ticker visibility no longer depends on Astra/header/breadcrumb placement hooks.
- Preserves the v4.40.0.1 measured ticker runtime: pixel-measured travel distance, sufficient duplicate sets, resize remeasurement, hover/focus/manual pause, reduced-motion behavior, mobile rotator behavior, links, analytics, and accessibility semantics.
- Preserves the existing dark/green homepage widget and the four current signal cards shown below the ticker.
- Preserves the Energy Systems Site Intelligence consumer at component version `4.40.0` because this repair does not change that consumer contract.

## Acceptance contract

A production v4.40.0.2 release is accepted only when all of the following are true:

1. Backend health reports `4.40.0.2`.
2. `/v1/public/site-intelligence/summary` exposes exactly the capability IDs and values `172 / 14 / 35 / 8`.
3. `featured_signal_count` remains a separate refresh field.
4. `/public/live-intelligence/homepage` returns one or more governed signals.
5. WordPress reports plugin `4.40.0.2` and loads v4.40.0.2 assets.
6. The homepage widget visibly contains a Live Intelligence ticker between the metric strip and the current-signal cards.
7. On normal desktop motion settings the ticker moves continuously; reduced-motion users retain a static/manual presentation.
8. Existing entry cards and the Open Site Intelligence action remain intact.

This is a forward-only repair. It does not roll back v4.40.0, v4.40.0 r1, or v4.40.0.1.
