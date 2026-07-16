# Site Intelligence v2.21.0 — Installation and Validation

## Files

- `sustainable-catalyst-site-intelligence-v2.21.0-repo.zip`
- `sustainable-catalyst-site-intelligence-v2.21.0-wordpress.zip`
- `install_and_push_site_intelligence_v2_21_0.sh`

## Installer behavior

The installer creates a safety archive and backup branch, resets the repository to `origin/main`, overlays the immutable release, creates an isolated Python 3.11–3.13 validation environment, verifies HTTPX2/TestClient compatibility, redirects all writable runtime paths to a temporary directory, runs the complete backend suite, validates release and syntax contracts, rechecks the immutable manifest, packages the WordPress plugin, commits, rebases, and pushes with GitHub CLI or SSH authentication.

## Production deployment

1. Run the installer from `~/Downloads`.
2. In Render, use **Manual Deploy → Clear build cache & deploy**.
3. Confirm `/health` and `/release` report `2.21.0`.
4. Confirm `/public/scheduled-monitoring`, `/public/intelligence-digests`, and `/public/intelligence-feeds` respond.
5. Install the WordPress plugin only after backend parity is confirmed.
6. Configure a persistent disk or another durable path for monitor, alert, digest, feed, and delivery state.
7. An external scheduler may invoke `/admin/scheduled-monitoring/run-due?dry_run=false` no more often than hourly. The application does not claim an internal persistent scheduler.

## WordPress shortcodes

- `[sc_public_monitoring_digests]`
- `[sc_public_intelligence_feed feed_id="feed-id"]`
- `[sc_scheduled_monitoring_control_center]`

## Validation baseline

The packaged release contains 471 immutable files and is expected to complete 504 backend tests before the installer commits or pushes any changes.
