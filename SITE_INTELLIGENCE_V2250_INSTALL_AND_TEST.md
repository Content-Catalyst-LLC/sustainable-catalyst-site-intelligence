# Install and test Site Intelligence v2.25.0

1. Put the repository ZIP and installer in `~/Downloads`.
2. Run the installer.
3. Confirm 554 tests pass, the release contract passes, and the immutable manifest is reverified.
4. Deploy the latest `main` commit in Render with **Clear build cache & deploy**.
5. Confirm `/health`, `/release`, and `/public/production-governance` report v2.25.0.
6. Install the WordPress plugin only after backend parity is confirmed.

For durable production state, configure:

```text
SC_SI_PRODUCTION_DATABASE_PATH=/var/data/production-governance/site_intelligence.sqlite3
SC_SI_PRODUCTION_BACKUP_PATH=/var/data/production-governance/backups
```

The default repository-relative paths are suitable for local validation but not durable Render redeployments.
