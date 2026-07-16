# Sustainable Catalyst Site Intelligence v2.14.0

## Historical Archive and Temporal Change Intelligence

Site Intelligence v2.14.0 adds an auditable historical evidence layer to the managed connector system introduced in v2.13.0. Successful accepted ingestions can now create immutable, sanitized dataset snapshots with SHA-256 integrity receipts, temporal coverage, change events, and source-revision records.

### New capabilities

- Versioned snapshots across all 14 managed connector datasets
- Canonical JSON serialization and SHA-256 integrity verification
- Automatic capture after accepted live connector ingestion
- Identical-payload deduplication
- First-seen, last-seen, and source-period coverage metadata
- Generic numeric historical series without interpolation or imputation
- Snapshot comparison with field and numeric deltas
- Material-change labels using an explicit configurable threshold
- Same-period source correction and revision detection
- Public-safe snapshot, change, revision, and series metadata
- Administrator-only archive inspection and export bundles
- Preview-first retention with protected newest snapshots
- Verified restoration previews that do not overwrite live data
- File-backed zero-cost operation with configurable durable paths
- Public and administrator-only WordPress temporal intelligence surfaces

### Public endpoints

- `GET /public/history`
- `GET /public/history/datasets`
- `GET /public/history/datasets/{dataset_id}/series`
- `GET /public/history/changes`
- `GET /public/history/revisions`

### Private control center

- `GET /admin/history/control-center`
- `GET /admin/history/snapshots`
- `POST /admin/history/snapshots/capture`
- `GET /admin/history/snapshots/{snapshot_id}`
- `GET /admin/history/compare`
- `GET /admin/history/export/{dataset_id}`
- `GET /admin/history/restore-preview/{snapshot_id}`
- `GET /admin/history/retention`
- `POST /admin/history/retention/apply`

### WordPress shortcodes

- `[sc_public_temporal_intelligence]`
- `[sc_historical_archive_control_center]`

### Validation

- 417 backend tests passed
- v2.14.0 release contract passed
- Python compilation passed
- JavaScript and service-worker syntax passed
- WordPress PHP syntax passed
- JSON, webmanifest, and YAML parsing passed
- Writable archive, connector state, queues, caches, Python bytecode, and pytest caches excluded from the immutable release manifest
- 367 immutable release files verified

### Important boundaries

Archived payload bodies are private. Public endpoints expose only sanitized metadata and derived series. Source revisions are distinguished from new observations when the available timestamps or revision identifiers support that conclusion. Missing observations are not silently imputed. Restoration remains preview-only in v2.14.0.

The default archive is file-backed. A Render persistent disk or another durable configured path is required if hosted history must survive service replacement or redeployment.
