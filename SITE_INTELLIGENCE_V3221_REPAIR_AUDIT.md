# Site Intelligence v3.22.1 Repair Audit

## Scope

The uploaded v3.22.0 repository was inspected as a complete platform rather than as a single map component. The active backend, standalone public application, service worker, WordPress plugin, spatial evidence module, and inherited tests were reviewed.

## Production causes found

### 1. Map boot depended on a single third-party Leaflet load

The standalone application loaded Leaflet from `unpkg.com` and immediately initialized map objects. A blocked CDN, restrictive network, or Content Security Policy could leave `L` undefined and stop the broader application boot sequence.

**Repair:** a first-party map reliability runtime now executes after the remote Leaflet request and before the application. It patches real Leaflet when available or installs a static SVG geographic-grid implementation when it is not.

### 2. Multiple maps used a single CARTO basemap without failover

Live Events, Country, Compare, Earth Observation, Thematic Intelligence, and several domain modules could render blank when CARTO tiles failed.

**Repair:** repeated CARTO tile errors now activate an OpenStreetMap fallback. Map containers retain a geographic grid and visible degraded status even when all raster tiles are unavailable.

### 3. Satellite imagery failures were largely silent

NASA/public imagery failures could leave a map apparently empty without clearly separating imagery failure from application failure.

**Repair:** imagery tile degradation now emits a shared application event and updates public status messaging while preserving the basemap and evidence layers.

### 4. Spatial Evidence had no map surface

The v2.15.0 Spatial Evidence frontend listed layers and selectors but did not instantiate a map or draw area/evidence geometry.

**Repair:** the workspace now maps public areas of interest, optional public context locations, and matched GeoJSON evidence. Context records are explicitly separated from evidence matches.

### 5. Approved embeds received conflicting frame policy

`/app/` could send a permissive `Content-Security-Policy: frame-ancestors ...` while also sending `X-Frame-Options: SAMEORIGIN`. The legacy header could block an otherwise approved cross-origin WordPress iframe.

**Repair:** embeddable app responses use the configured `frame-ancestors` policy without the conflicting legacy header. When embeds are disabled, same-origin protection remains in place.

### 6. WordPress map loading had no bounded local recovery

The WordPress geospatial surface dynamically requested Leaflet from the same third-party CDN and rejected the map initialization when that request failed.

**Repair:** WordPress now switches to the bundled map runtime after an error or a 3.5-second timeout.

## Validation result

- 847 tests passed.
- 28 JavaScript files parsed successfully.
- 114 JSON files parsed successfully.
- Python application and release scripts compiled successfully.
- WordPress PHP syntax passed.
- 15 critical public endpoints/assets returned HTTP 200 in TestClient smoke validation.
- Embed headers were verified for the enabled and disabled states.

## Browser-validation limitation

Chromium navigation is blocked by administrator policy in this execution environment, including localhost. No claim of screenshot-based or real-browser visual validation is made. The release instead includes static contracts, endpoint smoke coverage, map-runtime regression tests, and an explicit on-site verification checklist.

## Recommended production verification

After deployment, open the standalone application and embedded WordPress surface in a normal browser, then inspect Overview, Events, Country, Compare, Earth Observation, Thematic Intelligence, and Spatial Evidence. Test once normally and once with `unpkg.com` blocked to confirm the static fallback path.
