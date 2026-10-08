# Sustainable Catalyst Site Intelligence v4.55.3.1

Sustainable Catalyst Site Intelligence is the geospatial, country, Earth-observation, ocean, space, infrastructure, environmental, and live public-intelligence layer of the Sustainable Catalyst platform.

**Current release:** v4.55.3.1 — API Reliability & Contract Truth Repair


## v4.55.3.1 API Reliability & Contract Truth Repair

- Separates process liveness (`/health`) from required data readiness (`/ready`).
- Adds `/public/capability-health` with an explicit live-probe mode.
- Adds six `/public/reliable/*` domain routes that distinguish `no-records` from dependency failure and use HTTP 503 when the requested dependency is unavailable.
- Changes capability maturity default from `production` to `migration`; production maturity is now explicit.
- Adds a visible API data-readiness state to the standalone home surface.
- Adds no new providers or domain features; v4.55.3.2 remains the functional-parity recovery build.

### v4.55.2 Advanced Domain Intelligence Workspace Expansion

- Converts Dossiers, Economics, International Law, Science, Humanitarian, and Resources from shallow category workspaces into first-class analytical research surfaces.
- Adds current-record analysis modes, source-aware summaries, explicit comparison/time/scenario context, provenance boundaries, research workflows, and deterministic research packets.
- Adds an Advanced Research panel directly inside all six standalone workspaces so users can analyze the records already loaded on screen.
- Keeps missing data missing and disables automatic causal, legal, investment, culpability, and security-risk conclusions.


### v4.54 Reproducible Spatial Intelligence Packages

- Adds deterministic, sealed spatial intelligence packages spanning v4.46–v4.53 evidence, analysis, graph, live-event, federation, predictive, scenario/exposure/change, and advanced-domain context.
- Adds content-addressed manifests, integrity verification, inspection, package comparison, and human-authorized reproduction plans without automatically rerunning analysis.
- Adds preview-only export plans for Workspace, Knowledge Library, Research Librarian, Research Lab, Workbench, Decision Studio, Platform Core, and local filesystem archives.
- Rejects credentials and private session material, preserves observation-vs-derived boundaries, and requires downstream validation before import.

### v4.53 Scenario, Exposure & Change Intelligence + Advanced Domain Parity

- Adds deterministic scenario definition/comparison, derived change, potential exposure, threshold evaluation, and graph/live/predictive/research context while preserving observation-vs-model boundaries.
- Repairs Economics and International Law workspace resilience so optional country/facet/catalog failures no longer collapse their public surfaces.
- Adds advanced parity APIs and research panels for International Law, Economics, Ocean, and Space covering evidence, comparison, scenario, provenance, research handoff, export, and diagnostics.
- Ocean gains multi-variable/depth-aware analysis across marine systems; Space gains mission/target/observation context across orbital, planetary, astronomy, solar-system, exoplanet, SETI, and live-space capabilities.

### v4.52 Predictive Spatial Intelligence Consumer

- Consumes provider-neutral forecast, probability, uncertainty, calibration, and scenario artifacts from Workspace/Core, existing Site Intelligence model governance, or explicit published external sources.
- Binds predictive artifacts to the canonical v4.46 spatial layer registry without converting model output into observation truth.
- Adds deterministic query, comparison, scenario, calibration-context, spatial binding, and v4.51 research-context contracts.
- Site Intelligence does not train, retrain, automatically select, or rank predictive models in this release.

### v4.51 Spatial Research Object & Cross-Product Handoffs

Site Intelligence now packages a complete spatial investigation as a content-addressed research object spanning canonical evidence, spatiotemporal results, relationship graphs, live events, and source-federation context. Provider-neutral preview handoffs are available for Workspace, Knowledge Library, Research Librarian, Research Lab, Workbench, Decision Studio, and Platform Core. Handoffs never perform implicit delivery, publication, remote writes, or source mutation.

### v4.50 Global Source Federation

Site Intelligence now exposes a first-class global/regional source authority registry over its existing connector ecosystem. Source identity, jurisdiction scope, authority class, regional eligibility, language, federation mode, quality signals, and deterministic selection are machine-readable, while user trust choices remain separate from source authority and provenance. Federation planning is preview-only and performs no automatic remote fetch, import, or write.

### v4.49 Live Geospatial Fusion

Site Intelligence now normalizes live geospatial events into provenance-preserving evidence, reconciles strict cross-source identities, evaluates lifecycle/freshness against explicit analysis time, and fuses live events with v4.46 layers and v4.48 infrastructure graphs without treating spatial overlap as confirmed impact.


## v4.55.3 standalone web application

Site Intelligence v4.55.3 ships an independent `web/` application intended for `https://intelligence.sustainablecatalyst.com`. The FastAPI service remains the machine-facing authority at `https://site-intelligence-api.sustainablecatalyst.com`. WordPress is a public-site launch bridge only; the standalone application owns routing, country context, browser state, and API transport. The legacy FastAPI `/app/` shell is retained temporarily for compatibility but is no longer the preferred user application.

## Architecture

### v4.47 spatiotemporal analysis architecture

Site Intelligence v4.47.0 consumes the canonical v4.46 spatial evidence object and layer registry through a deterministic, stateless query engine. It adds WGS84 bounding-box spatial predicates, temporal interval predicates, property filters, cross-layer joins, grouped aggregation, content-addressed query plans/results, and provenance-preserving source-digest lineage without changing source records or legacy spatial APIs.

### v4.43 modular route architecture

Site Intelligence v4.43.0 begins the staged decomposition of the FastAPI application. Foundational system/runtime routes and data-truth/provenance routes now live in explicit `APIRouter` modules under `backend/app/routers/`. The machine-readable capability registry inventories the complete API surface, reports router ownership, and exposes migration state without changing existing public URLs. Remaining legacy routes stay compatible in `main.py` and can be moved family-by-family in later releases.


Site Intelligence combines source-aware geospatial evidence, country intelligence, environmental observation, infrastructure context, and public-facing analytical workspaces while preserving explicit source and evidence boundaries.

- **Country intelligence** — country identity, indicators, official and harmonized evidence, country-linked records, provenance, and evidence hierarchy.
- **Earth & environmental intelligence** — atmosphere, climate, hydrology, cryosphere, terrestrial ecosystems, soils, wetlands, biodiversity, agriculture, geosphere, coastal change, and related Earth-observation domains.
- **Ocean intelligence** — ocean surface, water column, seafloor, missions, vehicles, observatories, biodiversity, bioacoustics, pollution, maritime governance, and coastal evidence.
- **Space intelligence** — orbital Earth observation, astronomical observation, solar-system missions, exoplanets, SETI/technosignature context, and related source-bounded space evidence.
- **Infrastructure intelligence** — energy systems, transportation, digital connectivity, water/sanitation, industrial systems, mining/materials, settlements, waste, and other spatial infrastructure layers.
- **Live intelligence** — bounded current signals, monitoring, event streams, public summaries, and source-health-aware live interfaces.
- **Spatial reasoning** — maps, route-aware workspaces, spatial evidence, country selection, comparison, and geospatial presentation.
- **Backend runtime** — FastAPI services, authoritative source connectors, data-truth controls, source governance, runtime state, and public APIs.
- **WordPress interface** — public Site Intelligence application, homepage snapshot, country and thematic experiences, and Sustainable Catalyst integration.
- **Platform integration** — governed handoffs to Platform Core, Research Librarian, Knowledge Library, Workbench, Decision Studio, and related products.

Site Intelligence preserves distinctions between observations, models, forecasts, mapped infrastructure, source-issued notices, harmonized statistics, and derived analytical context. It does not silently convert one evidence type into another or present inference as source truth.

## Repository layout

- `backend/` — FastAPI backend, public application assets, source connectors, data, tests, and runtime configuration.
- `deploy/` — production deployment material.
- `docs/` — current architecture, source, integration, and operational documentation.
- `scripts/` — active build, validation, release, deployment, and operational tooling.
- `wordpress-plugin/` — Sustainable Catalyst Site Intelligence WordPress plugin.
- `compose.yml` — container orchestration definition.
- `render.yaml` — retained deployment configuration.

## Release history

Historical release notes, validation reports, audit files, terminal-command files, install/test notes, package receipts, manifests, and one-off per-version promotion/deployment scripts are intentionally not retained at the root of `main`.

The exact repository state immediately before the September 29, 2026 cleanup is preserved on:

`archive/pre-root-cleanup-2026-09-29-site-intelligence`

Git history continues to preserve prior source and release artifacts. Generated release material should live in release bundles, Git history, or ignored staging directories rather than accumulating in the source-tree root.

## v4.55.2 — Spatial Provenance & Transformation Lineage

Adds content-addressed transformation events, explicit lineage chains and graphs, ancestor/descendant tracing, integrity verification, package-lineage context, and non-ranking lineage comparison across spatial evidence and derived analysis. Lineage is declared rather than inferred; missing history is reported rather than repaired.

### v4.55 spatial lineage API

`/public/spatial-lineage` exposes registry/schema discovery, transformation recording and validation, deterministic chain creation, lineage graphs, ancestor/descendant tracing, chain verification, v4.54 package context, lineage comparison, and compatibility contracts.
