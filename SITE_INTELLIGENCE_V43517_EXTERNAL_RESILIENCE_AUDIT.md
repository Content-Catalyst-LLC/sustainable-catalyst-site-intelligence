# Site Intelligence v4.35.21 — External Resilience Audit

## Objective
Prevent upstream rate limits, timeouts, temporary errors, and repeated provider failures from cascading into broken Site Intelligence workspaces.

## Control-plane result
The resilience layer is first-party, deterministic at readiness, network-free, and non-blocking with respect to provider health. It exposes operational telemetry without exposing request URLs or secret material.

## Retry contract
Retryable statuses are restricted to `408`, `425`, `429`, `500`, `502`, `503`, and `504`. GET is retry-safe by default. POST is single-attempt unless the connector explicitly marks the request read-safe. Authentication/client failures such as 401 are not retried into a circuit outage.

## Retry-After contract
`Retry-After` is accepted as either delay-seconds or an HTTP date. When present on a retryable response it supersedes the local exponential-backoff calculation, subject to a bounded safety cap.

## Cache contract
Fresh cache hits can suppress duplicate upstream requests. Cache keys are SHA-256 digests of request material and are never surfaced in public telemetry. The process-local cache is bounded and evicts oldest entries.

Stale-if-error is opt-in. The transport returns explicit metadata (`stale=true`, `cache_status=stale-error` or `stale-circuit`) whenever stale content is served. Existing legacy raw-payload helpers use fresh-cache reuse only, preventing silent stale-data substitution.

## Circuit-breaker contract
Repeated retryable upstream/network failures increment a provider-local consecutive-failure counter. The default threshold is three. An open circuit rejects further upstream calls until its open interval expires; stale fallback can be used only when explicitly enabled by the caller.

## Pacing contract
Provider profiles impose conservative minimum request intervals to reduce accidental request bursts. These intervals are client-side safeguards and are not represented as authoritative provider quotas. Upstream response headers remain authoritative for retry timing.

## Provider profiles
Profiles are present for AirNow, EIA, Overpass, World Bank/WITS, NASA CMR, USGS Water, NOAA, EPA, Copernicus/ECMWF, plus a conservative default profile.

## Integrated code paths
- `authoritative_connectors_v4353.py`
- `authoritative_connectors_v4354.py`
- `authoritative_connectors_v4355.py`
- `authoritative_connectors_v43511.py` XML/text helper
- `unified_live_events.py`
- `connectors/advanced_external.py`
- `connectors/external_data.py` JSON client

## Public routes
- `/public/external-resilience`
- `/public/external-resilience/readiness`
- `/public/external-resilience/providers`

## Deployment boundary
`/public/external-resilience/readiness` is now a first-party deployment invariant. It performs no provider calls. An unavailable NOAA, NASA, EPA, USGS, EIA, World Bank, Copernicus, or other source cannot by itself fail a valid deployment.
