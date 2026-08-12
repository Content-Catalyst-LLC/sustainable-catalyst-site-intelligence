# Site Intelligence v4.35.22 — Country Evidence Reconciliation & Scope Integrity Audit

## Problem addressed
v4.35.21 made source roles visible, but a federated country page could still leave users to infer why one value was displayed when multiple authorities or geographic scopes existed. For Palestine this is particularly risky: Palestine-wide, West Bank-only and Gaza-only evidence must remain distinguishable, and a harmonized World Bank series must not look like an automatically preferred national authority when an exact PCBS candidate is absent from the current candidate set.

## Selection order
v4.35.22 evaluates evidence in this order:
1. exact metric concept;
2. compatible units;
3. national versus subnational geography;
4. declared jurisdiction/source precedence;
5. authority class;
6. cadence-aware freshness;
7. observation status.

Authority and freshness cannot rescue a semantically or geographically incompatible record.

## Palestine scope integrity
The reconciliation engine normalizes Palestine national aliases to `PSE` and preserves explicit West Bank and Gaza scopes as `PSE-WBK` and `PSE-GZA`. Those subnational records remain visible as context but are ineligible for automatic national selection.

## Discrepancy handling
Same-concept, same-unit, same-national-geography candidates are compared without automatic blending. A material difference can be classified as:
- `material-discrepancy-review` when the reference period is aligned;
- `material-discrepancy-methodology-diverges` when the period is aligned but methodologies differ;
- `different-reference-periods` when the observations refer to different periods;
- `unit-incompatible-do-not-compare` when units are not aligned.

The comparison record preserves both values and a non-blending flag.

## Preferred-source gap
For Palestine official statistics, PCBS is the preferred national statistical authority when an exact supported concept is present. If the country workspace currently contains only a World Bank harmonized candidate, the reconciliation state is `fallback-selected-preferred-source-not-in-candidate-set`. This is intentionally different from saying PCBS is unavailable or has no data.

## Workspace integration
A lazy Evidence Reconciliation panel is added to the country workspace. It does not block the underlying country indicators. It summarizes current selection states and explains source-precedence gaps without changing the displayed canonical observation behind the user's back.

## Release boundary
The readiness gate performs no upstream calls. Live source availability remains non-blocking. The release verifies the reconciliation rules and route contracts, not the current health of PCBS, World Bank, HDX, Wikimedia or other external systems.

## Validation evidence
The frozen implementation passed **1,636 / 1,636 deterministic tests**. The browser control plane passed **35 / 35 routes** in desktop, mobile and iframe modes with zero degraded routes. The targeted reconciliation/Palestine slice passed **19 / 19 tests**. Static validation parsed 134 JSON/GeoJSON files, validated 152 JavaScript files, passed WordPress PHP syntax, and returned zero static-security findings.

The inherited application budgets were not raised for this release: HTML is 171,981 bytes against a 172,000-byte gate, CSS is 101,860 bytes against a 102,000-byte gate, and the measured HTML+CSS+application-JavaScript shell is 485,433 bytes against a 500,000-byte gate.
