# Changelog

## 1.8.0
- Added Live Disaster, Displacement, and Humanitarian Intelligence.
- Added GDACS, ReliefWeb, USGS, NASA EONET, and UNHCR source contracts.
- Added crisis map, report stream, displacement context, source registry, methodology, and export endpoints.
- Added matching WordPress shortcodes and public proxy routes.
- Preserved connector reliability, freshness, schema validation, and last-known-good behavior.


- Added a nine-boundary public observatory with safe-operating-space reference categories.
- Added boundary detail, assessment milestone, source, methodology, and export endpoints.
- Added scientific-status, coverage, derivation, and source-freshness labels.
- Added WordPress observatory, detail, trend, source, methodology, and export shortcodes.
- Preserved the v1.6.1 connector reliability, cache, freshness, and schema-validation layer.

## 1.8.0 — Connector Reliability, Freshness and Schema Validation

- Added retries with bounded exponential backoff.
- Added circuit breakers and rate-limit-aware status metadata.
- Added stale-while-revalidate and last-known-good connector states.
- Added source-specific response checks and normalized observation validation.
- Added freshness thresholds, cache diagnostics, reliability endpoints, WordPress routes, and shortcodes.
- Updated backend and WordPress versions to 1.8.0.

# Changelog

## 1.6.0 — Sustainable Development Data Connectors and Public Source Registry

- Added a normalized sustainable-development source registry and observation schema.
- Added NASA EONET and NASA POWER connector registrations.
- Added UN SDG, World Bank Indicators/PIP, UNESCO UIS, FAOSTAT, UN-Water, and OECD source registrations.
- Added planetary-boundaries definitions, control-variable mappings, and derived-assessment boundaries.
- Added public source-family, source-health, methodology, and registry endpoints.
- Added five WordPress public shortcodes and proxy endpoints.
- Added freshness, cache, fallback, provenance, and public-safety labels.



## v1.5.0 — Source-Aware Briefs and Dashboard Exports

- Added public source-aware brief endpoints for Site Intelligence, indicator dashboards, and source health.
- Added public dashboard export manifest and export bundle endpoints.
- Added copy-ready Markdown and CSV-preview export payloads.
- Added WordPress shortcodes for brief directories, source briefs, dashboard exports, and export visual QA.
- Added public-safe source citation policy and private-field exclusions for export pages.


## v1.4.0 — Public Indicator Dashboards and Chart Layer

- Added public indicator dashboard endpoints for sustainability, development, source health, research metadata, and repository intelligence.
- Added chart-ready public JSON specs for Site Intelligence indicator dashboards.
- Added WordPress shortcodes for indicator dashboard directory, chart dashboards, chart gallery, and chart visual QA.
- Added public-safe WordPress fallback chart rendering with no external chart dependency.
- Added tests and documentation for the v1.4.0 chart layer.

## v1.4.0 — Connector Reliability Patch and Public Status Polish

- Updated backend and WordPress plugin versions to 1.4.0.
- Added connector reliability scoring and reliability-count payloads for public connector panels.
- Added public status-card payloads with display mode, cache state, freshness state, and recovery guidance.
- Added public endpoints `/public/connectors/reliability` and `/public/connectors/status-polish`.
- Added WordPress shortcodes `[sc_public_connector_reliability]` and `[sc_public_connector_status_polish]`.
- Added JavaScript and CSS polish for reliability labels, status cards, cache-state labels, freshness-state labels, and recovery actions.
- Added admin-safe recovery queue metadata without exposing secrets, raw upstream payloads, or private diagnostics.
- Added backend tests for v1.4.0 reliability, status polish, and public endpoint behavior.

## v1.3.0 — Live API Connectors, Caching, and Public Source Status

- Added public connector status endpoints for live/cached/fallback source readiness.
- Added public cache and freshness summaries for connector panels.
- Added connector detail endpoints for World Bank, OpenAlex, Crossref, GitHub, and Environmental connectors.
- Added admin-safe connector diagnostics that do not expose secrets or raw payloads.
- Added WordPress shortcodes for public connector status, cache status, freshness, and connector detail panels.

## 1.2.1 — Public Source Pages and Indicator Integration Polish

- Updated backend and WordPress plugin versions to 1.2.1.
- Added public source-page directory, navigation, template, and visual-QA endpoints.
- Added WordPress shortcodes for source page directory, source navigation, source page templates, and source page visual QA.
- Added source-page CSS polish, active link styling, and nowrap helpers.
- Added backend tests for public source pages and template payloads.
- Added documentation for public source/indicator page setup.

## 1.2.0 — Public API Source Expansion and Live Indicator Layer

- Updated backend and WordPress plugin versions to 1.2.0.
- Added public API source expansion payloads for source families, source health, development indicators, research metadata, publication metadata, repository intelligence, public indicator overview, and sustainability indicator context.
- Added public endpoints for `/public/sources`, `/public/sources/health`, `/public/sources/development-indicators`, `/public/sources/research-metadata`, `/public/sources/publications`, `/public/sources/repositories`, `/public/indicators/overview`, and `/public/indicators/sustainability`.
- Added WordPress shortcodes for `[sc_public_api_sources]`, `[sc_public_source_health]`, `[sc_public_development_indicators]`, `[sc_public_research_metadata]`, `[sc_public_publication_metadata]`, `[sc_public_repository_intelligence]`, `[sc_public_indicator_overview]`, and `[sc_public_sustainability_indicators]`.
- Added JavaScript rendering for public source panels and source-health/indicator labels.
- Added CSS polish for public API source panels.
- Added v1.2.0 backend tests for public-safe source payloads and endpoints.


## 1.1.1 — Public Topic Page Templates and Navigation Polish

- Updated backend and WordPress plugin versions to 1.1.1.
- Added canonical `/platform/site-intelligence/` page-path metadata for public topic dashboards.
- Added public dashboard navigation endpoint `/public/navigation`.
- Added public topic-page template endpoint `/public/page-templates`.
- Added public topic-page visual QA endpoint `/public/topic-page-visual-qa`.
- Added WordPress shortcodes `[sc_public_dashboard_navigation]`, `[sc_public_topic_page_templates]`, and `[sc_public_topic_page_visual_qa]`.
- Added JavaScript active-link detection for Site Intelligence, Platform, and homepage links.
- Added CSS helpers for active dashboard buttons and controlled nowrap text polish.
- Updated admin shortcode/module catalogs to include public topic dashboard helpers.
- Added v1.1.1 tests for navigation, page templates, metadata, and visual QA.

## 1.1.0 — Public Topic Dashboards and Source Pages

- Added public dashboard directory endpoint `/public/dashboards`.
- Added public-safe topic dashboard endpoints for climate/energy, environmental monitoring, biodiversity/land use, knowledge-system, and search/discovery pages.
- Added public source-methodology endpoint `/public/source-methodology`.
- Added WordPress shortcodes for public topic dashboard pages and source methodology.
- Added JavaScript renderers for topic dashboard cards, section pipelines, source-methodology rows, and dashboard-directory output.
- Added CSS alignment for topic dashboard modules using the current Sustainable Catalyst public-platform visual language.
- Added v1.1.0 backend tests for public topic dashboard payloads and public-safe boundaries.

## 1.0.1 — Public Shortcode Visual Alignment

- Updated WordPress plugin version to 1.0.1.
- Updated backend version to 1.0.1 for deployment verification.
- Added a public-shortcode visual alignment layer for `[sc_public_site_intelligence]`, `[sc_public_knowledge_overview]`, `[sc_public_climate_energy_summary]`, and `[sc_public_methodology]`.
- Restyled public shortcode modules to match the current Sustainable Catalyst public-platform style: cream panels, black top rules, red accent labels, compact uppercase buttons, square cards, and methodology-style rows.
- Added CSS handling for public shortcodes embedded inside the custom `ccp-site-intelligence-public` page shell, preventing nested legacy-card appearance.
- Clarified that `[sc_site_intelligence_public_flagship]` is for standalone all-in-one pages, while custom HTML pages should use the four smaller public shortcodes.

## 1.0.0 — Public Flagship Release

- Added v1.0.0 release status endpoint for launch readiness review.
- Added release checklist endpoint for final public/private boundary, methodology, metadata, WordPress, and smoke-test checks.
- Added production smoke-test endpoint with release-critical endpoint map and post-deploy commands.
- Added public release summary endpoint with public value statement, boundaries, recommended page metadata, and launch placement guidance.
- Added private WordPress shortcode `[sc_site_intelligence_release_status]` for release review pages.
- Added release module and release shortcode to the admin catalog.
- Updated backend, WordPress plugin, JavaScript event metadata, README, and docs to v1.0.0.
- Added v1.0.0 tests for release endpoints, metadata, smoke checks, and admin catalog integration.

## 0.10.1 — Public Dashboard Visual QA and Copy Polish

- Added public-dashboard visual QA endpoint for final public page review.
- Added WordPress visual QA shortcode for private/review pages.
- Polished flagship dashboard copy, safety language, CTA labels, and empty-state messaging.
- Added mobile/spacing/readability QA checks and copy-ready public page notes.
- Added v0.10.1 tests for visual QA payloads and shortcode catalog registration.

## 0.10.0 — Public Flagship Dashboard Page Builder

- Added public-safe page-builder endpoints.
- Added flagship public dashboard shortcode.
- Added copy-ready shortcode bundles and public page presets.
- Added public release checklist and methodology-forward page guidance.
- Added v0.10.0 tests for public-safe defaults, shortcodes, and admin catalog integration.

## v0.9.1 — WordPress Admin UX Polish and Diagnostic Stabilization

- Added fast admin status endpoint.
- Added connection-check endpoint for backend, token, registry, source, public dashboard, Search Console, and AI provider status.
- Added public-readiness check for public/private dashboard boundaries.
- Added one-click diagnostic summary endpoint.
- Added private diagnostic summary and connection-check shortcodes.
- Polished WordPress settings page with operational cards, diagnostic links, and public/private warnings.
- Improved JavaScript rendering for admin diagnostics and copyable shortcode rows.

## v0.9.0 — Admin Registry Manager and Source Control Tools

- Added registry manager, source manager, module manager, shortcode catalog, visibility matrix, source-control guidance, and admin overview.
