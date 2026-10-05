# v4.49.0 Release Certification

Certified release: **Site Intelligence v4.49.0 — Live Geospatial Event Fusion**.

Certification gates:

- canonical release identity aligned across backend, standalone application, WordPress plugin, manifests, and release-bound data;
- 13 modular live-geospatial API routes registered as a first-class capability family;
- canonical event normalization produces v4.46 spatial evidence lineage and SHA-256 content digests;
- USGS, NASA EONET, and NOAA/NWS source adapters certified with source identity preserved;
- strict cross-source reconciliation tested without fuzzy merging;
- lifecycle, severity, freshness, space/time filtering, layer fusion, graph fusion, and snapshots tested;
- event-to-layer and event-to-graph outputs explicitly retain `impact_confirmed=false` unless future source evidence establishes otherwise;
- v4.46, v4.47, and v4.48 compatibility suites retained;
- 31 release-bound static files promoted by the corrected Contabo deployment contract;
- WordPress remains `thin-shell-and-embed-bridge` and the 72-shortcode compatibility ceiling is unchanged.

Current-release test gate: **79 tests passing** before package verification.

Runtime inventory certified before packaging:

- FastAPI routes: **1,399**
- modularized routes: **90**
- capability families: **20**
- live-geospatial routes: **13/13 modularized**
- unclassified routes: **0**
- duplicate method/path contracts: **0**
