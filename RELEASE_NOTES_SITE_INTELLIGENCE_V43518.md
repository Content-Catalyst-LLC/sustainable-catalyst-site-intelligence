# Site Intelligence v4.35.18 — Full Workspace End-to-End Browser Audit & “Simply Works” Reliability

## Release objective
Make the complete public Site Intelligence workspace contract behave predictably for a visitor: every registered route must render its intended workspace or an explicit degraded recovery surface; registered routes may not silently become blank or fall through to the generic unavailable view.

## Delivered
- Audited all 35 registered routes across the six primary Site Intelligence areas.
- Added deterministic route-to-surface and route-metadata contracts.
- Added first-party workspace-browser readiness and per-route audit endpoints.
- Added post-navigation recovery enforcement with Retry workspace and Sources & methods actions.
- Repaired the missing Workflows route metadata contract.
- Fixed mobile horizontal overflow caused by hidden evidence drawers and the overview evidence rail.
- Added desktop, 390 px mobile, and iframe browser-route audit coverage.
- Preserved canonical evidence/Truth behavior, credential control, external resilience, and non-blocking external source health.

## Release invariants
- 35 registered routes.
- 6 primary areas.
- No registered-route generic unavailable fallback.
- Explicit degraded state when a registered workspace module/surface is unavailable.
- Browser audit and readiness perform no upstream provider health checks.
- External provider availability remains non-blocking for deployment.
- Authoritative connector coverage is unchanged from v4.35.17: 50 public connector interfaces and 112 machine-readable source registrations.

## Validation
The final release is gated by the full deterministic pytest suite, immutable repository manifest, JSON/GeoJSON parsing, JavaScript/PHP syntax validation, static security scanning, release contract validation, and the 35-route desktop/mobile/iframe browser audit.
