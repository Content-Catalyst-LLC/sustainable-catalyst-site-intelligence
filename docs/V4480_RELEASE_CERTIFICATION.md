# Site Intelligence v4.48.0 Release Certification

Release: **v4.48.0 — Spatial Relationship & Infrastructure Graph**

Certification gates:

- canonical backend, standalone runtime, deployment manifests, and WordPress plugin report v4.48.0;
- capability registry generation 1.5.0 includes first-class `spatial-relationship-graph` capability;
- nine `/public/spatial-graph/*` routes are modularized;
- 12 relationship types declare directionality and automatic-vs-explicit derivation rules;
- v4.46 evidence/layer contracts and v4.47 spatiotemporal contracts remain available;
- automatic relationships use declared bounding-box-first spatial semantics and never fabricate semantic dependency edges;
- explicit infrastructure relationships preserve source evidence digests and assertion provenance;
- graph, edge, query, neighborhood, path, and analysis results are deterministic/content-addressed;
- route inventory remains fully classified and duplicate-free;
- runtime inventory certifies at 1,386 routes / 77 modularized / 19 capability families / 9 graph routes;
- 30 release-bound static policy/registry files advance together;
- corrected Contabo deployment behavior preserves dynamic production data while promoting release-bound files;
- WordPress remains `thin-shell-and-embed-bridge` with the 72-shortcode ceiling preserved.

The current release suite passes 63 tests covering v4.48 graph behavior, v4.47 spatiotemporal compatibility, v4.46 spatial-evidence compatibility, release-reconciliation invariants, source reconciliation, homepage preservation, and energy runtime/spatial regressions.
