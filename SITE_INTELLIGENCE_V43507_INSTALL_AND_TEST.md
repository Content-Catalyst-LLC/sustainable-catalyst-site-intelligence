# Site Intelligence v4.35.8 — Install and Test

Place the release bundle and deploy script in `~/Downloads`, then run:

```bash
cd ~/Downloads
INSTALLER="$(find . -maxdepth 1 -type f -name 'deploy_and_validate_site_intelligence_v4_35_7_macos*.sh' -print0 | xargs -0 ls -t | head -1)"
BUNDLE="$(find . -maxdepth 1 -type f -name 'sustainable-catalyst-site-intelligence-v4.35.8-release-bundle*.zip' -print0 | xargs -0 ls -t | head -1)"
chmod +x "$INSTALLER"
bash "$INSTALLER" "$BUNDLE"
```

The installer verifies SHA-256 checksums, creates an isolated Python environment, runs deterministic validation, runs the static/browser gate, promotes through GitHub/Render, and verifies first-party release identity/runtime without using upstream API health as a blocker.
