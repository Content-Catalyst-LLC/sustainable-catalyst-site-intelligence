# Site Intelligence v3.11.0 — Editorial Workspace, Review Queues, and Publication Orchestration

Site Intelligence v3.11.0 extends source-linked Live Intelligence briefings with a governed editorial workspace.

## Delivered

- Role-based assignments using editorial handles rather than contact records.
- Retained revision history for title, deck, summary, observations, and limitations.
- Immutable canonical evidence, claim-source links, observed values, chronology, and provenance.
- Submit, request-changes, reject, and approve review states.
- Enforced separation of duties between authorship, submission, revision, and final approval.
- provider-neutral orchestration manifests for Publications, Knowledge Library, Decision Studio, and download workflows.
- Public aggregate workflow policy and status routes.
- Read-only WordPress editorial-governance surface.

## Boundaries

- No automatic publication.
- No automatic WordPress write.
- No publication-adapter write is performed.
- No evidence or source-value mutation through editorial revisions.
- No recipient, subscriber, email, phone, IP, cookie, session, or user-agent storage.
- Orchestration requires a human-approved workspace and verifies that canonical evidence has not changed.
