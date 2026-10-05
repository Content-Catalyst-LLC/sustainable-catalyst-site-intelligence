# Site Intelligence v4.46.0 — Install & Verify

## Current-contract certification

```bash
python scripts/validate_v4460_release.py
PYTHONPATH=backend python -m pytest -q \
  backend/tests/test_v4460_unified_spatial_evidence_registry.py \
  backend/tests/test_release_reconciliation_invariants.py \
  backend/tests/test_source_reconciliation_v4410.py \
  backend/tests/test_v4410_preserves_v44003_homepage_ticker.py \
  backend/tests/test_energy_spatial_global_v4410.py \
  backend/tests/test_energy_runtime_consumer.py
```

## New API surface

- `GET /public/spatial-evidence/registry`
- `GET /public/spatial-evidence/layers`
- `GET /public/spatial-evidence/layers/{layer_id}`
- `GET /public/spatial-evidence/domains`
- `GET /public/spatial-evidence/object-schema`
- `POST /public/spatial-evidence/objects/normalize`
- `POST /public/spatial-evidence/objects/validate`
- `GET /public/spatial-evidence/compatibility`

Existing `/public/spatial/*` routes are intentionally preserved.
