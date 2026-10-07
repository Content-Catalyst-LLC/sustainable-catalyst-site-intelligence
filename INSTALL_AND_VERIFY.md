# Site Intelligence v4.54.0 Install & Verify

Run `python scripts/validate_v4530_release.py`, then the current v4.46–v4.53 regression suite. Expected architecture: 1455 routes, 146 modularized, 25 capability families, 0 unclassified routes, 12 scenario/exposure routes, and 12 advanced-domain routes.

Deploy with `deploy/contabo/upgrade_site_intelligence_backend_v4_53_0_contabo.sh`. The helper preserves dynamic `backend/data/` state while explicitly promoting 36 release-bound registries/policies and waits for Docker health to become healthy before certification.


See `docs/V4540_INSTALL_AND_VERIFY.md` for v4.54.0 package verification and deployment.
