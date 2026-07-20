# Site Intelligence v3.1.3 — Install and Test

1. Place `sustainable-catalyst-site-intelligence-v3.1.3-repo.zip` and `install_and_push_site_intelligence_v3_1_3.sh` in `~/Downloads`.
2. Run the installer from Terminal.
3. Deploy the latest `main` commit on Render.
4. Confirm backend and WordPress plugin versions both report `3.1.3`.
5. Upload `sustainable-catalyst-site-intelligence-v3.1.3-wordpress.zip` in WordPress.
6. Open **Site Intelligence → Live Intelligence** and choose the feeds to display.
7. Test the automatic homepage ticker and a manual shortcode such as `[sc_live_intelligence feeds="usgs,noaa,reliefweb" limit="12"]`.
8. Confirm the ticker remains visible with **Below Astra breadcrumb** selected, including on the homepage.
9. Confirm the theme's existing navigation and breadcrumb colors are unchanged.
