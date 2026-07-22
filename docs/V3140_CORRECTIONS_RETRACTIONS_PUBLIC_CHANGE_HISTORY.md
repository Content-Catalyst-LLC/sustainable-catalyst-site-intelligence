# Site Intelligence v3.22.0 — Corrections, Retractions, and Public Change History

Live Intelligence v3.22.0 adds an append-only public integrity layer above the approved correction workflow introduced in v3.13.0.

## Workflow

1. A post-publication issue is reviewed in Release Operations.
2. A public correction package is separately approved.
3. An editor prepares a public change notice.
4. A different approver confirms the notice, scope, release checksums, and effective date.
5. The approved notice enters the public change history and may be exported as JSON or Markdown for manual delivery.

## Notice types

- Correction
- Clarification
- Replacement
- Retraction
- Rollback notice

## Integrity rules

- The original release remains retained and addressable.
- Public history is append-only.
- Replacements link the original and replacement release checksums.
- Retractions require explicit acknowledgement that the original record remains retained.
- Draft notices and private corrections never enter the public feed.
- Site Intelligence does not rewrite evidence, delete destination content, or automatically republish a corrected record.
