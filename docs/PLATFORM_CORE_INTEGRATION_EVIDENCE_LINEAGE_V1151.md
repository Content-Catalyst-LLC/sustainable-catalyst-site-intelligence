# Site Intelligence v1.15.1 — Platform Core Integration and Evidence Lineage

## Purpose

This release connects live Site Intelligence records to Sustainable Catalyst Platform Core v2.5.0. Platform Core becomes the system of record for evidence IDs, source snapshots, provenance activities, and ledger-backed write history.

## Record flow

```text
World Bank response
→ immutable source snapshot
→ normalization provenance activity
→ used/generated provenance links
→ stable evidence record
→ public evidence drawer
```

## Environment variables

```text
SC_SI_PLATFORM_CORE_ENABLED=true
SC_SI_PLATFORM_CORE_URL=https://your-platform-core-service.onrender.com
SC_SI_PLATFORM_CORE_WRITE_API_KEY=backend-only-secret
SC_SI_PLATFORM_CORE_PUBLIC_API_KEY=
SC_SI_PLATFORM_CORE_TIMEOUT_SECONDS=5
SC_SI_PLATFORM_CORE_QUEUE_PATH=backend/data/platform_core_queue.jsonl
SC_SI_PLATFORM_CORE_PUBLIC_EVIDENCE_URL=https://your-platform-core-service.onrender.com
```

## Security boundary

The Platform Core write key is used only by the Site Intelligence backend. It is never returned by public endpoints, embedded in WordPress, or included in browser JavaScript.

## Failure behavior

Platform Core failure does not prevent a validated source record from rendering. Failed writes enter a local JSONL queue. Stable deterministic IDs make replay idempotent.

## Public interface

Selecting a country-indicator card opens an evidence drawer with:

- displayed value and reporting year
- source and original source link
- Platform Core write state
- evidence ID
- source snapshot ID
- provenance activity ID
- transformation summary
- verification link
- known limitations
