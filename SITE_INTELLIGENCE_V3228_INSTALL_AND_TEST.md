# Site Intelligence v3.22.8 Installation and Production Test

## Required order

1. Place the v3.22.8 release bundle and macOS installer in `~/Downloads`.
2. Run the Terminal command provided with the release.
3. Allow both deterministic validation passes to complete.
4. Allow the installer to push the exact Git tree and release tags to GitHub.
5. Wait for Render verification of the release gate, exact commit, live app shell, map-engine asset, world-boundary asset, and runtime health.
6. Upload the WordPress ZIP only after the installer prints the success message and ZIP path.

## WordPress installation

In WordPress, open **Plugins → Add New → Upload Plugin**, select the printed v3.22.8 WordPress ZIP, and replace the installed Site Intelligence plugin.

After replacement:

- purge WordPress and host page caches;
- purge any active CDN cache;
- unregister older Site Intelligence service workers in browser developer tools;
- clear site storage once;
- reopen Site Intelligence in an Incognito window.

## Production browser checklist

### Release parity

- The embedded app and Site Health report version `3.22.8`.
- The release identifier is `site-intelligence-v3.22.8`.
- The WordPress release surface and Render release gate agree.

### Overview and Global Conditions

- Overview displays recognizable country/coastline geography before or beneath live data.
- Global Conditions opens from the left navigation.
- The Global Conditions map displays local geography even if external tiles are blocked.
- Navigation remains functional after switching repeatedly between Overview and Global Conditions.

### Map workspaces

Open Events, Earth, Spatial, Economics, Humanitarian, Resources, Science, Law, Dossiers, Country, Compare, and Themes. Confirm each visible map:

- has non-zero height and width;
- displays country/coastline geography;
- retains available evidence overlays;
- supports drag and zoom interaction;
- does not become blank when an optional imagery source fails.

### Site Health

- A local-vector map is reported as ready.
- Tile or imagery failure appears as imagery limited, not application degraded.
- Hidden map workspaces are excluded from the current health result.
- Recovered endpoint or browser errors are marked resolved and no longer count as active faults.

## Rollback

The deployment receipt records the rollback tag created before v3.22.8. Use the exact tag and commit printed by the installer if production must be restored. Do not reinstall an older WordPress plugin without restoring the matching backend release.
