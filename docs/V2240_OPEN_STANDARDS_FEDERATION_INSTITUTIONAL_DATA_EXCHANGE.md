# Site Intelligence v2.24.0 — Open Standards, Federation, and Institutional Data Exchange

## Purpose

This release makes Site Intelligence records portable across institutions without pretending that every institution uses the same methods, trust model, hosting arrangement, or identity system.

## Exchange model

- Institutions register stable identifiers, public catalog locations, and presentation metadata.
- Records retain type, license, rights, provenance, distributions, temporal/spatial coverage, and hosting mode.
- Catalogs export as DCAT-compatible JSON-LD, GeoJSON, or CSV.
- Federation manifests carry SHA-256 receipts and optional HMAC-SHA256 signatures.
- Local trust policies define accepted institutions, key IDs, record types, and hosting modes.
- Imports are previewed before a human-confirmed acceptance or quarantine receipt is written.

## Hosting modes

- **Hosted:** Site Intelligence or the publishing institution is the authoritative host.
- **Mirrored:** A copy is retained while the original authority remains visible.
- **Referenced:** Metadata points to an external authoritative record without copying its payload.

## Safety and governance

A valid signature can verify manifest integrity when a trusted key is available. It does not independently prove institutional identity, methodological quality, legal authority, or truth. Remote fetching, materialization, and external writes are not automatic. Trust policies, signing keys, import receipts, and private records are never exposed in public responses.
