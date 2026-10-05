# Site Intelligence v4.45.0 Install and Verify

Run the release validator, current-contract pytest gate, Python/JavaScript/PHP syntax checks, commit to `main`, then deploy the backend before the WordPress plugin.

Current-contract test gate:

```bash
python scripts/validate_v4450_release.py
PYTHONPATH=backend python -m pytest -q \
  backend/tests/test_v4450_wordpress_thin_shell_embed_bridge.py \
  backend/tests/test_release_reconciliation_invariants.py \
  backend/tests/test_source_reconciliation_v4410.py \
  backend/tests/test_v4410_preserves_v44003_homepage_ticker.py \
  backend/tests/test_energy_spatial_global_v4410.py \
  backend/tests/test_energy_runtime_consumer.py
```

Production backend verification must include `/health`, `/public/build-info`, `/public/app/bootstrap?surface=wordpress-embed`, `/public/integrations/wordpress/bridge`, `/public/integrations/wordpress/embed-contract`, `/public/integrations/wordpress/compatibility`, `/public/routes/summary`, and `/public/release-gate`.
