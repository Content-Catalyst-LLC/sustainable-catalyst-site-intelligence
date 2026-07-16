# Site Intelligence v2.23.0 — Typed Cross-Platform Intelligence Workflows

## Purpose

This release turns product handoffs into explicit, portable intelligence contracts. Each route declares a source platform, target platform, packet type, required payload fields, provenance, and receipt lifecycle.

## Platforms

- Site Intelligence
- Workbench
- Decision Studio
- Research Librarian
- Knowledge Library
- Research Lab
- Sustainable Catalyst Platform Core

## Workflow lifecycle

1. Create a packet against a registered route.
2. Validate required fields, size, platform direction, and provenance.
3. Export or queue the packet.
4. Deliver through a separately configured adapter or Platform Core.
5. Record an explicit accepted, completed, rejected, or failed receipt.
6. Add external record linkbacks when available.
7. Preview and human-confirm bounded retries after failures.

## Safety and truthfulness boundaries

- Packet creation is not delivery.
- Queueing is not delivery.
- Export is not delivery.
- A linkback is not verified unless an external validation process confirms it.
- File-backed mode has no persistent message broker or automatic retry worker.
- Platform Core is the preferred orchestration layer, but this release does not claim a live connection.
- Public endpoints expose route contracts and aggregate methodology only; packet payloads and operational history remain private.
- No account provisioning, individual tracking, social scoring, or autonomous consequential action is included.

## Public endpoints

- `GET /public/cross-platform-workflows`
- `GET /public/cross-platform-workflows/diagnostics`

## Administrative endpoints

- `GET /admin/cross-platform-workflows/control-center`
- `POST /admin/cross-platform-workflows/packets`
- `POST /admin/cross-platform-workflows/incoming`
- `GET /admin/cross-platform-workflows/packets/{packet_id}/validate`
- `GET /admin/cross-platform-workflows/packets/{packet_id}/dispatch-preview`
- `POST /admin/cross-platform-workflows/packets/{packet_id}/queue`
- `POST /admin/cross-platform-workflows/packets/{packet_id}/receipts`
- `GET /admin/cross-platform-workflows/packets/{packet_id}/retry-preview`
- `POST /admin/cross-platform-workflows/packets/{packet_id}/retry`
- `POST /admin/cross-platform-workflows/packets/{packet_id}/linkbacks`
- `GET /admin/cross-platform-workflows/packets/{packet_id}/export`

## Persistence

The default implementation is file-backed. Production packet, receipt, linkback, attempt, and recovery history requires a durable Render disk or another persistent path. Writable state is excluded from the immutable release manifest.
