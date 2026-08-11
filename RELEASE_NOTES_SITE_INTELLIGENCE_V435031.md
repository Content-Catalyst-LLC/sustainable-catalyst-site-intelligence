# Site Intelligence v4.35.3.1 — Deployment Verification, Source Health & Release-Gate Hardening

v4.35.3.1 is a production-reliability patch on top of Authoritative Connector Expansion I.

## Changes

- Promotion now verifies release identity, Git commit, first-party runtime, application shell, structural 35-route readiness, and authoritative connector-router readiness.
- External domain/API health is explicitly separated from deployment validity.
- Added `/public/deployment-verification`.
- Added `/public/source-health-policy`.
- Removed domain `/state` endpoints from the current GitHub/Render release decision.
- ReliefWeb configuration requirements and future upstream outages are reported as source conditions rather than release failures.
- Deployment receipts now record the verification policy.

## Release boundary

A healthy Site Intelligence deployment does not guarantee that every external public source is available at that instant. Source availability may be healthy, degraded, unavailable, unknown, or configuration-required without invalidating the application deployment.
