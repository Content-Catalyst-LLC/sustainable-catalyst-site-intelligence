# Site Intelligence v4.39.0 — Install and Test

Use the flat-root `sustainable-catalyst-site-intelligence-v4.39.0-release-bundle.zip`. The installer validates SHA-256 checksums, extracts the repository, creates a Python virtual environment, installs backend/dev requirements, runs all 1708 deterministic tests, runs browser certification, pushes the certified tree to GitHub, waits for Render, and verifies the live Space/Ocean/application contracts.

After Render promotion succeeds, replace the WordPress Site Intelligence plugin with `sustainable-catalyst-site-intelligence-v4.39.0-wordpress-plugin.zip`. The plugin replacement is required because v4.39.0 changes the application shell, live Space JS/CSS, iframe CSS, router integration, and cache lineage.

No new Space credential is required for the five core live lanes.
