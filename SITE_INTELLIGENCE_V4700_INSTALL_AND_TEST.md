# Site Intelligence v4.12.0 — Install and Test

Use the release bundle and installer together. The installer verifies SHA-256 bundle checksums, creates an isolated Python environment, validates the exact extracted repository, runs the backend regression suite, and promotes the validated source through GitHub and Render.

Do not install the WordPress plugin ZIP before the installer reports a successful live release gate.

## Local validation

```bash
PYTHON=python3 bash verify_site_intelligence_v4_7_0_macos.sh
SC_SI_RUN_BROWSER=1 PYTHON=python3 bash verify_site_intelligence_v4_7_0_macos.sh
```

## Bundle-only verification

```bash
SC_VERIFY_BUNDLE_ONLY=1 bash deploy_and_validate_site_intelligence_v4_7_0_macos.sh sustainable-catalyst-site-intelligence-v4.12.0-release-bundle.zip
```

## Expected release boundaries

- six primary v4 areas / 35 public routes remain unchanged;
- Seafloor is an Earth Observation sub-environment;
- no terrain value is fabricated when a source record is absent;
- grid spacing is not described as measurement spacing or accuracy;
- survey footprint is not promoted to point-level sounding evidence;
- no automatic vertical-datum or depth-sign conversion occurs;
- WordPress and backend Seafloor assets must be byte-identical.
