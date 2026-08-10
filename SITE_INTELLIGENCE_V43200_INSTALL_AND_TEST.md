# Site Intelligence v4.32.0 — Install and Test

1. Run `deploy_and_validate_site_intelligence_v4_32_0_macos.sh` with the v4.32.0 release bundle.
2. The installer verifies bundle checksums, creates an isolated Python environment, runs deterministic validation, then promotes through GitHub/Render.
3. Install the WordPress ZIP only after the live Render gate reports v4.32.0 ready at the expected commit.
