# Site Intelligence v2.18.0

## Evidence Synthesis, Claims, and Contradiction Review

Site Intelligence v2.18.0 adds a governed evidence-analysis layer above the connector, archive, spatial, harmonization, and model systems. Claims, evidence records, reviewer decisions, uncertainty, and synthesis packets remain separate and digest-verifiable.

### Added

- Structured factual, interpretive, causal, projection, and normative claims.
- Supporting, qualifying, conflicting, and contextual evidence relationships.
- Source titles, identifiers, URLs, excerpts, locators, authority context, methodology context, limitations, and SHA-256 receipts.
- Measurement, method, source, comparability, causal, forecast, and coverage uncertainty records.
- Human approval, rejection, revision, unresolved, and supersession workflows.
- Contradiction and evidence-completeness diagnostics.
- Deterministic grounded synthesis using only registered evidence IDs.
- Citation-ready JSON, CSV, and Markdown evidence packets.
- Read-only Knowledge Library and Research Librarian handoffs.
- Public-safe claims and evidence workspace at `/app/?view=evidence`.
- WordPress public and administrator shortcodes.

### Public endpoints

- `/public/evidence-synthesis`
- `/public/evidence-synthesis/methodology`
- `/public/evidence-synthesis/diagnostics`
- `/public/claims`
- `/public/claims/{claim_id}`
- `/public/claims/{claim_id}/contradictions`
- `/public/evidence-synthesis/export`

### Administrative endpoints

- `/admin/evidence-synthesis/control-center`
- `/admin/evidence-synthesis/claims/register`
- `/admin/evidence-synthesis/evidence/add`
- `/admin/evidence-synthesis/uncertainty/record`
- `/admin/evidence-synthesis/claims/review`
- `/admin/evidence-synthesis/synthesize`
- `/admin/evidence-synthesis/export`
- `/admin/evidence-synthesis/handoff`

### Governance

The release does not permit fabricated evidence, hidden contradictions, automatic causal findings, public synthesis without human approval, individual targeting, or autonomous consequential decisions. External AI assistance remains disabled by default.
