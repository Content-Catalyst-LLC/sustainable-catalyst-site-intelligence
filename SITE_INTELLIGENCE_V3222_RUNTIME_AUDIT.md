# Site Intelligence v3.22.4 Runtime Audit

## Audit objective

Determine whether Site Intelligence can expose actionable production truth when a map, panel, endpoint, browser dependency, or upstream tile service fails.

## Findings carried forward from v3.22.1

The previous repair established three important foundations:

1. Leaflet failure no longer prevents verified spatial overlays from rendering.
2. CARTO basemap failure can fall back to OpenStreetMap.
3. approved WordPress embeds no longer receive a contradictory `X-Frame-Options` header.

Those changes improved continuity, but operators still lacked a single place to see which layer had failed.

## v3.22.4 remediation

### 1. Local runtime contract

The new `/public/runtime-health` endpoint evaluates only first-party state. It verifies version alignment, the standalone app shell, required runtime assets, script order, offline-shell inclusion, map-container declarations, and embed policy without making outbound requests.

### 2. Browser health tray

The standalone app now includes a Site Health tray. It checks the service, build, runtime, geospatial, and spatial endpoints with bounded timeouts. It also reports service-worker state, initialized maps, visible maps, map modes, runtime events, script errors, and unhandled promise rejections.

### 3. Fault-domain separation

The health tray distinguishes:

- Local package or asset failure
- Backend endpoint failure
- Browser offline state
- Leaflet unavailable
- CARTO tile degradation
- OpenStreetMap tile degradation
- Satellite or specialist imagery degradation
- Script or promise failure
- Offline-shell/service-worker state

### 4. OpenStreetMap failure continuity

If CARTO fails, the runtime still attempts OpenStreetMap. If OpenStreetMap also fails, the failed tile pane is hidden and the first-party geographic grid remains visible behind verified markers, lines, and polygons.

### 5. Supportability

The user can copy a JSON support report containing release, page, endpoint timing, map modes, visible map containers, recent events, recent faults, service-worker state, and user-agent context. The report contains no credentials or private upstream payloads.

## Remaining production validation

The release should still be checked on the deployed domain in a normal browser because this build environment cannot prove real third-party tile rendering, WordPress theme interactions, content-security-policy behavior at the hosting edge, or mobile viewport behavior under the production cache stack.
