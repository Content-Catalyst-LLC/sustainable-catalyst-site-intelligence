# Install and Test — Site Intelligence v4.35.9

Place the v4.35.9 release bundle and standalone deployment script in `~/Downloads`, then run:

```bash
cd ~/Downloads
INSTALLER="$(find . -maxdepth 1 -type f -name 'deploy_and_validate_site_intelligence_v4_35_8_macos*.sh' -print0 | xargs -0 ls -t | head -1)"
BUNDLE="$(find . -maxdepth 1 -type f -name 'sustainable-catalyst-site-intelligence-v4.35.9-release-bundle*.zip' -print0 | xargs -0 ls -t | head -1)"
chmod +x "$INSTALLER"
bash "$INSTALLER" "$BUNDLE"
```

The installer verifies SHA-256 bundle checksums, creates an isolated virtual environment, runs the complete deterministic verifier, reruns the static/browser gate, promotes the repository through GitHub/Render, and verifies first-party release identity/runtime plus the canonical workspace-evidence readiness contract.

To verify package integrity without deployment:

```bash
SC_VERIFY_BUNDLE_ONLY=1 bash "$INSTALLER" "$BUNDLE"
```
