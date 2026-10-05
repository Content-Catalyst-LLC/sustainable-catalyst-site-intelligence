# Site Intelligence v4.49.0 — Install and Verify

## Local certification

```bash
python scripts/validate_v4490_release.py
PYTHONPATH=backend python -m pytest -q \
  backend/tests/test_v4490_live_geospatial_event_fusion.py \
  backend/tests/test_v4480_spatial_relationship_infrastructure_graph.py \
  backend/tests/test_v4470_spatiotemporal_cross_layer_engine.py \
  backend/tests/test_v4460_unified_spatial_evidence_registry.py \
  backend/tests/test_release_reconciliation_invariants.py \
  backend/tests/test_source_reconciliation_v4410.py \
  backend/tests/test_v4410_preserves_v44003_homepage_ticker.py \
  backend/tests/test_energy_spatial_global_v4410.py \
  backend/tests/test_energy_runtime_consumer.py
```

Expected current-release result: `79 passed`.

## Contabo

Deploy with `deploy/contabo/upgrade_site_intelligence_backend_v4_49_0_contabo.sh`. The script preserves dynamic `backend/data/` content and credentials, then explicitly promotes all 31 certified release-bound policy/registry files, including `live_geospatial_event_fusion_registry_v4490.json`.

After deployment verify `/health`, `/public/live-geospatial/registry`, `/public/live-geospatial/sources`, `/public/routes/summary`, and `/public/release-gate`.

## WordPress

Install the v4.49.0 plugin ZIP with `--force --activate`. WordPress remains a thin shell/embed bridge; no new feature-specific shortcode is introduced.
