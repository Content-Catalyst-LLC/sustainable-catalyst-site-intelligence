# Sustainable Catalyst Site Intelligence

**Current release:** v2.22.0 — Institutional Workspaces, Collaboration, and Review

## v2.22.0 — Institutional Workspaces, Collaboration, and Review

This release adds optional shared institutional workspaces while preserving the public, account-free Site Intelligence experience. It introduces explicit analyst, reviewer, publisher, and administrator roles; assignments; comments and review notes; evidence approval; shared source collections; activity receipts; preview-first retention; institutional branding; and exportable workspace archives. It does not provision accounts, replace an identity provider, expose private collaboration records, or publish evidence automatically.

- Public workspace: `/app/?view=workspaces`
- Public directory: `/public/institutional-workspaces`
- Public diagnostics: `/public/institutional-workspaces/diagnostics`
- Admin control center: `/admin/institutional-workspaces/control-center`
- Public shortcode: `[sc_public_institutional_workspaces]`
- Admin shortcode: `[sc_institutional_workspaces_control_center]`

## v2.21.0 — Scheduled Monitoring, Digests, and Public Intelligence Feeds

This release turns browser-local alert concepts into a governed, file-backed monitoring and delivery layer. It adds reusable monitor definitions, explicit due-job execution, deduplicated alert receipts, human-reviewed daily and weekly digests, public JSON/RSS/Atom feeds, quiet periods, delivery logs, and optional email/webhook adapter boundaries. No always-on scheduler, emergency authority, subscriber tracking, or automatic publication is claimed.

- Public workspace: `/app/?view=monitoring`
- Public summary: `/public/scheduled-monitoring`
- Public digests: `/public/intelligence-digests`
- Public feeds: `/public/intelligence-feeds`
- Admin control center: `/admin/scheduled-monitoring/control-center`
- Due-job runner: `/admin/scheduled-monitoring/run-due?dry_run=true`


## v2.20.0 — Intelligence Publishing and Story Map Studio

- Human-reviewed publication projects with narrative, map, timeline, chart, evidence, source, methodology, image, and callout blocks.
- Explicit draft, review, approval, publication, and archive lifecycle states.
- Immutable publication versions with SHA-256 integrity receipts.
- Public and unlisted modes, version history, story-map views, and JSON/CSV/Markdown/print-HTML exports.
- Read-only WordPress handoffs and public application workspace at `/app/?view=publishing`.
- No automatic publication, fabricated sources, hidden conflicts, or causal inference from narrative sequence or map proximity.

## v2.19.0 — Cross-Domain Knowledge Graph and Relationship Explorer

- Typed countries, regions, organizations, sources, indicators, events, documents, models, claims, datasets, publications, methodologies, workspaces, places, programs, and policies.
- Versioned entity and relationship records with SHA-256 integrity receipts.
- Alias and external-identifier registration with ambiguity-preserving resolution.
- Human-reviewed reconciliation previews with no automatic entity merging.
- Evidence-backed relationships with confidence labels, temporal validity, and preserved source/target direction.
- Bounded graph traversal, entity neighborhoods, relationship filtering, and shortest-path exploration.
- Public-safe diagnostics for orphans, dangling edges, unsupported edges, and alias collisions.
- Read-only JSON/CSV graph exports and Platform Core handoff packets.
- Public workspace: `/app/?view=graph`.
- Public endpoints: `/public/knowledge-graph`, `/public/knowledge-graph/entities`, `/public/knowledge-graph/relationships`, `/public/knowledge-graph/traverse`, `/public/knowledge-graph/path`, and `/public/knowledge-graph/export`.
- WordPress shortcodes: `[sc_public_relationship_explorer]` and `[sc_knowledge_graph_control_center]`.
- Graph connectivity never establishes causation, importance, risk, or operational priority.

## v2.18.0 — Evidence Synthesis, Claims, and Contradiction Review

- Structured factual, interpretive, causal, projection, and normative claim records.
- Typed supporting, qualifying, conflicting, and contextual evidence relationships.
- Explicit source, methodology, authority, excerpt, locator, limitation, and integrity metadata.
- Contradiction review that preserves disagreement and requires human resolution.
- Measurement, method, source, comparability, causal, forecast, and coverage uncertainty records.
- Human approval, rejection, revision, unresolved, and supersession workflows.
- Deterministic grounded synthesis that never invents sources or citations.
- Citation-ready JSON, CSV, and Markdown evidence packets.
- Read-only Knowledge Library and Research Librarian handoffs.
- Public-safe claim and synthesis views plus administrator control-center endpoints.
- Public workspace: `/app/?view=evidence`.

## v2.17.0 — Model Registry, Forecast Evaluation, and Early-Warning Indicators

Site Intelligence v2.17.0 adds an auditable governance layer for models, forecasts, evaluation evidence, and early-warning indicators. It registers versioned model cards; preserves intended use, limitations, provenance, uncertainty, training and evaluation periods, expiry, and prohibited uses; ingests attributable forecasts; evaluates overlapping observed periods; and keeps calibration, drift, and threshold evidence reviewable without granting autonomous decision authority.

The engine supports MAE, RMSE, bias, MAPE, sMAPE, prediction-interval empirical coverage, calibration gaps, mean interval width, recent-versus-baseline drift review, model expiry diagnostics, and threshold or percent-change indicators. Forecasts remain distinct from user-defined scenarios, and threshold crossings remain review signals rather than evidence of cause or emergency instructions.

Public workspace: `/app/?view=models`

Public endpoints: `/public/model-governance`, `/public/model-governance/methodology`, `/public/models`, `/public/forecasts`, `/public/forecast-evaluations`, `/public/early-warning`, and `/public/model-governance/export`

Private control center: `/admin/model-governance/control-center`

Command-line utility: `python scripts/model_governance_v2170.py summary`

WordPress shortcodes: `[sc_public_model_forecasts]` and `[sc_model_forecast_control_center]`

The release prohibits individual targeting, surveillance, emergency dispatch, autonomous consequential decisions, hidden model substitution, silent retraining, guaranteed outcomes, and unsupported causal claims.

## v2.16.0 — Statistical Harmonization and Comparable-Series Engine

Site Intelligence v2.16.0 adds an explicit, auditable statistical transformation layer for public and administrative series. It registers raw source series with units, currencies, price bases, reporting frequencies, geographic definitions, observation periods, missing-data classes, and source methodology; applies only requested transformations; and preserves digest-linked lineage from the original values to every reviewed output.

The engine supports dimensional unit conversion, per-capita normalization with supplied denominators, monthly and quarterly period alignment with declared aggregation, supplied-rate currency conversion, supplied-deflator constant-price adjustment, index rebasing, comparable-series diagnostics, raw-versus-transformed views, CSV/JSON exports, and read-only Workbench handoff packets. It does not silently impute values, select exchange rates, normalize geography, manufacture equivalence, create composite scores, or rank countries.

Public workspace: `/app/?view=harmonization`

Public endpoints: `/public/harmonization`, `/public/harmonization/standards`, `/public/harmonization/methodology`, `/public/harmonization/series`, `/public/harmonization/compare`, and `/public/harmonization/export`

Private control center: `/admin/harmonization/control-center`

Command-line utility: `python scripts/statistical_harmonization_v2160.py summary`

WordPress shortcodes: `[sc_public_comparable_series]` and `[sc_statistical_harmonization_control_center]`

## v2.15.0 — Geospatial Analysis and Spatial Evidence Studio

Site Intelligence v2.15.0 turns the existing map and public-data layers into an inspectable geospatial analysis system. It adds validated WGS84 areas of interest, versioned spatial datasets, exact point-in-polygon tests, segment-aware geometry intersections, great-circle point proximity, explicit approximation labels for complex geometries, geographic aggregation, temporal layer comparison, and reproducible spatial evidence exports.

Spatial records preserve source identity, geometry type, coordinate-reference-system declarations, observation periods, method notes, payload digests, and interpretation limits. The studio does not silently reproject coordinates, invent missing geographic values, rank places, track individuals, or support military targeting. Raw private datasets and administrative analysis history remain outside public endpoints.

Public workspace: `/app/?view=spatial`

Public endpoints: `/public/spatial`, `/public/spatial/layers`, `/public/spatial/methodology`, `/public/spatial/areas`, `/public/spatial/datasets`, and `/public/spatial/evidence`

Private control center: `/admin/spatial/control-center`

Command-line utility: `python scripts/spatial_evidence_v2150.py summary`

WordPress shortcodes: `[sc_public_spatial_evidence]` and `[sc_spatial_evidence_control_center]`

## v2.14.0 — Historical Archive and Temporal Change Intelligence

Site Intelligence v2.14.0 adds a file-backed historical evidence layer behind the managed connector system. Successful live ingestions can create sanitized, canonicalized, SHA-256-verified dataset snapshots. Identical payloads are deduplicated, changed records create temporal change receipts, and corrections to the same source period are distinguished as source revisions when the available metadata supports that interpretation.

The release adds historical coverage diagnostics, scalar time-series extraction without imputation, snapshot comparison, material-change labels, retention previews and controlled application, portable history bundles, and verified restoration previews. Public endpoints expose metadata and derived series only; archived payload bodies, storage paths, credentials, and live restore actions remain private. The zero-cost file-backed mode remains available, but persistent hosting requires a durable disk path.

Public endpoints: `/public/history`, `/public/history/datasets`, `/public/history/changes`, `/public/history/revisions`, and `/public/history/datasets/{dataset_id}/series`

Private control center: `/admin/history/control-center`

Command-line utility: `python scripts/historical_archive_v2140.py datasets`

WordPress shortcodes: `[sc_public_temporal_intelligence]` and `[sc_historical_archive_control_center]`

## v2.13.0 — Connector Operations and Data Ingestion Control Center

Site Intelligence v2.13.0 adds a managed, source-aware operations layer across 14 existing public-data connectors. It introduces a unified connector and dataset registry, manual/scheduled/conditional refresh jobs, due-job evaluation, execution receipts, freshness diagnostics, quota windows, bounded retries, circuit breakers, schema validation, transformation declarations, and redacted quarantine review.

The zero-cost default remains file-backed and can be redirected to ephemeral or durable storage through environment variables. Credentials, request headers, and complete upstream payloads are never returned by the control center or persisted in execution history. Scheduled work remains explicit: a protected endpoint and command-line runner can execute due jobs, but the application does not claim a background scheduler is active unless one is configured.

Public status endpoint: `/public/connectors/operations`

Private control center: `/admin/connectors/control-center`

Due-job runner: `python scripts/run_connector_jobs_v2130.py --dry-run`

WordPress shortcodes: `[sc_public_connector_operations]` and `[sc_connector_operations_control_center]`


## v2.12.1 — Production Offline, Mobile, and Embed Reliability Patch

Site Intelligence v2.12.1 hardens the v2.12.0 delivery layer for production. Service-worker installation now survives individual optional asset failures, activates release updates without reusing a cached worker script, removes prior release caches, and applies real entry and age limits to public-data fallbacks. The offline page and Experience workspace can repair browser-local cache state. Application HTML, the manifest, service worker, backend responses, and WordPress plugin expose aligned release metadata.

WordPress embeds now share one responsive controller that verifies both the message origin and the iframe source window, adjusts desktop and mobile heights up to a safe maximum, reports delayed loads, and preserves a new-tab fallback. No account, telemetry service, paid cache, paid API, or server-side user profile is added.

Public route: `/app/?view=experience`

Reliability endpoint: `/public/offline-experience/reliability`

WordPress shortcode: `[sc_site_intelligence_app height="1000"]`

## v2.12.0 — Offline, Mobile, Accessibility, and Performance

Site Intelligence v2.12.0 adds an installable web application manifest, browser service worker, offline fallback page, bounded browser-local cache policy, low-bandwidth controls, mobile-safe delivery, accessibility contracts, first-party performance budgets, and a dedicated `/app/?view=experience` workspace. Cached records retain stale-state warnings, external maps and imagery may remain network-dependent, and automated diagnostics do not claim formal accessibility certification.

Public route: `/app/?view=experience`

WordPress shortcode: `[sc_offline_mobile_accessibility_performance height="1500"]`

## v2.11.0 — Public Data API, Embeds, and Institutional Integration

Site Intelligence v2.11.0 adds a versioned read-only public API at `/api/public/v1`, workspace manifests, sanitized record collections for the primary data observatories, portable iframe manifests, a public institutional presentation profile, a dedicated `/app/?view=integration` workspace, and generic WordPress embeds. Provider credentials, private ingestion configuration, and hosted user profiles remain excluded.

Public shortcodes: `[sc_public_data_api_integration height="1500"]` and `[sc_site_intelligence_embed view="economics" height="900"]`.

## v2.10.0 — Research Paths, Saved Investigations, and Briefing Workflows

Site Intelligence v2.10.0 adds `/app/?view=research` for browser-local investigations, evidence sets, notes, checkpoints, saved public views, deterministic briefing packets, JSON import/export, and explicit handoffs to Knowledge Library, Research Librarian, Workbench, and Decision Studio. The backend validates and packages records statelessly; it does not persist private research history or generate factual conclusions.

## v2.9.0 — Comparative Intelligence and Scenario Studio

Site Intelligence v2.9.0 adds `/app/?view=scenarios` for multi-geography indicator baskets, compatibility review, catalog-based regional peers, transparent arithmetic scenarios, correlation review, and reproducible comparison packets. It does not silently normalize incompatible values, rank countries, forecast outcomes, infer causation, or require paid data services.

WordPress embed: `[sc_comparative_intelligence_scenario_studio height="1550"]`.

## v2.8.0 — Alerts, Monitoring, and Live Intelligence Streams

Site Intelligence v2.8.0 adds a reconnectable public monitoring workspace at `/app/?view=alerts`. It combines sanitized public records from global conditions, humanitarian evidence, economics, international law, scientific data, and trade/resource systems. Alert rules and watched places remain browser-local; the backend performs stateless matching and does not create user profiles or monitoring histories.

Key capabilities:

- reconnecting server-sent stream snapshots with JSON fallback;
- browser-local alert rules and watched country filters;
- source availability and public-record recency monitoring;
- deterministic digests and CSV exports;
- explicit no-fabrication, no-emergency-service, no-risk-score, and no-server-tracking boundaries; and
- WordPress embed `[sc_alerts_monitoring_live_intelligence height="1500"]`.

## v2.7.0 — Unified Country and Regional Intelligence Dossiers

Site Intelligence v2.7.0 adds a cross-domain dossier workspace for countries and catalog regions. It composes public conditions, country indicators, official economics, international law, scientific records, humanitarian evidence, and trade, energy, and resource context without creating a composite score, ranking, causal conclusion, or automated judgment.

- Public route: `/app/?view=dossiers`
- WordPress shortcode: `[sc_country_regional_intelligence_dossiers height="1500"]`
- Country, regional, and two-country coverage views
- Source-aware evidence samples and domain delivery states
- No paid provider requirement and no fabricated fallback records

## v2.6.0 — Trade, Energy, and Resource Security Observatory

Site Intelligence v2.6.0 adds a public workspace for official trade flows, energy systems, agriculture, food, water, materials, supply-chain relationships, and climate-transition context. It preserves source units, periods, classifications, counterpart geographies, frequencies, licenses, and methodology rather than creating a proprietary resource-security score.

- Public route: `/app/?view=resources`
- WordPress shortcode: `[sc_trade_energy_resource_security_observatory height="1450"]`
- Free official and public data through Platform Core
- No simulated real-time markets, proprietary risk score, sanctions determination, or fabricated fallback values

## v2.5.0 — Humanitarian, Conflict, and Displacement Observatory

Site Intelligence v2.5.0 adds a source-aware public workspace for humanitarian reporting, conflict-related public records, displacement evidence, civilian-protection context, humanitarian access, and hazard exposure. It combines the existing live-event layer with scoped Platform Core records while preserving source, date, geography, uncertainty, legal authority, and explicit responsible-data boundaries.

- Public route: `/app/?view=humanitarian`
- WordPress shortcode: `[sc_humanitarian_conflict_displacement_observatory height="1450"]`
- No fabricated crisis records or paid provider requirement
- No legal-responsibility inference, military targeting, individual risk scoring, refugee-status determination, eligibility decision, or emergency warning

## v2.4.0 — Scientific and Earth Systems Observatory

Site Intelligence v2.4.0 adds a dedicated public workspace for scientific records and the Core v2.8.0 data fabric. It exposes public scientific metadata, assets, map layers, STAC items, and time-series records while preserving mission, instrument, observation time, quality, license, attribution, file formats, and explicit interpretation limits.

- Public workspace: `/app/?view=science`
- WordPress shortcode: `[sc_scientific_earth_systems_observatory height="1400"]`
- No paid provider dependency and no fabricated scientific fallback records

## v2.3.0 — International Law and Global Governance Observatory

Site Intelligence v2.3.0 adds a dedicated public workspace for official international-law and global-governance records supplied through Sustainable Catalyst Core.

Public route: `/app/?view=law`

WordPress shortcode: `[sc_international_law_governance_observatory height="1350"]`

The workspace supports authority and record-type filters, official document symbols, legal and issuing bodies, procedural status, adoption and publication dates, country and subject associations, citations, official source links, a geographic profile map, timeline, country legal profile, authority matrix, CSV export, Saved View support, and Workbench and Decision Studio handoffs.

Legal authority is never flattened into a single score. Treaties, treaty actions, judgments, advisory opinions, procedural orders, Security Council resolutions, General Assembly resolutions, human-rights recommendations, ILC texts, and official reports retain distinct classifications. The workspace does not provide legal advice, compliance determinations, or automatic claims about binding effect.

The Core connection remains optional. When Core is disabled or unavailable, the workspace reports an explicit unavailable or degraded state and does not fabricate legal records.

Sustainable Catalyst Site Intelligence is an auditable public observatory for Earth observation, global country indicators, natural hazards, humanitarian reporting, comparative research, source-aware briefs, evidence lineage, and portable public verification records.

## Public application

- Standalone app: `https://sustainable-catalyst-site-intelligence.onrender.com/app/`
- Auditable Public Observatory: `/app/?view=observatory`
- Scientific and Earth Systems Observatory: `/app/?view=science`
- International Law and Global Governance Observatory: `/app/?view=law`
- Economics, Markets, and Sustainability Signals: `/app/?view=economics`
- Global Conditions and Live Map Observatory: `/app/?view=global`
- Public launch and portfolio: `/app/?view=launch`
- Earth Observation: `/app/?view=earth`
- Live Events: `/app/?view=events`
- Global Country Intelligence: `/app/?view=country&country=KEN`
- Comparative Intelligence: `/app/?view=compare&country=KEN&compare=GHA`
- Thematic Intelligence: `/app/?view=thematic&dashboard=climate-environment&country=KEN`
- Public Briefing Studio: `/app/?view=briefing&briefType=country&country=KEN`
- Source and Methodology Studio: `/app/?view=sources`
- Saved Views and Shareable Research Paths: `/app/?view=saved`
- Primary WordPress embed: `[sc_site_intelligence_app height="1000"]`
- Observatory WordPress embed: `[sc_auditable_public_observatory height="1250"]`

## v2.0.0 release focus

v2.0.0 consolidates Site Intelligence into an Auditable Public Observatory. It adds a public evidence ledger, source-method-workspace lineage graph, canonical SHA-256 integrity records, a non-persistent payload verification contract, a release ledger, downloadable audit packets, a first-class observatory workspace, and a dedicated WordPress embed.

### Public observatory route

```text
/app/?view=observatory
```

### Public observatory endpoints

- `GET /public/observatory`
- `GET /public/observatory/catalog`
- `GET /public/observatory/audit/{artifact_id}`
- `GET /public/observatory/lineage`
- `GET /public/observatory/verification`
- `POST /public/observatory/verify`
- `GET /public/observatory/release-ledger`
- `GET /public/observatory/diagnostics`
- `GET /public/observatory/export?format=json`
- `GET /public/observatory/export?format=markdown`

### Integrity boundary

A matching SHA-256 digest can detect whether a canonicalized record changed relative to an expected digest. It does not prove factual correctness, publisher identity, legal authenticity, source availability, or completeness. Submitted verification payloads are validated in memory and are not persisted.

### WordPress

The flagship public page should continue using one primary application embed:

```text
[sc_site_intelligence_app height="1000"]
```

The dedicated audit workspace uses:

```text
[sc_auditable_public_observatory height="1250"]
```

The legacy country, comparison, and geospatial shortcode implementations are retired in v2.0.0. Their names remain as migration-safe aliases that open the modern standalone workspaces instead of rendering the former preview components.

## v1.25.0 release focus

v1.25.0 presents Site Intelligence as a coherent public product and portfolio release. It adds a dedicated launch route, product-area directory, public launch profile, portfolio export, launch-material registry, responsible-use presentation, Open Graph metadata, a WordPress launch embed, and a published deprecation schedule for legacy preview shortcodes.

### Public launch route

```text
/app/?view=launch
```

### Public launch endpoints

- `GET /public/launch-profile`
- `GET /public/launch-profile/checklist`
- `GET /public/launch-profile/materials`
- `GET /public/launch-profile/diagnostics`
- `GET /public/launch-profile/portfolio?format=json`
- `GET /public/launch-profile/portfolio?format=markdown`

### WordPress

The flagship public page should use one primary application embed:

```text
[sc_site_intelligence_app height="1000"]
```

The dedicated launch and portfolio presentation uses:

```text
[sc_site_intelligence_launch height="1200"]
```

Legacy country, comparison, and map preview shortcodes remain compatible in v1.x and are scheduled for removal or redesign in v2.0.0.

## v1.24.0 release focus

v1.24.0 hardens Site Intelligence for keyboard use, reduced-motion preferences, mobile navigation, constrained networks, and responsive WordPress embedding. It adds public experience-profile diagnostics, response compression, explicit cache behavior, lazy optional PNG capture loading, first-party performance budgets, safe-area layouts, and a complete phone navigation drawer while preserving visible source and data-state context.

Public experience endpoints:

- `GET /public/experience-profile`
- `GET /public/experience-profile/checklist`
- `GET /public/experience-profile/diagnostics`

The release targets WCAG 2.2 Level AA behavior but does not claim third-party certification. Manual screen-reader, browser-zoom, real-device, and network-throttling review remains required.

## v1.23.0 release focus

v1.23.0 adds browser-local saved views and portable research paths to the standalone Site Intelligence application. Users can preserve public interface state, reopen it later, exchange a shareable URL, and import or export a validated JSON manifest without creating an account or sending the view to hosted profile storage.

### Saved Views route

```text
/app/?view=saved
```

### Portable schema

```text
sc-saved-view/1.0
```

A saved-view manifest records:

- application and schema version
- stable saved-view ID
- user-provided view name
- public route and route-specific state
- country and comparison selections
- map viewport where applicable
- imagery layer, dates, opacity, and swipe position
- event, thematic, briefing, source, and methodology filters
- created and updated timestamps

It does not store API keys, authentication data, private notes, internal diagnostics, environment variables, cookies, or briefing evidence payloads.

### Browser-local storage

```text
sc_site_intelligence_saved_views_v1
```

Saved views remain in the current browser, do not synchronize across devices, and are removed when the user clears site data. The interface handles unavailable storage, quota errors, invalid local records, duplicate IDs, duplicate names, and clear-all operations without breaking the public application.

### Public endpoints

- `/public/saved-views/schema`
- `/public/saved-views/validate`
- `/public/saved-views/migrations`
- `/public/saved-views/diagnostics`

The validation endpoint checks structure only and never persists submitted manifests.

### Import and export

- individual saved-view JSON
- portable saved-view collection JSON
- migration from `sc-saved-view/0.9`
- invalid JSON rejection
- unsupported schema and route rejection
- sensitive-field rejection
- manifest-size limits
- invalid country and state validation

### WordPress

```text
[sc_saved_research_views height="1000"]
```

The full application remains the preferred primary embed:

```text
[sc_site_intelligence_app height="1000"]
```

No account system, hosted profile database, Redis service, paid persistence layer, or additional Render service is required.

## v1.22.0 release focus

v1.22.0 adds a first-class public Source and Methodology Studio to the standalone Site Intelligence application. The studio makes provenance, coverage, connector state, source usage, known limitations, and the system's evidence-handling rules visible without exposing private infrastructure.

### Public source route

```text
/app/?view=sources
```

### Public source registry

The registry includes complete public records for:

- World Bank Open Data
- NASA EOSDIS GIBS
- USGS Earthquake Hazards Program
- NASA EONET
- ReliefWeb
- NASA POWER
- OpenStreetMap
- optional Sustainable Catalyst Platform Core provenance integration

Each source record includes publisher, authority, connector, domains, data types, update frequency, current public state, geographic and temporal coverage, license context, feature usage, official URL, and known limitations.

### Public methodology registry

The studio documents actual application behavior for:

- latest valid indicator selection
- missing-value handling
- zero versus unavailable
- delivery-state labeling
- trend construction
- reporting-year differences
- indicator compatibility
- country-name normalization
- country-event matching
- event deduplication
- Earth-observation date validation
- imagery interpretation
- comparison calculations
- deterministic brief generation
- export generation
- cache and stale-record behavior
- optional-source failure isolation

### Public endpoints

- `/public/sources`
- `/public/sources/{source_id}`
- `/public/sources/{source_id}/status`
- `/public/sources/{source_id}/coverage`
- `/public/methodology`
- `/public/methodology/{method_id}`
- `/public/source-methodology/diagnostics`
- `/public/source-methodology/export`

### Public-safe connector states

- Live
- Cached
- Stale
- Temporarily unavailable
- Experimental
- Disabled

The public studio never exposes API keys, private URLs, internal stack traces, secret environment variables, authentication state, or raw retry queues.

### Exports

- JSON source and methodology registry
- UTF-8 CSV source registry with spreadsheet-formula safeguards

### WordPress

```text
[sc_source_methodology_studio height="1100"]
```

Focused source example:

```text
[sc_source_methodology_studio source="world-bank" height="1000"]
```

The standalone app remains the primary public product, and Platform Core remains optional.

## v1.21.0 release focus

v1.21.0 adds four first-class, source-aware thematic public-beta dashboards to the standalone Site Intelligence application. Each dashboard combines a selected-country map, public indicators, historical trends, recent event context, Earth-observation layers, source records, methodology, interpretation limits, briefing handoff, and JSON/CSV/HTML exports.

### Public thematic routes

- `/app/?view=thematic&dashboard=climate-environment&country=KEN`
- `/app/?view=thematic&dashboard=human-development&country=KEN`
- `/app/?view=thematic&dashboard=human-security&country=KEN`
- `/app/?view=thematic&dashboard=infrastructure&country=KEN`

### Public endpoints

- `/public/thematic-dashboards`
- `/public/thematic-dashboard/{dashboard_id}`
- `/public/thematic-dashboard/{dashboard_id}/indicators`
- `/public/thematic-dashboard/{dashboard_id}/trends`
- `/public/thematic-dashboard/{dashboard_id}/events`
- `/public/thematic-dashboard/{dashboard_id}/brief`
- `/public/thematic-dashboard/{dashboard_id}/export`
- `/public/thematic-dashboard/{dashboard_id}/diagnostics`

### WordPress

```text
[sc_thematic_intelligence dashboard="climate-environment" country="KEN" height="1150"]
```

The dashboards do not create proprietary composite scores. Missing values and optional event failures remain local, source dates and units remain visible, trend gaps are not silently interpolated, and Platform Core remains optional.

## v1.20.1 release focus

v1.20.1 makes the WordPress-to-backend compatibility check deployment-aware. Matching versions are cached efficiently, mismatches and errors are rechecked quickly, stale legacy transients are removed during activation and upgrade, and administrators can refresh the backend version directly from WordPress settings.

### Admin reliability changes

- version-scoped build-info cache keys
- six-hour cache for successful matches
- 45-second cache for mismatches
- 30-second cache for unavailable or invalid responses
- automatic cleanup on activation, upgrade, and settings save
- explicit match, mismatch, unavailable, invalid-response, and not-configured states
- backend URL, HTTP state, returned version, and last verification time
- manual Refresh backend version action

## v1.20.0 release focus

v1.20.0 adds a unified deterministic Public Briefing and Export Studio across country, comparison, event, Earth-observation, and thematic investigations.

### Canonical investigation manifest

Every brief uses one source-aware schema containing:

- stable deterministic brief ID
- brief type and title
- investigation scope and selected state
- geography and date range
- evidence groups and normalized records
- source names, source IDs, and source URLs
- live, cached, stale, fallback, modeled, and unavailable states
- explicit missing-data and compatibility records
- methodology version
- interpretation limits and responsible-use boundary
- optional provenance state without requiring Platform Core

### Supported brief types

- country brief
- country-comparison brief
- event-situation brief
- Earth-observation brief
- thematic dashboard brief

### Public briefing route

```text
/app/?view=briefing&briefType=country&country=KEN
```

The studio provides type-specific controls, URL-restorable state, local request cancellation, evidence metrics, source lists, data-gap reporting, print mode, and downloadable exports.

### Export contract

- JSON evidence manifest
- CSV evidence table with UTF-8 and spreadsheet-formula safeguards
- print-ready HTML with visible source URLs
- browser-rendered PNG capture with attribution visible in the captured brief

PDF remains intentionally deferred until the print-ready HTML contract is stable.

### Public endpoints

- `/public/briefing-studio`
- `/public/briefing-studio/brief`
- `/public/briefing-studio/export`
- `/public/briefing-studio/diagnostics`

### WordPress

```text
[sc_public_briefing_studio type="country" country="KEN" height="1150"]
```

The standalone app remains the primary public product, and Platform Core remains optional.

## v1.19.1 release focus

v1.19.1 hardens Comparative Intelligence for mismatched years, missing values, source conflicts, unit conflicts, chart gaps, mobile use, printing, sharing, and export reliability.

### Reliability contract

- Strict ISO2/ISO3 pair validation; punctuation is not silently removed.
- Duplicate countries return an explicit validation state.
- Indicator definition, normalized unit, source family, and data state must align before records are display-comparable.
- Mathematical differences are calculated only when reporting years also match.
- Year, source, unit, definition, state, partial-coverage, and unavailable conditions have distinct compatibility states.
- Optional event-source failures remain local and cannot block indicator comparison or briefing.

### Trend and interface reliability

- Synchronized trend charts require compatible definitions, units, source families, and at least one shared reporting year.
- Missing years appear as explicit chart gaps and in an accessible year-by-year table.
- Comparison table rows become readable mobile cards instead of forcing nested horizontal scrolling.
- Share URLs retain country pair, active view, indicator filter, and trend selection.
- Print mode now reliably exposes the comparison brief.
- Invalid pairs and unavailable panels use local, actionable states.

### Export and source reliability

- CSV exports include indicator IDs, both source IDs, source URLs, reporting years, units, data states, compatibility, differences, and warnings.
- CSV output uses UTF-8 BOM, RFC-style line endings, and spreadsheet-formula safeguards.
- HTML exports include source links, methodological cautions, version, and print-visible URLs.
- JSON exports include an export manifest and schema version.
- Export responses use `no-store` and `nosniff` headers.
- Indicator-filtered brief and export generation is supported.

### New diagnostics

- `/public/compare/diagnostics`

The endpoint reports compatibility counts, calculation-eligible rows, chartable trends, and public-safe issue summaries.

### WordPress

The specialized shortcode now supports an initial view and optional indicator filter:

```text
[sc_comparative_intelligence country="KEN" compare="GHA" view="brief" indicator="SP.POP.TOTL" height="1100"]
```

## v1.19.0 release focus

v1.19.0 replaces the legacy comparison placeholder with a first-class Comparative Intelligence and Briefing Studio in the standalone application.

### Comparative workspace

- Two-country selector using the normalized global country catalog
- Swap, reset, share, and print controls
- Shareable URL state using `country` and `compare`
- Table, chart, map, brief, and export views
- Request cancellation and stale-response protection
- Local loading and failure states
- Duplicate-country prevention

### Methodological comparison contract

The comparison layer calculates a difference only when:

- indicator IDs match
- units match
- both countries have explicitly labeled values
- definitions are aligned

Reporting years remain visible. A year mismatch is labeled rather than silently normalized. Missing values remain explicit as:

> No validated public value is currently available.

The product does not create an unexplained composite score or national ranking.

### Comparative charts and map

- Grouped latest-value presentation in the table
- Synchronized multi-year trend charts
- Common-year counts
- Two-country geographic orientation map
- Accessible tabular information alongside charts
- Clear primary and comparison color keys

### Comparative briefing

The public brief includes:

1. comparison scope
2. country summaries
3. latest available indicators
4. trend series
5. recent public event counts
6. methodological caveats
7. source list
8. generated timestamp
9. responsible-use boundary

### Exports

- JSON evidence manifest
- CSV indicator table
- print-ready HTML brief

Exports preserve values, units, reporting years, compatibility states, calculated differences, source names, source URLs, application version, and methodological boundaries.

### Public endpoints

- `/public/compare`
- `/public/compare/indicators`
- `/public/compare/trends`
- `/public/compare/events`
- `/public/compare/brief`
- `/public/compare/export`
- `/public/compare/diagnostics`

### WordPress

New specialized embed:

```text
[sc_comparative_intelligence country="KEN" compare="GHA" view="table" height="1100"]
```

The primary public embed remains:

```text
[sc_site_intelligence_app height="1000"]
```

### v1.18.3 reliability foundation retained

v1.19.0 retains:

- normalized global country names and aliases
- explicit live, cached, stale, reference-snapshot, and unavailable states
- process-memory and JSON last-known-good caching
- abortable country requests
- country diagnostics
- retained country-event match method and confidence
- optional Platform Core integration
- no additional paid infrastructure

## Public diagnostics

### Build compatibility

`GET /public/build-info`

Returns:

- backend version
- API schema version
- expected WordPress plugin version
- release name
- Git commit when supplied by the host
- build timestamp
- Platform Core optional state

### Country catalog diagnostics

`GET /public/countries/diagnostics`

Returns public-safe catalog, coverage, timing, and cache information.

### Country diagnostics

`GET /public/country/{ISO3}/diagnostics`

Returns:

- metadata state
- successful indicator count
- live indicator count
- missing indicator IDs
- trend count
- country-linked event count
- cache state
- stale state
- connector timings
- event timing

Diagnostics do not expose API keys, stack traces, raw retry queues, or private configuration.

## Principal public endpoints

### Public Briefing and Export Studio

- `GET /public/briefing-studio`
- `GET /public/briefing-studio/brief?type=country&country=KEN`
- `GET /public/briefing-studio/export?type=country&country=KEN&format=json|csv|html`
- `GET /public/briefing-studio/diagnostics`

### Comparative Intelligence

- `GET /public/compare?country=KEN&compare=GHA`
- `GET /public/compare/indicators?country=KEN&compare=GHA`
- `GET /public/compare/trends?country=KEN&compare=GHA`
- `GET /public/compare/events?country=KEN&compare=GHA`
- `GET /public/compare/brief?country=KEN&compare=GHA`
- `GET /public/compare/export?country=KEN&compare=GHA&format=json|csv|html`


### Release and health

- `/`
- `/health`
- `/public/build-info`
- `/public/launch-status`
- `/release/public-summary`
- `/release/status`
- `/release/smoke-test`

### Countries

- `/public/countries`
- `/public/countries/search`
- `/public/countries/regions`
- `/public/countries/diagnostics`
- `/public/country/{ISO3}/overview`
- `/public/country/{ISO3}`
- `/public/country/{ISO3}/indicators`
- `/public/country/{ISO3}/trends`
- `/public/country/{ISO3}/brief`
- `/public/country/{ISO3}/evidence-lineage`
- `/public/country/{ISO3}/diagnostics`

### Events

- `/public/events`
- `/public/events/categories`
- `/public/events/sources`
- `/public/events/timeline`
- `/public/events/summary`
- `/public/events/{event_id}`

### Earth Observation

- `/public/earth-observation`
- `/public/earth-observation/layers`
- `/public/earth-observation/compare`
- `/public/earth-observation/timeline`
- `/public/earth-observation/presets`
- `/public/earth-observation/export-manifest`
- `/public/earth-observation/diagnostics`

## WordPress shortcodes

- `[sc_comparative_intelligence country="KEN" compare="GHA" view="table" height="1100"]`
- `[sc_public_briefing_studio type="country" country="KEN" height="1150"]`

Primary product:

```text
[sc_site_intelligence_app height="1000"]
```

Specialized standalone views:

```text
[sc_earth_observation_studio height="1000"]
[sc_live_event_intelligence height="1000"]
[sc_global_country_intelligence country="KEN" height="1100"]
[sc_comparative_intelligence country="KEN" compare="GHA" height="1100"]
[sc_public_briefing_studio type="country" country="KEN" height="1150"]
```

Legacy compatibility views remain available, but the long-term direction is one main standalone app embed rather than a long stack of demonstration shortcodes.

## Local development

```bash
cd backend
python3 -m pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8091
```

Open:

- API: `http://127.0.0.1:8091/`
- Docs: `http://127.0.0.1:8091/docs`
- App: `http://127.0.0.1:8091/app/`

## Validation

```bash
cd backend
python3 -m pytest -q
python3 -m compileall -q app
node --check public_app/assets/app.js
php -l ../wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php
```

Expected test result for v1.20.0:

```text
224 passed
```

## Render deployment

The repository includes `render.yaml` for the existing free Render service.

Build command:

```text
pip install -r backend/requirements.txt
```

Start command:

```text
cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Platform Core remains optional and disabled by default.

## Responsible-use boundary

Site Intelligence supports research, orientation, source review, public understanding, and documented comparison. It does not replace authoritative records, field investigation, professional environmental analysis, engineering review, legal advice, financial advice, medical advice, regulatory compliance review, emergency instructions, or safety-critical judgment.

## License

MIT. See `LICENSE`.


## v2.2.0 economics workspace

Site Intelligence v2.2.0 adds a Core-backed public workspace for official economics, markets, and sustainability records. It preserves source identity, geography, reporting period, frequency, units, vintage dates, and market-data timing labels while explicitly avoiding simulated real-time exchange data.

Public route: `/app/?view=economics`

WordPress shortcode: `[sc_economics_sustainability_observatory height="1250"]`
