# Site Intelligence v3.23.6.3

## Performance and Offline Recovery

This release improves the time to a useful map and makes browser recovery deterministic across route changes, slow public endpoints, offline sessions, and service-worker upgrades.

### Runtime changes

- Measures first useful map only after a visible map has usable dimensions and rendered geography, tiles, or evidence.
- Measures active-route interactivity separately from generic page load.
- Coalesces duplicate same-origin public GET requests.
- Cancels requests owned by a workspace after the user navigates away.
- Marks inactive routed surfaces inert and excludes them from active presentation work.
- Uses a bounded 5.5-second network timeout for public data.
- Labels service-worker fallback responses as `offline-cached` with a cache age.
- Uses cache-first delivery for release-pinned JavaScript, CSS, geography, and images.
- Uses network-first delivery for app HTML and changing public data.
- Retains local Natural Earth geography when external imagery or tiles are unavailable.
- Removes old Site Intelligence cache generations during service-worker activation.
- Performs one controlled reload after a new service worker takes control.
- Preserves the WordPress host-isolation boundary; app recovery code is packaged but not executed in the host document.

### Public contract

`GET /public/performance-offline`

The contract discloses budgets, loading policy, cache strategies, offline states, recovery behavior, measurement requirements, and limitations.

### Boundaries

Cached public data may be stale. The offline shell does not imply current data, and external map imagery is not guaranteed offline.
