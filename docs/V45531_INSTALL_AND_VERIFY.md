# Install and Verify Site Intelligence v4.55.3.1

1. Run `python scripts/validate_v45531_release.py` and the selected v4.46–v4.55.3.1 regression suite.
2. Deploy the backend ZIP with `deploy/contabo/upgrade_site_intelligence_backend_v4_55_3_1_contabo.sh`.
3. Verify `/health` returns process-only liveness semantics.
4. Verify `/ready`; HTTP 200 means the required Core dependency is reachable, while HTTP 503 means the API process is alive but data readiness is not established.
5. Run `/public/capability-health?probe=true` and inspect every domain state. Do not promote unavailable domains based on route existence or HTTP 200 from legacy endpoints.
6. Verify the reliable domain endpoints for Economics, Law, Science, Humanitarian, Resources, and Dossiers. Connected empty queries must return `data_state=no-records`; dependency failures must return HTTP 503 with `ok=false`.
7. Deploy the v4.55.3.1 standalone web artifact so the visible release identity and API-readiness card match the backend.
8. Install the WordPress v4.55.3.1 launch bridge only after backend/web verification.

Production target: backend `4.55.3.1`, capability registry `2.5.0`, 1,515 routes, 206 modularized routes, 30 capabilities, 0 unclassified routes, nine API-reliability routes, standalone web on loopback port 8096.
