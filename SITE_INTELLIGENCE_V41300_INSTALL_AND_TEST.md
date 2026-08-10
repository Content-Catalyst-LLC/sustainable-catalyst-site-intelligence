# Site Intelligence v4.13.0 — Install and Test

Place the v4.13.0 release bundle and installer in `~/Downloads`.

```bash
cd ~/Downloads

INSTALLER="$(find . -maxdepth 1 -type f \
  -name 'deploy_and_validate_site_intelligence_v4_13_0_macos*.sh' \
  -print0 | xargs -0 ls -t | head -1)"

BUNDLE="$(find . -maxdepth 1 -type f \
  -name 'sustainable-catalyst-site-intelligence-v4.13.0-release-bundle*.zip' \
  -print0 | xargs -0 ls -t | head -1)"

chmod +x "$INSTALLER"
bash "$INSTALLER" "$BUNDLE"
```

The installer validates checksums, creates an isolated Python environment, executes deterministic validation passes, then invokes GitHub/Render promotion. Install the WordPress ZIP only after the live v4.13.0 release gate passes.
