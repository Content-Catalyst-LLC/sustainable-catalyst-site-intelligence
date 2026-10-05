# v4.52.0 Install & Verify

Run the release validator and current-contract suite before deployment:

```bash
python scripts/validate_v4520_release.py
PYTHONPATH=backend python -m pytest -q \
  backend/tests/test_v4520_predictive_spatial_intelligence_consumer.py \
  backend/tests/test_v4510_spatial_research_handoffs.py \
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

Expected current-contract result: **133 passed**.

Contabo deployment helper:

```bash
/tmp/upgrade_site_intelligence_backend_v4_52_0_contabo.sh \
  /tmp/sustainable-catalyst-site-intelligence-backend-v4.52.0.zip
```

After deployment verify `/health`, `/public/predictive-spatial/registry`, `/public/predictive-spatial/providers`, `/public/routes/summary`, and `/public/release-gate`.
