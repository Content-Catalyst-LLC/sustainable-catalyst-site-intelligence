# Sustainable Catalyst Site Intelligence

Current version: v1.4.0 — Public Indicator Dashboards and Chart Layer

# Sustainable Catalyst Site Intelligence

Version: 1.4.0

## v1.4.0 — Connector Reliability Patch and Public Status Polish

This patch improves the v1.3.0 connector layer with clearer public reliability labels, status cards, cache-state labels, freshness-state labels, and recovery guidance. It is intended to make public source-health pages easier to read while keeping credentials, raw upstream payloads, backend logs, and private diagnostics hidden.

New public connector endpoints:

- `/public/connectors/reliability`
- `/public/connectors/status-polish`

New WordPress shortcodes:

- `[sc_public_connector_reliability]`
- `[sc_public_connector_status_polish]`

Recommended placement:

- Use `[sc_public_connector_status]` and `[sc_public_connector_reliability]` on `/platform/site-intelligence/source-health/`.
- Use `[sc_public_cache_status]`, `[sc_public_source_freshness]`, and `[sc_public_connector_status_polish]` on source methodology or source-status review pages.
- Use connector-specific shortcodes only on focused source pages or expandable detail sections.

## v1.3.0 — Live API Connectors, Caching, and Public Source Status

This release adds the public connector status layer for Site Intelligence. It exposes public-safe readiness labels, cache policy, freshness labels, and connector detail panels for World Bank, OpenAlex, Crossref, GitHub, and environmental source families. Public endpoints return curated status metadata and methodology notes, not credentials, raw upstream payloads, backend logs, or private analytics.

New public connector endpoints:

- `/public/connectors/status`
- `/public/connectors/cache`
- `/public/connectors/freshness`
- `/public/connectors/world-bank`
- `/public/connectors/openalex`
- `/public/connectors/crossref`
- `/public/connectors/github`
- `/public/connectors/environmental`

New admin-safe endpoint:

- `/admin/connectors/diagnostics`

New WordPress shortcodes:

- `[sc_public_connector_status]`
- `[sc_public_cache_status]`
- `[sc_public_source_freshness]`
- `[sc_public_world_bank_connector]`
- `[sc_public_openalex_connector]`
- `[sc_public_crossref_connector]`
- `[sc_public_github_connector]`
- `[sc_public_environmental_connectors]`


Site Intelligence is the Sustainable Catalyst analytics, registry, external-source, reporting, AI-brief, public-dashboard, admin-control, and public flagship dashboard platform.


## v1.1.1 — Public Topic Page Templates and Navigation Polish

This patch locks in the public topic-page system introduced in v1.1.0. It adds canonical `/platform/site-intelligence/` page paths, reusable public dashboard navigation, copy-ready page-template metadata, active-page link behavior, visual QA for topic pages, and nowrap helpers for cleaner homepage/platform text wrapping.

New public shortcodes:

```text
[sc_public_dashboard_navigation]
[sc_public_topic_page_templates]
[sc_public_topic_page_visual_qa]
```

New public endpoints:

```text
/public/navigation
/public/page-templates
/public/topic-page-visual-qa
```

## v1.1.0 — Public Topic Dashboards and Source Pages

This release expands Site Intelligence beyond one flagship public page into a small public topic-dashboard ecosystem. It adds public-safe topic dashboard endpoints, WordPress shortcodes, a dashboard directory, and a source-methodology page.

New public shortcodes:

```text
[sc_public_dashboard_directory]
[sc_public_climate_energy_dashboard]
[sc_public_environmental_monitoring_dashboard]
[sc_public_biodiversity_land_use_dashboard]
[sc_public_knowledge_system_dashboard]
[sc_public_search_discovery_dashboard]
[sc_public_source_methodology]
```

New public endpoints:

```text
/public/dashboards
/public/dashboards/climate-energy
/public/dashboards/environmental-monitoring
/public/dashboards/biodiversity-land-use
/public/dashboards/knowledge-system
/public/dashboards/search-discovery
/public/source-methodology
```

## v1.0.1 — Public Shortcode Visual Alignment

This patch aligns the public shortcode output with the current Sustainable Catalyst public-platform visual system. It updates the WordPress public dashboard module styling for the smaller public shortcodes used inside the custom Site Intelligence page shell.

Public page shortcodes recommended for custom HTML:

```text
[sc_public_site_intelligence]
[sc_public_knowledge_overview]
[sc_public_climate_energy_summary]
[sc_public_methodology]
```

Keep `[sc_site_intelligence_public_flagship]` for a standalone all-in-one page only; do not nest it inside a custom page shell.

## v1.0.0 — Public Flagship Release

This release hardens the public-facing Site Intelligence dashboard for launch. It focuses on final public/private boundaries, stable public defaults, smoke-test guidance, release metadata, and production documentation rather than adding another broad feature layer.

### Public flagship shortcode

Use this on the public page:

```text
[sc_site_intelligence_public_flagship]
```

The flagship shortcode renders the public-safe stack:

- Public dashboard hero
- Public Site Intelligence
- Knowledge overview
- Climate, energy, and external-source snapshot
- Public methodology

### New release endpoints

Private/admin endpoints:

- `/release/status`
- `/release/checklist`
- `/release/smoke-test`

Public-safe endpoint:

- `/release/public-summary`

### New private/review shortcode

Use this only on private/admin review pages:

```text
[sc_site_intelligence_release_status]
```

### Suggested public page metadata

- Page title: `Site Intelligence`
- SEO title: `Site Intelligence: Public Dashboard for Sustainable Catalyst Knowledge Infrastructure`
- Meta description: `Explore Sustainable Catalyst Site Intelligence: a public-safe dashboard for knowledge architecture, platform tools, public data-source notes, and methodology boundaries.`

### Public/private boundary

Public pages should use only public-safe shortcodes unless a module has been manually reviewed. Keep the following private:

- Raw GA4 dashboards
- Search Console reports
- Conversion diagnostics
- Admin control panels
- Reports and exports
- AI-assisted internal briefs
- Source diagnostics and operational queues

### Deployment check

After pushing and redeploying Render, confirm:

```bash
curl "https://sustainable-catalyst-site-intelligence.onrender.com/"
```

Expected version:

```json
"version":"1.0.1"
```

Then install the v1.0.1 WordPress plugin ZIP and test the public flagship page logged out or in an incognito window.


## v1.3.0 — Live API Connectors, Caching, and Public Source Status

Adds public-safe connector status, cache policy, freshness, and connector detail panels for World Bank, OpenAlex, Crossref, GitHub, and environmental source families. Public endpoints expose readiness labels and methodology notes, not credentials or raw upstream payloads.


## v1.4.0 — Public Indicator Dashboards and Chart Layer

Adds public indicator dashboard endpoints, chart-ready JSON payloads, WordPress chart shortcodes, and visual QA for sustainability, development, source-health, research metadata, and repository intelligence dashboards.
