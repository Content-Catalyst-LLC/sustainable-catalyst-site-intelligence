# Site Intelligence v4.35.20 — Live-Operation Stress, Semantic Truth & Recovery Integrity

## Release objective
Prove that Site Intelligence remains usable and truthful while external providers slow down, rate-limit, fail, flap, recover, or lack credentials—and prevent transport freshness from being misrepresented as evidence freshness or current operational reality.

## Delivered
- Added an application-level deterministic production-soak control plane using the same resilient transport exercised by authoritative connectors.
- Added eight release-blocking fault/recovery scenarios: steady success, 429 + Retry-After, 503 recovery, explicit stale fallback, circuit opening, circuit recovery, 24-cycle provider flapping, and missing-credential degradation.
- Kept the separate live-provider operator soak explicitly non-blocking for release readiness.
- Added evidence presentation classes: LIVE / OPERATIONAL, CURRENT OFFICIAL, ANNUAL STATISTIC, MODELED ESTIMATE, HARMONIZED BENCHMARK, HISTORICAL, and UNAVAILABLE.
- Separated `transport_state` from `presentation_state` in canonical country evidence and the public country workspace.
- World Bank annual country indicators now present as HARMONIZED BENCHMARK rather than inheriting a `live` label merely because retrieval succeeded.
- Added Palestine source-priority rules that put PCBS first for supported exact-concept statistical evidence while retaining World Bank as a harmonized comparison/fallback.
- Added explicit structural/operational warnings for electricity access and basic drinking-water access.
- Added the soak status to Sources alongside connector, credential, external-resilience, canonical Truth, and 35-route browser readiness.

## Release invariants
- Deterministic soak scenarios: 8 / 8 required.
- Provider flapping exercise: 24 cycles.
- Registered workspace routes: 35 across 6 primary areas.
- Public connector interfaces: 50; machine-readable source registrations: 112.
- Release-readiness soak performs no provider network calls.
- Real upstream provider health remains non-blocking for release readiness.
- A successful HTTP response, cache hit, or stale fallback cannot by itself classify an annual/statistical observation as live operational evidence.
- World Bank remains available for international comparison and fallback; the semantic fix does not discard it.

## Validation
The release is gated by the complete deterministic pytest suite, the 14-case v4.35.20 fault-injection/semantic regression layer, immutable repository manifest, JSON/GeoJSON parsing, JavaScript/PHP syntax validation, static security scanning, the inherited 35-route desktop/mobile/iframe browser audit, canonical evidence/Truth readiness, external-resilience readiness, and the v4.35.20 release contract.
