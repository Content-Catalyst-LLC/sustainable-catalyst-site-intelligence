# Install and Verify — Site Intelligence v4.55.0

## Local certification

```bash
python scripts/validate_v4550_release.py
PYTHONPATH=backend python -m pytest -q backend/tests/test_v4550_spatial_provenance_lineage.py
python -m compileall -q backend/app
bash -n deploy/contabo/upgrade_site_intelligence_backend_v4_55_0_contabo.sh
```

## Contabo deployment

```bash
/tmp/upgrade_site_intelligence_backend_v4_55_0_contabo.sh \
  /tmp/sustainable-catalyst-site-intelligence-backend-v4.55.0.zip
```

Expected deployment markers:

```text
PASS: 38 release-bound policies aligned to 4.55.0
PASS: Site Intelligence v4.55.0 spatial provenance and transformation lineage verified
PASS: Site Intelligence v4.55.0 backend deployed and verified.
```

## Runtime checks

Check `/health`, `/public/spatial-lineage/registry`, `/public/spatial-lineage/transformation-types`, `/public/routes/summary`, and `/public/release-gate`.
