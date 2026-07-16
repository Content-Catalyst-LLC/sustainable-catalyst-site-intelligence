# Sustainable Catalyst Site Intelligence v2.12.1

## Production Offline, Mobile, and Embed Reliability Patch

v2.12.1 hardens the v2.12.0 installable and mobile delivery layer for production use.

### Service worker and offline delivery

- Individual optional shell-asset failures no longer abort the entire service-worker installation.
- Service-worker scripts are fetched outside the browser HTTP cache and waiting updates activate immediately.
- Caches are release-scoped, and caches from previous Site Intelligence releases are removed during activation.
- Public-data fallbacks are capped at 120 entries and expire after 24 hours by default.
- Navigation uses preload and a defined fallback chain: live response, exact cached page, cached application shell, then offline page.
- The Experience workspace and offline page can clear corrupted or stale Site Intelligence caches.

### Mobile and WordPress embeds

- All Site Intelligence iframe wrappers now use one responsive host controller.
- Resize messages must match both the expected backend origin and the iframe's source window.
- Desktop and mobile minimum heights are enforced, with a 2,600-pixel safety maximum.
- Delayed embeds expose an explanatory state and a permanent new-tab fallback.
- Safe-area, reduced-motion, forced-color, and full-width mobile behavior are preserved.

### Installer and validation compatibility

- The release installer now installs `backend/requirements-dev.txt` rather than the production-only requirements file.
- `httpx2` is explicitly included for Starlette TestClient compatibility on Python 3.14 and current Python 3.13 environments.
- Test-only dependencies remain outside the Render production dependency set.

### Release-package integrity

- Removed the generated `backend/data/country_last_known_good.json` runtime cache from the distributable repository and release manifest.
- Validation redirects writable country-cache and Platform Core queue paths to an isolated temporary directory.
- The immutable release manifest now covers 344 source files and remains unchanged after all 395 tests run.

### Release alignment

- Backend, public application, service worker, manifest, WordPress plugin, response headers, documentation, and release diagnostics report v2.12.1.
- Application HTML and the worker script use strict revalidation/no-store policies to prevent stale releases.
- `/public/offline-experience/reliability` publishes the production delivery contract.

No account system, paid API, paid cache, telemetry vendor, hosted profile, or new server is required.
