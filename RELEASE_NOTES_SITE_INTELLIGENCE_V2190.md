# Site Intelligence v2.19.0

## Cross-Domain Knowledge Graph and Relationship Explorer

Site Intelligence v2.19.0 connects countries, regions, organizations, sources, indicators, events, documents, models, claims, datasets, publications, methodologies, workspaces, places, programs, and policies through typed, evidence-backed, time-aware relationships.

The graph remains an inspectable evidence structure. It does not convert graph proximity, path length, degree, sequence, or association into a causal conclusion, importance score, risk score, or ranking.

### Added

- Stable typed entity records with aliases, external identifiers, visibility, lifecycle state, source-system context, and SHA-256 integrity receipts.
- Immutable entity-type and relationship-type registries.
- Directed relationships with inverse labels, evidence/source references, confidence metadata, human-review state, and temporal validity.
- Exact alias and identifier resolution with ambiguity-preserving candidate responses.
- Preview-only entity reconciliation; no automatic merging.
- Bounded breadth-first traversal and shortest-path exploration.
- Orphan, dangling-edge, missing-evidence, and alias-collision diagnostics.
- Public-safe JSON and CSV graph exports.
- Read-only Platform Core graph handoff packets.
- Dedicated public Relationships workspace at `/app/?view=graph`.
- WordPress public and administrator shortcodes.

### Public endpoints

- `/public/knowledge-graph`
- `/public/knowledge-graph/methodology`
- `/public/knowledge-graph/diagnostics`
- `/public/knowledge-graph/entities`
- `/public/knowledge-graph/entities/{entity_id}`
- `/public/knowledge-graph/relationships`
- `/public/knowledge-graph/resolve`
- `/public/knowledge-graph/traverse`
- `/public/knowledge-graph/path`
- `/public/knowledge-graph/export`

### Administrative endpoints

- `/admin/knowledge-graph/control-center`
- `/admin/knowledge-graph/entities/register`
- `/admin/knowledge-graph/aliases/register`
- `/admin/knowledge-graph/relationships/register`
- `/admin/knowledge-graph/reconcile/preview`
- `/admin/knowledge-graph/export`
- `/admin/knowledge-graph/platform-core-handoff`

### Governance

The release does not permit automatic causation, automatic entity merging, unsupported relationship creation, individual tracking, surveillance, social scoring, military targeting, or autonomous consequential decisions. Public relationships require approved public endpoint entities, evidence or source references, and human review.
