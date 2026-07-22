# Site Intelligence v3.21.0 — Public Record Archive, Provenance Ledger, and Long-Term Preservation

Live Intelligence v3.21.0 adds a long-term public-record layer above approved briefings, publication releases, and public change notices.

## Workflow

1. An already approved public source record is selected for preservation.
2. Site Intelligence creates a deterministic public-safe source snapshot and checksum.
3. A separate verifier confirms that the source has not changed and the archive record checksum is valid.
4. A different approver confirms retention, provenance, and public visibility.
5. The approved record enters an append-only chain and may be exported as JSON or Markdown for manual institutional custody.

## Preservation records

Each record includes:

- Source type and immutable source identifier
- Canonical source SHA-256
- Archive-record SHA-256
- Previous archive identifier and checksum
- Retention class and review date
- Preservation manifest with logical file checksums
- Verification and approval history
- Manual custody handoff receipts

## Integrity rules

- Only approved public records may be archived.
- The source record remains authoritative and is never mutated by the archive.
- Archive records are append-only and never deleted by Site Intelligence.
- Source drift blocks verification.
- Separate preparation, verification, and approval roles are required.
- Site Intelligence performs no remote deposit, destination write, or automatic institutional transfer.
- Credentials, recipients, and contact identities are prohibited.
