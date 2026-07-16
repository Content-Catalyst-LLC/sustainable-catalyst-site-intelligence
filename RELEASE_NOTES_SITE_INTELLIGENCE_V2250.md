# Site Intelligence v2.25.0

## Security, Privacy, Governance, and Production Scale

Site Intelligence v2.25.0 adds the production control plane required to operate the expanding public intelligence platform more safely and consistently.

### Added

- Versioned SQLite database migrations
- Scoped API keys stored as hashes
- Hash-chained, secret-redacted audit logs
- Privacy-request workflow and deadlines
- Preview-first retention and confirmed deletion receipts
- Digest-verified backup archives and restore previews
- Persistent bounded job queue
- Deployment validation receipts
- Production diagnostics and synthetic load probes
- Stronger public security headers
- Public Governance workspace and WordPress shortcodes

### Responsible-use boundaries

Local rate limiting is not described as distributed enforcement. The queue does not claim an always-on worker. Backups are not described as successful disaster recovery until restoration is tested. The release does not claim automatic compliance or unbreakable security.
