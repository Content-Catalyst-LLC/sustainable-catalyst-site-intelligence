# v4.37.0 R3 Science→Ocean Hydration Audit

## Failure reproduced

The failed R2 browser certificate reported:

- Ocean panel visible: `true`
- Ocean title: `Ocean observation & marine systems`
- rendered Ocean cards: `0`

The deterministic backend suite had already passed 1,672/1,672 tests. R2 therefore stopped before GitHub/Render promotion even though the failure occurred in a browser timing boundary.

## Root cause

`SCSIOceanObservationV4360.open()` makes `#oceanObservationStudio` visible before awaiting its asynchronous catalog/readiness hydration. The R2 Playwright gate waited only for visibility and then immediately counted `[data-ocean-card]` elements. Browser click completion does not await an asynchronous DOM event listener, so the gate could run between panel reveal and catalog render.

## R3 contract

Ocean now exposes `data-ocean-hydration-state` with these states:

- `idle` — shell has not hydrated yet.
- `loading` — source-bound catalog/readiness contracts are loading.
- `ready` — catalog has rendered and marine cards are present.
- `error` — hydration failed; no ready state is fabricated.

The runtime emits `scsi:ocean-observation-ready` after render and includes both rendered `cardCount` and contract `systemCount`.

Science awaits the Ocean open contract and reports ready only when the Ocean panel is in `ready` state with exactly 11 marine system cards.

## Promotion boundary

The R3 browser gate certifies the exact user path:

1. Platform Core unconfigured.
2. Open Science.
3. Earth / Ocean / Space selector populated.
4. Select Ocean.
5. Launch Ocean Intelligence.
6. Wait for hydration state `ready`.
7. Confirm exactly 11 marine cards.
8. Return to Science.
9. Confirm six Space launch modules remain available.

The release does not weaken scientific evidence boundaries or treat workspace availability as proof of upstream scientific-data availability.
