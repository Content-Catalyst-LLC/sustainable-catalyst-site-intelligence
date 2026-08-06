# Install and test Site Intelligence v3.23.6.3

1. Download the release bundle and macOS installer into `~/Downloads`.
2. Run the installer with the bundle path.
3. The installer verifies flat or uniquely nested bundle layouts and checks `SHA256SUMS.txt`.
4. It creates an isolated Python environment and runs deterministic validation twice.
5. It pushes the verified repository to GitHub and waits for the exact Render commit.
6. The live gate verifies the app shell, performance runtime, service worker, public performance contract, maps, analytical workflows, browser reliability, production truth, and runtime health.
7. Install the WordPress ZIP only after Terminal reports success.
8. Purge WordPress, hosting, CDN, and browser caches, then open a new Incognito window.

The performance status should progress from **Preparing useful map** to **Map ready**. Offline cached evidence must remain labeled as potentially stale.
