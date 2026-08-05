# Site Intelligence v3.22.8

## Self-Hosted Mapping Engine and Production Browser Recovery

v3.22.8 repairs the production condition in which the backend and release gate could be healthy while map workspaces remained visually blank or the browser health tray stayed degraded.

### Mapping engine

- Replaces the v3.22.7 false-positive tile compatibility stub with a first-party interactive mapping engine.
- Creates and positions real raster tile images for OpenStreetMap, CARTO, and configured imagery sources.
- Bundles a public-domain Natural Earth country/coastline GeoJSON basemap so every map retains geographic context without a tile provider.
- Preserves markers, circles, GeoJSON polygons, paths, popups, layer controls, drag interaction, keyboard controls, wheel zoom, and bounds fitting.
- Uses the local vector basemap as the final resilient mode rather than presenting an empty grid.
- Keeps optional imagery failures visible as an imagery limitation without declaring the whole application unhealthy.

### Browser and WordPress recovery

- Loads the locally bundled map engine before all application modules in both the standalone app and WordPress plugin.
- Adds explicit `release=3.22.8` identity to embedded application URLs.
- Detects stale embedded releases and performs one controlled cache-busting reload.
- Uses network-first service-worker handling for the app shell, JavaScript, CSS, map engine, and world-boundary asset.
- Resolves recovered browser and service errors so historical faults do not remain active health failures.
- Keeps hidden workspaces out of the visible-map health calculation.

### Deployment assurance

- Verifies the live release gate, actual `/app/` HTML, self-hosted map-engine asset, local world-boundary asset, and runtime-health response before WordPress installation is permitted.
- Preserves resume-safe GitHub/Render promotion, deployment receipts, rollback tags, exact commit verification, and runtime-state isolation.

### Validation boundary

The release includes deterministic Python, JavaScript, JSON/GeoJSON, PHP, deployment-contract, and Chromium map-engine checks. The Chromium harness verifies visible rendered geographic paths, map controls, overlays, dimensions, interaction state, and zero console errors. Production WordPress visual verification remains a post-deployment check because the build environment cannot authenticate to the site administration interface.
