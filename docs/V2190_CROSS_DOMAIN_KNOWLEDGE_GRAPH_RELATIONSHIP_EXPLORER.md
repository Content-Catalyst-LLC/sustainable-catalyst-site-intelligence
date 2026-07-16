# Site Intelligence v2.19.0 — Cross-Domain Knowledge Graph and Relationship Explorer

## Purpose

This release connects the entities already represented across Site Intelligence without collapsing them into a score, ranking, causal model, or hidden ontology. Countries, regions, organizations, sources, indicators, events, documents, models, claims, datasets, publications, methodologies, workspaces, places, programs, and policies become typed graph entities. Relationships remain independently reviewable records with source and target direction, evidence references, confidence metadata, temporal validity, visibility, human-review status, and SHA-256 integrity.

## Entity and identifier model

Each entity has a stable internal identifier, type, label, description, visibility, lifecycle state, aliases, external identifiers, source-system metadata, and integrity receipt. Aliases and external identifiers support exact lookup and reconciliation previews. A preview may return multiple candidates and explicitly reports ambiguity. The system never merges entities automatically.

## Relationship model

The immutable relationship registry defines allowed relationship types, direction, inverse labels, evidence requirements, and causal status. Public relationships require approved public endpoint entities, evidence IDs or source IDs, and explicit human-review confirmation. Temporal relationships may include `valid_from`, `valid_to`, and `observed_at` fields.

## Exploration

The public API provides entity search, entity detail, relationship filtering, alias resolution, bounded breadth-first traversal, shortest paths, diagnostics, and read-only exports. Traversal depth and result counts are capped. Path results preserve canonical edge direction but may navigate relationships in either direction for discovery.

## Diagnostics

Diagnostics identify orphan entities, dangling relationships, relationships missing evidence references, and alias collisions. These are review queues, not automatic correction instructions.

## Platform Core integration

The Platform Core handoff is read-only. It packages entities, relationships, evidence references, temporal metadata, visibility, review state, and integrity receipts. Site Intelligence does not write to Platform Core or claim successful graph ingestion.

## Responsible-use boundaries

- Graph proximity, sequence, degree, centrality, or path length does not prove causation, importance, influence, or risk.
- Entity reconciliation remains preview-only and requires human review.
- No individual tracking, surveillance, targeting, social scoring, or military operational use.
- No unsupported relationship creation or hidden confidence metadata.
- No public relationship without evidence or source references and human approval.
