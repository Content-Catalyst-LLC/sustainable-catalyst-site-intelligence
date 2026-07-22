# Site Intelligence v3.21.0 — Saved Discovery Views, Public Research Collections, and Evidence Pathways

## Summary

Site Intelligence v3.21.0 adds a governed curation layer above Public Registry Discovery. Editorial and research teams can preserve reproducible discovery states, review and approve public research collections, and publish ordered evidence pathways tied to retained public-record snapshots and SHA-256 checksums.

## Evidence pathways and delivered capabilities

- Saved Discovery Views with canonical query, filter, and sort states.
- Separate preparation, review, and approval roles.
- Approved result snapshots and filter-state checksums.
- Public research collections assembled from approved saved views and public registry records.
- Human-written rationale for ordered evidence-pathway steps.
- Drift detection for changed or missing source records and saved views.
- Required drift acknowledgment before collection approval.
- JSON and Markdown collection packages.
- Public API and read-only WordPress collection surface.

## Privacy and governance

Visitor queries are not stored. Visitor profiles and personal identity records are not created. Drafts and private collections do not enter public endpoints. Approved snapshots are retained rather than overwritten. Site Intelligence performs no network verification, source-record mutation, certification, or remote-system write.

## WordPress shortcode

`[sc_live_intelligence_registry_collections]`
