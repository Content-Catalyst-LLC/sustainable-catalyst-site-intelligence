# Site Intelligence v3.23.6.2 Production Truth Audit

## Audit objective

The v3.23.0 interface exposed 35 public navigation routes. The objective of v3.23.6.2 was to ensure that each route either opens a real public surface with complete runtime states or fails closed with an explicit unavailable state.

## Findings and repairs

### Route inventory

The canonical route directory now contains 35 routes:

- 19 core analytical workspaces marked `operational`.
- 16 public-summary, browser-local, governance, publishing, integration, or workflow surfaces marked `operational-bounded`.
- 0 routes falsely marked available without a controller or native surface.

Each route declares its controller when applicable, visible surface selectors, endpoint families, empty result language, degraded service language, methodological limitation, and lazy-load contract.

### Runtime states

The browser now distinguishes five states:

1. `initial` — the route is opening and its public surface is being verified.
2. `ready` — a meaningful active surface is visible.
3. `empty` — the route works, but no public records match the current selection.
4. `degraded` — the route remains partially usable while a service recovers.
5. `unavailable` — the required controller or visible workspace surface is missing.

The runtime no longer treats a missing controller as a successful route. Missing controllers disable their navigation item and expose an unavailable explanation.

### Navigation truth

The production-truth runtime records route changes in browser history, restores supported deep links, handles back and forward navigation through the public router, moves focus to the route heading, and maintains one active workspace state.

### Data truth

Empty results remain distinct from service failure. Degraded messages are route-specific and retain source, coverage, freshness, and methodological limits. Recovery events reevaluate the active workspace without claiming that every upstream provider is healthy.

### Deployment truth

The release validator checks the backend route directory, all public tests, JavaScript syntax, JSON and GeoJSON parsing, WordPress PHP syntax, the cartographic Chromium smoke test, and the production-truth Chromium smoke test. The Render promotion gate verifies the live route count, release ID, production-truth JavaScript contract, app shell, map runtime, local world geography, runtime health, and exact Git commit before the WordPress ZIP is released.
