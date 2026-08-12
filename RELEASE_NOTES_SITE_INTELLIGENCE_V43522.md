# Site Intelligence v4.35.22 — Country Evidence Reconciliation & Scope Integrity

## Release objective
Turn the v4.35.21 country federation into an explainable selection system. The release must distinguish exact-concept disagreement from geographic, temporal and methodological mismatch; disclose why a value was selected; and prevent Palestine-wide statistics from being silently replaced or blended with Gaza- or West Bank-only observations.

## Delivered
- Added a country evidence-reconciliation engine with explicit concept, unit, geographic-scope, reference-period and methodology checks.
- Added Palestine-wide PCBS-first statistical precedence for exact supported national concepts, retaining World Bank as harmonized comparison/fallback.
- Added a hard subnational scope guard: Gaza and West Bank records remain scoped context and are ineligible for automatic Palestine-wide national selection.
- Added material discrepancy classification without averaging or synthetic blending.
- Added temporal-difference handling so different reference periods are not automatically labeled contradictions.
- Added methodology-divergence disclosure when same-period exact-concept values differ materially.
- Added explicit fallback state when a higher-precedence source is not present in the current candidate set.
- Added country-workspace Evidence Reconciliation panel showing selected source, reconciliation state, preferred-source gaps and selection rationale.
- Added public readiness, generic reconcile, and country snapshot endpoints.
- Preserved v4.35.21 Palestine federation/Wikimedia context, v4.35.20 linked-record recovery, and v4.35.19 semantic-truth/production-soak controls.

## Truth boundaries
- Site Intelligence does not average conflicting observations into a synthetic country statistic.
- Source precedence is applied only after exact concept, compatible units and geographic scope have been established.
- A Gaza or West Bank observation cannot silently stand in for a Palestine-wide national statistic.
- Different reference periods are temporal differences rather than automatic contradictions.
- Different methodologies may produce different valid estimates; the methodology difference remains attached to the discrepancy.
- Absence of a preferred source from the current candidate set does not mean the source has no data; it means that an exact candidate was not available to this reconciliation operation.

## Release readiness
The reconciliation readiness surface is deterministic and network-free. External provider availability remains non-blocking for release promotion.

## Frozen validation
- Deterministic Python suite: **1,636 / 1,636 passed**.
- Workspace browser control plane: **35 / 35 desktop**, **35 / 35 mobile**, **35 / 35 iframe**, with **0 degraded routes**.
- v4.35.22 targeted Palestine/reconciliation release slice: **19 / 19 passed**.
- JSON/GeoJSON parse: **134 files passed**.
- JavaScript validation: **152 files passed**.
- WordPress PHP syntax: **passed**.
- Static security scan: **0 findings**.
- Application-shell measurements remain inside inherited gates: HTML **171,981 / 172,000 bytes**, CSS **101,860 / 102,000 bytes**, and HTML+CSS+application JavaScript **485,433 / 500,000 bytes**.
