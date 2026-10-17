# Site Intelligence production-source reconciliation — 2026-10-17

**Status: IN PROGRESS — not merged, not a production deployment.**

## Why this branch exists

The remote repository currently identifies v4.56.0 in its README, while the standalone application running on Contabo has been incrementally extended with ocean research overlays. Installing overlay ZIPs on the VPS does not update GitHub. This reconciliation must preserve the newer production integrations and the existing repository history without overwriting the large customized FastAPI entry point.

## Snapshot examined

User-supplied source-only Contabo archive `site-intelligence-source-sync.tar.gz` (3.2 MiB compressed; 1,120 tar members; approximately 13.27 MB uncompressed file content) containing:
- `site-intelligence/backend`
- `site-intelligence-web`

The archive was collected after the v4.64.0 deployment and **does not contain** `ocean-nasa-imagery-v4650.js` or `ocean-workbench-tabs-v4650.js`. Therefore it must not be represented as a fully deployed v4.65.0 snapshot.

## Relevant production-source modules located

- `site-intelligence/backend/app/chlorophyll_v4600.py`
- `site-intelligence/backend/app/salinity_v4610.py`
- `site-intelligence/backend/app/currents_v4620.py`
- `site-intelligence/backend/app/sea_level_v4630.py`
- `site-intelligence/backend/app/marine_waves_v4640.py`
- `site-intelligence-web/app/assets/ocean-biology-v4600.js`
- `site-intelligence-web/app/assets/ocean-salinity-v4610.js`
- `site-intelligence-web/app/assets/ocean-currents-v4620.js`
- `site-intelligence-web/app/assets/ocean-sea-level-v4630.js`
- `site-intelligence-web/app/assets/ocean-marine-waves-v4640.js`
- `site-intelligence-web/app/assets/ocean-workbench-tabs-v4640.js`
- `site-intelligence-web/app/assets/ocean-certification-v46212.js`
- `site-intelligence-web/app/assets/ocean-reliability-v46213.js`

## Reconciliation gates before merging

1. Review all archive contents for secrets, keys, tokens, personal data, binary/backup artifacts; the initial limited-pattern scan found no recognizable private keys or GitHub tokens, but this is not a comprehensive secret audit.
2. Diff the actual GitHub branch source against the uploaded production snapshot, retaining repository files absent from the archive.
3. Apply source-only changes and appropriately update tests, asset entry-point references, backend routing, and documentation. **Never wholesale replace** production `backend/app/main.py`.
4. Verify the ocean backend endpoints, browser tab registration, and existing non-ocean modules.
5. Reconcile v4.65.0 separately from its release overlay or a later verified production snapshot.
6. Run CI/tests and review the full diff; merge only after review.

## Scope of this commit

This first commit creates a reconciliation audit record only. **It does not yet import the production source files and must not be treated as a synchronized repository.**
