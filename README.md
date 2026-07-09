# Sustainable Catalyst Site Intelligence

Version: 0.10.0

Site Intelligence is the Sustainable Catalyst analytics, registry, external-source, reporting, AI-brief, public-dashboard, and admin-control platform.

## v0.10.0 highlights

- WordPress admin UX polish
- Diagnostic stabilization
- Backend connection checker
- Public/private visibility warning layer
- One-click diagnostic summary
- Shortcode copy/placement support

## New backend endpoints

- `/admin/status`
- `/admin/connection-check`
- `/admin/public-readiness-check`
- `/admin/diagnostic-summary`

## New private shortcodes

- `[sc_site_intelligence_diagnostic_summary]`
- `[sc_site_intelligence_connection_check]`

Keep admin shortcodes on private/admin-only pages.


## v0.10.0 — Public Flagship Dashboard Page Builder

Adds a public-safe page-builder layer for assembling the flagship Sustainable Catalyst Site Intelligence dashboard.

New public endpoints:

- `/public/page-builder`
- `/public/page-builder/shortcodes`
- `/public/page-builder/readiness`
- `/intelligence/public-page-builder`

New WordPress shortcodes:

- `[sc_site_intelligence_public_flagship]`
- `[sc_site_intelligence_public_page_builder]`
- `[sc_public_dashboard_shortcode_bundle]`

The flagship shortcode uses only public-safe modules and local presentation copy by default.
