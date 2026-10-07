# Site Intelligence v4.55.0 — Spatial Provenance & Transformation Lineage

v4.55.0 makes transformation provenance a first-class Site Intelligence contract. It records explicit, content-addressed transformation events across spatial evidence and derived analysis, builds deterministic lineage chains and graphs, traces ancestors and descendants, verifies chain integrity without rerunning analysis, and binds lineage into v4.54 reproducible packages.

## New capability family

`spatial-provenance-lineage` owns 12 modular routes under `/public/spatial-lineage`.

## Transformation classes

The registry defines 15 classes: source ingestion, normalization, reprojection, resampling, spatial join, filtering, aggregation, interpolation, graph derivation, model binding, scenario derivation, exposure analysis, threshold evaluation, visualization derivation, and manual annotation.

## Architectural boundaries

Lineage is declared rather than inferred. Transformation history is not causal attribution. Derived artifacts remain distinct from observations. Missing history is reported rather than repaired. Integrity verification never reruns analysis. Manual annotations remain explicitly human asserted. Research objects and packages are not mutated.

## Runtime inventory

- Version: 4.55.0
- Capability registry: 2.2.0
- Routes: 1479
- Modularized routes: 170
- Capability families: 27
- Unclassified routes: 0
- Spatial lineage routes: 12
- Transformation classes: 15
- Release-bound static files: 38
