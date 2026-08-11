# Site Intelligence v4.35.1 — Install and Test

1. Download the release bundle and macOS installer into `~/Downloads`.
2. Run `deploy_and_validate_site_intelligence_v4_35_0_macos.sh` against the release bundle.
3. The installer verifies bundle SHA-256 values, creates an isolated Python environment, runs deterministic validation, promotes GitHub/Render, and polls the exact release gate.
4. Do not install the WordPress ZIP until the installer reports the exact v4.35.1 backend release gate and deep-live gate as successful.
5. After backend success, install/replace the WordPress plugin ZIP and verify the public app, Astronomy environment, Exoplanets / Atmospheres panel, and SETI sibling panel.

The release preserves the v4.12 nested-runtime-state exclusion and the bounded Render verification model introduced after the v4.21 verification hang.
