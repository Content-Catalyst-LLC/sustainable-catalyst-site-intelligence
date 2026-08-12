# Site Intelligence v4.35.24 — Palestine-First Country Navigation Integrity Audit

## Observed defect

After v4.35.23, Palestine was still not reliably selected outside the dedicated Country workspace, and selecting Israel could still leave or move the application to Palestine. This was a release-blocking identity/navigation defect.

## Root cause

v4.35.23 did not cover every country-navigation path. The top-level Overview selector still used the legacy `loadCountry()` flow. In addition, frontend and backend live-catalog merge order could overwrite first-party identity fields with external metadata despite the stated canonical-first policy. The cartographic workspace could then apply a delayed live-catalog map focus and overwrite an earlier correct selection.

## Repair invariants

1. Bundled first-party identity wins for ISO3, ISO2, display name, canonical coordinates and other identity-bearing fields.
2. External country catalogs are enrichment-only.
3. Overview commits the selected ISO3 before upstream retrieval.
4. Overview map focus uses canonical coordinates immediately.
5. Upstream coordinates are accepted only after the returned ISO3 matches the requested ISO3.
6. Cross-identity responses are blocked.
7. Delayed cartographic catalog hydration cannot replace canonical identity or coordinates.
8. Palestine and Israel remain separate identities; neither is renamed to the other.

## Hostile-source regression

The browser fixture deliberately supplies an external country catalog where:

- `ISR` is mislabeled with Palestine's name, ISO2 and coordinates;
- `PSE` is mislabeled with Israel's name, ISO2 and coordinates;
- country evidence responses return the opposite ISO3.

The release passes only when:

- selecting `PSE` leaves the selector/profile on `PSE / Palestine` and the map at the canonical Palestine focus;
- selecting `ISR` leaves the selector/profile on `ISR / Israel` and the map at the canonical Israel focus;
- mismatched evidence is rejected with the identity-mismatch state.

## Release gate

`/public/country-navigation-integrity/readiness` verifies the canonical-overrides-external invariant without network calls. `/public/deployment-verification` requires this plane alongside the existing country identity, evidence reconciliation, Palestine federation, linked-record, semantic-truth, soak and browser gates.
