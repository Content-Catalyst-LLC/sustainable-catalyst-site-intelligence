# v4.35.15 Workspace Evidence Unification & Truth-Layer Audit

## Problem repaired

Before v4.35.15, the public country workspace and Record Truth could follow different indicator evidence paths. The country workspace used `live_country_intelligence.country_indicators()`, which could display a live/cached World Bank observation. Record Truth used `GlobalCountryDataTruth.country_indicators()`, which primarily represented packaged fallback coverage. For a country such as Palestine this allowed the visible card to show a real source observation while Truth could simultaneously report the same indicator as missing.

## Canonical observation contract

v4.35.15 introduces `sc-site-intelligence-canonical-observation/1.0`. Each country-indicator observation retains:

- canonical observation identifier;
- country and indicator identity;
- numeric/text value and explicit availability state;
- original/display units;
- observation year/date and retrieval timestamp;
- source identifier, publisher, URL and authority class;
- live/cached/stale/reference/unavailable presentation state;
- metric concept and forbidden substitutions;
- cadence-aware freshness assessment;
- evidence-selection record;
- Platform Core lineage when present;
- limitations; and
- deterministic SHA-256 fingerprint.

Response-generation timestamps and freshness reference timestamps are excluded from the canonical fingerprint so identical evidence produces the same observation identity.

## Consumer unification

The same canonical object now supplies:

1. `/public/country/{country}/indicators`;
2. `/public/country/{country}` headline highlights;
3. country evidence metadata;
4. `/public/record-truth/indicator/{country}/{indicator}`;
5. `/public/record-truth/country/{country}`; and
6. `/public/record-truth/manifest` indicator entries.

Map-layer Record Truth remains on its established context-only provenance contract.

## Palestine electricity regression

The test contract explicitly verifies both directions:

- if the canonical Palestine electricity-access observation is `100.0`, the workspace and Truth both disclose `100.0` with the same canonical SHA-256; and
- if the canonical value is missing, both surfaces disclose missing.

The semantic rule from v4.35.7 remains attached: `EG.ELC.ACCS.ZS` is structural electricity access and cannot be used as current supply availability, grid reliability, outage status, hours of supply, or generator-dependence evidence.

## Compatibility

Legacy Record Provenance contract names, indicator record IDs, export-manifest shape, map-layer entries, and public endpoint paths are retained. New fields are additive, including `canonical_observation`, `canonical_observation_sha256`, and unification-contract metadata.

## Deployment boundary

`/public/workspace-evidence/readiness` is deterministic and performs no upstream network calls. The GitHub/Render promotion verifier checks this first-party contract, but external source health continues to be handled separately and remains non-blocking.
