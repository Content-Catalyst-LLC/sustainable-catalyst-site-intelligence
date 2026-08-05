# Site Intelligence v3.22.9

## Vector Cartography, Satellite Composition, and Map Presentation

v3.22.9 upgrades the v3.22.8 recovery engine from a technically functional map surface into a clearer institutional cartographic presentation. It preserves the self-hosted, no-blocking-CDN startup path while improving geographic hierarchy, imagery composition, labeling, scale, sizing, and browser-visible quality checks.

### Vector cartography

- Adds `vector-cartography-v3229.js` and `vector-cartography-v3229.css` as the shared standalone and WordPress map runtime.
- Enriches the bundled Natural Earth geography with country identity, label coordinates, label rank, extent score, and cartography class.
- Renders country and coastline geometry beneath evidence overlays at every map startup.
- Adds zoom-aware country labels, continent-sensitive land fills, national outlines, coordinate readout, scale bar, and map-quality status.
- Keeps the familiar Site Intelligence `window.L` integration contract so the existing fourteen map workspaces do not require separate rewrites.

### Satellite and raster composition

- Creates separate base, imagery, and overlay raster panes.
- Keeps the base map visible beneath NASA imagery rather than replacing the map with a black placeholder.
- Moves imagery above the base map with explicit layer roles and controlled opacity.
- Removes the oversized orbital glow and vignette masks that obscured the map.
- Preserves local vector geography if raster tiles or satellite imagery are unavailable.

### Map presentation

- Raises desktop map height to a controlled 520–720 pixel range.
- Uses deep slate water, differentiated land classes, restrained borders, readable labels, and evidence-first accent treatment.
- Adds scale and coordinate context without crowding the evidence interface.
- Keeps event markers, polygons, popups, layer controls, dragging, wheel zoom, keyboard controls, and bounds fitting.
- Reports local-vector and vector-plus-satellite modes as valid operational states.

### Release and browser assurance

- Packages the same cartography runtime and geography in the standalone app and WordPress plugin.
- Adds all current map assets to the network-first service-worker shell.
- Requires the live promotion gate to retrieve the current app shell, vector engine, local geography, runtime health, release ID, branch, and exact Git commit before WordPress installation is released.
- Adds a deterministic Chromium visual smoke test for raster layering, local boundaries, labels, controls, scale, coordinates, evidence overlays, non-zero dimensions, color diversity, dark-pixel ratio, and console errors.

### Validation boundary

The release validates the shared map renderer directly in Chromium with deterministic local raster tiles. The managed Chromium environment blocks navigation to localhost, so the full FastAPI application route is verified structurally and through API tests rather than claimed as an end-to-end localhost screenshot test. Production WordPress visual inspection remains part of the post-deployment checklist.
