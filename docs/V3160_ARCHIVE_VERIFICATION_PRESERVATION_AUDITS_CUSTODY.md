# Site Intelligence v3.22.0 — Archive Verification, Preservation Audits, and Institutional Custody

v3.22.0 adds a preservation-assurance layer above the append-only public archive. It verifies retained record checksums, source snapshots, preservation manifests, and provenance-chain links; records findings; and creates human-approved custody packages for manual institutional transfer.

## Workflow

1. Define an audit scope and cadence.
2. Run deterministic checksum and chain verification.
3. Record warning and critical findings without altering archived records.
4. Approve the audit through a separate human role.
5. Prepare an institution-ready custody package from an approved audit.
6. Verify and approve the package through separate roles.
7. Record a non-sensitive manual custody receipt after an external transfer.

## Explicit boundaries

- Cadence metadata is not a hosted scheduler.
- Public-source drift is reported as a warning; the preserved source snapshot remains unchanged.
- Critical integrity findings cannot be hidden or silently repaired.
- Custody packages do not perform remote deposits or destination writes.
- Archives remain append-only and independently addressable.
