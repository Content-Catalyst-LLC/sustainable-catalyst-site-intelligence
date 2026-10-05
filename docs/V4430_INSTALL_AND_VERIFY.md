# Site Intelligence v4.43.0 Install and Verify

## Local verification

Use Python 3.13 and `backend/requirements-dev.txt`, then run the v4.43 validator and current-contract test gate.

## GitHub

Overlay the verified release repository onto the existing Git clone, certify, commit, and push `main`.

## Contabo

Upload the backend ZIP and `upgrade_site_intelligence_backend_v4_43_0_contabo.sh`. The script backs up the runtime, preserves dynamic data and credentials, restores release-bound policy files from the package, rebuilds the container, and verifies the modular route registry.

## WordPress

Install the v4.43.0 plugin ZIP with `wp plugin install --force --activate`, flush transients/cache/rewrite rules, and verify plugin version 4.43.0.
