# Sustainable Catalyst Site Intelligence v3.22.1

## Map Runtime Reliability, Spatial Evidence Mapping, and Embed Repair

This patch repairs the shared map runtime rather than applying isolated fixes to individual screens.

### What changed

- Added a first-party map reliability runtime that loads after Leaflet and before the application.
- Added a static geographic-grid fallback so verified points, lines, and polygons remain visible when Leaflet or external map assets are blocked.
- Added automatic CARTO-to-OpenStreetMap fallback after repeated basemap tile failures.
- Added explicit degraded-imagery events and visible map status messaging instead of silent blank panels.
- Added the fallback runtime and stylesheet to the offline application shell.
- Added a bounded 3.5-second WordPress Leaflet failover to the local map runtime.
- Converted Spatial Evidence from a list-only surface into a map-backed workspace with area previews, contextual public locations, and matched GeoJSON evidence.
- Fixed contradictory embed protection: approved `/app/` embeds now use `Content-Security-Policy: frame-ancestors` without also sending `X-Frame-Options: SAMEORIGIN`.
- Preserved same-origin frame protection whenever public embeds are disabled.
- Aligned backend, public app, service worker, manifest, policies, tests, and WordPress plugin to v3.22.1.

### Validation

- 847 inherited and new regression tests passed.
- All Python modules compiled.
- All public-app and WordPress JavaScript parsed with Node.
- WordPress PHP passed `php -l`.
- Public map, spatial, app-shell, service-worker, and fallback-asset endpoints passed smoke checks.
- Browser automation could not be used in the build environment because Chromium navigation is administrator-blocked. This limitation is recorded rather than presented as visual-browser validation.

### Operational boundaries

- The fallback grid is a continuity and diagnostics surface, not a replacement for a detailed cartographic basemap.
- Satellite imagery still depends on its public upstream tile service; failures now degrade visibly without stopping the rest of the application.
- The Spatial Evidence map displays published records only. Context locations are labeled as orientation data and are not treated as evidence matches.
