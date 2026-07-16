# Sustainable Catalyst Site Intelligence v2.24.0

## Open Standards, Federation, and Institutional Data Exchange

This release adds a governed institutional exchange layer built around portable catalogs, explicit provenance, licensing, signed manifests, trust policies, and preview-first imports.

### Highlights

- DCAT-compatible JSON-LD public catalogs
- PROV-compatible provenance metadata
- GeoJSON and CSV exchange
- Dataset, publication, service, model, evidence-package, and spatial-layer records
- Hosted, mirrored, and referenced record states
- SHA-256 and HMAC-SHA256 manifest integrity
- Institution trust policies and expected key IDs
- Preview-only validation and human-confirmed import receipts
- Quarantine for blocked or invalid manifests
- Public Federation workspace and WordPress surfaces

### Boundaries

The release does not automatically fetch remote catalogs, import records, materialize external payloads, write to remote institutions, or infer institutional identity from a signature. Public endpoints exclude private records, trust policies, signing keys, and import receipts.
