# Site Intelligence v4.42.1 Release Certification

## Release

**v4.42.1 — Release Identity, Static Policy & Certification Reconciliation**

This maintenance release repairs release-state drift left after v4.42.0. It does not add a new analytical domain and does not widen the WordPress shortcode registry.

## Certified invariants

- Canonical backend version: `4.42.1`.
- WordPress plugin version and release ID: `4.42.1` / `site-intelligence-v4.42.1`.
- README, standalone runtime, standalone shell marker, and retained Render manifests use the same release identity.
- All 27 release-bound static policy/registry files advertise `4.42.1` as their runtime compatibility version.
- Historical policy origin metadata such as `release_id: site-intelligence-v4.35.5` remains unchanged.
- Energy Systems handoff consumer derives its consumer version from `APP_VERSION`.
- v4.42.0 shortcode containment is preserved exactly: 68 currently published Site Intelligence shortcodes plus 4 protected canonical entry points, 72 retained shortcodes total.
- Protected canonical entry points remain:
  - `sc_earth_observation_studio`
  - `sc_live_event_intelligence`
  - `sc_global_country_intelligence`
  - `sc_site_intelligence_embed`

## Local certification

From the repository root:

```bash
python3 scripts/validate_v4421_release.py
PYTHONPATH=backend python3 -m pytest -q \
  backend/tests/test_v4421_release_reconciliation.py \
  backend/tests/test_source_reconciliation_v4410.py \
  backend/tests/test_v4410_preserves_v44003_homepage_ticker.py \
  backend/tests/test_energy_spatial_global_v4410.py \
  backend/tests/test_energy_runtime_consumer.py
python3 -m compileall -q backend/app
php -l wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php
```

## Deployment acceptance

After backend deployment, verify that `/health` and `/public/build-info` report `4.42.1`, and that the WordPress plugin reports `4.42.1`. The WordPress shortcode registry must continue compiling without a `regular expression is too large` PCRE warning.
