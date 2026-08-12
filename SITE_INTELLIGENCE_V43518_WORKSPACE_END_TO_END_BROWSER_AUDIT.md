# Site Intelligence v4.35.21 — Workspace End-to-End Browser Audit

## Audit scope
The audit covers the entire 35-route public workspace contract across six primary navigation areas, not only recently added domain workspaces.

## “Simply works” definition
A registered workspace succeeds when it:
1. resolves through the public router;
2. has declared route metadata;
3. maps to an explicit workspace surface;
4. finishes route navigation without leaving the application busy;
5. renders either the expected surface or an explicit degraded recovery surface;
6. never falls through to the generic `View unavailable` state;
7. remains inside the browser viewport on mobile;
8. preserves evidence/Truth and external-source degradation semantics.

## Browser modes
The automated browser audit exercises all 35 routes in:
- desktop: 1360 × 940;
- mobile: 390 × 844;
- iframe/embed: 1180 × 820 inside a 1280 × 920 host page.

## Defects found and repaired
### Missing Workflows metadata
The `workflows` route was registered but lacked an explicit `routeMeta()` entry. v4.35.21 adds the missing title, eyebrow, description, and announcement metadata.

### Registered-route recovery
Previously, an optional module failing during route initialization could leave a registered route without a usable first-party workspace surface. v4.35.21 enforces the expected surface after every route transition. If the surface is absent or hidden, an explicit degraded workspace appears with `Retry workspace` and `Sources & methods` actions.

### Mobile horizontal overflow
Hidden evidence drawers and the overview evidence rail could widen a 390 px document to roughly 796 px even while visually off-canvas. The application shell now contains those surfaces within the viewport.

## Deterministic readiness
`/public/workspace-browser-audit/readiness` reports:
- 35 routes;
- 6 primary areas;
- all route surfaces mapped;
- all surfaces declared;
- all route metadata declared;
- all router branches declared;
- recovery layer present;
- registered routes protected from generic unavailable fallback;
- upstream provider health non-blocking;
- zero network calls during readiness.

## Deployment boundary
The workspace-browser control plane is a first-party release invariant. External API/provider availability is not. A broken browser/recovery contract can block promotion; an upstream NOAA/NASA/EPA/World Bank/etc. outage cannot.
