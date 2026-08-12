# Site Intelligence v4.35.14 — Install & Test

## macOS deployment
Place the release bundle and installer in `~/Downloads`, then run:

```bash
cd ~/Downloads
INSTALLER="$(find . -maxdepth 1 -type f -name 'deploy_and_validate_site_intelligence_v4_35_14_macos*.sh' -print0 | xargs -0 ls -t | head -1)"
BUNDLE="$(find . -maxdepth 1 -type f -name 'sustainable-catalyst-site-intelligence-v4.35.14-release-bundle*.zip' -print0 | xargs -0 ls -t | head -1)"
chmod +x "$INSTALLER"
bash "$INSTALLER" "$BUNDLE"
```

The installer verifies SHA-256 checksums, extracts the repository, creates a virtual environment, installs pinned requirements, runs deterministic validation and the static/browser pass, then promotes GitHub/Render and verifies first-party deployment identity. External source health is not a release blocker.

## Optional server-side configuration
```text
SC_SI_HDX_HAPI_APP_IDENTIFIER=...
SC_SI_IPC_API_KEY=...
SC_SI_RELIEFWEB_APPNAME=...
```

GDACS, HDX dataset discovery, and public FEWS NET retrieval do not require these credentials.

## Bundle-only verification
```bash
SC_VERIFY_BUNDLE_ONLY=1 bash "$INSTALLER" "$BUNDLE"
```
