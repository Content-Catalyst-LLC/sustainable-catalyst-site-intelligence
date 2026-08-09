# Site Intelligence v4.7.0 — Research Evidence and Knowledge Integration

## Purpose

This release connects Site Intelligence evidence to the wider Sustainable Catalyst research workflow without turning cross-product integration into an opaque automation layer.

## Added

- Public research-context normalization for selected places, indicators, events, records, and saved views.
- Source snapshots retaining publisher, source id, safe source URL, observation date, and retrieval date.
- Deterministic record and context fingerprints for change detection.
- Evidence-manifest export with record-level truth states and limitations.
- Citation export with source de-duplication and record fingerprints.
- Claim/evidence maps supporting `supports`, `contradicts`, `qualifies`, and `contextualizes` relationships.
- Knowledge Library discovery-query plans that explicitly distinguish query preparation from verified document matching.
- Review-only Research Librarian, Knowledge Library, Workbench, and Decision Studio handoff packets.
- Research workspace interface for manifest, citation, discovery, and handoff preview preparation.

## Responsible-use boundary

No public endpoint in this release remotely delivers a packet, writes to another Sustainable Catalyst product, publishes a conclusion, or claims that a Knowledge Library search was executed. Every handoff requires explicit human confirmation. Relevance does not establish truth, authority, causation, importance, or decision priority.
