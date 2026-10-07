# Install and Verify — Site Intelligence v4.55.1

Deploy the backend first. The v4.55.1 backend carries the repaired public application shell and workspace controllers.

## Contabo

```bash
chmod +x /tmp/upgrade_site_intelligence_backend_v4_55_1_contabo.sh
/tmp/upgrade_site_intelligence_backend_v4_55_1_contabo.sh \
  /tmp/sustainable-catalyst-site-intelligence-backend-v4.55.1.zip
```

Expected deployment markers:

```text
PASS: 38 release-bound policies aligned to 4.55.1
PASS: six core workspace production-truth surfaces aligned
PASS: Site Intelligence v4.55.1 core workspace runtime repair verified
PASS: Site Intelligence v4.55.1 backend deployed and verified.
```

## Runtime checks

Verify `/health`, `/public/workspaces/production-truth`, `/public/routes/summary`, and `/public/release-gate`, then open each route:

```text
/app/?view=dossiers
/app/?view=economics
/app/?view=law
/app/?view=science
/app/?view=humanitarian
/app/?view=resources
```

The six route surfaces must remain visible even if an optional public catalog is unavailable. A degraded state may be shown; a blank or hidden workspace is a failure.

## WordPress

Install the v4.55.1 plugin only after the backend reports 4.55.1. WordPress remains a thin shell pointing at the standalone FastAPI app.
