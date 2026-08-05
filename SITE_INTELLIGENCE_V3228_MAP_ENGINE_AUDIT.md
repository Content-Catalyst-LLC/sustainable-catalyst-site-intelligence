# Site Intelligence v3.22.8 Map Engine Audit

## Incident

The v3.22.7 backend could report healthy while maps remained blank in production. The release gate proved deployment identity and packaged-asset presence, but it did not prove that the browser map layer rendered geographic content.

## Root causes

### False-positive tile runtime

The previous compatibility layer implemented `L.tileLayer()` as an object that emitted a successful load event without creating raster tile images. Application modules therefore believed a basemap had loaded even when no basemap existed.

### Incomplete fallback presentation

The fallback geographic grid could retain simple overlays but did not provide country outlines, coastlines, labels, or recognizable geographic context. A workspace with delayed or empty overlay data appeared blank.

### Sticky browser degradation

Session errors remained in the diagnostics history and could continue to influence the visible status after their service or map recovered.

### Stale embedded browser shells

The WordPress iframe did not enforce an explicit release identity strongly enough. Service-worker and page caches could preserve an older application shell even after Render was current.

## Repairs

### First-party map engine

`map-engine-v3228.js` is loaded before application modules and implements the subset of the Leaflet API used by Site Intelligence. It creates real tile `<img>` elements, calculates visible tile coordinates, projects geographic coordinates, redraws on interaction, and preserves application overlays.

### Bundled world geography

`world-boundaries-v3228.geojson` contains simplified Natural Earth country and coastline geometry. It is served by the backend, bundled in WordPress, cached by the offline shell, and rendered beneath evidence overlays. The source dataset is public domain.

### Layered recovery order

1. Use the requested tile or imagery source.
2. For failed CARTO basemaps, retry OpenStreetMap.
3. If external tiles remain unavailable, retain the bundled local vector geography and evidence overlays.
4. Mark imagery as limited without failing the application map.

### Correct health semantics

- A visible map is degraded only when its map container is explicitly failed.
- A local-vector map is a healthy operational mode.
- Optional imagery outages are reported separately.
- Successful endpoint and map recovery resolves active session errors while retaining resolved history.
- Hidden workspaces do not reduce overall health.

### Browser cache recovery

- Versioned app-shell assets use network-first service-worker handling.
- WordPress iframe URLs include the expected release.
- A mismatched iframe response triggers one controlled cache-busting reload.
- Height and readiness messages are accepted only from the expected release.

## Chromium evidence

The release harness creates two independent map surfaces using the shipped engine and local world-boundary file. It verifies:

- both map containers initialize with the self-hosted engine;
- each surface renders geographic boundary paths;
- controls and evidence overlays are visible;
- map dimensions are non-zero;
- the map runtime does not classify the surfaces as degraded;
- no JavaScript console errors are emitted.

The harness remains network-independent: it validates the local vector mode even when external tiles are unavailable.
