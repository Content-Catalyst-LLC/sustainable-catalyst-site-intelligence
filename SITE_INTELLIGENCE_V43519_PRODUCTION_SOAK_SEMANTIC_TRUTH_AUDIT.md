# Site Intelligence v4.35.22 — Production Soak & Semantic Truth Audit

## Production failure/recovery matrix
1. Steady upstream success.
2. HTTP 429 with Retry-After honored.
3. HTTP 503 followed by bounded recovery.
4. Explicit stale-cache fallback after upstream failure.
5. Circuit breaker opens after repeated failure.
6. Open circuit transitions through recovery and closes after success.
7. Twenty-four alternating provider-flap cycles without corrupting control-plane state.
8. Missing credentials degrade the affected connector profile without blocking a healthy first-party release.

All eight scenarios are deterministic, execute in process, and use the production resilient-transport implementation with fake upstream responses and a fake clock. They make no real provider network calls.

## Semantic truth boundary
`transport_state` describes how data was retrieved or served (`live`, `cached`, `stale`, unavailable). It is not the evidence class.

`presentation_state` describes what the observation is allowed to mean. World Bank annual country observations are classified as `harmonized-benchmark`; a fresh retrieval does not convert them into live operational conditions.

Structural electricity access cannot substitute for current electricity availability, outage status, service hours, grid reliability, or generator dependence. Structural drinking-water access cannot substitute for current availability, pressure, continuity, quality, or household service conditions.

## Palestine precedence
For supported exact-concept national statistical evidence, the source registry puts the Palestinian Central Bureau of Statistics first and retains World Bank as harmonized comparison/fallback. Operational electricity, health-system, water-service, and similar current-condition evidence remain separate concepts and require appropriate operational/sector sources; v4.35.22 does not claim connectors that are not yet implemented.

## Release policy
The deterministic first-party soak is release-blocking. A separate live-provider operator soak is not. This preserves the ability to verify real post-deployment behavior without allowing a transient external outage to invalidate an otherwise healthy Site Intelligence release.
