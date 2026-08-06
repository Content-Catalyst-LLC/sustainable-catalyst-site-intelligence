# v3.23.6.3 Bootstrap Recovery Audit

## Confirmed v3.23.6 defect

The v3.23.6 package contained three service-worker registration paths:

1. `backend/public_app/assets/app.js`
2. `backend/public_app/assets/performance-offline-v3236.js`
3. `backend/public_app/assets/experience-v2120.js`

It also registered more than one controller-change recovery path. In addition, responsive height listeners at the end of `app.js` referenced the closure-private `reportHeight` function from global scope.

## v3.23.6.3 ownership contract

`bootstrap-v32361.js` is now the only file under `backend/public_app/assets` containing either:

- `serviceWorker.register`
- a `controllerchange` listener

The bootstrap owner:

- registers `/app/service-worker.js` after window load;
- never waits for service-worker readiness before revealing the app;
- activates a waiting worker through one message path;
- uses a release-specific, session-scoped reload guard;
- fails open when registration is unsupported, blocked, or rejected;
- opens a limited workspace after a bounded startup deadline.

## Application recovery

The complete asynchronous `init()` function is now called through `startApplication()`. Errors before the previous inner network `try` block are caught, logged, and converted into a visible limited workspace.

The application dispatches `scsi:application-ready`. The bootstrap listens for that event, hides the launch screen, records the visible startup state, and reports readiness to an iframe parent.

## Browser validation

Two Chromium harnesses are included:

- `scripts/browser_smoke_v32361.py` validates isolated worker and deadline behavior.
- `scripts/browser_full_startup_v32361.py` loads the complete production HTML, exact startup assets, and full `app.js` against fresh, current, older, disabled, failed-worker, failed-data, and iframe conditions.

Managed Chromium blocks localhost navigation in this environment, so the full-shell harness loads the exact production document and first-party assets inline. This limitation is explicit and does not affect the source or package tests.
