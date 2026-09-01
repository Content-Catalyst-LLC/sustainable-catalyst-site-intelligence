# Site Intelligence v4.39.0 R4 — Controller, Route Ownership & Prominence Audit

## Reported production symptom

The public application could show the Ocean title while Production Truth reported `Workspace unavailable`. Science could also open without a visible workspace surface when its controller was stale or missing.

## Root causes

1. The Science route used a controller that could be absent/stale without a hard failure, allowing the router to return while the Science panel remained hidden.
2. Ocean entered through the Earth route and could race the asynchronous route transition, leaving header state and workspace ownership out of sync.
3. Production Truth evaluated the canonical Earth surface even while Ocean owned the Earth route.
4. R3 cache busting did not cover every controller involved in route ownership.
5. Ocean was featured, but Space still required a secondary Science-domain selection.

## R4 controls

- `ensureScienceController()` verifies the R4 controller contract and reloads it dynamically when required.
- `openFeaturedScienceDomain("space")` opens Science and selects Space through the recovered controller.
- Ocean establishes `data-ocean-workspace-owner="earth:ocean"` after awaiting route ownership.
- Production Truth resolves the Ocean surface when Ocean mode is active and certifies the 11-card ready state.
- The main app controller and other ownership-critical assets use `4.39.0` cache lineage.
- Navigation consolidation retains two supplemental featured entries: Ocean and Space.

## Architecture boundary

R4 does not add a public route. Ocean remains an Earth-route owned mode; Space remains a Science-domain owned mode. The canonical public registry remains six areas and 35 routes. Platform Core scientific records remain optional and missing records are never fabricated.
