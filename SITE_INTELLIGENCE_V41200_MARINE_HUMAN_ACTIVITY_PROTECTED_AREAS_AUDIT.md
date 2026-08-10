# Site Intelligence v4.15.0 — Marine Human Activity, Protected Areas & Maritime Pressure Audit

## Audit objective

Confirm that the new marine human-activity layer provides spatial orientation while refusing unsupported compliance, enforcement, vessel-presence, fishing-legality, and protected-area conclusions.

## Required invariants

1. AIS evidence is never described as a complete vessel census.
2. An empty AIS result is never described as proof of vessel absence.
3. Inferred fishing activity is never upgraded to illegal fishing.
4. A protected-area or management boundary is kept source-attributed.
5. Spatial overlap may be computed as geometry but never becomes a legal violation or enforcement finding.
6. Upstream API credentials and access tokens are not stored in public state, exports, fixtures, or JavaScript.
7. Source dates, geometry limits, aggregation, and coverage remain visible.
8. The v4 public architecture remains six primary areas and 35 routes.

## Source families

- NOAA / BOEM Marine Cadastre Vessel Traffic
- NOAA National Marine Protected Areas Center
- EMODnet Human Activities
- Global Fishing Watch APIs

## Result

The v4.15.0 implementation satisfies the bounded evidence model through backend normalization contracts, overlap preview semantics, browser copy, export manifests, readiness checks, and automated tests.
