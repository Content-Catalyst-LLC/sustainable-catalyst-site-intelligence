# Site Intelligence v4.48.0 — Spatial Relationship & Infrastructure Graph

v4.48.0 turns canonical spatial evidence and v4.47 cross-layer analysis into an explicit relationship graph. The graph is deterministic, content-addressed, and provenance-preserving: nodes reference canonical v4.46 evidence objects, while edges are either caller-asserted infrastructure relationships or declared spatial relationships derived under the v4.47 bounding-box-first semantics.

## New contracts

- `sc-site-intelligence-spatial-relationship-registry/1.0`
- `sc-site-intelligence-spatial-relationship-graph/1.0`
- `sc-site-intelligence-spatial-graph-query-result/1.0`
- `sc-site-intelligence-spatial-graph-neighborhood/1.0`
- `sc-site-intelligence-spatial-graph-path/1.0`
- `sc-site-intelligence-spatial-graph-analysis/1.0`

## New graph capabilities

- deterministic graph construction over canonical spatial evidence;
- automatic `spatial-intersects` and `co-located-with` edges using declared v4.47 bounding-box semantics;
- explicit directed and undirected infrastructure relationships;
- `connected-to`, `depends-on`, `supplies`, `serves`, `upstream-of`, `downstream-of`, `part-of`, `exposed-to`, `monitors`, and `adjacent-to` contracts;
- graph subsetting by node, layer, domain, capability, and relationship type;
- bounded neighborhood traversal with directionality;
- deterministic shortest-path traversal;
- connected-component, degree, relationship-count, cross-domain, infrastructure-edge, and critical-node analysis;
- SHA-256 graph/edge/path/neighborhood/analysis digests;
- source evidence digest lineage in graph and analysis outputs.

Automatic derivation does **not** infer semantic dependencies such as `depends-on`, `supplies`, or `serves`. Those relationships require explicit caller assertions with provenance. This avoids converting simple spatial coincidence into unsupported causal or infrastructure claims.

## Compatibility

The v4.46 spatial evidence registry and v4.47 spatiotemporal engine remain available and are consumed by v4.48. WordPress remains a thin shell/embed bridge, the standalone application remains authoritative, and the 72-shortcode compatibility ceiling is unchanged.
