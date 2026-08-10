# Site Intelligence v4.23.0 Install & Test

Use `deploy_and_validate_site_intelligence_v4_23_0_macos.sh` with the v4.23.0 release bundle. The installer verifies checksums, creates an isolated virtual environment, runs deterministic validation twice, promotes GitHub/Render, and only then prints the WordPress-plugin installation path.

Do not install the WordPress ZIP until the live backend release gate confirms v4.23.0 and the exact Git commit.
