# Site Intelligence v4.11.0 — Install and Test

## Release
Orbital Earth & Satellite Observation extends the existing Earth Observation route. It does not add a new top-level public route.

## macOS deployment
Use `deploy_and_validate_site_intelligence_v4_1_0_macos.sh` with the matching v4.11.0 release bundle. The installer verifies bundle SHA-256 checksums, extracts the immutable repository, creates an isolated Python virtual environment, installs release dependencies, runs the complete backend regression suite and deterministic package checks, then promotes the exact validated tree through GitHub and Render.

Browser interaction validation is a package-build gate rather than a nested installer gate because Chromium child-process teardown has produced false installer hangs in prior releases. The production promotion gate separately verifies the live Orbital Earth contract/readiness and shipped orbital browser asset after Render deployment.

## Required live gate
Do not install the WordPress ZIP until Terminal reports that the exact v4.11.0 release, Git commit, release id, v4 platform contracts, Orbital Earth contract/readiness, application assets, Data Truth, provenance, maps, runtime health, and WordPress installation gate are synchronized.

## Orbital truth boundary
The orbital interface uses real registered Earth-observation imagery products. It does not claim a live spacecraft position, physical camera solution, pass-specific ground track, or instantaneous sensor swath unless a future telemetry source explicitly provides one.
