# Site Intelligence v4.36.0 R3 — Science→Ocean Hydration & Browser Promotion Gate Repair

R3 repairs the release-gate failure observed while installing R2. R2 correctly decoupled Science discovery from Platform Core, but its new browser certification asserted the Ocean card count immediately after the Ocean panel became visible. Ocean intentionally makes its shell visible before asynchronously hydrating `/public/ocean-observation/catalog` and `/public/ocean-observation/readiness`, so the test could observe a valid intermediate state: visible panel, correct title, zero rendered cards.

## Repair

- Adds an explicit Ocean hydration lifecycle: `idle → loading → ready` or `error`.
- Emits `scsi:ocean-observation-ready` only after the catalog is rendered.
- Publishes the rendered card count and catalog system count in the ready event.
- Makes the Science→Ocean launcher await `SCSIOceanObservationV4360.open()` and report readiness only after all 11 marine cards exist.
- Replaces the R2 browser race with an R3 gate that waits for Ocean hydration state `ready` and exactly 11 rendered marine systems.
- Preserves the R2 Core-decoupled Science front door: Earth, Ocean, and Space remain available when Platform Core is unconfigured.
- Preserves the no-fabrication rule and the established six-area / 35-route contract.
- Runtime and WordPress plugin versions remain `4.36.0`; repaired release lineage is `v4.36.0-r3`.
