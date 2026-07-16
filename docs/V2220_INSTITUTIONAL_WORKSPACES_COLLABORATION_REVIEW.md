# Site Intelligence v2.22.0 — Institutional Workspaces, Collaboration, and Review

## Purpose

This release adds optional shared institutional workspaces without changing the account-free public Site Intelligence experience. Private collaboration records remain behind token-protected administrative APIs. Public endpoints expose only workspaces that have been deliberately set to `public` and `published` after human evidence review.

## Workspace model

A workspace contains an institutional label and branding, topics, visibility, lifecycle status, retention period, member-role records, assignments, comments and review notes, evidence decisions, source collections, activity receipts, and exportable archive packets.

Roles are explicit:

- **Analyst:** capture sources, create assignments, and comment.
- **Reviewer:** review evidence, qualify limitations, and add review notes.
- **Publisher:** assess publication readiness, publish, and export.
- **Administrator:** manage workspaces, members, retention, and all publisher capabilities.

These role records do not provision accounts and do not replace an institutional identity provider.

## Public boundary

Public visitors never need an account. Public APIs and WordPress surfaces expose only:

- published public workspace titles and summaries;
- institutional presentation metadata;
- approved public-eligible evidence counts;
- public source collections containing approved public-eligible evidence identifiers;
- aggregate governance diagnostics.

Member identities, assignments, comments, review notes, private evidence, activity logs, retention receipts, and private or unlisted workspaces are not exposed publicly.

## Human approval and review

Evidence approval is never automatic. Every review requires a decision and rationale. A workspace cannot be published until at least one evidence review is approved and all urgent assignments are completed or cancelled.

## Retention and deletion

Retention is preview-first. Applying retention requires `confirm=true`. Completed assignments and resolved comments may be tombstoned after the configured period. Evidence decisions, published summaries, member-role history, and append-only audit receipts remain protected.

## Persistence

The default implementation is file-backed and zero-cost. Production collaboration requires a durable Render disk or another configured persistent path. This release does not include a database, account provisioning, or an identity provider.

## Endpoints

Public:

- `GET /public/institutional-workspaces`
- `GET /public/institutional-workspaces/diagnostics`
- `GET /public/institutional-workspaces/{workspace_id}`

Administrative, token-protected:

- `GET /admin/institutional-workspaces/control-center`
- `GET /admin/institutional-workspaces/{workspace_id}`
- `POST /admin/institutional-workspaces`
- `POST /admin/institutional-workspaces/{workspace_id}`
- `POST /admin/institutional-workspaces/{workspace_id}/members`
- `POST /admin/institutional-workspaces/{workspace_id}/assignments`
- `POST /admin/institutional-workspaces/{workspace_id}/comments`
- `POST /admin/institutional-workspaces/{workspace_id}/evidence-reviews`
- `POST /admin/institutional-workspaces/{workspace_id}/source-collections`
- `GET /admin/institutional-workspaces/{workspace_id}/retention-preview`
- `POST /admin/institutional-workspaces/{workspace_id}/retention`
- `GET /admin/institutional-workspaces/{workspace_id}/export?format=json|zip`

## Responsible-use boundaries

- No automatic publication or evidence approval.
- No exposure of private collaboration records.
- No individual tracking, social scoring, or hidden performance ranking.
- No claim that role records constitute authentication.
- No claim that archive exports were ingested by another system.
- No automatic deletion without explicit confirmation.
