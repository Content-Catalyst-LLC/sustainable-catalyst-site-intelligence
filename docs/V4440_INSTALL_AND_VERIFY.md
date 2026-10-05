# Site Intelligence v4.44.0 Install and Verify

Use `scripts/validate_v4440_release.py`, the v4.44 current-contract pytest group, PHP lint, and shell syntax before commit. Deploy the backend with `deploy/contabo/upgrade_site_intelligence_backend_v4_44_0_contabo.sh`, then verify `/health`, `/public/build-info`, `/public/app/bootstrap`, `/public/app/runtime-handshake?client_version=4.44.0`, `/public/routes/summary`, and `/public/release-gate`. Install the matching WordPress v4.44.0 package only after the backend reports the same expected plugin version.
