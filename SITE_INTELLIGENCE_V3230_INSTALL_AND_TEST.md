# Site Intelligence v3.23.0 Installation and Test Guide

## Required order

1. Run the macOS deployment installer.
2. Allow it to validate the release twice.
3. Allow it to commit and push the exact release to GitHub.
4. Wait for Render to verify version, release ID, branch, commit, app shell, map engine, cartographic workspace, local geography, and runtime health.
5. Install the WordPress ZIP only after the installer prints the final success message.

## WordPress installation

In WordPress, open **Plugins → Add New → Upload Plugin**, choose the printed v3.23.0 WordPress ZIP, and replace the current plugin. Purge WordPress, host, CDN, and browser caches afterward.

## Production browser checks

- Overview opens as a bounded map-first workspace.
- The page does not continue through every hidden module.
- The evidence drawer opens, closes, and preserves the map width after resize.
- Selecting Kenya frames East Africa rather than the global 0°N/0°E view.
- Global Conditions, Spatial, Economics, Science, Humanitarian, and other navigation entries display only their active routed workspace.
- The primary map is at least 520 pixels high on desktop.
- Country boundaries or live map tiles are visible.
- Map controls, scale, coordinates, and evidence overlays remain usable.
- The visible-map status reports `ready` only for a rendered map.
- The WordPress host page retains normal scrolling and theme navigation.
