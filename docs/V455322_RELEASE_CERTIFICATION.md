# Site Intelligence v4.55.3.2.2 Release Certification

Release: **Browser API Transport & CORS Repair**

Artifact certification completed against the assembled release source before packaging:

- `V455322_RELEASE_VALIDATION=PASS`
- `V455322_BROWSER_CERTIFICATION=PASS`
- corrective + carried-forward regression line: **266 passed**
- Python compileall: PASS
- JavaScript syntax: PASS
- PHP lint: PASS
- shell syntax: PASS
- route inventory: 1518 total / 209 modularized / 31 capabilities / 0 unclassified
- capability registry: 2.6.2
- release-bound registries: 45 / 45 aligned to 4.55.3.2.2

The backend contract includes an explicit CORS preflight test from `https://intelligence.sustainablecatalyst.com` to `/health` requesting `X-SCSI-Runtime-Diagnostic`. The browser runtime no longer requires that custom header for ordinary public GET probes, so normal health checks are preflight-light while the diagnostic header remains explicitly supported.

Production certification is not complete until the backend deployment helper passes its live Contabo preflight gate, the web artifact is deployed afterward, and a hard-refreshed production browser no longer reports `Site health: Offline` while `/health` is reachable.
