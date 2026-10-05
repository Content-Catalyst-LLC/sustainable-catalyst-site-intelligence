# Sustainable Catalyst Site Intelligence

Sustainable Catalyst Site Intelligence is the geospatial, country, Earth-observation, ocean, space, infrastructure, environmental, and live public-intelligence layer of the Sustainable Catalyst platform.

**Current release:** v4.51.0 — Spatial Research Object & Cross-Product Handoffs


### v4.51 Spatial Research Object & Cross-Product Handoffs

Site Intelligence now packages a complete spatial investigation as a content-addressed research object spanning canonical evidence, spatiotemporal results, relationship graphs, live events, and source-federation context. Provider-neutral preview handoffs are available for Workspace, Knowledge Library, Research Librarian, Research Lab, Workbench, Decision Studio, and Platform Core. Handoffs never perform implicit delivery, publication, remote writes, or source mutation.

### v4.50 Global Source Federation

Site Intelligence now exposes a first-class global/regional source authority registry over its existing connector ecosystem. Source identity, jurisdiction scope, authority class, regional eligibility, language, federation mode, quality signals, and deterministic selection are machine-readable, while user trust choices remain separate from source authority and provenance. Federation planning is preview-only and performs no automatic remote fetch, import, or write.

### v4.49 Live Geospatial Fusion

Site Intelligence now normalizes live geospatial events into provenance-preserving evidence, reconciles strict cross-source identities, evaluates lifecycle/freshness against explicit analysis time, and fuses live events with v4.46 layers and v4.48 infrastructure graphs without treating spatial overlap as confirmed impact.


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
