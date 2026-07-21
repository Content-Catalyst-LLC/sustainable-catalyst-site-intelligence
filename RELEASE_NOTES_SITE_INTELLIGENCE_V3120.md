# Site Intelligence v3.12.0 — Publication Adapters, Institutional Handoffs, and Release Governance

This release turns human-approved editorial workspaces into controlled publication release candidates. Each release carries immutable evidence and content fingerprints, package checksums, adapter-specific delivery metadata, validation results, and a separate human approval record.

## Included

- Publication Adapters for Publications, Knowledge Library, Decision Studio, WordPress manual import, and download.
- Release preparation, validation, approval, package export, history, and manual handoff receipts.
- Package checksums and evidence-drift detection.
- Embargo and public, unlisted, or internal visibility metadata.
- Separation of duties between preparation, validation, and approval.
- Public policy, adapter catalog, and aggregate status endpoints.
- Read-only WordPress release-governance surface.

## Boundaries

No automatic publication, WordPress write, institutional destination write, credential storage, webhook delivery, recipient identity storage, evidence mutation, or affiliate insertion is performed.

The release enforces separation of duties across preparation, validation, and approval.
