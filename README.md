# Sustainable Catalyst Site Intelligence v0.7.0

Site Intelligence is the analytics, search, SEO, registry, external data, public dashboard, and reporting intelligence layer for Sustainable Catalyst.

Version **0.7.0 — Report Generator and Export Intelligence** turns the dashboard system into exportable planning reports.

## Core modules

- GA4 analytics intelligence
- Registry and article-map intelligence
- Event and conversion validation
- External source connectors
- Search Console and SEO intelligence
- Metadata, title, and internal-link intelligence
- Sitemap, indexing, and coverage intelligence
- Publishing strategy intelligence
- Public dashboard framework
- Advanced external data connectors
- Report generator and export intelligence

## New in v0.7.0

The report generator creates structured internal reports with:

- title
- summary
- generated timestamp
- source notes
- highlights
- recommendations
- report sections
- methodology/privacy notes
- JSON, Markdown, and CSV export support

## Backend endpoints

Protected report endpoints:

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

Each report endpoint supports:

```text
?format=json
?format=markdown
?format=csv
```

Example:

```bash
curl -H "X-SC-Intelligence-Token: $SC_SI_API_TOKEN" \
  "https://sustainable-catalyst-site-intelligence.onrender.com/reports/site-intelligence?format=markdown"
```

Combined export bundle:

```bash
curl -H "X-SC-Intelligence-Token: $SC_SI_API_TOKEN" \
  "https://sustainable-catalyst-site-intelligence.onrender.com/reports/export?report=site,search,content&format=csv"
```

## WordPress shortcodes

Private/internal report panels:

```text
[sc_site_intelligence_report]
[sc_search_intelligence_report]
[sc_content_strategy_report]
[sc_external_sources_report]
[sc_climate_energy_report]
[sc_indexing_report]
[sc_report_export_bundle]
```

Recommended private report page:

```text
[sc_site_intelligence_report]

[sc_search_intelligence_report]

[sc_content_strategy_report]

[sc_external_sources_report]

[sc_climate_energy_report]

[sc_indexing_report]

[sc_report_export_bundle]
```

## Required Render variables

Existing v0.6.0 variables still apply. No new required variables are added in v0.7.0.

```text
SC_SI_ENVIRONMENT=production
SC_SI_DEMO_MODE=false
SC_SI_API_TOKEN=<private-token>
SC_SI_GA4_PROPERTY_ID=<numeric-ga4-property-id>
SC_SI_GOOGLE_APPLICATION_CREDENTIALS_JSON=<one-line-service-account-json>
SC_SI_CORS_ORIGINS=https://sustainablecatalyst.com
SC_SI_REGISTRY_PATH=backend/data/site_registry.seed.json
SC_SI_SEARCH_CONSOLE_SITE_URL=https://sustainablecatalyst.com/
```

## Public/private rule

Report endpoints are intended for internal planning. Public-facing pages should use the public dashboard framework instead:

```text
[sc_site_intelligence_public_landing]
[sc_public_site_intelligence]
[sc_public_knowledge_overview]
[sc_public_climate_energy_summary]
[sc_public_methodology]
```

Do not expose raw reports publicly until they have been manually reviewed and sanitized.
