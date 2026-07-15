# Site Intelligence v2.7.0 installation and testing

1. Put `sustainable-catalyst-site-intelligence-v2.7.0.zip` and `install_and_push_site_intelligence_v2_7_0.sh` in `~/Downloads`.
2. Run the installer.
3. Confirm the backend `/health` and `/public/build-info` routes report `2.7.0`.
4. Install the generated WordPress plugin ZIP.
5. Clear WordPress, Cloudflare, and browser caches.
6. Test `/app/?view=dossiers` for a country, a region, and a two-country comparison.

The installer creates an isolated Python test environment, runs the complete backend suite, validates Python, JavaScript, PHP, Bash, JSON, YAML, HTML IDs, the release manifest, and a push-safe secret scan before committing or pushing.
