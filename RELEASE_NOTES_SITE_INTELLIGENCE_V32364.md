# Site Intelligence v3.23.7 — Production Soak, Route Stability, and Service-Worker Closure

This patch removes network access and service-worker lifecycle changes from the critical application-opening path. The application shell now opens first, while imagery, event, country, and requested-workspace data hydrate independently in the background.

## Changes

- Opens the usable application shell before optional public-data requests complete.
- Replaces blocking sequential startup with background `Promise.allSettled` hydration.
- Prevents the existing service-recovery layer and application retry helper from multiplying retries.
- Reduces recoverable request attempts to two bounded 6.5-second attempts.
- Serializes route transitions and retains only the latest pending route selection.
- Routes service-recovery refreshes through the same transition queue.
- Removes automatic service-worker reloads on `controllerchange`.
- Stops the service worker from calling `skipWaiting()` during installation.
- Defers service-worker registration until after window load and browser idle time.
- Loads the complete WordPress application iframe eagerly with high fetch priority.
- Adds `/public/startup-stability`, runtime-health enforcement, and a mandatory production-soak browser gate.

## Boundary

The shell opening does not imply that every upstream public data source is available. Each workspace continues to disclose limited, cached, stale, or unavailable data independently.

## Validation correction

- Resolves `ContentRegistry` data paths from the packaged backend rather than relying on the shell working directory.
- Prevents explicit pages such as `/publications/` from being downgraded to inferred mappings during installer validation.
- Adds an arbitrary-working-directory regression test for the release installer path.

