# Site Intelligence v4.14.0 — Install and Test

Use `deploy_and_validate_site_intelligence_v4_10_0_macos.sh` with the v4.14.0 release bundle. The installer verifies bundle checksums, creates an isolated Python environment, executes the deterministic release verifier, promotes the exact validated tree through GitHub/Render, and only then prints the WordPress ZIP path.

For checksum-only package verification:

```bash
SC_VERIFY_BUNDLE_ONLY=1 bash deploy_and_validate_site_intelligence_v4_10_0_macos.sh sustainable-catalyst-site-intelligence-v4.14.0-release-bundle.zip
```

Install the WordPress ZIP only after the live release gate confirms the exact v4.14.0 backend and Ocean Missions readiness contract.
