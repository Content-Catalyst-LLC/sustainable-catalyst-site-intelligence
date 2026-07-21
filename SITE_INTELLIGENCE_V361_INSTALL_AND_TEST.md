# Site Intelligence v3.6.1 install and test

1. Place the release bundle files together in `~/Downloads`.
2. Run `install_and_push_site_intelligence_v3_6_1.sh`.
3. Confirm the immutable manifest, 635-test suite, release contract, JavaScript syntax, and PHP syntax all pass.
4. Deploy the latest `main` commit on Render using **Clear build cache & deploy**.
5. Upload `sustainable-catalyst-site-intelligence-v3.6.1-wordpress.zip` in WordPress.
6. Open **Settings → SC Site Intelligence → Live Intelligence**.
7. Keep freshness labels enabled; begin with a 300-second browser refresh, 15-second proxy timeout, 120-second fresh cache, and 24-hour stale-cache ceiling.
8. Verify `/public/live-intelligence/status` reports a delivery state and freshness counts.
9. Confirm the homepage ticker shows `Live`, `Recently updated`, `Delayed`, `Stale`, `Historical observation`, `Update time unavailable`, or `Temporarily unavailable` honestly.
10. Test reduced motion, keyboard focus, mobile previous/next controls, and an unmatched country channel.

The installer preserves the repository `.env`, creates a safety archive and branch when updating an existing clone, and does not expose API credentials to WordPress or browser JavaScript.
