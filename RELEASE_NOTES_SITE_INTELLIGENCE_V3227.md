# Site Intelligence v3.22.7

## Production Map Runtime and Navigation Repair

This release repairs the production map and sidebar failures reported after v3.22.6.

### Repairs

- Makes **Global Conditions** a permanent, server-rendered sidebar route instead of inserting its button after navigation listeners have already been attached.
- Replaces per-button startup bindings with delegated sidebar routing so present and future workspace buttons remain functional.
- Removes blocking Leaflet CSS and JavaScript requests from `unpkg.com` during standalone application startup.
- Introduces a first-party interactive geographic runtime with pan, wheel zoom, keyboard navigation, reset controls, markers, GeoJSON lines and polygons, popups, bounds fitting, and synchronized map events.
- Uses the same first-party map runtime in the WordPress plugin before geospatial shortcodes initialize.
- Keeps hidden map workspaces out of the overall health calculation.
- Treats the functioning first-party interactive runtime as a healthy production mode rather than a degraded fallback.
- Preserves explicit degradation reporting for actual visible map failures, imagery failures, endpoint failures, and browser errors.
- Aligns the backend, application shell, service worker, WordPress plugin, Render release identifier, deployment gate, and promotion scripts to v3.22.7.

### Release boundary

The first-party runtime provides interactive geographic context and evidence overlays without third-party map code. Raster imagery remains dependent on the availability and terms of its registered public tile source; failure of a raster source does not disable the map or its verified vector evidence.
