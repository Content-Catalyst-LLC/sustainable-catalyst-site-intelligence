# Sustainable Catalyst Site Intelligence v3.22.4

## Self-Healing Data Services, Map Recovery, and Fault Isolation

This release builds on v3.22.2 diagnostics by adding automatic, bounded recovery. It keeps transient service failures local to the affected data family, preserves previously verified public JSON when appropriate, and reports each map surface independently.

### What changed

- Added `/public/runtime-recovery`, a public-safe local recovery contract.
- Added `service-recovery-v3224.js` before application modules.
- Added three-attempt retries for timeouts, network errors, HTTP 408/425/429, and HTTP 5xx gateway/service failures.
- Added separate circuits for core, geospatial, country, indicator, research, and operations services.
- Added a 30-second circuit cooldown and automatic recovery probes.
- Added marked last-known-good responses with stale age and release headers.
- Added service-worker recovery response headers so cached continuity is never mistaken for live network freshness.
- Added one-time active-workspace refresh after a degraded service returns.
- Added map surface registration, container-level state, recovery scheduling, and map-specific retry hooks.
- Added OpenStreetMap availability probes that restore the live tile pane after a grid-overlay fallback.
- Added WordPress proxy retries and session-scoped last-known-good responses.
- Added service and map recovery details to the Site Health console and copyable support report.

### Safety and data boundaries

- Only same-origin public GET JSON requests are eligible.
- Mutation requests and cross-origin requests are never retried or cached by the recovery runtime.
- Runtime diagnostic probes explicitly bypass recovery caches.
- Cached responses are used only after a prior successful browser response and are marked as recovered/stale.
- Service circuits are isolated by data family; one circuit cannot disable another.
- The runtime performs no credential storage, visitor profiling, source mutation, or third-party write.

### Validation

- 862 automated tests passed.
- JavaScript syntax validation passed for all packaged JavaScript files.
- Python modules compiled successfully.
- All packaged JSON files parsed successfully.
- WordPress PHP passed syntax validation.
- Critical application, recovery, map, and asset endpoints returned HTTP 200 in local smoke tests.
