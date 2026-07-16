# Site Intelligence v2.25.0

## Security, Privacy, Governance, and Production Scale

This release adds a production control plane to Site Intelligence while retaining a zero-cost SQLite deployment mode. Production environments should map the database and backup paths to persistent storage.

### Core contracts

- Versioned, idempotent SQLite migrations.
- Scoped API keys stored only as SHA-256 hashes and displayed once.
- Append-only, hash-chained audit events with secret redaction.
- Privacy-request tracking without storing the supplied subject reference.
- Preview-first retention requiring explicit confirmation.
- Digest-verified SQLite backup packages and verification-only restore previews.
- Persistent job queue with leasing, bounded attempts, and explicit completion receipts.
- Deployment receipts, public-safe diagnostics, and synthetic load probes.

### Boundaries

The release does not claim automatic regulatory compliance, distributed rate limiting from a single process, an always-on job worker, automatic restoration, unbreakable security, or zero data loss without durable storage and tested procedures.
