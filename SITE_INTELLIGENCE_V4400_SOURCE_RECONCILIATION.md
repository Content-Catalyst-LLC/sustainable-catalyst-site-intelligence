# Site Intelligence v4.40.0 — Source Reconciliation (r1)

## Purpose

Site Intelligence v4.40.0 introduced the Energy Systems target-side runtime consumer, but the first v4.40.0 backend package retained 27 release-bound static policy/registry JSON files with a top-level `version` of `4.39.2`.

Several runtime modules intentionally reject a release-bound policy whose compatibility version differs from `APP_VERSION`.  As a result, the production container entered a restart loop during import and Caddy returned HTTP 502.

## Reconciliation rule

The affected JSON files carry two different kinds of identity:

- `version` — active application compatibility marker and therefore must equal the running Site Intelligence release (`4.40.0`).
- historical filename, schema, release ID, contract name, and other origin metadata — preserved exactly unless the underlying historical contract itself changes.

This reconciliation changes only the top-level compatibility `version` from `4.39.2` to `4.40.0` in the explicit 27-file allowlist.  It does not rename historical files, rewrite historical release IDs, alter schemas, or mutate runtime JSONL/state data.

## Deployment correction

The original v4.40.0 upgrader excluded the complete `backend/data/` tree in order to protect mutable runtime state.  That also prevented corrected immutable release-bound policy files from reaching production.

The r1 upgrader keeps the data-directory protection but explicitly copies only the 27 approved static policy/registry files from the package into the live backend before rebuilding the container.

## Release identity

- Application version: `4.40.0` (unchanged)
- WordPress compatibility: `4.40.0` (unchanged)
- Corrective packaging/source revision: `r1`
- Recommended Git tag: `v4.40.0-r1`
- No database migration
- No new environment variable or secret
- No WordPress plugin change required

## Regression gate

`backend/tests/test_source_reconciliation_v4400.py` verifies:

1. all 27 release-bound static files match `APP_VERSION`;
2. historical origin metadata remains intact; and
3. `app.main` imports successfully, preventing a repeat of the startup-loop failure.
