# Sustainable Catalyst Site Intelligence v3.22.9

## Runtime Diagnostics, Map Health, and Fault Isolation

This patch builds on the v3.22.1 map-runtime repair by making production failures visible, classifiable, and easier to support. It does not treat every blank panel as the same problem: the application now distinguishes local package integrity, backend endpoint availability, browser/runtime faults, service-worker state, map-library mode, and upstream tile degradation.

### What changed

- Added the public-safe `/public/runtime-health` endpoint.
- Added local checks for release alignment, application-shell presence, required assets, script order, offline-shell alignment, known map containers, and embed policy.
- Added an in-application Site Health tray with:
  - Critical endpoint status and response time
  - Leaflet or static-fallback mode
  - Initialized and visible map counts
  - Service-worker status
  - Recent map degradation and fallback events
  - Browser script errors and unhandled promise rejections
  - A copyable support report
- Added explicit fault capture for browser online/offline transitions and service-worker events.
- Upgraded the map runtime so failed OpenStreetMap tiles fall back to the first-party geographic grid while verified overlays remain active.
- Added a compact map-runtime snapshot API for diagnostics.
- Added the diagnostics runtime to the offline application shell.
- Upgraded the WordPress map fallback package to the v3.22.9 runtime.
- Aligned backend, public app, tests, service worker, data contracts, WordPress plugin, and release metadata to v3.22.9.

### Validation

- 854 automated tests passed.
- 32 JavaScript files passed Node syntax validation.
- 114 JSON files parsed successfully.
- Python application and test modules compiled successfully.
- WordPress PHP passed `php -l`.
- 16 critical local endpoints and assets returned HTTP 200.
- The runtime-health contract reported healthy with 6 of 6 checks, 8 of 8 required assets, and 14 of 14 known map surfaces declared.

### Operational boundaries

- Runtime health is a local contract check and does not contact third-party APIs or tile providers.
- A healthy local contract does not guarantee that every upstream public source is currently available.
- The browser health tray reports page-session conditions; it is not a persistent monitoring service.
- The first-party geographic grid preserves continuity and evidence overlays but is not a replacement for a detailed cartographic basemap.
