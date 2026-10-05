# Site Intelligence v4.46.0 Release Certification

Release: **Unified Spatial Evidence Object & Layer Registry**

The release is certified when:

- `sc-site-intelligence-spatial-evidence-object/2.0` is the canonical cross-domain spatial evidence interchange object.
- normalized evidence uses WGS84/EPSG:4326 geometry, a stable registered `layer_id`, bounding box, source identity, temporal context, provenance/transformation lineage, quality metadata, visibility, and SHA-256 content digest.
- the source-controlled v4.46 registry exposes 18 unique layer families across environmental, infrastructure, human, ocean, country, and live-event intelligence.
- `/public/spatial-evidence/*` exposes registry, layer, domain, schema, normalization, validation, and compatibility contracts through a modular router.
- existing `/public/spatial/*` analysis endpoints and the v2.15 legacy layer catalog remain intact.
- capability registry v1.3.0 reports a first-class `spatial-evidence-registry` family with all eight routes modularized.
- no duplicate method/path contracts or unclassified routes are introduced.
- all 28 release-bound static files report v4.46.0 while historical origin metadata remains unchanged.
- the corrected Contabo deployment promotes the v4.46 registry while preserving dynamic production data and credentials.
- WordPress remains the v4.45 thin-shell/embed bridge and the 72-shortcode compatibility ceiling stays exact.
