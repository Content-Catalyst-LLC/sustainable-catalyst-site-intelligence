# Site Intelligence v4.35.12 — Workspace Evidence Unification & Truth-Layer Repair

Site Intelligence v4.35.12 removes the split evidence path between country-workspace indicator cards and Record Truth. Country headline values, evidence metadata, Truth responses, country truth catalogs, and record-truth manifests now resolve from one canonical country-indicator observation object.

## Primary changes

- Added `workspace_evidence_unification_v4358.py` with a canonical observation schema and deterministic SHA-256 identity.
- Added `record_provenance_v4358.py`, which renders Record Truth from the canonical workspace observation rather than the separate packaged-snapshot country-truth registry.
- Added `/public/workspace-evidence`, `/public/workspace-evidence/readiness`, country-catalog, and country-indicator canonical-observation endpoints.
- Attached canonical observations to `/public/country/{country}/indicators` and country-profile highlights.
- Added a visible **Truth** control to country indicator cards and exposed canonical observation identifiers/fingerprints inside the Truth drawer.
- Preserved legacy Record Provenance endpoint/manifest contracts for compatibility while adding canonical observation fingerprints.
- Preserved v4.35.7 metric semantics and freshness boundaries, including the strict distinction between structural electricity access and current electricity availability.
- Added first-party Render verification of the workspace-evidence readiness contract; external source availability remains non-blocking.

## Integrity rule

A displayed workspace value and its Truth response must have the same canonical observation identifier and SHA-256. If the canonical observation is missing, every consumer must display it as missing. No Truth surface may independently substitute a packaged snapshot, zero, or different observation.

## Validation

The release carries 1,479 deterministic tests, including 12 new v4.35.12 unification regressions. The suite preserves the complete v4.35.7 connector, deployment, source-precedence, Palestine-resolution, domain-workspace, and Record Provenance compatibility contracts.
