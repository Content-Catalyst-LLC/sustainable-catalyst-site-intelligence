# Site Intelligence v4.55.3 — Standalone Web Application Foundation & WordPress Decoupling

v4.55.3 separates the Site Intelligence user application from both WordPress and the FastAPI API hostname. The preferred user application is now designed for `https://intelligence.sustainablecatalyst.com`; FastAPI remains at `https://site-intelligence-api.sustainablecatalyst.com`.

## Delivered

- Independent `web/` application artifact with Docker/nginx deployment.
- History-based deep links for country, dossiers, economics, law, science, Earth, ocean, space, humanitarian, resources, events, research, and packages.
- Country context encoded in URL paths and propagated into domain API requests.
- Centralized API client with explicit configured API origin and credential forwarding boundary.
- Session context store independent of WordPress.
- Service worker and web application manifest owned by the standalone application.
- Six `/public/web-app/*` contract endpoints.
- First-party CORS support for `intelligence.sustainablecatalyst.com` even when an older env file has the pre-decoupling CORS list.
- WordPress role changed to `public-site-launch-bridge`; its primary Site Intelligence application shortcode launches the standalone app instead of hosting an iframe runtime.
- Legacy FastAPI `/app/` retained temporarily for migration compatibility but marked deprecated/non-preferred.

## Architecture

`intelligence.sustainablecatalyst.com` → standalone web container → `site-intelligence-api.sustainablecatalyst.com` → FastAPI/data/connectors.

WordPress is not required for standalone boot, routing, state, API transport, or application navigation.
