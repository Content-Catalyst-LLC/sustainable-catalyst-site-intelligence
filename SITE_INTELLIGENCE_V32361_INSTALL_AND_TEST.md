# Install and test Site Intelligence v3.23.6.3

1. Download the v3.23.6.3 release bundle and macOS installer into `~/Downloads`.
2. Run the Terminal block supplied with the release.
3. Wait for the installer to verify checksums, run the complete test suite twice, publish GitHub refs, and verify Render.
4. Install the WordPress ZIP only after the live release gate reports success.
5. Purge WordPress, hosting, and CDN caches.
6. Open Site Intelligence in a private browser window.

## Visible acceptance checks

- The launch overlay disappears within nine seconds.
- A limited workspace appears when optional services are unavailable.
- Reloading with an existing worker does not create a reload loop.
- The map retains non-zero dimensions.
- The WordPress host page does not display application diagnostics above the iframe.
- `/public/runtime-health`, `/public/performance-offline`, and `/public/bootstrap-recovery` report v3.23.6.3.

## Emergency browser reset

When upgrading from the failed v3.23.6 session, unregister the old Site Intelligence service worker and clear site data once. v3.23.6.3 then owns subsequent updates through the single bootstrap path.
