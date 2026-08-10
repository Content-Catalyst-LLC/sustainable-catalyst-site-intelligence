# Site Intelligence v4.15.0 — Install and Test

Use the release bundle and installer together. Do not install the WordPress ZIP until the installer reports that the exact GitHub commit and Render release gate passed.

```bash
cd ~/Downloads

INSTALLER="$(find . -maxdepth 1 -type f \
  -name 'deploy_and_validate_site_intelligence_v4_6_0_macos*.sh' \
  -print0 | xargs -0 ls -t | head -1)"

BUNDLE="$(find . -maxdepth 1 -type f \
  -name 'sustainable-catalyst-site-intelligence-v4.15.0-release-bundle*.zip' \
  -print0 | xargs -0 ls -t | head -1)"

chmod +x "$INSTALLER"
bash "$INSTALLER" "$BUNDLE"
```

## What the installer verifies

1. Bundle SHA-256 checksums.
2. Isolated Python environment and dependencies.
3. Immutable repository manifest.
4. Static release contract, JSON/GeoJSON, JavaScript, PHP, and security checks.
5. Complete backend regression suite.
6. Promotion to the configured GitHub repository.
7. Live Render release identity and runtime health.
8. v4 platform/navigation, space-observation stack, Ocean Surface, Water Column overview/catalog/state/readiness, Data Truth, provenance, maps, and other inherited production gates.

The WordPress ZIP printed by the successful installer is the package to install.
