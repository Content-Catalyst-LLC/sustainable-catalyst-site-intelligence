# Site Intelligence v2.20.0

## Intelligence Publishing and Story Map Studio

Site Intelligence v2.20.0 turns reviewed investigations, evidence, maps, timelines, charts, source records, and methodology notes into durable intelligence publications without collapsing editorial judgment into automation.

The studio preserves the distinction between draft work, editorial review, immutable published versions, public directory entries, and exact-link unlisted publications. Story order, spatial proximity, chart alignment, and temporal adjacency remain presentation structures—not proof of causation.

### Added

- Versioned publication projects with private, unlisted, and public visibility.
- Narrative, heading, callout, quote, map, timeline, chart, evidence-table, source-list, methodology, image, and divider blocks.
- Source and evidence references on analytical and visual blocks.
- Editorial submission, approval, changes-requested, and rejection workflows.
- Explicit human publish confirmation after editorial approval.
- Immutable publication versions with SHA-256 integrity receipts.
- Public directory behavior that excludes unlisted publications while preserving exact-ID access.
- Story-map extraction for map, timeline, chart, evidence, and narrative sequences.
- JSON, CSV, Markdown, and print-ready HTML exports.
- Read-only WordPress handoff packets.
- Dedicated public Publishing workspace at `/app/?view=publishing`.
- WordPress directory, publication, and administrator-control-center shortcodes.

### Public endpoints

- `/public/intelligence-publishing`
- `/public/intelligence-publishing/methodology`
- `/public/intelligence-publishing/diagnostics`
- `/public/intelligence-publications`
- `/public/intelligence-publications/{publication_id}`
- `/public/intelligence-publications/{publication_id}/story-map`
- `/public/intelligence-publications/{publication_id}/versions`
- `/public/intelligence-publications/{publication_id}/export`

### Administrative endpoints

- `/admin/intelligence-publishing/control-center`
- `/admin/intelligence-publishing/projects`
- `/admin/intelligence-publishing/projects/{project_id}/blocks`
- `/admin/intelligence-publishing/projects/{project_id}/review/submit`
- `/admin/intelligence-publishing/projects/{project_id}/review/decide`
- `/admin/intelligence-publishing/projects/{project_id}/publish`
- `/admin/intelligence-publishing/projects/{project_id}/export`
- `/admin/intelligence-publishing/projects/{project_id}/wordpress-handoff`

### Governance

No publication becomes public without a human editorial approval and explicit publish confirmation. The studio does not fabricate sources, quotations, evidence, maps, institutional approval, or causal conclusions. Conflicting evidence, limitations, missing data, and methodology notes must not be silently removed. WordPress handoffs remain read-only and do not claim a successful remote write.
