# Site Intelligence v2.14.0

## Historical Archive and Temporal Change Intelligence

Site Intelligence v2.14.0 adds a historical evidence layer to the managed connector system introduced in v2.13.0. Accepted live ingestions can create immutable, sanitized dataset snapshots without exposing credentials, request headers, or archived payload bodies through public endpoints.

## Core capabilities

- Versioned snapshots across all 14 managed connector datasets
- Canonical JSON serialization and SHA-256 integrity digests
- Duplicate snapshot detection and deduplication
- Historical first-seen, last-seen, and source-period coverage
- Generic numeric historical series without silent imputation
- Snapshot-to-snapshot field and numeric change comparison
- Material-change labels based on explicit configurable thresholds
- Source revision detection when the same source period changes
- Snapshot, change, and revision metadata endpoints
- History export bundles with optional administrator-only payload inclusion
- Preview-first retention with protected newest snapshots
- Verified restoration previews that do not overwrite live state
- Automatic archive receipts attached to successful live connector ingestion

## Public boundary

Public endpoints expose dataset coverage, snapshot metadata, derived numeric series, change events, and revision events. They do not expose:

- archived payload bodies;
- storage paths;
- connector credentials or headers;
- private execution notes;
- a live restore operation; or
- claims that historical coverage is continuous or complete.

## Source revisions versus real-world change

When a changed payload covers the same declared source timestamp as the previous accepted snapshot, the archive records a source revision. An explicit changed source revision identifier also creates a revision receipt. This distinction prevents a correction to a previously published record from being presented automatically as a newly observed real-world event.

The classification remains evidence-dependent. Sources that do not publish usable timestamps or revision identifiers may only support a general `data_update` classification.

## Storage and zero-cost operation

The default archive is file-backed under `backend/data/historical_archive_v2140`. The directory is excluded from Git and immutable release manifests. This keeps local and self-hosted operation free, but a Render deployment needs a persistent disk or an external durable storage path if history must survive service replacement or redeployment.

## Retention

Retention is dry-run by default. The implementation can evaluate age and per-dataset snapshot limits while protecting the newest snapshots. Applying retention removes selected snapshot payload files and rewrites the snapshot index; change and revision receipts remain as audit metadata.

## Restoration boundary

v2.14.0 provides verified restoration previews. The archive checks the stored payload digest and returns the private snapshot body to an authorized administrator. It does not overwrite the current connector cache, current dataset state, or public application state.

## Endpoints

### Public

- `GET /public/history`
- `GET /public/history/datasets`
- `GET /public/history/datasets/{dataset_id}/series`
- `GET /public/history/changes`
- `GET /public/history/revisions`

### Private administrator

- `GET /admin/history/control-center`
- `GET /admin/history/snapshots`
- `POST /admin/history/snapshots/capture`
- `GET /admin/history/snapshots/{snapshot_id}`
- `GET /admin/history/compare`
- `GET /admin/history/export/{dataset_id}`
- `GET /admin/history/restore-preview/{snapshot_id}`
- `GET /admin/history/retention`
- `POST /admin/history/retention/apply`

## WordPress

- Public metadata panel: `[sc_public_temporal_intelligence]`
- Administrator control center: `[sc_historical_archive_control_center]`

## Command line

```bash
python scripts/historical_archive_v2140.py datasets
python scripts/historical_archive_v2140.py snapshots --dataset climate-energy-timeseries
python scripts/historical_archive_v2140.py retention --days 3650 --max-snapshots 3650
```

The `--apply` retention flag is required before any snapshot deletion occurs.
