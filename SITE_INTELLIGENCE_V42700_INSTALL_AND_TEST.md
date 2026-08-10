# Site Intelligence v4.27.0 — Install and Test

Use the complete v4.27.0 release bundle and its macOS installer.

```bash
cd ~/Downloads

INSTALLER="$(find . -maxdepth 1 -type f \
  -name 'deploy_and_validate_site_intelligence_v4_27_0_macos*.sh' \
  -print0 | xargs -0 ls -t | head -1)"

BUNDLE="$(find . -maxdepth 1 -type f \
  -name 'sustainable-catalyst-site-intelligence-v4.27.0-release-bundle*.zip' \
  -print0 | xargs -0 ls -t | head -1)"

chmod +x "$INSTALLER"
bash "$INSTALLER" "$BUNDLE"
```

The installer verifies bundle checksums, extracts the immutable repository, creates an isolated Python environment, runs deterministic validation pass 1 and pass 2, promotes the backend through GitHub/Render, and waits for the bounded live release gate.

Do not install the v4.27.0 WordPress ZIP until the terminal explicitly reports that the exact v4.27.0 backend release, Git commit, release gate and transportation deep gate are live.
