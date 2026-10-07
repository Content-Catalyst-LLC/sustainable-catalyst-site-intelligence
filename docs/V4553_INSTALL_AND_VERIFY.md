# Install and Verify Site Intelligence v4.55.3

1. Certify the repository with `scripts/validate_v4553_release.py` and the v4.46–v4.55.3 regression suite.
2. Deploy the v4.55.3 backend ZIP with `deploy/contabo/upgrade_site_intelligence_backend_v4_55_3_contabo.sh`.
3. Deploy the separate v4.55.3 web ZIP with `deploy/contabo/upgrade_site_intelligence_web_v4_55_3_contabo.sh`.
4. Point DNS for `intelligence.sustainablecatalyst.com` at the Contabo host and install the Caddy site block in `deploy/contabo/site-intelligence-web-v4553.Caddyfile`.
5. Verify `https://intelligence.sustainablecatalyst.com/`, `/economics/KEN`, `/law/KEN`, and `/humanitarian/KEN` resolve through the standalone web container.
6. Verify API CORS from the standalone origin and `/public/web-app/manifest` reports WordPress runtime dependency `false`.
7. Install the WordPress v4.55.3 bridge package only after backend/web verification. WordPress remains optional to Site Intelligence application execution.

Production targets: backend `4.55.3`, capability registry `2.4.0`, 1506 routes, 197 modularized, 29 capabilities, 0 unclassified, 6 standalone-web routes, web container healthy on loopback port 8096.
