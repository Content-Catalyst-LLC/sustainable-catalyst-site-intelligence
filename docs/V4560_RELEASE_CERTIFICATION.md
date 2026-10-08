# v4.56.0 Release Certification

A v4.56.0 release is certified only when all of the following pass:

1. Repository validator reports `V4560_RELEASE_VALIDATION=PASS`.
2. Targeted pytest suite passes, including the v4.56.0 production-consolidation test and the v4.55.3.x regression line.
3. Browser certification reports `V4560_BROWSER_CERTIFICATION=PASS`.
4. Backend deploy helper reports the 46 release-bound policies aligned and the v4.56.0 production-certification API surface valid.
5. Web deploy helper reports a healthy web container, release identity 4.56.0, all 11 deep-link fallbacks, truthful runtime transport, and public HTTPS release identity.
6. `/ready` may truthfully return 503 when an optional/domain dependency is unavailable; this is a degraded-domain condition, not permission to fabricate readiness or mark core liveness Offline.

The static production certification endpoint does not claim live external-source availability. Live capability state remains the responsibility of `/ready` and `/public/capability-health`.
