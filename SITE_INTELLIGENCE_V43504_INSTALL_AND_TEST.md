# Site Intelligence v4.35.4 — Install and Test

Use the generated release bundle and macOS deployment script from `~/Downloads`.

```bash
cd ~/Downloads

INSTALLER="$(find . -maxdepth 1 -type f \
  -name 'deploy_and_validate_site_intelligence_v4_35_4_macos*.sh' \
  -print0 | xargs -0 ls -t | head -1)"

BUNDLE="$(find . -maxdepth 1 -type f \
  -name 'sustainable-catalyst-site-intelligence-v4.35.4-release-bundle*.zip' \
  -print0 | xargs -0 ls -t | head -1)"

chmod +x "$INSTALLER"
bash "$INSTALLER" "$BUNDLE"
```

The installer verifies bundle checksums, creates an isolated virtual environment, runs deterministic validation, runs the browser/static gate, promotes the exact validated Git tree, and verifies first-party Render deployment identity/runtime without making external source health a release blocker.

For checksum/structure verification only:

```bash
SC_VERIFY_BUNDLE_ONLY=1 bash "$INSTALLER" "$BUNDLE"
```
