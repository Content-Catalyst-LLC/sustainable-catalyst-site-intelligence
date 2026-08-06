# Site Intelligence v3.23.6.1 performance and offline audit

## Completion target

The release targets operational performance and recovery rather than new analytical features.

## Implemented controls

1. **First useful map measurement** — requires a nontrivial visible map surface and rendered geography, tiles, canvas, or evidence.
2. **Route request ownership** — same-origin public requests are associated with the active route and aborted after route departure, except for persistent release and health contracts.
3. **Duplicate request coalescing** — identical in-flight public GET requests share one network operation.
4. **Critical-shell installation** — service-worker installation caches only the application shell, map runtime, local world geography, and recovery runtime needed for first use.
5. **Route asset caching** — noncritical modules are cached on first browser use rather than blocking installation.
6. **Immutable asset strategy** — release-pinned code, styles, geography, icons, and fonts use cache-first delivery.
7. **Changing-data strategy** — public API responses use network-first delivery with a bounded timeout and cached fallback.
8. **Truthful fallback headers** — recovered responses include `X-SCSI-Data-State: offline-cached`, stale age, recovery reason, and release identity.
9. **Release migration** — activation removes earlier `scsi-` cache generations and claims open application clients.
10. **Controlled reload** — browser controller changes allow one release-scoped reload, guarded by session state.
11. **WordPress isolation** — v3.23.6.1 assets are available to the embedded app but are not enqueued as application runtimes in the WordPress host page.

## Operational budgets

- First useful map: 3,500 ms
- Active route interactive: 1,800 ms
- Public API network timeout: 5,500 ms
- Long task threshold: 50 ms
- Maximum cached public responses: 160
- Maximum immutable entries: 180
- Cached public fallback age: 24 hours

These are operational targets and do not constitute third-party performance certification.
