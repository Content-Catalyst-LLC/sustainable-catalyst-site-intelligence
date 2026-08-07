# Install and Test Site Intelligence v3.25.0

Place the macOS installer and release bundle in `~/Downloads`, then run:

```bash
cd ~/Downloads

INSTALLER="$(find . -maxdepth 1 -type f \
  -name 'deploy_and_validate_site_intelligence_v3_25_0_macos*.sh' \
  -print0 | xargs -0 ls -t | head -1)"

BUNDLE="$(find . -maxdepth 1 -type f \
  -name 'sustainable-catalyst-site-intelligence-v3.25.0-release-bundle*.zip' \
  -print0 | xargs -0 ls -t | head -1)"

chmod +x "$INSTALLER"
bash "$INSTALLER" "$BUNDLE"
```

The installer verifies checksums, creates an isolated Python environment, runs deterministic validation twice, publishes the exact Git tree, waits for Render, and checks the live unified-state contracts before allowing WordPress installation.

Install only the WordPress ZIP printed by the successful installer.
