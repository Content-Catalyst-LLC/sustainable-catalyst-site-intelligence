# Site Intelligence v4.18.0 — Install and Test

Use the packaged macOS installer and release bundle. The installer verifies bundle checksums, creates an isolated Python environment, runs deterministic validation pass 1, reruns static/package assurance as pass 2, then promotes the exact Git tree to GitHub and waits for the Render live release gate.

Do not install the WordPress ZIP until the installer reports the exact v4.18.0 GitHub/Render gate as ready.

```bash
cd ~/Downloads
INSTALLER="$(find . -maxdepth 1 -type f -name 'deploy_and_validate_site_intelligence_v4_18_0_macos*.sh' -print0 | xargs -0 ls -t | head -1)"
BUNDLE="$(find . -maxdepth 1 -type f -name 'sustainable-catalyst-site-intelligence-v4.18.0-release-bundle*.zip' -print0 | xargs -0 ls -t | head -1)"
chmod +x "$INSTALLER"
bash "$INSTALLER" "$BUNDLE"
```
