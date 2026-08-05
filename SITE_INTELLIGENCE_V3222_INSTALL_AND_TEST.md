# Site Intelligence v3.22.7 Installation and Test Guide

## Recommended path

Use the supplied macOS installer from Terminal. It verifies bundle checksums, extracts the repository, creates an isolated Python environment, installs dependencies, validates source files, and runs the full test suite.

```bash
cd ~/Downloads

INSTALLER="$(ls -t install_and_validate_site_intelligence_v3_22_2_macos*.sh | head -1)"
BUNDLE="$(ls -t sustainable-catalyst-site-intelligence-v3.22.7-release-bundle*.zip | head -1)"

chmod +x "$INSTALLER"
bash "$INSTALLER" "$BUNDLE"
```

Expected final result:

```text
854 passed
SUCCESS: Site Intelligence v3.22.7 passed local validation.
```

## WordPress update

1. Open WordPress administration.
2. Go to Plugins → Add New → Upload Plugin.
3. Upload `sustainable-catalyst-site-intelligence-v3.22.7-wordpress-plugin.zip`.
4. Replace the existing plugin when prompted.
5. Purge WordPress, hosting, CDN, and browser caches.

## Production checks

1. Open the standalone Site Intelligence application.
2. Confirm the Site Health control appears at the lower-right.
3. Open it and run checks.
4. Confirm Service, Build, Runtime, Geospatial, and Spatial report Pass.
5. Open each map-backed workspace.
6. Confirm markers or evidence overlays remain visible if a basemap is unavailable.
7. Test the WordPress embed in a logged-out browser.
8. Confirm the browser console has no uncaught errors.
9. Copy the health report if any panel remains degraded.

## Important boundary

The local test suite verifies package and runtime contracts. It cannot guarantee current availability of third-party public APIs, CARTO, OpenStreetMap, satellite imagery, or hosting-edge configuration.
