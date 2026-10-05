# Site Intelligence v4.47.0 — Install and Verify

## Local certification

```bash
python scripts/validate_v4470_release.py
PYTHONPATH=backend python -m pytest -q \
  backend/tests/test_v4470_spatiotemporal_cross_layer_engine.py \
  backend/tests/test_v4460_unified_spatial_evidence_registry.py \
  backend/tests/test_release_reconciliation_invariants.py \
  backend/tests/test_source_reconciliation_v4410.py \
  backend/tests/test_v4410_preserves_v44003_homepage_ticker.py \
  backend/tests/test_energy_spatial_global_v4410.py \
  backend/tests/test_energy_runtime_consumer.py
python -m compileall -q backend/app
php -l wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php
bash -n deploy/contabo/upgrade_site_intelligence_backend_v4_47_0_contabo.sh
```

## Runtime verification

Verify `/health`, `/public/build-info`, `/public/release-gate`, `/public/routes/summary`, `/public/spatial-evidence/registry`, and all `/public/spatiotemporal/*` contracts after deployment.

The deployment script promotes 29 release-bound static files while preserving dynamic production data and credentials.
