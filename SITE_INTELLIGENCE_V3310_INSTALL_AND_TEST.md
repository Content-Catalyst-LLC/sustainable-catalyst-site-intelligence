# Site Intelligence v4.14.0 — Install and Test

Run `deploy_and_validate_site_intelligence_v3_31_0_macos.sh` with the v4.14.0 release bundle.

The installer:
1. verifies the release-bundle SHA-256 checksums;
2. extracts the immutable repository package;
3. creates a clean Python virtual environment and installs declared requirements;
4. runs the complete v4.14.0 verifier, including static assurance, supply-chain checks, and all 1,079 Python tests;
5. runs a second deterministic static/package pass without repeating the browser or regression suite;
6. revalidates the source and exact Git tree during promotion without nested Chromium launches;
7. pushes the exact Git commit and release tags to GitHub;
8. waits for Render and verifies the live release identity and production contracts;
9. prints the approved WordPress plugin ZIP location only after the live gate succeeds.

Chromium validation is a package-build gate rather than an installer-time gate. The immutable package is browser-tested before distribution, including the 47-script complete shell, 173-country selection, Brazil Data Truth hydration, route churn, production assurance, direct/iframe execution, and fixed 1,100 px WordPress embed isolation. This avoids known false installer hangs caused by Chromium child-process teardown while retaining browser assurance on the exact packaged release.
