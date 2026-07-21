# Site Intelligence v3.8.0 — Install and Test

1. Unzip `sustainable-catalyst-site-intelligence-v3.8.0-release-bundle.zip` in Downloads.
2. Run `chmod +x install_and_push_site_intelligence_v3_7_1.sh`.
3. Run `./install_and_push_site_intelligence_v3_7_1.sh`.
4. Deploy the resulting `main` commit in Render.
5. Upload `sustainable-catalyst-site-intelligence-v3.8.0-wordpress.zip` in WordPress.
6. Confirm `/public/build-info`, `/public/live-intelligence/rotation-policy`, and `/public/live-intelligence/homepage` report v3.8.0.
7. Confirm `[sc_live_intelligence surface="homepage" limit="8" max_visible="8"]` renders beneath the homepage hero.

The installer preserves `.env`, verifies the immutable manifest, runs the full backend regression suite, checks JavaScript and PHP syntax, packages the WordPress plugin, commits the release, and pushes only when validation succeeds.
