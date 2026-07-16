## 2.10.0 — Research Paths, Saved Investigations, and Briefing Workflows

- Added browser-local research paths and saved investigations.
- Added evidence sets, notes, checkpoints, saved public views, and JSON import/export.
- Added deterministic briefing packets and structured cross-product handoffs.
- Added public validation, schema, evidence-set, briefing, handoff, and diagnostics endpoints.
- Added `[sc_research_paths_investigations height="1650"]`.
- Preserved evidence classes and prohibited automatic factual, legal, predictive, ranking, or recommendation claims.

## 2.9.0 — Comparative Intelligence and Scenario Studio

- Added multi-geography indicator baskets and explicit compatibility warnings.
- Added catalog-based regional peer context without rankings.
- Added transparent percentage and absolute scenarios over compatible published baselines.
- Added correlation review with overlapping-period and no-causation safeguards.
- Added reproducible JSON comparison packets with SHA-256 integrity digests.
- Added `/app/?view=scenarios` and `[sc_comparative_intelligence_scenario_studio]`.
- Preserved the free-data, no-fabrication, no-silent-normalization, no-ranking, and no-forecast architecture.

## 2.8.0 — Alerts, Monitoring, and Live Intelligence Streams

- Added reconnectable public server-sent intelligence snapshots.
- Added browser-local alert rules with stateless backend evaluation.
- Added source-watch recency and availability diagnostics.
- Added deterministic monitoring digests and matched-signal CSV export.
- Added `/app/?view=alerts` and `[sc_alerts_monitoring_live_intelligence]`.
- Preserved no-fabrication, no-emergency-service, no-profile, no-risk-score, and free-data boundaries.

## 2.7.0 — Unified Country and Regional Intelligence Dossiers

- Added country and regional cross-domain dossiers.
- Added coverage matrices for conditions, indicators, economics, law, science, humanitarian evidence, and resources.
- Added two-country evidence coverage alignment without composite scoring or silent normalization.
- Added public dossier, facets, region, comparison, brief, and diagnostics endpoints.
- Added `/app/?view=dossiers` and `[sc_country_regional_intelligence_dossiers]`.
- Preserved free-source, no-fabrication, and responsible-use safeguards.

## 2.6.0 — Trade, Energy, and Resource Security Observatory

- Added `/app/?view=resources` and nine source-aware public endpoints.
- Added official trade, energy, food, agriculture, water, materials, supply-chain, and climate-transition record views.
- Added country profiles, counterpart relationship lists, global coverage mapping, CSV export, shareable views, and briefing handoff.
- Preserved units, periods, directions, classifications, source identity, frequency, license, and attribution.
- Added explicit no-risk-score, no-sanctions-screening, no-investment-advice, and no-fabrication safeguards.
- Added `[sc_trade_energy_resource_security_observatory height="1450"]`.

## 2.5.0 — Humanitarian, Conflict, and Displacement Observatory

- Added `/app/?view=humanitarian` and eight source-aware public endpoints.
- Combined non-fabricated Site Intelligence events with scoped Core live, legal, and official-statistics records.
- Added country, category, source, time-window, and text filters; global map; timeline; record explorer; CSV export; shareable views; and Decision Studio handoff.
- Added explicit responsible-data, non-advice, non-targeting, non-eligibility, and no-fabrication safeguards.
- Added `[sc_humanitarian_conflict_displacement_observatory height="1450"]`.
- Updated release metadata, public workspace registry, audit ledger, documentation, and regression tests to v2.5.0.

## 2.4.0 — Scientific and Earth Systems Observatory

- Added a public scientific and Earth systems workspace backed by Sustainable Catalyst Core v2.8.0.
- Added scientific record, asset, map-layer, STAC, time-series, brief, and diagnostics endpoints.
- Added source, quality, mission, instrument, license, attribution, date, variable, and file-format preservation.
- Added explicit distinctions among observations, forecasts, catalogs, telescope records, compounds, materials, and scientific datasets.
- Added a WordPress shortcode, saved-view state, CSV export, Workbench handoff, and responsive public interface.
- Added no-fabrication, no-clinical-advice, remote-sensing interpretation, and scientific-validation boundaries.
- Updated backend, standalone application, WordPress plugin, release metadata, documentation, and automated tests to v2.4.0.

## 2.3.0 — International Law and Global Governance Observatory

- Added the standalone `/app/?view=law` International Law and Global Governance Observatory.
- Added server-side, public-safe delivery of Core international-law records without exposing Core credentials to browser JavaScript.
- Added authority, record-type, legal-body, country, subject, date, and keyword filters.
- Added official-symbol, citation, procedural-status, adoption-date, publication-date, and canonical-source preservation.
- Added geographic country association mapping, chronological timeline, country legal profiles, and an authority matrix.
- Added CSV export, shareable URL state, Saved View integration, and Workbench and Decision Studio handoffs.
- Added explicit authority explanations and non-advice safeguards; the application does not infer binding effect, compliance, or legal conclusions from a document symbol alone.
- Added public observatory profile, records, facets, timeline, country-profile, authority-matrix, brief, and diagnostics endpoints.
- Added `[sc_international_law_governance_observatory height="1350"]` for WordPress.
- Added free-source-only configuration and explicit disabled, unavailable, degraded, stale, and connected states.
- Updated backend, standalone application, WordPress plugin, release metadata, documentation, and automated tests to v2.3.0.

## 2.2.0 — Economics, Markets, and Sustainability Signals

- Release hardening: filtered country, category, and source requests no longer inherit a `stale` state from unrelated cached events when no matching evidence exists.

- Added a server-side public bridge to Core economics and official-statistics records.
- Added economic-domain classification, precise data-timing labels, source-safe sanitization, geography mapping, time-series visualization, comparison, filtering, and CSV export.
- Added an explicit boundary against simulated or falsely labeled real-time exchange data.
- Added `/app/?view=economics` and `[sc_economics_sustainability_observatory]`.
- Preserved v2.1.0 global conditions and all earlier public workspaces.

# Changelog

## 2.1.0 — Global Conditions and Live Map Observatory

- Added a first-class Global Conditions workspace at `/app/?view=global`.
- Added a server-side public-read bridge to Sustainable Catalyst Core v2.8.0.
- Added sanitized Core GeoJSON features, map-layer registry records, and latest observation signals.
- Added an automatic local fallback to existing Site Intelligence events when Core is unavailable.
- Added visible freshness, quality, source, attribution, and integration-state handling.
- Added the `[sc_global_conditions_observatory]` WordPress shortcode.
- Preserved the zero-paid-provider architecture and existing v2.0.0 Auditable Public Observatory.


## 2.0.0 — Auditable Public Observatory

- Added a first-class `/app/?view=observatory` workspace for evidence records, lineage, integrity, release history, and verification boundaries.
- Added public observatory profile, catalog, audit-record, lineage, verification, release-ledger, diagnostics, and export endpoints.
- Added ten registered public audit artifacts spanning sources, methodology, Earth observation, events, country intelligence, comparison, thematic dashboards, briefing manifests, saved views, and the public release record.
- Added canonical UTF-8 JSON and SHA-256 integrity digests with explicit scope rules that exclude volatile timestamps.
- Added a non-persistent verification endpoint with payload-size limits, sensitive-field rejection, and optional expected-digest matching.
- Added a source → method → audit artifact → workspace lineage graph with public cross-reference diagnostics.
- Added JSON and Markdown audit packets plus a release ledger documenting the auditability contribution of releases 1.18.0 through 2.0.0.
- Added `[sc_auditable_public_observatory height="1250"]` for a dedicated WordPress observatory page.
- Redesigned the three legacy preview shortcodes as migration-safe aliases to the modern Earth, country, and comparison workspaces.
- Added the observatory route to browser-local saved views and shareable research paths.
- Preserved explicit missing-data, source-state, methodology, and responsible-use boundaries.
- Preserved Platform Core as optional and added no account system, telemetry vendor, paid database, Redis service, proprietary map service, or additional Render service.

## 1.25.0 — Public Launch and Portfolio Release

- Added a dedicated public launch and portfolio route at `/app/?view=launch`.
- Added a public product directory for Earth observation, events, country intelligence, comparison, thematic dashboards, briefing, sources, and saved research paths.
- Added public launch profile, checklist, materials, diagnostics, and portfolio endpoints.
- Added downloadable JSON and Markdown portfolio records.
- Added public positioning, technical architecture, research workflow, and responsible-use panels.
- Added Open Graph, social description, and Twitter-card metadata to the standalone application.
- Added `[sc_site_intelligence_launch]` while retaining `[sc_site_intelligence_app]` as the primary flagship embed.
- Added a v2.0.0 removal target for legacy country, comparison, and geospatial preview shortcodes.
- Added homepage, Platform page, LinkedIn, GitHub, social-preview, and demo-sequence launch copy.
- Preserved Platform Core as optional and added no account system, telemetry vendor, paid database, Redis service, or additional Render service.

## 1.24.0 — Accessibility, Performance, and Mobile Release

- Added public experience profile, checklist, and diagnostics endpoints with explicit first-party performance budgets.
- Added GZip middleware, app-shell no-cache behavior, short asset caching with stale-while-revalidate, and public-safe delivery headers.
- Replaced eager html2canvas loading with an on-demand PNG capture dependency.
- Added a complete phone navigation drawer exposing every public research workspace.
- Added route announcements, `aria-current`, visible focus hardening, Escape-close behavior, inert background content, and focus restoration.
- Added reduced-motion CSS and disabled timeline autoplay when reduced motion is requested.
- Added forced-colors support, safe-area padding, dynamic viewport units, 44px design touch targets, and compact-phone layouts.
- Removed mobile sticky-filter stacking that could create nested scrolling traps.
- Added below-fold `content-visibility` hints and requestAnimationFrame-throttled WordPress embed height messages.
- Changed WordPress standalone embeds to lazy loading, allowed clipboard-write explicitly, and restricted responsive height messages to the configured backend origin.
- Added the accessible-responsive-delivery methodology record and aligned backend, standalone app, WordPress plugin, documentation, and tests on v1.24.0.
- Preserved Platform Core as optional and added no account system, telemetry vendor, paid database, Redis service, proprietary map service, or additional Render service.

## 1.23.0 — Saved Views and Shareable Research Paths

- Added a first-class standalone `/app/?view=saved` workspace for browser-local research paths.
- Added Save view controls across the public application with accessible naming, local confirmation, and duplicate-name handling.
- Added portable `sc-saved-view/1.0` manifests containing public interface state, application version, stable ID, view name, timestamps, and route-specific parameters.
- Added browser-local storage under `sc_site_intelligence_saved_views_v1` with storage-unavailable and quota-failure handling.
- Added reopen, copy-link, export, duplicate, delete, export-all, import, and clear-all workflows.
- Added shareable research URLs for overview, Earth observation, country, event, comparison, thematic, briefing, and source-methodology views.
- Added map viewport restoration plus route-specific state restoration for imagery, events, comparisons, trends, dashboards, briefs, and source filters.
- Added `/public/saved-views/schema`, `/public/saved-views/validate`, `/public/saved-views/migrations`, and `/public/saved-views/diagnostics`.
- Added structural validation without server persistence, including schema migration, sensitive-field rejection, manifest-size limits, invalid-country rejection, unsupported-view rejection, and state-key filtering.
- Added legacy migration from `sc-saved-view/0.9` to `sc-saved-view/1.0`.
- Added individual and collection JSON import/export with backend validation before local storage.
- Added the saved-view methodology record to the public Source and Methodology Studio.
- Added `[sc_saved_research_views height="1000"]` for a focused WordPress embed.
- Updated backend, WordPress plugin, release metadata, documentation, and automated tests to v1.23.0.
- Preserved Platform Core as optional and added no accounts, paid database, Redis service, hosted profile storage, or additional Render service.

## 1.22.0 — Source and Methodology Studio

- Added a first-class standalone `/app/?view=sources` Source and Methodology Studio.
- Added a searchable public source registry with domain, state, feature, and text filters.
- Added complete public records for World Bank Open Data, NASA GIBS, USGS Earthquakes, NASA EONET, ReliefWeb, NASA POWER, OpenStreetMap, and optional Platform Core provenance integration.
- Added source detail, status, and coverage endpoints with publisher, connector, update frequency, license context, geographic and temporal coverage, feature usage, official URLs, and known limitations.
- Added a public methodology registry covering latest-value selection, missing values, zero handling, delivery states, trends, reporting-year differences, indicator compatibility, country normalization, country-event matching, event deduplication, Earth date validation, imagery interpretation, comparison calculations, briefing, exports, caching, and optional-source failures.
- Added public-safe source states: Live, Cached, Stale, Temporarily unavailable, Experimental, and Disabled.
- Added `/public/source-methodology/diagnostics` with source-reference validation and no-secret checks.
- Added JSON and UTF-8 CSV source-registry exports with spreadsheet-formula safeguards and no-store/nosniff response headers.
- Added shareable source, domain, state, feature, and search URL state.
- Added source links from thematic and briefing panels into the Source and Methodology Studio.
- Added `[sc_source_methodology_studio height="1100"]` with optional source, domain, state, feature, and query attributes.
- Updated backend, WordPress plugin, release metadata, documentation, and automated tests to v1.22.0.
- Preserved Platform Core as optional and added no paid database, Redis service, proprietary map service, or additional Render service.

## 1.21.0 — Thematic Intelligence Dashboards

- Added four first-class public-beta dashboards: Climate and Environment, Human Development, Human Security, and Infrastructure and Connectivity.
- Added the standalone `/app/?view=thematic` workspace with dashboard, country, event-window, layer, trend, share, print, briefing, and export controls.
- Added map, indicator-card, trend-chart, accessible trend-table, public-event, source, methodology, missing-data, and interpretation-limit panels.
- Added `/public/thematic-dashboards` and dashboard-specific data, indicator, trend, event, brief, export, and diagnostics endpoints.
- Added JSON, UTF-8 CSV, and print-ready HTML dashboard exports with source identity, units, reporting years, data states, missing-data records, and responsible-use boundaries.
- Added request cancellation and stale-response protection for country and dashboard switching.
- Kept optional event-source failures local so available indicators, trends, Earth layers, briefs, and exports remain usable.
- Connected thematic briefing handoffs to the v1.20.0 canonical investigation-manifest system.
- Added `[sc_thematic_intelligence dashboard="climate-environment" country="KEN" height="1150"]`.
- Preserved explicit source, date, unit, modeled/observed state, and no-composite-score boundaries.
- Preserved Platform Core as optional and added no paid database, Redis service, proprietary map service, or additional Render service.


## 1.20.1 — Backend Compatibility Check and Admin Cache Reliability Patch

- Isolated pytest caches, Python bytecode, country last-known-good data, and optional Platform Core queue files outside the release tree during validation.

- Replaced the single ten-minute build-info cache with version-scoped cache keys.
- Cache matching versions for six hours, mismatches for 45 seconds, and verification errors for 30 seconds.
- Added plugin-version and cache-busting query parameters to build-info requests.
- Added explicit match, mismatch, unavailable, invalid-response, and not-configured states.
- Added a Refresh backend version action to the settings page and admin notices.
- Added backend URL, last verification time, backend version, and HTTP status to the settings page.
- Clear legacy and version-scoped build-info transients on activation, plugin upgrade, and settings save.
- Prevent an old cached mismatch from being presented as current deployment state.
- Updated backend and WordPress plugin release metadata to v1.20.1.
- Added automated compatibility-cache contract tests.

## 1.20.0 — Public Briefing and Export Studio

- Added a first-class standalone Public Briefing and Export Studio for country, comparison, event, Earth-observation, and thematic investigations.
- Added a canonical `sc-public-briefing/1.0` investigation manifest with deterministic brief IDs, scope, state, geography, selected dates, evidence groups, source records, data states, missing-data records, methodology, interpretation limits, and provenance state.
- Added `/public/briefing-studio`, `/public/briefing-studio/brief`, `/public/briefing-studio/export`, and `/public/briefing-studio/diagnostics`.
- Added source-aware country, country-comparison, event-situation, Earth-observation, and thematic briefs without requiring Platform Core.
- Added JSON evidence-manifest, CSV evidence-table, and print-ready HTML exports.
- Added browser-rendered PNG capture with visible attribution; deferred PDF until the HTML export contract is stable.
- Added export filenames, content-disposition headers, `no-store`, and `nosniff` response protections.
- Added UTF-8 CSV output and spreadsheet-formula safeguards.
- Added local event-source failure isolation so optional feed outages do not block briefing generation.
- Added request cancellation, stale-response rejection, URL-restorable briefing state, source and data-gap summaries, and type-specific controls.
- Added print styling with visible source URLs and a responsible-use boundary.
- Added `[sc_public_briefing_studio type="country" country="KEN" height="1150"]`.
- Updated backend, WordPress plugin, release metadata, documentation, and automated tests to v1.20.0.
- Preserved Platform Core as optional and added no paid database, Redis service, proprietary map service, or additional Render service.

## 1.19.1 — Comparison Reliability Patch

- Added strict country-pair validation and explicit duplicate-country handling.
- Added distinct aligned, reporting-year, source, unit, definition, state, partial, and unavailable compatibility states.
- Stopped mathematical difference calculations when reporting years do not match.
- Added normalized unit and source-family compatibility checks while retaining live-versus-reference World Bank attribution.
- Reused one country-pair retrieval for indicators, trends, and embedded briefs to reduce duplicate connector requests and inconsistent snapshots.
- Isolated optional event failures so indicator comparison, trends, briefing, and exports remain available.
- Added chartability rules, shared-year checks, explicit gap years, aligned series, and accessible year-by-year trend tables.
- Added public-safe `/public/compare/diagnostics` compatibility diagnostics.
- Added source-complete JSON, CSV, and HTML exports with warning fields, data states, source IDs, source URLs, safe response headers, and indicator filtering.
- Added share-state restoration for active view, indicator filter, and trend selection.
- Added mobile card rendering for comparison tables and corrected print rendering for comparison briefs.
- Added local pair-validation and panel-level empty/error states.
- Extended `[sc_comparative_intelligence]` with `view` and `indicator` attributes and stricter shortcode input validation.
- Updated backend, WordPress plugin, release metadata, documentation, and tests to v1.19.1.
- Preserved Platform Core as optional and added no paid infrastructure dependency.

## 1.19.0 — Comparative Intelligence and Briefing Studio

- Replaced the standalone app comparison placeholder with a complete two-country Comparative Intelligence workspace.
- Added table, synchronized trend chart, map, brief, and export views.
- Added normalized global country selectors, swap, reset, share, print, and indicator filtering controls.
- Added explicit compatibility rules for indicator IDs, units, definitions, reporting years, and data states.
- Added mathematical differences only for compatible records; mismatched years remain visible and labeled.
- Preserved explicit missing-value language and prohibited unexplained composite scores and rankings.
- Added `/public/compare`, `/public/compare/indicators`, `/public/compare/trends`, `/public/compare/events`, `/public/compare/brief`, and `/public/compare/export`.
- Added JSON, CSV, and print-ready HTML comparison exports.
- Added source-aware comparison briefs with country summaries, indicators, trends, events, caveats, sources, and timestamps.
- Added request cancellation, stale-response rejection, duplicate-country prevention, and local retry states.
- Parallelized independent World Bank indicator requests and added short-lived negative caching for unavailable optional event feeds to prevent repeated timeout cascades.
- Added `[sc_comparative_intelligence country="KEN" compare="GHA" height="1100"]`.
- Updated backend, WordPress plugin, release metadata, documentation, and tests to v1.19.0.
- Preserved Platform Core as optional and added no paid service dependency.

## 1.18.3 — Global Country Reliability, Data Coverage, and Release Integrity

- Fixed the release validator so a normal repository-root `.git` directory is allowed while nested repositories and generated artifacts remain forbidden.

- Added a canonical release-version module and aligned backend, plugin, launch status, release status, and documentation on v1.18.3.
- Added `/public/build-info` with backend version, API schema version, expected plugin version, Git commit, and build timestamp.
- Added a WordPress administrator warning when the plugin and backend releases do not match.
- Added public display-name normalization while retaining unmodified source names and aliases for search.
- Added ISO2, ISO3, display-name, source-name, and alternate-name search coverage.
- Added process-memory plus atomic JSON last-known-good caching for country catalog and World Bank indicator series.
- Added explicit live, partial-live, cached, stale, reference-snapshot, and unavailable states.
- Added source IDs, source URLs, retrieval timestamps, cache state, and stale flags to indicator payloads.
- Added `/public/countries/diagnostics` and `/public/country/{ISO3}/diagnostics`.
- Added retained country-match method, confidence, and evidence fields to public event records.
- Added source-country, title-name, and limited coordinate-bounding-box matching.
- Added abortable country requests, stale-response rejection, country-search debouncing, request timeouts, local retries, and invalid-code fallback in the standalone app.
- Prevented duplicate country map markers and stale trend/chart content during rapid country switching.
- Added source links to country indicator cards.
- Preserved Platform Core as an optional integration and added no paid infrastructure dependency.
- Expanded the automated suite to 199 passing tests.

## 1.18.2 — WordPress Skeleton Loader Completion Patch

- Fixed Country Intelligence Profile skeleton bars remaining after content rendered.
- Fixed Cross-Domain Comparison skeleton bars remaining after fallback or completed requests.
- Added shared loading-state helpers with `aria-busy` management.
- Added `finally` cleanup for initial loads and country-profile reloads.
- Removed completed loading-shell elements from the DOM.
- Added CSS safeguards so hidden or completed loaders cannot remain visible.
- Reworded missing comparison values as “No validated public value is currently available.”
- Preserved explicit missing-data rows instead of disguising unavailable connector values.

## 1.18.1 — Public Feed Notice Removal

- Removed the persistent global “Some public feeds are unavailable” banner.
- Removed the fixed overlay that could not be dismissed reliably.
- Replaced global warnings with quiet local panel states and brief toasts.
- Preserved retries and fallback behavior without interrupting the interface.
- Optional feed failures no longer create a site-wide warning.

## 1.18.0 — Global Country Intelligence

- Expanded country intelligence from five hard-coded countries to dynamic global World Bank country coverage.
- Added searchable country catalog, ISO code search, and regional filtering.
- Added country metadata for region, income level, capital, and geographic center.
- Added a redesigned global country explorer in the standalone application.
- Added country fly-to map, live indicator cards, multi-year trends, and country-linked public events.
- Added shareable country URL state and direct transitions to Earth Observation and Live Event Intelligence.
- Added public country catalog, search, region, and overview endpoints.
- Added a WordPress shortcode for Global Country Intelligence.
- Preserved reporting-year visibility, missing-data transparency, and non-ranking boundaries.

## 1.17.0 — Unified Live Event Intelligence

- Added a dedicated unified live-event explorer to the standalone application.
- Added live USGS earthquake, NASA EONET natural-event, and ReliefWeb humanitarian-report connectors.
- Added normalized event categories, stable event IDs, source identity, timestamps, location, severity, record type, and data state.
- Added category, source, date-range, and country filters.
- Added synchronized event map and event list.
- Added event detail drawer with source links and interpretation boundaries.
- Added event timeline playback.
- Added category, source, and country summaries.
- Added public event, category, source, timeline, summary, and detail endpoints.
- Added a WordPress shortcode for the event explorer.
- Preserved explicit fallback labeling and avoided presenting public records as operational alerts.

## 1.16.1 — Earth Observation Reliability and Interaction Polish

- Added explicit broken-tile and imagery-unavailable states.
- Added layer and date validation before comparison loading.
- Added retry and reset controls.
- Added safer timeline playback with pause-on-change behavior.
- Restored swipe position in shareable URL state.
- Improved mobile sticky controls and responsive action layout.
- Improved keyboard focus, slider accessibility, and ARIA state.
- Improved print and fullscreen presentation.
- Added Earth Observation diagnostics endpoint.
- Preserved browser-dependent PNG fallback to print and JSON manifest.

## 1.16.0 — Earth Observation Studio

- Added a dedicated Earth Observation Studio view to the standalone application.
- Added before-and-after satellite imagery comparison with a draggable swipe divider.
- Added independent before and after dates, layer opacity, synchronized maps, fullscreen-compatible presentation, and shareable URL state.
- Added timeline playback across recent imagery dates.
- Added true color, land-surface temperature, fire signals, vegetation, precipitation, snow cover, nighttime lights, and atmospheric aerosol layers.
- Added layer metadata for source, attribution, temporal resolution, spatial resolution, observation type, availability, description, and known limits.
- Added browser PNG snapshot attempt, print view, and downloadable JSON view manifest.
- Added Earth Observation public API endpoints and a WordPress Earth Studio shortcode.
- Preserved source-aware interpretation warnings and explicit imagery limitations.

## 1.15.2 — Public Launch Hardening and Experience Cleanup

- Added a polished public-beta loading experience for Render cold starts.
- Added retry logic for satellite layers, event feeds, country summaries, and live indicators.
- Added launch progress, partial-data notices, retry actions, and intentional empty states.
- Added responsive iframe height messaging between the standalone app and WordPress.
- Added a full-app launch action and improved mobile embedding behavior.
- Reduced public-facing technical language and strengthened launch copy.
- Added public launch-status diagnostics.
- Added resilient partial-data behavior so one unavailable source does not block the workspace.
- Preserved Platform Core as an optional audit layer rather than a public-app dependency.
- Added launch-ready WordPress loading treatment and mobile full-width presentation.

## 1.15.1 — Platform Core Integration and Evidence Lineage

- Added a backend-only Platform Core v2.5.0 client.
- Added source snapshot creation for live World Bank responses.
- Added provenance activities and used/generated provenance links.
- Added stable evidence records for validated country indicators.
- Added deterministic IDs for idempotent retries and conflict-safe replay.
- Added a JSONL retry queue for temporary Platform Core outages.
- Added public-safe Platform Core integration status.
- Added country evidence-lineage endpoint.
- Added an accessible evidence and provenance drawer to the standalone app.
- Kept Platform Core write keys out of WordPress, JavaScript, public diagnostics, and exports.
- Preserved explicit live/reference states and non-imputation boundaries.

## 1.15.0 — Live Country Intelligence

- Added live World Bank country-indicator connectors.
- Added country profile, indicator, trend, and briefing endpoints.
- Added current values, reporting years, units, source identity, and explicit live/reference states.
- Added multi-year country trend visualizations in the standalone app.
- Added a finished country intelligence workspace with key metrics and evidence notes.
- Added support for Kenya, Ghana, the United States, India, and Brazil.
- Preserved missing-data, differing-reporting-period, and non-ranking boundaries.
- Retained labeled reference snapshots when upstream public data is temporarily unavailable.

## 1.14.1 — Visual Foundation and Application Polish

- Introduced an immersive dark visual system for the standalone public application.
- Added cinematic map framing, orbital visual treatment, glass panels, richer depth, and controlled accent lighting.
- Added custom animated public-event markers and polished Leaflet controls.
- Added skeleton loading states, route transitions, metric reveal motion, and refined hover behavior.
- Improved map captions, source legends, responsive controls, and mobile presentation.
- Added shareable country and application-view query state.
- Added reduced-motion handling for accessibility.
- Preserved all source, missing-data, and responsible-use boundaries.

## 1.14.0 — Standalone Public Intelligence App and Visual System

- Added a dedicated map-first public application at `/app/`.
- Added responsive top navigation, side navigation, map canvas, layer controls, legends, fullscreen mode, country selection, event stream, source view, and comparison view.
- Added satellite imagery switching for true color, surface heat, fire signals, and vegetation.
- Added live USGS and NASA EONET event rendering.
- Added a WordPress iframe embed shortcode: `[sc_site_intelligence_app]`.
- Removed backend diagnostics from the primary visual hierarchy.
- Preserved explicit missing-data, provenance, and responsible-use boundaries.

## 1.12.6 — Public Interface Redesign and Renderer Simplification

- Replaces generic readiness-card output with dedicated public templates for country profiles, dashboards, comparisons, and directories.
- Adds a compact country selector and responsive evidence-domain cards.
- Converts the dashboard directory to curated navigation rather than connector diagnostics.
- Removes technical navigation duplication inside embedded public modules.
- Adds responsive comparison tables and source chips.
- Keeps unavailable values explicit and never fabricates or silently imputes data.

# v1.12.4 — Dashboard Studio Route and Fallback Hotfix

- Fixed Public Intelligence Dashboard, Country Intelligence Profile, and Cross-Domain Comparison delivery.
- Added schema-specific frontend rendering for dashboard cards, country domains, and comparison dimensions.
- Added deterministic WordPress fallbacks when the Render proxy is unavailable.
- Added safe default country codes and consistent dashboard data routing.


## 1.12.3 — Feed Reliability and Render Cold-Start Hotfix

- Increased WordPress-to-Render request timeout from 12 seconds to 45 seconds.
- Added five-minute shared caching for successful public GET responses.
- Added six-hour stale-response fallback when Render is waking, unavailable, or returns a temporary gateway error.
- Added delivery metadata distinguishing origin, fresh-cache, and stale-cache responses.
- Added a plugin-specific user agent and limited redirect handling for origin requests.
- Preserved the v1.12.2 JavaScript and navigation-route fixes.

## 1.12.3 — WordPress Feed Loading Hotfix

- Fixed a JavaScript `ReferenceError` that stopped all connector-backed public panels before their REST requests were sent.
- Corrected the Dashboard Studio navigation panel to use the registered WordPress REST route.
- Bumped the WordPress plugin asset version so cached v1.12.1 JavaScript is invalidated after upgrade.

# v1.12.1 — Dashboard Reliability, Accessibility, and Mobile Polish

- Added launch-ready public navigation and dashboard experience contracts.
- Added loading, empty, stale, last-known-good, and unavailable states.
- Added responsive, keyboard, screen-reader, share-state, and accessible-table polish.
- Added public launch manifest, readiness, and navigation endpoints.
- Preserved all v1.12.0 dashboard studio and domain intelligence capabilities.

# Changelog

## v1.12.1 — Cross-Domain Intelligence and Public Dashboard Studio

- Added a configuration-driven public dashboard studio spanning planetary boundaries, sustainable development, human development, disasters, conflict, displacement, and international law.
- Added four initial flagship dashboard definitions, country intelligence profiles, and cross-country comparison contracts.
- Added source, data, brief, export, manifest, and accessible-table contracts.
- Added WordPress shortcodes and public REST proxy routes for dashboard directories, dashboard views, country profiles, comparisons, sources, and exports.
- Preserved existing topic-dashboard routes under their original URLs and placed the new studio under `/public/dashboard-studio`.
- Added share-state parameters without collecting personal data and retained source-specific freshness, units, methodology, uncertainty, and legal-status labels.

## v1.11.0 — Conflict, Displacement and Human Security

- Added ACLED, UCDP, UNHCR, IOM DTM, ReliefWeb, and HDX source registrations.
- Added conflict-event, civilian-protection, displacement-flow, infrastructure-security, humanitarian-access, and modeled-risk monitor contracts.
- Added normalized `sc-conflict-displacement-human-security/1.0` records with explicit observed, reported, estimated, and modeled labels.
- Added public human-security overview, source, event, displacement, forecast, methodology, monitor, and export endpoints.
- Added WordPress shortcodes and public REST proxy routes for conflict, displacement, and human-security dashboards.
- Added responsible-data protections for sensitive geography, civilian status, fatality estimates, displacement statistics, and forecast interpretation.

## v1.9.0 — Human Development and Social Conditions

- Added source-aware registries for poverty, inequality, health, education, decent work, food security, and water and sanitation.
- Added UN SDG, World Bank PIP, WHO, UNESCO UIS, ILOSTAT, FAOSTAT, and UN-Water source contracts.
- Added country-profile, domain-detail, disaggregation, methodology, and export endpoints.
- Added WordPress shortcodes for the Human Development and Social Conditions observatory.
- Preserved reference periods, modeled-estimate labels, methodological breaks, and disaggregation dimensions.

## v1.8.0 — Live Disaster, Displacement, and Humanitarian Intelligence
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

## v1.6.1 — Connector Reliability, Freshness and Schema Validation

- Added retries with bounded exponential backoff.
- Added circuit breakers and rate-limit-aware status metadata.
- Added stale-while-revalidate and last-known-good connector states.
- Added source-specific response checks and normalized observation validation.
- Added freshness thresholds, cache diagnostics, reliability endpoints, WordPress routes, and shortcodes.
- Updated backend and WordPress versions to 1.12.1.

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
