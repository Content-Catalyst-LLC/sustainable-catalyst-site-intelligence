# Site Intelligence v4.13.0 — Install and Test

Use the release bundle and installer together. The installer verifies bundle SHA-256 checksums, extracts the exact repository ZIP, creates an isolated Python environment, runs the deterministic repository validator and complete backend test suite, performs a fast second deterministic pass, and only then promotes the validated tree through GitHub and Render.

The live gate requires the v4.13.0 Underwater Observation overview, catalog, bounded state, readiness contract, and shipped browser asset in addition to the inherited Seafloor, Water Column, Ocean Surface, space-observation, Data Truth, map, platform, governance, and runtime-health gates.

Do not install the WordPress ZIP until the installer reports that the exact v4.13.0 GitHub and Render live gate passed.

Bundle-only validation is available with:

```bash
SC_VERIFY_BUNDLE_ONLY=1 bash deploy_and_validate_site_intelligence_v4_8_0_macos.sh sustainable-catalyst-site-intelligence-v4.13.0-release-bundle.zip
```
