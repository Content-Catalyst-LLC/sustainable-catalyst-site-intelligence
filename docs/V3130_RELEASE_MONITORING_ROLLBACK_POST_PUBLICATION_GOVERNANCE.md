# v3.13.0 — Release Monitoring, Rollback, and Post-Publication Governance

Site Intelligence v3.13.0 extends the governed publication workflow beyond package preparation. It records externally performed deployments, checks published package integrity through human-supplied verification receipts, tracks post-publication issues, and prepares correction or rollback packages.

## Operating model

1. A human or external deployment system publishes an approved v3.12 release package.
2. An authorized operator records the destination, adapter, environment, and immutable checksums.
3. A different human verifies the published release checksum, payload checksum, adapter package checksum, destination accessibility, source links, freshness labels, and correction path.
4. Issues may be opened against a release or deployment receipt.
5. Corrections and rollback packages require separate human approval.
6. Site Intelligence creates manual handoff receipts only; it never changes the destination.

## Boundaries

- No network verification is claimed.
- No deployment or rollback is executed.
- No WordPress or institutional destination is modified.
- No credentials, tokens, subscriber identities, or recipient data are stored.
- Private corrections never enter the public correction feed.
- Public correction notices require explicit approval.
