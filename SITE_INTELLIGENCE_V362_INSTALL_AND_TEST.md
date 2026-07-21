# Site Intelligence v3.6.2 install and test

1. Place the v3.6.2 release-bundle files together in `~/Downloads`.
2. Run `install_and_push_site_intelligence_v3_6_2.sh`.
3. Confirm the immutable manifest, 642-test suite, v3.6.2 release contract, JavaScript syntax, and PHP syntax pass.
4. Deploy the latest `main` commit on Render using **Clear build cache & deploy**.
5. Upload `sustainable-catalyst-site-intelligence-v3.6.2-wordpress.zip` in WordPress.
6. Open **Settings → SC Site Intelligence → Live Intelligence**.
7. Choose **Slow moving ticker**, **Fully static strip**, or **Manual previous / next viewer**.
8. Keep the reduced-motion result on **Static strip** unless you prefer the manual viewer.
9. Begin with eight maximum visible signals and the mobile rotator or stacked-card mode.
10. Verify `/public/live-intelligence/presentation-policy` and the matching WordPress REST proxy route.
11. Test pause, hover, keyboard focus, Arrow Left, Arrow Right, Home, End, previous/next buttons, swipe gestures, reduced motion, forced colors, 200% zoom, mobile stacked mode, and JavaScript-disabled fallback.
12. Confirm Astra navigation and breadcrumb colors remain unchanged.

The installer preserves the repository `.env`, creates a safety archive and branch when updating an existing clone, and does not expose API credentials to WordPress or browser JavaScript.
