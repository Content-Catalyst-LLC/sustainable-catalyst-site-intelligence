# Site Intelligence v3.22.7 installation and testing

## Local validation

From the extracted repository root:

```bash
bash verify_site_intelligence_v3_22_3_macos.sh
```

The verifier checks release identity, compiles Python, parses JSON, validates JavaScript and WordPress PHP when those runtimes are available, and runs the full pytest suite.

## WordPress

Upload `sustainable-catalyst-site-intelligence-v3.22.7-wordpress-plugin.zip` through **Plugins → Add New → Upload Plugin**, replace the installed version, and purge WordPress, host/CDN, and browser caches.

## Production checks

1. Open the standalone application and select **Site health**.
2. Confirm Core, Geospatial, Country, Indicators, Research, and Operations show ready or explain a degraded state.
3. Open every map workspace and confirm the map-by-map list names the active container.
4. Temporarily block a public JSON request and confirm retries occur without disabling unrelated workspaces.
5. Restore the request and confirm the active workspace refreshes once.
6. Temporarily block map tiles and confirm verified overlays remain on the geographic grid.
7. Restore map tiles and confirm the affected map reports recovered.
8. Confirm WordPress shortcode panels continue from a prior session response during a transient proxy failure.
