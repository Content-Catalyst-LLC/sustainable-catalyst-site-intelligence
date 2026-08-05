# Site Intelligence v3.22.9 Installation and Production Test

## Required deployment order

1. Put the v3.22.9 release bundle and macOS deployment installer in `~/Downloads`.
2. Run the Terminal commands included with the release.
3. Allow deterministic source validation, all inherited tests, and the Chromium cartography smoke test to complete.
4. Allow the installer to synchronize the exact release tree with the GitHub `main` branch and create the release and rollback tags.
5. Wait for Render to report the expected version, release ID, branch, and exact commit.
6. Allow the live gate to retrieve the current app shell, vector-cartography JavaScript, local geography, and runtime-health response.
7. Upload the WordPress ZIP only after Terminal prints the final success message and exact plugin path.

## WordPress installation

Open **WordPress → Plugins → Add New → Upload Plugin**, select the v3.22.9 WordPress ZIP printed by the installer, and replace the installed Site Intelligence plugin.

Then:

- purge WordPress and host page caches;
- purge any active CDN cache;
- unregister older Site Intelligence service workers in browser developer tools;
- clear Site Intelligence site storage once;
- reopen the page in an Incognito window.

## Production visual checklist

### Release parity

- The embedded app and Site Health report `3.22.9`.
- The release identifier is `site-intelligence-v3.22.9`.
- WordPress and Render agree on the release.

### Overview map

- The map has a controlled desktop height rather than a shallow or collapsed panel.
- The giant black circular mask is absent.
- Water is deep slate rather than pure black.
- Country and coastline geometry remains visible before live data finishes loading.
- Country labels, scale, coordinate readout, and zoom/home controls are visible.
- Satellite imagery appears above, but does not erase, the base geography.
- Event markers and selected evidence remain visually distinct.

### Global Conditions

- The left-navigation button opens Global Conditions.
- The map initializes after repeated route changes.
- Base geography remains visible when imagery is unavailable.
- The current imagery or thematic layer can be changed without blanking the map.

### Other map workspaces

Open Events, Earth, Spatial, Economics, Humanitarian, Resources, Science, Law, Dossiers, Country, Compare, and Themes. Confirm each visible map:

- has non-zero width and height;
- retains local country and coastline geography;
- shows labels appropriate to the zoom level;
- preserves available evidence overlays;
- supports drag, wheel zoom, keyboard controls, and home reset;
- does not become blank when an optional raster source fails.

### Health semantics

- A local-vector map is treated as operational.
- A vector-plus-satellite map is treated as operational.
- An imagery outage is reported as an imagery limitation, not an application-wide failure.
- Hidden map workspaces do not count against the visible health state.
- Recovered faults no longer remain active solely because they occurred earlier in the session.

## Rollback

The deployment receipt records the rollback tag created immediately before v3.22.9. Use the exact tag and commit printed by the installer if production must be restored. Keep the WordPress plugin and Render backend on matching release versions.
