# Sustainable Catalyst Site Intelligence

**Version:** 0.9.0  
**Build:** Admin Registry Manager and Source Control Tools

Sustainable Catalyst Site Intelligence is a FastAPI + WordPress plugin layer for interpreting Sustainable Catalyst analytics, search visibility, publishing strategy, public dashboards, external data connectors, reports, and AI-assisted briefs.

## v0.9.0 release

v0.9.0 adds the administrative control plane needed before the public flagship release. It gives the site owner a private overview of what exists, what is connected, what is public, what is private, and which registry/source files control the platform.

### New backend endpoints

```text
/admin/registry
/admin/registry/coverage
/admin/sources
/admin/modules
/admin/shortcodes
/admin/diagnostics
/admin/visibility
/admin/source-control
/intelligence/admin
```

### New WordPress shortcodes

```text
[sc_site_intelligence_admin_overview]
[sc_site_intelligence_shortcode_catalog]
[sc_site_intelligence_module_status]
```

Keep these shortcodes on private/admin-only pages.

### Admin control-plane features

- Registry Manager: hub counts, content-type counts, article-map counts, missing repository links, missing Workbench tool IDs, missing next-paths, and registry grouping.
- Source Manager: content registry file, external connector registry file, live/fallback settings, cache settings, Search Console mode, public-dashboard mode, AI-provider mode, and optional API-key status without exposing secret values.
- Module Manager: private/public visibility, endpoint groups, shortcode groups, and module-level notes.
- Shortcode Catalog: every known shortcode grouped by category, visibility, endpoint, and placement purpose.
- Diagnostics: backend version, registry/source file status, API token presence, GA4 mode, Search Console mode, public dashboard mode, and AI provider mode.
- Source Control Tools: read-only audit mode, managed file list, safe Git workflow, and secret-handling guardrails.

## Deployment

Render build command:

```bash
pip install -r backend/requirements.txt
```

Render start command:

```bash
cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

After deployment, test:

```bash
curl "https://sustainable-catalyst-site-intelligence.onrender.com/"
```

Expected version:

```json
{"version":"0.9.0"}
```

## Required configuration

No new Render environment variables are required for v0.9.0.

Existing key variables still apply:

```text
SC_SI_ENVIRONMENT=production
SC_SI_API_TOKEN=<private-token>
SC_SI_CORS_ORIGINS=https://sustainablecatalyst.com
SC_SI_REGISTRY_PATH=backend/data/site_registry.seed.json
```

Optional variables remain available for GA4, Search Console, external connectors, and Gemini.

## Security notes

- Admin control-plane endpoints are protected by the existing Site Intelligence API token on the backend.
- WordPress admin REST routes require `manage_options`.
- Source-control tools are read-only in v0.9.0.
- Do not commit API tokens, Google service-account JSON, Gemini keys, EIA keys, or EPA AQS credentials.
