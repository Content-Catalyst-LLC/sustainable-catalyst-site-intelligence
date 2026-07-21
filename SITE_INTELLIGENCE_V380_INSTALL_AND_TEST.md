# Site Intelligence v3.8.0 — Install and Test

1. Run `install_and_push_site_intelligence_v3_8_0.sh` from the release-bundle directory.
2. Deploy the resulting `main` commit in Render with a cleared build cache.
3. Confirm `/public/build-info` reports `3.8.0`.
4. Confirm `/public/live-intelligence/surfaces` lists eight surfaces.
5. Confirm `/public/live-intelligence/surfaces/library/feed` returns a bounded Library surface or an honest empty state.
6. Confirm `/public/live-intelligence/embed-manifest?surface=external_embed` exposes no credentials or administrative routes.
7. Upload `sustainable-catalyst-site-intelligence-v3.8.0-wordpress.zip` in WordPress.
8. Clear WordPress, Cloudflare, and browser caches.
9. Test the homepage shortcode and at least one Library, Advisory, Lab, publication, and external-embed preset while logged out.
