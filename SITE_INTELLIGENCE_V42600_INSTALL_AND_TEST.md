# Site Intelligence v4.26.0 — Install and Test

Use the release bundle with `deploy_and_validate_site_intelligence_v4_26_0_macos.sh`. The installer verifies bundle checksums, extracts the repository, creates an isolated Python environment, runs deterministic pass 1 and pass 2, then invokes the resume-safe GitHub/Render promoter.

Install the WordPress ZIP only after the live Render release gate verifies version 4.26.0, release id `site-intelligence-v4.26.0`, the exact Git commit, and the Human Settlements deep gate.
