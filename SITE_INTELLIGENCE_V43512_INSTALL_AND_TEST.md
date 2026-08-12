# Site Intelligence v4.35.13 — Install & Test

## macOS deployment
Place the v4.35.13 release bundle and standalone installer in `~/Downloads`, then run:

```bash
cd ~/Downloads
INSTALLER="$(find . -maxdepth 1 -type f -name 'deploy_and_validate_site_intelligence_v4_35_12_macos*.sh' -print0 | xargs -0 ls -t | head -1)"
BUNDLE="$(find . -maxdepth 1 -type f -name 'sustainable-catalyst-site-intelligence-v4.35.13-release-bundle*.zip' -print0 | xargs -0 ls -t | head -1)"
chmod +x "$INSTALLER"
bash "$INSTALLER" "$BUNDLE"
```

The installer verifies SHA-256 checksums, extracts the repository, creates a Python virtual environment, installs requirements, performs deterministic validation, performs the static/browser pass, and then runs the resume-safe GitHub/Render promotion script.

## Air quality configuration
For EPA AirNow current observations set the server-side Render environment variable:

```text
SC_SI_AIRNOW_API_KEY=<AirNow API key>
```

The existing EPA AQS connector requires its existing server-side credentials:

```text
SC_SI_EPA_AQS_EMAIL=<registered email>
SC_SI_EPA_AQS_KEY=<AQS key>
```

ERA5 and CAMS catalogue discovery in this release does not require a credential. Actual Copernicus data-store retrieval remains distinct from catalogue discovery and should use its own authenticated data-store workflow when implemented.

## Local verification
From the repository root:

```bash
bash verify_site_intelligence_v4_35_12_macos.sh
SC_SI_SKIP_TESTS=1 SC_SI_RUN_BROWSER=1 bash verify_site_intelligence_v4_35_12_macos.sh
```
