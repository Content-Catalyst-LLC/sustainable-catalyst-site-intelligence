# Install and Verify Site Intelligence v4.55.2

Run `scripts/validate_v4552_release.py` and the v4.46–v4.55.2 regression suite before commit. Deploy the backend with `deploy/contabo/upgrade_site_intelligence_backend_v4_55_2_contabo.sh`, then verify `/health`, `/public/domain-intelligence/registry`, `/public/domain-intelligence/parity-audit`, `/public/routes/summary`, and `/public/release-gate`.

The production targets are version `4.55.2`, capability registry `2.3.0`, 1500 routes, 191 modularized routes, 28 capabilities, 0 unclassified routes, and 21 advanced-domain-intelligence routes.
