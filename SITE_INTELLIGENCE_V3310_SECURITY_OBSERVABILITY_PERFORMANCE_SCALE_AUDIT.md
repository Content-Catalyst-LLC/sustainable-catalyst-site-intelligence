# Site Intelligence v4.7.0 — Security / Observability / Performance / Scale Audit

## Security
- Production admin authentication: fail closed.
- Default development token accepted in production: no.
- Rate-limit identity: SHA-256 token fingerprint, not visitor IP.
- Public embed CSP preserves configured frame ancestors while restricting scripts, objects, base URI, and form actions.
- Production HSTS enabled.

## Observability
- Response-local Server-Timing enabled.
- No persistent visitor profiles or IP logs are introduced by this build.
- Public diagnostics remain aggregate and methodology-forward.

## Performance
Budgets cover largest/total first-party JavaScript and CSS, startup deadline, route transition target, and service-worker cache bounds. Asset sizes are measured from the packaged release.

## Supply chain
- `pip check` is a release gate.
- Secret-pattern static scan is a release gate.
- Immutable SHA-256 repository manifest remains mandatory.
- Dependency hash pinning is not claimed where requirements use compatible ranges.
