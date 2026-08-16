# Site Intelligence v4.36.1 — Install, Test, Push & Deploy

The release bundle is designed for macOS/zsh and contains the repository ZIP, WordPress plugin ZIP, checksums, validation notes, and a deployment script.

## Recommended one-command path

Place the release bundle in `~/Downloads`, then run:

```bash
cd ~/Downloads
BUNDLE="$(find . -maxdepth 1 -type f -name 'sustainable-catalyst-site-intelligence-v4.36.1-release-bundle*.zip' -print | sort | tail -1)"
[ -n "$BUNDLE" ] || { echo 'ERROR: v4.36.1 release bundle not found.'; exit 1; }
rm -rf sustainable-catalyst-site-intelligence-v4.36.1-release
unzip -q "$BUNDLE" -d sustainable-catalyst-site-intelligence-v4.36.1-release
cd sustainable-catalyst-site-intelligence-v4.36.1-release
chmod +x deploy_and_validate_site_intelligence_v4_36_1_macos.sh
./deploy_and_validate_site_intelligence_v4_36_1_macos.sh
```

The script verifies bundle checksums, installs exact backend/test dependencies into an isolated venv, runs v4.36.1 validation, clones the GitHub repository into a clean deployment directory, commits the validated tree, creates the `v4.36.1` release tag and rollback tag, pushes GitHub refs, and waits for Render release identity/health/OpenAPI verification.

## WordPress

After backend promotion succeeds, upload the bundled `sustainable-catalyst-site-intelligence-v4.36.1-wordpress-plugin.zip` through WordPress. The plugin and backend must both report `4.36.1`.

## Live post-deploy probes

The promotion script verifies `/health`, `/openapi.json`, Ocean readiness, and first-party connector routes. External provider health remains non-blocking. Optional live NOAA/OBIS/NASA probes can be enabled with:

```bash
SC_SI_RUN_LIVE_PROVIDER_PROBES=1 ./promote_site_intelligence_v4_36_1_to_github_and_render_macos.sh
```

No API secret is required for the public NOAA/OBIS/NASA probes used by this release.
