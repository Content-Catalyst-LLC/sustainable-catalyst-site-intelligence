# Site Intelligence v3.22.8 Map Runtime Audit

## Reported production symptoms

- Site Health displayed **Degraded**.
- Global Conditions appeared in the left navigation but did not open.
- The Overview live map and other map workspaces did not render reliably.

## Root causes

1. `global-conditions-v210.js` inserted the Global Conditions button from a later `DOMContentLoaded` handler. `app.js` had already bound click handlers only to the buttons present at its own initialization, leaving the inserted button inert.
2. The standalone shell loaded Leaflet from `unpkg.com` as an ordered deferred script before all first-party application modules. A blocked, delayed, or filtered request could stall the complete application bootstrap.
3. The WordPress map loader also attempted the same remote Leaflet runtime before activating its local implementation.
4. Browser health logic classified any fallback- or grid-named mode as degraded, including hidden workspaces and an otherwise functioning first-party map.

## Corrective architecture

- The Global Conditions route is declared directly in `index.html`.
- The sidebar uses one delegated click listener on `#primaryNavigation`.
- `map-fallback-v3224.js` is now the primary first-party interactive map runtime and loads before application modules.
- The runtime exposes the Leaflet-compatible subset used by Site Intelligence modules while implementing map interaction locally.
- WordPress enqueues the map runtime as an explicit dependency of the main plugin script.
- Runtime health evaluates visible surfaces and their explicit status, not naming heuristics.

## Known boundary

Chromium was available, but the managed browser policy blocked both localhost and file URLs with “Your organization doesn’t allow you to view this site.” No visual screenshot sign-off is claimed. Automated validation covers script order, route contracts, endpoint contracts, syntax, package integrity, runtime health, and the inherited backend suite. Production validation should still confirm pointer interaction, mobile layout, and representative vector overlays after Render and WordPress reach exact release parity.
