# Site Intelligence v3.7.2 — Install and Test

1. Run `install_and_push_site_intelligence_v3_7_0.sh` from the release-bundle directory.
2. Deploy the pushed backend revision on Render.
3. Install `sustainable-catalyst-site-intelligence-v3.7.2-wordpress.zip` in WordPress.
4. Place `[sc_live_intelligence surface="homepage" limit="8" max_visible="8"]` directly below the homepage hero, or use the automatic top-surface setting.
5. Confirm `/wp-json/sc-site-intelligence/v1/live-intelligence/homepage` and `/wp-json/sc-site-intelligence/v1/live-intelligence/gateway-policy`.
6. Open several signals and confirm that context pages remain on the Sustainable Catalyst domain before source handoff.
