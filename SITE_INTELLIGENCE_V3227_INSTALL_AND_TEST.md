# Site Intelligence v3.22.7 Installation and Production Test

1. Place the v3.22.7 release bundle and macOS installer in `~/Downloads`.
2. Run the provided Terminal command.
3. Allow the installer to validate the package twice, push the exact Git tree to GitHub, and verify the Render release gate.
4. Upload the printed WordPress ZIP only after Terminal confirms GitHub, Render, and the installation gate are synchronized.
5. Purge WordPress, hosting, CDN, service-worker, and browser caches.

## Required production checks

- Open `/app/?view=overview` and confirm the live map appears without a request to `unpkg.com`.
- Drag the map, use wheel or `+`/`−` controls, and activate a marker popup.
- Select **Global conditions** from the left navigation and confirm the workspace opens.
- Open Global Conditions directly with `/app/?view=global` and confirm mapped records or a clearly labeled empty-data state.
- Open Earth, Spatial, Events, Economics, Humanitarian, Resources, Dossiers, Country, Compare, and Themes; confirm each map container initializes.
- Open Site Health. A first-party interactive map should be **Ready**, and hidden workspaces should not lower overall health.
- Confirm the WordPress release-status surface reports backend v3.22.7 and release id `site-intelligence-v3.22.7`.
