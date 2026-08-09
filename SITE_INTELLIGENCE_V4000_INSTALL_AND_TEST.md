# Site Intelligence v4.11.0 — Install and Test

Use the release bundle and macOS installer together. The installer verifies SHA-256 bundle checksums before extracting the repository or allowing promotion.

## Terminal

```bash
cd ~/Downloads

INSTALLER="$(find . -maxdepth 1 -type f \
  -name 'deploy_and_validate_site_intelligence_v4_0_0_macos*.sh' \
  -print0 | xargs -0 ls -t | head -1)"

BUNDLE="$(find . -maxdepth 1 -type f \
  -name 'sustainable-catalyst-site-intelligence-v4.11.0-release-bundle*.zip' \
  -print0 | xargs -0 ls -t | head -1)"

chmod +x "$INSTALLER"
bash "$INSTALLER" "$BUNDLE"
```

## Validation sequence

1. Verify bundle checksums.
2. Extract the immutable repository package.
3. Create an isolated Python virtual environment.
4. Install runtime and test dependencies.
5. Run the v4 contract validator, manifest checks, Python compilation, JSON/GeoJSON parsing, JavaScript and PHP syntax checks, static security scan, and complete regression suite.
6. Run a second static/package validation pass without repeating the full regression suite.
7. Synchronize the exact validated tree to GitHub.
8. Verify the live Render release ID, Git commit, v4 consolidation endpoints, app shell, truth/provenance, analytical state, governance, security, maps, and runtime health.
9. Install the WordPress ZIP only after the live gate reports ready.

The browser consolidation gates are package-build gates rather than nested installer-time Chromium gates, avoiding the process-teardown false hangs observed in earlier releases.
