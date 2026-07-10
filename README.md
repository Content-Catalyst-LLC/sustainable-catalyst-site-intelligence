
## v1.12.1 Cross-Domain Intelligence and Public Dashboard Studio

The dashboard studio composes existing Site Intelligence domains into reusable public experiences rather than hard-coding every dashboard. It includes flagship climate-and-vulnerability, conflict-and-development, international-law-and-humanitarian, and country-intelligence configurations.

Public endpoints begin at `/public/dashboard-studio`, with country profiles at `/public/country-intelligence/{country_code}` and comparisons at `/public/cross-domain-comparison`. WordPress includes directory, dashboard, country, comparison, source, and export shortcodes. Cross-domain views preserve original definitions, units, reference periods, freshness, uncertainty, and procedural status; they do not create a proprietary composite score or imply causality.

# Sustainable Catalyst Site Intelligence

## v1.10.0 — International Law and Global Governance Monitor

Adds source-aware public monitoring for sanctions, treaties, UN decisions, courts, human rights, EU law, and trade governance. The monitor preserves procedural status and authoritative-source links and does not provide legal advice or compliance determinations.

Current version: v1.12.1 — Conflict, Displacement and Human Security

# Sustainable Catalyst Site Intelligence

Version: 1.12.1

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


## v1.5.0 — Source-Aware Briefs and Dashboard Exports

Adds public source-aware brief payloads, dashboard export manifests, copy-ready Markdown export summaries, public source endpoint citations, and WordPress shortcodes for reviewed Site Intelligence handoff pages.

New endpoints include `/public/source-aware-briefs`, `/public/dashboard-exports`, and `/public/dashboard-exports/visual-qa`.


## v1.6.0 Sustainable Development Data Layer

Initial public-source registry and connector contracts for NASA EONET, NASA POWER, the UN SDG database, World Bank development and poverty data, UNESCO education data, FAOSTAT, UN-Water SDG 6, and OECD SDMX. Includes a planetary-boundaries adapter registry, normalized observation schema, freshness classes, public health endpoints, and WordPress shortcodes.


## v1.6.1 Connector Reliability

Adds retry and exponential backoff, circuit breakers, rate-limit awareness, stale-while-revalidate cache states, last-known-good fallbacks, explicit freshness thresholds, connector response validation, and public reliability/schema/cache endpoints.


## v1.7.0 Planetary Boundaries Observatory

Public endpoints:

- `/public/planetary-boundaries`
- `/public/planetary-boundaries/overview`
- `/public/planetary-boundaries/{boundary_id}`
- `/public/planetary-boundaries/{boundary_id}/trend`
- `/public/planetary-boundaries/{boundary_id}/sources`
- `/public/planetary-boundaries/methodology`
- `/public/planetary-boundaries/export`

WordPress shortcodes:

- `[sc_planetary_boundaries_observatory]`
- `[sc_planetary_boundary_overview]`
- `[sc_planetary_boundary id="climate-change"]`
- `[sc_planetary_boundary_trend id="climate-change"]`
- `[sc_planetary_boundary_sources]`
- `[sc_planetary_boundary_methodology]`
- `[sc_planetary_boundary_export]`


## v1.8.0 — Live Disaster, Displacement, and Humanitarian Intelligence

Adds source-aware GDACS, ReliefWeb, USGS earthquake, NASA EONET, and UNHCR integration contracts; a normalized humanitarian-event schema; crisis-map, report-stream, displacement-context, methodology, and export endpoints; and matching WordPress shortcodes. Live network retrieval remains governed by connector reliability, caching, source freshness, and last-known-good safeguards.


## v1.9.0 — Human Development and Social Conditions

Public source-aware observatory coverage now includes poverty, inequality, health, education, decent work, food security, and water and sanitation. The release adds domain detail, country profile, inequality-dimension, methodology, and export contracts while preserving source definitions, reference periods, revisions, and modeled-estimate labels.

## v1.12.1 — Conflict, Displacement and Human Security

The human-security layer connects conflict-event sources, civilian-protection reporting, forced-displacement statistics, mobility assessments, infrastructure disruption, humanitarian-access records, and explicitly labeled modeled risk. It preserves source methodology, reference periods, geographic precision, confidence, revisions, and responsible-data limits.

Public endpoints begin at `/public/human-security`. WordPress shortcodes include `[sc_conflict_human_security_monitor]`, `[sc_conflict_event_stream]`, `[sc_human_security_monitor]`, `[sc_forced_displacement_flows]`, `[sc_modeled_human_security_risk]`, `[sc_human_security_sources]`, `[sc_human_security_methodology]`, and `[sc_human_security_export]`.


## v1.13.0 geospatial visualization

Interactive mapping, NASA satellite imagery, live USGS/NASA event markers, heat maps, time controls, legends, accessible tables, and WordPress embeds.
