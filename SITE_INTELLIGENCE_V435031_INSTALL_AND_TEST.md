# Install and Test — Site Intelligence v4.35.5

Place the release bundle and macOS installer in `~/Downloads`, then run:

```bash
cd ~/Downloads
chmod +x deploy_and_validate_site_intelligence_v4_35_3_1_macos.sh
./deploy_and_validate_site_intelligence_v4_35_3_1_macos.sh
```

Bundle-only verification:

```bash
SC_VERIFY_BUNDLE_ONLY=1 ./deploy_and_validate_site_intelligence_v4_35_3_1_macos.sh
```

The installer validates checksums, runs deterministic tests, executes the static/browser gate, promotes to GitHub/Render, and verifies the first-party release contract without using external source health as a deployment blocker.
