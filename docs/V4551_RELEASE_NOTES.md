# Site Intelligence v4.55.1 — Core Workspace Runtime Repair

v4.55.1 repairs the six first-generation public workspace surfaces that remained unreliable under the newer standalone application shell: **Dossiers, Economics, International Law, Science, Humanitarian, and Resources**.

## Root causes repaired

1. The backend production-truth directory referenced stale, nonexistent DOM selectors such as `#economicsWorkspace`, `#scienceWorkspace`, and `#dossiersWorkspace`; the actual public surfaces are `#economicsStudio`, `#scienceStudio`, and `#dossierStudio`.
2. The browser production-truth controller was still hard-coded to release `4.39.0`, causing it to reject the current route directory and silently fall back on every load.
3. Dossiers and Resources treated optional facets/country catalogs as mandatory startup dependencies, allowing an upstream catalog failure to reject the entire workspace open operation.
4. Legacy workspace startup lacked a single resilient opener that guaranteed the registered public surface remained visible after a controller or optional request failure.
5. The offline/cache contract did not explicitly treat the workspace runtime repair as a critical shell asset.

## Repair contract

A new `workspace-runtime-repair-v4551.js` runtime owns resilient opening for six routes while preserving their existing domain controllers and backend APIs. It never fabricates missing data. When an optional service fails, the workspace remains visible, reports a degraded/fallback state, and exposes a retry action.

## Repaired route surfaces

- Economics → `#economicsStudio` → `/public/economics-sustainability`
- International Law → `#lawStudio` → `/public/international-law-observatory`
- Science → `#scienceStudio` → `/public/scientific-earth-systems`
- Humanitarian → `#humanitarianStudio` → `/public/humanitarian-conflict-displacement`
- Resources → `#resourceStudio` → `/public/trade-energy-resources`
- Dossiers → `#dossierStudio` → `/public/intelligence-dossiers`

## Runtime inventory

v4.55.1 intentionally adds no new FastAPI routes or capability families. It preserves v4.55.0 at 1,479 routes, 170 modularized routes, 27 capability families, zero unclassified routes, 12 spatial-lineage routes, and 15 transformation classes.
