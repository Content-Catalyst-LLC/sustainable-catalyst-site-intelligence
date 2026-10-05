# Site Intelligence v4.47.0 — Spatiotemporal Query & Cross-Layer Analysis Engine

v4.47.0 turns the v4.46 unified spatial-evidence contract into an executable analysis surface. The engine is stateless, deterministic, and provenance-preserving: it operates on caller-supplied canonical evidence objects (or raw objects that can be normalized by the v4.46 contract) and does not silently mutate source evidence or fetch/duplicate underlying domain datasets.

## New contracts

- `sc-site-intelligence-spatiotemporal-query/1.0`
- `sc-site-intelligence-spatiotemporal-query-plan/1.0`
- `sc-site-intelligence-spatiotemporal-query-result/1.0`
- `sc-site-intelligence-cross-layer-join-result/1.0`
- `sc-site-intelligence-cross-layer-analysis-result/1.0`
- `sc-site-intelligence-spatiotemporal-operator-registry/1.0`

## New analysis capabilities

- layer/domain/capability filtering;
- WGS84 bounding-box predicates: intersects, within, contains, disjoint;
- temporal interval predicates: overlaps, within, contains, before, after, at;
- property predicates: eq, ne, gt, gte, lt, lte, in, contains, exists;
- deterministic content-addressed query plans;
- query execution with source-object content-digest lineage;
- cross-layer space/time joins;
- grouped count/sum/mean/min/max analysis;
- cross-layer overlap matrix generation.

Spatial relation semantics are explicitly `bounding-box-first`. The engine does not represent those relations as exact polygon topology. Exact/proximity/topological engines can be added later without changing this contract.

## Compatibility

The v4.46 spatial evidence registry and all legacy `/public/spatial/*` endpoints remain available. WordPress remains a thin shell/embed bridge. The 72-shortcode compatibility ceiling is unchanged.
