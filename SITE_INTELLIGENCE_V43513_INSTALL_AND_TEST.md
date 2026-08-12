# Site Intelligence v4.35.15 — Install & Test

## macOS deployment
Place the v4.35.15 release bundle and standalone installer in `~/Downloads`, then run:

```bash
cd ~/Downloads
INSTALLER="$(find . -maxdepth 1 -type f -name 'deploy_and_validate_site_intelligence_v4_35_13_macos*.sh' -print0 | xargs -0 ls -t | head -1)"
BUNDLE="$(find . -maxdepth 1 -type f -name 'sustainable-catalyst-site-intelligence-v4.35.15-release-bundle*.zip' -print0 | xargs -0 ls -t | head -1)"
chmod +x "$INSTALLER"
bash "$INSTALLER" "$BUNDLE"
```

The installer verifies SHA-256 checksums, extracts the repository, creates a Python virtual environment, installs requirements, performs deterministic validation, performs the static/browser pass, and then runs the resume-safe GitHub/Render promotion script.

## Water / hydrology configuration
No new server credential is required for the five v4.35.15 connector interfaces. EPA SDWIS/Envirofacts, bounded OSM/Overpass, NIDIS public drought files, NASA CMR GPM discovery, and GloFAS public product discovery are exposed without adding a new API-key requirement in this release.

Existing credentials for other Site Intelligence workspaces remain unchanged.

## Local verification
From the repository root:

```bash
bash verify_site_intelligence_v4_35_13_macos.sh
SC_SI_SKIP_TESTS=1 SC_SI_RUN_BROWSER=1 bash verify_site_intelligence_v4_35_13_macos.sh
```
