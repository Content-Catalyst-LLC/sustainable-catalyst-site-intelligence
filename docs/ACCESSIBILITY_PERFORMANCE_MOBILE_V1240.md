# Site Intelligence v1.24.0 — Accessibility, Performance, and Mobile Release

This release hardens the public Site Intelligence application for keyboard use, reduced-motion preferences, mobile navigation, constrained networks, and WordPress embedding. It targets WCAG 2.2 Level AA behavior but does not claim third-party certification.

## Accessibility work

- Added a two-destination skip-link system, route announcement live region, explicit `aria-current` navigation state, and persistent visible focus treatment.
- Added a complete mobile navigation drawer so all nine research workspaces remain reachable on phones.
- Added Escape-close behavior, backdrop handling, inert main content while the drawer is open, and focus restoration.
- Added reduced-motion handling in CSS and disabled timeline autoplay when the operating system requests reduced motion.
- Added forced-colors support and retained text labels for status, source, and data state.
- Preserved accessible tables, source notes, and textual evidence alongside maps and visual charts.

## Performance work

- Added GZip middleware for eligible responses.
- Added explicit no-cache behavior for the app shell and short stale-while-revalidate caching for first-party assets.
- Removed the eager html2canvas dependency from initial page load and load it only when a PNG export is requested.
- Added first-party byte budgets and public diagnostics.
- Added `content-visibility` and intrinsic-size hints for below-fold workspaces.
- Throttled WordPress embed height messages with `requestAnimationFrame`.

## Mobile work

- Replaced the truncated five-column bottom navigation with an accessible drawer exposing every workspace.
- Added safe-area padding, dynamic viewport units, 44px design touch targets, compact-phone behavior, and horizontal overflow containment.
- Removed stacked sticky filter decks on small screens to reduce nested scrolling traps.
- Hardened WordPress embeds for full-width phone layouts and lazy loading.

## Public endpoints

- `GET /public/experience-profile`
- `GET /public/experience-profile/checklist`
- `GET /public/experience-profile/diagnostics`

Diagnostics verify release contracts and first-party budgets. Manual screen-reader, zoom, real-device, and network-throttling review remains required.

## Infrastructure boundary

This release adds no accounts, telemetry vendor, paid database, Redis service, proprietary map service, or additional Render service. Platform Core remains optional.
