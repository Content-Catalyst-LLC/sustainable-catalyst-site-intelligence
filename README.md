# Sustainable Catalyst Site Intelligence

Sustainable Catalyst Site Intelligence is the geospatial, country, Earth-observation, ocean, space, infrastructure, environmental, and live public-intelligence layer of the Sustainable Catalyst platform.

**Current release:** v4.46.0 — Unified Spatial Evidence Object & Layer Registry

## Architecture

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
