# Site Intelligence v4.40.0.3 — Live Intelligence Ticker Pace & Readability Repair

## Why this patch exists

v4.40.0.2 restored the homepage capability contract and integrated the governed Live Intelligence ticker directly into the Site Intelligence homepage card. Production browser acceptance then showed that the ticker moved too quickly to read comfortably.

The cause was a mismatch between the new measured ticker geometry and the inherited fixed animation durations: the desktop ticker still used a 42-second cycle and mobile used 36 seconds regardless of the rendered signal-set width.

## Repair scope

- Preserves the v4.40.0.2 homepage capability contract: **172 country profiles / 14 enabled connectors / 35 public workspaces / 8 live ticker feeds**.
- Preserves the integrated homepage Live Intelligence ticker and governed signal feed.
- Replaces fixed-cycle ticker pacing with a **distance-based speed model**.
- Targets approximately **28 px/second on desktop** and **23 px/second on mobile**.
- Bounds desktop duration to **75–220 seconds** and mobile duration to **90–260 seconds** so short and long payloads remain readable without becoming effectively static.
- Records measured travel, calculated duration, and effective pixels-per-second in DOM data attributes for production diagnostics.
- Keeps hover pause, focus pause, manual pause, reduced-motion handling, inert duplicate sets, signal links, and measured seamless-loop geometry intact.
- Raises CSS fallback durations from 42/36 seconds to 96/118 seconds as a defensive fallback; normal ticker motion uses the measured JavaScript duration.

## Release boundary

This is a presentation/runtime pacing repair. It does **not** change the underlying Live Intelligence feed selection, homepage metric semantics, Energy Systems consumer behavior, source registry, or signal content.

## Acceptance criteria

1. Backend and WordPress report **4.40.0.3**.
2. Homepage capability metrics remain **172 / 14 / 35 / 8**.
3. The governed homepage ticker renders and moves continuously.
4. Desktop ticker speed is approximately 28 px/s; mobile ticker speed is approximately 23 px/s, subject to bounded duration safeguards.
5. Hover/focus/manual pause and reduced-motion behavior remain functional.
6. No fixed 42-second desktop or 36-second mobile ticker cycle remains active.
