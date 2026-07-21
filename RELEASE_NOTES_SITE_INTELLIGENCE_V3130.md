# Site Intelligence v3.13.0

## Release Monitoring, Rollback, and Post-Publication Governance

This release extends Live Intelligence release governance into the post-publication lifecycle.

### Delivered

- Externally reported deployment receipts tied to approved publication releases.
- Human verification of release, payload, and adapter-package checksums.
- Required checks for destination accessibility, source links, freshness labels, and a correction path.
- Post-publication issue records with bounded severity and evidence references.
- Human-approved public or private correction packages.
- Approved-release rollback manifests with immutable source and target checksums.
- Manual correction and rollback handoff receipts.
- Public aggregate status and approved correction-notice routes.
- A read-only WordPress release-operations surface.

### Governance

Site Intelligence performs no network verification, deployment, rollback, deletion, WordPress write, institutional write, webhook delivery, or credential storage. Deployment and destination status are human-reported. Private corrections are excluded from the public feed, and both corrections and rollbacks require separation of duties.
