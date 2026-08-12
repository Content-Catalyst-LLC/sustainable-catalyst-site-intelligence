# Site Intelligence v4.35.19 — Rate Limits, Retries, Caching, Backoff & Circuit Breakers

## Purpose
Make Site Intelligence remain usable when authoritative upstream APIs are slow, rate-limited, temporarily unavailable, or intermittently failing.

## Added
- Shared process-local external resilience transport for authoritative read-oriented connectors.
- Bounded retries for GET/read-safe requests on 408, 425, 429, 500, 502, 503, and 504.
- `Retry-After` support for server-directed retry timing.
- Bounded exponential backoff with small deterministic jitter.
- Conservative provider pacing profiles. These are Site Intelligence client safeguards, not assertions about upstream contractual quotas.
- Fresh-response cache reuse with a bounded process-local LRU cache.
- Explicit opt-in stale-if-error support. Stale responses are never silently labeled fresh.
- Per-provider circuit breakers with closed/open/half-open state.
- Secret-safe provider telemetry: request, retry, cache, stale, failure, circuit, and pacing counts without URLs, credentials, hashes, or masked secret fragments.
- New public control-plane routes:
  - `/public/external-resilience`
  - `/public/external-resilience/readiness`
  - `/public/external-resilience/providers`
- Source & Methodology Studio External Resilience panel.
- Deployment verification now requires the first-party resilience control plane while continuing to exclude upstream provider health from release blocking.

## Integrated request paths
The shared resilience layer now covers the v4.35 authoritative connector helper chain, unified live-event JSON requests, the Advanced External Data hub, and the core External Data hub JSON client. This gives the majority of current live authoritative HTTP JSON requests one consistent retry/cache/circuit policy without rewriting every domain connector.

## Integrity boundaries
- A cached response inside its TTL remains a fresh cache hit.
- A stale response can only be returned through an explicit stale-if-error request path and carries `stale=true` transport metadata.
- Legacy raw-payload helpers do not silently receive stale payloads.
- 401/403-style authentication failures are not treated as provider outages and do not trip a provider circuit breaker.
- POST requests are not retried unless the caller explicitly marks the operation read-safe/idempotent.
- HTTP is rejected for authoritative-source transport; HTTPS is required.
- Readiness performs no external network calls.
- Provider failures remain operational source health, not deployment blockers.

## Default client policy
- Maximum attempts: 3
- Base backoff: 250 ms
- Maximum exponential backoff: 4 seconds
- Circuit opens after 3 consecutive retryable failures
- Circuit open interval: 60 seconds
- Maximum process-local cache entries: 256

Provider-specific cache/pacing profiles exist for AirNow, EIA, Overpass, World Bank/WITS, NASA CMR, USGS Water, NOAA, EPA, and Copernicus/ECMWF. Exact provider quotas are not hard-coded unless an upstream response communicates them; `Retry-After` takes precedence when supplied.

## Configuration
Optional tuning variables:

```text
SC_SI_EXTERNAL_RESILIENCE_ENABLED=true
SC_SI_EXTERNAL_RETRY_ATTEMPTS=3
SC_SI_EXTERNAL_BACKOFF_BASE_MS=250
SC_SI_EXTERNAL_BACKOFF_MAX_SECONDS=4
SC_SI_EXTERNAL_CIRCUIT_FAILURE_THRESHOLD=3
SC_SI_EXTERNAL_CIRCUIT_OPEN_SECONDS=60
SC_SI_EXTERNAL_CACHE_MAX_ENTRIES=256
```

No new credential or paid infrastructure dependency is introduced.
