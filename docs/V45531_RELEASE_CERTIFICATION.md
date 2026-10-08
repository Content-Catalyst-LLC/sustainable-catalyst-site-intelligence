# v4.55.3.1 Release Certification

Certification requires:

- release identity `4.55.3.1` and capability registry `2.5.0`;
- 1,515 total routes, 206 modularized routes, 30 capabilities, and 0 unclassified routes;
- nine modular `api-reliability` routes;
- `/health` explicitly scoped to process liveness only;
- `/ready` returns HTTP 503 when Platform Core is not ready and HTTP 200 only after a successful Core health probe;
- a connected empty domain query is reported as `no-records`, not a source failure;
- a domain dependency failure cannot remain `ok=true` on the reliable API surface;
- legacy `main.py` capability families do not default to production maturity;
- the release-bound API reliability contract is present and aligned;
- the selected v4.46–v4.55.3.1 regression line passes;
- backend, standalone web JavaScript, WordPress PHP, and deployment helpers pass syntax validation.

Production deployment is allowed even if `/ready` reports 503: that state is the information this repair is designed to expose. Site Intelligence must not be called data-ready until `/ready` and the required live capability probes pass in production.

## Local artifact gate completed

- `scripts/validate_v45531_release.py`: `V45531_RELEASE_VALIDATION=PASS`
- Selected reliability + v4.46–v4.55.3 regression gate: `229 passed`
- `python3 -m compileall -q backend/app`: pass
- standalone and legacy critical JavaScript `node --check`: pass
- WordPress plugin `php -l`: pass
- backend/web deployment helper `bash -n`: pass

These results certify the packaged code and contract behavior locally. They do not claim that production data dependencies are ready. After deployment, `/ready` and `/public/capability-health?probe=true` are the production truth gates.
