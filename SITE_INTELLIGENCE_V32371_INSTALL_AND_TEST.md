# Site Intelligence v3.24.0 Installation and Test Guide

## Required files

Place these two files in `~/Downloads`:

- `deploy_and_validate_site_intelligence_v3_23_7_1_macos.sh`
- `sustainable-catalyst-site-intelligence-v3.24.0-release-bundle.zip`

## Run

```bash
cd ~/Downloads

INSTALLER="$(find . -maxdepth 1 -type f \
  -name 'deploy_and_validate_site_intelligence_v3_23_7_1_macos*.sh' \
  -print0 | xargs -0 ls -t | head -1)"

BUNDLE="$(find . -maxdepth 1 -type f \
  -name 'sustainable-catalyst-site-intelligence-v3.24.0-release-bundle*.zip' \
  -print0 | xargs -0 ls -t | head -1)"

chmod +x "$INSTALLER"
bash "$INSTALLER" "$BUNDLE"
```

## Expected validation

The installer must complete two deterministic validation passes, including the country-selector browser gate, the Global Data Truth browser gate, the complete inherited Python suite, immutable-manifest verification, JavaScript and PHP syntax checks, complete-shell validation, production-soak route validation, and the long-page WordPress embed gate.

## Live promotion gate

The installer then promotes the exact validated Git tree and checks the Render deployment for:

- release `3.24.0`;
- matching Git commit and release ID;
- a global Data Truth country catalog of at least 170 entries;
- selector startup code that hydrates from `/public/data-truth/countries`;
- the country-catalog-ready event contract;
- the inherited startup, route, service-worker, map, and embed health contracts.

## WordPress installation

Install the emitted WordPress ZIP only after the installer reports that the live v3.24.0 release gate passed. Purge WordPress/page cache after replacement, then open Site Intelligence in a new private browser window and verify that the country selector contains countries beyond Kenya.
