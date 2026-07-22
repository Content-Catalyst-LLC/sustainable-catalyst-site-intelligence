# Site Intelligence v3.20.0

## Archive Verification, Preservation Audits, and Institutional Custody

This release adds repeatable preservation assurance above the v3.15.0 public-record archive. Approved archive records can be audited for checksum, preservation-manifest, source-snapshot, provenance-chain, retention, and custody integrity without changing the archived record.

### Added

- Manual, quarterly, semiannual, and annual preservation-audit definitions.
- Full-chain, record-sample, retention-review, and custody-review audit types.
- Checksum verification for archive records, preserved source snapshots, and preservation manifests.
- Provenance-chain verification across linked archive records.
- Warning and critical preservation findings with immutable finding checksums.
- Human-reviewed public audit reports.
- Institution-ready custody manifests and package checksums.
- Separate custody preparation, verification, approval, and manual receipt records.
- JSON and Markdown audit and custody packages.
- Read-only public and WordPress preservation-assurance surfaces.

### Governance boundaries

- No automatic scheduler is claimed.
- No archive record is mutated or deleted.
- No remote institutional deposit is performed.
- No destination write is performed.
- No credentials, subscribers, or recipient identities are stored.
- Critical findings require explicit acknowledgment before audit approval.
- Audit and custody approval use separation of duties.
