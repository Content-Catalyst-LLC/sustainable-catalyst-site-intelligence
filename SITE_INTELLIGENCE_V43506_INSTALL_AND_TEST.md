# Site Intelligence v4.35.15 — Install and Test

1. Place the release bundle and `deploy_and_validate_site_intelligence_v4_35_6_macos.sh` in `~/Downloads`.
2. Run the installer. It verifies SHA-256 checksums, creates an isolated Python environment, runs deterministic validation, runs the browser/static gate, then promotes through GitHub and Render.
3. Promotion verifies the expected version, release ID, Git commit, first-party runtime, 35-route v4 structure, authoritative connector readiness, and application assets. External provider availability does not block release.

No new credentials are required for the five v4.35.15 connectors. Existing FIRMS/NASS/ReliefWeb credentials remain optional/configuration-gated as documented in prior releases.
