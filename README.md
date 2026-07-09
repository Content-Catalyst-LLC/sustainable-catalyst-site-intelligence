# Sustainable Catalyst Site Intelligence

**Version:** 0.7.1  
**Build:** Export Bundle Timeout Patch

Site Intelligence is a custom backend and WordPress bridge for Sustainable Catalyst. It combines GA4 analytics, Search Console intelligence, registry/page mapping, event validation, external data connectors, public dashboard summaries, and report/export tools.

## v0.7.1 Patch

v0.7.1 fixes a WordPress timeout issue on the export bundle shortcode. The previous default `/reports/export` call attempted to assemble all report payloads at once, which could exceed the WordPress proxy timeout window.

The endpoint now behaves as follows:

- `/reports/export` returns a lightweight manifest suitable for WordPress pages.
- `/reports/export?full=true` returns the complete combined report bundle for direct internal use.
- `/reports/export?full=true&format=markdown` returns a full Markdown bundle.
- `/reports/export?full=true&format=csv` returns a full flattened CSV bundle.

For WordPress pages, use the shortcode normally:

```text
[sc_report_export_bundle]
```

For large exports, call individual report endpoints or the `full=true` export directly from Terminal/internal workflows.

## Core Report Endpoints

```text
/reports/site-intelligence
/reports/search-intelligence
/reports/content-strategy
/reports/external-sources
/reports/climate-energy
/reports/indexing
/reports/export
/intelligence/reports
```

All private report endpoints require `X-SC-Intelligence-Token`.

## Required Render Variables

```text
SC_SI_ENVIRONMENT=production
SC_SI_DEMO_MODE=false
SC_SI_API_TOKEN=<private-token>
SC_SI_CORS_ORIGINS=https://sustainablecatalyst.com
SC_SI_GA4_PROPERTY_ID=<numeric-ga4-property-id>
SC_SI_GOOGLE_APPLICATION_CREDENTIALS_JSON=<one-line-service-account-json>
SC_SI_REGISTRY_PATH=backend/data/site_registry.seed.json
SC_SI_SEARCH_CONSOLE_LIVE=true
SC_SI_SEARCH_CONSOLE_SITE_URL=https://sustainablecatalyst.com/
```

Optional external-source variables:

```text
SC_SI_EIA_API_KEY=
SC_SI_EPA_AQS_EMAIL=
SC_SI_EPA_AQS_KEY=
```

## Deployment

Build command:

```bash
pip install -r backend/requirements.txt
```

Start command:

```bash
cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Health/root check:

```bash
curl https://sustainable-catalyst-site-intelligence.onrender.com/
```

Expected version:

```json
{"version":"0.7.1"}
```
