# Site Intelligence v2.12.1 Installation and Test Guide

## 1. Install the repository update

Run the supplied installer from `~/Downloads`. It creates a safety branch and archive, resets the local repository to `origin/main`, overlays the v2.12.1 release, installs an isolated Python environment from `backend/requirements-dev.txt`, including Starlette’s `httpx2` TestClient dependency, runs the complete regression and syntax suite, verifies release contracts and file hashes, packages the WordPress plugin, commits, rebases, and pushes.

## 2. Verify Render

After Render deploys, confirm:

- `/health` reports `2.12.1`.
- `/public/build-info` reports backend and expected WordPress plugin version `2.12.1`.
- `/public/offline-experience/diagnostics` returns `ok: true`.
- `/public/offline-experience/reliability` reports the v2.12.1 cache generation and embed contract.
- `/app/service-worker.js` returns `Cache-Control: no-cache, no-store, must-revalidate` and `X-SC-Cache-Generation: scsi-v2.12.1`.

## 3. Update WordPress

Upload and activate the v2.12.1 WordPress plugin ZIP. Clear WordPress, Cloudflare, and browser caches. Then test the Site Intelligence page while logged out.

## 4. Browser and mobile checks

1. Open `/app/?view=experience` and clear the offline cache once.
2. Reload and confirm the PWA shell is available.
3. Open a WordPress embed at 320, 375, 390, 768, and 1024 CSS pixels.
4. Change workspaces inside the iframe and confirm its height updates without clipping.
5. Temporarily disable the network and confirm the cached shell or offline page appears with a stale-data warning.
6. Restore the network and confirm the current release replaces the offline state.

Cached records are not guaranteed current. External tiles, imagery, fonts, and third-party libraries may still require a live network connection. Automated accessibility checks remain engineering diagnostics, not certification.
