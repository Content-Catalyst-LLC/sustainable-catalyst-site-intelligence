# Site Intelligence v4.48.0 — Install and Verify

## Local certification

```bash
python scripts/validate_v4480_release.py
PYTHONPATH=backend python -m pytest -q \
  backend/tests/test_v4480_spatial_relationship_infrastructure_graph.py \
  backend/tests/test_v4470_spatiotemporal_cross_layer_engine.py \
  backend/tests/test_v4460_unified_spatial_evidence_registry.py \
  backend/tests/test_release_reconciliation_invariants.py \
  backend/tests/test_source_reconciliation_v4410.py \
  backend/tests/test_v4410_preserves_v44003_homepage_ticker.py \
  backend/tests/test_energy_spatial_global_v4410.py \
  backend/tests/test_energy_runtime_consumer.py
python -m compileall -q backend/app
node --check backend/public_app/assets/app.js
node --check backend/public_app/service-worker.js
node --check wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js
php -l wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php
bash -n deploy/contabo/upgrade_site_intelligence_backend_v4_48_0_contabo.sh
```

Expected current release test result: `63 passed`.

## Runtime verification

Verify `/health`, `/public/build-info`, `/public/release-gate`, `/public/routes/summary`, `/public/spatial-evidence/registry`, `/public/spatiotemporal/registry`, and all `/public/spatial-graph/*` contracts after deployment.

The deployment script promotes 30 release-bound static files while preserving dynamic production data and credentials.
