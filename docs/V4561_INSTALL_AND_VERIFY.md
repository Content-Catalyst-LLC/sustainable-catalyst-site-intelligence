# v4.56.1 Install and Verify

Apply on a clean v4.56.0 repository, run `python3 scripts/validate_v4561_release.py`, run the v4.56.1 pytest plus the v4.56.0/4.55.3 regression line, package, commit/push, and deploy backend before web.

The production backend helper intentionally modifies only the Site Intelligence `.env.production` bridge/workspace switches. Existing provider credentials are preserved. It executes Platform Core's idempotent migration/seed path inside `sc-core` to restore any missing catalog rows.
