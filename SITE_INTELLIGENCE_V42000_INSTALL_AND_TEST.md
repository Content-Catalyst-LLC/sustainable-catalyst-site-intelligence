# Site Intelligence v4.20.0 — Install and Test

Use only the v4.20.0 installer together with the v4.20.0 release bundle.

```bash
cd ~/Downloads

INSTALLER="$(find . -maxdepth 1 -type f \
  -name 'deploy_and_validate_site_intelligence_v4_20_0_macos*.sh' \
  -print0 | xargs -0 ls -t | head -1)"

BUNDLE="$(find . -maxdepth 1 -type f \
  -name 'sustainable-catalyst-site-intelligence-v4.20.0-release-bundle*.zip' \
  -print0 | xargs -0 ls -t | head -1)"

[ -n "$INSTALLER" ] || { echo "ERROR: v4.20.0 installer not found"; exit 1; }
[ -n "$BUNDLE" ] || { echo "ERROR: v4.20.0 release bundle not found"; exit 1; }

chmod +x "$INSTALLER"
bash "$INSTALLER" "$BUNDLE"
```

The installer performs checksum validation, isolated dependency installation, deterministic release pass 1, immutable pass 2, GitHub promotion and Render live-gate verification.

Do not install the WordPress ZIP until Terminal reports the exact v4.20.0 GitHub/Render live gate passed.
