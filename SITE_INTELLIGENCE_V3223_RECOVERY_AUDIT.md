# Site Intelligence v3.22.8 recovery audit

## Release objective

Prevent transient API, proxy, tile, or service-family failures from making Site Intelligence appear globally broken. Recovery must remain public-safe, bounded, transparent, and isolated to the affected surface.

## Findings addressed

### Fragmented request behavior

Application modules previously implemented their own one-shot fetch helpers. Some core routes retried, while many specialized workspaces failed immediately. The v3.22.8 recovery runtime now wraps eligible same-origin public JSON requests before application modules load.

### Cascading failure perception

A failed endpoint could leave several panels displaying unavailable states even when unrelated services remained healthy. Separate circuits now isolate Core, Geospatial, Country, Indicators, Research, and Operations.

### Cached continuity without freshness labels

The service worker already retained public data, but a cached response could be difficult to distinguish from a current network response. Recovered responses now carry explicit recovery mode, stale age, and release headers.

### Aggregate-only map diagnostics

The v3.22.2 console reported map counts and modes but did not identify exactly which map was degraded. Every initialized map now registers its container ID, mode, status, visibility, imagery state, and recovery schedule.

### Static fallback without return path

The geographic grid preserved overlays after OpenStreetMap failure, but the browser did not actively restore the live tile pane. A bounded OpenStreetMap probe now restores the pane and emits a map-specific recovery event.

### WordPress proxy fragility

Direct WordPress shortcode panels depended on a single REST proxy request. They now retry transient failures and can use a six-hour session-scoped last-known-good response after a prior verified success.

## Recovery architecture

1. Eligible request: same-origin GET request for public JSON.
2. Network attempt with a 12-second timeout.
3. Up to three total attempts with 600 ms and 1,400 ms backoff.
4. Service-family failure count and circuit isolation after three failed request cycles.
5. Last-known-good response when a verified browser cache entry remains inside its service TTL.
6. Automatic 30-second service probe while degraded.
7. Circuit closure and one-time refresh of the active workspace after recovery.

Mutation requests, cross-origin requests, exports, and diagnostic probes are excluded.

## Map recovery architecture

- Leaflet unavailable: first-party static geographic grid.
- CARTO unavailable: OpenStreetMap fallback.
- OpenStreetMap unavailable: hide failed tiles and retain overlays on the grid.
- OpenStreetMap restored: reveal the tile pane, redraw the layer, and report the named map as recovered.
- Imagery unavailable: keep other layers active and report imagery degradation separately.

## Operational limitations

- A last-known-good response exists only after that URL has loaded successfully in the browser.
- Recovered data may be stale and must be interpreted using the included stale-age headers.
- Automatic recovery does not guarantee third-party availability.
- Browser screenshot validation was not performed in this container; browser behavior is covered by source contracts and automated regressions.
