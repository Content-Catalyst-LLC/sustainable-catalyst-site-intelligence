# Site Intelligence v4.55.3.1 — API Reliability & Contract Truth Repair

v4.55.3.1 is a reliability-only release. It adds no new provider, domain, analytical, or geospatial capability.

The release corrects the distinction between process liveness and usable data readiness. `/health` now explicitly reports process-only liveness. `/ready` actively verifies the required Platform Core dependency and returns HTTP 503 when that dependency is disabled, unconfigured, or unreachable.

A new `/public/capability-health` endpoint reports domain configuration state and supports `probe=true` for explicit live bridge checks. Six `/public/reliable/*` domain routes provide transport-level truth for Economics, International Law, Science, Humanitarian, Resources, and country Dossiers. A connected query with zero matches remains HTTP 200 and is labeled `no-records`; an unavailable dependency returns HTTP 503 with `ok=false`; usable partial results return HTTP 206.

The capability registry advances to 2.5.0. Capability maturity now defaults to `migration` rather than `production`; production maturity must be assigned explicitly. This prevents legacy `main.py` ownership from being treated as evidence of production readiness.

The standalone home surface now shows API data-readiness state separately from backend process liveness. WordPress remains a launch bridge only.
