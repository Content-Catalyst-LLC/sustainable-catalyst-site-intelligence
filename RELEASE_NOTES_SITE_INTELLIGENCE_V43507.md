# Site Intelligence v4.35.9 — Source Precedence, Metric Semantics & Freshness Intelligence

## Purpose

v4.35.9 adds a deterministic evidence-intelligence layer above Site Intelligence's authoritative connector and provenance systems. The release decides whether evidence is semantically eligible for a requested metric before considering source authority, jurisdictional precedence, status, or freshness.

## Major changes

- Added a metric-concept registry with explicit claims, canonical units, publication cadence, compatible indicator identifiers, and forbidden substitutions.
- Separated `electricity_structural_access` from `electricity_operational_availability`.
- Added jurisdiction-aware precedence rules, including Palestine structural access: PCBS → World Bank fallback/comparison.
- Added Palestine operational electricity precedence that excludes World Bank and requires operator/energy-authority/humanitarian operational evidence.
- Added cadence-aware freshness states: current, recent, older, stale, dated, unknown.
- Added deterministic evidence selection with semantic compatibility before authority/freshness scoring.
- Added exact-concept conflict disclosure without automatic averaging or blending.
- Added evidence-selection SHA-256 fingerprints.
- Enriched Record Truth indicator responses with metric concept, forbidden substitutions, precedence context, and freshness.
- Added an Evidence Intelligence panel to the Source & Methodology Studio.
- Preserved the v4.35.6 twenty-interface authoritative connector catalog and v4.35.3.1 non-blocking external-source-health deployment policy.

## Public endpoints

- `/public/evidence-intelligence`
- `/public/evidence-intelligence/metrics`
- `/public/evidence-intelligence/precedence`
- `/public/evidence-intelligence/freshness`
- `/public/evidence-intelligence/indicator/{indicator_id}`
- `/public/evidence-intelligence/select`
- `/public/evidence-intelligence/readiness`

## Electricity integrity boundary

`EG.ELC.ACCS.ZS` maps only to the structural-access concept. It does not establish current supply availability, reliability, outages, hours of service, generator dependence, or present service continuity.
