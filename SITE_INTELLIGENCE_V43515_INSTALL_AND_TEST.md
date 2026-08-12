# Site Intelligence v4.35.15 — Install & Test

## macOS deployment
Place the release bundle and installer in `~/Downloads`, then run:

```bash
cd ~/Downloads
INSTALLER="$(find . -maxdepth 1 -type f -name 'deploy_and_validate_site_intelligence_v4_35_15_macos*.sh' -print0 | xargs -0 ls -t | head -1)"
BUNDLE="$(find . -maxdepth 1 -type f -name 'sustainable-catalyst-site-intelligence-v4.35.15-release-bundle*.zip' -print0 | xargs -0 ls -t | head -1)"
echo "INSTALLER=$INSTALLER"
echo "BUNDLE=$BUNDLE"
chmod +x "$INSTALLER"
bash "$INSTALLER" "$BUNDLE"
```

The installer verifies SHA-256 checksums, extracts the repository, creates a virtual environment, installs pinned requirements, runs deterministic validation plus the static/browser pass, then promotes GitHub/Render and verifies first-party deployment identity. External source health is not a release blocker.

## v4.35.15 configuration
No new credential is required for the v4.35.15 Mining/Critical Materials/Industrial additions. Existing credentials from earlier releases remain optional/required only for their respective connectors.

## Bundle-only verification
```bash
SC_VERIFY_BUNDLE_ONLY=1 bash "$INSTALLER" "$BUNDLE"
```
