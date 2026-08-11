# Site Intelligence v4.35.3 — Install and Test

## macOS deployment

Place the v4.35.3 release bundle and `deploy_and_validate_site_intelligence_v4_35_3_macos.sh` in `~/Downloads`, then run:

```bash
cd ~/Downloads
chmod +x deploy_and_validate_site_intelligence_v4_35_3_macos.sh
./deploy_and_validate_site_intelligence_v4_35_3_macos.sh
```

The installer verifies release-bundle checksums, creates an isolated Python virtual environment, installs backend/dev requirements, runs deterministic validation, promotes the repository through GitHub/Render, and prints the WordPress plugin ZIP path.

For checksum-only validation:

```bash
SC_VERIFY_BUNDLE_ONLY=1 ./deploy_and_validate_site_intelligence_v4_35_3_macos.sh
```

## Optional configuration

USGS Water Data public reads do not require an API key. If a higher permitted rate limit is needed, set `SC_SI_USGS_WATER_API_KEY` only in the backend environment. ReliefWeb V2 remains separately gated by the approved `SC_SI_RELIEFWEB_APPNAME` value.
