# Site Intelligence v4.50.0 — Install & Verify

## Local certification

```bash
python scripts/validate_v4500_release.py

PYTHONPATH=backend python -m pytest -q \
  backend/tests/test_v4500_global_source_federation.py \
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

Expected: `93 passed`.

## Production backend

```bash
/tmp/upgrade_site_intelligence_backend_v4_50_0_contabo.sh \
  /tmp/sustainable-catalyst-site-intelligence-backend-v4.50.0.zip
```

Verify:

```bash
curl -fsS http://127.0.0.1:8091/health | python3 -m json.tool
curl -fsS http://127.0.0.1:8091/public/source-federation/registry | python3 -m json.tool
curl -fsS http://127.0.0.1:8091/public/source-federation/regions | python3 -m json.tool
curl -fsS http://127.0.0.1:8091/public/routes/summary | python3 -m json.tool
curl -fsS http://127.0.0.1:8091/public/release-gate | python3 -m json.tool
```

Expected core inventory: version 4.50.0; registry 1.7.0; 1409 routes; 100 modularized; 21 capabilities; 0 unclassified.

## WordPress

Install `sustainable-catalyst-site-intelligence-wordpress-v4.50.0.zip` with `--force --activate`, flush Site Intelligence transients/cache/rewrite rules, and confirm plugin version 4.50.0. WordPress remains `thin-shell-and-embed-bridge`.
